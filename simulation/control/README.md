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
- `test_mechanisms.py`: moves every simulated mechanism (intake rollers and head,
  tower, feeder, shooter, elevator carriage) through the `power_expand_board` ports
  (menu option 5 of the 3D launcher).
- `test_ball_collection.py`: collects the balls released from both red own resource
  areas with the intake on `DC1` (`viewer3d.py --balls released`, menu option 4 of the
  3D launcher). In simulation it fills the intake (18 balls) in about 19 s. It shows how
  tight the route is: to clear the resource-area legs and still reach both ball rows, the
  robot centre must stay within a 15 mm (area 1) and 33 mm (area 2) corridor.

Simulated results check the control logic with ideal wheels (no slip, no motor
dynamics, no collisions); they do not replace calibration on the robot.
