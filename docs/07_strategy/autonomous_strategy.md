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

## Candidate plans (team proposal: central balls first, letter cubes with the time left)

| Candidate | Order | Simulated result | Robot stationary | Value / risk |
| --- | --- | --- | --- | --- |
| **A** (default, `LOWER_PASS = False`) | Head up while driving → 2 passes on the central upper level → cube route | 14 balls by 15.7 s; one cube cycle (take 21.9 s, release 27.3 s, gripper not simulated) | 27.3 s | Balls + possible 30-point cube; cube handling unproven |
| **B** (`LOWER_PASS = True`) | As A + a third pass at the lower level | 18 balls (robot full) by 23.8 s; no time for cubes | 25.8 s | Maximum denial and ammunition; no cube |

Both run in [`auto_central_then_cubes.py`](../../software/autonomous/task_execution/auto_central_then_cubes.py)
from Red Start 1 (one flag selects the variant).

Rough value of the four extra balls of B: each is up to 10–20 points for us when shot in the
manual stage, plus up to 10–20 points the opponent cannot score with it, so 40–160 points,
against 30 points (+ progress toward the 50-point MAKE bonus) for one letter cube in A.
**Recommendation from the simulation: B**, unless the cube cycle becomes reliable. The
opponent also reaches the table from the blue side, so the earlier the passes, the more
balls are left; our first balls come in at 6.7 s.

## Timeline of plan A (simulation)

| Time | Event |
| --- | --- |
| 0.0–0.5 s | Gyro calibration (robot still); intake head starts rising (4.8 s to ~254 mm) |
| 0.5–5.6 s | Diagonal drive at 150 RPM to the table front (1720, 1427 mm), head rising on the way |
| 5.6–9.9 s | Pass A on the upper level (intake + tower on): first balls at 6.7 s, 10 balls |
| 9.9–15.7 s | Strafe 19 cm, pass B: 4 more balls by 13.5 s (one edge ball is pushed, see notes) |
| 15.7–21.9 s | Head down, drive to the fortress, turn the gripper toward it, carriage up, jaw (placeholder) |
| 21.9–27.3 s | Turn, carriage down, drive to the E window, release (placeholder) |
| 27.3 s | Everything stopped (R19 satisfied) |

## Open questions before the cube phase is real

1. **Reaching the cubes in the fortress.** The cubes sit about 95 mm inside the fortress edge on the
   171 mm level. The v22 gripper reaches 22 mm beyond the robot footprint, and the elevator
   tower (right side, up to 642 mm) would touch the fortress. Pushing the own fortress is allowed
   (p.21) but it must not tilt (R02).
2. **Placing a cube without entering the channel (R26).** The gripper holds the cube centre 22 mm
   behind the jaw tips, so the cube centre cannot pass the channel entrance while the jaws stay
   outside. A cube left with its centre outside tips onto the map and does not score. Options: release
   with forward speed so the cube slides in, or a gripper that holds the cube by its rear.
3. **Bonus Battle instead of letter cubes.** A valid X12 bonus cube adds 12 balls that score 20 each
   (p.30). It needs the AI camera (`ELV_AI_camera_2_0` is in the CAD) to read the prop-card layout.
   Worth comparing with the letter cube for the time after phase 1, or giving it to the alliance partner.
4. **Alliance partner.** Two robots per alliance: splitting central balls (ours) and cubes / bonus cubes
   (partner) avoids both doing a half job.

## Evaluation

| Candidate | Setup revision | Repetitions / success / uncertainty | Timing evidence | Failure / corrective action | Decision |
| --- | --- | --- | --- | --- | --- |
| A | v22 CAD, simulator 2026-10-31 | Simulation, deterministic: 14 balls, cube route fits | Timeline above; `simulation/field2d/test_match.py` | Edge ball pushed on pass B (13–14 of 15) | Pending team review |
| B | Same | Simulation: 18 balls | Phase 1 ends 23.8 s | — | Recommended by simulation |

Coordinate [autonomous controls](../04_controls/autonomous/README.md), [mode contracts](../04_controls/stateflow/README.md), and [competition tests](../06_verification/competition_tests/README.md). Record strategy changes and actual outcomes in [notebook results](../08_engineering_notebook/test_results/README.md).
