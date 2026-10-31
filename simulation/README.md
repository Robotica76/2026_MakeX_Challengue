# Simulation

Design investigation workspace. The first executable study is the [2D field layout](field2d/README.md) (Python + pygame); no robot model, controller, or tuning is selected yet.

| Directory | Intended studies |
| --- | --- |
| [robot_model](robot_model/README.md) | Robot-level models and local mechanism models with explicit assumptions |
| [control](control/README.md) | Control simulations, feedback/interface studies, and sensitivity to uncertainty |
| [trajectories](trajectories/README.md) | Robot-motion and mechanism-motion trajectory studies |
| [analysis](analysis/README.md) | Design calculations, parameter studies, and simulation data analysis |
| [field2d](field2d/README.md) | 2D field layout and viewer for autonomous-motion tests (robot as a box) |
| [field3d](field3d/README.md) | 3D view of the same simulation with the v22 CAD robot (Panda3D) and a UDP state stream for Unreal / ROS 2 bridges |

TBD for every study: question, owner, model revision, input sources, units/frames, assumptions, validity limits, experiment definition, comparison criteria, and evidence. Separate sourced inputs, estimates, predictions, and measurements.

Reference [mechanical designs](../mechanical/README.md), [electrical interfaces](../electrical/README.md), and authorized [field/game resources](../resources/README.md). Simulations inform decisions; they do not prove competition compliance or physical performance. Other framework/tool selections remain open.
