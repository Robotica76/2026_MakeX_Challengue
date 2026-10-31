"""Props, gripper and automatic score preview: python -m unittest (this directory)."""

import math
import unittest

import field_layout as fl
from props import CHANNEL_RAIL_Z, CUBE, Gripper, Prop, bonus_state, field_props, load_gripper, score_preview, support_under
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
        self.assertTrue(all(p.z == 259.0 for p in props if p.kind != "letter"))   # strategy area top
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


class SupportTest(unittest.TestCase):
    def test_channel_rail_strategy_top_fortress_floor(self):
        slot = next(e for e in ELEMENTS if e.kind == "slot")
        self.assertEqual(support_under(Prop("p", "letter", "M", "red", slot.x, slot.y, 0), ELEMENTS), CHANNEL_RAIL_Z)
        strat = fl.get(ELEMENTS, "strategy_lower")
        self.assertEqual(support_under(Prop("p", "bonus", "X3", "neutral", strat.x, strat.y + 470, 0), ELEMENTS), 259.0)
        fort = fl.get(ELEMENTS, "red_fortress")
        self.assertEqual(support_under(Prop("p", "letter", "M", "red", fort.x, fort.y, 0), ELEMENTS), 171.0)
        self.assertEqual(support_under(Prop("p", "bonus", "X3", "neutral", 1500.0, 1500.0, 0), ELEMENTS), 0.0)


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
