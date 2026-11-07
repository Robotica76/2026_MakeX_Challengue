"""Four robots on one field: python -m unittest (this directory)."""

import unittest

from four_robots import play


class FourRobotsTest(unittest.TestCase):
    def test_automatic_stage_with_four_robots(self):
        out = play(12, 12, seconds=30.2, trace_every=0)    # bonus judged at 30 s, before the manual moves
        robots = out["robots"]
        self.assertEqual([(r.alliance, r.role, r.half) for r in robots],
                         [("red", "main", "lower"), ("red", "partner", "upper"),
                          ("blue", "main", "upper"), ("blue", "partner", "lower")])
        host = robots[0].sim
        self.assertEqual(host.bonus_judged["red"]["valid"], ["X12"])
        self.assertEqual(host.bonus_judged["blue"]["valid"], ["X6"])
        self.assertTrue(all(r.sim.balls is host.balls for r in robots))
        partner = robots[1].sim
        self.assertLess(abs(partner.pose.y - 2730.0), 30.0)       # ORDER 0: the partner stays in Red Start 2
        self.assertEqual(out["contacts"], [])


if __name__ == "__main__":
    unittest.main()
