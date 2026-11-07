# Autonomous Control Architecture

Automatic stage: 30 s, program only (rules p.52, R19 stationary at the end). Routines exist in
code and run in the simulator; none has run on the robot.

| Routine | Code | Preconditions | Inputs / frames | Outputs | Completion / cancellation | Failure response |
| --- | --- | --- | --- | --- | --- | --- |
| Competition automatic (missions by `ORDER`) | [`storm_breaker_2026.py`](../../../software/robot/main/storm_breaker_2026.py) `automatic()`, `mission_N()` | Robot in Red Start 1, start jig, `calibrate_N_N_N` (gyro bias) | Field mm / deg, odometry (encoders + gyro) | Wheels, DC2 head, DC3 carriage, DC6 jaw, DC1/DC4/DC5/DC7, BL1 | Each mission skipped if it cannot end before `END_BY`; everything stops before 30 s | Timeouts per move (`GO_TIMEOUT`) |
| Pull central resources (`bonus`, `balls`, `props`) | [`auto_pull_central.py`](../../../software/autonomous/task_execution/auto_pull_central.py) `run(strategy)` | Same | Same (chassis.py `odo`) | Wheels, DC2, DC7, DC1, DC6 | `END_BY` 29.0 s, `HARD_STOP` | Stop all |
| Earlier plan (central balls, then cubes) | [`auto_central_then_cubes.py`](../../../software/autonomous/task_execution/auto_central_then_cubes.py) | Same | Same | Same | Same | Same |

## Verification questions

| Question | Evidence so far | Test |
| --- | --- | --- |
| Repeatable initial state | Start heading error dominates; jig 2 mm / 0.3° assumed | Jig + 10 starts, measure X12 placement |
| Uncertain observations | AI camera to locate the X12 before the grab (not coded) | Vision bench test |
| Command ownership at the end of the stage | Program returns to `manual_loop()` | Full-match rehearsal |

See [autonomous strategy](../../07_strategy/autonomous_strategy.md) and [stateflow](../stateflow/README.md).
