"""Sensors, move(), gamepad link, project imports, and the chassis.py demo programs
(simulation/control, importing software/controls/drivetrain/chassis.py) running in
the simulator: python -m unittest."""

import contextlib
import io
import math
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import field_layout as fl
from kinematics import load_drive_train
from mblock_runtime import GamepadInput, MotorBus, ProgramRunner, SimClock, UnsupportedAPI
from robot import RobotPose, load_config, start_pose
from simulation import Simulation, load_gyro_sign

CONTROL = Path(__file__).resolve().parents[1] / "control"
AUTO = CONTROL / "test_chassis_control_automatico.py"
MANUAL = CONTROL / "test_chassis_control_manual.py"


def make_sim(program, time_limit=120.0, gamepad=None, start=None):
    cfg = load_config()
    sim = Simulation(cfg, start or start_pose(cfg, fl.build_field()), load_drive_train(), time_limit,
                     load_gyro_sign(), gamepad)
    sim.program = Path(program)
    return sim


def step_for(sim, seconds, fps=60):
    for _ in range(int(seconds * fps)):
        if not sim.running:
            break
        sim.step(1 / fps)


def run_to_program_end(sim, max_seconds=120):
    """Run until the program returns (the sim itself keeps going after that)."""
    sim.run()
    while sim.running and not (sim._runner and sim._runner.finished) and sim.time < max_seconds:
        sim.step(1 / 60)


def chassis_frame(sim):
    """True displacement in chassis.py's frame: (x right cm, y forward cm, heading cw deg)."""
    p, s = sim.pose, sim.start_pose
    dx, dy = (p.x - s.x) / 10, (p.y - s.y) / 10
    c, si = math.cos(s.theta), math.sin(s.theta)
    forward, left = dx * c + dy * si, -dx * si + dy * c
    turn = math.degrees(math.atan2(math.sin(p.theta - s.theta), math.cos(p.theta - s.theta)))
    return -left, forward, -turn


class RuntimeSensorsTest(unittest.TestCase):
    def program(self, source, extra=None):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for name, text in (extra or {}).items():
            Path(tmp.name, name).write_text(text)
        path = Path(tmp.name) / "prog.py"
        path.write_text(source)
        return path

    def test_move_turns_exact_degrees_then_stops(self):
        bus = MotorBus(580)
        bus.move("M1", 90, 60)  # 60 rpm = 360 deg/s -> 0.25 s
        for _ in range(100):
            bus.integrate(0.01)
        self.assertAlmostEqual(bus.angle("M1"), 90)
        self.assertEqual(bus.snapshot()["M1"], 0)
        bus.move("M1", -45, 60)
        bus.set("M1", 10)  # set_speed cancels the pending move
        for _ in range(100):
            bus.integrate(0.01)
        self.assertAlmostEqual(bus.angle("M1"), 90 + 60 * 1.0, places=6)

    def test_encoders_gyro_and_sibling_module(self):
        # With the chassis.py wiring (left motors mirrored), the same command on all
        # four motors drives the left wheels backward and the right ones forward: a CCW spin.
        helper = ("from mbuild.encoder_motor import encoder_motor_class\n"
                  "def spin(rpm):\n"
                  "    for p in ('M4', 'M1', 'M3', 'M2'):\n"
                  "        encoder_motor_class(p, 'INDEX1').set_speed(rpm)\n")
        src = ("import time, novapi, helper\n"
               "from mbuild.encoder_motor import encoder_motor_class\n"
               "helper.spin(30)\n"
               "time.sleep(1)\n"
               "g = novapi.get_gyroscope('z')\n"
               "a = encoder_motor_class('M1', 'INDEX1').get_value('angle')\n"
               "assert g < 0, g\n"             # config: clockwise positive -> CCW reads negative
               "assert abs(a - 180) < 1, a\n"  # 30 rpm for 1 s = 180 deg
               "helper.spin(0)\n")
        # Spin in mid-field: the v22 wheel rectangle is off-centre, so a spin in the start
        # area sweeps the footprint corners past the field wall.
        mid = RobotPose(fl.FIELD_W / 4, fl.FIELD_H / 2, 0.0)
        sim = make_sim(self.program(src, {"helper.py": helper}), time_limit=2, start=mid)
        sim.run()
        step_for(sim, 3)
        self.assertEqual(sim.state.status, "done", sim.state.message)
        self.assertGreater(sim.pose.theta, 0.1)  # turned CCW in the field frame

    def test_turn_about_offset_wheel_centre_keeps_odometry_on_footprint_centre(self):
        # v22: the wheel rectangle is 79 mm behind the footprint centre, so a turn swings the
        # footprint centre; odometry must report it, in closed loop and in open loop.
        for sensors in ("True", "False"):
            src = ("import chassis as ch\n"
                   "ch.USE_SENSORS = %s\n"
                   "ch.odo.calibrate(0.5)\nch.odo.reset()\n"
                   "ch.turn_to(90)\n"
                   "print('pose', ch.odo.x, ch.odo.y, ch.odo.heading)\n" % sensors)
            mid = RobotPose(fl.FIELD_W / 4, fl.FIELD_H / 2, 0.0)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                sim = make_sim(self.program(src), time_limit=6, start=mid)
                sim.run()
                step_for(sim, 7)
            line = [l for l in out.getvalue().splitlines() if l.startswith("pose")][-1]
            odo_x, odo_y, odo_h = (float(v) for v in line.split()[1:])
            true_x, true_y, true_h = chassis_frame(sim)
            self.assertGreater(math.hypot(true_x, true_y), 5, sensors)   # the centre did swing (~11 cm)
            self.assertAlmostEqual(odo_x, true_x, delta=0.5, msg=sensors)
            self.assertAlmostEqual(odo_y, true_y, delta=0.5, msg=sensors)
            self.assertAlmostEqual(odo_h, true_h, delta=2.0, msg=sensors)

    def test_error_in_sibling_module_names_the_file(self):
        sim = make_sim(self.program("import helper\n", {"helper.py": "x = 1\ny = x / 0\n"}), time_limit=1)
        sim.run()
        step_for(sim, 1)
        self.assertEqual(sim.state.status, "error")
        self.assertIn("helper.py line 2", sim.state.message)

    def test_project_modules_resolve_beside_then_under_roots(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "prog").mkdir()
        (root / "lib" / "a").mkdir(parents=True)
        (root / "lib" / "b").mkdir(parents=True)
        (root / "lib" / "a" / "shared.py").write_text("")
        (root / "lib" / "a" / "dup.py").write_text("")
        (root / "lib" / "b" / "dup.py").write_text("")
        (root / "prog" / "local.py").write_text("")
        runner = ProgramRunner(root / "prog" / "main.py", SimClock(), MotorBus(580),
                               module_roots=[root / "lib"])
        self.assertEqual(runner.find_module("local"), root / "prog" / "local.py")
        self.assertEqual(runner.find_module("shared").name, "shared.py")
        self.assertIsNone(runner.find_module("math"))   # left to the normal import
        with self.assertRaises(ImportError):
            runner.find_module("dup")

    def test_gamepad_events_map_to_mblock_names(self):
        pad = GamepadInput()
        pad.apply_event({"event": "axis", "control": "left_stick", "x": 0.5, "y": -1.0})
        pad.apply_event({"event": "press", "control": "button_1"})
        pad.apply_event({"event": "press", "control": "menu"})
        self.assertEqual((pad.joystick("Lx"), pad.joystick("Ly")), (50.0, -100.0))
        self.assertTrue(pad.pressed("N1") and pad.pressed("≡"))
        pad.apply_event({"event": "release", "control": "button_1"})
        self.assertFalse(pad.pressed("N1"))
        pad.apply_event({"event": "power", "control": "power", "on": False})
        self.assertEqual(pad.joystick("Lx"), 0)
        self.assertFalse(pad.pressed("≡"))
        with self.assertRaises(UnsupportedAPI):
            pad.pressed("A")


