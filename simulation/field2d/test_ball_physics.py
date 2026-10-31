"""Ball dynamics and ball path checks: python -m unittest (this directory)."""

import contextlib
import io
import json
import math
import unittest
from pathlib import Path

import field_layout as fl
from ball_physics import BallWorld, R, field_colliders, load_ball_path
from balls import BALL_D, Ball, load_intake
from kinematics import load_drive_train
from mblock_runtime import DCBus
from mechanisms import load_mechanisms
from robot import DEFAULT_CONFIG, RobotPose, load_config, start_pose
from simulation import Simulation, load_gyro_sign

CONTROL = Path(__file__).resolve().parents[1] / "control"
PATH_DATA = json.loads(DEFAULT_CONFIG.read_text())["ball_path"]
FAR = RobotPose(4300.0, 2800.0, 0.0)          # robot parked out of the way


def world(balls, intake=None, with_path=True):
    return BallWorld(fl.build_field(), balls, intake, load_ball_path(PATH_DATA) if with_path else None,
                     tuple(PATH_DATA["body_box_mm"]), tuple(PATH_DATA["head_box_mm"]))


def run(w, seconds, pose=FAR, velocity=(0.0, 0.0, 0.0), lift=0.0, dc=None, dt=1 / 240):
    dc = dc or DCBus()
    for _ in range(int(seconds / dt)):
        w.step(dt, pose, velocity, lift, dc)


class FreeBallTest(unittest.TestCase):
    def test_dropped_ball_bounces_lower_and_sleeps_on_the_floor(self):
        b = Ball("b", 1500.0, 1500.0, 600.0)
        w = world([b])
        b.asleep = False
        peaks, last_vz = [], 0.0
        for _ in range(240 * 3):
            w.step(1 / 240, FAR, (0, 0, 0), 0.0, DCBus())
            if last_vz > 0 >= b.vz:
                peaks.append(b.z)
            last_vz = b.vz
        self.assertTrue(b.asleep)
        self.assertAlmostEqual(b.z, R, places=3)
        self.assertGreater(len(peaks), 1)
        self.assertLess(peaks[0], 600.0)
        self.assertTrue(all(a > c for a, c in zip(peaks, peaks[1:])))      # each bounce lower

    def test_rolling_ball_slows_down_and_bounces_off_the_frame(self):
        b = Ball("b", 300.0, 1500.0, R, vx=-1500.0)
        w = world([b])
        b.vx, b.asleep = -1500.0, False
        run(w, 5)
        self.assertTrue(b.asleep)
        self.assertGreater(b.x, R)                                         # bounced off the wall at x = 0
        self.assertAlmostEqual(b.z, R, places=3)

    def test_ball_rests_on_the_central_upper_level(self):
        table = fl.get(fl.build_field(), "central_resource")
        b = Ball("b", table.x, table.y, 400.0)
        w = world([b])
        b.asleep = False
        run(w, 2)
        self.assertAlmostEqual(b.z, 250.0 + R, delta=1.0)                  # plate top at 250 mm

    def test_initial_balls_start_asleep_on_their_supports(self):
        sim = Simulation(load_config(), FAR, load_drive_train(), 5, ball_scenario="initial")
        before = [(b.x, b.y, b.z) for b in sim.balls]
        run(sim.world, 1)
        self.assertEqual(before, [(b.x, b.y, b.z) for b in sim.balls])     # nothing moves by itself

    def test_ball_thrown_into_the_fortress_counts(self):
        fort = next(e for e in fl.build_field() if e.kind == "movable" and e.alliance == "blue")
        b = Ball("b", fort.x - 900.0, fort.y, 600.0)
        w = world([b])
        flight_t = 0.5
        b.vx, b.vy, b.vz, b.asleep = 900.0 / flight_t, 0.0, (442 - 600 + 0.5 * 9810 * flight_t ** 2) / flight_t, False
        run(w, 3)
        self.assertIn("b", w.in_fortress["blue"])
        self.assertAlmostEqual(b.z, 407.0 + R, delta=1.0)                  # resting on the mesh


