# Subsystem controls

| Directory | Content |
| --- | --- |
| [drivetrain](drivetrain/README.md) | [`chassis.py`](drivetrain/chassis.py): mecanum drive, odometry, closed-loop moves, adaptive S-curve (DEC-S01…S03) |
| [ball_system](ball_system/README.md) | Intake / tower / feed roller ports and modes |
| [shooter](shooter/README.md) | Brushless power from distance |
| [manipulator](manipulator/README.md) | Elevator carriage and jaw |
| [flag](flag/README.md) | `hang_flag()` and its mismatch with the v22 mast (KI-008) |

Except `chassis.py`, the subsystem functions live inside the competition programs in
[robot/main](../robot/main/README.md) (mBlock uploads one file; see DEC-S04).
