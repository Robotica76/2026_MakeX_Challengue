# Path following

| Implementation | Controller |
| --- | --- |
| [`chassis.py`](../../controls/drivetrain/chassis.py): `drive`, `forward`, `right`, `turn`, `turn_to` | Closed loop on odometry with heading hold; `RAMP` limits acceleration; returns `True` on arrival; `on_cycle` runs mechanisms while moving |
| [`storm_breaker_2026.py`](../../robot/main/storm_breaker_2026.py): `go_N_N_N_N_N(x, y, heading, v_max, v_end)`, `travel_N_N_N_N_N` | Point-to-point in field coordinates, translating and turning together; speed profile with `A_MAX` and braking `v = √(v_end² + 2·D_MAX·d)`; `v_end > 0` passes a waypoint without stopping (DEC-S05) |

Gains and tolerances (`TOL_CM`, `TOL_DEGREES`, `POS_TOL`, `K_HEADING`) are set from the
[Monte Carlo study](../../../simulation/analysis/README.md); they must be recalibrated on the robot
([drivetrain motion control](../../../docs/04_controls/drivetrain_motion_control.md)).
