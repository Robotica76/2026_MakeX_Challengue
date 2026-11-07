"""Two identical robots on one field: python -m unittest (this directory)."""

import math
import unittest

from two_robots import obb_overlap, play, turned


class TwoRobotsTest(unittest.TestCase):
    def test_turned_frame_and_footprint_overlap(self):
        self.assertEqual(turned(325.0, 325.0, 0.0), (4330.0, 2730.0, 180.0))

        class P:
            def __init__(self, x, y, t):
                self.x, self.y, self.theta = x, y, t
        self.assertAlmostEqual(obb_overlap(P(0, 0, 0), P(480, 0, 0)), 20.0)
        self.assertEqual(obb_overlap(P(0, 0, 0), P(520, 0, math.pi / 2)), 0.0)

    def test_twin_runs_the_same_automatic_stage_on_the_blue_side(self):
        out = play(12, 12, seconds=31.0, trace_every=0)
        red, blue = out["red"].sim, out["blue"].sim
        self.assertEqual(red.bonus_judged["red"]["valid"], ["X12"])
        self.assertEqual(red.bonus_judged["blue"]["valid"], ["X6"])        # the X12 spot turned holds the X6
        self.assertEqual(out["contacts"], [])
        self.assertEqual(red.collisions.collisions + blue.collisions.collisions, [])
        self.assertGreater(blue.pose.x, 2435.0)                            # the twin stayed on its side


if __name__ == "__main__":
    unittest.main()
