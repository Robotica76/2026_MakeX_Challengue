# Software

Programs that run on the robot's **NovaPi** (Makeblock mBlock Python: `novapi`, `mbuild`). The
same files run unchanged in the [simulators](../simulation/README.md), which emulate those modules.

## What runs on the robot

| Program | Role | Status |
| --- | --- | --- |
| [`robot/main/storm_breaker_2026.py`](robot/main/storm_breaker_2026.py) + [`.mblock`](robot/main/storm_breaker_2026.mblock) | **Competition program** (one file, blocks and Python are the same program): automatic missions by `ORDER`, manual loop with two modes, aim assist, flag routine | Simulated (Monte Carlo); not run on the robot |
| [`robot/main/robot_2026.py`](robot/main/robot_2026.py) | 2025 flow on `chassis.py` + `auto_pull_central.py`; needs `bundle_for_mblock.py` | Simulated |
| [`controls/drivetrain/chassis.py`](controls/drivetrain/chassis.py) | Mecanum drive: odometry, closed-loop moves, adaptive S-curve | Simulated + Monte Carlo |
| [`autonomous/task_execution/`](autonomous/task_execution/README.md) | Automatic-stage routines | Simulated |
| [`legacy/challenge_2025/`](legacy/challenge_2025/README.md) | 2025 program (blocks + Python) | Reference |

## Organisation

| Directory | Content |
| --- | --- |
| [robot](robot/README.md) | Top-level programs ([main](robot/main/README.md)) |
| [controls](controls/README.md) | Drivetrain (`chassis.py`), ball system, shooter, manipulator, flag |
| [autonomous](autonomous/README.md) | Task execution, path following, localization, navigation, target selection, arbitration |
| [manual](manual/README.md) | Gamepad and bindings |
| [vision](vision/README.md) | AI camera plans and reference material |
| [drivers](drivers/README.md) | mBlock APIs used (no wrappers) |
| [common](common/README.md) | Shared code (inlined by the bundler) |
| [legacy](legacy/README.md) | 2025 program |

## Match flow (as implemented)

```text
power on → constants() → wait for N1 → automatic() [30 s, missions in ORDER, all stopped before END_BY]
        → manual_loop()  ["≡" ball mode / "+" gripper mode; R2 aim fortress, N3 aim X, N2 pull mode, N4 flag]
```

The proposed formal mode chain (INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL →
STOP) and the missing fault paths are in [stateflow](../docs/04_controls/stateflow/README.md).

## Key decisions

DEC-S01 reuse 2025 drive + odometry, DEC-S02 fronts as angles, DEC-S03 v22 geometry, DEC-S04
blocks-expressible Python, DEC-S05 profiled motion + calibration, DEC-S06 aim assist —
[DL-SYS-001](../docs/08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md).

## Before the first run on the robot

1. Wire and confirm the port map ([electrical](../electrical/architecture/README.md); simulator copy in `robot_config.json`).
2. Confirm the NovaPi sensor API names (gyro, accelerometer, encoder angle).
3. Calibrate ([tools/calibration](../tools/calibration/README.md)) and write the constants.
4. Fix the flag routine vs the flag-mast position (KI-008).
