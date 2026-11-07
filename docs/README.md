# Documentation

Engineering documentation of the 2026 MakeX Challenge **Storm Breaker** robot, following the
engineering lifecycle. Technical values are CAD or simulation results unless a test report says
otherwise.

| Stage | Workspace | Content today |
| --- | --- | --- |
| Understand | [01 Requirements](01_requirements/README.md) | Rules Guide V1.1, compliance matrix (T01, T02, T17 vs v22 CAD) |
| Architect | [02 System architecture](02_system_architecture/README.md) | Subsystem chain, budgets |
| Design | [03 Subsystem design](03_design/README.md) | Selected concepts: chassis, ball system, shooter, manipulator, flag, electronics |
| Control | [04 Controls](04_controls/README.md) | Drivetrain motion control, stateflow, autonomous routines, manual bindings, vision plans |
| Integrate | [05 Integration](05_integration/README.md) | Known issues KI-001…KI-010, CAD integration checks |
| Verify | [06 Verification](06_verification/README.md) | Proposed test campaign, subsystem / integration / competition test plans |
| Plan operation | [07 Strategy](07_strategy/README.md) | Scoring, automatic and manual plans, Monte Carlo and reinforcement-learning searches |
| Record throughout | [08 Engineering notebook](08_engineering_notebook/README.md) | Design log (DL-T05-001, **DL-SYS-001 decision register**), lessons, media |

## Traceability

IDs: rule `R##` / `T##` (rules guide), requirement `T05-R#` etc. (team issues), decision `DEC-…`,
known issue `KI-###`, test `IT-##` / `CT-##`, log `DL-…`, lesson `LL-###`. Trace each decision from
rule → requirement → design → decision → test → result.

| Work item | Owner / reviewer | Requirement | Notebook | Status |
| --- | --- | --- | --- | --- |
| Chassis motion software | TBD (T05) | T05-R1…R9 | DL-T05-001 | Simulated; calibration pending |
| Robot CAD v22 | TBD | T01, T02, T17 | DL-SYS-001 | CAD complete; build pending |
| Strategy | TBD | p.27–54 | montecarlo_strategy.md | Simulated |

## Mode sequence

`INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL → STOP` — proposal; what the
competition program does today is in [stateflow](04_controls/stateflow/README.md).
