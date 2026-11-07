# System Architecture

Boundaries, interfaces and budgets of the robot. The architecture implemented in CAD v22 is:

```text
          +---------------- gripper elevator (5) ---- carriage + gripper (6) ---- flag mast (9, modification stage)
          |
chassis (1) + electronics box (2)
          |
          +-- ball intake + UR arm (4) --> tower (3) --> elbow --> basket + feed roller (8) --> inverted launcher (7)
```

(numbers = subsystem numbers of the [v22 manual](../../mechanical/assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf)).

| Document | Scope | Status |
| --- | --- | --- |
| [Robot architecture](robot_architecture.md) | Subsystem responsibilities and flows | Template |
| [Mechanical interfaces](mechanical_interfaces.md) | Mounting, clearance, frames | Template; v22 frame in [full_robot v22](../../mechanical/assemblies/full_robot/v22/README.md#frame-and-units) |
| [Electrical architecture](electrical_architecture.md) | Power, signals | Template; components in [electronics design](../03_design/electronics/README.md) |
| [Software architecture](software_architecture.md) | Ownership, mode model | Proposal; implemented flow in [stateflow](../04_controls/stateflow/README.md) |
| [Weight and power budget](weight_power_budget.md) | Budgets | Template; CAD mass 9.88 kg (9.92 with the flag mast) |

Decisions that shaped the architecture: [DL-SYS-001](../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md)
(fixed launcher, 3-wide tower, inverted launcher, electronics box, removable flag mast).
