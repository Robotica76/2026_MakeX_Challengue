"""Monte Carlo search of the automatic-stage route: every order of the missions (storm_breaker_2026.py
ORDER digits), then the best ones played as whole matches with the scripted driver.

Missions: 1 X12 into red exchange area 1 (bonus: 12 extra balls worth 20), 2 X9 and cone a to our
side (denial), 3 central table balls, lower level, 4 upper level (taken in; the robot shoots them at
the blue fortress before parking). A mission that does not fit before END_BY is left out by the
program. 64 orders (every subset in every order) run on N sampled robots each
(montecarlo_config_competition.json: calibrated robot, start jig; props within +-5 mm); common
random numbers: the same seeds for every order.

Stage 1 (automatic stage, 31 s) ranks the orders by the points the automatic stage makes or makes
possible:
  value = 20 x balls scored in the stage if the X12 is valid, else 10 x  (precision throwing)
        + 120 if the X12 is valid (12 bonus balls x 10 extra, they need the manual stage)
        + 45 if the X9 is ours (an X9 the opponent cannot use: 9 x 5, estimate)
        + 10 per cone on our side (20 if hung later, estimate half)
        - 20 per rule problem (collision, R06, R19, R26, prop across the line, > 2 bonus cubes)
  the time in the partner half (team rule: two robots per alliance) is reported, not penalised.
Stage 2 plays the best `--matches` orders as 280 s matches (simulate_driver.play) at several driver
delays and ranks them by the match score.

    .venv/bin/python simulation/analysis/montecarlo_routes.py --trials 6 --matches 6
Writes simulation/analysis/results/montecarlo_routes.json.
"""

import argparse
import contextlib
import io
import itertools
import json
import math
import os
import random
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIELD2D = ROOT / "simulation" / "field2d"
CONTROL = ROOT / "simulation" / "control"
sys.path.insert(0, str(HERE))
from montecarlo_strategy import CONFIG, jitter_props, program_text  # noqa: E402

REPORT = HERE / "results" / "montecarlo_routes.json"
NAMES = {1: "bonus X12", 2: "deny X9+cone", 3: "balls low", 4: "balls high"}


def orders():
    """Every subset of the missions in every order (64), as ORDER integers; 0 = do nothing."""
    out = [0]
    for k in range(1, 5):
        for perm in itertools.permutations((1, 2, 3, 4), k):
            out.append(int("".join(map(str, perm))))
    return out


def describe(order: int) -> str:
    return " > ".join(NAMES[int(d)] for d in str(order)) if order else "nothing (park)"


def _sim(seed, seconds, program):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    for path in (FIELD2D, CONTROL):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    import field_layout as fl
    from balls import load_intake
    from kinematics import load_drive_train
    from mechanisms import load_mechanisms
    from props import load_gripper
    from robot import RobotPose, load_config, start_pose
    from simulation import Simulation, load_gyro_sign
    from uncertainty import Variation, sample_variation
    drive = load_drive_train()
    ranges = json.loads(CONFIG.read_text())["ranges"]
    var = sample_variation(ranges, seed, tuple(drive.motors)) if seed >= 0 else Variation()
    cfg = load_config()
    s0 = start_pose(cfg, fl.build_field())
    start = RobotPose(s0.x + var.start_dx_mm, s0.y + var.start_dy_mm, s0.theta + math.radians(var.start_dtheta_deg))
    sim = Simulation(cfg, start, drive, seconds, load_gyro_sign(), variation=var, ball_scenario="initial",
                     intake=load_intake(), mechanisms=load_mechanisms(), gripper=load_gripper())
    sim.program = program
    return sim


