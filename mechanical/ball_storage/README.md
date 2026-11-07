# Ball Storage

> **Revision v22 (CAD only).** Parts 8.x (Basket and feed roller) of the [Storm Breaker v22 manual](../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf). Not built or measured yet.

## Purpose

Hold 6–8 balls next to the launcher and release them one at a time.

## Competition Capabilities

Ball storage between collection and shooting. Rule references are to the MakeX Challenge 2026 Storm Breaker rules used for the CAD (see [resources](../../resources/rules/README.md)); confirm against the official, current version.

## Requirements

Release only when the launcher is at speed (software interlock); no gate.

## Mechanical Interfaces

Receives from the elbow of the [tower](../feeder/README.md); feeds the [shooter](../shooter/README.md) at the launcher mouth (`x −163`, `y 4`, `z 389`).

## Electrical Interfaces

DC-25 feed motor (3:1).

## Software Interfaces

Roller runs only with the brushless motors at speed.

## Design

At 200 RPM direct (0.31 m/s) a waiting ball does not climb into the wheel (simulation), hence the 3:1 gear-up added in v20.

## Current Status

v22 CAD; feed simulated in 2D.

## Testing

See [prototypes](prototypes/README.md).

## Known Issues

- Two balls entering together not simulated.
- The 16T stands ~3 mm above the floor near the lane edge.

## Design decisions

| ID | Decision |
| --- | --- |
| [DEC-M05](../../docs/08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | Basket floor feeds the inverted launcher; the feed roller is the gate (no servo) |
| [DEC-M06](../../docs/08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | Feed roller 3:1 (direct 200 RPM fails in simulation) |

## Documentation map

| Folder | Content |
| --- | --- |
| [cad](cad/README.md) | 9 numbered STL, robot frame |
| [drawings](drawings/README.md) | Exploded, numbered sheets from the manual |
| [manufacturing](manufacturing/README.md) | BOM with process / material, assembly steps, checks |
| [prototypes](prototypes/README.md) | Simulation evidence and test plan |

## Related GitHub Issues

TBD: link actual design and validation issues when created.
