# Scoring Strategy

Scoring from the rules guide V1.1 (`resources/rules/`, p.30-54). Simulated values come from the 2D
simulator (`simulation/analysis/simulate_match.py`), not from the robot.

| Opportunity | Source | Rule | Scoring condition / value | Capability | Simulated | Risk / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| Balls in the opponent fortress upper area | p.36, p.53 | Precision Throwing | projection completely inside at scoring time: 10 each | intake, tower, shooter | 18 of 30 shots stay in (match_2026.py) | deep shots bounce out; table top and X mark block paths across the centre |
| Bonus balls | p.30, p.36 | Bonus Battle | valid bonus cube in own exchange area at 30 s: X3-X12 extra balls in our resource area, that many balls score 20 | pull mode + gripper | X12 valid at 22.7 s | prop card changes the layout: the AI camera must find the X12 |
| Letter cubes | p.38-40 | Letter Cube Transfer | 30 each in a strategy channel, +50 per MAKE side | gripper | not simulated | R26: no robot part in a channel |
| Pins | p.44-45 | Pin Transfer | 10 on own side touching the map, 30 in the pin placement area | TBD | not simulated | — |
| Cones | p.43 | Cone Transfer | 20 each, hung on own cone post | gripper + carriage | not simulated | carriage max 358 mm: lifting a cone over the 405 mm post is not possible in the model |
| X mark | p.46 | X Clash | 30, colored face toward us | shooter | not simulated | balls aimed at the fortress across the centre hit it |
| Team flag | p.47 | Team Flag Hanging | 50, final stage | flag system | not simulated | — |

## Prioritization decision

| Proposal | Comparison method / assumptions | Evidence | Compliance review | Decision |
| --- | --- | --- | --- | --- |
| X12 into exchange area 1 in the automatic stage, then ball cycles | Same scripted manual stage after each automatic strategy (`simulate_match.py --compare`) | bonus 300, props 130, balls 90, mixed 80 points (balls only, no opponent) | R06, R19, R23, collisions checked by the simulator | Selected (2026-10-31) |
