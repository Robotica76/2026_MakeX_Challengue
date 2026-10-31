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
    def test_bonus_automatic_and_manual_cycles(self):
        sim = new_sim()
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
        score = referee.match_score(sim, "red")
        self.assertGreaterEqual(score["balls"], 14, out.getvalue())
        self.assertGreaterEqual(score["total"], 260)


if __name__ == "__main__":
    unittest.main()
