# Manual Control Architecture

Operator devices, bindings, enabled modes, and override permissions are TBD pending rules and student review.

| Operator intent | Device / input | Command / units | Allowed mode / rule ID | Arbitration owner | Limits / feedback | Verification ID |
| --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Handoff and human factors

| Scenario | Expected ownership / indication | Input reset / stale command policy | Failure / recovery question | Notebook / test evidence |
| --- | --- | --- | --- | --- |
| Autonomous-to-manual handoff | TBD | TBD | TBD | TBD |
| Connection loss / reconnection | TBD | TBD | TBD | TBD |
| Stop or mode change while input is held | TBD | TBD | TBD | TBD |

Coordinate [stateflow](../stateflow/README.md), [manual strategy](../../07_strategy/manual_strategy.md), and [integration tests](../../06_verification/integration_tests/README.md). Record driver feedback and design changes in the [notebook](../../08_engineering_notebook/README.md).
