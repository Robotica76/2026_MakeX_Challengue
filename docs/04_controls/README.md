# Controls

Document control intent and contracts without implementation.

| Workspace | Scope |
| --- | --- |
| [Stateflow](stateflow/README.md) | Mode transitions, guards, arbitration, exceptional paths |
| [Autonomous](autonomous/README.md) | Routine contracts and evidence requirements |
| [Manual control](manual_control/README.md) | Operator mappings and command handoff |
| [Vision](vision/README.md) | Optional perception feasibility and data contracts |
| [Drivetrain motion control](drivetrain_motion_control.md) | Reused 2025 functions, control decisions, calibration parameters, TODO |

Intended sequence: `INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL → STOP`, pending official rules verification.

Future top-level mode management: `software/robot/main/`. Future state machine/arbitration: `software/autonomous/arbitration/`. These are documentation references, not implemented paths.

| Control decision | Requirement / rule IDs | Interface IDs | Owner / reviewer | Notebook record | Verification ID |
| --- | --- | --- | --- | --- | --- |
| [Drivetrain odometry, closed-loop moves, adaptive S-curve](drivetrain_motion_control.md) | T05-R4, R5, R8, R9 | Drive motors M1–M4, NovaPi IMU, gamepad | TBD (T05 assignees) / TBD | [DL-T05-001](../08_engineering_notebook/design_log/DL-T05-001_chassis_motion_software.md) | T05-R8, T05-R9 (not executed) |

Coordinate [software architecture](../02_system_architecture/software_architecture.md), [integration](../05_integration/README.md), and [notebook decisions](../08_engineering_notebook/README.md).
