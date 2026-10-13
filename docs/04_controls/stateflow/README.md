# Stateflow and Arbitration Specification

Proposed mode chain, not verified competition format:

`INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL → STOP`

Top-level mode management belongs conceptually in `software/robot/main/`; state machine/arbitration belongs conceptually in `software/autonomous/arbitration/`. No implementation is included.

## Transition contracts

| Proposed transition | Official source / rule ID | Authoritative trigger | Guard / preconditions | Exit / entry actions | Command handoff / cancellation | Test ID |
| --- | --- | --- | --- | --- | --- | --- |
| INIT → WAIT_START | TBD | TBD | TBD | TBD | TBD | TBD |
| WAIT_START → AUTONOMOUS | TBD | TBD | TBD | TBD | TBD | TBD |
| AUTONOMOUS → MANUAL | TBD | TBD | TBD | TBD | TBD | TBD |
| MANUAL → MODIFICATION | TBD | TBD | TBD | TBD | TBD | TBD |
| MODIFICATION → FINAL | TBD | TBD | TBD | TBD | TBD | TBD |
| FINAL → STOP | TBD | TBD | TBD | TBD | TBD | TBD |

## Arbitration contract

| Mode / actuator group | Eligible command sources | Single owner | Priority / conflict resolution | Stale / denied command handling | Reviewer |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD |

## Exceptional paths to resolve

| Event | Applicable modes | Requested destination / safe response | Guard / reset authority | Official / engineering basis | Verification / notebook link |
| --- | --- | --- | --- | --- | --- |
| Stop / emergency-stop request | TBD | TBD | TBD | TBD | TBD |
| Fault / loss of communication | TBD | TBD | TBD | TBD | TBD |
| Invalid or repeated transition | TBD | TBD | TBD | TBD | TBD |
| Reset / recovery request | TBD | TBD | TBD | TBD | TBD |

Verify phase meanings, timing, modification permissions, and FINAL behavior before accepting the chain. Record transition ownership decisions in [design logs](../../08_engineering_notebook/design_log/README.md) and test plans in [integration tests](../../06_verification/integration_tests/README.md). See [software architecture](../../02_system_architecture/software_architecture.md).
