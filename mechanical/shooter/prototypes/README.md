# Shooter Prototypes

**Status (v22): no physical prototype has been built.** The figures below are CAD-based simulations (2D single-ball contact models or rigid-body estimates); they define what to measure, not results.

## Simulation evidence (v22 design inputs)

| Figure | What it shows |
| --- | --- |
| [`simulacion_lanzador_al_reves_v19.png`](v22/simulacion_lanzador_al_reves_v19.png) | Exit angle ~44° (fixed hood) / ~54–58° (servo flap); ball speed ≈ 0.47 × wheel speed |
| [`simulacion_tiro_balistica_v19.png`](v22/simulacion_tiro_balistica_v19.png) | Wheel-speed window to land inside the Mobile Fortress top (640 mm, rim 646 mm) at 1–3 m, with air drag and an assumed 30 g ball |

## Test plan

| Test | Measure | Pass criterion (from CAD / simulation) |
| --- | --- | --- |
| Exit speed / angle | High-speed video at 8 m/s wheel | ≈ 3.7 m/s, 44° / 54° |
| Range table | Wheel speed that lands in a 640 mm box at 1, 2, 3 m | Window ±0.6–0.8 m/s; compare with the figure |
| Repeatability | Spread of 10 shots | Inside 640 mm |

Record each test with date, robot revision, configuration, number of trials, and raw data before changing the design.
