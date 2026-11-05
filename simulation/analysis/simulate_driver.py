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


def play(seconds=280.0, program=PROGRAM, delay_frames=0, every=2, opponent_x_at=None):
    """delay_frames: the driver sees the state this many 1/60 s frames late (the viewer's stream);
    opponent_x_at: match time when a (simulated) opponent shot turns the X mark blue."""
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
    k, queue = 0, []
    with contextlib.redirect_stdout(io.StringIO()):
        sim.run()
        while sim.running:
            sim.step(1 / 60)
            k += 1
            if opponent_x_at is not None and sim.world and opponent_x_at <= sim.time < opponent_x_at + 0.02:
                sim.world.x_mark_state = "blue"
            if k % every == 0:
                vx, vy, w = sim._velocity
                state = {"t": sim.time, "pose": {"x_mm": sim.pose.x, "y_mm": sim.pose.y,
                                                 "theta_deg": math.degrees(sim.pose.theta)},
                         "velocity": {"vx_mm_s": vx, "vy_mm_s": vy, "omega_deg_s": math.degrees(w)},
                         "stored": sim.world.stored if sim.world else 0,
                         "intake_lift_mm": sim.mechanisms.position("intake_lift"),
                         "score": referee.match_score(sim, "red")["total"],
                         "flag": sim.flag.state if sim.flag else None,
                         "x_mark": sim.world.x_mark_state if sim.world else None,
                         "carriage_mm": sim.mechanisms.position("elevator"),
                         "jaw_mm": sim.mechanisms.position("gripper_jaw"),
                         "held": sim.gripper.held.kind if sim.gripper and sim.gripper.held else None,
                         "cones": [{"x_mm": p.x, "y_mm": p.y, "z_mm": p.z, "post": p.on_post}
                                   for p in sim.props if p.kind == "cone"],
                         "letters": [{"label": p.label, "x_mm": p.x, "y_mm": p.y, "z_mm": p.z, "held": p.held}
                                     for p in sim.props if p.kind == "letter" and p.alliance == "red"],
                         "fortress": dict(sim.fortresses.offsets)}
                queue.append(state)
                if len(queue) > max(1, delay_frames // every):
                    for ev in driver.tick(queue.pop(0)):
                        sim.gamepad.apply_event(ev)
    return sim, driver, referee.match_score(sim, "red")


def main():
    delay = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    opponent = float(sys.argv[2]) if len(sys.argv) > 2 else None    # e.g. 50: opponent turns the X at 50 s
    sim, driver, score = play(delay_frames=delay, opponent_x_at=opponent)
    print("\n".join(driver.log))
    print("\nend:", sim.state.status, sim.state.message)
    print("collisions:", [(e["element"], e["part"], round(e["start"], 1)) for e in sim.collisions.collisions] or "none")
    print("partner half:", sim.half.report() or "never", "| R06:", sim.monitor.r06_penalties,
          "| R19:", sim.monitor.report()[:1], "| modification:", sim.modification)
    print("bonus:", sim.bonus_judged and sim.bonus_judged["red"], "| flag:", sim.flag and sim.flag.state)
    print("SCORE:", score)


if __name__ == "__main__":
    main()
