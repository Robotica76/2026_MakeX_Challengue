# Chassis Prototypes

**Status (v22): no physical prototype has been built.** The figures below are CAD-based simulations (2D single-ball contact models or rigid-body estimates); they define what to measure, not results.

## Simulation evidence (v22 design inputs)

| Figure | What it shows |
| --- | --- |
| [`simulacion_inercia_vuelco_v21.png`](v22/simulacion_inercia_vuelco_v21.png) | CG (measured in CAD) over the wheel polygon in 5 configurations and the acceleration that tips the robot in each direction |
| [`simulacion_inercia_frenado_v21.png`](v22/simulacion_inercia_frenado_v21.png) | Forward pitch when braking at 0.35 g and 0.6 g, and the frontal impact speed that tips the robot |
| [`simulacion_inercia_maniobra_v21.png`](v22/simulacion_inercia_maniobra_v21.png) | Yaw time limited by friction and the fastest start / stop without tipping |

## Test plan

| Test | Measure | Pass criterion (from CAD / simulation) |
| --- | --- | --- |
| Static tip angle | Tilt the robot forward until it tips (empty, gripper up + pin) | ≥ 26° / ≥ 22° (CAD CG) |
| Braking | Peak deceleration logged from the encoders when stopping from 1.5 m/s | Software limit 0.35 g; no front-wheel lift |
| Frontal impact | Drive into a padded wall at increasing speed | No tip below 0.85 m/s (CAD estimate, worst case) |
| Mass and CG | Scale per wheel | Total ≤ 10 kg, CG y ≈ −43 mm, z ≈ 176–181 mm |

Record each test with date, robot revision, configuration, number of trials, and raw data before changing the design.
