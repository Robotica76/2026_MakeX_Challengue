"""Props, gripper and automatic score preview: python -m unittest (this directory)."""

import math
import unittest

import field_layout as fl
from balls import load_intake
from props import (CHANNEL_RAIL_Z, CONE_HANG_DROP, CUBE, Gripper, Prop, bonus_state, denial_count, field_props, load_gripper,
                   rake_props, score_preview, support_under)
from robot import RobotPose

ELEMENTS = fl.build_field()


def prop_named(props, name):
    return next(p for p in props if p.name == name)


class FieldPropsTest(unittest.TestCase):
    def test_counts_and_heights(self):
        props = field_props(ELEMENTS)
        self.assertEqual(sum(p.kind == "bonus" for p in props), 4)      # p.24
        self.assertEqual(sum(p.kind == "cone" for p in props), 4)       # p.25
        self.assertEqual(sum(p.kind == "letter" for p in props), 16)    # p.23: 8 per alliance
        self.assertTrue(all(p.z == 259.0 for p in props if p.kind in ("bonus", "cone")))   # strategy area top
        self.assertEqual(sum(p.kind == "pin" for p in props), 16)       # p.13: 4 per own resource area
        self.assertTrue(all(p.z == 758.5 for p in props if p.kind == "pin"))
        self.assertTrue(all(p.z == 171.0 for p in props if p.kind == "letter"))   # fortress cube level
        self.assertEqual(sorted(p.label for p in props if p.kind == "letter" and p.alliance == "red"),
                         sorted("MAKEMAKE"))


class GripperTest(unittest.TestCase):
    def setUp(self):
        self.g = load_gripper()
        self.cube = Prop("c", "bonus", "X12", "neutral", 0.0, 0.0, 259.0)
        self.pose = RobotPose(1000.0, 1000.0, math.pi / 2)              # facing +y: gripper (right) toward +x
        gx, gy, _ = self.g.grab_field(self.pose, 0.0)
        self.cube.x, self.cube.y = gx, gy
        self.carriage = 259.0 + CUBE / 2 - self.g.grab_point[2]          # grab point at the cube centre

    def test_holds_when_closed_and_follows(self):
        self.g.update(self.pose, self.carriage, 5.0, [self.cube], ELEMENTS)    # gap 133 > 120: open
        self.assertIsNone(self.g.held)
        self.g.update(self.pose, self.carriage, 20.0, [self.cube], ELEMENTS)   # gap 118: closed on it
        self.assertIs(self.g.held, self.cube)
        moved = RobotPose(1200.0, 1000.0, math.pi / 2)
        self.g.update(moved, self.carriage, 20.0, [self.cube], ELEMENTS)
        self.assertAlmostEqual(self.cube.x, self.g.grab_field(moved, 0.0)[0])

    def test_released_on_the_floor(self):
        self.g.update(self.pose, self.carriage, 20.0, [self.cube], ELEMENTS)
        self.g.update(self.pose, self.carriage, 0.0, [self.cube], ELEMENTS)    # open: drop
        self.assertIsNone(self.g.held)
        self.assertEqual(self.cube.z, 0.0)

    def test_out_of_reach_is_not_taken(self):
        self.cube.x += 60.0
        self.g.update(self.pose, self.carriage, 30.0, [self.cube], ELEMENTS)
        self.assertIsNone(self.g.held)


