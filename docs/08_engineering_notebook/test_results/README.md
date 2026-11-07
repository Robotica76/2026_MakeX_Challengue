# Test Results

Measured results of executed tests, with the procedure revision, configuration, and retests.
**No physical test has been executed yet**: the robot has not been built.

## What exists instead (simulation evidence, not test results)

| Evidence | What it predicts | Where |
| --- | --- | --- |
| Chassis Monte Carlo (300 sampled robots per scenario) | Moves pass the 1 cm / 1.5° criterion only with a calibrated robot | [chassis_montecarlo](../../../simulation/analysis/reports/chassis_montecarlo/README.md) |
| Automatic-stage and route Monte Carlo | P(X12 valid) 0.96 with a start jig; best orders 12 / 13 | [montecarlo_strategy.md](../../07_strategy/montecarlo_strategy.md) |
| 4-robot match Monte Carlo (80 matches) | Margin red − blue +31 … +64 ± 70 points; flag hung in 55/80 matches | [four_robots report](../../../simulation/analysis/reports/four_robots/REPORTE.md) |
| Mechanism 2D simulations | Intake → tower → elbow → basket → launcher works for a single ball | per subsystem `prototypes/` in [mechanical](../../../mechanical/README.md) |

## Recording a result

| Result ID / date | Test / procedure revision | Requirement IDs | Hardware / software configuration | Measurements with units and uncertainty | Pass / fail vs agreed criterion | Corrective action / retest |
| --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Store the raw data with the report under [`tests/`](../../../tests/README.md) and link it here. Never mark
an unperformed test as passed; keep failed results.
