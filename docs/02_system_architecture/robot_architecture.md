# Robot Architecture

Proposed decomposition for discussion; task applicability and hardware selections remain TBD.

| Study area | Candidate responsibility | Inputs | Outputs | Requirement IDs | Student owner | Decision record |
| --- | --- | --- | --- | --- | --- | --- |
| [Chassis](../03_design/chassis/README.md) | Mobility and structural support | TBD | TBD | TBD | TBD | TBD |
| [Ball system](../03_design/ball_system/README.md) | Study acquisition / transfer | TBD | TBD | TBD | TBD | TBD |
| [Shooter](../03_design/shooter/README.md) | Study release / launch concepts | TBD | TBD | TBD | TBD | TBD |
| [Manipulator](../03_design/manipulator/README.md) | Study grasp / placement | TBD | TBD | TBD | TBD | TBD |
| [Flag system](../03_design/flag_system/README.md) | Study any verified flag task | TBD | TBD | TBD | TBD | TBD |
| [Electronics](../03_design/electronics/README.md) | Power and sensing integration | TBD | TBD | TBD | TBD | TBD |
| [Controls](../04_controls/README.md) | Commands, state, control authority | TBD | TBD | TBD | TBD | TBD |

## System flows and boundaries

| Flow | Source → destination | Interface ID | Quantity / format / units | Failure or conflict | Verification |
| --- | --- | --- | --- | --- | --- |
| Mechanical load / object transfer | TBD | TBD | TBD | TBD | TBD |
| Electrical energy / signals | TBD | TBD | TBD | TBD | TBD |
| Command / state / evidence | TBD | TBD | TBD | TBD | TBD |

## Operating model

Intended mode chain: `INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL → STOP`. This is only a design proposal pending official rules verification, not a statement of match format.

Top-level mode ownership is planned under `software/robot/main/`; state machine/arbitration under `software/autonomous/arbitration/`. These are conceptual future paths, not implemented directories. See [software architecture](software_architecture.md).

| System-level risk | Requirement / interface IDs | Mitigation candidate | Evidence needed | Notebook link |
| --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD |

Confirm physical boundaries in [mechanical interfaces](mechanical_interfaces.md), power/signal boundaries in [electrical architecture](electrical_architecture.md), and ownership in the [interface matrix](../05_integration/interface_matrix.md).
