# Sensors

| Sensor | Where (v22) | Use | Code status |
| --- | --- | --- | --- |
| Gyroscope (NovaPi) | Controller | Heading for odometry, heading hold, turns | Used (`novapi.get_gyroscope("z")`, name to confirm) |
| Accelerometer (NovaPi) | Controller | Collision detection, vibration-adaptive S-curve | Used in `chassis.py` (units to confirm) |
| Encoders (180 motors) | Wheels | Distance for odometry | Used |
| Ranging sensor | Gripper (6.14) | Distance to props | Not used yet |
| Ranging sensor S2 | Tower entry (3.18) | Ball counting | Not used yet |
| AI camera 2.0 | Elevator lid (5.7) | Bonus cube, fortress | Not used yet ([vision](../../software/vision/README.md)) |

Rules T10: up to 3 ranging sensors. Registers: [sensor_register.md](sensor_register.md), [vision_interfaces.md](vision_interfaces.md).
