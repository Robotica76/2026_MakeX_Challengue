# Known Issues

No observed issues are asserted by this starter. Add actual observations separately from risks or untested hypotheses.

| Issue ID | Observation / hypothesis label | Description / reproduction context | Severity / impact | Requirement / interface IDs | Configuration / evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KI-001 | Observation (CAD) | Footprint is 499.5 × 499.0 mm: 0.5 mm margin to the 500 × 500 mm limit; gripper jaw reaches `x = +250.0` | High: manufacturing tolerance or a bent part can fail inspection | T01-R1, T01-R2, T05-R1 (target ≤ 480 × 480) | [v22 CAD](../../mechanical/assemblies/full_robot/v22/README.md) | TBD | Open |
| KI-002 | Observation (CAD) | 13 DC/encoder motors used out of 13 allowed; no motor in reserve | Medium: no spare actuator for late changes | T02-R1, T02-R6 | [v22 CAD](../../mechanical/assemblies/full_robot/v22/README.md#actuators-from-part-names) | TBD | Open |
| KI-003 | Risk (CAD) | Power management module sits inside the carbon-fiber electronics box with a CF lid | Medium: carbon fiber is conductive (antenna) and hides the module from ID scanning | T17-R7 | `ELB_caja_paredes_CF1_ventiladas`, `ELB_caja_tapa_CF1_removible` | TBD | Open |
| KI-004 | Observation (CAD) | No team ID plate in the model | Low: needs a place on a light background, characters ≥ 3.5 cm | T01-R4 | [v22 CAD](../../mechanical/assemblies/full_robot/v22/README.md) | TBD | Open |
| KI-005 | Observation (CAD vs software) | Wheel rectangle is centered 79 mm behind the envelope center; a + b = 345 mm (0.603 cm/°). `chassis.py` uses 47 cm/90° = 0.522 cm/° from the 2025 robot; the 2D simulator places wheels at the footprint corners | Medium: open-loop turns (`USE_SENSORS = False`) about 13 % short; simulator turn geometry wrong | T05-R9 | [v22 drive geometry](../../mechanical/assemblies/full_robot/v22/README.md#measured-envelope-from-the-step-via-glb-mesh), [chassis.py](../../software/controls/drivetrain/chassis.py) | TBD | Corrected in code and simulator (CAD values); verify on robot |
| KI-006 | Observation (CAD vs software) | In v22 the gripper is on the right side (`+x`) and the shooter on the left (`−x`); the intake is at the front (`+y`). `chassis.py` fronts F1 (launcher) and F2 (gripper) assume both on the forward axis, as in 2025 | Medium: "gripper first" now means strafing, not driving forward | T20, T05 | [v22 frame](../../mechanical/assemblies/full_robot/v22/README.md#frame-and-units) | TBD | Corrected in code (fronts as angles); driver mapping to confirm (T20) |
| KI-007 | Gap | Robot mass cannot be computed exactly from the STEP (no material data); estimate 8.94 kg from mesh volumes, keyword densities and catalogue masses (intake 2.96 kg, chassis 1.47 kg, tower 1.45 kg) | Medium: T01-R3 (≤ 10 kg) likely met but only 0.26 kg under the 9.2 kg T02 budget | T01-R3, T02-R7 | [robot_mass.json](../../simulation/field3d/robot_mass.json), [mass_properties.py](../../tools/scripts/mass_properties.py) | TBD | Open (weigh parts) |

## Corrective action and closure

| Issue ID | Root-cause evidence | Corrective action / decision ID | Notebook link | Retest ID / result | Closure reviewer / date | Remaining risk |
| --- | --- | --- | --- | --- | --- | --- |
| KI-005 | Wheel centres measured in the v22 STEP | `CM_PER_TURN_DEGREE` = 0.603 cm/°, `ODOM_CENTER_OFFSET_CM` = 7.9; simulator `wheel_centers_mm` and least-squares kinematics | [DL-T05-001](../08_engineering_notebook/design_log/DL-T05-001_chassis_motion_software.md) | Simulator tests: offset-turn odometry within 0.5 cm (closed and open loop); robot test TBD | TBD | Real turn radius may differ (slip, build) |
| KI-006 | v22 layout: gripper `+x`, launcher `−x`, intake `+y` | Fronts `F_INTAKE`/`F_GRIPPER`/`F_LAUNCHER`/`F_REAR` as angles; default `F_INTAKE` | [Drivetrain motion control](../04_controls/drivetrain_motion_control.md) | Manual demo test: launcher front strafes left; robot test TBD | TBD | Driver button mapping still to agree (T20) |

Closure requires evidence against the affected acceptance criterion, not only a design change. Update the [interface matrix](interface_matrix.md), [compliance matrix](../01_requirements/rules_compliance_matrix.md), and [test results](../08_engineering_notebook/test_results/README.md) where affected.
