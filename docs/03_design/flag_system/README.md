# Flag System Design Study

Task: **Team Flag Hanging**, final stage, 50 points (rules p.47). Flag ≥ 400 × 300 mm, optional
rigid pole < 10 × 10 mm, suspension ≤ 400 × 10 × 10 mm (T17); the flag mass is excluded from the
10 kg limit (T02), the mast is not. Field bar: horizontal aluminium bar 160 mm long at
≈ 950–965 mm.

## Selected concept

Removable mast installed in the **Modification Stage** ([DEC-M12](../../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md)): CF tube 8×6 in a
receptor on the gripper mounting block, raised by the gripper elevator (358 mm stroke; top
704 → 1062 mm); C-shaped head closed by two rubber bands holds the flag pole. Hang: raise, put
the field bar in the flag loop, lower, strafe `−x`. Hardware and drawing:
[mechanical/flag_system](../../../mechanical/flag_system/README.md).

| Rule | Design response | Status |
| --- | --- | --- |
| T01: ≤ 700 mm before modification | Mast not installed at the start | Meets in CAD (642 mm) |
| T08 (5): no hook-shaped parts | Bands close the C | Confirm with the referee |
| T02: ≤ 10 kg | Mast 31.6 g → 9.92 kg | Margin 80 g |

## Open issues

- [KI-008](../../05_integration/known_issues.md): with the right-side v22 mast, the red cone post keeps the
  rod ≥ 150 mm short of flagpole 2 in the simulated field; the simulator and `hang_flag()` use a proposed
  left-front rod instead. **Decide before building the mast.**
- Bar direction relative to the pin table is not dimensioned in the rules.
- Simulated success 55 / 80 matches (odometry error) — [four robots report](../../../simulation/analysis/reports/four_robots/REPORTE.md).
