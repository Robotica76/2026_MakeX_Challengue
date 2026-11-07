# Feeder

> **Revision v22 (CAD only).** Parts 3.x (Ball tower (transfer to basket)) of the [Storm Breaker v22 manual](../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf). Not built or measured yet.

## Purpose

Lift balls from the intake and store them (≈ 15 when stopped), then pass them over the elbow into the basket in front of the tower.

## Competition Capabilities

Ball transfer and storage. Rule references are to the MakeX Challenge 2026 Storm Breaker rules used for the CAD (see [resources](../../resources/rules/README.md)); confirm against the official, current version.

## Requirements

3 balls wide (227 mm internal), top at z = 430 so nothing violates the Central Resource Area roof (z 543 at y > −67).

## Mechanical Interfaces

Inlet from the [intake](../ball_intake/README.md); outlet into the [basket](../ball_storage/README.md); right plate on the elevator bulkhead ([gripper_elevation](../gripper_elevation/README.md)).

## Electrical Interfaces

DC-37 (belts, 3:1 up) and DC-25 inside the elbow roller; S2 entry sensor (ranging sensor).

## Software Interfaces

Runs with the intake; S2 counts balls in.

## Design

Tilted 15°, length 352 mm, belts at 0.94 m/s. Elbow roller r20 at 51 mm from the cover axis, cover R86. R2 core passes through a D34 clearance in both plates (fixed in v20).

## Current Status

v22 CAD; elbow and lift simulated in 2D.

## Testing

See [prototypes](prototypes/README.md).

## Known Issues

- The elbow motor could be removed with a transmission from the belts (frees a motor slot) but gears / belt clash with the launcher or the ball path; kept internal.

## Design decisions

| ID | Decision |
| --- | --- |
| [DEC-M03](../../docs/08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | Tower 3 balls wide, 15°, top at z 430 (roof limit z 543) |
| [DEC-M04](../../docs/08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | Elbow roller + concentric cover (rejected: single top roller) |
| [DEC-M07](../../docs/08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | Elbow keeps its internal DC-25 (transmission from the belts clashes) |

## Documentation map

| Folder | Content |
| --- | --- |
| [cad](cad/README.md) | 21 numbered STL, robot frame |
| [drawings](drawings/README.md) | Exploded, numbered sheets from the manual |
| [manufacturing](manufacturing/README.md) | BOM with process / material, assembly steps, checks |
| [prototypes](prototypes/README.md) | Simulation evidence and test plan |

## Related GitHub Issues

TBD: link actual design and validation issues when created.
