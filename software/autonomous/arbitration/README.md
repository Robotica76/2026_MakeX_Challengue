# State machine and arbitration

**Status:** no separate module. In both competition programs a single loop owns every actuator,
so there is nothing to arbitrate yet:

| Program | Flow |
| --- | --- |
| [`storm_breaker_2026.py`](../../robot/main/storm_breaker_2026.py) | wait for N1 → `automatic()` (if `STRATEGY > 0`) → `manual_loop()`; N4 in the manual loop runs `hang_flag()` |
| [`robot_2026.py`](../../robot/main/robot_2026.py) | `wait_for_start()` (N2/N3/N4 pick the strategy, N1 starts) → `automatic(strategy)` → `manual()` |

Mode table and missing transitions (fault, loss of communication, stop):
[stateflow](../../../docs/04_controls/stateflow/README.md). Add a module here only when a second
command source needs priorities (e.g. vision corrections during the automatic stage).
