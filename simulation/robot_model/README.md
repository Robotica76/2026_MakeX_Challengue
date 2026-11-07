# Robot and mechanism models

The robot model used by the simulators is not in this folder; it is split by what each simulator needs:

| Model | Where | Source |
| --- | --- | --- |
| Footprint, wheel centres, ports, mechanism travel / speed, ball path, gripper, flag rod | [`field2d/robot_config.json`](../field2d/robot_config.json) | v22 CAD (estimates marked) |
| Mecanum kinematics, motor-port mapping | [`field2d/kinematics.py`](../field2d/kinematics.py) | v22 wheel geometry |
| Mechanism motion (kinematic: no load, no inertia) | [`field2d/mechanisms.py`](../field2d/mechanisms.py) | `robot_config.json` |
| Imperfect-robot error model for Monte Carlo | [`field2d/uncertainty.py`](../field2d/uncertainty.py) | Estimated ranges |
| 3D mesh grouped by moving part | [`field3d/robot_model.py`](../field3d/robot_model.py), [`robot_model.json`](../field3d/robot_model.json), [`assets/storm_breaker_v22.glb`](../field3d/assets/) | STEP → GLB with [`step_to_glb.py`](../../tools/scripts/README.md) |
| Mass, CG, inertia (estimate 8.94 kg from mesh volumes) | [`field3d/robot_mass.json`](../field3d/robot_mass.json) | [`mass_properties.py`](../../tools/scripts/README.md) |

Mechanism-level 2D contact simulations of the ball path (intake, elbow, inverted launcher) were
run while designing the CAD; their figures are in each subsystem's `prototypes/` folder in
[mechanical](../../mechanical/README.md). Mass from the CadQuery model with material densities is
9.88 kg (more accurate than the mesh estimate; KI-007).
