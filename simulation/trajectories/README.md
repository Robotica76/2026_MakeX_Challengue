# Trajectory studies

Trajectories are computed inside the field simulator and the analysis scripts rather than kept here:

| Study | Script | Output |
| --- | --- | --- |
| Automatic-stage route (lanes, clearances to table legs / cone posts) | [`optimize_auto_route.py`](../analysis/optimize_auto_route.py) | Waypoints written into `auto_pull_central.py` |
| Every mission order | [`montecarlo_routes.py`](../analysis/montecarlo_routes.py) | `ORDER` of `storm_breaker_2026.py` |
| Ball flight (shots, X mark, pins) | [`field2d/ball_physics.py`](../field2d/ball_physics.py), [`pin_shots.py`](../analysis/pin_shots.py) | Aim assist parameters |
| Reach studies (pins, cone post, letter cubes) | [`pin_reach.py`](../analysis/pin_reach.py), [`cone_post_reach.py`](../analysis/cone_post_reach.py), [`letter_cube_reach.py`](../analysis/letter_cube_reach.py) | Feasibility (pins not reachable; cone post needs 430 mm elevator travel) |

Field geometry comes from [`field2d/field_layout.py`](../field2d/field_layout.py) (rules guide V1.1, estimates noted in the file).
