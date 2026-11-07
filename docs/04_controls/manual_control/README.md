# Manual Control Architecture

Driver controls in the competition programs (Makeblock Bluetooth gamepad). Both programs use
two modes selected with the "≡" and "+" buttons.

## Bindings (`storm_breaker_2026.py`, `robot_2026.py`)

| Intent | Input | Command | Mode |
| --- | --- | --- | --- |
| Drive / strafe | Left stick | Toward the mode's front (intake front in ball mode, gripper front in gripper mode), acceleration limited, gyro heading hold | Both |
| Turn | Right stick X | Yaw rate | Both |
| Intake in / out | L1 / L2 | Throat DC1, head roller DC7, tower DC4 | Ball |
| Shoot / spin-up | R1 / R2 (R2 in `storm_breaker_2026`: aim at the blue fortress and set power) | BL1 + feed DC5 | Ball |
| Intake head up / down | Up / Down | DC2 | Ball |
| Elevator up / down, jaw | Up / Down, Left / Right | DC3, DC6 | Gripper |
| Pull mode | N2 | Only the head roller turns | Both (`storm_breaker_2026`) |
| Aim at the X mark | N3 held | Heading + power to the X | `storm_breaker_2026` |
| Hang the flag | N4 (in Red Start 1) | Scripted routine | Final stage |
| Reset odometry | N1 | `odo.reset()` | `robot_2026` |

## Handoff and human factors

| Scenario | Behaviour in code | Open question |
| --- | --- | --- |
| Automatic → manual | Program enters `manual_loop()` after `automatic()` | Wait for the referee signal? |
| Connection loss | Not handled | Stop all actuators after a timeout |
| Mode change while a key is held | Modes are read every cycle | Driver training |

Simulated driver: [`simulation/control/ai_driver.py`](../../../simulation/control/ai_driver.py) plays this gamepad;
see [manual strategy](../../07_strategy/manual_strategy.md).
