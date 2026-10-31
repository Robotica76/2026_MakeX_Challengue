# Storm Breaker v22 · Full robot CAD

Full-robot CAD revision v22 (2026-10-26). v22 = v21 + removable flag mast,
installed during the Modification Stage. Generated with CadQuery / Open CASCADE 7.9.

**Status:** CAD only. No prototype has been built or measured. Every result below
is a check against the CAD model, not a verification of the physical robot.

## Files

| Path | Content | Notes |
| --- | --- | --- |
| [`cad/Robot_StormBreaker_v22_inicial.step.zip`](cad/Robot_StormBreaker_v22_inicial.step.zip) | Robot as it enters the field: carriage down, mast receptor only, no reference objects | STEP 121 MB zipped to 20 MB (GitHub limit is 100 MB per file); 207 named parts |
| [`cad/Robot_StormBreaker_v22_con_mastil_y_bandera_carro_arriba.step.zip`](cad/Robot_StormBreaker_v22_con_mastil_y_bandera_carro_arriba.step.zip) | After the Modification Stage: mast + flag installed, carriage up (zc = 386 mm), reference balls | 231 parts (adds 4 `FLAG_` mast parts and 24 `REF_` objects) |
| [`cad/Robot_StormBreaker_v22_inicial_stl.zip`](cad/Robot_StormBreaker_v22_inicial_stl.zip) | Initial robot as one STL (tolerance 0.2 mm) | For quick viewing; use the STEP for engineering |
| [`source/`](source/) | CadQuery scripts: `robot_v22.py` (model), `export_v22.py`, `clash_v22.py` (interference check), `plano_mastil_v22.py` (mast drawing) | **Not runnable from this repo:** they import `robot_v21`, `r19`, `r20`, which were not provided, and use absolute paths (`/home/claude`) |
| [`renders/`](renders/) | Isometric, right side, and top views, with the carriage down (`mastil_bajo`) and up | |
| [Flag mast STL](../../../flag_system/cad/README.md#v22--removable-flag-mast) | Printable mast parts, kept in the flag subsystem | |

## Frame and units

- Units: mm. Origin at the floor, at the center of the 500 × 500 mm envelope.
- `+y` forward (intake side, front wheels), `+x` right (gripper side), `+z` up.
- Front wheels at `y = +45`, rear wheels at `y = −203`, both at `x = ±221.2`.

## Subsystems in the model

Part names carry a prefix per subsystem. The owning mechanical directory is the
home for each subsystem's own CAD.

| Prefix | Parts | Subsystem | Directory |
| --- | --- | --- | --- |
| `CH_` | 49 | Chassis, 4 × 80 mm mecanum, 4 × 180 smart encoder motors | [chassis](../../../chassis/README.md) |
| `INT_` | 55 | Ball intake (rollers, centering, lift arm `UR`, lower roller `LR`) | [ball_intake](../../../ball_intake/README.md) |
| `CN_` | 9 | Ball basket and feed roller | [ball_storage](../../../ball_storage/README.md) |
| `TW_` | 21 | Transfer tower to the shooter (belts, elbow roller, exit chute, S2 sensor) | [feeder](../../../feeder/README.md) |
| `SH_` | 16 | Shooter: 2 friction wheels on 2 brushless motors, hood flap on servo MS-12A | [shooter](../../../shooter/README.md) |
| `GR_` | 14 | Gripper: lead-screw jaw, distance sensor | [gripper](../../../gripper/README.md) |
| `ELV_`, `CAR_`, `MAS_` | 10 + 3 + 11 | Gripper elevator (belt, 358 mm travel), carriage, elevator tower with AI camera tray | [gripper_elevation](../../../gripper_elevation/README.md) |
| `FLAG_` | 1 (5 with mast) | Flag mast receptor (on robot) and mast | [flag_system](../../../flag_system/README.md) |
| `ELEC_`, `ELB_` | 4 + 6 | NovaPi, LiPo 3S 4200 mAh, power management module, drivers/Bluetooth, electronics box | [electrical](../../../../electrical/README.md) |
| `RIG_` | 7 | Structural frames and launcher base | Shared structure |
| `HW_` | 1 | 73 × M3 button-head screws | [common_parts](../../../common_parts/README.md) |
| `REF_` | 24 | Reference balls and flag (not robot parts) | — |

## Measured envelope (from the STEP, via GLB mesh)

| Configuration | X × Y footprint | Height | Notes |
| --- | --- | --- | --- |
| Initial (`inicial`) | 499.5 × 499.0 mm | 642.0 mm | Gripper jaw at `x = +250.0`, chassis at `y = −250.0` |
| Carriage up, no mast | 499.5 × 499.0 mm | 642.0 mm | Carriage stays inside the elevator tower |
| After modification, mast + flag (`carro_arriba`) | 499.5 × 499.0 mm | 1062.6 mm (mast), 1128.3 mm (flag loop) | Flag cloth stays inside the footprint |

| Drive geometry | Value |
| --- | --- |
| Wheel centers | `x = ±221.2`, `y = +45.0` / `−203.0`, `z = 40.0` |
| Track × wheelbase | 442.5 × 248.0 mm |
| Wheel-rectangle center | `y = −79.0 mm` (79 mm behind the envelope center) |
| Effective turn radius a + b | 345.2 mm → 0.603 cm of wheel travel per degree |
| Mecanum outer diameter | 78.9 mm (rollers) |

## Actuators (from part names)

| Type | Count | Parts | Limit (T02) |
| --- | --- | --- | --- |
| 180 smart encoder motor | 4 | `CH_motor_180_encoder_{del,tras}_{izq,der}` | — |
| DC 25 motor | 6 | `GR` jaw, `CN` feeder, `INT_LR` roller, `INT_UR` lift, `INT_UR` rotation, `TW` elbow | — |
| DC 37 motor | 3 | `ELV` elevator (50 rpm), `INT` intake (200 rpm), `TW` tower (200 rpm) | — |
| **DC + encoder total** | **13** | | ≤ 13 (T02-R1), with ≥ 1 in reserve (T02-R6) |
| Brushless | 2 | `SH_brushless_kit_horario`, `SH_brushless_kit_antihorario` | ≤ 2 (T02-R3) |
| Servo MS-12A | 1 | `SH_servo_MS12A_kit` (hood flap) | ≤ 6 (T02-R2) |

Sensors in the model: distance sensor (`GR_sensor_distancia_kit`), AI camera 2.0
(`ELV_AI_camera_2_0_kit`), S2 entry sensor (`TW_S2_sensor_entrada`).

## Requirements check (CAD)

| Requirement | Criterion | CAD result | Status |
| --- | --- | --- | --- |
| T01-R1 | ≤ 500 × 500 × 700 mm before modification | 499.5 × 499.0 × 642.0 mm | Meets in CAD; **0.5 mm** footprint margin |
| T01-R2 | ≤ 500 × 500 mm footprint after modification | 499.5 × 499.0 mm with mast and flag | Meets in CAD; same margin |
| T01-R3 | ≤ 10 kg with battery | No mass data in the STEP | Not checked |
| T01-R4 | Team ID ≥ 3.5 cm on light background | No ID plate in the model | **Missing in CAD** |
| T02-R1 | ≤ 13 DC/encoder motors | 13 | Meets in CAD, at the limit |
| T02-R2 | ≤ 6 servos MS-12A | 1 | Meets in CAD |
| T02-R3 | ≤ 2 brushless 2823/2824 | 2 | Meets in CAD; brushless model not named in CAD |
| T02-R4 | Allowed motor models only | DC25, DC37, 180 encoder, brushless, MS-12A | Meets in CAD (by name) |
| T02-R6 | ≥ 1 motor and ≥ 1 servo in reserve | 0 motors, 5 servos | **Does not meet** (motor reserve) |
| T05-R1 | Fits the 500 × 500 mm Starting Area | 499.5 × 499.0 mm | Meets the rule; misses the T05 design target ≤ 480 × 480 mm |
| T05-R7 | Space for battery, NovaPi, power module | All three in `ELB` box at the rear | Meets in CAD |
| T16-R5 | Mast added during modification keeps 500 × 500 mm | 499.5 × 499.0 mm | Meets in CAD |
| T17-R1 | One LiPo 3S 11.1 V 4200 mAh | `ELEC_bateria_LiPo_3S_4200mAh` | Meets in CAD; C rating not in CAD |
| T17-R2 | Battery fixed | `ELB_cinchos_bateria_velcro_x2` | To inspect on the prototype |
| T17-R7 | Power module visible, antenna away from metal | Inside the carbon-fiber `ELB` box with a CF lid | **Risk:** carbon fiber is conductive and blocks the view |

Issues found are recorded in [known issues](../../../../docs/05_integration/known_issues.md)
(KI-001 to KI-007) and in the [rules compliance matrix](../../../../docs/01_requirements/rules_compliance_matrix.md).

## Method

The STEP files were converted to GLB with `cascadio` (Open CASCADE, linear
tolerance 0.5 mm) and measured per part with `trimesh`. Bounding boxes come from the
tessellated meshes, so values carry up to about 0.5 mm of tessellation error. The
CadQuery scripts were read but not run.
