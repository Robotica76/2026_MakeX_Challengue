# Control Simulations

Investigate candidate feedback strategies and subsystem coordination in simulation, not production robot software.

TBD: study objective, plant/model revision, command and feedback semantics, observation timing, uncertainty, limits, disturbances, fault cases, and performance criteria. Compare alternatives without assuming a controller family, framework, or tuning values.

Use [robot/mechanism models](../robot_model/README.md) and planned [electrical interfaces](../../electrical/README.md). Record assumptions and simulated results separately from eventual physical validation.

## Chassis control demos

Programs run in the [2D simulator](../field2d/README.md#chassis-demos-simulationcontrol)
against the real robot module `software/controls/drivetrain/chassis.py`, imported
unchanged:

- `test_chassis_control_automatico.py`: closed-loop moves (encoders + gyroscope),
  prints whether each arrived and the odometry pose.
- `test_chassis_control_manual.py`: `joystick_drive` driven from the emulated
  gamepad (Open gamepad in the viewer).

Simulated results check the control logic with ideal wheels (no slip, no motor
dynamics, no collisions); they do not replace calibration on the robot.
