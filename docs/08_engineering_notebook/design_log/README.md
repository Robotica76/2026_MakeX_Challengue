# Design Log

Dated engineering records: decisions, alternatives, prototypes, failures, and corrective actions.
Use the [entry template](entry_template.md) for new entries; keep rejected options and failed
tests.

## Entries

| Log ID / entry | Date / authors / reviewer | Lifecycle stage | Scope | Requirement / rule / interface IDs | Status / next action |
| --- | --- | --- | --- | --- | --- |
| [DL-T05-001](DL-T05-001_chassis_motion_software.md) | 2026-10-24 / TBD (T05 assignees) / TBD | Concept + software implementation | Mecanum drive carried over from 2025: encoder + gyro odometry, closed-loop moves, adaptive S-curve | T05-R1 to T05-R9; issue #6, PR #27, PR #28 | Open: confirm NovaPi sensor API, calibrate, run T05-R8/R9 |
| [DL-SYS-001](DL-SYS-001_design_decisions.md) | 2026-11-06 / TBD / TBD | Design (CAD v15 → v22), control, simulation, strategy | Register of every design decision (`DEC-M…`, `DEC-S…`, `DEC-X…`, `DEC-T…`) with rationale, rejected options and evidence | T01, T02, T05, T16, T17; KI-001 to KI-009 | Open decisions listed at the end of the entry |
| [entry_template.md](entry_template.md) | — | Template | Objective → requirements → alternatives → decision → prototype → test → results → corrective action | — | — |

## Entry workflow

1. Start with the objective, source-linked requirements, and alternatives.
2. Record the selection and its rationale before building or changing a prototype.
3. Add the prototype revision, the test procedure, and observed results.
4. Record problems, corrective actions, and the Keep / Modify / Reject decision.
5. Link evidence and update the affected design, requirements, interfaces, and verification records.

For a decision without a prototype, say why the prototype/test sections do not apply yet; do not
invent results. Link [test results](../test_results/README.md), [lessons](../lessons_learned/README.md),
and the [notebook index](../README.md).
