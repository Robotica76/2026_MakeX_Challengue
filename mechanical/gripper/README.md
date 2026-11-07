# Gripper

> **Revision v22 (CAD only).** Parts 6.x (Carriage and gripper) of the [Storm Breaker v22 manual](../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf). Not built or measured yet.

## Purpose

Pick and place pins and other non-ball elements on the right side of the robot.

## Competition Capabilities

Pins, Cones, Letter Cubes, Bonus Cubes are under study. Rule references are to the MakeX Challenge 2026 Storm Breaker rules used for the CAD (see [resources](../../resources/rules/README.md)); confirm against the official, current version.

## Requirements

Inside the 500 mm footprint (jaw tip at x = +250).

## Mechanical Interfaces

On the [gripper elevator](../gripper_elevation/README.md) carriage; holds the [flag mast](../flag_system/README.md) receptor.

## Electrical Interfaces

DC-25 jaw motor, distance sensor.

## Software Interfaces

Open / close commands; distance feedback.

## Design

Single lead-screw jaw with V pads (v15 design, unchanged in v22).

## Current Status

v22 CAD.

## Testing

See [prototypes](prototypes/README.md).

## Known Issues

- Universal vs dedicated tool trade study still open (see the original study table in git history).

## Documentation map

| Folder | Content |
| --- | --- |
| [cad](cad/README.md) | 18 numbered STL, robot frame |
| [drawings](drawings/README.md) | Exploded, numbered sheets from the manual |
| [manufacturing](manufacturing/README.md) | BOM with process / material, assembly steps, checks |
| [prototypes](prototypes/README.md) | Simulation evidence and test plan |

## Related GitHub Issues

TBD: link actual design and validation issues when created.
