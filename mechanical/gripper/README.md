# Gripper

## Purpose

Investigate acquisition, retention, and placement of candidate non-ball game elements.

## Competition Capabilities

Explicitly investigate **Pins, Cones, Letter Cubes, and Bonus Cubes**. These names identify study scope, not confirmed rules or capabilities; verify official terminology, geometry, permitted interactions, and task requirements through [game-element resources](../../resources/game_elements/README.md).

## Requirements

TBD for each element: sourced geometry, contact constraints, approach/placement conditions, retention needs, and success criteria. Do not infer common handling requirements.

## Mechanical Interfaces

TBD: attachment, loads, tool-change boundary if relevant, and pose reference with [gripper_elevation](../gripper_elevation/README.md).

## Electrical Interfaces

TBD per concept: actuators, element/retention sensing, wiring, and power needs with [electrical](../../electrical/README.md).

## Software Interfaces

TBD: element/task selection, acquire/release commands, retention feedback, elevation interlocks, and recovery states.

## Design

Perform a **universal versus dedicated manipulator trade study**; a final universal gripper is not presumed. Compare one shared tool, element-specific tools, and any justified hybrid/tool-change options.

| Investigation | Universal concept | Dedicated concept | Evidence needed |
| --- | --- | --- | --- |
| Pins | TBD | TBD | Verified geometry, contact and placement tests |
| Cones | TBD | TBD | Verified geometry, retention and release tests |
| Letter Cubes | TBD | TBD | Verified geometry, orientation and placement tests |
| Bonus Cubes | TBD | TBD | Verified geometry, retention and placement tests |

Compare task coverage, retention reliability, placement accuracy, mass/envelope implications, actuation/control complexity, changeover costs, and serviceability. All targets and scores remain TBD until sourced or measured. Keep models in [cad](cad/README.md); integrate references through [manipulation_system](../assemblies/manipulation_system/README.md).

## Current Status

Architecture and trade-study scaffold only; no manipulator concept selected or demonstrated.

## Testing

Plan separate acquisition, retention, orientation, and release trials for each verified element; compare universal and dedicated concepts under equivalent conditions.

## Known Issues

TBD: official element definitions, task constraints, tool coverage, and tool-change feasibility are unresolved.

## Related GitHub Issues

TBD: link actual element-verification, trade-study, and prototype-test issues when created.
