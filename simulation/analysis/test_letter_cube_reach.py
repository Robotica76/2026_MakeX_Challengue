"""Letter cube reach analysis: python -m unittest (this directory)."""

import unittest

from letter_cube_reach import check


class LetterCubeReachTest(unittest.TestCase):
    def test_v22_gripper_cannot_reach_and_a_longer_one_reaches_k_and_e(self):
        free = lambda rows: {r[0] for r in rows if r[7] == 0 and not r[9] and r[10] == 0}  # noqa: E731
        self.assertEqual(free(check(0.0)), set())
        self.assertEqual(free(check(150.0)), {"K", "E"})


if __name__ == "__main__":
    unittest.main()
