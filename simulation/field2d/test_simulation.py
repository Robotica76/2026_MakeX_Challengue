"""Kinematics, mBlock runtime and simulation checks: python -m unittest (this directory)."""

import math
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

import field_layout as fl
from kinematics import DriveTrain, MotorPort, body_velocity, integrate, load_drive_train
from mblock_runtime import MotorBus
from robot import RobotPose, load_config, start_pose
from simulation import Simulation

HERE = Path(__file__).parent
EXAMPLE = HERE / "programs" / "all_motors_forward.py"
PORTS = {"M1": MotorPort("front_left", 1), "M2": MotorPort("front_right", 1),
         "M3": MotorPort("rear_left", 1), "M4": MotorPort("rear_right", 1)}


def run_until_done(sim, seconds=60, fps=60):
    sim.run()
    for _ in range(int(seconds * fps)):
        sim.step(1 / fps)
        if not sim.running:
            break
    return sim


class KinematicsTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()

    def wheels(self, fl_, fr, rl, rr):
        return {"front_left": fl_, "front_right": fr, "rear_left": rl, "rear_right": rr}

    def test_forward(self):
        vx, vy, w = body_velocity(self.cfg, self.wheels(10, 10, 10, 10))
        self.assertAlmostEqual(vx, 10 / 60 * math.pi * 80)  # 80 mm wheels: ~41.9 mm/s
        self.assertAlmostEqual(vy, 0)
        self.assertAlmostEqual(w, 0)

    def test_strafe_left(self):
        vx, vy, w = body_velocity(self.cfg, self.wheels(-10, 10, 10, -10))
        self.assertAlmostEqual(vx, 0)
        self.assertGreater(vy, 0)
        self.assertAlmostEqual(w, 0)

    def test_rotate_ccw(self):
        vx, vy, w = body_velocity(self.cfg, self.wheels(-10, 10, -10, 10))
        self.assertAlmostEqual(vx, 0)
        self.assertAlmostEqual(vy, 0)
        self.assertGreater(w, 0)

    def test_motor_direction_and_clamp(self):
        drive = DriveTrain({**PORTS, "M2": MotorPort("front_right", -1)}, max_rpm=100)
        rpms = drive.wheel_rpms({"M1": 50, "M2": 50, "M5": 999})  # M5 is not a drive motor
        self.assertEqual(rpms["front_right"], -50)
        self.assertEqual(drive.wheel_rpms({"M1": 500})["front_left"], 100)

    def test_integrate_quarter_turn(self):
        pose = RobotPose(0, 0, 0)
        for _ in range(1000):
            pose = integrate(pose, 0, 0, math.pi / 2, 0.001)
        self.assertAlmostEqual(pose.theta, math.pi / 2, places=6)

    def test_config_drive_train(self):
        drive = load_drive_train()
        self.assertEqual(set(drive.motors), {"M1", "M2", "M3", "M4"})


