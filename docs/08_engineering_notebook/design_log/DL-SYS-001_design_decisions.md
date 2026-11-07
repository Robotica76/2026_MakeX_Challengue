# DL-SYS-001 · Design decisions register (robot v15 → v22)

Single register of the decisions taken so far for the Storm Breaker robot: mechanical (CAD
revisions v15 to v22), control software, simulation, and strategy. Each row says what was
decided, why, what was rejected, and where the evidence is. IDs are local (`DEC-…`) and stable;
other READMEs refer to them.

**Status of the evidence:** CAD checks, 2D contact simulations, rigid-body estimates, and
field simulations. **Nothing has been built or measured on a robot yet.** A decision here is a
design intent until the matching test in [`tests/`](../../../tests/README.md) passes.

Dates are when the decision entered the repository (CAD revisions were produced between
2026-10-24 and 2026-11-06 and committed as v22 on 2026-10-30 / 2026-11-06).

## Mechanical (CAD)

| ID | Decision | Why (evidence) | Rejected alternatives | Where |
| --- | --- | --- | --- | --- |
| DEC-M01 | Four 80 mm mecanum wheels on 180 smart encoder motors; front axle at `y = +45`, rear at `y = −203`, track 442.5 mm | Omnidirectional driving is used to align on shelves and to strafe off the flag. The front axle cannot go further forward: with the robot face against the Central Resource Area table (`y = 93`) the lower shelf occupies the space ahead of the wheels | Wheels further forward (collide with the lower shelf); tank drive (no strafing) | [chassis](../../../mechanical/chassis/README.md), [DL-T05-001](DL-T05-001_chassis_motion_software.md) |
| DEC-M02 | Fixed launcher on the left side, firing toward `−x`; **no turret** (v17) | Champion-style layout: a turret cost mass and space and the mecanum base can aim the whole robot. Frees the centre for a tall storage tower | Rotating turret on the tower (v14–v16); launcher on the forward axis | [shooter](../../../mechanical/shooter/README.md) |
| DEC-M03 | Ball tower **3 balls wide** (227 mm inside), tilted 15°, top at `z = 430` (v19) | Stores ~15 balls in the tower itself. The top must respect the Central Area roof (nothing above `z = 543` for `y > −67`) | 1-ball tower (v17–v18, ~5 balls); basket behind the turret (v16); two independent lifts (v17 lane-2 idea) | [feeder](../../../mechanical/feeder/README.md) |
| DEC-M04 | **Elbow** at the tower top: roller r20 with a concentric cover R86 (165° → −15°) carries the ball over and drops it into the basket (v18) | 2D simulation: works from 0.42 to 1.26 m/s roller speed | Single top roller (ball flew out or stalled in simulation) | [feeder](../../../mechanical/feeder/README.md), [sim figure](../../../mechanical/feeder/prototypes/README.md) |
| DEC-M05 | **Inverted launcher** (friction wheel above, hood below) fed horizontally from a sloped basket floor; the short **feed roller is the gate** (no servo gate) — team proposal (v19) | 2D simulation: with the feed roller stopped the ball waits even with the wheel at speed; with the roller running it fires at ~44° (fixed hood) or ~54–58° (servo flap) | Over-the-top launcher with a pocket and a one-way flap (v18); servo gate | [shooter](../../../mechanical/shooter/README.md), [ball_storage](../../../mechanical/ball_storage/README.md) |
| DEC-M06 | Feed roller driven 3:1 (48T → 16T) by a DC-25 under the basket floor (v20) | At 200 RPM direct (0.31 m/s) the waiting ball does not climb into the wheel (simulation); 0.94 m/s fires it | Direct drive inside the roller (v19) | [ball_storage](../../../mechanical/ball_storage/README.md) |
| DEC-M07 | Elbow roller keeps its own internal DC-25 | A transmission from the tower belts needs ~98 mm gears or a crossed belt that clash with the launcher or with the ball path | Belt / gear drive from the tower (would free one motor slot) | [feeder](../../../mechanical/feeder/README.md) |
| DEC-M08 | Wide intake: R3 entry roller ±108 mm, R2 changed to a straight roller (v19) | The tower is 3 balls wide, so balls no longer need centring | Helical centring R2 (v15–v18) | [ball_intake](../../../mechanical/ball_intake/README.md) |
| DEC-M09 | Mass reductions: carbon-fibre tube rails instead of aluminium 2020 profile, aluminium axles where unloaded (v19) | Robot mass 9.88 kg in CAD (limit 10 kg) | Aluminium profile and steel axles (over budget) | [full_robot v22](../../../mechanical/assemblies/full_robot/v22/README.md) |
| DEC-M10 | Electronics inside a **structural carbon-fibre box** on the rear rails (v21); the box floor is bolted to both rails and acts as a rear cross-member | Protects battery and NovaPi; adds rigidity. Stability is the same as with a low tray (0.49 g forward tip) because the box is further back | Low open tray at 14 mm from the floor (v20: exposed); electronics floating at `z = 61` without support (v19) | [chassis](../../../mechanical/chassis/README.md), [KI-003](../../05_integration/known_issues.md) |
| DEC-M11 | Motors **not relocated**; forward stability handled by software (braking ≤ 0.35 g) | Moving the intake DC-37, the UR lift DC-25 and the elbow DC-25 would gain only ~+0.03 g of forward tip margin for a large redesign; the limit is the front-axle position (DEC-M01) | Bevel-gear relocations of the UR lift motor and the intake motor | [chassis prototypes](../../../mechanical/chassis/prototypes/README.md) |
| DEC-M12 | **Removable flag mast** installed in the Modification Stage: CF tube 8×6 in a receptor on the gripper mounting block, C-shaped head closed by two rubber bands — team proposal (v22) | Uses the gripper elevator (358 mm stroke) to lift the flag over the field bar at ~950–965 mm without a new motor (13/13 used). 31.6 g; robot 9.92 kg with it | Fixed tall mast (fails the 700 mm initial height); open hook (T08 (5) forbids hook-shaped parts) | [flag_system](../../../mechanical/flag_system/README.md) |
| DEC-M13 | Part numbering `<subsystem>.<part>` and one folder per subsystem with `cad/`, `drawings/`, `manufacturing/`, `prototypes/` (v22) | One number per part across the manual, STL names and BOMs | Prefix names only | [mechanical](../../../mechanical/README.md) |

