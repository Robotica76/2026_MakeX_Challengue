# Lessons Learned

Evidence-backed lessons and the follow-up they caused. Lessons so far come from the CAD and
simulation work; each one links the record where it was found.

| ID | Lesson | Evidence | Follow-up |
| --- | --- | --- | --- |
| LL-001 | Interference checks must list *every* clash, not a filtered view: a filter hid the R2 core crossing the tower plates from v19 to v20 | [DL-SYS-001](../design_log/DL-SYS-001_design_decisions.md) (v20 fix) | Clash reports reviewed unfiltered before each CAD release |
| LL-002 | Check motor speeds against the rules' motor catalogue early: the feed roller at the real DC-25 speed (200 RPM) did not work in simulation | DEC-M06 | Every roller simulation uses the real motor speed |
| LL-003 | Calibration matters more than controller gains: odometry "arrives" while the robot is elsewhere (strafe slip, gyro scale) | [chassis Monte Carlo](../../../simulation/analysis/reports/chassis_montecarlo/README.md) | Calibration procedure before tuning ([tools/calibration](../../../tools/calibration/README.md)) |
| LL-004 | Start-heading error dominates autonomous accuracy (1° → 30 mm after 1.7 m) | [montecarlo_strategy.md](../../07_strategy/montecarlo_strategy.md) | Start-alignment jig |
| LL-005 | Results from ideal robots overstate match scores; apply the ±5 mm prop jitter and sampled robots before ranking plans | [four_robots report](../../../simulation/analysis/reports/four_robots/REPORTE.md) (2026-11-06 update) | Rank strategies with `mc_four.py` |
| LL-006 | Mass margin shrinks with every "small" addition (battery real mass, screws, flag mast): 9.48 → 9.92 kg | DEC-M09, DEC-M10, DEC-M12 | Weigh parts as soon as they exist |

| Lesson ID | Source event / evidence | Affected requirement / interface | Owner | Implementation evidence | Status |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD |
