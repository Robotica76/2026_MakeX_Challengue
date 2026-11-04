# Scoring Strategy

Scoring from the rules guide V1.1 (`resources/rules/`, p.30-54). Simulated values come from the 2D
simulator (`simulation/analysis/simulate_match.py`), not from the robot.

| Opportunity | Source | Rule | Scoring condition / value | Capability | Simulated | Risk / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| Balls in the opponent fortress upper area | p.36, p.53 | Precision Throwing | projection completely inside at scoring time: 10 each | intake, tower, shooter | 18 of 30 shots stay in (match_2026.py) | deep shots bounce out; table top and X mark block paths across the centre |
| Bonus balls | p.30, p.36 | Bonus Battle | valid bonus cube in own exchange area at 30 s: X3-X12 extra balls in our resource area, that many balls score 20 | pull mode + gripper | X12 valid at 22.7 s | prop card changes the layout: the AI camera must find the X12 |
| Letter cubes | p.38-40 | Letter Cube Transfer | 30 each in a strategy channel, +50 per side with M-A-K-E from outside to inside | gripper reaching into the fortress | simulated (props.make_bonus, R26 ChannelMonitor); `letter_cube_reach.py`: **the v22 gripper reaches none** (the body runs 102+ mm into the fortress plate); with +150 mm reach to the right, K and E of our half from the south; M crosses into the partner half, A (230 mm inside, pin area behind) stays out of reach, so MAKE needs the partner or a deeper arm | R26: no robot part in a channel (−20, then −120) |
| Pins | p.13, p.40-42 | Pin Transfer | 10 on own floor out of the resource areas, 30 partly in the pin placement area | a mechanism reaching 760-1050 mm | simulated (props.pin_points): **0, the v22 robot cannot reach them** | the pins stand on the resource-area side shelves at 758.5 mm; the robot reaches 645 mm (body), 525 (intake head), 515 (gripper, carriage up): up to 120 points for our half need a new mechanism |
| Cones | p.43 | Cone Transfer | 20 each, hung on own cone post | gripper + carriage | simulated (props.thread_cone: the cone hangs only if lowered onto the post from above): **+40, both lower cones on red cone post 2** in the manual stage (manual_strategy.md) | needs the 430 mm elevator proposal: the v22 carriage (358 mm) is 57 mm short of lifting a gripped cone over the 405 mm post (`cone_post_reach.py`) |
| X mark | p.44-46 | X Clash | 30, colored face toward us | shooter (N3 aims at it) | simulated: 30 from the start (each colour faces its camp); a hit from our side turns it red (model, check on a real field) | shoot it only if the opponent turned it: 2 balls win back 30 |
| Team flag | p.47 | Team Flag Hanging | 50, final stage | flag system | not simulated | — |

## Prioritization decision

| Proposal | Comparison method / assumptions | Evidence | Compliance review | Decision |
| --- | --- | --- | --- | --- |
| X12 into exchange area 1 in the automatic stage, then ball cycles | Same scripted manual stage after each automatic strategy (`simulate_match.py --compare`) | bonus 300, props 130, balls 90, mixed 80 points (balls only, no opponent) | R06, R19, R23, collisions checked by the simulator | Selected (2026-10-31) |