class LetterChannelTest(unittest.TestCase):
    """A letter cube held 40 mm outward of the grab point sticks out past the jaws: its centre gets
    over the channel rail (x 2220) with the robot body outside the strategy area."""
    def setUp(self):
        self.g = load_gripper()
        self.window = fl.get(ELEMENTS, "strategy_lower_channel_3")          # y 877.5 (K)
        self.pose = RobotPose(1100.0, 700.0, math.pi / 2)
        gx, gy, _ = self.g.grab_field(self.pose, 0.0)
        self.cube = Prop("k", "letter", "K", "red", gx + 40.0, gy, 0.0)    # 40 mm outward (+x at heading 90)

    def test_grip_overlap_limits(self):
        self.assertTrue(self.g.lateral_ok(-40.0, CUBE))                     # 41.5 mm on the 43 mm plates
        self.assertFalse(self.g.lateral_ok(-55.0, CUBE))                    # 26.5 mm: slips out
        self.assertFalse(self.g.lateral_ok(30.0, CUBE))                     # deeper than the slot end
        self.assertFalse(self.g.lateral_ok(-40.0, 90.0))                    # a cone (90 mm) that far out

    def held_at(self, robot_x, robot_y):
        self.g.update(self.pose, 0.0, 28.0, [self.cube], ELEMENTS)
        self.assertIs(self.g.held, self.cube)
        pose = RobotPose(robot_x, robot_y, math.pi / 2)
        self.g.update(pose, 10.0, 28.0, [self.cube], ELEMENTS)
        return pose

    def test_released_over_the_rail_it_scores(self):
        pose = self.held_at(2220.0 - 250.0 - 8.0, self.window.y + 89.0)    # body 8 mm off the strategy area
        self.assertGreater(self.cube.x, 2220.0)
        self.g.update(pose, 10.0, 0.0, [self.cube], ELEMENTS)               # open
        self.assertEqual(self.cube.z, CHANNEL_RAIL_Z)
        self.assertEqual(score_preview([self.cube], ELEMENTS, "red")["letter_cubes"], 1)

    def test_off_the_window_it_drops_in_front(self):
        pose = self.held_at(2220.0 - 250.0 - 8.0, self.window.y + 89.0 + 20.0)   # 20 mm off the window centre
        self.g.update(pose, 10.0, 0.0, [self.cube], ELEMENTS)
        self.assertEqual(self.cube.z, 0.0)
        self.assertLess(self.cube.x, 2220.0)
        self.assertEqual(score_preview([self.cube], ELEMENTS, "red")["letter_cubes"], 0)


class ConeHangTest(unittest.TestCase):
    """A cone hangs on a cone post only when it is lowered onto it from above (405 mm post)."""
    def setUp(self):
        self.g = load_gripper()
        self.post = next(el for el in ELEMENTS if el.name == "red_cone_post_2")
        self.heading = math.radians(250.0)                                # cone_post_reach.py
        gx, gy, _ = self.g.grab_point
        c, s = math.cos(self.heading), math.sin(self.heading)
        self.at_post = RobotPose(self.post.x - (gx * c - gy * s), self.post.y - (gx * s + gy * c), self.heading)
        self.away = RobotPose(self.at_post.x + 250 * math.cos(math.radians(340)),
                              self.at_post.y + 250 * math.sin(math.radians(340)), self.heading)
        x, y, _ = self.g.grab_field(self.away, 0.0)
        self.cone = Prop("cone", "cone", "cone", "neutral", x, y, 0.0)
        self.g.update(self.away, 0.0, 56.0, [self.cone], ELEMENTS)        # taken off the floor
        self.assertIs(self.g.held, self.cone)

    def carry_to_post(self, carriage):
        self.g.update(self.away, carriage, 56.0, [self.cone], ELEMENTS)
        self.g.update(self.at_post, carriage, 56.0, [self.cone], ELEMENTS)

    def test_lifted_over_the_post_lowered_and_released_it_hangs(self):
        self.carry_to_post(425.0)                                         # bottom 425.5 > 405
        self.assertEqual(self.cone.on_post, "red_cone_post_2")
        self.g.update(self.at_post, 200.0, 56.0, [self.cone], ELEMENTS)   # lowered: rests on the post
        self.assertAlmostEqual(self.cone.z, 405.0 - CONE_HANG_DROP)
        self.g.update(self.at_post, 300.0, 0.0, [self.cone], ELEMENTS)    # jaws open
        self.assertIsNone(self.g.held)
        self.assertAlmostEqual(self.cone.z, 405.0 - CONE_HANG_DROP)
        self.assertEqual(score_preview([self.cone], ELEMENTS, "red")["cones"], 1)
        self.assertEqual(score_preview([self.cone], ELEMENTS, "blue")["cones"], 0)

    def test_v22_carriage_cannot_lift_it_over_the_post(self):
        self.carry_to_post(358.0)                                         # v22 top: bottom 358.5 < 405
        self.assertEqual(self.cone.on_post, "")
        self.g.update(self.at_post, 358.0, 0.0, [self.cone], ELEMENTS)
        self.assertEqual(self.cone.z, 0.0)                                # falls beside the post
        self.assertGreater(math.hypot(self.cone.x - self.post.x, self.cone.y - self.post.y), 60.0)
        self.assertEqual(score_preview([self.cone], ELEMENTS, "red")["cones"], 0)


class SupportTest(unittest.TestCase):
    def test_channel_rail_strategy_top_fortress_floor(self):
        slot = next(e for e in ELEMENTS if e.kind == "slot")
        self.assertEqual(support_under(Prop("p", "letter", "M", "red", slot.x, slot.y, 0), ELEMENTS), CHANNEL_RAIL_Z)
        strat = fl.get(ELEMENTS, "strategy_lower")
        self.assertEqual(support_under(Prop("p", "bonus", "X3", "neutral", strat.x, strat.y + 470, 0), ELEMENTS), 259.0)
        fort = fl.get(ELEMENTS, "red_fortress")
        self.assertEqual(support_under(Prop("p", "letter", "M", "red", fort.x, fort.y, 0), ELEMENTS), 171.0)
        self.assertEqual(support_under(Prop("p", "bonus", "X3", "neutral", 1500.0, 1500.0, 0), ELEMENTS), 0.0)


