# Autonomous software

| Directory | Content today |
| --- | --- |
| [task_execution](task_execution/README.md) | Automatic-stage routines (`auto_pull_central.py`, `auto_central_then_cubes.py`) |
| [path_following](path_following/README.md) | Points to the closed-loop moves in `chassis.py` and the profiled `go_…` in the competition program |
| [localization](localization/README.md) | Encoder + gyro odometry (inside the drive code) |
| [navigation](navigation/README.md) | Motor smoke test; routes planned offline in simulation |
| [target_selection](target_selection/README.md) | Mission order, aim targets |
| [arbitration](arbitration/README.md) | No module: one control loop owns all actuators |

Strategy behind the routines: [autonomous strategy](../../docs/07_strategy/autonomous_strategy.md),
[Monte Carlo](../../docs/07_strategy/montecarlo_strategy.md).
