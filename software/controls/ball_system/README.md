# Ball system controls

Intake, tower and feed roller are open-loop DC motors driven from the power expansion board.

| Function | Port (assumed) | Code |
| --- | --- | --- |
| Intake throat rollers | DC1 | `L1` in / `L2` out in the manual loops |
| Intake head lift (UR arm, ~53 mm/s) | DC2 | `head_to_N(mm)`, `head_estimate()` (time-based height estimate) in [`storm_breaker_2026.py`](../../robot/main/storm_breaker_2026.py); `head_to()` in `auto_pull_central.py` |
| Intake head roller | DC7 | `L1`/`L2`; **pull mode** (N2): only DC7 turns to drag props |
| Tower belts | DC4 | with the intake (`L1`) and when shooting |
| Feed roller | DC5 | only while shooting (R1 / R2 held): the gate of DEC-M05 |

Interlock in code: the feed roller runs 0.5 s after the shooter starts (`aim_and_shoot_N_N_N_N`).
Not yet: basket-full detection (S2 tower sensor not read), current limits, jam detection.
Hardware: [ball_intake](../../../mechanical/ball_intake/README.md), [feeder](../../../mechanical/feeder/README.md),
[ball_storage](../../../mechanical/ball_storage/README.md).