class RobotContactTest(unittest.TestCase):
    def test_robot_body_pushes_a_ball(self):
        pose = RobotPose(1500.0, 1500.0, 0.0)
        b = Ball("b", 1500.0 - 250.0 - R + 5, 1500.0, R)                   # touching the rear face
        w = world([b])
        run(w, 0.05, pose=pose, velocity=(-500.0, 0.0, 0.0))
        self.assertLess(b.vx, -400.0)                                      # pushed backward with the robot
        self.assertLessEqual(b.x, 1500.0 - 250.0 - R + 0.01)

    def test_ball_path_through_tower_basket_and_shooter(self):
        intake = load_intake()
        pose = RobotPose(1500.0, 1500.0, 0.0)
        b = Ball("b", 1500.0 + 240.0, 1500.0, R)
        w = world([b], intake)
        dc = DCBus()
        dc.set("DC1", 80)
        run(w, 1.0, pose=pose, dc=dc)                                      # captured, tower off
        self.assertEqual(b.state, "carried")
        c = w.carried[0]
        self.assertTrue(c.route and c.route[0][1] == "tower")              # waits at the tower
        dc.set("DC4", 80)
        run(w, 4.0, pose=pose, dc=dc)
        self.assertFalse(c.route)
        slot = w.path.slots[0]
        fx, fy = pose.to_field(slot[0], slot[1])
        self.assertAlmostEqual(b.x, fx, delta=0.5)                         # in basket slot 0
        self.assertAlmostEqual(b.z, slot[2], delta=0.5)
        dc.set("DC5", 80)
        dc.set("BL1", 50)
        run(w, 1.0, pose=pose, dc=dc)
        self.assertEqual(w.shots, 1)
        self.assertEqual(b.state, "field")
        self.assertTrue(b.collected)
        self.assertEqual(w.stored, 0)

    def test_capacity_is_the_slot_count(self):
        intake = load_intake()
        pose = RobotPose(1500.0, 1500.0, 0.0)
        balls = [Ball(f"b{i}", 1500.0 + 240.0, 1500.0 - 150 + 15 * i, R) for i in range(20)]
        w = world(balls, intake)
        dc = DCBus()
        dc.set("DC1", 80)
        run(w, 0.1, pose=pose, dc=dc)
        self.assertEqual(w.stored, 18)


class ColliderTest(unittest.TestCase):
    def test_colliders_cover_the_structures(self):
        boxes = field_colliders(fl.build_field())
        self.assertGreater(len(boxes), 60)
        self.assertTrue(any(abs(b[5] - 407.0) < 1e-6 for b in boxes))     # fortress ball level
        self.assertTrue(any(abs(b[5] - 758.5) < 1e-6 for b in boxes))     # resource shelves


class FullIntakeProgramTest(unittest.TestCase):
    def test_collect_store_and_shoot_into_the_blue_fortress(self):
        cfg = load_config()
        sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), 100, load_gyro_sign(),
                         ball_scenario="released", intake=load_intake(), mechanisms=load_mechanisms())
        sim.program = CONTROL / "test_full_intake.py"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sim.run()
            for _ in range(60 * 60):
                sim.step(1 / 60)
                if not sim.running or sim._runner.finished:
                    break
            for _ in range(60 * 3):
                sim.step(1 / 60)
        self.assertIn("done", out.getvalue(), sim.state.message)
        self.assertNotIn("MISSED", out.getvalue())
        w = sim.world
        self.assertEqual(w.captured, 10)
        self.assertEqual(w.shots, 10)
        self.assertGreaterEqual(len(w.in_fortress["blue"]), 8)
        self.assertEqual(w.in_fortress["red"], [])


if __name__ == "__main__":
    unittest.main()