class RakeTest(unittest.TestCase):
    def test_pulled_cube_rides_the_top_then_drops_at_the_centre_line(self):
        intake = load_intake()
        props = field_props(ELEMENTS)
        x12 = prop_named(props, next(p.name for p in props if p.label == "X12"))
        x, y = 2000.0, x12.y
        rake_props(RobotPose(x, y, 0.0), 250.0, True, props, ELEMENTS, 1 / 60, intake, (46.0, 145.0))
        self.assertTrue(x12.dragged)
        for _ in range(60):                                                # back out pulling
            rake_props(RobotPose(x, y, 0.0), 250.0, True, props, ELEMENTS, 1 / 60, intake, (46.0, 145.0))
            if x12.z == 259.0:
                self.assertTrue(x12.dragged)                               # on the top, not in a channel
            x -= 5.0
        self.assertFalse(x12.dragged)
        self.assertEqual(x12.z, 0.0)
        self.assertGreater(x12.x, 2220.0 - CUBE / 2)                       # fell at the line
        self.assertEqual(denial_count(props, [], "red")["props_on_line"], 3)   # the head spans X9, X12 and a cone

    def test_head_pulls_letter_cubes_off_the_fortress_cube_level(self):
        intake = load_intake()
        props = field_props(ELEMENTS)
        k, e = [p for p in props if p.alliance == "red" and p.label in "KE" and p.y < fl.CY - 150]
        pose = RobotPose((k.x + e.x) / 2, k.y - 300.0, math.pi / 2)          # facing north, head over the level
        for _ in range(30):
            rake_props(pose, 150.0, True, props, ELEMENTS, 1 / 60, intake, (46.0, 145.0))
        fort = fl.get(ELEMENTS, "red_fortress")
        for cube in (k, e):
            self.assertEqual(cube.z, 0.0)                                   # off the 171 mm level, on the floor
            self.assertLess(cube.y, fort.y - fort.h / 2)                     # centre out of the fortress

    def test_not_pulling_leaves_props_alone(self):
        props = field_props(ELEMENTS)
        before = [(p.x, p.y, p.z) for p in props]
        rake_props(RobotPose(2000.0, 839.5, 0.0), 250.0, False, props, ELEMENTS, 1 / 60, load_intake(), (46.0, 145.0))
        self.assertEqual(before, [(p.x, p.y, p.z) for p in props])


class PinTest(unittest.TestCase):
    def test_pin_points(self):
        from props import pin_points
        props = [p for p in field_props(ELEMENTS) if p.kind == "pin" and p.alliance == "red"]
        self.assertEqual(pin_points(props, ELEMENTS, "red")["points"], 0)          # still on the shelves
        props[0].x, props[0].y, props[0].z = 98.0, 1500.0, 405.0                  # in the pin placement area
        props[1].x, props[1].y, props[1].z = 1200.0, 1000.0, 0.0                  # on our floor
        props[2].x, props[2].y, props[2].z = 2300.0, 1000.0, 0.0                  # not completely on our side
        self.assertEqual(pin_points(props, ELEMENTS, "red"), {"placement_area": 1, "floor": 1, "points": 40})

    def test_pin_drops_onto_the_placement_area_shelf(self):
        pin = next(p for p in field_props(ELEMENTS) if p.kind == "pin")
        pin.x, pin.y = 98.0, 1500.0
        self.assertEqual(support_under(pin, ELEMENTS), 405.0)


class MakeBonusTest(unittest.TestCase):
    def test_make_in_order_on_the_lower_side(self):
        from props import make_bonus
        props = [p for p in field_props(ELEMENTS) if p.kind == "letter" and p.alliance == "red"]
        by_label = {}
        for p in props:
            by_label.setdefault(p.label, p)
        channels = sorted((e for e in ELEMENTS if e.name.startswith("strategy_lower_channel")), key=lambda e: e.y)
        for letter, ch in zip("MAKE", channels):                          # outside (wall) to inside
            cube = by_label[letter]
            cube.x, cube.y, cube.z = ch.x - 80, ch.y, CHANNEL_RAIL_Z          # partly in, on the rails
        result = make_bonus(props, ELEMENTS, "red")
        self.assertEqual((result["sides"], result["points"]), (["lower"], 50))
        by_label["A"].z = 0.0                                              # on the map: not valid
        self.assertEqual(make_bonus(props, ELEMENTS, "red")["points"], 0)


