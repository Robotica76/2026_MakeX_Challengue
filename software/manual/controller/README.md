# Controller

Makeblock Bluetooth gamepad, read with `mbuild.gamepad.get_joystick("Lx" | "Ly" | "Rx" | "Ry")`
(−100…100) and `is_key_pressed(name)`. Sticks are scaled and dead-banded in
`drive_joystick_N()` / `chassis.joystick_drive()`, with acceleration limits and gyro heading hold.
In simulation: the emulated gamepad window ([`gamepad.py`](../../../simulation/field2d/gamepad.py)) and
the scripted driver ([`ai_driver.py`](../../../simulation/control/ai_driver.py)).
