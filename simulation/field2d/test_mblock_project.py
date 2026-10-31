"""mBlock block projects (.mblock) in the simulator: python -m unittest (this directory)."""

import ast
import contextlib
import io
import json
import math
import os
import re
import time
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import field_layout as fl  # noqa: E402
from kinematics import load_drive_train  # noqa: E402
from mblock_project import MblockError, identifier, mblock_to_python  # noqa: E402
from mblock_runtime import ServoBus  # noqa: E402
from robot import RobotPose, load_config, start_pose  # noqa: E402
from simulation import Simulation, load_gyro_sign  # noqa: E402

LEGACY = Path(__file__).resolve().parents[2] / "software" / "legacy" / "challenge_2025"
PROJECT = LEGACY / "Challenge_2025.n2.mblock"


def program_parts(code):
    tree = ast.parse(code)
    defs = {n.name: ast.dump(n) for n in tree.body if isinstance(n, ast.FunctionDef)}
    main = [ast.dump(n) for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.Import, ast.ImportFrom))]
    return defs, sorted(main)


def project_file(folder, blocks, variables=None):
    path = Path(folder) / "p.mblock"
    data = {"targets": [{"name": "Stage", "isStage": True, "variables": variables or {}, "blocks": {}},
                        {"name": "novapi", "isStage": False, "variables": {}, "blocks": blocks}]}
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("project.json", json.dumps(data))
    return path


def new_sim(program=None):
    cfg = load_config()
    sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), 0, load_gyro_sign())
    sim.program = program
    return sim


class TranslatorTest(unittest.TestCase):
    def test_same_program_as_mblock_python_view(self):
        reference = program_parts((LEGACY / "mblock_python_view.py").read_text(encoding="utf-8"))
        self.assertEqual(program_parts(mblock_to_python(PROJECT)), reference)

    def test_identifiers_follow_mblock(self):
        self.assertEqual(identifier("Avanzar %n"), "Avanzar_N")
        self.assertEqual(identifier("avance derecha %n"), "avance_derecha_N")
        self.assertEqual(identifier("cerrar_pinza-auto %n"), "cerrar_pinza_auto_N")
        self.assertEqual(identifier("girar_izquierda_90°"), "girar_izquierda_90_C2_B0")

    def test_unknown_block_is_reported(self):
        blocks = {"h": {"opcode": "novapi.NovaPi main program setup", "next": "a", "inputs": {}, "fields": {},
                        "topLevel": True},
                  "a": {"opcode": "novapi.led_show", "next": None, "inputs": {}, "fields": {}, "topLevel": False}}
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(MblockError, "novapi.led_show"):
                mblock_to_python(project_file(d, blocks))

    def test_not_a_project(self):
        with TemporaryDirectory() as d:
            bad = Path(d) / "x.mblock"
            bad.write_text("not a zip")
            with self.assertRaises(MblockError):
                mblock_to_python(bad)


class DevicesTest(unittest.TestCase):
    def test_servo_moves_at_its_speed_and_holds(self):
        s = ServoBus()
        s.move_to("M6", 30, 5)                       # 5 rpm = 30 deg/s
        s.integrate(0.5)
        self.assertAlmostEqual(s.angle("M6"), 15.0)
        s.integrate(1.0)
        self.assertAlmostEqual(s.angle("M6"), 30.0)
        s.move("M6", -20, 10)
        s.integrate(0.1)
        s.move("M6", 0, 0)                           # stop where it is
        s.integrate(1.0)
        self.assertAlmostEqual(s.angle("M6"), 24.0)

    def test_ranging_sensor_sees_the_field_wall(self):
        sim = new_sim()
        sim.pose = RobotPose(1000.0, 600.0, math.pi)                  # facing the x = 0 wall
        self.assertAlmostEqual(sim.ranging_cm({"position_mm": [200, 0, 100]}), 80.0)
        sim.pose = RobotPose(1000.0, 1500.0, math.pi)                 # the red pin area is in the way
        self.assertAlmostEqual(sim.ranging_cm({"position_mm": [200, 0, 100]}), 60.5)
        self.assertAlmostEqual(sim.ranging_cm({"position_mm": [0, 0, 120], "direction": "down"}), 12.0)
        sim.pose = RobotPose(2000.0, 1215.0, 0.0)                     # facing a central table leg
        self.assertAlmostEqual(sim.ranging_cm({"position_mm": [100, 0, 300]}), 12.0)


