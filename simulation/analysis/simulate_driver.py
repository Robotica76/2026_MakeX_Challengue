"""Headless match: the competition program driven by the scripted driver (ai_driver.py).

    .venv/bin/python simulation/analysis/simulate_driver.py            # 280 s, prints the driver log
The driver gets the same state the viewer streams (pose, time, balls inside, score, flag) at 30 Hz.
"""

import contextlib
import io
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "simulation" / "field2d"))
sys.path.insert(0, str(ROOT / "simulation" / "control"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

PROGRAM = ROOT / "software" / "robot" / "main" / "storm_breaker_2026.py"


def play(seconds=280.0, program=PROGRAM):
    import field_layout as fl
    import referee
    from ai_driver import Driver
    from balls import load_intake
    from kinematics import load_drive_train
    from mechanisms import load_mechanisms
    from props import load_gripper
    from robot import load_config, start_pose
    from simulation import Simulation, load_gyro_sign
    cfg = load_config()
    sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), seconds, load_gyro_sign(),
                     ball_scenario="initial", intake=load_intake(), mechanisms=load_mechanisms(), gripper=load_gripper())
    sim.program = Path(program)
    driver = Driver()
    k = 0
    with contextlib.redirect_stdout(io.StringIO()):
        sim.run()
        while sim.running:
            sim.step(1 / 60)
            k += 1
            if k % 2 == 0:
                state = {"t": sim.time, "pose": {"x_mm": sim.pose.x, "y_mm": sim.pose.y,
                                                 "theta_deg": math.degrees(sim.pose.theta)},
                         "stored": sim.world.stored if sim.world else 0,
                         "score": referee.match_score(sim, "red")["total"],
                         "flag": sim.flag.state if sim.flag else None}
                for ev in driver.tick(state):
                    sim.gamepad.apply_event(ev)
    return sim, driver, referee.match_score(sim, "red")


def main():
    sim, driver, score = play()
    print("\n".join(driver.log))
    print("\nend:", sim.state.status, sim.state.message)
    print("collisions:", [(e["element"], e["part"], round(e["start"], 1)) for e in sim.collisions.collisions] or "none")
    print("partner half:", sim.half.report() or "never", "| R06:", sim.monitor.r06_penalties,
          "| R19:", sim.monitor.report()[:1], "| modification:", sim.modification)
    print("bonus:", sim.bonus_judged and sim.bonus_judged["red"], "| flag:", sim.flag and sim.flag.state)
    print("SCORE:", score)


if __name__ == "__main__":
    main()
