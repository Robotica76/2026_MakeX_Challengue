# Software Architecture

This is a future organization and responsibility proposal only. No code, controllers, or state machines are implemented by these documents.

## Ownership boundaries

| Intended future path | Proposed responsibility | Must coordinate with | Open design decisions |
| --- | --- | --- | --- |
| `software/robot/main/` | Top-level mode management; consume phase/start/stop information and coordinate robot-wide mode requests | Arbitration and all subsystems | Authoritative signals, guards, transition ownership, safety policy: TBD |
| `software/autonomous/arbitration/` | State machine/arbitration; resolve command ownership and enable/deny requests according to agreed mode policy | Top-level manager, autonomous routines, manual input | Priority, handoff, stale-command handling, fault overrides: TBD |

The top-level manager should request mode changes; arbitration should determine permitted command ownership under the agreed policy. Specify one authoritative owner for each transition and actuator before implementation. Safety precedence and stop behavior remain design decisions requiring review.

## Intended competition mode model

`INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL → STOP`

This chain is subject to official rules verification. Do not infer phase durations, operator permissions, modification permissions, or FINAL behavior from these names.

| Proposed mode | Design question | Command owner / permitted actions | Transition trigger / guard | Rule source | Verification ID |
| --- | --- | --- | --- | --- | --- |
| INIT | What initialization and checks are allowed? | TBD | TBD | TBD | TBD |
| WAIT_START | What constitutes a valid start and readiness state? | TBD | TBD | TBD | TBD |
| AUTONOMOUS | What autonomous behavior is allowed? | TBD | TBD | TBD | TBD |
| MANUAL | What operator authority and limits apply? | TBD | TBD | TBD | TBD |
| MODIFICATION | Is this phase permitted, and what can change? | TBD | TBD | TBD | TBD |
| FINAL | What does this stage mean under official rules? | TBD | TBD | TBD | TBD |
| STOP | What stopped state and reset policy are required? | TBD | TBD | TBD | TBD |

Fault, cancellation, and emergency-stop paths are **not defined** by the linear chain. Document and review them explicitly in [stateflow](../04_controls/stateflow/README.md) before implementation.

## Data and command contracts

| Interface ID | Producer → consumer | Message / units / coordinate frame | Validity / freshness | Arbitration / rejection behavior | Requirement ID |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD |

Trace decisions to [controls](../04_controls/README.md), [integration interfaces](../05_integration/interface_matrix.md), and [notebook logs](../08_engineering_notebook/design_log/README.md).
