"""2 vs 2 strategy game: python -m unittest (this directory)."""

import statistics as st
import unittest

from strategy_game import ARCHETYPES, Plan, fixed_aim_factor, play


class StrategyGameTest(unittest.TestCase):
    def test_fixed_aim_cliff(self):                      # measured: 10/13 at 0, 9-11 at 50-100, 0 at 150 mm
        self.assertEqual(fixed_aim_factor(0), 1.0)
        self.assertEqual(fixed_aim_factor(100), 1.0)
        self.assertEqual(fixed_aim_factor(150), 0.0)

    def test_same_plans_are_even(self):
        plans = ARCHETYPES["current (ours)"]
        margins = [play(plans, plans, seed=i)["red"]["total"] - play(plans, plans, seed=i)["blue"]["total"]
                   for i in range(600)]
        self.assertLess(abs(st.mean(margins)), 25)

    def test_three_bonus_cubes_on_a_side_invalidate_them(self):
        greedy = (Plan("DD", "SS", "F"), Plan("B", "SS", "F"))    # two denied + one in the exchange area
        idle = (Plan("", "SS", "F"), Plan("", "SS", "F"))
        m = play(greedy, idle, seed=3)
        self.assertGreater(len(m["cubes"]["red"]), 2)
        self.assertEqual(m["red"]["bonus_balls"], 0)

    def test_evasion_beats_fixed_aim_only(self):
        evader = (Plan("TE", "SS", "F"), Plan("B", "SS", "F"))   # B (23 s) leaves no time for E in 30 s
        plain = (Plan("B", "SS", "F"), Plan("B", "SS", "F"))
        fixed = st.mean(play(plain, evader, seed=i)["red"]["precision"] for i in range(300))
        adaptive = st.mean(play(plain, evader, seed=i, aims=("adaptive", "fixed"))["red"]["precision"] for i in range(300))
        self.assertLess(fixed, 0.3 * adaptive)


if __name__ == "__main__":
    unittest.main()