@unittest.skipUnless(AUTO.is_file() and MANUAL.is_file(), "chassis demo programs not found")
class ChassisProgramsTest(unittest.TestCase):
    def test_automatic_demo_arrives_everywhere_and_odometry_matches_truth(self):
        sim = make_sim(AUTO)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            run_to_program_end(sim)
        text = out.getvalue()
        self.assertTrue(sim._runner is None or sim._runner.error is None, sim.state.message)
        self.assertIn("done:", text, text)
        self.assertNotIn("MISSED", text, text)
        self.assertNotEqual(sim.state.status, "out_of_bounds", sim.state.message)
        last = [l for l in text.splitlines() if l.startswith("backward")][-1]
        odo_x, odo_y = (float(v) for v in re.findall(r"[xy]=\s*(-?[\d.]+)", last))
        true_x, true_y, _ = chassis_frame(sim)
        self.assertAlmostEqual(odo_x, true_x, delta=0.5)
        self.assertAlmostEqual(odo_y, true_y, delta=0.5)
        self.assertLess(math.hypot(true_x, true_y), 5)  # back near the start

    def test_manual_demo_follows_the_gamepad(self):
        pad = GamepadInput()
        sim = make_sim(MANUAL, gamepad=pad)
        with contextlib.redirect_stdout(io.StringIO()):
            sim.run()
            step_for(sim, 1.5)                                # calibrate(1.0)
            pad.apply_event({"event": "axis", "control": "left_stick", "x": 0.0, "y": 1.0})
            step_for(sim, 2.0)                                # full forward
            pad.apply_event({"event": "axis", "control": "left_stick", "x": 0.0, "y": 0.0})
            step_for(sim, 1.0)                                # S-curve brakes to a stop
            x1, y1, h1 = chassis_frame(sim)
            pad.apply_event({"event": "press", "control": "menu"})   # front = F_LAUNCHER (left side)
            step_for(sim, 0.2)
            pad.apply_event({"event": "release", "control": "menu"})
            pad.apply_event({"event": "axis", "control": "left_stick", "x": 0.0, "y": 1.0})
            step_for(sim, 2.0)                                # stick up now strafes left (away from the wall)
            pad.apply_event({"event": "axis", "control": "left_stick", "x": 0.0, "y": 0.0})
            step_for(sim, 1.0)
            x2, y2, h2 = chassis_frame(sim)
        self.assertEqual(sim.state.status, "running", sim.state.message)
        self.assertGreater(y1, 40)          # MAX_SPEED 100 rpm ~ 42 cm/s
        self.assertLess(abs(x1), 1)
        self.assertLess(abs(h1), 1)         # no turn requested
        self.assertLess(x2, x1 - 40)        # F_LAUNCHER drove toward the launcher (left)
        self.assertLess(abs(y2 - y1), 2)
        self.assertLess(abs(h2), 1)
        sim.stop()


if __name__ == "__main__":
    unittest.main()
