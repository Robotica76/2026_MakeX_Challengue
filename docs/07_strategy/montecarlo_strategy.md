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

## Four robots: 2 vs 2 strategy game and reinforcement learning (2026-11-05)

Rules that bound the search: physical blocking is forbidden (R27: no obstructing or restricting the
opponents' movement or their access to field elements, -20 then -120; R06 keeps every robot in its
camp), so it is not modelled. Legal levers: taking contested central resources first (R23 only
forbids moving elements into the opponent's field), moving our own fortress (p.25, R02: no tilt,
R25: never remove scored balls; a referee could still read a fortress pushed against shots as R27,
check before using it), and the last hit at the X mark (R24: no contact).

**Fixed-aim cliff** (detailed simulator, our shots from (1600, 900) at fixed coordinates, 13 shots):
blue fortress at 0 mm 10 in, 50-100 mm 9-11, **150 mm north or east 0**, 150 mm south 7. Two-robot
check: the blue twin pushing its fortress 190 mm cut our precision from 240 to 140. Our own fortress
pushed north does not help (the blue shots come from the north-east) and takes our K/E out of reach;
it would have to go south (the partner, from the north side) or west (147 mm of room only).

`simulation/analysis/strategy_game.py`: the match at mission level for four robots (red lower =
ours, red upper = partner, blue lower, blue upper), calibrated from the detailed runs, with the
contested bonus cubes (prop card at random; > 2 cubes on a side invalidate all), central table
balls, cones, X mark race and movable fortresses; `rl_strategy.py`: self-play REINFORCE over each
robot's automatic order, manual plan, final plan and X time (~28 million alliance plans), 192 000
matches, then 2000-match Monte Carlo per opponent style and an exploitability check (an opponent
trained against the plan). Figures: `simulation/analysis/reports/rl_strategy*/`.

| Plan | Ours (lower) | Partner (upper) | vs styles (fixed / adaptive aim) | Exploitable by |
| --- | --- | --- | --- | --- |
| current | BD / SSC / LFX | B / SSC / LFX | -363 (evader) ... +444 | +521 |
| learned, our aim fixed | B + push fortress / SSC / LFX, X 277.8 s | B + table / SSC / LFX | +20 ... +633 (fixed); -349 vs evader (adaptive) | -42 |
| learned, our aim adaptive | B + table / SSC / LFX | B + table / SSC / FL | +167 ... +609, wins 85-100 % | +20 |

Codes: B bonus cube to the exchange area, D deny (second cube + cone), T central table balls,
E push our fortress, S sweep + shoot, C hang a cone, L letters K, E, F flag, X keep 2 balls for
the X mark.

Findings: (1) **aim at the fortress where it is** (driver offset or vision): with fixed-coordinate
aim any alliance that moves its fortress 150 mm wins by ~350 points; (2) in the automatic stage the
bonus cube then the central table balls (ORDER 13) beats bonus then deny (also the best whole-match
order of the detailed route Monte Carlo, 443); (3) both robots of the alliance should take a bonus
cube (one per half: at most two on our side); (4) last shots at the X at ~277.8 s.

## Extended Monte Carlo with sampled robots (2026-11-06)

`simulation/analysis/mc_four.py`: 80 whole 4-robot matches, sampled robots, props within +-5 mm. The
figures above from whole matches (388, 410, 415 points, the bandit) came from ideal robots, with
delays 0 and 2 being the same run; the +-5 mm prop jitter was never applied before this date (it ran
before `run()` rebuilt the props). Margin red - blue (95 % CI): 12 vs 12 +31 +- 75; 13 vs 12 +53 +- 65;
13 with X 277.8 vs 12 +64 +- 71; paired 13/X 277.8 over 12: +33 +- 46 (blue 12), +42 +- 37 (blue 13). Our
flag routine hangs in only 55 of 80 matches (odometry); details in
`simulation/analysis/reports/four_robots/REPORTE.md`.
