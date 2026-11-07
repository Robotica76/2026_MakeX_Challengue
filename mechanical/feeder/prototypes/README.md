# Feeder Prototypes

**Status (v22): no physical prototype has been built.** The figures below are CAD-based simulations (2D single-ball contact models or rigid-body estimates); they define what to measure, not results.

## Simulation evidence (v22 design inputs)

| Figure | What it shows |
| --- | --- |
| [`simulacion_recoleccion_torre_v19.png`](v22/simulacion_recoleccion_torre_v19.png) | Ball path from the intake up the tilted tower to the elbow (z = 430) |
| [`simulacion_codo_y_bolsillo_v18.png`](v22/simulacion_codo_y_bolsillo_v18.png) | Left panel: elbow roller + cover takes the ball over the top into the basket (works from 0.42 to 1.26 m/s). Right panel is the v18 pocket, no longer used |

## Test plan

| Test | Measure | Pass criterion (from CAD / simulation) |
| --- | --- | --- |
| Lift | Balls lifted per minute, 3 rows | No stalls with 15 stored |
| Elbow | Hand-off to basket at DC-25 200 RPM (0.42 m/s) | 10/10 into the basket |
| Storage | Balls held with tower stopped | ≈ 15 |

Record each test with date, robot revision, configuration, number of trials, and raw data before changing the design.
