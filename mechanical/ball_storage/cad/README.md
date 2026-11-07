# Ball Storage CAD

Wide basket in front of the tower and the short feed roller that hands balls to the launcher (subsystem 8, `CN_`).

## Revisions

| Revision | Parts | Integration |
| --- | --- | --- |
| [v22](v22/) | 9 numbered STL (this page) | [Storm Breaker v22](../../assemblies/full_robot/v22/README.md) |

## v22 · Numbered parts

File name = `<subsystem>.<part>_<CAD name>.stl`, the same numbering as the [assembly manual](../../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf) (sheet 10). Within a subsystem, part 1 is the largest by volume.

- Every STL is exported in the **robot frame at its assembled position** (mm; origin on the floor at the centre of the 500 × 500 envelope; `+y` forward, `+x` right, `+z` up), so the files drop into place together. Re-orient each part on the build plate before printing.
- Mesh tolerance 0.1 mm linear / 0.2 rad angular. Use the STEP in [full_robot/v22](../../assemblies/full_robot/v22/cad/) for engineering changes.
- Kit parts (motors, wheels, beams, gears, belts) and electronics are included only as **reference geometry** for fit checks; do not print them.
- A file whose name ends in `_xN` holds N identical instances in one mesh.

### 8. Basket and feed roller (9 parts)

| No. | File | Size X × Y × Z (mm) | Process |
| --- | --- | --- | --- |
| 8.1 | [`8.1_CN_paredes_canasta_PC_1.stl`](v22/8.1_CN_paredes_canasta_PC_1.stl) | 272 × 140 × 103.9 | Cut / bend sheet |
| 8.2 | [`8.2_CN_rodillo_alimentador_TPU_D30.stl`](v22/8.2_CN_rodillo_alimentador_TPU_D30.stl) | 30 × 69 × 30 | FDM print |
| 8.3 | [`8.3_CN_piso_canasta_PC_1_2.stl`](v22/8.3_CN_piso_canasta_PC_1_2.stl) | 271 × 143 × 35.2 | Cut / bend sheet |
| 8.4 | [`8.4_CN_motor_DC25_200rpm_alimentador_3a1.stl`](v22/8.4_CN_motor_DC25_200rpm_alimentador_3a1.stl) | 24.4 × 61 × 24.4 | MakeX kit part |
| 8.5 | [`8.5_CN_engrane_48T_kit_motor_alimentador.stl`](v22/8.5_CN_engrane_48T_kit_motor_alimentador.stl) | 50 × 8.1 × 50 | MakeX kit part |
| 8.6 | [`8.6_CN_soporte_alimentador_y_motor_PETG.stl`](v22/8.6_CN_soporte_alimentador_y_motor_PETG.stl) | 52.7 × 58 × 48 | FDM print |
| 8.7 | [`8.7_CN_eje_alimentador_D8_Al.stl`](v22/8.7_CN_eje_alimentador_D8_Al.stl) | 8 × 90 × 8 | Cut to length (rod / tube) |
| 8.8 | [`8.8_CN_engrane_16T_kit_alimentador.stl`](v22/8.8_CN_engrane_16T_kit_alimentador.stl) | 18 × 8 × 18 | MakeX kit / purchase |
| 8.9 | [`8.9_CN_buje_alimentador_en_pared_trasera.stl`](v22/8.9_CN_buje_alimentador_en_pared_trasera.stl) | 10 × 4 × 10 | FDM print |

