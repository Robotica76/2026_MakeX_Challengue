"""Mechanism (elevator, intake lift, rollers) checks: python -m unittest (this directory)."""

import contextlib
import io
import unittest
from pathlib import Path

import field_layout as fl
from balls import BALL_D, Ball, load_intake
from kinematics import load_drive_train
from mblock_runtime import DCBus
from mechanisms import Linear, Mechanisms, Spinner, load_mechanisms
from robot import RobotPose, load_config, start_pose
from simulation import Simulation, load_gyro_sign

CONTROL = Path(__file__).resolve().parents[1] / "control"


class MechanismModelTest(unittest.TestCase):
    def test_linear_moves_with_power_and_clamps(self):
        m = Linear("DC3", travel_mm=358, speed_mm_s=150)
        m.step(100, 1.0)
        self.assertAlmostEqual(m.position, 150)
        m.step(50, 1.0)
        self.assertAlmostEqual(m.position, 225)
        m.step(100, 10.0)
        self.assertEqual(m.position, 358)       # top stop
        m.step(-100, 10.0)
        self.assertEqual(m.position, 0)         # bottom stop
        m.direction = -1
        m.step(-100, 1.0)
        self.assertAlmostEqual(m.position, 150)

    def test_spinner_angle(self):
        s = Spinner("DC1", rpm=200)
        s.step(50, 0.5)                          # 100 rpm for 0.5 s = 300 deg
        self.assertAlmostEqual(s.angle, 300)
        s.reset()
        self.assertEqual(s.angle, 0)

    def test_config(self):
        mech = load_mechanisms()
        self.assertEqual(set(mech.linear), {"elevator", "intake_lift", "gripper_jaw"})
        self.assertEqual(mech.linear["elevator"].travel_mm, 358.0)      # v22 CAD
        self.assertEqual(mech.linear["elevator"].port, "DC3")
        self.assertEqual(set(mech.spinners), {"intake_rollers", "tower", "feeder", "shooter"})
        self.assertEqual(mech.spinners["intake_rollers"].port, load_intake().port)

    def test_step_reads_the_dc_bus(self):
        mech = Mechanisms({"lift": Linear("DC2", 100, 50)}, {"roll": Spinner("DC1", 60)})
        dc = DCBus()
        dc.set("DC2", 100)
        dc.set("DC1", -100)
        mech.step(dc, 1.0)
        self.assertEqual(mech.position("lift"), 50)
        self.assertEqual(mech.angle("roll"), -360)
        self.assertEqual(mech.position("missing", 7.0), 7.0)


class MechanismSimulationTest(unittest.TestCase):
    def make(self, program=None, **kw):
        cfg = load_config()
        sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), 30, load_gyro_sign(),
                         mechanisms=load_mechanisms(), **kw)
        if program:
            sim.program = program
        return sim

    def test_demo_program_moves_every_mechanism(self):
        sim = self.make(CONTROL / "test_mechanisms.py")
        peaks = {"elevator": 0.0, "intake_lift": 0.0}
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sim.run()
            for _ in range(60 * 20):
                sim.step(1 / 60)
                for name in peaks:
                    peaks[name] = max(peaks[name], sim.mechanisms.position(name))
                if not sim.running or sim._runner.finished:
                    break
        self.assertIn("done", out.getvalue(), sim.state.message)
        self.assertAlmostEqual(peaks["elevator"], 358.0, delta=0.5)        # reached the top
        self.assertAlmostEqual(peaks["intake_lift"], 212.0, delta=3.0)     # 4 s at 53 mm/s
        self.assertEqual(sim.mechanisms.position("elevator"), 0.0)        # and back down
        self.assertEqual(sim.mechanisms.position("intake_lift"), 0.0)
        for name in ("intake_rollers", "tower", "feeder", "shooter"):
            self.assertGreater(abs(sim.mechanisms.angle(name)), 1000, name)
        sim.reset()
        self.assertEqual(sim.mechanisms.angle("shooter"), 0.0)

    def test_intake_reach_follows_the_head(self):
        sim = self.make(ball_scenario="none", intake=load_intake())
        pose = RobotPose(1000.0, 1000.0, 0.0)
        sim.pose = pose
        floor = Ball("floor", pose.x + 240, pose.y - 50, BALL_D / 2)
        shelf = Ball("shelf", pose.x + 240, pose.y + 50, 285.0)       # central upper level centre
        sim.balls = [floor, shelf]
        sim.dc.set("DC1", 80)                                   # rollers on
        sim.state.status = "running"                            # step without a program
        sim.state.trail = [(pose.x, pose.y)]
        sim._runner = None
        sim.time_limit = 0
        sim.mechanisms.linear["intake_lift"].position = 255.0   # head up: shelf only
        sim.step(0.05)
        self.assertEqual((floor.collected, shelf.collected), (False, True))
        sim.mechanisms.linear["intake_lift"].position = 0.0     # head down: floor
        sim.step(0.05)
        self.assertTrue(floor.collected)

if __name__ == "__main__":
    unittest.main()
