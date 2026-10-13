# Software architecture

This tree reserves responsibilities for future implementation. There is no robot
functionality, language, runtime, hardware API, or framework selected here.

| Directory | Responsibility |
| --- | --- |
| [robot/main](robot/main/README.md) | Top-level competition mode management and application composition |
| [controls](controls/README.md) | Subsystem control logic |
| [autonomous](autonomous/README.md) | Arbitration, localization, navigation, path following, target selection, and task execution |
| [manual](manual/README.md) | Operator inputs and mappings |
| [vision](vision/README.md) | Detection and calibration |
| [drivers](drivers/README.md) | Hardware interfaces |
| [common](common/README.md) | Shared contracts and utilities |

## Intended competition control architecture

```text
INIT
 ↓
WAIT_START
 ↓
AUTONOMOUS
 ↓
MANUAL
 ↓
MODIFICATION
 ↓
FINAL
 ↓
STOP
```

This sequence is architectural intent, not an implemented state machine or a
verified statement of official phase durations or transition rules. Confirm
those details against the sourced competition requirements before coding.

Top-level competition mode management belongs in `software/robot/main/`.
Future state machine/arbitration implementation belongs in
`software/autonomous/arbitration/`; main should coordinate with it, not duplicate
its decision logic. Mode ownership, transition conditions, stop behavior,
authority handoff, and allowed subsystem actions must be specified and reviewed
before implementation.

Use explicit, documented interfaces between mode management, arbitration,
subsystem controls, vision, and drivers. Track configuration, units, coordinate
frames, timing, ownership, and failure behavior in the
[software architecture](../docs/02_system_architecture/software_architecture.md)
and [interface matrix](../docs/05_integration/interface_matrix.md).
