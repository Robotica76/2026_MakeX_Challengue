# Known Issues

No observed issues are asserted by this starter. Add actual observations separately from risks or untested hypotheses.

| Issue ID | Observation / hypothesis label | Description / reproduction context | Severity / impact | Requirement / interface IDs | Configuration / evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KI-001 | Observation (CAD) | Footprint is 499.5 × 499.0 mm: 0.5 mm margin to the 500 × 500 mm limit; gripper jaw reaches `x = +250.0` | High: manufacturing tolerance or a bent part can fail inspection | T01-R1, T01-R2, T05-R1 (target ≤ 480 × 480) | [v22 CAD](../../mechanical/assemblies/full_robot/v22/README.md) | TBD | Open |
| KI-002 | Observation (CAD) | 13 DC/encoder motors used out of 13 allowed; no motor in reserve | Medium: no spare actuator for late changes | T02-R1, T02-R6 | [v22 CAD](../../mechanical/assemblies/full_robot/v22/README.md#actuators-from-part-names) | TBD | Open |
| KI-003 | Risk (CAD) | Power management module sits inside the carbon-fiber electronics box with a CF lid | Medium: carbon fiber is conductive (antenna) and hides the module from ID scanning | T17-R7 | `ELB_caja_paredes_CF1_ventiladas`, `ELB_caja_tapa_CF1_removible` | TBD | Open |
| KI-004 | Observation (CAD) | No team ID plate in the model | Low: needs a place on a light background, characters ≥ 3.5 cm | T01-R4 | [v22 CAD](../../mechanical/assemblies/full_robot/v22/README.md) | TBD | Open |
| KI-005 | Observation (CAD vs software) | Wheel rectangle is centered 79 mm behind the envelope center; a + b = 345 mm (0.603 cm/°). `chassis.py` uses 47 cm/90° = 0.522 cm/° from the 2025 robot; the 2D simulator places wheels at the footprint corners | Medium: open-loop turns (`USE_SENSORS = False`) about 13 % short; simulator turn geometry wrong | T05-R9 | [v22 drive geometry](../../mechanical/assemblies/full_robot/v22/README.md#measured-envelope-from-the-step-via-glb-mesh), [chassis.py](../../software/controls/drivetrain/chassis.py) | TBD | Open |
| KI-006 | Observation (CAD vs software) | In v22 the gripper is on the right side (`+x`) and the shooter on the left (`−x`); the intake is at the front (`+y`). `chassis.py` fronts F1 (launcher) and F2 (gripper) assume both on the forward axis, as in 2025 | Medium: "gripper first" now means strafing, not driving forward | T20, T05 | [v22 frame](../../mechanical/assemblies/full_robot/v22/README.md#frame-and-units) | TBD | Open |
| KI-007 | Gap | Robot mass cannot be computed from the STEP (no material data) | Medium: T01-R3 (≤ 10 kg) and the T02 budget unverified | T01-R3, T02-R7 | — | TBD | Open |

## Corrective action and closure

| Issue ID | Root-cause evidence | Corrective action / decision ID | Notebook link | Retest ID / result | Closure reviewer / date | Remaining risk |
| --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Closure requires evidence against the affected acceptance criterion, not only a design change. Update the [interface matrix](interface_matrix.md), [compliance matrix](../01_requirements/rules_compliance_matrix.md), and [test results](../08_engineering_notebook/test_results/README.md) where affected.
