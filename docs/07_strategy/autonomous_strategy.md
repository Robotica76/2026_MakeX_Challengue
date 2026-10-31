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

## Plan (team): central balls, then props from the central strip to our side

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
| Central balls + X12 to the exchange area | v22 CAD, simulator 2026-10-31 | Simulation, deterministic: 14 balls, X12 valid, stationary at 29.0 s | Timeline above; `simulation/field2d/test_match.py` | Edge ball pushed on pass B; 1 s timing margin | Team plan |
| Central balls only (`LOWER_PASS`) | Same | Simulation: 18 balls by 23.8 s | — | No bonus cube | Fallback |

Coordinate [autonomous controls](../04_controls/autonomous/README.md), [mode contracts](../04_controls/stateflow/README.md), and [competition tests](../06_verification/competition_tests/README.md). Record strategy changes and actual outcomes in [notebook results](../08_engineering_notebook/test_results/README.md).
