# Task execution

Automatic-stage routines (30 s, Red Start 1). They run on the robot through the competition
program or alone, and in the [2D / 3D simulators](../../../simulation/README.md).

| File | Routine | Status |
| --- | --- | --- |
| [`auto_pull_central.py`](auto_pull_central.py) | Pull central resources onto our side; strategies `bonus` (default: X12 into exchange area 1), `balls`, `props`; `run(strategy)` is called by `robot_2026.py` | Simulated; route from `optimize_auto_route.py` |
| [`auto_central_then_cubes.py`](auto_central_then_cubes.py) | Earlier plan: central balls first (up to 18), then the X12 and a cone with the gripper | Simulated; superseded by the X12-first plan (DEC-T01) |

The current competition automatic stage is inside
[`storm_breaker_2026.py`](../../robot/main/storm_breaker_2026.py) (`mission_N`). Rules respected in code:
R06 (stay in our area, 3 s grace), R19 (stationary at 30 s: `END_BY`, `HARD_STOP`), R23, R26.
Ports `DC1`, `DC2`, `DC3`, `DC6`, `DC7` are assumptions until wired.
