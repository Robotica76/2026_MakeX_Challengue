# Mechanical

Mechanical design of the Storm Breaker robot. Current revision: **v22** (CAD complete, 211 numbered parts, not built). Masses, clearances and mechanism behaviour come from CAD checks and simulations; they become approved values only after the tests in each subsystem's `prototypes/` pass.

Start here: [full robot v22](assemblies/full_robot/v22/README.md) · [assembly manual (PDF)](assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf) · [design decisions DL-SYS-001](../docs/08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md)

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

## Revision v22 · part numbering

The Storm Breaker v22 CAD is split into numbered subsystems. Every part has a number `<subsystem>.<part>` used in the
[assembly manual](assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf), in the STL file names
(`<subsystem>.<part>_<CAD name>.stl`), and in each subsystem's `manufacturing` BOM. Each folder keeps the same four
areas: `cad/v22` (numbered STL), `drawings/v22` (exploded, numbered sheet), `manufacturing` (BOM, process, assembly,
checks), `prototypes` (simulation evidence and test plan).

| No. | Subsystem (manual) | CAD prefixes | Folder | Parts |
| --- | --- | --- | --- | --- |
| 1 | Chassis and drive | `CH_` | [chassis](chassis/README.md) | 49 |
| 2 | Electronics box | `ELB_`, `ELEC_` | [chassis](chassis/README.md) | 10 |
| 3 | Ball tower (transfer to basket) | `TW_` | [feeder](feeder/README.md) | 21 |
| 4 | Ball intake and UR arm | `INT_` | [ball_intake](ball_intake/README.md) | 55 |
| 5 | Gripper elevator and structure | `MAS_`, `ELV_`, `RIG_separador`, `RIG_cuaderna` | [gripper_elevation](gripper_elevation/README.md) | 26 |
| 6 | Carriage and gripper | `CAR_`, `GR_`, `FLAG_receptor` | [gripper](gripper/README.md) | 18 |
| 7 | Shooter (inverted launcher) | `SH_`, `RIG_base`, `RIG_postes` | [shooter](shooter/README.md) | 18 |
| 8 | Basket and feed roller | `CN_` | [ball_storage](ball_storage/README.md) | 9 |
| 9 | Flag mast (Modification Stage) | `FLAG_` | [flag_system](flag_system/README.md) | 4 |
| 10 | Hardware | `HW_` | [common_parts](common_parts/README.md) | 1 |

Status: CAD only (211 parts); nothing has been built or measured.

## Key figures (v22 CAD)

| Item | Value |
| --- | --- |
| Envelope | 499.5 × 499.0 × 642 mm initial; 1062 mm with the flag mast, carriage up |
| Mass | 9.88 kg (9.92 kg with the flag mast) + ≈ 0.08 kg screws not modelled |
| Actuators | 13 / 13 DC + encoder motors, 2 / 2 brushless, 1 / 6 servos |
| Ball capacity | ~15 in the tower + 6–8 in the basket |
| Stability | Forward tip at 0.49 g empty, 0.41 g worst case |

Open issues: KI-001 (0.5 mm footprint margin), KI-002 (no motor reserve), KI-003 (power-module
visibility), KI-008 (flag mast position), KI-009 (elevator travel), KI-010 (DC ports) in
[known issues](../docs/05_integration/known_issues.md).
