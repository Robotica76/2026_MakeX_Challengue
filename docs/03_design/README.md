# Subsystem Design

Concept-level design studies. The hardware (CAD, drawings, BOM, test plans) is under
[mechanical](../../mechanical/README.md); these pages record the concept choice and its evidence.

| Workspace | Selected concept (v22) | Decisions | Status |
| --- | --- | --- | --- |
| [Chassis](chassis/README.md) | 4 × 80 mm mecanum, closed-loop odometry | DEC-M01, DEC-M10, DEC-M11, DEC-S01…S03 | Software simulated; CAD done |
| [Ball system](ball_system/README.md) | Wide intake → 3-wide tower → elbow → basket | DEC-M03…M08 | CAD + 2D simulation |
| [Shooter](shooter/README.md) | Fixed inverted friction-wheel launcher, left side | DEC-M02, DEC-M05, DEC-S06 | CAD + simulation |
| [Manipulator](manipulator/README.md) | Single lead-screw jaw on a belt elevator; intake head as prop puller | — | CAD + field simulation |
| [Flag system](flag_system/README.md) | Removable mast with C head on the gripper carriage | DEC-M12 | CAD |
| [Electronics](electronics/README.md) | MakeX kit in a structural CF box | DEC-M10 | CAD |

Decision register: [DL-SYS-001](../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md).
