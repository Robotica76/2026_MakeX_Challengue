# Mechanical

Architecture and design workspace only. No mechanisms, CAD, dimensions, materials, or competition requirements are approved here yet.

## Integration hierarchy

Components → subsystems → assemblies → full robot. Component work lives in a subsystem's local `cad/`, or [common_parts](common_parts/README.md) when genuinely shared. Subsystem CAD stays local. Assemblies reference their constituent subsystem files rather than copying them. Full-robot CAD belongs only in [assemblies/full_robot](assemblies/full_robot/README.md).

## Subsystems

| Subsystem | Design question |
| --- | --- |
| [Chassis](chassis/README.md) | How will mobility, stability, and mounting support the selected mechanisms? |
| [Ball Intake](ball_intake/README.md) | How will authorized ball interactions be acquired reliably? |
| [Ball Storage](ball_storage/README.md) | How will balls be retained and organized? |
| [Feeder](feeder/README.md) | How will balls transfer between storage and shooter? |
| [Shooter](shooter/README.md) | Which release approach meets verified task needs? |
| [Gripper](gripper/README.md) | Should Pins, Cones, Letter Cubes, and Bonus Cubes use universal or dedicated manipulation? |
| [Gripper Elevation](gripper_elevation/README.md) | How will a selected manipulator be positioned? |
| [Flag System](flag_system/README.md) | What, if any, mechanism is justified by verified flag-related tasks? |
| [Common Parts](common_parts/README.md) | Which interfaces and components should be shared? |

See [assemblies](assemblies/README.md) for ball-system, manipulation-system, and full-robot integration.

## Workflow and evidence

Every subsystem contains `cad/`, `drawings/`, `prototypes/`, and `manufacturing/` READMEs describing intended artifacts. Their presence does not imply a finished design. Record alternatives, interface ownership, evidence, and unresolved decisions before promoting a design.

Requirements, game-element names, and capabilities are investigation topics until supported by a reviewed [official resource register](../resources/rules/README.md). Connect mechanical decisions to [electrical](../electrical/README.md), [simulation](../simulation/README.md), and future software interfaces without prescribing implementations. Track real issue references only when issues exist.
