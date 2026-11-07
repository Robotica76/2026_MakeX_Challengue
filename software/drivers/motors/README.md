# Motor drivers

| API | Used for | Notes |
| --- | --- | --- |
| `mbuild.encoder_motor.encoder_motor_class("M1"…"M4", "INDEX1")` | Drive wheels (M1 FR, M2 RR, M3 RL, M4 FL) | `set_speed(rpm)`, `move(deg, rpm)`, `get_value("angle")` (encoder) |
| `mbuild.power_expand_board.set_power(port, pct)`, `.stop(port)` | DC1–DC8 mechanisms, BL1 shooter | Open loop, ±100 % |

Unverified: the exact Python name of the encoder angle read (`get_value("angle")`) — export a
block project from mBlock to confirm (see `SENSORS` in
[`mblock_project.py`](../../../simulation/field2d/mblock_project.py)).
