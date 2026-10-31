# Rules Compliance Matrix

Compliance remains unverified until the official source and relevant evidence have been reviewed. Local IDs do not imply official rule numbering.

| Local rule ID | Official source + revision + section | Student-authored interpretation | Robot requirement ID | Design / interface link | Verification ID / procedure link | Result / evidence link | Reviewer | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01-R1 | MakeX 2026 rules T01, p. 54–55 (revision TBD), via issue #11 | ≤ 500 × 500 × 700 mm before the Modification Stage | T05-R1 | [v22 CAD](../../mechanical/assemblies/full_robot/v22/README.md) | Cardboard template (issue #11 step 3) | CAD: 499.5 × 499.0 × 642.0 mm, 0.5 mm margin ([KI-001](../05_integration/known_issues.md)) | TBD | Unverified (CAD check only) |
| T01-R2 | Rules T01, p. 55, via issue #11 | ≤ 500 × 500 mm footprint after modification; height free | T16-R5 | [v22 CAD](../../mechanical/assemblies/full_robot/v22/README.md) | Template | CAD: 499.5 × 499.0 mm with mast and flag; height 1128 mm | TBD | Unverified (CAD check only) |
| T01-R3 | Rules T02, p. 55, via issue #11 | ≤ 10 kg including battery, excluding flag | T02-R7 | — | Scale ≥ 15 kg | Not computable from STEP ([KI-007](../05_integration/known_issues.md)) | TBD | Unverified |
| T01-R4 | Rules T03, p. 55; Appendix 3, via issue #11 | Team ID characters > 3.5 cm on a light background | — | — | Inspection | No ID plate in CAD ([KI-004](../05_integration/known_issues.md)) | TBD | Unverified (missing) |
| T02-R1 | Rules T10, p. 57, via issue #12 | ≤ 13 DC or encoder motors | — | [v22 actuators](../../mechanical/assemblies/full_robot/v22/README.md#actuators-from-part-names) | Inspection | CAD: 13 (4 encoder, 6 DC25, 3 DC37) | TBD | Unverified (CAD check only) |
| T02-R2 | Rules T10, p. 57, via issue #12 | ≤ 6 MS-12A servos | — | [v22 actuators](../../mechanical/assemblies/full_robot/v22/README.md#actuators-from-part-names) | Inspection | CAD: 1 | TBD | Unverified (CAD check only) |
| T02-R3 | Rules T10, p. 57, via issue #12 | ≤ 2 brushless 2823/2824 | — | [v22 actuators](../../mechanical/assemblies/full_robot/v22/README.md#actuators-from-part-names) | Inspection | CAD: 2; model number not in CAD | TBD | Unverified (CAD check only) |
| T02-R6 | Team design rule, issue #12 | ≥ 1 motor and ≥ 1 servo unassigned | — | [v22 actuators](../../mechanical/assemblies/full_robot/v22/README.md#actuators-from-part-names) | Analysis | CAD: 0 motors in reserve ([KI-002](../05_integration/known_issues.md)) | TBD | Not met in CAD |
| T17-R1 | Rules T11, T14, p. 58, via issue #21 | One LiPo 3S 11.1 V 4200 mAh, 25–30C | — | [v22 CAD](../../mechanical/assemblies/full_robot/v22/README.md) | Inspection | CAD: `ELEC_bateria_LiPo_3S_4200mAh`; C rating TBD | TBD | Unverified (CAD check only) |
| T17-R7 | Appendix 6, p. 96–97, via issue #21 | Power module fixed, visible, antenna away from metal | — | [v22 CAD](../../mechanical/assemblies/full_robot/v22/README.md) | Inspection | CAD: inside CF box with CF lid ([KI-003](../05_integration/known_issues.md)) | TBD | At risk in CAD |

## Change impact

| Source change | Affected rule / requirement IDs | Affected design / strategy | Retest needed | Owner | Notebook decision |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD |

Record noncompliance in [known issues](../05_integration/known_issues.md). Link corrective actions to the [verification plan](../06_verification/verification_plan.md) and [design log](../08_engineering_notebook/design_log/entry_template.md). Do not mark “compliant” based only on an intended design.
