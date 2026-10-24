# Engineering Design Log

| Record metadata | Value |
| --- | --- |
| Log ID / date | DL-T05-001 / 2026-10-22 to 2026-10-24 |
| Student authors / peer reviewer | TBD (T05 assignees) / TBD |
| Lifecycle stage / configuration revision | Concept + software implementation / `chassis.py` at commit `6bd40cb` (merged in PR #27) |
| Related decision / interface / test / issue IDs | Issue #6 (T05), PR #27, PR #28; T05-R1 to T05-R9 |
| Status / next review | Open: software simulated, physical tests not executed / after sensor API confirmation |

## Objective

What are we trying to accomplish?

Carry the 2025 mecanum drive into the 2026 robot (8 cm wheels instead of 6 cm),
fix the defects found in the 2025 code, and make motion precise enough for
T05-R8 (3 m straight, < 5 cm drift) and T05-R9 (90° turn, < 5° error) without
depending only on mechanical constants.

## Requirements

What requirements or competition rules affect the design?

| Requirement / local rule ID | Source document + revision + section | Constraint / criterion | Verification status |
| --- | --- | --- | --- |
| T05-R8 | Team goal, issue #6 | 3 m straight with < 5 cm drift | Not executed |
| T05-R9 | Team goal, issue #6 | 90° turn with < 5° error | Simulation only |
| T05-R4 | MakeX 2026 rules R02, p. 64 (revision TBD) | Do not hit the field frame or central barrier | Not executed |
| T05-R5 | MakeX 2026 rules R02, p. 64 (revision TBD) | Do not tilt the fortress | Not executed |
| T05-R1, R2, R3, R6, R7 | See [chassis design](../../03_design/chassis/README.md) | Packaging and driving rules | TBD (no CAD yet) |

## Design

What was designed or changed?

**1. Review of the 2025 implementation.** Sources: the 2025 robot code and the
team's 2025 engineering document ("ROBOTICA 76", MakeX Ultimate Challenge winner).

- The 2025 joystick mixing matches standard mecanum kinematics with motor map
  M4 = FL, M1 = FR, M3 = RL, M2 = RR and the left side mirrored (signs −1, +1, −1, +1).
  Switching fronts (F1 launcher / F2 gripper) inverts forward and strafe only.
- The 2025 document has two sets of equations. The ρ1–ρ4 set (p. 14) is correct.
  The M_FR/M_FL/M_RL/M_RR set (p. 15) is mirrored left–right (signs of Lx and Rx
  inverted) and has a typo (`Kx`); it should not be used as a reference.
- 2025 autonomous helpers mixed frames: `Avanzar_N` drove with the gripper in front (F2)
  while `avance_izquierda_N`/`avance_derecha_N` used the launcher front (F1), and
  `girar_derecha_*` turned counterclockwise relative to the joystick. `move()` is
  non-blocking, so chained moves overlapped. These helpers were not used in matches.
- 2025 manual control had no deadzone and clipped each wheel separately at ±100
  while the sum of axes could reach ±300.
- The 2025 manual loop sent about 13 commands per 1 ms cycle (motors, servos, DC stops).

**2. 2026 implementation** ([`chassis.py`](../../../software/controls/drivetrain/chassis.py)):

- One kinematic mix (`mecanum_mix`) and its inverse (`mecanum_unmix`) for manual and autonomous.
- `DEGREES_PER_CM` recalculated for 8 cm wheels (14.32 °/cm, 2025: 19.10 °/cm).
  The 2025 turn arc (47 cm per 90°) is a chassis property and was kept.
- Odometry class: distance from encoders, heading from the gyroscope (bias measured at
  start-up), field pose (x, y, heading), accelerometer collision flag.
- Closed-loop `drive()` and `turn_to()` with heading hold, ramp, minimum speed, collision stop,
  and timeout; every move takes a `front` argument so autonomous routines cannot mix frames.
- `USE_SENSORS` flag: `False` restores the 2025 open-loop behavior with commanded-pose bookkeeping.
- Manual: deadzone, proportional saturation, heading hold after the turn settles.
- `SMOOTHING`: jerk-limited S-curve on joystick commands.
- `ADAPTIVE_SMOOTHING`: S-curve limits scaled by speed (×1.8 at rest to ×0.7 at top speed)
  and reduced further by an accelerometer vibration level (high-pass + envelope).
- Code and comments in English; all hardware reads isolated in one `sensors` section.

Affected interfaces: drivetrain motor ports M1–M4, NovaPi IMU, gamepad mapping (unchanged
from 2025). See the [drivetrain README](../../../software/controls/drivetrain/README.md).

## Alternatives Considered

What other solutions were evaluated?

| Alternative | Evaluation criteria | Evidence / uncertainty | Advantages / limitations |
| --- | --- | --- | --- |
| Keep 2025 open-loop moves (mechanical constants only) | Accuracy, effort | Accumulates slip error; kept as `USE_SENSORS = False` fallback | No sensors needed / no correction of slip or bumps |
| Encoders + gyroscope odometry (selected) | Accuracy, robustness to slip, effort | Monte Carlo: passes with calibration | Heading immune to wheel slip / needs calibration and confirmed sensor API |
| Double-integrated accelerometer position | Accuracy | Drift of several cm within seconds | Independent of wheels / unusable for position; accelerometer used for collisions and vibration instead |
| Unpowered odometry (tracking) wheels | Accuracy, ports, mechanics | Common in FTC; legality in MakeX 2026 TBD | Best accuracy / extra encoder ports and mechanical design |
| Linear ramp for manual smoothing | Smoothness, responsiveness | Limits acceleration only | Simple / jerk still present at ramp start and end |
| S-curve (jerk-limited) smoothing (selected) | Smoothness, responsiveness | Simulated: no overshoot, 0 → 100 RPM in 0.35 s | Removes start/end jolts / adds a short delay |

## Decision

Which design was selected?

Mecanum drive with encoder + gyroscope odometry, closed-loop autonomous moves,
S-curve manual smoothing with adaptive limits, and flags to disable each feature.
Decision date 2026-10-23. Reviewers TBD.

## Rationale

Why was this approach selected?

The gyroscope gives heading independently of wheel slip, which is the main error
source of mecanum drives, and encoders give distance with low noise. Keeping every
feature behind a flag preserves the proven 2025 behavior as a fallback during the
season. The S-curve addresses the 2025 observation that the robot rocked and vibrated
at speed, without assuming its root cause. Remaining assumptions: sensor API names,
accelerometer units, motor ports and signs (see Problems).

## Prototype

What was built?

Software only (`chassis.py`, commit `6bd40cb`). No chassis prototype was built in
this entry; CAD and prototype are pending (issue steps 2–3).

## Test

How was the design tested?

Offline Python simulations with mocked `novapi`/`mbuild` (ideal wheels, gyroscope
bias 0.3 °/s, injected vibration) during development, and the
[Monte Carlo study](../../../simulation/analysis/reports/chassis_montecarlo/README.md)
in the 2D simulator (PR #28; 300 robots per scenario with sampled wheel, slip, gyro,
and encoder errors). No physical test has been executed.

## Results

What happened? Include measurements where applicable.

| Test / run | Measured outcome + units | Uncertainty / conditions | Acceptance comparison | Evidence link |
| --- | --- | --- | --- | --- |
| Dev sim: forward 60, turn 90, forward 30, left 20, turn_to 0 | All moves arrived; turns within 1.5° after raising `KP_TURN` 1.2 → 3.0 | Ideal wheels | Logic check only | This entry |
| Dev sim: `USE_SENSORS` True vs False, same routine | End pose (0.7, −88.1) cm / (0.0, −90.0) cm | Ideal wheels | Both modes consistent | This entry |
| Dev sim: S-curve step responses | 0→100 RPM 0.35 s; 100→0 0.25 s; 100→−100 0.46 s; no overshoot | dt 10 and 40 ms | Logic check only | This entry |
| Dev sim: adaptive smoothing | 0→30 RPM 0.15 → 0.11 s; reversal 0.41 → 0.31 s (no vibration), 0.47 s (with vibration) | Injected 20 Hz vibration | Logic check only | This entry |
| Monte Carlo, chassis.py as is | Turns: p95 3.06°, max 4.54°; drive/strafe p95 4.46 cm | Estimated error ranges | T05-R9 < 5°: met in simulation | [Report](../../../simulation/analysis/reports/chassis_montecarlo/README.md) |
| Monte Carlo, scenario C (calibrated, tight tolerances) | Turns p95 1.27°; drive/strafe p95 0.63 cm | Estimated residual errors | T05-R9 met in simulation | [Report](../../../simulation/analysis/reports/chassis_montecarlo/README.md) |
| T05-R8 3 m straight | Not executed | — | — | — |
| T05-R9 physical turns | Not executed | — | — | — |

## Problems / Failures

What did not work?

- Observed (2025): vibration increasing with speed in manual and autonomous modes.
  Hypothesis: mechanical (rollers, wheel runout, tall robot). Not confirmed.
- Observed (development): turns timed out with `KP_TURN = 1.2` because 1 wheel RPM
  turns the robot only ≈ 0.8 °/s with 8 cm wheels.
- Open: NovaPi API names for gyroscope, accelerometer, and encoder angle are guesses;
  no public reference was found.
- Open (Monte Carlo): `TOL_CM = 1.0` stops the robot ≈ 1 cm short; strafe slip and gyro
  scale error are invisible to the encoders.

## Corrective Actions

What was changed to address the problem?

| Issue ID | Change / revision | Owner | Retest ID / evidence | Status |
| --- | --- | --- | --- | --- |
| Turn timeout | `KP_TURN` 1.2 → 3.0 | TBD | Dev sim rerun | Done |
| 2025 vibration | S-curve and adaptive smoothing in software; mechanical checks pending | TBD | Wheels-in-air test, slow-motion video | Software done, mechanical TBD |
| Sensor API | Confirm with Python generated by mBlock blocks | TBD | — | Open |
| Tolerances / gyro scale | `TOL_CM` 0.3, `TOL_DEGREES` 0.5, add `GYRO_SCALE` (from Monte Carlo report) | TBD | Regenerate Monte Carlo report | Open |

## Final Decision

Keep / Modify / Reject

**Modify** — keep the architecture; apply the Monte Carlo tolerance and `GYRO_SCALE`
changes and calibrate on the competition mat before physical verification of T05-R8/R9.
Reviewer TBD.

## Evidence

Links or references to CAD, pictures, calculations, measurements, plots, videos,
or code.

| Evidence ID | Relative link or authorized reference | Revision / date / creator | Requirement / decision / test IDs | What it supports |
| --- | --- | --- | --- | --- |
| EV-T05-01 | [chassis.py](../../../software/controls/drivetrain/chassis.py) | `6bd40cb`, 2026-10-23 | T05-R8, R9 | Implementation |
| EV-T05-02 | [Drivetrain README](../../../software/controls/drivetrain/README.md) | 2026-10-23 | Interfaces | Frames, flags, open items |
| EV-T05-03 | [Monte Carlo report](../../../simulation/analysis/reports/chassis_montecarlo/README.md) | PR #28, 2026-10-23 | T05-R8, R9 | Simulated accuracy and calibration plan |
| EV-T05-04 | [Chassis design study](../../03_design/chassis/README.md) | 2026-10-24 | T05-R1 to R9 | Requirement status |
| EV-T05-05 | 2025 team engineering document "ROBOTICA 76" (team-owned, not stored in repo) | 2025 | Drive selection | 2025 kinematics, wheel size, lessons |
| EV-T05-06 | [Drivetrain motion control](../../04_controls/drivetrain_motion_control.md) | 2026-10-24 | T05-R8, R9 | Reused functions, control decisions, calibration, TODO |
