# Electrical architecture

Kit-based architecture of the v22 robot: **NovaPi** controller (4 encoder-motor ports M1–M4,
sensor ports, gyro / accelerometer inside), **power expansion / management board** (DC motor
ports DC1–DC8, brushless BL1–BL2), LiPo 3S 4200 mAh. Registers: [electrical_architecture.md](electrical_architecture.md),
[motor_allocation.md](motor_allocation.md), [servo_allocation.md](servo_allocation.md) (starter templates).

## Motor allocation (v22 CAD + port assumptions in `robot_config.json`)

| Port | Motor (rules catalogue) | Function | v22 part |
| --- | --- | --- | --- |
| M1 / M2 / M3 / M4 | 180 smart encoder × 4 | Drive FR / RR / RL / FL | 1.17–1.20 |
| DC1 | DC-37 200 RPM | Intake throat: R3 + R2 gear train | 4.6 |
| DC2 | DC-25 | Intake head lift (T8×16 lead screw, ~53 mm/s) | 4.16 |
| DC3 | DC-37 50 RPM | Gripper elevator carriage (90T GT2, 150 mm/s) | 5.1 |
| DC4 | DC-37 200 RPM | Tower belts (3:1) | 3.4 |
| DC5 | DC-25 | Feed roller (3:1 under the basket) | 8.4 |
| DC6 | DC-25 | Gripper jaw (+ closes) | 6.3 |
| DC7 | DC-25 | Intake head band roller (internal) | 4.18 |
| **none** | DC-25 | Lower roller LR (internal) | 4.17 |
| **none** | DC-25 | Elbow roller (internal) | 3.11 |
| BL1 (+ BL2?) | Brushless 2823/2824 × 2 + ESC | Shooter wheels | 7.9, 7.10 |
| servo | MS-12A × 1 | Shooter hood flap | 7.8 |

Totals vs rules T10: DC + encoder **13 / 13** (KI-002), brushless 2 / 2, servo 1 / 6.
**Nine** non-encoder DC motors vs **eight** DC ports ([KI-010](../../docs/05_integration/known_issues.md)): the
lower roller could share DC1 (always runs with the intake) and the elbow DC4 (always runs with the
tower) — check the board's current limit per port first.
