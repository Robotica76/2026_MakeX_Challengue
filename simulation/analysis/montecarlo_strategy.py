"""Monte Carlo search of the automatic-stage strategy (storm_breaker_2026.py), simulator only.

Each candidate is a set of program constants (strategy switches, motion-control limits, route
points). It is run on N sampled robots (montecarlo_config.json: wheel scale, motor gains and lag,
slip, gyro bias / drift / noise / scale, encoder resolution, start pose error) with the props
moved within the rules' +-5 mm tolerance. The same seeds are used for every candidate (common
random numbers), so differences come from the candidate, not from luck.

Ranking (team priorities, 2026-10-31): first the resources the automatic stage secures, then
the points they make possible, then time:
  resources = 12 if the X12 is valid (bonus balls for us)
            + 9 if the X9 is on our side and the bonus stays valid (denied to the opponent)
            + 1 per cone on our side
            - 5 per rule problem (collision, R06, R19, partner half, prop across the line,
              more than two bonus cubes on our side)
  points    = 20 x bonus balls (scored in the manual stage)
  time      = when the X12 is in the exchange area (earlier: less chance the opponent takes it)

    .venv/bin/python simulation/analysis/montecarlo_strategy.py --trials 12
    .venv/bin/python simulation/analysis/montecarlo_strategy.py --trials 40 --refine
Writes simulation/analysis/results/montecarlo_strategy.json.
"""

import argparse
import contextlib
import io
import itertools
import json
import math
import os
import random
import re
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELD2D = ROOT / "simulation" / "field2d"
PROGRAM = ROOT / "software" / "robot" / "main" / "storm_breaker_2026.py"
CONFIG = Path(os.environ.get("MC_CONFIG", Path(__file__).resolve().parent / "montecarlo_config_competition.json"))
REPORT = Path(__file__).resolve().parent / "results" / "montecarlo_strategy.json"
SECONDS = 31.0


def program_text(constants: dict) -> str:
    """The program with some of the values set in its constants() block replaced."""
    text = PROGRAM.read_text(encoding="utf-8")
    head, block = text.split("def constants():", 1)
    body, tail = block.split("\n\n\n", 1)
    for name, value in constants.items():
        body, n = re.subn(rf"^    {name} = .*$", f"    {name} = {value}", body, count=1, flags=re.M)
        if n != 1:
            raise KeyError(f"{name} is not set in constants() of {PROGRAM.name}")
    return head + "def constants():" + body + "\n\n\n" + tail


def trial(job):
    """job = (constants, seed) or (constants, seed, True) to also return the path (every 0.1 s)."""
    constants, seed = job[0], job[1]
    traced = len(job) > 2 and job[2]
    path = []
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    if str(FIELD2D) not in sys.path:
        sys.path.insert(0, str(FIELD2D))
    import field_layout as fl
    from balls import load_intake
    from kinematics import load_drive_train
    from mechanisms import load_mechanisms
    from props import denial_count, load_gripper
    from robot import RobotPose, load_config, start_pose
    from simulation import Simulation, load_gyro_sign
    from uncertainty import sample_variation

    ranges = json.loads(CONFIG.read_text())["ranges"]
    drive = load_drive_train()
    from uncertainty import Variation
    var = sample_variation(ranges, seed, tuple(drive.motors)) if seed >= 0 else Variation()   # seed < 0: ideal
    cfg = load_config()
    s0 = start_pose(cfg, fl.build_field())
    start = RobotPose(s0.x + var.start_dx_mm, s0.y + var.start_dy_mm, s0.theta + math.radians(var.start_dtheta_deg))
    sim = Simulation(cfg, start, drive, SECONDS, load_gyro_sign(), variation=var, ball_scenario="initial",
                     intake=load_intake(), mechanisms=load_mechanisms(), gripper=load_gripper())
    rng = random.Random(seed + 7)
    for p in sim.props if seed >= 0 else []:               # rules: props within +-5 mm
        if p.kind != "letter":
            p.x += rng.uniform(-5, 5)
            p.y += rng.uniform(-5, 5)
    folder = Path(tempfile.mkdtemp())
    program = folder / "storm_breaker_mc.py"
    program.write_text(program_text(constants), encoding="utf-8")
    sim.program = program
    x12_time = None
    exchange = next(el for el in sim.elements if el.name == "red_exchange_1")
    ex0, ey0, ex1, ey1 = exchange.bounds()
    with contextlib.redirect_stdout(io.StringIO()):
        sim.run()
        sim.gamepad.apply_event({"event": "press", "control": "button_1"})
        k = 0
        while sim.running:
            sim.step(1 / 60)
            k += 1
            if k == 15:
                sim.gamepad.apply_event({"event": "release", "control": "button_1"})
            if traced and k % 6 == 0:
                vx, vy, w = sim._velocity
                path.append((round(sim.time, 2), round(sim.pose.x), round(sim.pose.y),
                             round(math.degrees(sim.pose.theta), 1), round(math.hypot(vx, vy))))
            if x12_time is None:
                x12 = next(p for p in sim.props if p.label == "X12")
                if not x12.held and x12.z < 1 and x12.x + 60 > ex0 and x12.x - 60 < ex1 and x12.y - 60 < ey1:
                    x12_time = sim.time
    error = sim._runner.error if sim._runner else None
    denial = denial_count(sim.props, sim.balls, "red")
    judged = (sim.bonus_judged or {}).get("red", {"valid": [], "bonus_balls": 0, "on_side": 0})
    valid12 = "X12" in judged["valid"]
    x9_ours = any(p.label == "X9" and p.x + 60 <= 2220 for p in sim.props)
    problems = (len(sim.collisions.collisions) + sim.monitor.r06_penalties
                + (0 if (sim.monitor.auto_end or {}).get("stationary") else 1)
                + (1 if sim.half and sim.half.events else 0) + denial["props_on_line"]
                + len(sim.channels.events)                       # R26: robot inside a channel
                + (1 if judged.get("on_side", 0) > 2 else 0) + (1 if error and "Time limit" not in str(error) else 0))
    resources = 12 * valid12 + 9 * (x9_ours and valid12) + denial["cones"] - 5 * problems
    try:
        program.unlink()
        folder.rmdir()
    except OSError:
        pass
    x12_end = next(((round(p.x), round(p.y)) for p in sim.props if p.label == "X12"), None)
    return {"seed": seed, "valid_x12": valid12, "x12_end": x12_end, "path": path, "x9_ours": x9_ours, "cones": denial["cones"],
            "problems": problems, "resources": resources, "points": 20 * judged["bonus_balls"],
            "x12_time": x12_time, "collisions": [e["element"] for e in sim.collisions.collisions],
            "error": str(error) if error and "Time limit" not in str(error) else None}


