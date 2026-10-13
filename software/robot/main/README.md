# Competition mode management

Future home of the robot entry point and top-level competition mode management:
INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL → STOP.

Coordinate subsystem authority and application lifecycle with
[autonomous arbitration](../../autonomous/arbitration/README.md). Define start
conditions, transitions, stop behavior, and handoffs in the architecture documents
before implementation. This directory intentionally contains no robot code.
