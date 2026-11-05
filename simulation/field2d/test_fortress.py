"""Mobile fortress on casters: python -m unittest (this directory)."""

import math
import unittest

import field_layout as fl
from fortress import FortressMotion
from props import field_props
from robot import RobotPose

BODY = [(-250.0, -250.0, 0.0, 115.0, 250.0, 645.0)]
HEAD_AT = lambda lift: [(115.0, -190.0, 46.0 + lift, 249.0, 202.0, 145.0 + lift)]  # noqa: E731


def fortress(elements):
    return fl.get(elements, "red_fortress")


class FortressMotionTest(unittest.TestCase):
    def setUp(self):
        self.elements = fl.build_field()
        self.motion = FortressMotion.for_elements(self.elements)
        self.f0 = fortress(self.elements)

    def test_robot_front_pushes_it_north_with_its_letter_cubes(self):
        props = field_props(self.elements)
        cubes = [p for p in props if p.kind == "letter" and p.alliance == "red"]
        before = [(p.x, p.y) for p in cubes]
        y = self.f0.y - self.f0.h / 2 - 115.0 + 20.0            # body front 20 mm into the south side
        moved = self.motion.update(0.0, 0.01, RobotPose(self.f0.x, y, math.pi / 2), BODY, self.elements, props)
        f = fortress(self.elements)
        self.assertIn("red_fortress", moved)
        self.assertAlmostEqual(f.y - self.f0.y, 20.0, delta=0.6)
        self.assertAlmostEqual(f.x, self.f0.x, delta=0.6)
        for (x, y0), p in zip(before, cubes):
            self.assertAlmostEqual(p.y - y0, f.y - self.f0.y)
        self.assertAlmostEqual(self.motion.offsets["red_fortress"][1], f.y - self.f0.y)
        self.assertEqual(len(self.motion.pushes), 1)

    def test_head_over_the_cube_level_goes_in_without_pushing(self):
        y = self.f0.y - self.f0.h / 2 - 249.0 + 40.0            # head 40 mm in, above the 171 mm cube level
        pose = RobotPose(self.f0.x, y, math.pi / 2)
        self.assertEqual(self.motion.update(0.0, 0.01, pose, HEAD_AT(160.0), self.elements), {})
        self.assertIn("red_fortress", self.motion.update(0.0, 0.01, pose, HEAD_AT(60.0), self.elements))

    def test_stays_in_the_alliance_area_and_off_the_structures(self):
        x0 = self.f0.x - self.f0.w / 2                             # pushed west: the pin area is in the way
        moved = self.motion.update(0.0, 0.01, RobotPose(x0 + self.f0.w + 115.0 - 30.0, self.f0.y, math.pi),
                                   BODY, self.elements)
        pin = fl.get(self.elements, "red_pin_area")
        f = fortress(self.elements)
        if moved:
            self.assertGreaterEqual(f.x - f.w / 2, pin.x + pin.w / 2)
        lo, hi = fl.alliance_x_limits("red")
        self.assertGreaterEqual(f.x - f.w / 2, lo)
        self.assertLessEqual(f.x + f.w / 2, hi)


if __name__ == "__main__":
    unittest.main()
