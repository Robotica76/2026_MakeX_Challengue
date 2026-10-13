# Mechanical Assemblies

Integration hierarchy: component → subsystem → assembly → full robot.

| Assembly | Integration scope |
| --- | --- |
| [Ball System](ball_system/README.md) | Intake, storage, feeder, and shooter references |
| [Manipulation System](manipulation_system/README.md) | Gripper and elevation references; evaluate flag-system involvement only if justified |
| [Full Robot](full_robot/README.md) | Chassis and selected mechanism assemblies, with electrical packaging interfaces |

Subsystem CAD remains in each subsystem's `cad/`; shared component CAD remains in [common_parts](../common_parts/README.md). Future assembly artifacts should record source paths/revisions, transforms, interface owners, and unresolved conflicts rather than duplicate constituent CAD. Full-robot CAD belongs only in `full_robot/`.

TBD: integration owners, interface register, review gates, and acceptance evidence. No integrated assembly exists yet.
