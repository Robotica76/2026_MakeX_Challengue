# Game elements

Element data used by the design and the simulators (rules guide V1.1):

| Element | Data used | Where |
| --- | --- | --- |
| Balls | 70 mm, 10 per own resource area box + central table levels; mass not given (30 g assumed) | [`balls.py`](../../simulation/field2d/balls.py), ballistics |
| Pins | 290 mm, 16 on the resource-area shelves (760–1050 mm reach) | [`props.py`](../../simulation/field2d/props.py), [`pin_reach.py`](../../simulation/analysis/pin_reach.py) |
| Cones | Hung on own cone post (405 mm) | `props.py`, [`cone_post_reach.py`](../../simulation/analysis/cone_post_reach.py) |
| Letter cubes | 16, M-A-K-E | `props.py`, [`letter_cube_reach.py`](../../simulation/analysis/letter_cube_reach.py) |
| Bonus cubes | X3–X12, prop cards | `props.py`, [vision_reference](../../software/vision/vision_reference/README.md) |
| Team flag | ≥ 400 × 300 mm, pole < 10 × 10 mm | [`flag.py`](../../simulation/field2d/flag.py), [flag_system](../../mechanical/flag_system/README.md) |
