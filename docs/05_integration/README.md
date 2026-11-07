# Integration

Interface agreements, integration plan and the issues found when subsystems meet.

| Document | Content |
| --- | --- |
| [Known issues](known_issues.md) | KI-001 … KI-010: footprint margin, motor reserve, power-module visibility, ID plate, drive geometry, fronts, mass, flag mast position, elevator travel, DC ports |
| [Interface matrix](interface_matrix.md) | Producer / consumer agreements |
| [Integration plan](integration_plan.md) | Order of integration and checks |

## Integration checks done in CAD (v22)

| Check | Result | Evidence |
| --- | --- | --- |
| Interference between all parts | No clashes except mounting contacts | [full_robot v22](../../mechanical/assemblies/full_robot/v22/README.md) |
| Central Resource Area table | 0 mm³ interference, face contact at `y = 93`, 1 mm to the roof edge | [analysis](../../mechanical/assemblies/full_robot/v22/analysis/) |
| Footprint / height | 499.5 × 499.0 × 642 mm | KI-001 |
| Mass | 9.88 kg (9.92 kg with the flag mast) | [DL-SYS-001](../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) |

Next integration step: wire the robot and confirm the port map assumed in
[`robot_config.json`](../../simulation/field2d/robot_config.json).
