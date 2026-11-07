# Navigation

| File | Content |
| --- | --- |
| [`basic_movement.py`](basic_movement.py) | First motor test (2026-10-19): the four drive motors at 10 RPM. Kept as a wiring smoke test |

Route planning is done **offline in simulation** and written into the programs as waypoints:
[`optimize_auto_route.py`](../../../simulation/analysis/optimize_auto_route.py) (automatic-stage lanes,
clearances to table legs and cone posts) and [`montecarlo_routes.py`](../../../simulation/analysis/montecarlo_routes.py)
(every mission order). The resulting coordinates live in
[`auto_pull_central.py`](../task_execution/auto_pull_central.py) and
[`storm_breaker_2026.py`](../../robot/main/storm_breaker_2026.py).
