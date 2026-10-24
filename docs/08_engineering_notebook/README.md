# Engineering Notebook

Maintain a shared evidence trail throughout requirements, architecture, design, prototypes, integration, verification, and strategy. The notebook is not an end-of-project report.

| Workspace | Purpose |
| --- | --- |
| [Design log](design_log/README.md) | Decisions, alternatives, prototypes, failures, corrective actions |
| [Entry template](design_log/entry_template.md) | Reusable engineering lifecycle record |
| [Test results](test_results/README.md) | Measurements, procedure revisions, outcomes, retests |
| [Lessons learned](lessons_learned/README.md) | Evidence-backed improvements and follow-up |
| [Media](media/README.md) | Evidence index with provenance and usage permissions |

## Shared index

| Log ID / date | Lifecycle stage | Student authors / reviewer | Objective | Requirement / rule / interface IDs | Decision / test / issue IDs | Entry / evidence link | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DL-T05-001 / 2026-10-24 | Concept + software implementation | TBD (T05 assignees) / TBD | Carry over 2025 mecanum drive with sensor odometry and smoothing | T05-R1 to T05-R9 | Issue #6, PR #27, PR #28 | [Entry](design_log/DL-T05-001_chassis_motion_software.md) | Confirm sensor API, calibrate, run T05-R8/R9 |

## Recording conventions

- Create a record when a requirement changes, an alternative is evaluated, a prototype is revised, a test runs, or a strategy is reconsidered.
- Separate expectation from observation; record measurements with units, conditions, and uncertainty.
- Retain failed tests and rejected designs. Corrections should identify the original record, change, and retest.
- Include date, authors, peer reviewer, configuration revision, and stable traceability IDs.
- Link evidence with relative Markdown links when it is stored in this documentation tree.
- Do not store copyrighted official documents or unapproved/private media; reference authorized sources instead.

Cross-link entries to [requirements](../01_requirements/README.md), [architecture](../02_system_architecture/README.md), [design](../03_design/README.md), [controls](../04_controls/README.md), [integration](../05_integration/README.md), [verification](../06_verification/README.md), and [strategy](../07_strategy/README.md).
