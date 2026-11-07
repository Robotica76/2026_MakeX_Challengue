# Ball Intake CAD

Floor and shelf intake, rollers, and the UR lift arm (subsystem 4).

## Revisions

| Revision | Parts | Integration |
| --- | --- | --- |
| [v22](v22/) | 55 numbered STL (this page) | [Storm Breaker v22](../../assemblies/full_robot/v22/README.md) |

## v22 · Numbered parts

File name = `<subsystem>.<part>_<CAD name>.stl`, the same numbering as the [assembly manual](../../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf) (sheet 6). Within a subsystem, part 1 is the largest by volume.

- Every STL is exported in the **robot frame at its assembled position** (mm; origin on the floor at the centre of the 500 × 500 envelope; `+y` forward, `+x` right, `+z` up), so the files drop into place together. Re-orient each part on the build plate before printing.
- Mesh tolerance 0.1 mm linear / 0.2 rad angular. Use the STEP in [full_robot/v22](../../assemblies/full_robot/v22/cad/) for engineering changes.
- Kit parts (motors, wheels, beams, gears, belts) and electronics are included only as **reference geometry** for fit checks; do not print them.
- A file whose name ends in `_xN` holds N identical instances in one mesh.

### 4. Ball intake and UR arm (55 parts)

| No. | File | Size X × Y × Z (mm) | Process |
| --- | --- | --- | --- |
| 4.1 | [`4.1_INT_LR_manguito_TPU_D44.stl`](v22/4.1_INT_LR_manguito_TPU_D44.stl) | 270.1 × 43.9 × 43.9 | FDM print |
| 4.2 | [`4.2_INT_UR_nucleo_D32.stl`](v22/4.2_INT_UR_nucleo_D32.stl) | 332 × 32 × 32 | FDM print |
| 4.3 | [`4.3_INT_centrador_nucleo.stl`](v22/4.3_INT_centrador_nucleo.stl) | 282 × 32 × 32 | FDM print |
| 4.4 | [`4.4_INT_R3_entrada_nucleo.stl`](v22/4.4_INT_R3_entrada_nucleo.stl) | 216 × 32 × 32 | FDM print |
| 4.5 | [`4.5_INT_UR_anillos_banda_D60_PETG.stl`](v22/4.5_INT_UR_anillos_banda_D60_PETG.stl) | 250.1 × 60 × 60.1 | FDM print |
| 4.6 | [`4.6_INT_motor_DC37_200rpm_kit.stl`](v22/4.6_INT_motor_DC37_200rpm_kit.stl) | 103 × 37 × 37 | MakeX kit part |
| 4.7 | [`4.7_INT_centrador_helicoidal_TPU.stl`](v22/4.7_INT_centrador_helicoidal_TPU.stl) | 275 × 64 × 57 | FDM print |
| 4.8 | [`4.8_INT_placa_lateral_der_CF3.stl`](v22/4.8_INT_placa_lateral_der_CF3.stl) | 3 × 94 × 348 | CNC / water-jet cut plate, 3 mm |
| 4.9 | [`4.9_INT_placa_lateral_izq_CF3.stl`](v22/4.9_INT_placa_lateral_izq_CF3.stl) | 3 × 94 × 348 | CNC / water-jet cut plate, 3 mm |
| 4.10 | [`4.10_INT_tobogan_repisa_alta_PC_2mm.stl`](v22/4.10_INT_tobogan_repisa_alta_PC_2mm.stl) | 240 × 105 × 16.3 | Cut / bend sheet |
| 4.11 | [`4.11_INT_UR_riel_tubo_CF_20x20_430_izq.stl`](v22/4.11_INT_UR_riel_tubo_CF_20x20_430_izq.stl) | 20 × 20 × 428 | Cut to length from CF tube |
| 4.12 | [`4.12_INT_UR_riel_tubo_CF_20x20_430_der.stl`](v22/4.12_INT_UR_riel_tubo_CF_20x20_430_der.stl) | 20 × 20 × 428 | Cut to length from CF tube |
| 4.13 | [`4.13_INT_piso_entrada_ancho_PC.stl`](v22/4.13_INT_piso_entrada_ancho_PC.stl) | 225 × 64 × 2 | Cut / bend sheet |
| 4.14 | [`4.14_INT_UR_brazo_izq_CF3.stl`](v22/4.14_INT_UR_brazo_izq_CF3.stl) | 3 × 164 × 98 | CNC / water-jet cut plate, 3 mm |
| 4.15 | [`4.15_INT_UR_brazo_der_CF3.stl`](v22/4.15_INT_UR_brazo_der_CF3.stl) | 3 × 164 × 98 | CNC / water-jet cut plate, 3 mm |
| 4.16 | [`4.16_INT_UR_motor_DC25_elevacion.stl`](v22/4.16_INT_UR_motor_DC25_elevacion.stl) | 25 × 25 × 55 | MakeX kit part |
| 4.17 | [`4.17_INT_LR_motor_DC25_interno.stl`](v22/4.17_INT_LR_motor_DC25_interno.stl) | 55 × 25 × 25 | MakeX kit part |
| 4.18 | [`4.18_INT_UR_motor_DC25_giro_interno.stl`](v22/4.18_INT_UR_motor_DC25_giro_interno.stl) | 55 × 25 × 25 | MakeX kit part |
| 4.19 | [`4.19_INT_UR_tornillo_T8x16.stl`](v22/4.19_INT_UR_tornillo_T8x16.stl) | 9.6 × 9.6 × 437 | Purchase (T8 lead screw + nut) |
| 4.20 | [`4.20_INT_rampa_ancha_PC_2mm.stl`](v22/4.20_INT_rampa_ancha_PC_2mm.stl) | 294 × 38 × 22 | Cut / bend sheet |
| 4.21 | [`4.21_INT_UR_poleas_PU_20mm_kit_nariz_y_cola_x10.stl`](v22/4.21_INT_UR_poleas_PU_20mm_kit_nariz_y_cola_x10.stl) | 248 × 112 × 24 | MakeX kit / purchase |
| 4.22 | [`4.22_INT_R3_entrada_estrellas_TPU.stl`](v22/4.22_INT_R3_entrada_estrellas_TPU.stl) | 195 × 64 × 64 | FDM print |
| 4.23 | [`4.23_INT_UR_bandas_PU_redondas_x5.stl`](v22/4.23_INT_UR_bandas_PU_redondas_x5.stl) | 243 × 118 × 82 | MakeX kit / purchase |
| 4.24 | [`4.24_INT_engrane_48T_kit_motor.stl`](v22/4.24_INT_engrane_48T_kit_motor.stl) | 8 × 50.1 × 50.1 | MakeX kit part |
| 4.25 | [`4.25_INT_engrane_48T_kit_loco_R3.stl`](v22/4.25_INT_engrane_48T_kit_loco_R3.stl) | 8 × 50.1 × 50.1 | MakeX kit / purchase |
| 4.26 | [`4.26_INT_engrane_48T_kit_loco.stl`](v22/4.26_INT_engrane_48T_kit_loco.stl) | 8 × 50.1 × 50.1 | MakeX kit / purchase |
| 4.27 | [`4.27_INT_UR_eje_nariz_D8_Al.stl`](v22/4.27_INT_UR_eje_nariz_D8_Al.stl) | 380 × 8 × 8 | Cut to length (rod / tube) |
| 4.28 | [`4.28_INT_UR_eje_cola_D8_Al.stl`](v22/4.28_INT_UR_eje_cola_D8_Al.stl) | 380 × 8 × 8 | Cut to length (rod / tube) |
| 4.29 | [`4.29_INT_UR_dedos_TPU_espiga.stl`](v22/4.29_INT_UR_dedos_TPU_espiga.stl) | 283 × 64 × 64 | FDM print |
| 4.30 | [`4.30_INT_UR_soporte_superior_PETG.stl`](v22/4.30_INT_UR_soporte_superior_PETG.stl) | 50 × 55 × 4 | FDM print |
| 4.31 | [`4.31_INT_UR_patin_impreso_2020_izq_PETG.stl`](v22/4.31_INT_UR_patin_impreso_2020_izq_PETG.stl) | 26 × 26 × 40 | FDM print |
| 4.32 | [`4.32_INT_UR_patin_impreso_2020_der_PETG.stl`](v22/4.32_INT_UR_patin_impreso_2020_der_PETG.stl) | 26 × 26 × 40 | FDM print |
| 4.33 | [`4.33_INT_centrador_eje_D8.stl`](v22/4.33_INT_centrador_eje_D8.stl) | 316.2 × 8 × 8 | Cut to length from rod |
| 4.34 | [`4.34_INT_R3_entrada_eje_D8.stl`](v22/4.34_INT_R3_entrada_eje_D8.stl) | 316.2 × 8 × 8 | Cut to length from rod |
| 4.35 | [`4.35_INT_LR_vaso_soporte_motor_PETG.stl`](v22/4.35_INT_LR_vaso_soporte_motor_PETG.stl) | 18 × 31 × 31 | FDM print |
| 4.36 | [`4.36_INT_UR_estribo_motor_PETG.stl`](v22/4.36_INT_UR_estribo_motor_PETG.stl) | 22 × 20 × 20 | FDM print |
| 4.37 | [`4.37_INT_soporte_DC37_kit_intake.stl`](v22/4.37_INT_soporte_DC37_kit_intake.stl) | 3 × 44 × 44 | MakeX kit / purchase |
| 4.38 | [`4.38_INT_deflector_PC_der.stl`](v22/4.38_INT_deflector_PC_der.stl) | 30.6 × 39.2 × 50 | Cut / bend sheet |
| 4.39 | [`4.39_INT_deflector_PC_izq.stl`](v22/4.39_INT_deflector_PC_izq.stl) | 30.6 × 39.2 × 50 | Cut / bend sheet |
| 4.40 | [`4.40_INT_UR_munon_D8_acero.stl`](v22/4.40_INT_UR_munon_D8_acero.stl) | 80 × 8 × 8 | Cut to length from rod |
| 4.41 | [`4.41_INT_UR_poleas_GT2_20T_x2.stl`](v22/4.41_INT_UR_poleas_GT2_20T_x2.stl) | 16 × 51 × 6 | MakeX kit / purchase |
| 4.42 | [`4.42_INT_UR_tuerca_brazo_PETG.stl`](v22/4.42_INT_UR_tuerca_brazo_PETG.stl) | 14 × 12 × 24 | FDM print |
| 4.43 | [`4.43_INT_LR_munon_D8_acero.stl`](v22/4.43_INT_LR_munon_D8_acero.stl) | 41 × 8 × 8 | Cut to length from rod |
| 4.44 | [`4.44_INT_UR_soporte_inferior_PETG.stl`](v22/4.44_INT_UR_soporte_inferior_PETG.stl) | 41.2 × 10 × 4 | FDM print |
| 4.45 | [`4.45_INT_engrane_16T_kit_centrador.stl`](v22/4.45_INT_engrane_16T_kit_centrador.stl) | 8 × 18.1 × 18.1 | MakeX kit / purchase |
| 4.46 | [`4.46_INT_engrane_16T_kit_R3.stl`](v22/4.46_INT_engrane_16T_kit_R3.stl) | 8 × 18.1 × 18.1 | MakeX kit / purchase |
| 4.47 | [`4.47_INT_UR_escuadras_perfil_izq_PETG.stl`](v22/4.47_INT_UR_escuadras_perfil_izq_PETG.stl) | 4 × 20 × 428 | FDM print |
| 4.48 | [`4.48_INT_UR_escuadras_perfil_der_PETG.stl`](v22/4.48_INT_UR_escuadras_perfil_der_PETG.stl) | 4 × 20 × 428 | FDM print |
| 4.49 | [`4.49_INT_tobogan_paredes_PC_2mm.stl`](v22/4.49_INT_tobogan_paredes_PC_2mm.stl) | 243.6 × 5.9 × 45 | Cut / bend sheet |
| 4.50 | [`4.50_INT_UR_rodamiento_8x16x5.stl`](v22/4.50_INT_UR_rodamiento_8x16x5.stl) | 5 × 16 × 16 | Purchase (bearing 8x16x5) |
| 4.51 | [`4.51_INT_eje_loco.stl`](v22/4.51_INT_eje_loco.stl) | 10 × 8 × 8 | Cut to length from rod |
| 4.52 | [`4.52_INT_eje_loco_R3.stl`](v22/4.52_INT_eje_loco_R3.stl) | 10 × 8 × 8 | Cut to length from rod |
| 4.53 | [`4.53_INT_LR_collarin.stl`](v22/4.53_INT_LR_collarin.stl) | 3 × 14 × 14 | Purchase (8 mm shaft collar) |
| 4.54 | [`4.54_INT_LR_buje_PETG.stl`](v22/4.54_INT_LR_buje_PETG.stl) | 5 × 12 × 12 | FDM print |
| 4.55 | [`4.55_INT_UR_banda_GT2_elevacion.stl`](v22/4.55_INT_UR_banda_GT2_elevacion.stl) | 2 × 35 × 4 | MakeX kit / purchase |

