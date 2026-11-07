# Challenge 2025 program (reference)

The 2025 competition program as the team wrote it in mBlock blocks, kept as the base for 2026:

- [`Challenge_2025.n2.mblock`](Challenge_2025.n2.mblock): the block project (mBlock 5.6, NovaPi).
- [`mblock_python_view.py`](mblock_python_view.py): the Python mBlock shows for those blocks.

The simulator runs either one (Load program). A `.mblock` is translated by
[`mblock_project.py`](../../../simulation/field2d/mblock_project.py) into that same Python;
`test_mblock_project.py` checks that both programs are identical. The 2026 program built on it is
[`software/robot/main/robot_2026.py`](../../robot/main/robot_2026.py).

The 2025 robot differs from the v22 robot (6 cm wheels, smart servos on M5 / M6, a distance
sensor on PORT5), so in the 2026 simulator it drives the v22 chassis with the 2025 commands.
