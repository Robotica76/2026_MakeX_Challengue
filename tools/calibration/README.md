# Calibration support

Calibration is the main requirement found by the [chassis Monte Carlo](../../simulation/analysis/reports/chassis_montecarlo/README.md)
(LL-003). Procedures to run on the robot as soon as it drives, with the constant each one sets:

| Measurement | Procedure | Sets | Target residual (calibrated scenario) |
| --- | --- | --- | --- |
| Effective wheel diameter / forward slip | Drive 2–3 m straight, compare tape measure vs encoders | `WHEEL_DIAMETER` / `DEGREES_PER_CM`, `WHEEL_MM_PER_DEG` | ~0.2 % |
| Strafe slip | Strafe 1 m, compare | `STRAFE_FACTOR` (`chassis.py`), `STRAFE_SLIP` (`storm_breaker_2026.py`) | 0.3–0.5 % |
| Gyro scale | 10 full turns on a mark | gyro scale (not yet a constant in `chassis.py`) | ~0.2 % |
| Gyro drift / bias | 60 s at rest | bias (calibrated at start by `odo.calibrate()`) | — |
| Turn geometry | 10 × 360° open loop | `CM_PER_TURN_DEGREE` (0.603 cm/° from CAD) | — |
| Mechanism speeds | Time head lift, carriage, jaw end to end | DC2 53 mm/s, DC3 150 mm/s, DC6 (estimates) | — |
| Shooter | Exit speed vs power, range table at 1, 2, 3 m | `SHOT_SPEED_FULL`, `HOOD_DEG` | — |
| Start jig | 10 placements, measure heading | jig design (2 mm / 0.3° assumed) | — |

Record each run in [`tests/`](../../tests/README.md) and the values in the
[drivetrain motion control](../../docs/04_controls/drivetrain_motion_control.md) parameter tables. Then rerun
the Monte Carlo with `montecarlo_config_calibrated.json` replaced by the measured ranges.
