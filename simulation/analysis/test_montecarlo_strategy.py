"""Monte Carlo strategy search: python -m unittest (this directory)."""

import unittest

from montecarlo_strategy import program_text, summarize, trial


class MonteCarloStrategyTest(unittest.TestCase):
    def test_constants_are_replaced_inside_the_constants_block(self):
        text = program_text({"V_MAX": 555, "ORDER": 1})
        self.assertIn("    V_MAX = 555", text)
        self.assertIn("    ORDER = 1", text)
        with self.assertRaises(KeyError):
            program_text({"pos_x": 1})                    # a state variable, not a constant

    def test_one_sampled_robot_secures_the_x12(self):
        row = trial(({}, 9000))
        self.assertTrue(row["valid_x12"], row)
        self.assertEqual(row["problems"], 0, row)
        self.assertLess(row["x12_time"], 17.0)
        self.assertGreaterEqual(summarize({}, [row])["resources"], 20)


if __name__ == "__main__":
    unittest.main()
