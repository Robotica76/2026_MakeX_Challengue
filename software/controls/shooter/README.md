# Shooter controls

| Function | Port | Code |
| --- | --- | --- |
| Friction wheels (2 brushless + ESC) | BL1 | `R1` shoot, `R2` spin-up / aim (`robot_2026.py`); `aim_N_N_N_N()` in `storm_breaker_2026.py` |
| Hood flap servo (MS-12A) | TBD | Not used in code yet (fixed ~44° assumed) |

Power from distance (`storm_breaker_2026.py`): ballistic speed for the hood angle `HOOD_DEG`,
divided by `SHOT_SPEED_FULL` (ball speed at 100 %, **to calibrate with real shots**); target
`short` mm before the fortress centre and `rise` mm above launch height. Range windows predicted by
simulation: [shooter prototypes](../../../mechanical/shooter/prototypes/README.md).
