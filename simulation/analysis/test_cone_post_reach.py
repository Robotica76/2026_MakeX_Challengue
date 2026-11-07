"""Cone post reach analysis: python -m unittest (this directory)."""

import unittest

from cone_post_reach import poses


class ConePostReachTest(unittest.TestCase):
    def test_gripper_reaches_our_cone_post_from_the_east_south_east(self):
        free = {r[0] for r in poses() if r[3] == 0 and r[5] and r[6]}
        self.assertEqual(free, {240, 245, 250, 255, 260})          # the driver uses 250

    def test_lane_a_cone_is_taken_only_off_the_shelf_legs(self):
        clear = lambda xy: {r[0] for r in poses(xy, 15) if r[3] == 0 and r[5] and r[6]}  # noqa: E731
        self.assertEqual(clear((2105.0, 378.0)), set())             # where the plain lane a pull leaves it
        self.assertIn(30, clear((2029.0, 535.0)))                   # PULL_A_DY 200


if __name__ == "__main__":
    unittest.main()
