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

## Practice evaluation

| Configuration / driver | Setup / procedure | Measured outcome / units | Driver feedback | Failure / corrective action | Retest / evidence |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD |

Open points: shooter calibration (power vs distance) on the robot, balls bouncing out of the
fortress, pins / X mark / letter cubes for the extra points.
