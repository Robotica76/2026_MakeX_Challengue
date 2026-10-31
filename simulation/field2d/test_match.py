"""Match clock, rule monitors and the automatic routine: python -m unittest (this directory)."""

import contextlib
import io
import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import field_layout as fl
from balls import load_intake
from kinematics import load_drive_train
from match import STAGES, MatchMonitor, format_clock, stage_at
from mechanisms import load_mechanisms
from props import load_gripper, score_preview
from robot import RobotPose, load_config, start_pose
from simulation import Simulation, load_gyro_sign

REPO = Path(__file__).resolve().parents[2]
AUTO = REPO / "software" / "autonomous" / "task_execution" / "auto_central_then_cubes.py"


class ClockTest(unittest.TestCase):
    def test_stages_follow_the_rules(self):
        self.assertEqual([s for s, _ in STAGES], ["automatic", "manual", "modification", "final"])
        self.assertEqual(sum(t for _, t in STAGES), 280.0)          # 4 min 40 s (p.9)
        self.assertEqual(stage_at(0.0)[:2], ("automatic", 30.0))
        self.assertEqual(stage_at(29.9)[0], "automatic")
        self.assertEqual(stage_at(30.0)[0], "manual")
        self.assertEqual(stage_at(130.0)[0], "modification")
        self.assertEqual(stage_at(190.0)[0], "final")
        self.assertEqual(stage_at(280.0)[0], "ended")

    def test_format(self):
        self.assertEqual(format_clock(23.44), "0:23.4")
        self.assertEqual(format_clock(95.0), "1:35.0")
        self.assertEqual(format_clock(-3), "0:00.0")


class MonitorTest(unittest.TestCase):
    def test_r19_stationary_or_moving_at_30_s(self):
        pose = RobotPose(1000.0, 1000.0, 0.0)
        still = MatchMonitor("red")
        still.update(29.99, 0.02, pose, (0.0, 0.0, 0.0), False)
        self.assertTrue(still.auto_end["stationary"])
        moving = MatchMonitor("red")
        moving.update(29.99, 0.02, pose, (100.0, 0.0, 0.0), False)
        self.assertFalse(moving.auto_end["stationary"])
        lifting = MatchMonitor("red")
        lifting.update(29.99, 0.02, pose, (0.0, 0.0, 0.0), True)
        self.assertFalse(lifting.auto_end["stationary"])
        self.assertIn("MOVING", lifting.report()[0])

    def test_r06_body_outside_counts_and_penalises_after_3_s(self):
        m = MatchMonitor("red")
        lo, hi = m.limits()
        self.assertEqual(hi, fl.CX - fl.STRATEGY_W / 2)              # 2220 mm
        head_only = RobotPose(hi - 115.0 - 1.0, 1500.0, 0.0)        # intake head overhangs: allowed
        m.update(1.0, 0.01, head_only, (0, 0, 0), False)
        self.assertEqual(m.r06_events, [])
        body_out = RobotPose(hi - 100.0, 1500.0, 0.0)               # body 15 mm over the line
        t = 2.0
        while t < 5.5:
            m.update(t, 0.01, body_out, (0, 0, 0), False)
            t += 0.01
        self.assertEqual(len(m.r06_events), 1)
        self.assertTrue(m.r06_events[0]["penalty"])
        m.update(t, 0.01, head_only, (0, 0, 0), False)
        self.assertEqual(m.outside_s, 0.0)
        self.assertEqual(m.r06_penalties, 1)


class OnCycleTest(unittest.TestCase):
    def test_drive_calls_on_cycle(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        prog = Path(tmp.name) / "prog.py"
        prog.write_text("import chassis as ch\ncount = [0]\n"
                        "def f():\n    count[0] += 1\n"
                        "ch.odo.calibrate(0.2)\nch.odo.reset()\n"
                        "ch.drive(forward_cm=20, on_cycle=f)\nch.turn(30, on_cycle=f)\n"
                        "print('cycles', count[0])\n")
        cfg = load_config()
        sim = Simulation(cfg, RobotPose(1500.0, 1500.0, 0.0), load_drive_train(), 10, load_gyro_sign())
        sim.program = prog
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sim.run()
            while sim.running and not sim._runner.finished:
                sim.step(1 / 60)
        self.assertIsNone(sim._runner.error)
        self.assertGreater(int(out.getvalue().split("cycles")[-1]), 50)


class AutomaticRoutineTest(unittest.TestCase):
    def test_central_balls_then_x12_bonus_cube_stops_in_time(self):
        cfg = load_config()
        sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), 30, load_gyro_sign(),
                         ball_scenario="initial", intake=load_intake(), mechanisms=load_mechanisms(),
                         gripper=load_gripper())
        sim.program = AUTO
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sim.run()
            while sim.running:
                sim.step(1 / 60)
        text = out.getvalue()
        self.assertIsNone(sim._runner.error if sim._runner else None, text)
        self.assertEqual(sim.state.status, "done")
        self.assertNotIn("MISSED", text)
        self.assertIn("stopped", text)
        upper = sum(b.collected for b in sim.balls if b.name.startswith("central") and int(b.name.split("_")[-1]) >= 15)
        self.assertGreaterEqual(upper, 13)                            # two passes on the upper level
        self.assertTrue(sim.monitor.auto_end["stationary"])           # R19
        self.assertEqual(sim.monitor.r06_penalties, 0)                # body never 3 s outside
        bonus = score_preview(sim.props, sim.elements, "red")["bonus"]
        self.assertEqual(bonus["valid"], ["X12"])                     # in exchange area 1 at 30 s
        self.assertEqual(bonus["bonus_balls"], 12)


if __name__ == "__main__":
    unittest.main()
