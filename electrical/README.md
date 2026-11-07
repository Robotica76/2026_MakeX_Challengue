# Electrical

Controller, power, actuators and sensors of the v22 robot (MakeX kit). Nothing is wired yet; port
numbers are assumptions shared with the simulator ([`robot_config.json`](../simulation/field2d/robot_config.json)).

| Directory | Content |
| --- | --- |
| [architecture](architecture/README.md) | NovaPi + power board; motor allocation (13 / 13 DC + encoder, 2 brushless, 1 servo); 9 DC motors vs 8 DC ports (KI-010) |
| [power](power/README.md) | Battery LiPo 3S 4200 mAh, distribution, power-module visibility (KI-003) |
| [sensors](sensors/README.md) | Gyro, accelerometer, encoders, 2 ranging sensors, AI camera |
| [wiring](wiring/README.md) | Inputs for the first harness |
| [bom](bom/README.md) | Electrical parts list |

Mechanical packaging: electronics box (v22 subsystem 2, [chassis](../mechanical/chassis/README.md), DEC-M10).