class PushTest(unittest.TestCase):
    BODY = [(-250.0, -250.0, 0.0, 115.0, 250.0, 260.0)]

    def test_robot_pushes_a_cube_out_of_its_body(self):
        from props import push_props
        cube = Prop("c", "bonus", "X9", "neutral", 1000.0 + 115 + 50, 600.0, 0.0)   # 10 mm into the front
        push_props(RobotPose(1000.0, 600.0, 0.0), self.BODY, [cube], ELEMENTS, [])
        self.assertAlmostEqual(cube.x, 1000.0 + 115 + 60 + 0.5)
        self.assertAlmostEqual(cube.y, 600.0)

    def test_structure_blocks_the_push_and_slot_lets_it_in(self):
        from props import push_props
        cube = Prop("c", "bonus", "X9", "neutral", 1165.0, 600.0, 0.0)
        wall = [(1220.0, 0.0, 0.0, 1300.0, 3000.0, 500.0)]
        jammed = push_props(RobotPose(1000.0, 600.0, 0.0), self.BODY, [cube], ELEMENTS, wall)
        self.assertEqual(jammed, ["c"])
        self.assertEqual(cube.x, 1165.0)                                          # jammed, not moved
        slot = [(100.0, -60.0, 0.0, 300.0, 60.0, 200.0)]                           # free space at the front
        self.assertEqual(push_props(RobotPose(1000.0, 600.0, 0.0), self.BODY, [cube], ELEMENTS, [], slot), [])
        self.assertEqual(cube.x, 1165.0)

    def test_pushed_off_the_strategy_top_it_drops(self):
        from props import push_props
        cube = Prop("c", "bonus", "X12", "neutral", 2250.0, 840.0, 259.0)          # 30 mm inside the edge
        robot = RobotPose(2250.0 + 60 + 250 - 50, 840.0, 0.0)                       # its back 50 mm into the cube
        push_props(robot, [(-250.0, -250.0, 0.0, 115.0, 250.0, 645.0)], [cube], ELEMENTS, [])
        self.assertAlmostEqual(cube.x, 2199.5)                                      # centre off the top (x 2220)
        self.assertEqual(cube.z, 0.0)


class BonusRuleTest(unittest.TestCase):
    def setUp(self):
        self.props = field_props(ELEMENTS)
        self.area = fl.get(ELEMENTS, "red_exchange_1")
        self.area2 = fl.get(ELEMENTS, "red_exchange_2")

    def put(self, name, x, y):
        p = prop_named(self.props, name)
        p.x, p.y, p.z = x, y, 0.0
        return p

    def test_partial_overlap_is_valid(self):
        self.put("prop_lower_3", self.area.x, self.area.y + self.area.h / 2 + 40)   # 20 mm inside
        self.assertEqual(bonus_state(self.props, ELEMENTS, "red")["valid"], ["X12"])

    def test_two_in_one_area_are_invalid(self):
        self.put("prop_lower_3", self.area.x - 40, self.area.y)
        self.put("prop_lower_2", self.area.x + 40, self.area.y)
        self.assertEqual(bonus_state(self.props, ELEMENTS, "red")["valid"], [])     # rule c

    def test_more_than_two_on_our_side_invalidates_all(self):
        self.put("prop_lower_3", self.area.x, self.area.y)
        self.put("prop_lower_2", self.area2.x, self.area2.y)
        self.put("prop_upper_2", 1500.0, 1500.0)                                    # a third on our side
        self.assertEqual(bonus_state(self.props, ELEMENTS, "red")["valid"], [])     # rule d

    def test_held_cube_does_not_count(self):
        p = self.put("prop_lower_3", self.area.x, self.area.y)
        p.held = True
        self.assertEqual(bonus_state(self.props, ELEMENTS, "red")["valid"], [])     # rule e

    def test_preview_counts_letter_cubes_in_channels(self):
        slot = next(e for e in ELEMENTS if e.kind == "slot")
        cube = next(p for p in self.props if p.kind == "letter" and p.alliance == "red")
        cube.x, cube.y, cube.z = slot.x, slot.y, CHANNEL_RAIL_Z
        prev = score_preview(self.props, ELEMENTS, "red")
        self.assertEqual(prev["letter_cubes"], 1)
        self.assertEqual(prev["points_now"], 30)


if __name__ == "__main__":
    unittest.main()
