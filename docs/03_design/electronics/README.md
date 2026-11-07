# Electronics Design Study

Control, power and sensing for the v22 robot. Selected arrangement is the MakeX kit: NovaPi
controller, power management/expansion board, LiPo 3S 11.1 V 4200 mAh (rules T11, T14).
Packaging: structural CF box on the rear rails ([DEC-M10](../../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md)). Electrical registers:
[electrical](../../../electrical/README.md).

| Function | Component (v22 CAD) | Rule | Interface | Mounting | Decision |
| --- | --- | --- | --- | --- | --- |
| Control | NovaPi with case (`ELEC_NovaPi_con_case`, 2.2) | T10 | Encoder motors M1–M4, gamepad (Bluetooth), sensors | Electronics box, back row | DEC-M10 |
| Power distribution | Power expansion / management module (2.3) | T17-R7 (visible, antenna away from metal) | DC1–DC8, BL1–BL2 ports | Electronics box | **At risk**: CF lid ([KI-003](../../05_integration/known_issues.md)) |
| Battery | LiPo 3S 4200 mAh, ~330 g (2.1) | T17-R1 | — | Box, 2 Velcro straps | — |
| Actuation | 13 DC/encoder motors, 2 brushless + ESC, 1 servo | T10 | [motor allocation](../../../electrical/architecture/motor_allocation.md) | Subsystems | 13/13 used ([KI-002](../../05_integration/known_issues.md)) |
| Sensing | AI camera 2.0, ranging sensors (gripper, tower S2), gyro/accelerometer in the NovaPi | T10 | [sensor register](../../../electrical/sensors/sensor_register.md) | Elevator lid, gripper, tower | — |

## Open items

- Port assignment is an assumption in `simulation/field2d/robot_config.json` until wiring is done.
- Polycarbonate lid or window for the power module (KI-003).
- Cable mass (0.15 kg estimated) and routing through the box grommets.
