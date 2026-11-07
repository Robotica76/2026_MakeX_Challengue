# Ball Intake Prototypes

**Status (v22): no physical prototype has been built.** The figures below are CAD-based simulations (2D single-ball contact models or rigid-body estimates); they define what to measure, not results.

## Simulation evidence (v22 design inputs)

| Figure | What it shows |
| --- | --- |
| [`simulacion_recoleccion_torre_v19.png`](v22/simulacion_recoleccion_torre_v19.png) | 2D single-ball simulation: floor, lower shelf (rows 2 and 3) and upper shelf (rows 2 and 3) all reach the top of the tower in 1.0–1.4 s |
| [`simulacion_cono_v15.png`](v22/simulacion_cono_v15.png) | Cone handling with the UR band at z = 468 (knocks the cone over); at z = 455 the cone stays leaning |

## Test plan

| Test | Measure | Pass criterion (from CAD / simulation) |
| --- | --- | --- |
| Floor pick-up | Balls per 10 attempts, time to tower top | ≥ 9/10, ≤ 1.4 s |
| Lower / upper shelf | Balls per 10 attempts per row | ≥ 8/10 |
| Cone | Knock-over with band at z 468 | Cone falls in 0.6 s |
| Jam recovery | Reverse sequence clears a stuck ball | Clears in < 1 s |

Record each test with date, robot revision, configuration, number of trials, and raw data before changing the design.
