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

Alliance note: with DENY_X9 our side holds two bonus cubes (X12 in the area, X9 on the floor), the
rules' maximum (p.30 d): the partner must not bring a third one to our side.

Remaining failures (4 %): a gripper miss or a leg touch when errors add up. On the robot, the AI
camera can locate the X12 before the grab (Bonus Battle expects vision, p.28).
