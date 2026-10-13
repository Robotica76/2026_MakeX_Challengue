# Controls

Document control intent and contracts without implementation.

| Workspace | Scope |
| --- | --- |
| [Stateflow](stateflow/README.md) | Mode transitions, guards, arbitration, exceptional paths |
| [Autonomous](autonomous/README.md) | Routine contracts and evidence requirements |
| [Manual control](manual_control/README.md) | Operator mappings and command handoff |
| [Vision](vision/README.md) | Optional perception feasibility and data contracts |

Intended sequence: `INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL → STOP`, pending official rules verification.

Future top-level mode management: `software/robot/main/`. Future state machine/arbitration: `software/autonomous/arbitration/`. These are documentation references, not implemented paths.

| Control decision | Requirement / rule IDs | Interface IDs | Owner / reviewer | Notebook record | Verification ID |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD |

Coordinate [software architecture](../02_system_architecture/software_architecture.md), [integration](../05_integration/README.md), and [notebook decisions](../08_engineering_notebook/README.md).
