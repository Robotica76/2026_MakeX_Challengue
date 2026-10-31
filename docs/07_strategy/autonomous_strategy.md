# Autonomous Strategy

Automatic stage: 30 s, program only, Bluetooth controller outside the arena (rules guide V1.1
p.52, R19). Missions allowed: Letter Cube Transfer, Pin Transfer, Cone Transfer, X Clash,
Precision Throwing and Bonus Battle (p.27). Values below are **simulation results** with
the v22 model; nothing has been run on the robot.

## Rules that shape the plan

| Rule | Source | Effect on the automatic plan |
| --- | --- | --- |
| Collecting central balls is part of the automatic stage | p.32 (Precision Throwing) | Phase 1 is legal; no rule limits how many balls a robot holds (searched the guide) |
| Robot must be stationary when the stage ends | R19, p.71 | −20 points; the routine stops everything before 29 s |
| Robot projection inside its own area (red: x ≤ 2220 mm) | R06, p.66–67, Fig 6.2-1 | Team decision: the intake head overhang into the central strip is allowed; the simulator checks the body only and the 3 s grace |
| No robot part inside a strategy area channel | R26, p.73 | Letter cubes must end with their projection in the channel without the gripper entering it (open design question, below) |
| Letter cube scores if partly in the channel and not touching the map | p.38 | 30 points; MAKE order on one side +50 |
| Bonus cube in own exchange area at the end of the stage | p.29–30 | X3–X12 extra balls placed in the own resource area, each scoring 20 instead of 10 |
| X mark must not be touched | R24, p.72–73 | The routine stays below the table top (654 mm) and away from the X |

## Plan (team, current): pull the central elements to our side

Team decision (2026-10-31): in the automatic stage, do not store or shoot; drag as many central
elements as possible onto our side, where the opponent cannot reach them (R06), and use or place
them in the manual stage: (1) upper-level balls, (2) lower-level balls, (3) cones and bonus cubes
from the strategy areas. Moving them to our own side is allowed (R23 only forbids the opponent's
side or out of the arena).

Pull mode: the intake head roller (DC7) runs with the throat (DC1) off; what the head touches
slides toward the robot and drops in front of the body. Each pass enters the table with the head
**above** the balls (nothing is pushed to the opponent), lowers it onto the level and backs out
pulling.

Routine: [`auto_pull_central.py`](../../software/autonomous/task_execution/auto_pull_central.py).
Route chosen by [`optimize_auto_route.py`](../../simulation/analysis/optimize_auto_route.py)
(task orders, speeds, lane depth, arrival tolerance and head heights; the score counts elements on
our side and penalises collisions, R06, R19 and elements fed to the opponent). Simulated result:

| Time | Event |
| --- | --- |
| 0.0–2.7 s | Gyro calibration; one diagonal to (1240, 950): clear of the cone post and the resource-area legs, the body passes the fortress corner; the head rises |
| 2.7–10.2 s | Pass upper b (lane y 1600): in to x 2100 at 290 mm, head to 250 mm, back out pulling |
| 10.2–15.5 s | Pass upper a (y 1437); the head starts down once it is clear of the table |
| 15.5–21.8 s | Pass lower a (head 85 → 50 mm) |
| 21.8–27.0 s | Pass lower b; everything stopped at 27.0 s (R19) |

Result: the 30 central balls are off the table; **22 completely on our side**, 8 on the floor
against the table base (x ≈ 2200, 15 mm over the line), none on the opponent side. No contact
with any field structure, the body never crosses x 2220 (R06), stationary at 30 s.

**Props: first with the head high, then a floor pass with the head low.** A cone or bonus cube
pulled off the strategy area falls when its centre leaves the top, at the centre line (x ≈ 2219,
half on the opponent side). A floor pass (head at 50 mm, stopping at x 1925 so the head stays clear
of the strategy-area dividers) pulls it from the line onto our floor. The head lift is slow
(53 mm/s), so the props passes go first, while the head is high on the way, and the floor passes
go once it is low (after the lower-level balls). Each lane takes the props under the head width:
lane b (y 951) the X12 and a cone, lane a (y 570) the X9 and a cone.

Strategies in the routine (`STRATEGY`), simulated, all without collisions, R06 or R19 penalties:

| `STRATEGY` | Order | On our side | Done |
| --- | --- | --- | --- |
| `balls` | upper b, upper a, lower a, lower b | 21–22 balls | 27.0 s |
| `mixed` (default) | props b, upper b, lower b, floor b | 16–17 balls, 1 cone, X12 | 25.1 s |
| `props` | props b, props a, floor a, floor b, lower b | 11 balls, 2 cones, X9, X12 | 28.0 s |

