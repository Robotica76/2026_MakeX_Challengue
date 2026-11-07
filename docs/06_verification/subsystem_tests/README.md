# Subsystem Test Planning

One plan per subsystem; the detailed procedures are in each mechanical subsystem's
`prototypes/README.md`.

| Subsystem | Test plan | Key criterion |
| --- | --- | --- |
| Chassis | [chassis prototypes](../../../mechanical/chassis/prototypes/README.md) | Tip angle, braking, mass |
| Ball intake | [ball_intake prototypes](../../../mechanical/ball_intake/prototypes/README.md) | ≥ 9/10 floor pick-ups |
| Tower (feeder) | [feeder prototypes](../../../mechanical/feeder/prototypes/README.md) | 10/10 elbow hand-offs at 0.42 m/s |
| Basket + feed roller | [ball_storage prototypes](../../../mechanical/ball_storage/prototypes/README.md) | Holds when stopped, feeds one at a time |
| Shooter | [shooter prototypes](../../../mechanical/shooter/prototypes/README.md) | Range table |
| Gripper / elevator | [gripper](../../../mechanical/gripper/prototypes/README.md), [gripper_elevation](../../../mechanical/gripper_elevation/prototypes/README.md) | Grip and stroke |
| Flag mast | [flag_system prototypes](../../../mechanical/flag_system/prototypes/README.md) | Hangs on a real bar |
| Drive software | [T05-R8, T05-R9](../../03_design/chassis/README.md) | 3 m < 5 cm, 90° < 5° |

Reports: [`tests/subsystem`](../../../tests/subsystem/README.md).
