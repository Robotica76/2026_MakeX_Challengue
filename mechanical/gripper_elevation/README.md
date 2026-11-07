# Gripper Elevation

> **Revision v22 (CAD only).** Parts 5.x (Gripper elevator and structure) of the [Storm Breaker v22 manual](../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf). Not built or measured yet.

## Purpose

Raise and lower the gripper carriage 358 mm; also raises the flag mast after the Modification Stage.

## Competition Capabilities

Manipulator positioning; flag hanging height. Rule references are to the MakeX Challenge 2026 Storm Breaker rules used for the CAD (see [resources](../../resources/rules/README.md)); confirm against the official, current version.

## Requirements

Initial height ≤ 700 mm (robot 642 mm).

## Mechanical Interfaces

Carriage for the [gripper](../gripper/README.md); bulkhead shared with the [tower](../feeder/README.md); camera on the lid.

## Electrical Interfaces

DC-37 50 RPM, AI camera 2.0.

## Software Interfaces

Position presets; flag sequence (raise, lower, strafe).

## Design

Belt drive with 90T pulleys; ribs at z 150 / 300 / 440.

## Current Status

v22 CAD.

## Testing

See [prototypes](prototypes/README.md).

## Known Issues

- Elevator top support is 1 mm from the Central Area roof edge when the robot face is against the table; trim 10–15 mm suggested.

## Design decisions

| ID | Decision |
| --- | --- |
| [DEC-M12](../../docs/08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | Raises the flag mast after the Modification Stage; guide notch in the lid |

## Documentation map

| Folder | Content |
| --- | --- |
| [cad](cad/README.md) | 26 numbered STL, robot frame |
| [drawings](drawings/README.md) | Exploded, numbered sheets from the manual |
| [manufacturing](manufacturing/README.md) | BOM with process / material, assembly steps, checks |
| [prototypes](prototypes/README.md) | Simulation evidence and test plan |

## Related GitHub Issues

TBD: link actual design and validation issues when created.
