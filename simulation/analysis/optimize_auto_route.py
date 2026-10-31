"""Route search for the pull-mode automatic stage (auto_pull_central.py), simulator only.

Each candidate PLAN (task order and parameters) is run headless in the 2D simulator for the 30 s
automatic stage. The score rewards central elements left completely on our side and penalises
what the rules and the field punish:

  score = balls + 1.5 * cones + 1.5 * bonus cubes (at most 2 count, p.30 d)
          - 3 * balls pushed to the opponent side       (R23 spirit: never feed the opponent)
          - 3 * props dropped across the centre line    (partly on the opponent side)
          - 20 * collisions with field structures       (fortress pushes excluded)
          - 20 * R06 penalties - 20 if moving at 30 s (R19)

Usage (from the repository root):
    .venv/bin/python simulation/analysis/optimize_auto_route.py            # default search
    .venv/bin/python simulation/analysis/optimize_auto_route.py --quick    # a few candidates
Writes simulation/analysis/results/auto_route_search.json (not committed), best first.
"""

import argparse
import contextlib
import io
import itertools
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELD2D = ROOT / "simulation" / "field2d"
PROGRAM = ROOT / "software" / "autonomous" / "task_execution" / "auto_pull_central.py"
REPORT = Path(__file__).resolve().parent / "results" / "auto_route_search.json"
SETTLE_S = 2.0               # balls settle after the stage (motors stopped)


def evaluate(plan: dict) -> dict:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    if str(FIELD2D) not in sys.path:
        sys.path.insert(0, str(FIELD2D))
    os.chdir(FIELD2D)
    import field_layout as fl
    from balls import load_intake
    from kinematics import load_drive_train
    from mechanisms import load_mechanisms
    from props import denial_count, load_gripper
    from robot import load_config, start_pose
    from simulation import Simulation, load_gyro_sign

    cfg = load_config()
    sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), 30, load_gyro_sign(),
                     ball_scenario="initial", intake=load_intake(), mechanisms=load_mechanisms(),
                     gripper=load_gripper())
    sim.program = PROGRAM
    sim.trace_options = plan
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        sim.run()
        while sim.running:
            sim.step(1 / 60)
        for _ in range(int(SETTLE_S * 60)):
            sim.world.step(1 / 60, sim.pose, (0, 0, 0), sim.mechanisms.position("intake_lift"), sim.dc)
    denial = denial_count(sim.props, sim.balls, "red")
    collisions = [(e["element"], e["part"], round(e["start"], 1), round(e["depth_mm"]))
                  for e in sim.collisions.collisions]
    moving = not (sim.monitor.auto_end or {}).get("stationary", False)
    error = sim._runner.error if sim._runner else None
    score = (denial["balls"] + 1.5 * denial["cones"] + 1.5 * min(denial["bonus"], 2)
             - 3 * denial["balls_opponent_side"] - 3 * denial["props_on_line"] - 20 * len(collisions)
             - 20 * sim.monitor.r06_penalties - 20 * moving - (100 if error else 0))
    return {"score": score, "plan": plan, "denial": denial, "collisions": collisions,
            "r06": sim.monitor.r06_penalties, "moving_at_30s": moving, "error": str(error) if error else None,
            "log": log.getvalue().strip().splitlines()}


def candidates(quick: bool):
    ua, ub, la, lb = "upper_a", "upper_b", "lower_a", "lower_b"
    orders = [[ua, ub, lb, la, "props_low_b"], [ub, ua, la, lb, "props_low_b"],
              [ua, ub, lb, "props_low_b", la], [la, lb, ua, ub, "props_low_b"]]
    speeds = [(150, 90, 60), (200, 90, 60), (200, 130, 60), (200, 130, 80)]
    lanes_x = [1720.0, 1800.0]
    tols = [1.0, 3.0]
    heights = [((300.0, 240.0), (90.0, 40.0)), ((290.0, 250.0), (85.0, 50.0))]
    if quick:
        orders, speeds, tols, heights = orders[:2], speeds[1:2], tols[1:], heights[:1]
    for order, (travel, approach, pull), x_far, tol, (up, low) in itertools.product(orders, speeds, lanes_x, tols, heights):
        yield {"tasks": order, "travel_speed": travel, "approach_speed": approach, "pull_out_speed": pull,
               "x_far": x_far, "x_in": 2100.0, "tol_cm": tol, "upper_heights": up, "lower_heights": low}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()
    plans = list(candidates(args.quick))
    print(f"{len(plans)} candidates, {args.workers} workers")
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(evaluate, plans))
    results.sort(key=lambda r: r["score"], reverse=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=1))
    for r in results[:8]:
        p = r["plan"]
        print(f"{r['score']:6.1f}  {r['denial']}  coll {len(r['collisions'])}  r06 {r['r06']}  "
              f"moving {r['moving_at_30s']}  speeds {p['travel_speed']}/{p['approach_speed']}/{p['pull_out_speed']}  "
              f"x {p['x_far']:.0f}  tol {p['tol_cm']:g}  heads {p['upper_heights']}/{p['lower_heights']}  {' '.join(p['tasks'])}")
    best = results[0]
    print("\nbest run log:\n  " + "\n  ".join(best["log"]))
    if best["collisions"]:
        print("best collisions:", best["collisions"])
    print("report:", REPORT.relative_to(ROOT))


if __name__ == "__main__":
    main()
