# Chassis Design Study

Mobility, structure, packaging, and service access for the 2026 robot. Tracked by
issue [#6 · T05 Carry over movement robot system](https://github.com/Robotica76/2026_MakeX_Challengue/issues/6).
Notebook entry: [DL-T05-001](../../08_engineering_notebook/design_log/DL-T05-001_chassis_motion_software.md).

**Status (2026-10-24):** drive type selected and motion software implemented and
simulated. CAD, prototype, and physical tests are **not started**.

## Requirements and verification status

Requirement IDs and wording come from issue #6. Page references point to the
official MakeX 2026 rules cited in that issue (revision TBD).

| ID | Requirement | Verification | Design response | Status |
| --- | --- | --- | --- | --- |
| T05-R1 | Whole robot fits inside the 500 × 500 mm Starting Area | M | CAD footprint target ≤ 480 × 480 mm | TBD (no CAD yet) |
| T05-R2 | Driving system unchanged during the Modification Stage | I | Drive hardware frozen before the event; software flags do not change hardware | TBD |
| T05-R3 | Stay in own half, or return within 3 s | P | Driver practice; `odo` pose available for autonomous boundary checks | Not executed |
| T05-R4 | Do not climb or deliberately hit the frame or central barrier | P | Accelerometer collision detection stops autonomous moves (`IMPACT_THRESHOLD`) | Not executed; threshold uncalibrated |
| T05-R5 | Do not tilt or knock over the fortress | P | Speed limits and S-curve smoothing; tilt speed to be measured (issue step 5) | Not executed |
| T05-R6 | Do not block the opponent for more than 3 s | P | Driver practice | Not executed |
| T05-R7 | Space for battery, NovaPi, and power management module | I | Reserve in CAD | TBD (no CAD yet) |
| T05-R8 | 3 m straight with < 5 cm drift | P | Gyro heading hold in `drive()` and in manual mode | Not executed (simulation did not cover 3 m runs) |
| T05-R9 | 90° turn with < 5° error | P | Closed-loop `turn_to()` on gyroscope heading | Simulation only: max 4.54° uncalibrated, p95 1.27° calibrated (see below) |

## Drive type selection (issue step 1)

| Alternative | Evaluation criteria | Evidence / uncertainty | Advantages / limitations |
| --- | --- | --- | --- |
| Tank (differential) | Traction, pushing, simplicity, maneuverability | No team code; general experience | Simple and strong; cannot strafe, so aligning to field elements needs extra turns |
| Omni X-drive | Holonomic motion, traction, packaging | No team experience | Holonomic; wheels at 45° are harder to package and have less traction |
| **Mecanum (selected)** | Holonomic motion, team experience, code reuse | Used on the 2025 winning robot; 2025 code available | Strafes and turns at the same time; strafing slips more and roller transitions vibrate at speed |

**Decision:** mecanum, X roller pattern, 8 cm wheels (2025 used 6 cm). Selected
for holonomic alignment to field elements and for reuse of the 2025 drive code
and driver experience. Rationale and rejected alternatives are logged in
[DL-T05-001](../../08_engineering_notebook/design_log/DL-T05-001_chassis_motion_software.md).

## Configuration

| Item | Value | Status |
| --- | --- | --- |
| Wheels | Mecanum, 8 cm nominal diameter | Effective diameter TBD (calibration step 3 of the Monte Carlo report) |
| Motors | 4 NovaPi encoder motors: M4 = FL, M1 = FR, M3 = RL, M2 = RR (front F1) | Deduced from 2025 code; verify on robot |
| Fronts | F1 = launcher (button "≡"), F2 = gripper (button "+") | Carried over from 2025 |
| Turn geometry | 47 cm of wheel travel per 90°, effective radius ≈ 30 cm | Measured in 2025; recalibrate if the chassis changes |
| Footprint / height | 2025 robot: ≈ 50 × 40 cm base, ≈ 60 cm tall | 2026 values TBD |

## Motion software

Implementation and API: [`software/controls/drivetrain/chassis.py`](../../../software/controls/drivetrain/chassis.py),
documented in the [drivetrain README](../../../software/controls/drivetrain/README.md).
Reused functions, control decisions, calibration parameters, and pending work:
[drivetrain motion control](../../04_controls/drivetrain_motion_control.md).

- **Kinematics:** standard mecanum mixing `FL = vy + vx + w`, `FR = vy − vx − w`,
  `RL = vy − vx + w`, `RR = vy + vx − w`, shared by manual and autonomous modes.
- **Odometry:** distance from wheel encoders, heading from the gyroscope.
  `USE_SENSORS = False` falls back to the 2025 open-loop behavior.
- **Autonomous:** `drive`, `forward`, `backward`, `right`, `left`, `turn`, `turn_to`;
  closed loop with heading hold, acceleration ramp, collision stop, and timeout.
- **Manual:** `joystick_drive(front)` with deadzone, proportional saturation,
  heading hold, S-curve smoothing (`SMOOTHING`), and speed/vibration-adaptive
  limits (`ADAPTIVE_SMOOTHING`).

## Simulation evidence

[Monte Carlo study of chassis.py](../../../simulation/analysis/reports/chassis_montecarlo/README.md)
(300 simulated robots per scenario, 2026-10-23). Its acceptance criterion
(≤ 1 cm per move) is stricter than T05-R8/R9.

| Scenario | Worst p95 drive/strafe | Worst p95 turn | Max turn error | Relevance to T05-R9 (< 5°) |
| --- | --- | --- | --- | --- |
| chassis.py as is | 4.46 cm | 3.06° | 4.54° | All simulated turns < 5° |
| C: tight tolerances + calibrated robot | 0.63 cm | 1.27° | 2.04° | All simulated turns < 5° |

Simulation tests the control logic against estimated error ranges; it does not
verify the physical robot.

## Packaging and prototype record

| Prototype / CAD revision | Mounting interface IDs | Envelope / center-of-mass assumptions | Access / interference risks | Verification ID | Result link |
| --- | --- | --- | --- | --- | --- |
| TBD (issue step 2) | TBD | ≤ 480 × 480 mm footprint; tall robot with launcher on top raises center of mass | Battery, NovaPi, power module access (T05-R7) | T05-R1, T05-R7 | TBD |

## Known issues and risks

| Issue | Evidence | Action |
| --- | --- | --- |
| 2025 robot vibrated more the faster it drove (manual and autonomous) | Team observation; hypothesis is mechanical (rollers, wheel runout, tall robot), not confirmed | Wheels-in-air test, roller check, slow-motion video; S-curve smoothing added in software |
| NovaPi sensor API names in `chassis.py` are unverified | No public NovaPi API reference found | Confirm with the Python generated by mBlock blocks |
| Strafe slip and gyro scale dominate the remaining error | Monte Carlo sensitivity (ρ = −0.96 and +0.94) | Calibrate `STRAFE_FACTOR`; add `GYRO_SCALE` (proposed in the Monte Carlo report) |
| Unknown whether mBlock uploads more than one `.py` file | Not tested | Test; fallback is concatenating modules before upload |

## Next steps

1. Confirm the sensor API from mBlock blocks and verify motor ports and signs with the wheels in the air.
2. CAD with ≤ 480 × 480 mm footprint and space for battery, NovaPi, and power module (T05-R1, R7).
3. Calibrate on the competition mat following the [Monte Carlo report](../../../simulation/analysis/reports/chassis_montecarlo/README.md#calibration-steps).
4. Run T05-R8 (3 m straight) and T05-R9 (90° and 180° turns) with at least 10 repetitions each; record results in [test results](../../08_engineering_notebook/test_results/README.md).
5. Fortress tilt test (T05-R5) and center-line practice (T05-R3, R4).

Review [mechanical interfaces](../../02_system_architecture/mechanical_interfaces.md) and [mass budget](../../02_system_architecture/weight_power_budget.md). Log build changes and failed concepts using the [entry template](../../08_engineering_notebook/design_log/entry_template.md); link [subsystem tests](../../06_verification/subsystem_tests/README.md).
