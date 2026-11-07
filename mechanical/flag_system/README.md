# Flag System

> **Revision v22 (CAD only).** Parts 9.x (Flag mast (Modification Stage)) of the [Storm Breaker v22 manual](../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf). Not built or measured yet.

## Purpose

Carry the team flag and hang it on the field flag bar in the Final Stage.

## Competition Capabilities

Flag hanging, 50 points per flag. Rule references are to the MakeX Challenge 2026 Storm Breaker rules used for the CAD (see [resources](../../resources/rules/README.md)); confirm against the official, current version.

## Requirements

- Flag ≥ 400 × 300 mm; optional rigid pole < 10 × 10 mm; suspension ≤ 400 × 10 × 10 (T17). Flag mass excluded, mast mass included (T02).
- Field bar: horizontal aluminium bar 160 mm long at ≈ 950–965 mm.
- No hook-shaped parts that can catch other robots (T08 (5)): the bands close the C.

## Mechanical Interfaces

Receptor 6.17 on the gripper mounting block; guide notch in the elevator lid.

## Electrical Interfaces

None (uses the gripper elevator).

## Software Interfaces

Flag sequence: raise, hook, lower, strafe −x.

## Design

Mast 31.6 g (tube 18.9 g, head 10.9 g, pin 1 g, bands 0.9 g).

## Current Status

v22 CAD.

## Testing

See [prototypes](prototypes/README.md).

## Known Issues

- Bar direction relative to the pin table is not dimensioned in the rules; the head can be rotated 90° in the receptor.
- Band stiffness must let the pole slide out without dragging the flag off the bar.

## Documentation map

| Folder | Content |
| --- | --- |
| [cad](cad/README.md) | 4 numbered STL, robot frame |
| [drawings](drawings/README.md) | Exploded, numbered sheets from the manual |
| [manufacturing](manufacturing/README.md) | BOM with process / material, assembly steps, checks |
| [prototypes](prototypes/README.md) | Simulation evidence and test plan |

## Related GitHub Issues

TBD: link actual design and validation issues when created.
