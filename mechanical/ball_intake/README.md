# Ball Intake

> **Revision v22 (CAD only).** Parts 4.x (Ball intake and UR arm) of the [Storm Breaker v22 manual](../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf). Not built or measured yet.

## Purpose

Acquire balls from the floor and from both levels of the Central Resource Area and hand them to the 3-ball-wide tower; handle cones with the UR arm.

## Competition Capabilities

Ball collection from floor and shelves; cone interaction. Rule references are to the MakeX Challenge 2026 Storm Breaker rules used for the CAD (see [resources](../../resources/rules/README.md)); confirm against the official, current version.

## Requirements

- Robot face against the Central Resource Area at `y = 93`; nothing fixed beyond `y = 93` below `z = 42`.
- UR heights: 95 (floor), 128 (lower shelf), 325 (upper shelf), 468 (cone).
- Hand-off width = tower width (3 balls, 227 mm internal).

## Mechanical Interfaces

Feeds the [feeder tower](../feeder/README.md) at its lower window; side plates on the chassis spacers; left plate trimmed above z 278 for the [shooter](../shooter/README.md).

## Electrical Interfaces

DC-37 (R3 + R2 train), DC-25 lower roller, DC-25 UR lift, DC-25 UR band rotation: 4 of the 13 DC-motor slots.

## Software Interfaces

Run intake with the tower; UR position presets; reverse for jam clearing.

## Design

R2 changed to a straight roller in v19 (no longer needs to centre: the tower is 3 balls wide). Measured clearance to the Central Resource Area: 0 mm contact at the face (stop), 23–52 mm inside the table, 26.5 mm to the posts.

## Current Status

v22 CAD; simulated in 2D only.

## Testing

See [prototypes](prototypes/README.md).

## Known Issues

- Multi-ball behaviour not simulated.
- The UR lift motor sits high (z ≈ 500); moving it down was not possible (front wheel motor and lead-screw nut).

## Documentation map

| Folder | Content |
| --- | --- |
| [cad](cad/README.md) | 55 numbered STL, robot frame |
| [drawings](drawings/README.md) | Exploded, numbered sheets from the manual |
| [manufacturing](manufacturing/README.md) | BOM with process / material, assembly steps, checks |
| [prototypes](prototypes/README.md) | Simulation evidence and test plan |

## Related GitHub Issues

TBD: link actual design and validation issues when created.
