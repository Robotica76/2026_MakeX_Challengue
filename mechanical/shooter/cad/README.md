# Shooter CAD

Inverted launcher: friction wheel on top, hood below, ball fed horizontally from the basket (subsystem 7).

## Revisions

| Revision | Parts | Integration |
| --- | --- | --- |
| [v22](v22/) | 18 numbered STL (this page) | [Storm Breaker v22](../../assemblies/full_robot/v22/README.md) |

## v22 · Numbered parts

File name = `<subsystem>.<part>_<CAD name>.stl`, the same numbering as the [assembly manual](../../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf) (sheet 9). Within a subsystem, part 1 is the largest by volume.

- Every STL is exported in the **robot frame at its assembled position** (mm; origin on the floor at the centre of the 500 × 500 envelope; `+y` forward, `+x` right, `+z` up), so the files drop into place together. Re-orient each part on the build plate before printing.
- Mesh tolerance 0.1 mm linear / 0.2 rad angular. Use the STEP in [full_robot/v22](../../assemblies/full_robot/v22/cad/) for engineering changes.
- Kit parts (motors, wheels, beams, gears, belts) and electronics are included only as **reference geometry** for fit checks; do not print them.
- A file whose name ends in `_xN` holds N identical instances in one mesh.

### 7. Shooter (inverted launcher) (18 parts)

| No. | File | Size X × Y × Z (mm) | Process |
| --- | --- | --- | --- |
| 7.1 | [`7.1_SH_friction_wheel_D45x19_5_kit_x2.stl`](v22/7.1_SH_friction_wheel_D45x19_5_kit_x2.stl) | 45 × 41.1 × 45 | MakeX kit / purchase |
| 7.2 | [`7.2_SH_placa_lateral_CF3_der.stl`](v22/7.2_SH_placa_lateral_CF3_der.stl) | 128 × 3 × 146.5 | CNC / water-jet cut plate, 3 mm |
| 7.3 | [`7.3_SH_placa_lateral_CF3_izq.stl`](v22/7.3_SH_placa_lateral_CF3_izq.stl) | 128 × 3 × 146.5 | CNC / water-jet cut plate, 3 mm |
| 7.4 | [`7.4_RIG_base_lanzador_CF3.stl`](v22/7.4_RIG_base_lanzador_CF3.stl) | 82 × 119 × 3 | CNC / water-jet cut plate, 3 mm |
| 7.5 | [`7.5_RIG_postes_lanzador_tubo_CF_16_x2.stl`](v22/7.5_RIG_postes_lanzador_tubo_CF_16_x2.stl) | 16 × 62 × 212.7 | Cut to length from CF tube |
| 7.6 | [`7.6_SH_separadores_Al_D8_x4.stl`](v22/7.6_SH_separadores_Al_D8_x4.stl) | 100 × 113 × 147 | Cut to length (rod / tube) |
| 7.7 | [`7.7_SH_capucha_inferior_PC2mm_R82.stl`](v22/7.7_SH_capucha_inferior_PC2mm_R82.stl) | 111.5 × 88 × 37.2 | Cut / bend sheet |
| 7.8 | [`7.8_SH_servo_MS12A_kit.stl`](v22/7.8_SH_servo_MS12A_kit.stl) | 20 × 22 × 40 | MakeX kit part |
| 7.9 | [`7.9_SH_brushless_kit_antihorario.stl`](v22/7.9_SH_brushless_kit_antihorario.stl) | 28 × 26 × 28 | MakeX kit part |
| 7.10 | [`7.10_SH_brushless_kit_horario.stl`](v22/7.10_SH_brushless_kit_horario.stl) | 28 × 26 × 28 | MakeX kit part |
| 7.11 | [`7.11_SH_brushless_ESC_kit_x2.stl`](v22/7.11_SH_brushless_ESC_kit_x2.stl) | 50 × 6 × 52 | MakeX kit part |
| 7.12 | [`7.12_SH_capucha_costillas_PETG_x3.stl`](v22/7.12_SH_capucha_costillas_PETG_x3.stl) | 122 × 64 × 44 | FDM print |
| 7.13 | [`7.13_SH_capucha_grip_TPU.stl`](v22/7.13_SH_capucha_grip_TPU.stl) | 91.4 × 60 × 30.4 | FDM print |
| 7.14 | [`7.14_SH_friction_wheel_ring_D28x7_kit_x2.stl`](v22/7.14_SH_friction_wheel_ring_D28x7_kit_x2.stl) | 28 × 55 × 28 | MakeX kit / purchase |
| 7.15 | [`7.15_SH_guarda_superior_PC.stl`](v22/7.15_SH_guarda_superior_PC.stl) | 48.3 × 88 × 20.7 | Cut / bend sheet |
| 7.16 | [`7.16_SH_brushless_motor_bracket_kit_x2.stl`](v22/7.16_SH_brushless_motor_bracket_kit_x2.stl) | 34 × 113 × 34 | MakeX kit part |
| 7.17 | [`7.17_SH_bisagra_aleta_D3.stl`](v22/7.17_SH_bisagra_aleta_D3.stl) | 3 × 113 × 3 | Cut to length from rod |
| 7.18 | [`7.18_SH_aleta_capucha_PC2mm_servo.stl`](v22/7.18_SH_aleta_capucha_PC2mm_servo.stl) | 3.3 × 88 × 3.5 | MakeX kit part |

