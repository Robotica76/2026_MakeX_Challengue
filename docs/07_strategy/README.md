# Strategy

Match plans and the simulations that rank them. Values are **simulation results** (2D simulator,
v22 robot model), not measured on a robot.

| Document | Focus |
| --- | --- |
| [Scoring strategy](scoring_strategy.md) | Every scoring opportunity, its rule, the robot capability and the simulated value |
| [Autonomous strategy](autonomous_strategy.md) | 30 s automatic stage: rules that shape it, the X12 plan, timing |
| [Manual strategy](manual_strategy.md) | 100 s manual stage and two-robot plan with cones |
| [Monte Carlo strategy](montecarlo_strategy.md) | Sampled-robot search of the automatic stage, every mission order, two and four robots, reinforcement learning |
| [Alliance strategy](alliance_strategy.md) | Partner coordination (template) |

## Current plan

| Item | Decision | Evidence |
| --- | --- | --- |
| Automatic stage | X12 into red exchange area 1, then deny X9 (`ORDER` 12); candidate 13 (X12 then lower table balls) | DEC-T01; [Monte Carlo](montecarlo_strategy.md) |
| Our half | Lower half of the red camp | DEC-T02 |
| X mark | Keep 2 balls, fire at ~277.8 s | DEC-T03 |
| Aim | At the fortress where it is (driver / assist) | DEC-S06 |

Figures: [simulation/analysis/reports](../../simulation/analysis/reports/README.md).
