# Drivetrain Motion Control

Control record for [`software/controls/drivetrain/chassis.py`](../../software/controls/drivetrain/chassis.py),
issue [#6 · T05](https://github.com/Robotica76/2026_MakeX_Challengue/issues/6).
Design context: [chassis design study](../03_design/chassis/README.md).
Notebook: [DL-T05-001](../08_engineering_notebook/design_log/DL-T05-001_chassis_motion_software.md).

**Status (2026-10-24):** implemented and simulated. Not yet tested on the robot.
Values below are the ones in `chassis.py` at this date.

- [Part 1 · Reused and improved functions](#part-1--reused-and-improved-functions)
- [Part 2 · Control decisions](#part-2--control-decisions)
- [Calibration parameters](#calibration-parameters)
- [TODO](#todo)

---

## Part 1 · Reused and improved functions

The 2025 robot (MakeX Ultimate Challenge winner) was the starting point. Every
2025 drive function has a 2026 equivalent; the table lists what was kept and what
was fixed.

### Function map

| 2025 function | 2026 function | Kept | Improved / fixed |
| --- | --- | --- | --- |
| `movimiento_joystick_lanzador()` / `movimiento_joystick_pinza()` | `joystick_drive(front)` with `F1` / `F2` | Same mecanum mixing and the two fronts (launcher / gripper) | One function instead of two copies; deadzone; proportional saturation; heading hold; S-curve smoothing |
| Mixing written inline per motor | `mecanum_mix(vy, vx, w)` / `mecanum_unmix(...)` | Same equations (standard mecanum) | Shared by manual and autonomous; inverse used by odometry |
| `Avanzar_N(cm)` / `Retroceder_N(cm)` | `forward(cm, front)` / `backward(cm, front)` | Distance in cm | Explicit front (2025 used the gripper front without saying so); closed loop; waits until arrival; returns `True`/`False` |
| `avance_izquierda_N(cm)` / `avance_derecha_N(cm)` | `left(cm, front)` / `right(cm, front)` | Distance in cm | 2025 used the launcher front, the opposite of `Avanzar_N`; fixed `+5 cm` replaced by calibrated `STRAFE_FACTOR` |
| `girar_izquierda_90/180_C2_B0()` / `girar_derecha_90/180_C2_B0()` | `turn(degrees)` / `turn_to(heading)` | 47 cm of wheel travel per 90° (`CM_PER_TURN_DEGREE`) | Any angle; 2025 "right" turned counterclockwise relative to the joystick; closed loop on the gyroscope; absolute headings |
| `Diametro = 6`, `cm / ((Diametro * pi) / 360)` | `WHEEL_DIAMETER = 8.0`, `DEGREES_PER_CM` | Same conversion | 8 cm wheels (14.32 °/cm instead of 19.10 °/cm); one constant instead of repeated formulas |
| `encoder_motor_Mx.move(...)` called 4 times, no wait | `move_open_loop(...)` | 2025 open-loop behavior, kept as a fallback (`USE_SENSORS = False`) | Per-wheel speeds so all wheels finish together; waits for the theoretical time; tracks the commanded pose |
| — | `Odometry` (`odo`) | — | New: field pose from encoders + gyroscope; collision and vibration detection |
| — | `SCurve`, `smoothing_scale()` | — | New: jerk-limited, adaptive manual smoothing |
| `auxiliar_modo_pinza_lanzador` with buttons "≡" / "+" | `F1` / `F2` constants | Same buttons and meaning | Front handling lives in the drivetrain; mode switching stays in the main program |

### Defects found in the 2025 code and in the 2025 document

| Defect | Effect | 2026 fix |
| --- | --- | --- |
| Autonomous helpers mixed fronts (F2 for forward, F1 for strafe) | "Left" moved right when the gripper was in front | Every move takes `front` |
| `girar_derecha_*` sign inverted relative to the joystick | Turned counterclockwise | `turn()` follows the joystick convention (clockwise +) |
| `move()` is non-blocking and was chained | Consecutive moves overlapped | Closed-loop moves wait; `move_open_loop()` waits too |
| No joystick deadzone | Motors twitch when the stick is released | `DEADZONE = 8` |
| Each wheel clipped at ±100 while `Ly + Lx + Rx` reached ±300 | Wheels fought each other in combined moves | `set_wheel_speeds()` scales all wheels proportionally |
| About 13 module commands per 1 ms cycle in manual mode | Irregular control rate | Partly addressed (see [Sampling time](#sampling-time)); send-on-change is a TODO |
| 2025 document, p. 15: M_FR/M_FL/M_RL/M_RR equations mirrored left–right, typo `Kx` | Wrong strafe and turn directions if used | Use the p. 14 (ρ1–ρ4) equations, implemented in `mecanum_mix()` |

---

## Part 2 · Control decisions

### Frames and conventions

- Robot frame: `vy` forward (+), `vx` right (+), `w` clockwise (+). Angles in degrees.
- Switching the front (`F1` ↔ `F2`) negates `vy` and `vx`, never `w`.
- Field frame: origin and heading 0 where `odo.reset()` is called.

### Odometry: encoders for distance, gyroscope for heading

| Decision | Reason |
| --- | --- |
| Distance from the four encoders through `mecanum_unmix()` | Low noise; already in the motors |
| Heading from the gyroscope, not from the encoders | Mecanum wheels slip; the gyroscope does not depend on traction |
| Gyroscope bias measured at start-up (`odo.calibrate()`) plus a ±0.5 °/s deadzone | Removes the constant drift while the robot is still |
| Accelerometer **not** used for position | Double integration drifts several cm within seconds |
| Accelerometer used for collisions and vibration | Short events, no integration needed |
| Pose projected with the mid-cycle heading | Less error while turning and moving at the same time |

### Closed-loop autonomous moves

`drive()` (straight and diagonal) and `turn_to()` share one structure:

1. Error in the field frame, converted to the robot frame each cycle.
2. Proportional command (`KP_DIST`, `KP_TURN`), limited between `MIN_SPEED` and the requested speed.
3. Heading hold during `drive()` (`KP_HEADING`), so a bump does not change direction.
4. Ramp on the command (`RAMP`) to avoid wheel slip at start.
5. Exit on arrival (`TOL_CM`, `TOL_DEGREES`), on collision (`IMPACT_THRESHOLD`), or on `timeout`. Returns `True` only on arrival.

`KP_TURN` was raised from 1.2 to 3.0 after simulated turns timed out: with 8 cm
wheels, 1 wheel RPM turns the robot only about 0.8 °/s.

### S-curve smoothing that reacts to the robot's motion

Problem: the 2025 robot rocked and vibrated more the faster it drove. A linear
ramp limits acceleration but still jolts at the start and end of each change.

**Decision 1: jerk-limited S-curve (`SCurve`).** Acceleration grows and fades
gradually. Each cycle the rate is limited to `√(2·J·|error|)`, the largest rate
that can still fade to zero exactly at the target, so the profile never overshoots.

| Simulated step | Time | Overshoot |
| --- | --- | --- |
| 0 → 100 RPM | 0.35 s | No |
| 100 → 0 RPM (stick released) | 0.25 s | No |
| 100 → −100 RPM (reversal or front switch) | 0.46 s | No |

**Decision 2: braking faster than speeding up.** `DECEL`/`DECEL_JERK` are higher
than `ACCEL`/`JERK`, so releasing the stick stops the robot sooner.

**Decision 3: limits that adapt to the robot's state (`ADAPTIVE_SMOOTHING`).**
`smoothing_scale()` multiplies the S-curve limits each cycle:

- **By speed, as a proxy for momentum:** ×1.8 at rest down to ×0.7 at `MAX_SPEED`.
  Near standstill the robot carries little momentum, so it can react quickly; at
  speed, the same change needs more force and excites more vibration, so the
  profile becomes gentler. This needs no sensors.
- **By measured vibration:** the accelerometer signal is split into slow motion
  (`VIB_BASE_TAU`, also removes gravity from tilt) and fast vibration, whose level
  (`VIB_ENVELOPE_TAU`) lowers the multiplier down to ×`VIB_MIN_SCALE`. The robot
  becomes smoother on its own when it starts shaking.

| Simulated case | Fixed S-curve | Adaptive |
| --- | --- | --- |
| 0 → 30 RPM (90 %) | 0.15 s | 0.11 s |
| 0 → 100 RPM (90 %) | 0.30 s | 0.24 s |
| Reversal 100 → −90, no vibration | 0.41 s | 0.31 s |
| Reversal 100 → −90, with vibration | 0.41 s | 0.47 s |

Limitation: speed is used as a proxy for inertia. Mass and center-of-mass height
are not estimated. Robot rocking depends on acceleration, not speed, so
`LOW_SPEED_SCALE` must be tuned if the robot tilts when starting from rest.

**Decision 4: heading hold waits for the turn to settle.** In manual mode the held
heading is captured only after the smoothed turn rate falls below 1 RPM, so the
gyroscope does not fight the end of a smoothed turn.

### Sampling time

| Aspect | 2025 | 2026 |
| --- | --- | --- |
| Manual loop | `time.sleep(0.001)` plus about 13 module commands per cycle; real period unknown and irregular | Nominal `PERIOD = 0.01` s |
| Time base | None (cycle count) | `now()` from `time.ticks_ms()` (falls back to `time.time()`) |
| Integration of heading, pose, and S-curve | — | Uses the **measured** `dt` of each cycle, so results do not depend on loop speed |
| Protection against pauses | — | S-curve `dt` clamped to 1–50 ms so a long pause does not produce a jump |
| Robustness check | — | S-curve tested at 10 ms and 40 ms cycles: same shape, no overshoot |

Known limits (see [TODO](#todo)): autonomous loops sleep `PERIOD` **after** the
work, so the real period is `PERIOD` + computation time; `RAMP` is defined per
cycle, not per second; every cycle reads 4 encoders, the gyroscope, and 2
accelerometer axes, and the real loop time on the NovaPi has not been measured.

### Feature flags

| Flag | `True` | `False` |
| --- | --- | --- |
| `USE_SENSORS` | Encoders + gyroscope + accelerometer, closed loop | 2025 open-loop behavior with commanded-pose bookkeeping |
| `SMOOTHING` | S-curve on joystick commands | Direct joystick response |
| `ADAPTIVE_SMOOTHING` | Limits scaled by speed and vibration | Fixed S-curve limits |

The autonomous routines are written the same way for both `USE_SENSORS` values.

---

## Calibration parameters

All values must be measured on the competition mat, with a charged battery and
the robot at its final weight. Detailed procedures for the starred items:
[Monte Carlo report, calibration steps](../../simulation/analysis/reports/chassis_montecarlo/README.md#calibration-steps).

### Mechanical and sensor (calibrate first)

| Parameter | Current | How to calibrate | Priority |
| --- | --- | --- | --- |
| Motor ports and `SIGNS` | M4/M1/M3/M2, (−1, 1, −1, 1) | Wheels in the air: `Ly` up spins all wheels forward | 1 |
| `GYRO_SIGN` ★ | 1 | Turn by hand clockwise: `odo.heading` must increase | 1 |
| Gyroscope bias | Measured at start-up | `odo.calibrate()` with the robot still; 60 s drift check | 1 |
| `WHEEL_DIAMETER` ★ | 8.0 cm | 200 cm run: `× D_real / D_odo` (effective diameter) | 2 |
| `STRAFE_FACTOR` ★ | 1.0 | 100 cm strafe: `× D_odo / D_real` (estimated 1.05–1.10) | 2 |
| `GYRO_SCALE` ★ | Not in the code yet | 10 hand turns: `× 3600 / |H|` | 2 |
| `CM_PER_TURN_DEGREE` | 47 / 90 | Only for `USE_SENSORS = False`: 360° open-loop turn | 3 |

### Control loop

| Parameter | Current | Tune by | Priority |
| --- | --- | --- | --- |
| `TOL_CM` | 1.0 cm | Monte Carlo recommends 0.3 | 2 |
| `TOL_DEGREES` | 1.5° | Monte Carlo recommends 0.5 | 2 |
| `KP_DIST` | 4.0 RPM/cm | Overshoot → lower; slow ending → higher | 3 |
| `KP_TURN` | 3.0 RPM/° | Oscillation → lower; slow ending → higher | 3 |
| `KP_HEADING` | 2.0 RPM/° | Weaving → lower; drift after bumps → higher | 3 |
| `MIN_SPEED` | 12 RPM | Lowest speed at which the robot still moves on the mat | 3 |
| `RAMP` | 6 RPM/cycle | Wheel slip at start → lower | 3 |
| `AUTO_SPEED` / `MAX_SPEED` | 80 / 100 RPM | Speed vs. accuracy; vibration limit | 3 |
| `DEADZONE` | 8 | Raise if the robot creeps with the stick released | 3 |
| `IMPACT_THRESHOLD` | 15.0 (units TBD) | Log acceleration during normal driving and a soft bump | 3 |

### Smoothing

| Parameter | Current | Tune by | Priority |
| --- | --- | --- | --- |
| `ACCEL` / `JERK` | 400 RPM/s / 3000 RPM/s² | Rocks at start → lower `JERK`; feels sluggish → higher `ACCEL` | 4 |
| `DECEL` / `DECEL_JERK` | 700 / 5000 | Tips forward when braking → lower `DECEL_JERK` | 4 |
| `TURN_ACCEL` / `TURN_JERK` | 500 / 4000 | Same, for turns | 4 |
| `LOW_SPEED_SCALE` / `HIGH_SPEED_SCALE` | 1.8 / 0.7 | Tilts when starting from rest → `LOW_SPEED_SCALE` 1.2–1.4 | 4 |
| `VIB_OK` / `VIB_MAX` | 1.0 / 4.0 (units TBD) | Print `odo.vibration`: value at medium speed without visible vibration / with bad vibration | 4 |
| `VIB_MIN_SCALE` | 0.4 | Lowest acceptable responsiveness | 4 |
| `VIB_BASE_TAU` / `VIB_ENVELOPE_TAU` | 0.1 s / 0.2 s | Only if the vibration level reacts too slowly or too nervously | 5 |

---

## TODO

### Blocking (needed before testing on the robot)

- [ ] Confirm NovaPi API names with the Python generated by mBlock blocks: gyroscope Z rate, accelerometer X/Y, encoder angle, timer (`read_gyro_z`, `read_accel`, `read_motor_angle`, `now`).
- [ ] Confirm accelerometer units (g or m/s²) and NovaPi axis orientation relative to the robot.
- [ ] Verify motor ports and `SIGNS` with the wheels in the air.
- [ ] Find out whether mBlock uploads more than one `.py` file; otherwise add a build script that concatenates modules.

### Code changes

- [ ] Add `GYRO_SCALE` (two lines, proposed in the Monte Carlo report).
- [ ] Set `TOL_CM = 0.3` and `TOL_DEGREES = 0.5` and check routine timeouts.
- [ ] Fixed-period loop: sleep for `PERIOD` minus the computation time instead of a fixed `PERIOD`.
- [ ] Make `RAMP` time-based (RPM/s) or replace it with `SCurve` in `drive()` and `turn_to()`.
- [ ] Send motor, servo, and DC commands only when the value changes.
- [ ] Measure and log the real loop time on the NovaPi.
- [ ] Optional `on_cycle` callback in `drive()`/`turn_to()` to run mechanisms during a move.
- [ ] Lever-arm correction of the accelerometer (NovaPi offset from the chassis center) once the mounting position is known.
- [ ] Wheel-slip residual `FL + FR − RL − RR` and encoder-vs-IMU acceleration comparison.
- [ ] Continuous gyroscope bias update while the encoders report no motion.
- [ ] `align_to_wall()` using the ranging sensor to reset `odo` against field walls.
- [ ] Vibration diagnostic tool: fixed speed, record accelerometer, report dominant frequency.
- [ ] Optional: choose `USE_SENSORS` at power-up with a button combination.

### Calibration and verification

- [ ] Calibrate the parameters above in priority order.
- [ ] T05-R8: 3 m straight, < 5 cm drift, at least 10 runs.
- [ ] T05-R9: 90° and 180° turns, < 5° error, at least 10 runs each.
- [ ] Update `montecarlo_config_calibrated.json` with measured spreads and regenerate the report.
- [ ] Mechanical vibration checks: rollers spin freely, wheels-in-air test, slow-motion video.
- [ ] Check whether unpowered odometry wheels are legal in MakeX 2026.
