# Chassis

> **Revision v22 (CAD only).** Parts 1.x (Chassis and drive), 2.x (Electronics box) of the [Storm Breaker v22 manual](../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf). Not built or measured yet.

## Purpose

Mobile base for the whole robot: four mecanum wheels, the rails that carry every other subsystem, and (since v21) a structural electronics box at the rear.

## Competition Capabilities

Omnidirectional driving (strafing is used to place the flag and to align on the resource shelves). Rule references are to the MakeX Challenge 2026 Storm Breaker rules used for the CAD (see [resources](../../resources/rules/README.md)); confirm against the official, current version.

## Requirements

- Footprint 500 × 500 mm and initial height ≤ 700 mm; mass ≤ 10 kg at any time (flag excluded).
- Front wheels cannot pass `y = +45`: with the robot face against the Central Resource Area table (y = 93), the lower shelf occupies the space ahead of the wheels.
- Electronics enclosed and protected; battery LiPo 3S 11.1 V 4200 mAh as required by the rules.

## Mechanical Interfaces

- Rails `x = ±175…199`, top at `z = 69`; three crossbars `y = −164…−18`, top at `z = 61` (tower plates and intake stand on them).
- Electronics box `x −197…136`, `y −249…−178`, `z 72…112`, floor bolted to both rails (acts as an extra rear crossmember).
- Track × wheelbase 442.5 × 248 mm; wheel centres `z = 40`.

## Electrical Interfaces

4 × 180 smart encoder motors (4 of the 13 DC-motor slots). Box holds the battery (≈330 g), NovaPi with case, power/expansion module, drivers + Bluetooth; grommets on the front wall (motors, sensors) and left wall (launcher, ESCs). Cable mass is estimated at 0.15 kg, not modelled.

## Software Interfaces

Mecanum kinematics; ramp limits from the stability study: braking ≤ 0.35 g, avoid frontal impacts above ≈ 0.85 m/s.

## Design

Mass 9.88 kg (CAD, robot) with CG at `y ≈ −43`, `z ≈ 181` mm. Forward tip limit is the critical one: 0.49 g empty, 0.41 g with gripper up + pin + balls. Moving motors was studied and rejected (≈ +0.03 g for a large redesign); the limit comes from the front-wheel position.

## Current Status

v22 CAD complete and clash-checked against the rest of the robot. Not built.

## Testing

See [prototypes](prototypes/README.md): tip angle, braking, impact, mass/CG.

## Known Issues

- Mass margin ≈ 0.12 kg, and ~80 screws are not modelled yet (≈ 80 g).
- Electronics dimensions (NovaPi, power module) are approximations; the box back row is 328 mm of equipment in 330 mm.
- 3 mm shims are needed because the rear motor M4 heads stand to `z = 72`.

## Documentation map

| Folder | Content |
| --- | --- |
| [cad](cad/README.md) | 59 numbered STL, robot frame |
| [drawings](drawings/README.md) | Exploded, numbered sheets from the manual |
| [manufacturing](manufacturing/README.md) | BOM with process / material, assembly steps, checks |
| [prototypes](prototypes/README.md) | Simulation evidence and test plan |

## Related GitHub Issues

TBD: link actual design and validation issues when created.
