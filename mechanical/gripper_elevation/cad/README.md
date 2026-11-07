# Gripper Elevation CAD

Elevator tower (mast) for the gripper carriage, plus the structural ribs and spacers that tie it to the tower and intake (subsystem 5).

## Revisions

| Revision | Parts | Integration |
| --- | --- | --- |
| [v22](v22/) | 26 numbered STL (this page) | [Storm Breaker v22](../../assemblies/full_robot/v22/README.md) |

## v22 · Numbered parts

File name = `<subsystem>.<part>_<CAD name>.stl`, the same numbering as the [assembly manual](../../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf) (sheet 7). Within a subsystem, part 1 is the largest by volume.

- Every STL is exported in the **robot frame at its assembled position** (mm; origin on the floor at the centre of the 500 × 500 envelope; `+y` forward, `+x` right, `+z` up), so the files drop into place together. Re-orient each part on the build plate before printing.
- Mesh tolerance 0.1 mm linear / 0.2 rad angular. Use the STEP in [full_robot/v22](../../assemblies/full_robot/v22/cad/) for engineering changes.
- Kit parts (motors, wheels, beams, gears, belts) and electronics are included only as **reference geometry** for fit checks; do not print them.
- A file whose name ends in `_xN` holds N identical instances in one mesh.

### 5. Gripper elevator and structure (26 parts)

| No. | File | Size X × Y × Z (mm) | Process |
| --- | --- | --- | --- |
| 5.1 | [`5.1_ELV_motor_DC37_50rpm_kit.stl`](v22/5.1_ELV_motor_DC37_50rpm_kit.stl) | 37 × 111 × 37 | MakeX kit part |
| 5.2 | [`5.2_ELV_riel_slide_beam_496_kit.stl`](v22/5.2_ELV_riel_slide_beam_496_kit.stl) | 8 × 24 × 496 | MakeX kit / purchase |
| 5.3 | [`5.3_MAS_placa_trasera_CF3.stl`](v22/5.3_MAS_placa_trasera_CF3.stl) | 49 × 3 × 551 | CNC / water-jet cut plate, 3 mm |
| 5.4 | [`5.4_MAS_mamparo_interior_CF3.stl`](v22/5.4_MAS_mamparo_interior_CF3.stl) | 3 × 80 × 476 | CNC / water-jet cut plate, 3 mm |
| 5.5 | [`5.5_ELV_soporte_superior_PETG.stl`](v22/5.5_ELV_soporte_superior_PETG.stl) | 24 × 48 × 50 | FDM print |
| 5.6 | [`5.6_MAS_placa_delantera_CF3.stl`](v22/5.6_MAS_placa_delantera_CF3.stl) | 49 × 3 × 479 | CNC / water-jet cut plate, 3 mm |
| 5.7 | [`5.7_ELV_AI_camera_2_0_kit.stl`](v22/5.7_ELV_AI_camera_2_0_kit.stl) | 30 × 50 × 30 | MakeX kit part |
| 5.8 | [`5.8_ELV_soporte_inferior_PETG.stl`](v22/5.8_ELV_soporte_inferior_PETG.stl) | 24 × 52 × 29 | FDM print |
| 5.9 | [`5.9_ELV_polea_90T_kit_loca.stl`](v22/5.9_ELV_polea_90T_kit_loca.stl) | 64.3 × 12.1 × 64.3 | MakeX kit / purchase |
| 5.10 | [`5.10_ELV_polea_90T_kit_motriz.stl`](v22/5.10_ELV_polea_90T_kit_motriz.stl) | 64.3 × 12.1 × 64.3 | MakeX kit / purchase |
| 5.11 | [`5.11_MAS_tapa_y_bandeja_camara_CF3.stl`](v22/5.11_MAS_tapa_y_bandeja_camara_CF3.stl) | 85 × 62 × 3 | CNC / water-jet cut plate, 3 mm |
| 5.12 | [`5.12_RIG_cuaderna_intake_elevador_der_CF3.stl`](v22/5.12_RIG_cuaderna_intake_elevador_der_CF3.stl) | 38.5 × 3 × 230 | CNC / water-jet cut plate, 3 mm |
| 5.13 | [`5.13_MAS_piso_CF3.stl`](v22/5.13_MAS_piso_CF3.stl) | 53 × 80 × 3 | CNC / water-jet cut plate, 3 mm |
| 5.14 | [`5.14_RIG_cuaderna_intake_elevador_izq_CF3.stl`](v22/5.14_RIG_cuaderna_intake_elevador_izq_CF3.stl) | 38.5 × 3 × 208 | CNC / water-jet cut plate, 3 mm |
| 5.15 | [`5.15_ELV_banda_dentada_kit.stl`](v22/5.15_ELV_banda_dentada_kit.stl) | 60.3 × 6.1 × 532.3 | MakeX kit / purchase |
| 5.16 | [`5.16_ELV_bracket_DC37_kit.stl`](v22/5.16_ELV_bracket_DC37_kit.stl) | 34.5 × 4 × 44 | MakeX kit / purchase |
| 5.17 | [`5.17_MAS_costilla_frente_z150_CF3.stl`](v22/5.17_MAS_costilla_frente_z150_CF3.stl) | 47 × 22 × 3 | CNC / water-jet cut plate, 3 mm |
| 5.18 | [`5.18_MAS_costilla_frente_z300_CF3.stl`](v22/5.18_MAS_costilla_frente_z300_CF3.stl) | 47 × 22 × 3 | CNC / water-jet cut plate, 3 mm |
| 5.19 | [`5.19_MAS_costilla_frente_z440_CF3.stl`](v22/5.19_MAS_costilla_frente_z440_CF3.stl) | 47 × 22 × 3 | CNC / water-jet cut plate, 3 mm |
| 5.20 | [`5.20_MAS_costilla_banda_z150_CF3.stl`](v22/5.20_MAS_costilla_banda_z150_CF3.stl) | 47 × 11.5 × 3 | MakeX kit / purchase |
| 5.21 | [`5.21_MAS_costilla_banda_z300_CF3.stl`](v22/5.21_MAS_costilla_banda_z300_CF3.stl) | 47 × 11.5 × 3 | MakeX kit / purchase |
| 5.22 | [`5.22_MAS_costilla_banda_z440_CF3.stl`](v22/5.22_MAS_costilla_banda_z440_CF3.stl) | 47 × 11.5 × 3 | MakeX kit / purchase |
| 5.23 | [`5.23_ELV_eje_loca_D4_kit.stl`](v22/5.23_ELV_eje_loca_D4_kit.stl) | 4 × 18 × 4 | MakeX kit / purchase |
| 5.24 | [`5.24_RIG_separador_torre_mastil_z380_PETG.stl`](v22/5.24_RIG_separador_torre_mastil_z380_PETG.stl) | 0.5 × 16 × 16 | FDM print |
| 5.25 | [`5.25_RIG_separador_torre_mastil_z250_PETG.stl`](v22/5.25_RIG_separador_torre_mastil_z250_PETG.stl) | 0.5 × 16 × 16 | FDM print |
| 5.26 | [`5.26_RIG_separador_torre_mastil_z120_PETG.stl`](v22/5.26_RIG_separador_torre_mastil_z120_PETG.stl) | 0.5 × 16 × 16 | FDM print |