Two bonus cubes on our side is the limit (p.30 d); outside the exchange area they only deny the
opponent. The upper strategy area (X3, X6, two cones) does not fit in this stage.

Collision check of the previous routines (`CollisionMonitor`, robot height bands from the CAD):
`auto_central_then_cubes.py` touches the red fortress on its diagonal (30 mm, a push), a table leg
with the head (6 mm) and enters `strategy_lower` with the body during the X12 grab;
`test_ball_collection.py` pushes the fortress (7 mm). The new route avoids all of them.

## Previous plan: central balls, then props from the central strip to our side

Team decisions (2026-10-31): take the central balls first (denial, no shooting in this stage);
then bring props from the strategy areas, right next to the table, to our side, where the
opponent cannot reach them. Placing cones and letter cubes waits for the manual stage.
Exception: a **bonus cube only counts if it is in our exchange area when the automatic stage
ends** (p.30) and the exchange happens once, so the X12 goes straight into exchange area 1.
At most two bonus cubes may be on our side, or none of ours count (rule d).

Routine: [`auto_central_then_cubes.py`](../../software/autonomous/task_execution/auto_central_then_cubes.py)
(Red Start 1, default prop card). Simulated result:

| Time | Event |
| --- | --- |
| 0.0–0.5 s | Gyro calibration; the intake head starts rising (4.8 s to ~254 mm) |
| 0.5–5.6 s | Diagonal drive at 150 RPM to the table front, head rising on the way |
| 5.6–9.9 s | Pass A on the upper level (intake + tower on): first balls at 6.7 s, 10 balls |
| 9.9–15.7 s | Strafe 19 cm, pass B: 14 balls by 13.5 s (one edge ball is pushed) |
| 15.7–17.7 s | Turn the gripper (right side) toward the strategy area; carriage to 268 mm, jaw pre-closed |
| 17.7–24.0 s | Approach the X12, reach in (body 2.26 s over the line, R06 allows 3 s), close, back out |
| 24.0–29.0 s | Turn, drive over red exchange area 1, open the jaw: **X12 valid, +12 bonus balls** |
| 29.0 s | Everything stopped (R19 satisfied); a safety stop at 29.5 s halts any overrun |

The cone step (drop on our side) is in the routine but does not fit in 30 s with this order.
`LOWER_PASS = True` takes 18 balls by 23.8 s instead and leaves no time for the X12.

Value of the plan: 14 balls held for the manual stage and denied to the opponent, plus 12 bonus
balls in our resource area, each scoring 20 instead of 10 (p.36): up to 240 points from the bonus
alone. The opponent also reaches the table from the blue side; our first balls come in at 6.7 s.

## Open questions

1. **Finding the X12 on the robot.** The prop card changes the layout every match (p.51); the
   routine uses the default card. The AI camera (`ELV_AI_camera_2_0` in the CAD) must read the
   cube labels (Bonus Battle, p.28) and give the routine the X12 position.
2. **Timing margin.** The plan ends at 29.0 s in simulation. On the robot, measure each step and
   keep at least 1 s of margin, or drop pass B (10 balls) to gain about 6 s.
3. **Gripper on real props.** Jaw closure, carriage height (268 mm, above the cone base) and the
   grab tolerance are estimates from the CAD; test on a strategy-area mock-up.
4. **Letter cubes in the manual stage.** Reaching cubes inside the fortress and placing them without
   entering the channel (R26) are still open design questions for the gripper.
5. **Alliance partner.** It could take cones / the second bonus cube while we take the balls.

## Evaluation

| Candidate | Setup revision | Repetitions / success / uncertainty | Timing evidence | Failure / corrective action | Decision |
| --- | --- | --- | --- | --- | --- |
| Pull the central elements to our side (`balls` / `mixed` / `props`) | v22 CAD, simulator 2026-10-31 | Simulation: table above, 0 collisions, stationary | `test_match.py` | Real pull behaviour (balls and props under the head roller) untested; head lift speed limits the props | Team plan |
| Central balls + X12 to the exchange area | v22 CAD, simulator 2026-10-31 | Simulation, deterministic: 14 balls, X12 valid, stationary at 29.0 s | `simulation/field2d/test_match.py` | Edge ball pushed on pass B; 1 s timing margin; touches the fortress and a table leg | Previous plan |
| Central balls only (`LOWER_PASS`) | Same | Simulation: 18 balls by 23.8 s | — | No bonus cube | Fallback |

Coordinate [autonomous controls](../04_controls/autonomous/README.md), [mode contracts](../04_controls/stateflow/README.md), and [competition tests](../06_verification/competition_tests/README.md). Record strategy changes and actual outcomes in [notebook results](../08_engineering_notebook/test_results/README.md).