class ChallengeProgramTest(unittest.TestCase):
    def test_2025_blocks_run_with_the_gamepad(self):
        with TemporaryDirectory() as d:
            program = Path(d) / "challenge_2025.py"
            program.write_text(mblock_to_python(PROJECT), encoding="utf-8")
            sim = new_sim(program)
            self.addCleanup(sim.reset)                                      # never leave the thread running
            press = lambda c: sim.gamepad.apply_event({"event": "press", "control": c})      # noqa: E731
            release = lambda c: sim.gamepad.apply_event({"event": "release", "control": c})  # noqa: E731

            def run(seconds):
                end = sim.time + seconds
                deadline = time.monotonic() + 20
                while sim.time < end and time.monotonic() < deadline:
                    sim.step(1 / 60)
                    if not sim.running:
                        break

            sim.run()
            run(1.0)
            self.assertAlmostEqual(sim.servos.angle("M6"), 30.0, places=3)   # setup: gripper to 30
            press("button_1")                                               # N1: automatic
            run(0.3)
            release("button_1")
            press("button_2")                                               # N2: right start (3 s)
            run(0.3)
            release("button_2")
            run(4.0)
            self.assertAlmostEqual(sim.servos.angle("M6"), 40.0, places=3)   # abrir_pinza_manual
            start = sim.pose
            sim.gamepad.apply_event({"event": "axis", "control": "left_stick", "x": 0.0, "y": 0.6})
            press("L1")                                                     # launcher mode: discs up
            run(1.0)
            self.assertIsNone(sim._runner.error, sim.state.message)
            self.assertGreater(math.hypot(sim.pose.x - start.x, sim.pose.y - start.y), 50.0)
            self.assertEqual(sim.dc.power("DC1"), 70.0)
            self.assertEqual(sim.dc.power("DC2"), -70.0)
            sim.stop()


class CompetitionProgramTest(unittest.TestCase):
    """software/robot/main/robot_2026.py, as modules (simulator) and bundled into one file
    for mBlock (tools/scripts/bundle_for_mblock.py): same automatic stage, then manual."""

    def run_program(self, program):
        from balls import load_intake
        from mechanisms import load_mechanisms
        from props import denial_count, load_gripper
        cfg = load_config()
        sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), 0, load_gyro_sign(),
                         ball_scenario="initial", intake=load_intake(), mechanisms=load_mechanisms(),
                         gripper=load_gripper())
        self.addCleanup(sim.reset)
        sim.program = program
        out = io.StringIO()
        events = [(1.5, "press", "button_3"), (1.7, "release", "button_3"),     # N3: strategy "balls"
                  (2.0, "press", "button_1"), (2.2, "release", "button_1")]     # N1: match start
        with contextlib.redirect_stdout(out):
            sim.run()
            while sim.time < 35.0 and sim.running:
                while events and sim.time >= events[0][0]:
                    _, kind, control = events.pop(0)
                    sim.gamepad.apply_event({"event": kind, "control": control})
                sim.step(1 / 60)
            self.assertIsNone(sim._runner.error, out.getvalue())
            moved = sim.pose
            sim.gamepad.apply_event({"event": "axis", "control": "left_stick", "x": 0.0, "y": 0.8})
            end = sim.time + 1.0
            while sim.time < end:
                sim.step(1 / 60)
        self.assertIsNone(sim._runner.error, out.getvalue())
        steps = [line.split()[2] for line in out.getvalue().splitlines() if line.strip()[:1].isdigit()]
        return steps, denial_count(sim.props, sim.balls, "red"), math.hypot(sim.pose.x - moved.x, sim.pose.y - moved.y)

    def test_modules_and_bundle_run_the_same_match(self):
        import sys
        sys.path.insert(0, str(LEGACY.parents[2] / "tools" / "scripts"))
        from bundle_for_mblock import bundle
        source = LEGACY.parents[1] / "robot" / "main" / "robot_2026.py"
        steps, denial, driven = self.run_program(source)
        self.assertIn("lower_b", steps)                                     # strategy "balls" ran
        self.assertGreaterEqual(denial["balls"], 20)
        self.assertGreater(driven, 100.0)                                   # manual: stick drives
        with TemporaryDirectory() as d:
            single = Path(d) / "robot_2026_mblock.py"
            single.write_text(bundle(source), encoding="utf-8")
            code = single.read_text(encoding="utf-8")
            self.assertNotIn("import chassis", code)
            self.assertIsNone(re.search(r"\b(ch|auto)\.", code))
            b_steps, b_denial, b_driven = self.run_program(single)
        self.assertEqual(b_steps, steps)
        self.assertEqual(b_denial["balls_opponent_side"], 0)
        self.assertGreater(b_driven, 100.0)


class ReloadTest(unittest.TestCase):
    def test_mblock_is_translated_and_reloaded_when_saved(self):
        from viewer import ProgramController
        with TemporaryDirectory() as d:
            src = Path(d) / "Challenge 2025.mblock"
            src.write_bytes(PROJECT.read_bytes())
            sim = new_sim()
            messages = []
            ctl = ProgramController(sim, lambda text, error=False: messages.append((text, error)))
            self.assertTrue(ctl.open(src))
            self.assertEqual(sim.program.name, "Challenge_2025.py")
            self.assertIn("def Avanzar_N(cm):", sim.program.read_text(encoding="utf-8"))
            self.assertFalse(ctl.watch(1.0))                                # unchanged
            os.utime(src, (time.time() + 5, time.time() + 5))               # saved again in mBlock
            self.assertTrue(ctl.watch(2.0))
            self.assertIn("changed: reloaded", messages[-1][0])
            self.assertFalse(ctl.open(Path(d) / "notes.txt"))
            self.assertTrue(messages[-1][1])
            sim.program.unlink()


if __name__ == "__main__":
    unittest.main()
