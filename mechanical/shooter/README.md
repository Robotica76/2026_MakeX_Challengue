# Shooter

> **Revision v22 (CAD only).** Parts 7.x (Shooter (inverted launcher)) of the [Storm Breaker v22 manual](../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf). Not built or measured yet.

## Purpose

Fire balls toward −x into the top of the opponent's Mobile Fortress.

## Competition Capabilities

Ball scoring. Rule references are to the MakeX Challenge 2026 Storm Breaker rules used for the CAD (see [resources](../../resources/rules/README.md)); confirm against the official, current version.

## Requirements

Fixed launcher (no turret), all parts below z 543 (Central Area roof), brushless 2/2, servos 1/6.

## Mechanical Interfaces

Fed by the [basket](../ball_storage/README.md); base on the left rail posts; left of the [tower](../feeder/README.md).

## Electrical Interfaces

2 brushless motors + 2 ESCs, 1 servo MS-12A.

## Software Interfaces

Wheel-speed setpoint from a distance table; feed interlock.

## Design

Wheel speed for a 30 g ball: 8.2–9.6 m/s at 1 m, 10.7–11.9 m/s at 2 m, 12.8–14.0 m/s at 3 m (44°).

## Current Status

v22 CAD; simulated (2D contact + ballistics).

## Testing

See [prototypes](prototypes/README.md).

## Known Issues

- Ball mass not in the rules (30 g assumed); spin (Magnus) not modelled.
- Brushless top speed on the D45 wheel unverified (needs ~14–15 m/s for 3 m).

## Documentation map

| Folder | Content |
| --- | --- |
| [cad](cad/README.md) | 18 numbered STL, robot frame |
| [drawings](drawings/README.md) | Exploded, numbered sheets from the manual |
| [manufacturing](manufacturing/README.md) | BOM with process / material, assembly steps, checks |
| [prototypes](prototypes/README.md) | Simulation evidence and test plan |

## Related GitHub Issues

TBD: link actual design and validation issues when created.
