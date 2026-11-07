# Localization

Odometry is implemented inside the drive code, not as a separate module:

| Implementation | Method | Frame / units |
| --- | --- | --- |
| [`chassis.py`](../../controls/drivetrain/chassis.py) `odo` | 4 encoders (mecanum unmix) for distance, gyroscope for heading, gyro bias calibrated at rest (`odo.calibrate()`), reset with `odo.reset()` | Field frame at the reset point, cm, degrees; reports the footprint centre (wheel centre 7.9 cm behind) |
| [`storm_breaker_2026.py`](../../robot/main/storm_breaker_2026.py) `read_odometry()`, `calibrate_N_N_N`, `set_pose_N_N_N` | Same, in mm and field coordinates of Red Start 1; strafe distance scaled by `STRAFE_SLIP` | Field mm, degrees |

Accuracy is limited by calibration, not by the algorithm
([chassis Monte Carlo](../../../simulation/analysis/reports/chassis_montecarlo/README.md), DEC-S05).
Not yet available: absolute fixes (walls, ranging sensors, AI camera). The flag routine hangs in
only 55 / 80 simulated matches because of accumulated odometry error.
