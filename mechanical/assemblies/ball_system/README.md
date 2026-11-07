# Ball system assembly

Integration of the subsystems the ball passes through (v22). Each subsystem keeps its own CAD;
this page describes how they connect.

```text
ball_intake (4) --IF-B1--> feeder / tower (3) --elbow, IF-B2--> ball_storage / basket (8) --feed roller, IF-B3--> shooter (7)
```

| Interface | Geometry (robot frame, mm) | Check |
| --- | --- | --- |
| IF-B1 intake → tower | Ramp to the tower lower window, 3 lanes at x −75.7 / 0 / +75.7 | 2D simulation: floor and shelves reach the tower top in 1.0–1.4 s |
| IF-B2 tower → basket | Elbow at the tower top (z 430), exit chute into the basket | 2D simulation, 0.42–1.26 m/s |
| IF-B3 basket → launcher | Basket floor sloped 10 % to the launcher mouth (x −163, y 4, z 389); feed roller protrudes 12 mm | 2D simulation: holds when stopped, fires at 0.94 m/s |

Capacity: ~15 balls in the tower + 6–8 in the basket. Decisions DEC-M02…M08
([DL-SYS-001](../../../docs/08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md)); concept page
[ball system design](../../../docs/03_design/ball_system/README.md). Whole-robot CAD: [full_robot](../full_robot/README.md).