def auto_trial(job):
    """job = (order, seed): the automatic stage; returns its outcome."""
    order, seed = job
    folder = Path(tempfile.mkdtemp())
    program = folder / "storm_breaker_routes.py"
    program.write_text(program_text({"ORDER": order}), encoding="utf-8")
    sim = _sim(seed, 31.0, program)
    import referee
    from props import denial_count
    with contextlib.redirect_stdout(io.StringIO()):
        sim.run()
        jitter_props(sim, seed)
        sim.gamepad.apply_event({"event": "press", "control": "button_1"})
        k = 0
        while sim.running:
            sim.step(1 / 60)
            k += 1
            if k == 15:
                sim.gamepad.apply_event({"event": "release", "control": "button_1"})
    error = sim._runner.error if sim._runner else None
    denial = denial_count(sim.props, sim.balls, "red")
    judged = (sim.bonus_judged or {}).get("red", {"valid": [], "bonus_balls": 0, "on_side": 0})
    valid12 = "X12" in judged["valid"]
    x9_ours = any(p.label == "X9" and p.x + 60 <= 2220 for p in sim.props)
    scored = referee.balls_scored(sim, "red")
    problems = (len(sim.collisions.collisions) + sim.monitor.r06_penalties
                + (0 if (sim.monitor.auto_end or {}).get("stationary") else 1)
                + denial["props_on_line"] + len(sim.channels.events)
                + (1 if judged.get("on_side", 0) > 2 else 0) + (1 if error and "Time limit" not in str(error) else 0))
    value = ((20 if valid12 else 10) * scored + 120 * valid12 + 45 * (x9_ours and valid12)
             + 10 * denial["cones"] - 20 * problems)
    try:
        program.unlink()
        folder.rmdir()
    except OSError:
        pass
    return {"order": order, "seed": seed, "value": value, "valid_x12": valid12, "x9_ours": x9_ours,
            "cones": denial["cones"], "taken": sim.world.captured if sim.world else 0, "scored": scored,
            "problems": problems, "half_s": round(sim.half.seconds, 1) if sim.half else 0.0,
            "collisions": [e["element"] for e in sim.collisions.collisions],
            "x_mark": sim.world.x_mark_state if sim.world else None,
            "error": str(error) if error and "Time limit" not in str(error) else None}


def match_trial(job):
    """job = (order, delay_frames): a whole match with the scripted driver."""
    order, delay = job
    folder = Path(tempfile.mkdtemp())
    program = folder / "storm_breaker_routes.py"
    program.write_text(program_text({"ORDER": order}), encoding="utf-8")
    import simulate_driver
    with contextlib.redirect_stdout(io.StringIO()):
        sim, driver, score = simulate_driver.play(program=program, delay_frames=delay)
    try:
        program.unlink()
        folder.rmdir()
    except OSError:
        pass
    keep = ("total", "precision", "bonus_cubes", "cones", "letter_cubes", "flag", "x_mark", "penalties")
    return {"order": order, "delay": delay, **{k: score[k] for k in keep},
            "collisions": len(sim.collisions.collisions), "half_s": round(sim.half.seconds, 1)}


def summarize(rows, key):
    out = {}
    for r in rows:
        out.setdefault(r["order"], []).append(r)
    table = []
    for order, rs in out.items():
        n = len(rs)
        mean = {k: sum(r[k] for r in rs) / n for k in key}
        table.append({"order": order, "route": describe(order), "n": n, **{k: round(v, 2) for k, v in mean.items()},
                      "min_" + key[0]: min(r[key[0]] for r in rs)})
    table.sort(key=lambda r: -r[key[0]])
    return table


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--trials", type=int, default=6, help="sampled robots per order (stage 1)")
    ap.add_argument("--matches", type=int, default=6, help="best orders played as whole matches (stage 2)")
    ap.add_argument("--delays", default="0,4,8", help="driver delays (frames, 2 or less are the same)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()
    jobs = [(o, 1000 + i) for o in orders() for i in range(args.trials)]
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(auto_trial, jobs, chunksize=1))
    auto = summarize(rows, ["value", "scored", "taken", "valid_x12", "x9_ours", "cones", "problems", "half_s"])
    print(f"== stage 1: automatic stage, {len(orders())} orders x {args.trials} robots")
    for r in auto[:15]:
        print(f"{r['value']:6.1f} (min {r['min_value']:4.0f})  scored {r['scored']:4.1f}  taken {r['taken']:4.1f}  "
              f"X12 {r['valid_x12']:.2f}  X9 {r['x9_ours']:.2f}  cones {r['cones']:.1f}  problems {r['problems']:.2f}  "
              f"partner half {r['half_s']:4.1f} s  {r['order']:>4}  {r['route']}")
    best = [r["order"] for r in auto[:args.matches]]
    delays = [int(d) for d in args.delays.split(",")]
    with ProcessPoolExecutor(args.workers) as pool:
        mrows = list(pool.map(match_trial, [(o, d) for o in best for d in delays], chunksize=1))
    match = summarize(mrows, ["total", "precision", "cones", "letter_cubes", "flag", "x_mark", "penalties",
                              "collisions", "half_s"])
    print(f"\n== stage 2: whole matches (scripted driver, delays {delays})")
    for r in match:
        print(f"{r['total']:6.1f} (min {r['min_total']:4.0f})  precision {r['precision']:5.1f}  cones {r['cones']:4.1f}  "
              f"letters {r['letter_cubes']:4.1f}  flag {r['flag']:4.1f}  X {r['x_mark']:4.1f}  pen {r['penalties']:4.1f}  "
              f"coll {r['collisions']:.1f}  {r['order']:>4}  {r['route']}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"auto": auto, "auto_rows": rows, "match": match, "match_rows": mrows}, indent=1))
    print("report:", REPORT.relative_to(ROOT))


if __name__ == "__main__":
    main()
