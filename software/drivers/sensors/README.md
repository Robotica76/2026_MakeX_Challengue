# Sensor drivers

| API | Sensor | Status |
| --- | --- | --- |
| `novapi.get_gyroscope("z")` | Yaw rate (heading) | Name and sign (`GYRO_SIGN`) to confirm on the robot |
| `novapi.get_acceleration(axis)` | Collision detection (`IMPACT_THRESHOLD`) | Units / axes to confirm |
| `ranging_sensor_class(port)` | Gripper distance sensor, tower entry S2 | Not used in the programs yet |
| `novapi.timer()`, `reset_timer()` | Match timing (`END_BY`) | — |

Calibration of these sensors: [tools/calibration](../../../tools/calibration/README.md).