## Control software

| ID | Decision | Why (evidence) | Where |
| --- | --- | --- | --- |
| DEC-S01 | Reuse the 2025 mecanum drive code, adding encoder + gyroscope odometry, closed-loop moves, and an adaptive S-curve for manual driving | Team code already proven in 2025; the Monte Carlo study shows calibration, not gains, is the limiting factor | [DL-T05-001](DL-T05-001_chassis_motion_software.md), [chassis.py](../../../software/controls/drivetrain/README.md) |
| DEC-S02 | Robot "fronts" are angles (`F_INTAKE` 0°, `F_GRIPPER` 90°, `F_LAUNCHER` −90°, `F_REAR` 180°) | v22 puts the gripper and the launcher on the sides (KI-006) | [drivetrain motion control](../../04_controls/drivetrain_motion_control.md) |
| DEC-S03 | Drive geometry from the v22 CAD: 0.603 cm of wheel travel per degree, odometry centre 7.9 cm ahead of the wheel rectangle | The 2025 constant (47 cm / 90°) made open-loop turns ~13 % short (KI-005) | [known issues](../../05_integration/known_issues.md) |
| DEC-S04 | Competition program written in the Python subset that mBlock blocks can express; `python_to_mblock.py` and `mblock_project.py` convert both ways and the tests check the round trip | The team programs in mBlock blocks; one source of truth for blocks and Python | [robot/main](../../../software/robot/main/README.md), [tools/scripts](../../../tools/scripts/README.md) |
| DEC-S05 | Profiled point-to-point motion in field coordinates (`go_N_N_N_N_N`, braking `v = √(v_end² + 2·D·d)`), long moves facing their direction, `STRAFE_SLIP` calibration, start-alignment jig | Monte Carlo: start heading error dominates (1° → 30 mm at the gripper after 1.7 m) and strafing slips ~7 % | [Monte Carlo strategy](../../07_strategy/montecarlo_strategy.md) |
| DEC-S06 | Assisted aiming: R2 aims the launcher at the blue fortress and sets the power from the odometry distance (ballistic model); N3 does the same at the X mark | Fixed-coordinate aim loses ~350 points if the opponent moves its fortress 150 mm | [Monte Carlo strategy](../../07_strategy/montecarlo_strategy.md) |

## Simulation

| ID | Decision | Why | Where |
| --- | --- | --- | --- |
| DEC-X01 | Own 2D simulator (pygame) and 3D viewer (Panda3D) that run the **same mBlock Python** with stand-in `novapi` / `mbuild` modules; the 3D view reuses the 2D physics | Test the real robot program before the robot exists; identical motion in 2D and 3D | [field2d](../../../simulation/field2d/README.md), [field3d](../../../simulation/field3d/README.md) |
| DEC-X02 | Robustness judged by Monte Carlo over sampled imperfect robots, with a one-sided Clopper–Pearson 95 % lower bound ≥ 95 % per move kind | A single ideal run hides slip, gyro scale, and start errors | [chassis Monte Carlo](../../../simulation/analysis/reports/chassis_montecarlo/README.md) |

## Strategy

| ID | Decision | Why (simulation) | Where |
| --- | --- | --- | --- |
| DEC-T01 | Automatic stage: X12 bonus cube into red exchange area 1 first (`ORDER` 12 today; 13 = X12 then the lower table balls is the candidate) | Every route without the X12 first loses its 12 bonus balls; 13 scored best in whole matches (443 mean) | [Monte Carlo strategy](../../07_strategy/montecarlo_strategy.md) |
| DEC-T02 | Our robot plays the lower half of the red camp (two robots per alliance) | Avoid interference with the partner | [storm_breaker_2026.py](../../../software/robot/main/README.md) |
| DEC-T03 | Keep 2 balls for the X mark and fire them at ~277.8 s (last hit wins) | Paired Monte Carlo: +11 ± 11 points | [four robots report](../../../simulation/analysis/reports/four_robots/REPORTE.md) |

## Open decisions

| Topic | Options | Blocking evidence |
| --- | --- | --- |
| Power-module visibility (T17-R7) | Polycarbonate lid / window on the electronics box | Inspection rule reading; KI-003 |
| Flag mast position | v22 mast on the gripper carriage (right side) vs the simulated proposal: rod on the left side reaching the front edge (the cone post keeps the right-side rod ≥ 150 mm short of flagpole 2) | KI-008: move the C head to the left front, or a new approach |
| Elevator travel | 358 mm (v22 CAD) vs 430 mm proposed so a gripped cone clears the 405 mm cone post | `simulation/analysis/cone_post_reach.py`; CAD change not made |
| Motor reserve (T02-R6) | Free one motor (elbow from the tower belts, or merge functions) | KI-002 |
| `ORDER` 12 vs 13 | Paired Monte Carlo difference is barely distinguishable from zero | More trials; robot calibration |
