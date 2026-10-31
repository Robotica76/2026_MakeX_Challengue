"""Play a whole match (automatic, manual, modification, final: 280 s) headless; print the timeline and score.

    .venv/bin/python simulation/analysis/simulate_match.py
    .venv/bin/python simulation/analysis/simulate_match.py --program simulation/control/match_2026.py

The program runs in the 2D simulator with the rules' initial ball state; at 30 s the referee
exchanges the valid bonus cubes and the observers release the own resource balls; at 130 s the
robot must be partly in its starting area and comes back with the flag mast (referee.py). The
score follows the rules guide table (p.53-54); pins and the X mark are not simulated.
"""

import argparse
import contextlib
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELD2D = ROOT / "simulation" / "field2d"
DEFAULT = ROOT / "simulation" / "control" / "match_2026.py"


def play(program: Path, seconds: float = 280.0, options=None):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    sys.path.insert(0, str(FIELD2D))
    import field_layout as fl
    import referee
    from balls import load_intake
    from kinematics import load_drive_train
    from mechanisms import load_mechanisms
    from props import load_gripper
    from robot import load_config, start_pose
    from simulation import Simulation, load_gyro_sign

    cfg = load_config()
    sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), seconds, load_gyro_sign(),
                     ball_scenario="initial", intake=load_intake(), mechanisms=load_mechanisms(),
                     gripper=load_gripper())
    sim.program = Path(program).resolve()
    sim.trace_options = dict(options or {})
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        sim.run()
        while sim.running:
            sim.step(1 / 60)
    return sim, log.getvalue(), referee.match_score(sim, "red")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--program", type=Path, default=DEFAULT)
    ap.add_argument("--seconds", type=float, default=280.0)
    ap.add_argument("--strategy", help="automatic strategy for match_2026.py (bonus, balls, mixed, props)")
    ap.add_argument("--compare", action="store_true", help="score every automatic strategy with the same manual stage")
    args = ap.parse_args()
    if args.compare:
        for name in ("bonus", "mixed", "balls", "props"):
            _, _, score = play(args.program, args.seconds, {"strategy": name})
            print(f"{name:6s} total {score['total']:4d}  balls in {score['balls']:2d}  bonus {score['bonus_cubes'] or '-'}")
        return
    sim, log, score = play(args.program, args.seconds, {"strategy": args.strategy} if args.strategy else None)
    print(log.rstrip())
    print(f"\nend: {sim.state.status} ({sim.state.message})")
    print("collisions:", [(e["element"], e["part"], round(e["start"], 1)) for e in sim.collisions.collisions] or "none")
    print("R06 penalties:", sim.monitor.r06_penalties, "| R19:", sim.monitor.report()[:1])
    print("bonus judged at 30 s:", sim.bonus_judged and sim.bonus_judged["red"])
    print("modification stage at 130 s:", sim.modification)
    print("own half:", (sim.half.report() or ["never crossed"]) if sim.half else "not set")
    if sim.flag:
        print(f"flag: {sim.flag.state} on {sim.flag.pole} at {sim.flag.hung_at and round(sim.flag.hung_at, 1)} s, "
              f"touching robot {sim.flag.touching}")
    w = sim.world
    print(f"balls shot {w.shots}, in the blue fortress now {score['balls']}")
    print("SCORE red:", score)


if __name__ == "__main__":
    main()