def summarize(constants, rows):
    n = len(rows)
    times = [r["x12_time"] for r in rows if r["x12_time"] is not None]
    return {"constants": constants, "trials": n,
            "resources": sum(r["resources"] for r in rows) / n,
            "p_x12": sum(r["valid_x12"] for r in rows) / n,
            "p_x9": sum(r["x9_ours"] for r in rows) / n,
            "points": sum(r["points"] for r in rows) / n,
            "problems": sum(r["problems"] for r in rows) / n,
            "x12_time": sum(times) / len(times) if times else None,
            "x12_time_max": max(times) if times else None,
            "failures": [{k: v for k, v in r.items() if k != "path"}
                         for r in rows if not r["valid_x12"] or r["problems"]][:5]}


def evaluate(candidates, trials, workers, seed0=1000):
    jobs = [(c, seed0 + i) for c in candidates for i in range(trials)]
    with ProcessPoolExecutor(workers) as pool:
        rows = list(pool.map(trial, jobs, chunksize=1))
    out = []
    for j, c in enumerate(candidates):
        out.append(summarize(c, rows[j * trials:(j + 1) * trials]))
    out.sort(key=lambda r: (-r["resources"], -r["points"], r["x12_time"] or 99))
    return out


def grid():
    strategies = [{"DENY_X9": 0}, {"DENY_X9": 1}]
    motion = [{"V_MAX": 700, "A_MAX": 1200, "D_MAX": 1400},
              {"V_MAX": 900, "A_MAX": 1600, "D_MAX": 1800},
              {"V_MAX": 1100, "A_MAX": 2200, "D_MAX": 2400}]
    approach = [{"V_APPROACH": 350, "V_PULL": 260}, {"V_APPROACH": 500, "V_PULL": 400}]
    # (first search, 16 robots each: DENY_X9 1 / 700 / 1200 / 1400 / 500 / 400 ranked first)
    for s, m, a in itertools.product(strategies, motion, approach):
        yield {**s, **m, **a}


def refine(best: dict):
    """Neighbours of the best candidate: route points and control gains, one at a time."""
    steps = {"X_LANE": (-60, 60), "X_FLOOR_IN": (-15, 15), "GRAB_SHORT": (-8, 8), "K_HEADING": (-1.5, 1.5),
             "V_MAX": (-150, 150), "A_MAX": (-300, 300), "PASS_RADIUS": (-15, 25)}
    defaults = {"X_LANE": 1800, "X_FLOOR_IN": 1925, "GRAB_SHORT": 15, "K_HEADING": 5, "V_MAX": 700,
                "A_MAX": 1200, "PASS_RADIUS": 40}
    yield dict(best)
    for name, deltas in steps.items():
        for d in deltas:
            c = dict(best)
            c[name] = round(best.get(name, defaults[name]) + d, 3)
            yield c


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--trials", type=int, default=12)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--refine", action="store_true", help="then search around the best candidate")
    ap.add_argument("--config", type=Path, help="uncertainty ranges (default: montecarlo_config_competition.json, "
                                                  "the calibrated robot placed with a start jig)")
    args = ap.parse_args()
    if args.config:
        os.environ["MC_CONFIG"] = str(args.config.resolve())
        global CONFIG
        CONFIG = args.config.resolve()
    results = evaluate(list(grid()), args.trials, args.workers)
    report = {"grid": results}
    show(results[:6], "grid")
    if args.refine:
        neighbours = evaluate(list(refine(results[0]["constants"])), args.trials, args.workers, seed0=5000)
        report["refine"] = neighbours
        show(neighbours[:6], "refine (new seeds)")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=1, default=str))
    print("report:", REPORT.relative_to(ROOT))


def show(rows, title):
    print(f"\n== {title}")
    for r in rows:
        t = f"{r['x12_time']:.1f}/{r['x12_time_max']:.1f} s" if r["x12_time"] else "-"
        print(f"res {r['resources']:5.1f}  P(X12) {r['p_x12']:.2f}  P(X9) {r['p_x9']:.2f}  pts {r['points']:5.0f}  "
              f"problems {r['problems']:.2f}  X12 at {t}  {r['constants']}")


if __name__ == "__main__":
    main()
