# Simulation

A field simulator written by the team to test the **real robot programs** before the robot exists
(DEC-X01), plus the analyses built on it.

| Directory | Content |
| --- | --- |
| [field2d](field2d/README.md) | 2D field (pygame): mecanum kinematics, encoders / gyro / accelerometer, mBlock runtime (`novapi`, `mbuild`), emulated gamepad, balls, props, mobile fortresses, match clock, referee and rule monitors; loads `.py` and `.mblock` programs |
| [field3d](field3d/README.md) | 3D view (Panda3D) of the same simulation with the v22 CAD robot; UDP state stream for Unreal / ROS 2; time-lapses |
| [control](control/README.md) | Demo programs (chassis, mechanisms, intake, shelf, ball collection), scripted drivers, whole-match plan |
| [analysis](analysis/README.md) | Monte Carlo of `chassis.py`, route and strategy searches, 2 and 4 robot matches, reinforcement learning, reach studies; [reports](analysis/reports/README.md) |
| [robot_model](robot_model/README.md) | Where the robot model lives (config, kinematics, mesh, mass) |
| [trajectories](trajectories/README.md) | Route and ball-flight studies |

## Run

Windows: `field2d/run_simulator.bat` or `field3d/run_simulator_3d.bat`; macOS: the `.command`
files (first run creates `.venv` and installs pygame / panda3d). Details in each README.

## Main results (simulation, v22 model)

| Question | Answer | Where |
| --- | --- | --- |
| Is `chassis.py` accurate to 1 cm / 1.5°? | Only after calibration (tolerances and slip, not gains) | [chassis Monte Carlo](analysis/reports/chassis_montecarlo/README.md) |
| Best automatic stage | X12 into exchange area 1 first; P(X12) 0.96 with a start jig | [Monte Carlo strategy](../docs/07_strategy/montecarlo_strategy.md) |
| 2 vs 2 matches | Margin +31 … +64 ± 70 points; aim at the fortress where it is | [four robots report](analysis/reports/four_robots/REPORTE.md) |

**Limits:** ideal geometry, estimated physics, robot does not collide with structures, mechanisms
are kinematic. Simulations inform decisions; they do not prove rules compliance or robot performance.
