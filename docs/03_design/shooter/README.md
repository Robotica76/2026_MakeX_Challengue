# Shooter Design Study

Scoring target: the opponent's **Mobile Fortress** upper area (rules p.25, p.36): 10 points per ball,
20 for bonus balls. Selected concept (v22): fixed **inverted friction-wheel launcher** on the left
side, firing `−x` ([DEC-M02, DEC-M05](../../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md)). Hardware: [mechanical/shooter](../../../mechanical/shooter/README.md).

## Concept and predicted performance (simulation)

| Item | Value | Source |
| --- | --- | --- |
| Wheel / hood | D45 friction wheel on top, PC hood R82.5 below, servo flap | v22 CAD |
| Exit angle | ~44° fixed hood, ~54–58° with the flap | 2D contact simulation |
| Ball exit speed | ≈ 0.47 × wheel surface speed | same |
| Wheel speed to land in the 640 mm top | 8.2–9.6 m/s at 1 m, 10.7–11.9 at 2 m, 12.8–14.0 at 3 m (44°, 30 g ball assumed) | [ballistics figure](../../../mechanical/shooter/prototypes/README.md) |
| Aiming | Whole robot turns (mecanum); R2 assist sets heading and power from odometry ([DEC-S06](../../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md)) | [storm_breaker_2026.py](../../../software/robot/main/README.md) |
| Simulated match | 18 of 30 shots stay in the fortress | [scoring strategy](../../07_strategy/scoring_strategy.md) |

## Prototype and repeatability plan

| Prototype revision | Setup | Controlled variables | Measurements | Acceptance | Result |
| --- | --- | --- | --- | --- | --- |
| P1 (not built) | Launcher module on a bench, balls from a basket | Wheel speed, hood flap | Exit speed / angle (video), landing spread | Inside a 640 mm box at 1, 2, 3 m | — |

Unknowns: real ball mass (not in the rules), spin, brushless top speed on the D45 wheel.
