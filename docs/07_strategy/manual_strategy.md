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
Up/Down head; "+" gripper front: Up/Down carriage, Right/Left jaw; N2 in both: pull mode, only the
head roller turns). Headless:
`simulation/analysis/simulate_driver.py [delay_frames]`.

| Step | Simulated time | What the driver does | Why |
| --- | --- | --- | --- |
| 1 | 30-54 s | Head up to 250 (over the strategy-area top, R26); cone a (left at (2029, 535) by the automatic lane a pull, `PULL_A_DY` 200) taken from the north at heading 35, lifted to 425, hung on red cone post 2 from heading 250 | the sweep would push it against the shelf legs, where the gripper cannot take it; heading 35 touches none of the released balls |
| 2 | 55-90 s | Sweep resource area 1 twice, shoot from (1600, 900) after each | bonus balls score 20 |
| 3 | 90-108 s | Cone b (pushed to (2160, 1080) by the sweep) taken at heading 90 and hung on post 2 | 20 points |
| 4 | 108-130 s | Back into Red Start 1 (modification stage) | flag mast |
| 5 | 190-200 s | Head at 150 mm (over the 171 mm fortress cube level), facing north under the fortress: N2 pulls K and E off onto the floor | the gripper cannot reach into the fortress |
| 6 | 200-215 s | Head at 40 mm, N2: drags E to (1500, 760), then K to (1100, 760), clear of the fortress, the cone post and each other | room to take each one with the gripper from the west |
| 7 | 215-257 s | Each cube taken 40 mm outward between the jaws (it sticks out past them), carriage 10 mm (bottom over the 25 mm rail), slid into its window (K channel 3, E channel 4) until its centre is 8+ mm over the rail with the body 3+ mm outside the strategy area (R26), released | 30 points each |
| 8 | 257-270 s | Back to Red Start 1 (pose to 6 mm), N4 hangs the flag | 50 points |

M and A sit on the east and west sides of the fortress at the centre line: taking them means
entering the partner's half, so in the two-robot plan they are the partner's (MAKE: +50 with K, E).

**Mobile fortress** (`simulation/field2d/fortress.py`, rules p.25: on casters, free to move in its
alliance area; R02: it must not tilt): the robot pushes it out along the smallest overlap with its
structure boxes (posts, cube level, ball level, walls); it stays in the alliance area and off the
other structures, and carries its letter cubes and balls. The 3D viewer moves it. Findings:

- The flag routine's end pose (322, 1204), rod over flagpole 2, puts the body 230 mm into where the
  fortress stands: the flag cannot be hung without pushing it ~290 mm north (into the partner
  half, with their letter cubes). The routine now turns first and pushes it at 150 mm/s from 7 mm
  before contact (was a 1.2 m/s shove); it runs last, after our letter cubes. Coordinate with the
  partner, or change the mast so the robot hangs the flag from outside the fortress footprint.
- Earlier routes that brushed the fortress (cone a carry at y 1150) shoved it up to 200 mm; the
  routes now pass between the ball rows and the fortress facing south (y 945).
- The program stops the other mode's motors in each mode (a head key held across "≡" → "+" kept
  DC2 running to the top).

Hanging needs the **430 mm elevator** (v22: 358 mm; the cone bottom must clear the 405 mm post:
`simulation/analysis/cone_post_reach.py`). The program tracks the carriage height in "+" mode, so
the flag routine starts from where the driver left it.

| Driver | Delay frames (1/60 s) 0 / 2 / 4 / 6 / 8 / 10 | Mean |
| --- | --- | --- |
| previous plan (no cones, commit cfb339f) | 300 / 340 / 350 / 380 / 330 / 330 | 338 |
| with the two cones | 400 / 400 / 410 / 360 / 390 / 370 | 388 |
| cones + letter cubes K, E + movable fortress | 440 / 440 / 380 / 430 / 400 / 400 | 415 |

Last row: both cones, both letter cubes and the flag in every run, no penalties (delay 10: brushes
of the cone post and the pin area). The ball count varies run to run (balls bouncing in the
fortress). Delays of 12-14 frames (200+ ms) still lose a cube or the flag.

## Practice evaluation

| Configuration / driver | Setup / procedure | Measured outcome / units | Driver feedback | Failure / corrective action | Retest / evidence |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD |

Open points: shooter calibration (power vs distance) on the robot, balls bouncing out of the
fortress, pins / X mark / letter cubes for the extra points.
