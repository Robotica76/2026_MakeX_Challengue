# Engineering Notebook

Shared, dated evidence trail of requirements, design, prototypes, integration, verification and
strategy. It is written during the work, not at the end.

| Workspace | Purpose |
| --- | --- |
| [Design log](design_log/README.md) | Decisions, alternatives, prototypes, failures, corrective actions — including the [decision register DL-SYS-001](design_log/DL-SYS-001_design_decisions.md) |
| [Entry template](design_log/entry_template.md) | Reusable engineering lifecycle record |
| [Test results](test_results/README.md) | Measurements, procedure revisions, outcomes, retests (none yet; simulation evidence listed) |
| [Lessons learned](lessons_learned/README.md) | Evidence-backed improvements and follow-up |
| [Media](media/README.md) | Evidence index with provenance and usage permissions |
| [Legacy](legacy/README.md) | 2025 robot presentation |

## Shared index

| Log ID / date | Lifecycle stage | Authors / reviewer | Objective | Requirement / rule / interface IDs | Decision / test / issue IDs | Entry | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DL-T05-001 / 2026-10-24 | Concept + software implementation | TBD (T05 assignees) / TBD | Carry over 2025 mecanum drive with sensor odometry and smoothing | T05-R1 to T05-R9 | Issue #6, PR #27, PR #28 | [Entry](design_log/DL-T05-001_chassis_motion_software.md) | Confirm sensor API, calibrate, run T05-R8/R9 |
| DL-SYS-001 / 2026-11-06 | Design + control + simulation + strategy | TBD / TBD | Register every decision of robot v15 → v22 | T01, T02, T05, T16, T17 | DEC-M01…M13, DEC-S01…S06, DEC-X01…X02, DEC-T01…T03 | [Entry](design_log/DL-SYS-001_design_decisions.md) | Close the open decisions (KI-002, KI-003, KI-008, KI-009) |

## Recording conventions

- Create a record when a requirement changes, an alternative is evaluated, a prototype is revised, a test runs, or a strategy is reconsidered.
- Separate expectation from observation; record measurements with units, conditions and uncertainty.
- Keep failed tests and rejected designs; a correction names the original record, the change and the retest.
- Include date, authors, peer reviewer, configuration revision and stable IDs.
- Do not store copyrighted official documents or private media; reference authorized sources.

Cross-links: [requirements](../01_requirements/README.md), [architecture](../02_system_architecture/README.md), [design](../03_design/README.md), [controls](../04_controls/README.md), [integration](../05_integration/README.md), [verification](../06_verification/README.md), [strategy](../07_strategy/README.md).
