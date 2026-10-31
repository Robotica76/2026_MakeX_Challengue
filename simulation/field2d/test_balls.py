"""Balls, intake and power expansion board checks: python -m unittest (this directory)."""

import contextlib
import io
import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import field_layout as fl
from balls import BALL_D, Ball, Intake, field_balls, load_intake
from kinematics import load_drive_train
from mblock_runtime import DCBus, MotorBus, ProgramRunner, SimClock
from robot import RobotPose, load_config, start_pose
from simulation import Simulation, load_gyro_sign

CONTROL = Path(__file__).resolve().parents[1] / "control"


class ScenarioTest(unittest.TestCase):
    def test_counts_follow_the_rules(self):
        elements = fl.build_field()
        self.assertEqual(field_balls(elements, "none"), [])
        for scenario in ("initial", "released"):
            balls = field_balls(elements, scenario)
            self.assertEqual(len(balls), 70)   # p.26: 10 per own resource area x4, 15 per central level x2
            self.assertEqual(sum(b.name.startswith("central") for b in balls), 30)
            self.assertEqual(len({b.name for b in balls}), 70)

    def test_initial_balls_are_on_the_shelf_released_on_the_floor(self):
        elements = fl.build_field()
        own = [b for b in field_balls(elements, "initial") if "_resource_" in b.name]
        self.assertTrue(all(b.z == 758.5 + BALL_D / 2 for b in own))
        released = [b for b in field_balls(elements, "released") if "_resource_" in b.name]
        self.assertTrue(all(b.z == BALL_D / 2 for b in released))
        for b in released:          # in front of the resource box, inside the field
            self.assertTrue(0 < b.y < fl.FIELD_H and (b.y > 318 + BALL_D / 2 or b.y < fl.FIELD_H - 318 - BALL_D / 2))

    def test_unknown_scenario(self):
        with self.assertRaises(ValueError):
            field_balls(fl.build_field(), "everywhere")


class IntakeTest(unittest.TestCase):
    def setUp(self):
        self.intake = Intake()
        self.pose = RobotPose(1000.0, 1000.0, 0.0)   # facing +x

    def ball(self, fx, ly, z=BALL_D / 2):
        return Ball("b", self.pose.x + fx, self.pose.y + ly, z)

    def test_collects_in_front_only_when_running(self):
        b = self.ball(240, 0)
        self.assertEqual(self.intake.update(self.pose, [b], power=10), 0)   # below min_power
        self.assertEqual(self.intake.update(self.pose, [b], power=80), 1)
        self.assertTrue(b.collected)
        self.assertEqual(self.intake.update(self.pose, [b], power=80), 0)   # not twice

    def test_zone_edges_height_and_reverse(self):
        balls = [self.ball(240, 0), self.ball(-240, 0), self.ball(240, 250), self.ball(240, 0, z=85)]
        self.intake.update(self.pose, balls, power=80)
        self.assertEqual([b.collected for b in balls], [True, False, False, False])
        self.intake.reset()
        b = self.ball(240, 0)
        self.assertEqual(self.intake.update(self.pose, [b], power=-80), 0)  # reversed: ejecting

    def test_zone_turns_with_the_robot(self):
        pose = RobotPose(1000.0, 1000.0, math.pi / 2)   # facing +y
        b = Ball("b", 1000.0, 1240.0, BALL_D / 2)
        self.assertEqual(self.intake.update(pose, [b], power=80), 1)

    def test_capacity(self):
        intake = Intake(capacity=2)
        balls = [self.ball(240, y) for y in (-100, 0, 100)]
        intake.update(self.pose, balls, power=80)
        self.assertEqual(sum(b.collected for b in balls), 2)

    def test_config(self):
        intake = load_intake()
        self.assertEqual(intake.port, "DC1")
        self.assertEqual(intake.capacity, 18)


class PowerExpandBoardTest(unittest.TestCase):
    def test_program_sets_and_stops_dc_ports(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "prog.py"
        path.write_text("from mbuild import power_expand_board\nimport time\n"
                        "power_expand_board.set_power('DC1', 150)\ntime.sleep(0.1)\n"
                        "power_expand_board.set_power('DC2', -40)\npower_expand_board.stop('DC1')\n")
        clock, dc = SimClock(), DCBus()
        runner = ProgramRunner(path, clock, MotorBus(580), dc=dc)
        runner.start()
        clock.sync()
        self.assertEqual(dc.power("DC1"), 100.0)        # clamped to 100 %
        clock.advance(0.1)
        clock.sync()
        runner.stop()
        self.assertIsNone(runner.error)
        self.assertEqual(dc.snapshot(), {"DC1": 0.0, "DC2": -40.0})


class BallCollectionProgramTest(unittest.TestCase):
    def test_collection_demo_fills_the_intake(self):
        cfg = load_config()
        sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), 100, load_gyro_sign(),
                         ball_scenario="released", intake=load_intake())
        sim.program = CONTROL / "test_ball_collection.py"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sim.run()
            for _ in range(60 * 40):
                sim.step(1 / 60)
                if not sim.running or (sim._runner and sim._runner.finished):
                    break
        self.assertIn("done", out.getvalue(), out.getvalue() + sim.state.message)
        self.assertNotIn("MISSED", out.getvalue())
        self.assertNotEqual(sim.state.status, "out_of_bounds", sim.state.message)
        by_area = {a: sum(b.collected and b.name.startswith(a) for b in sim.balls)
                   for a in ("red_resource_1", "red_resource_2")}
        self.assertEqual(by_area["red_resource_1"], 10)
        self.assertEqual(sim.balls_collected, 18)        # capacity reached on the second pass
        sim.reset()
        self.assertEqual(sim.balls_collected, 0)
        self.assertFalse(any(b.collected for b in sim.balls))


class ShelfProgramTest(unittest.TestCase):
    def test_shelf_demo_takes_the_upper_level_without_the_body_entering_the_table(self):
        from mechanisms import load_mechanisms
        cfg = load_config()
        intake = load_intake()
        sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), 100, load_gyro_sign(),
                         ball_scenario="initial", intake=intake, mechanisms=load_mechanisms())
        sim.program = CONTROL / "test_intake_shelf.py"
        table = fl.get(fl.build_field(), "central_resource")
        max_body_x = 0.0
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sim.run()
            for _ in range(60 * 45):
                sim.step(1 / 60)
                max_body_x = max(max_body_x, sim.pose.x + intake.body_front_mm)   # heading stays 0
                if not sim.running or sim._runner.finished:
                    break
        self.assertIn("done", out.getvalue(), sim.state.message)
        self.assertNotIn("MISSED", out.getvalue())
        upper = [b for b in sim.balls if b.name.startswith("central") and b.z > 200]
        lower = [b for b in sim.balls if b.name.startswith("central") and b.z < 200]
        self.assertEqual(sum(b.collected for b in upper), 15)
        self.assertEqual(sum(b.collected for b in lower), 0)
        self.assertLessEqual(max_body_x, table.x - table.w / 2)                  # body stays out of the table
        self.assertAlmostEqual(sim.mechanisms.position("intake_lift"), 0.0, delta=1.0)   # head back down


if __name__ == "__main__":
    unittest.main()