class SimulationTest(unittest.TestCase):
    def make(self, heading=0, program=EXAMPLE, time_limit=30.0):
        cfg = replace(load_config(), heading_deg=heading)
        sim = Simulation(cfg, start_pose(cfg, fl.build_field()), DriveTrain(PORTS), time_limit)
        sim.program = program
        return sim

    def program(self, source):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "prog.py"
        path.write_text(source)
        return path

    def test_example_drives_forward_until_time_limit(self):
        sim = run_until_done(self.make(heading=0))
        self.assertEqual(sim.state.status, "done")
        self.assertAlmostEqual(sim.time, 30.0, places=6)
        self.assertAlmostEqual(sim.pose.x - sim.start_pose.x, 30 * 10 / 60 * math.pi * 80, delta=1)

    def test_example_leaves_field(self):
        sim = run_until_done(self.make(heading=270))  # facing the near wall, 100 mm away
        self.assertEqual(sim.state.status, "out_of_bounds")
        self.assertIn("Out of boundaries", sim.state.message)
        self.assertAlmostEqual(sim.time, 100 / (10 / 60 * math.pi * 80), delta=0.02)

    def test_sleep_uses_simulated_time(self):
        src = ("import time\nfrom mbuild.encoder_motor import encoder_motor_class\n"
               "ms = [encoder_motor_class(p, 'INDEX1') for p in ('M1', 'M2', 'M3', 'M4')]\n"
               "for m in ms: m.set_speed(60)\n"
               "time.sleep(2)\n"
               "for m in ms: m.stop()\n")
        sim = run_until_done(self.make(program=self.program(src), time_limit=5))
        self.assertEqual(sim.state.status, "done")
        # 60 rpm for 2 s with 80 mm wheels = 2 revolutions = 502.7 mm
        self.assertAlmostEqual(sim.pose.x - sim.start_pose.x, 2 * math.pi * 80, delta=3)

    def test_unsupported_api_is_reported(self):
        src = "from mbuild.encoder_motor import encoder_motor_class\nencoder_motor_class('M1','INDEX1').move_to(90)\n"
        sim = run_until_done(self.make(program=self.program(src)), seconds=1)
        self.assertEqual(sim.state.status, "error")
        self.assertIn("move_to", sim.state.message)

    def test_syntax_error_is_reported(self):
        sim = self.make(program=self.program("encoder_motor_M1.set_speed(\n"))
        sim.run()
        self.assertEqual(sim.state.status, "error")
        self.assertIn("SyntaxError", sim.state.message)

    def test_stop_ends_infinite_loop(self):
        src = "import time\nwhile True:\n    time.sleep(0.1)\n"
        sim = self.make(program=self.program(src), time_limit=0)
        sim.run()
        for _ in range(30):
            sim.step(1 / 60)
        sim.stop()
        self.assertEqual(sim.state.status, "stopped")

    def test_busy_program_does_not_freeze(self):
        src = ("from mbuild.encoder_motor import encoder_motor_class\n"
               "m = encoder_motor_class('M1', 'INDEX1')\n"
               "while True:\n    m.set_speed(10)\n")
        sim = self.make(program=self.program(src), time_limit=1)
        run_until_done(sim, seconds=2)
        self.assertEqual(sim.state.status, "done")

    # --- regressions from the PR #26 review ---------------------------------
    def assert_no_program_threads(self):
        alive = [t for t in threading.enumerate() if t.name == "mblock-program" and t.is_alive()]
        self.assertEqual(alive, [])

    def run_then_stop(self, src, frames=10):
        sim = self.make(program=self.program(src), time_limit=0)
        sim.run()
        for _ in range(frames):
            sim.step(1 / 60)
        sim.stop()
        return sim

    def test_stop_kills_loop_without_api_calls(self):
        sim = self.run_then_stop("while True:\n    pass\n")
        self.assertEqual(sim.state.status, "stopped")
        self.assertNotIn("warning", sim.state.message)
        self.assert_no_program_threads()

    def test_stop_kills_loop_in_helper_function_with_bare_except(self):
        src = ("import math\n"
               "def spin():\n"
               "    while True:\n"
               "        try:\n"
               "            math.sqrt(2)\n"
               "        except BaseException:\n"
               "            pass\n"
               "spin()\n")
        sim = self.run_then_stop(src)
        self.assertEqual(sim.state.status, "stopped")
        self.assert_no_program_threads()

    def test_repeated_runs_do_not_accumulate_workers(self):
        sim = self.make(program=self.program("while True:\n    pass\n"), time_limit=0.1)
        for _ in range(3):
            run_until_done(sim, seconds=1)
            sim.reset()
        self.assert_no_program_threads()

    def test_motor_bus_clamps_commands(self):
        bus = MotorBus(max_rpm=580)
        bus.set("M5", 1000)
        bus.set("M6", -1000)
        self.assertEqual(bus.snapshot(), {"M5": 580, "M6": -580})

    def test_speed_feedback_matches_motion_limit(self):
        src = ("from mbuild.encoder_motor import encoder_motor_class\n"
               "drive = [encoder_motor_class(p, 'INDEX1') for p in ('M1', 'M2', 'M3', 'M4')]\n"
               "shooter = encoder_motor_class('M5', 'INDEX1')  # not a drive wheel\n"
               "for m in drive + [shooter]: m.set_speed(1000)\n"
               "assert drive[0].get_value('speed') == 580, drive[0].get_value('speed')\n"
               "assert shooter.get_value('speed') == 580, shooter.get_value('speed')\n")
        sim = run_until_done(self.make(program=self.program(src), time_limit=1), seconds=2)
        self.assertEqual(sim.state.status, "done", sim.state.message)
        self.assertAlmostEqual(sim.pose.x - sim.start_pose.x, 580 / 60 * math.pi * 80, delta=2)

    def test_missing_program_file_is_reported(self):
        sim = self.make(program=Path(self.program("pass\n").parent, "deleted.py"))
        sim.run()  # must not raise into the viewer
        self.assertEqual(sim.state.status, "error")
        self.assertIn("Cannot read deleted.py", sim.state.message)

    def test_undecodable_program_file_is_reported(self):
        path = self.program("")
        path.write_bytes(b"\xff\xfe\x00 not utf-8")
        sim = self.make(program=path)
        sim.run()
        self.assertEqual(sim.state.status, "error")
        self.assertIn("Cannot read", sim.state.message)


if __name__ == "__main__":
    unittest.main()
