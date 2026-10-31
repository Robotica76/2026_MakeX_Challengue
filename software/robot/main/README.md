# Competition mode management

Future home of the robot entry point and top-level competition mode management:
INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL → STOP.

Coordinate subsystem authority and application lifecycle with
[autonomous arbitration](../../autonomous/arbitration/README.md). Define start
conditions, transitions, stop behavior, and handoffs in the architecture documents
before implementation.

[`robot_2026.py`](robot_2026.py) is the competition program: the 2025 flow (setup, wait for N1,
automatic stage, manual loop with the "≡" ball mode and "+" gripper mode) on the chassis.py
dynamics (S-curve manual driving with heading hold, closed-loop moves) and the automatic strategy
of `auto_pull_central.py` (N2 / N3 / N4 choose it before N1). Ports follow
`simulation/field2d/robot_config.json` and are assumptions until the electrical team confirms them.

- Simulator: Load program -> `robot_2026.py`; it reloads by itself when the file is saved.
- Robot: mBlock uploads one file, so bundle the modules first and paste the result into mBlock's
  Python editor:

```bash
.venv/bin/python tools/scripts/bundle_for_mblock.py software/robot/main/robot_2026.py
```

[`storm_breaker_2026.py`](storm_breaker_2026.py) / [`storm_breaker_2026.mblock`](storm_breaker_2026.mblock):
the competition program as blocks and as Python (the same program; regenerate the blocks with
`tools/scripts/python_to_mblock.py` after editing the Python). Automatic: X12 into exchange area 1
plus the X9 and the cones onto our side (Monte Carlo winner); manual: "≡" / "+" modes; final: N4
in Red Start 1 hangs the flag. Blocks whose Python name or opcode is still assumed (gyro angle /
rate Python names, encoder angle, timer) are listed in `simulation/field2d/mblock_project.py`
(`SENSORS`): export a project with those blocks from mBlock to confirm them.
