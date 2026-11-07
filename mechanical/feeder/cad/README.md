# Feeder CAD

Ball tower: belts that lift the balls from the intake to the elbow at the top, which drops them into the basket (subsystem 3, `TW_`).

## Revisions

| Revision | Parts | Integration |
| --- | --- | --- |
| [v22](v22/) | 21 numbered STL (this page) | [Storm Breaker v22](../../assemblies/full_robot/v22/README.md) |

## v22 · Numbered parts

File name = `<subsystem>.<part>_<CAD name>.stl`, the same numbering as the [assembly manual](../../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf) (sheet 5). Within a subsystem, part 1 is the largest by volume.

- Every STL is exported in the **robot frame at its assembled position** (mm; origin on the floor at the centre of the 500 × 500 envelope; `+y` forward, `+x` right, `+z` up), so the files drop into place together. Re-orient each part on the build plate before printing.
- Mesh tolerance 0.1 mm linear / 0.2 rad angular. Use the STEP in [full_robot/v22](../../assemblies/full_robot/v22/cad/) for engineering changes.
- Kit parts (motors, wheels, beams, gears, belts) and electronics are included only as **reference geometry** for fit checks; do not print them.
- A file whose name ends in `_xN` holds N identical instances in one mesh.

### 3. Ball tower (transfer to basket) (21 parts)

| No. | File | Size X × Y × Z (mm) | Process |
| --- | --- | --- | --- |
| 3.1 | [`3.1_TW_placa_lateral_der_CF3.stl`](v22/3.1_TW_placa_lateral_der_CF3.stl) | 3 × 263.2 × 476.8 | CNC / water-jet cut plate, 3 mm |
| 3.2 | [`3.2_TW_placa_lateral_izq_CF3.stl`](v22/3.2_TW_placa_lateral_izq_CF3.stl) | 3 × 263.2 × 476.8 | CNC / water-jet cut plate, 3 mm |
| 3.3 | [`3.3_TW_placa_respaldo_bandas_PC.stl`](v22/3.3_TW_placa_respaldo_bandas_PC.stl) | 227 × 82.7 × 301.9 | MakeX kit / purchase |
| 3.4 | [`3.4_TW_motor_DC37_200rpm_kit.stl`](v22/3.4_TW_motor_DC37_200rpm_kit.stl) | 104 × 37 × 37 | MakeX kit part |
| 3.5 | [`3.5_TW_cubierta_codo_PC_1_5.stl`](v22/3.5_TW_cubierta_codo_PC_1_5.stl) | 227 × 175 × 87.5 | Cut / bend sheet |
| 3.6 | [`3.6_TW_rodillo_codo_manga_PETG_TPU_D40.stl`](v22/3.6_TW_rodillo_codo_manga_PETG_TPU_D40.stl) | 221 × 40 × 40 | FDM print |
| 3.7 | [`3.7_TW_pared_frontal_PC_con_ventana.stl`](v22/3.7_TW_pared_frontal_PC_con_ventana.stl) | 227 × 65.6 × 238.1 | Cut / bend sheet |
| 3.8 | [`3.8_TW_poleas_PU_30mm_kit_x12.stl`](v22/3.8_TW_poleas_PU_30mm_kit_x12.stl) | 196.4 × 121.1 × 370 | MakeX kit / purchase |
| 3.9 | [`3.9_TW_bandas_PU_redondas_kit_x6_L800.stl`](v22/3.9_TW_bandas_PU_redondas_kit_x6_L800.stl) | 191.4 × 127.1 × 376 | MakeX kit / purchase |
| 3.10 | [`3.10_TW_aleta_antirretorno_TPU_1_5.stl`](v22/3.10_TW_aleta_antirretorno_TPU_1_5.stl) | 223 × 24.8 × 87.5 | FDM print |
| 3.11 | [`3.11_TW_motor_DC25_interno_codo.stl`](v22/3.11_TW_motor_DC25_interno_codo.stl) | 55 × 24.4 × 24.4 | MakeX kit part |
| 3.12 | [`3.12_TW_engrane_48T_kit_motor.stl`](v22/3.12_TW_engrane_48T_kit_motor.stl) | 8.1 × 50 × 50 | MakeX kit part |
| 3.13 | [`3.13_TW_engrane_48T_kit_loco.stl`](v22/3.13_TW_engrane_48T_kit_loco.stl) | 8.1 × 50 × 50 | MakeX kit / purchase |
| 3.14 | [`3.14_TW_ejes_D8_tubo_Al_x2.stl`](v22/3.14_TW_ejes_D8_tubo_Al_x2.stl) | 247 × 99.1 × 348 | Cut to length (rod / tube) |
| 3.15 | [`3.15_TW_tobogan_salida_codo_PC_1_5.stl`](v22/3.15_TW_tobogan_salida_codo_PC_1_5.stl) | 227 × 21.4 × 19.5 | Cut / bend sheet |
| 3.16 | [`3.16_TW_soporte_DC37_kit.stl`](v22/3.16_TW_soporte_DC37_kit.stl) | 4 × 44 × 44 | MakeX kit / purchase |
| 3.17 | [`3.17_TW_munones_codo_D8_x2.stl`](v22/3.17_TW_munones_codo_D8_x2.stl) | 234.5 × 8 × 8 | Cut to length from rod |
| 3.18 | [`3.18_TW_S2_sensor_entrada.stl`](v22/3.18_TW_S2_sensor_entrada.stl) | 8 × 28.4 × 25.5 | MakeX kit part |
| 3.19 | [`3.19_TW_topes_aleta_PETG.stl`](v22/3.19_TW_topes_aleta_PETG.stl) | 227 × 25.2 × 80.8 | FDM print |
| 3.20 | [`3.20_TW_engrane_16T_kit_eje.stl`](v22/3.20_TW_engrane_16T_kit_eje.stl) | 8 × 18 × 18 | MakeX kit / purchase |
| 3.21 | [`3.21_TW_eje_loco.stl`](v22/3.21_TW_eje_loco.stl) | 11 × 8 × 8 | Cut to length from rod |

