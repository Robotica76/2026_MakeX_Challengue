# Gripper CAD

Carriage and lead-screw jaw gripper; also carries the flag-mast receptor (subsystem 6).

## Revisions

| Revision | Parts | Integration |
| --- | --- | --- |
| [v22](v22/) | 18 numbered STL (this page) | [Storm Breaker v22](../../assemblies/full_robot/v22/README.md) |

## v22 · Numbered parts

File name = `<subsystem>.<part>_<CAD name>.stl`, the same numbering as the [assembly manual](../../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf) (sheet 8). Within a subsystem, part 1 is the largest by volume.

- Every STL is exported in the **robot frame at its assembled position** (mm; origin on the floor at the centre of the 500 × 500 envelope; `+y` forward, `+x` right, `+z` up), so the files drop into place together. Re-orient each part on the build plate before printing.
- Mesh tolerance 0.1 mm linear / 0.2 rad angular. Use the STEP in [full_robot/v22](../../assemblies/full_robot/v22/cad/) for engineering changes.
- Kit parts (motors, wheels, beams, gears, belts) and electronics are included only as **reference geometry** for fit checks; do not print them.
- A file whose name ends in `_xN` holds N identical instances in one mesh.

### 6. Carriage and gripper (18 parts)

| No. | File | Size X × Y × Z (mm) | Process |
| --- | --- | --- | --- |
| 6.1 | [`6.1_CAR_linear_motion_slide_unit_kit_x2.stl`](v22/6.1_CAR_linear_motion_slide_unit_kit_x2.stl) | 24 × 32 × 98 | MakeX kit / purchase |
| 6.2 | [`6.2_CAR_placa_carro_CF3.stl`](v22/6.2_CAR_placa_carro_CF3.stl) | 5 × 60.5 × 110 | CNC / water-jet cut plate, 3 mm |
| 6.3 | [`6.3_GR_motor_DC25_pinza.stl`](v22/6.3_GR_motor_DC25_pinza.stl) | 25 × 55 × 25 | MakeX kit part |
| 6.4 | [`6.4_GR_bloque_montaje_PETG.stl`](v22/6.4_GR_bloque_montaje_PETG.stl) | 14 × 54 × 34 | FDM print |
| 6.5 | [`6.5_GR_almohadilla_V_movil_TPU.stl`](v22/6.5_GR_almohadilla_V_movil_TPU.stl) | 39 × 6 × 118 | FDM print |
| 6.6 | [`6.6_GR_almohadilla_V_fija_TPU.stl`](v22/6.6_GR_almohadilla_V_fija_TPU.stl) | 39 × 6 × 118 | FDM print |
| 6.7 | [`6.7_GR_mordaza_fija_Al3.stl`](v22/6.7_GR_mordaza_fija_Al3.stl) | 43 × 4 × 143 | CNC cut plate, 3 mm |
| 6.8 | [`6.8_GR_mordaza_movil_Al3.stl`](v22/6.8_GR_mordaza_movil_Al3.stl) | 43 × 4 × 142 | CNC cut plate, 3 mm |
| 6.9 | [`6.9_GR_tabla_marco_CF3.stl`](v22/6.9_GR_tabla_marco_CF3.stl) | 3 × 166 × 34 | CNC / water-jet cut plate, 3 mm |
| 6.10 | [`6.10_GR_tornillo_avance_T8x8.stl`](v22/6.10_GR_tornillo_avance_T8x8.stl) | 9.6 × 176 × 9.6 | Purchase (T8 lead screw + nut) |
| 6.11 | [`6.11_GR_guia_D8_tubo_Al.stl`](v22/6.11_GR_guia_D8_tubo_Al.stl) | 8 × 166 × 8 | Cut to length (rod / tube) |
| 6.12 | [`6.12_GR_carro_tuerca_PETG.stl`](v22/6.12_GR_carro_tuerca_PETG.stl) | 15 × 12 × 32 | FDM print |
| 6.13 | [`6.13_CAR_belt_connector_kit.stl`](v22/6.13_CAR_belt_connector_kit.stl) | 13.1 × 10 × 30 | MakeX kit / purchase |
| 6.14 | [`6.14_GR_sensor_distancia_kit.stl`](v22/6.14_GR_sensor_distancia_kit.stl) | 8 × 24 × 20 | MakeX kit part |
| 6.15 | [`6.15_GR_bloque_extremo_fijo_PETG.stl`](v22/6.15_GR_bloque_extremo_fijo_PETG.stl) | 15.5 × 8 × 34 | FDM print |
| 6.16 | [`6.16_GR_bloque_extremo_libre_PETG.stl`](v22/6.16_GR_bloque_extremo_libre_PETG.stl) | 15.5 × 8 × 34 | FDM print |
| 6.17 | [`6.17_FLAG_receptor_mastil_PETG.stl`](v22/6.17_FLAG_receptor_mastil_PETG.stl) | 13 × 14 × 22 | FDM print |
| 6.18 | [`6.18_GR_acople_motor.stl`](v22/6.18_GR_acople_motor.stl) | 14 × 2 × 14 | MakeX kit part |

