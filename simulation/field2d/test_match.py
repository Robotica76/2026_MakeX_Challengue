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
from ball_physics import named_colliders
from match import STAGES, ChannelMonitor, CollisionMonitor, MatchMonitor, format_clock, obb_aabb_depth, stage_at
from mechanisms import load_mechanisms
from props import denial_count, load_gripper, score_preview
from robot import RobotPose, load_config, start_pose
from simulation import Simulation, load_gyro_sign

REPO = Path(__file__).resolve().parents[2]
AUTO = REPO / "software" / "autonomous" / "task_execution" / "auto_central_then_cubes.py"
AUTO_PULL = REPO / "software" / "autonomous" / "task_execution" / "auto_pull_central.py"


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


class CollisionMonitorTest(unittest.TestCase):
    def setUp(self):
        cfg = load_config()
        self.monitor = CollisionMonitor(named_colliders(fl.build_field()), [(-250.0, -250.0, 0.0, 115.0, 250.0, 645.0)],
                                        (115.0, -190.0, 46.0, 249.0, 202.0, 145.0))

    def test_depth_of_a_turned_rectangle(self):
        pose = RobotPose(1000.0, 1000.0, 0.0)
        self.assertAlmostEqual(obb_aabb_depth(pose, (-100, -100, 100, 100), (1090, 900, 1200, 1100)), 10.0)
        self.assertEqual(obb_aabb_depth(RobotPose(1000.0, 1000.0, math.pi / 4), (-100, -100, 100, 100),
                                        (1150, 900, 1200, 1100)), 0.0)            # the corner reaches x 1141

    def test_cone_post_inside_the_gripper_slot_is_no_contact(self):
        slot = (-160.0, -450.0, 0.0, -18.0, -150.0, 160.0)               # robot_config.json gripper slot_mm
        monitor = CollisionMonitor(self.monitor.colliders, self.monitor.body_boxes, self.monitor.head_box, slot)
        post = next(b for n, b in monitor.colliders if n == "red_cone_post_2")
        th = math.radians(250.0)                                          # grab point (-89, -228.5) on the post
        c, s = math.cos(th), math.sin(th)
        x, y = (post[0] + post[3]) / 2 - (-89 * c + 228.5 * s), (post[1] + post[4]) / 2 - (-89 * s - 228.5 * c)
        monitor.update(0.0, RobotPose(x, y, th), 0.0, 300.0)              # carriage 300: jaws over the post top
        self.assertEqual(monitor.events, [])
        monitor.update(1.0, RobotPose(x, y, th), 0.0, 100.0)              # jaws below the post top: contact
        self.assertEqual([e["element"] for e in monitor.events], ["red_cone_post_2"])
        self.monitor.update(2.0, RobotPose(x, y, th), 0.0)                # no slot: contact
        self.assertEqual([e["element"] for e in self.monitor.events], ["red_cone_post_2"])

    def test_table_leg_and_fortress_push(self):
        self.monitor.update(0.0, RobotPose(1800.0, 1100.0, 0.0), 0.0)
        self.assertEqual(self.monitor.events, [])                                # open floor
        self.monitor.update(1.0, RobotPose(2000.0, 1300.0, 0.0), 300.0)          # head (front 2285) over the leg
        self.assertEqual([(e["element"], e["part"]) for e in self.monitor.collisions], [("central_resource", "head")])
        self.monitor.update(2.0, RobotPose(1200.0, 1500.0, 0.0), 0.0)            # rear against the red fortress
        pushes = [e for e in self.monitor.events if e["fortress"]]
        self.assertEqual([e["part"] for e in pushes], ["body"])
        self.assertEqual(len(self.monitor.collisions), 1)                        # a push is not a collision


class ChannelMonitorTest(unittest.TestCase):
    def test_r26_robot_part_inside_a_channel(self):
        slots = [(e.name, *e.bounds()) for e in fl.build_field() if e.kind == "slot"]
        m = ChannelMonitor(slots, [(-250.0, -250.0, 0.0, 115.0, 250.0, 260.0)])
        head = (115.0, -190.0, 46.0, 249.0, 202.0, 145.0)
        m.update(1.0, RobotPose(1900.0, 878.0, 0.0), head)                       # head front 2149: outside
        self.assertEqual(m.events, [])
        m.update(2.0, RobotPose(2050.0, 878.0, 0.0), head)                       # head 2299: in channel 3
        found = {e["channel"] for e in m.events}                                  # the 398 mm head spans 3
        self.assertIn("strategy_lower_channel_3", found)
        n = len(m.events)
        m.update(3.0, RobotPose(2050.0, 878.0, 0.0), (115.0, -190.0, 300.0, 249.0, 202.0, 400.0))
        self.assertEqual(len(m.events), n)                                       # head over the top: fine


class AutomaticRoutineTest(unittest.TestCase):
    def run_pull(self, strategy):
        cfg = load_config()
        sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), 30, load_gyro_sign(),
                         ball_scenario="initial", intake=load_intake(), mechanisms=load_mechanisms(),
                         gripper=load_gripper())
        sim.program = AUTO_PULL
        sim.trace_options = {"strategy": strategy}
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sim.run()
            while sim.running:
                sim.step(1 / 60)
        text = out.getvalue()
        self.assertIsNone(sim._runner.error if sim._runner else None, text)
        self.assertNotIn("MISSED", text)
        self.assertNotIn("safety stop", text)
        self.assertEqual(sim.collisions.collisions, [], text)                    # no field structure touched
        self.assertTrue(sim.monitor.auto_end["stationary"])                      # R19
        self.assertEqual(sim.monitor.r06_penalties, 0)
        denial = denial_count(sim.props, sim.balls, "red")
        self.assertEqual(denial["balls_opponent_side"], 0)
        self.assertEqual(denial["props_on_line"], 0)                             # no prop left across the line
        return denial, text

    def test_pull_balls_only(self):
        denial, text = self.run_pull("balls")
        self.assertGreaterEqual(denial["balls"], 20, text)

    def test_pull_props_first_then_balls(self):
        denial, text = self.run_pull("mixed")
        self.assertGreaterEqual(denial["balls"], 15, text)
        self.assertEqual((denial["cones"], denial["bonus"]), (1, 1), text)       # lane b: cone + X12

    def test_pull_all_lower_props(self):
        denial, text = self.run_pull("props")
        self.assertGreaterEqual(denial["balls"], 10, text)
        self.assertEqual((denial["cones"], denial["bonus"]), (2, 2), text)

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
