# Monte Carlo Strategy Search (automatic stage)

Method: [`montecarlo_strategy.py`](../../simulation/analysis/montecarlo_strategy.py) runs the
competition program [`storm_breaker_2026.py`](../../software/robot/main/storm_breaker_2026.py) in
the 2D simulator on sampled robots (scenario `montecarlo_config_competition.json`: the calibrated
robot, start-alignment jig 2 mm / 0.3 deg) with the props moved within the rules' +-5 mm. Same seeds
for every candidate. Ranking: resources first (X12 valid = 12 bonus balls; X9 kept on our side =
9 bonus balls denied to the opponent; cones on our side), then the points they allow (20 per bonus
ball), then the time the X12 is secured. Our robot stays in the lower half (two robots per alliance).

## Result (2026-10-31)

| Candidate | P(X12 valid) | P(X9 ours) | Resources | Problems / run | X12 placed |
| --- | --- | --- | --- | --- | --- |
| **DENY_X9, v 700 mm/s, a 1200, d 1400, approach 500, pull 400, grab centred** | **0.96** | **1.00** | **21.6** | 0.08 | 15.4 s |
| same, grab 7 mm short (cone clearance) | 0.92 | 1.00 | 20.5 | 0.12 | 15.4 s |
| same without DENY_X9 | 0.96 | 0 | 12.3 | 0.04 | 15.4 s |
| faster profile (900 / 1600 / 1800) | 0.71 | 1.00 | 15.3 | 0.29 | 15.2 s |

(24 robots per candidate, validation seeds; the first search used 16 robots on 12 candidates.)

What the search found and fixed:
- **Start heading error dominates.** 1 deg at the start becomes 30 mm at the gripper after 1.7 m:
  without a jig P(X12) was 0.2-0.8. Place the robot with a start-alignment jig.
- **Strafing slips** (~7 % uncalibrated): long moves now face the way they go and turn at the end
  (`travel_N_N_N_N_N`); calibrate `STRAFE_SLIP` on the field.
- **0.5-2 mm clearances to the resource-area legs** in the first routes: lane a moved to y 590 and
  the X12 drop to y 360 (cube still 18 mm inside exchange area 1).
- A faster profile saves 0.2 s but loses accuracy: the head lift (53 mm/s) sets the pace, not the chassis.

Lane a cone: the last lane a floor pull also moves 200 mm toward the field centre (`PULL_A_DY`),
so the cone ends near (2029, 535), clear of the shelf legs, where the gripper takes it in the
manual stage to hang it (manual_strategy.md).

Alliance note: with DENY_X9 our side holds two bonus cubes (X12 in the area, X9 on the floor), the
rules' maximum (p.30 d): the partner must not bring a third one to our side.

Remaining failures (4 %): a gripper miss or a leg touch when errors add up. On the robot, the AI
camera can locate the X12 before the grab (Bonus Battle expects vision, p.28).

## Route search: every order of the automatic missions (2026-11-05)

`simulation/analysis/montecarlo_routes.py`: the program runs the missions in the order of the
digits of `ORDER` (1 X12 into exchange area 1, 2 X9 + cone a to our side, 3 / 4 central table
balls lower / upper level, taken in and shot from (1600, 900); a mission that does not fit before
29 s is left out). Stage 1: the 65 orders (every subset in every order) x 6 sampled robots, automatic
stage only. Stage 2: the best 6 as whole matches with the scripted driver (delays 0, 4, 8 frames).
Figures: `simulation/analysis/reports/routes_montecarlo/`.

| ORDER | Route | Stage 1 value (min) | Match mean (min) | Notes |
| --- | --- | --- | --- | --- |
| 13 | X12, lower table balls | 180 (130) | **443** (420) | precision 323, but no cone hung and a 20 point penalty in every match; 4 s in the partner half |
| 124 / 123 / 1234 | X12, deny (3/4 do not fit in time) | 182 (175) | 423-427 (420) | same automatic stage as 12 |
| 12 | X12, deny (current) | 182 (175) | 410 (380) | |
| 1 | X12 only | 130 | - | |
| 34 | both table levels, no cube | 110 | - | 18 balls taken, 11 scored in the stage, no bonus |

Orders without the X12 first lose its 12 bonus balls (every 1-free route ranks below every route
that starts with 1). The ball-first routes (3/4 before 1) run out of time for the X12. The
differences between 12, 123, 124 (the same automatic stage) are the run-to-run noise of the
match (~±15).

**Two identical robots** (`simulation/analysis/two_robots.py`): our robot and its blue twin
(same program and driver, started from Blue Start 2: the field turned 180 deg) on one field,
sharing balls, props, X mark and fortresses.

| Red ORDER | Blue ORDER | Red | Blue | Interaction |
| --- | --- | --- | --- | --- |
| 12 | 12 | 420 | 310 | none; the twin's X12 spot holds the X6 (6 bonus balls) |
| 12 | 13 | 420 | 290 | none |
| 34 | 34 | 270 | 350 | the robots touch twice over the central table (4.8 s, 12.5 s); the twin takes more balls |
