# 2026 MakeX Challenge — Storm Breaker

Student collaborative engineering documentation workspace. This repository structure records architecture, decisions, interfaces, and evidence; it does not implement robot functionality or establish competition rules.

All technical values, task interpretations, and operating permissions are **TBD until verified**. Do not copy copyrighted competition documents here: record official source references, revision, section, and a short student-authored interpretation instead.

## Engineering lifecycle

| Stage | Shared workspace | Required record |
| --- | --- | --- |
| Define | [Project definition](00_project_definition.md) | Objectives, scope, constraints, and success criteria |
| Understand | [Requirements](01_requirements/README.md) | Source-backed requirement and rule IDs |
| Architect | [System architecture](02_system_architecture/README.md) | Interfaces, assumptions, budgets, decision records |
| Design | [Subsystem design](03_design/README.md) | Alternatives, selected concept, prototype evidence |
| Control | [Controls](04_controls/README.md) | Mode ownership, transitions, safety questions |
| Integrate | [Integration](05_integration/README.md) | Interface agreements and issue tracking |
| Verify | [Verification](06_verification/README.md) | Requirement-linked procedures and measured results |
| Plan operation | [Strategy](07_strategy/README.md) | Rule-backed strategy hypotheses |
| Record throughout | [Engineering notebook](08_engineering_notebook/README.md) | Decisions, failures, corrective actions, evidence |

## Collaboration and traceability

Use stable IDs when adding records: `RULE-###`, `REQ-###`, `IF-###`, `DEC-###`, `TEST-###`, `ISSUE-###`, and `LOG-###`. These are local documentation IDs, not official rule numbers. Retain IDs when records change.

Trace each decision from official source → rule/requirement → subsystem/interface → notebook decision → verification procedure → result → corrective action. Link the relevant documents in both directions when records exist.

| Work item / ID | Student owner | Peer reviewer | Linked requirement | Notebook record | Status / next action |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD |

Changes should name an owner, include a peer review, and state whether an item is proposed, verified, rejected, or superseded. A blank or TBD record is not evidence of compliance.

## Intended mode sequence

`INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL → STOP`

This is a proposed documentation model, **not a confirmed official competition sequence**. Phase duration, start/end signals, permitted actions, physical modifications, and the meaning of FINAL require official verification before adoption. See [software architecture](02_system_architecture/software_architecture.md) and [stateflow](04_controls/stateflow/README.md).
