# Strategy

Strategy documents contain hypotheses to evaluate, not confirmed scoring rules or implemented routines.

| Document | Focus |
| --- | --- |
| [Scoring strategy](scoring_strategy.md) | Official-source-backed opportunity comparison |
| [Autonomous strategy](autonomous_strategy.md) | Initial state, candidate objectives, fallback questions |
| [Manual strategy](manual_strategy.md) | Driver workflow and task prioritization |
| [Alliance strategy](alliance_strategy.md) | Responsibilities and coordination constraints |

| Strategy proposal | Rule / requirement IDs | Owner / peer reviewer | Evidence / notebook link | Decision / revision |
| --- | --- | --- | --- | --- |
| Automatic stage: central balls first, then props from the central strip to our side; the X12 bonus cube into the exchange area ([autonomous strategy](autonomous_strategy.md)) | p.27–38, R06, R19, R26 | TBD (team) / TBD | Simulation, `simulation/field2d/test_match.py` | Implemented in simulation: 14 balls + valid X12 by 29.0 s |

Review [competition requirements](../01_requirements/competition_requirements.md) first. Revisit architecture when strategy changes introduce new needs, and record evaluations in the [notebook](../08_engineering_notebook/README.md) with [competition-context verification](../06_verification/competition_tests/README.md).
