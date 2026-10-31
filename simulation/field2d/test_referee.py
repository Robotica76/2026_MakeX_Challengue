"""Referee actions, match score and the full-match strategy: python -m unittest (this directory)."""

import contextlib
import io
import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import field_layout as fl  # noqa: E402
import referee  # noqa: E402
from balls import load_intake  # noqa: E402
from kinematics import load_drive_train  # noqa: E402
from mechanisms import load_mechanisms  # noqa: E402
from props import load_gripper  # noqa: E402
from robot import load_config, start_pose  # noqa: E402
from simulation import Simulation, load_gyro_sign  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
MATCH = REPO / "simulation" / "control" / "match_2026.py"


def new_sim(seconds=130.0):
    cfg = load_config()
    return Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), seconds, load_gyro_sign(),
                      ball_scenario="initial", intake=load_intake(), mechanisms=load_mechanisms(),
                      gripper=load_gripper())


class ManualStageStartTest(unittest.TestCase):
    def test_bonus_balls_and_released_resource_balls(self):
        sim = new_sim()
        x12 = next(p for p in sim.props if p.label == "X12")
        x12.x, x12.y, x12.z = 1520.0, 340.0, 0.0                  # in red exchange area 1
        judged = referee.manual_stage_start(sim)
        self.assertEqual(judged["red"]["valid"], ["X12"])
        bonus = [b for b in sim.balls if b.name.startswith("red_bonus_ball")]
        self.assertEqual(len(bonus), 12)
        own = [b for b in sim.balls if b.name.startswith(("red_resource_", "blue_resource_"))]
        self.assertEqual(len(own), 40)
        self.assertTrue(all(b.z == 35.0 for b in own + bonus))    # all on the floor now
        area = fl.get(sim.elements, "red_resource_1")
        self.assertTrue(all(area.x - 200 <= b.x <= area.x + 200 and b.y > 318 for b in bonus))

    def test_score_counts_bonus_balls_double(self):
        sim = new_sim()
        sim.bonus_judged = {"red": {"valid": ["X6"], "bonus_balls": 6}}
        x0, y0, z0, x1, y1, z1 = referee.fortress_regions(sim.elements)["blue"]
        for i, b in enumerate(sim.balls[:9]):                      # 9 balls resting in the blue fortress
            b.x, b.y, b.z = x0 + 100 + 60 * i, (y0 + y1) / 2, 442.0
        score = referee.match_score(sim, "red")
        self.assertEqual(score["balls"], 9)
        self.assertEqual(score["precision"], 6 * 20 + 3 * 10)      # rules p.36, example 1


class WinningMatchTest(unittest.TestCase):
    def test_whole_match_in_our_half_with_the_flag(self):
        sim = new_sim(280.0)
        self.addCleanup(sim.reset)
        sim.program = MATCH
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sim.run()
            while sim.running:
                sim.step(1 / 60)
        self.assertEqual(sim.state.status, "done", out.getvalue())
        self.assertEqual(sim.bonus_judged["red"]["valid"], ["X12"], out.getvalue())
        self.assertTrue(sim.monitor.auto_end["stationary"])                   # R19 at 30 s
        self.assertEqual(sim.monitor.r06_penalties, 0)
        self.assertEqual(sim.collisions.collisions, [], out.getvalue())
        self.assertEqual(sim.half.events, [], out.getvalue())                 # never in the partner half
        self.assertTrue(sim.modification["in_start_area"])                    # taken out for the modification
        self.assertEqual((sim.flag.state, sim.flag.pole, sim.flag.touching), ("hung", "red_flag_2", False))
        self.assertLess(sim.flag.hung_at - referee.FINAL_START_S, 15.0)       # flag in the first 15 s
        score = referee.match_score(sim, "red")
        self.assertEqual(score["flag"], 50)
        self.assertGreaterEqual(score["balls"], 10, out.getvalue())
        self.assertGreaterEqual(score["total"], 250)


class FlagTest(unittest.TestCase):
    def test_rod_must_be_over_the_pole_and_lowered(self):
        from flag import load_flag
        from robot import RobotPose
        f = load_flag("red")
        f.state = "carried"
        far = RobotPose(700.0, 1204.0, 3.14159265)
        f.update(1.0, far, 160.0)                                             # low, but not over the pole
        self.assertEqual(f.state, "carried")
        over = RobotPose(330.0, 1204.0, 3.14159265)                          # facing the wall, rod on the left
        f.update(2.0, over, 230.0)                                            # over it, rod above the pole
        self.assertEqual(f.state, "carried")
        f.update(3.0, over, 160.0)                                            # lowered onto it
        self.assertEqual((f.state, f.pole), ("hung", "red_flag_2"))
        self.assertEqual(f.points, 0)                                         # still on the robot
        f.update(4.0, RobotPose(1100.0, 1204.0, 3.14159265), 160.0)         # holder clear of the flag
        self.assertEqual(f.points, 50)


if __name__ == "__main__":
    unittest.main()
