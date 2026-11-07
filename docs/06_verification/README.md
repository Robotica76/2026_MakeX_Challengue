# Verification

Plans that turn requirements into tests. Executable tests and reports go to [`tests/`](../../tests/README.md).

| Workspace | Scope |
| --- | --- |
| [Verification plan](verification_plan.md) | Requirement → method → test mapping |
| [Subsystem tests](subsystem_tests/README.md) | Each mechanism alone |
| [Integration tests](integration_tests/README.md) | Hand-offs between subsystems, robot integration |
| [Competition tests](competition_tests/README.md) | Missions and full-match rehearsals |

## Proposed test campaign (from the CAD and simulation predictions)

| Order | Test | Predicted value to confirm | Source of the prediction |
| --- | --- | --- | --- |
| 1 | Mass and CG on scales | 9.88 kg, CG `y ≈ −43`, `z ≈ 181` mm | CAD |
| 2 | Drive calibration (wheel travel, strafe slip, gyro scale and drift) | Calibrated robot passes 1 cm / 1.5° per move | [chassis Monte Carlo](../../simulation/analysis/reports/chassis_montecarlo/README.md) |
| 3 | T05-R8 (3 m, < 5 cm drift), T05-R9 (90°, < 5°) | — | [chassis design](../03_design/chassis/README.md) |
| 4 | Static tip angle and braking | ≥ 26° empty; braking limit 0.35 g | chassis prototypes |
| 5 | Intake, tower, elbow, basket, feed, launcher (single ball, then 10 balls) | per-subsystem criteria | mechanical `prototypes/` |
| 6 | Launcher range table at 1, 2, 3 m | wheel speed windows | shooter prototypes |
| 7 | Automatic stage with the start jig (10 runs) | P(X12 valid) ≈ 0.96 | [Monte Carlo strategy](../07_strategy/montecarlo_strategy.md) |
| 8 | Flag hanging on a real bar | hangs, no contact with the robot | flag_system prototypes |
| 9 | Full-match rehearsal | score vs simulated 300–440 | [strategy](../07_strategy/README.md) |
