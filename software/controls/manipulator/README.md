# Manipulator controls

| Function | Port | Code |
| --- | --- | --- |
| Elevator carriage (DC-37 50 RPM, 90T GT2 → 150 mm/s) | DC3 | `carriage_to_N(mm)` (time-based), Up/Down in gripper mode |
| Gripper jaw (lead screw, + closes) | DC6 | `jaw_N(seconds)`, Left/Right in gripper mode |

Jobs run while the robot drives (`service_jobs()`, `wait_jobs()`). Positions are time-based (no
encoder on DC motors): calibrate speeds on the robot. Travel used in simulation is 430 mm vs
358 mm in CAD (KI-009). Hardware: [gripper](../../../mechanical/gripper/README.md),
[gripper_elevation](../../../mechanical/gripper_elevation/README.md).
