# Target selection

| Target | How it is chosen today | Where |
| --- | --- | --- |
| Automatic missions | Fixed order `ORDER` (digits = missions 1 X12, 2 deny X9 + cone, 3 / 4 table balls), each skipped if it does not fit before `END_BY`; order chosen by Monte Carlo (DEC-T01) | [`storm_breaker_2026.py`](../../robot/main/storm_breaker_2026.py) `automatic()`, `mission_N()` |
| Strategy before the start | N2 / N3 / N4 (`bonus`, `balls`, `props`) | [`robot_2026.py`](../../robot/main/robot_2026.py) |
| Shot target | R2: blue fortress, N3: X mark — heading and power from the odometry distance (DEC-S06) | `aim_N_N_N_N()` |

Not implemented: choosing targets from the AI camera (bonus cube identity, fortress position) —
see [vision](../../vision/README.md).
