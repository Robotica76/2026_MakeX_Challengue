# Manual Strategy

The manual stage (100 s) after the "bonus" automatic stage. The driver uses `robot_2026.py`
("≡" ball mode: L1 intake, R1 shoot, Up/Down head); `simulation/control/match_2026.py` plays the
same plan as moves so the simulator can time and score it.

| Step | Simulated time | What the driver does | Why |
| --- | --- | --- | --- |
| 1 | 30-39 s | Sweep resource area 1 facing -x at y 590 (own 10 + 12 bonus balls, 18 fit), head down | bonus balls score 20 |
| 2 | 41-62 s | Shoot from (1600, 1000), launcher toward the blue fortress, aimed 150 mm short of its centre | path crosses the centre over the low strategy area |
| 3 | 64-81 s | Rest of area 1, then resource area 2 (y 2465) | own balls are uncontested |
| 4 | 83-100 s | Shoot from (1600, 2300) | path over the upper strategy area |
| 5 | 102-126 s | Central table upper level (head 255 mm, capture), shoot | contested balls last |

Result (simulation): 30 shots, 18 in the blue fortress, 300 points with the X12 bonus.

## Two-robot plan with cones (storm_breaker_2026, our half only)

`simulation/control/ai_driver.py` plays the gamepad of `storm_breaker_2026.py` ("≡" intake front:
Up/Down head; "+" gripper front: Up/Down carriage, Right/Left jaw). Headless:
`simulation/analysis/simulate_driver.py [delay_frames]`.

| Step | Simulated time | What the driver does | Why |
| --- | --- | --- | --- |
| 1 | 30-54 s | Head up to 250 (over the strategy-area top, R26); cone a (left at (2029, 535) by the automatic lane a pull, `PULL_A_DY` 200) taken from the north at heading 35, lifted to 425, hung on red cone post 2 from heading 250 | the sweep would push it against the shelf legs, where the gripper cannot take it; heading 35 touches none of the released balls |
| 2 | 55-90 s | Sweep resource area 1 twice, shoot from (1600, 900) after each | bonus balls score 20 |
| 3 | 90-108 s | Cone b (pushed to (2160, 1080) by the sweep) taken at heading 90 and hung on post 2 | 20 points |
| 4 | 108-130 s | Back into Red Start 1 (modification stage) | flag mast |
| 5 | 190-221 s | N4 hangs the flag, last sweep and shot | 50 points |

Hanging needs the **430 mm elevator** (v22: 358 mm; the cone bottom must clear the 405 mm post:
`simulation/analysis/cone_post_reach.py`). The program tracks the carriage height in "+" mode, so
the flag routine starts from where the driver left it.

| Driver | Delay frames (1/60 s) 0 / 2 / 4 / 6 / 8 / 10 | Mean |
| --- | --- | --- |
| previous plan (no cones, commit cfb339f) | 300 / 340 / 350 / 380 / 330 / 330 | 338 |
| with the two cones | 400 / 400 / 410 / 360 / 390 / 370 | 388 |

Both cones hang in every run; no collisions, no penalties, flag hung. The ball count varies run to
run (balls bouncing in the fortress), not the cones.

## Practice evaluation

| Configuration / driver | Setup / procedure | Measured outcome / units | Driver feedback | Failure / corrective action | Retest / evidence |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD |

Open points: shooter calibration (power vs distance) on the robot, balls bouncing out of the
fortress, pins / X mark / letter cubes for the extra points.
