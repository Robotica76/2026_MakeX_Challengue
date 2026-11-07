# Controls

Control intent, contracts and the decisions behind the robot programs in
[`software/`](../../software/README.md).

| Workspace | Scope |
| --- | --- |
| [Stateflow](stateflow/README.md) | Match modes as implemented in the competition program, transitions to complete |
| [Autonomous](autonomous/README.md) | Automatic-stage routines, their code and stopping rules |
| [Manual control](manual_control/README.md) | Gamepad bindings, modes, handoff |
| [Vision](vision/README.md) | AI camera plans (bonus cube, fortress) |
| [Drivetrain motion control](drivetrain_motion_control.md) | Reused 2025 functions, odometry, closed loop, adaptive S-curve, profiled motion, calibration parameters |

| Control decision | Rule / requirement | Notebook | Verification |
| --- | --- | --- | --- |
| [Drivetrain odometry, closed-loop moves, adaptive S-curve](drivetrain_motion_control.md) | T05-R4, R5, R8, R9 | [DL-T05-001](../08_engineering_notebook/design_log/DL-T05-001_chassis_motion_software.md) | T05-R8, T05-R9 (not executed) |
| Fronts as angles for the v22 layout | T05, T20 | DEC-S02 | Simulator demo |
| Blocks-expressible Python, profiled point-to-point motion | — | DEC-S04, DEC-S05 | Simulator, Monte Carlo |
| Aim assist (R2 fortress, N3 X mark) | p.36, p.44 | DEC-S06 | Simulation |
