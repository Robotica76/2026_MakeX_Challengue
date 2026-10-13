# State machine and arbitration

Future home of the state machine/arbitration implementation. Define task
priorities, subsystem authority, preemption, cancellation, completion, and
failure handling before writing code.

Top-level competition mode management stays in
[robot/main](../../robot/main/README.md); coordinate with it without duplicating
mode ownership. The proposed mode sequence is documented in the
[software overview](../../README.md), not implemented here.
