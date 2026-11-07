# Chassis CAD

Chassis, drive, and the electronics box (subsystems 1 and 2 of the v22 numbering). Full-robot CAD stays in [full_robot](../../assemblies/full_robot/README.md).

## Revisions

| Revision | Parts | Integration |
| --- | --- | --- |
| [v22](v22/) | 59 numbered STL (this page) | [Storm Breaker v22](../../assemblies/full_robot/v22/README.md) |

## v22 · Numbered parts

File name = `<subsystem>.<part>_<CAD name>.stl`, the same numbering as the [assembly manual](../../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf) (sheets 3, 4). Within a subsystem, part 1 is the largest by volume.

- Every STL is exported in the **robot frame at its assembled position** (mm; origin on the floor at the centre of the 500 × 500 envelope; `+y` forward, `+x` right, `+z` up), so the files drop into place together. Re-orient each part on the build plate before printing.
- Mesh tolerance 0.1 mm linear / 0.2 rad angular. Use the STEP in [full_robot/v22](../../assemblies/full_robot/v22/cad/) for engineering changes.
- Kit parts (motors, wheels, beams, gears, belts) and electronics are included only as **reference geometry** for fit checks; do not print them.
- A file whose name ends in `_xN` holds N identical instances in one mesh.

### 1. Chassis and drive (49 parts)

| No. | File | Size X × Y × Z (mm) | Process |
| --- | --- | --- | --- |
| 1.1 | [`1.1_CH_calzas_travesano_impresas_x6.stl`](v22/1.1_CH_calzas_travesano_impresas_x6.stl) | 398 × 146 × 24 | FDM print |
| 1.2 | [`1.2_CH_travesanos_square_beam_2424_312_x3.stl`](v22/1.2_CH_travesanos_square_beam_2424_312_x3.stl) | 312 × 146 × 24 | MakeX kit / purchase |
| 1.3 | [`1.3_CH_mecanum_80_R_del_der_llanta.stl`](v22/1.3_CH_mecanum_80_R_del_der_llanta.stl) | 37.6 × 64 × 64.1 | MakeX kit / purchase |
| 1.4 | [`1.4_CH_mecanum_80_L_tras_der_llanta.stl`](v22/1.4_CH_mecanum_80_L_tras_der_llanta.stl) | 37.6 × 64 × 64.1 | MakeX kit / purchase |
| 1.5 | [`1.5_CH_mecanum_80_R_tras_izq_llanta.stl`](v22/1.5_CH_mecanum_80_R_tras_izq_llanta.stl) | 37.6 × 64 × 64.1 | MakeX kit / purchase |
| 1.6 | [`1.6_CH_mecanum_80_L_del_izq_llanta.stl`](v22/1.6_CH_mecanum_80_L_del_izq_llanta.stl) | 37.6 × 64 × 64.1 | MakeX kit / purchase |
| 1.7 | [`1.7_CH_guarda_rueda_del_der_PETG.stl`](v22/1.7_CH_guarda_rueda_del_der_PETG.stl) | 50 × 94 × 94 | FDM print |
| 1.8 | [`1.8_CH_guarda_rueda_del_izq_PETG.stl`](v22/1.8_CH_guarda_rueda_del_izq_PETG.stl) | 50 × 94 × 94 | FDM print |
| 1.9 | [`1.9_CH_slide_beam_496_izq.stl`](v22/1.9_CH_slide_beam_496_izq.stl) | 24 × 339 × 8 | MakeX kit / purchase |
| 1.10 | [`1.10_CH_slide_beam_496_der.stl`](v22/1.10_CH_slide_beam_496_der.stl) | 24 × 339 × 8 | MakeX kit / purchase |
| 1.11 | [`1.11_CH_guarda_rueda_tras_izq_PETG.stl`](v22/1.11_CH_guarda_rueda_tras_izq_PETG.stl) | 50 × 94 × 75 | FDM print |
| 1.12 | [`1.12_CH_mecanum_80_R_del_der_rodillos.stl`](v22/1.12_CH_mecanum_80_R_del_der_rodillos.stl) | 29.7 × 78.8 × 79.1 | MakeX kit / purchase |
| 1.13 | [`1.13_CH_mecanum_80_L_del_izq_rodillos.stl`](v22/1.13_CH_mecanum_80_L_del_izq_rodillos.stl) | 29.7 × 78.8 × 79.1 | MakeX kit / purchase |
| 1.14 | [`1.14_CH_mecanum_80_R_tras_izq_rodillos.stl`](v22/1.14_CH_mecanum_80_R_tras_izq_rodillos.stl) | 29.7 × 78.8 × 79.1 | MakeX kit / purchase |
| 1.15 | [`1.15_CH_mecanum_80_L_tras_der_rodillos.stl`](v22/1.15_CH_mecanum_80_L_tras_der_rodillos.stl) | 29.7 × 78.8 × 79.1 | MakeX kit / purchase |
| 1.16 | [`1.16_CH_guarda_rueda_tras_der_PETG.stl`](v22/1.16_CH_guarda_rueda_tras_der_PETG.stl) | 50 × 88 × 75 | FDM print |
| 1.17 | [`1.17_CH_motor_180_encoder_del_izq_caja.stl`](v22/1.17_CH_motor_180_encoder_del_izq_caja.stl) | 24 × 48.1 × 32 | MakeX kit part |
| 1.18 | [`1.18_CH_motor_180_encoder_del_der_caja.stl`](v22/1.18_CH_motor_180_encoder_del_der_caja.stl) | 24 × 48.1 × 32 | MakeX kit part |
| 1.19 | [`1.19_CH_motor_180_encoder_tras_izq_caja.stl`](v22/1.19_CH_motor_180_encoder_tras_izq_caja.stl) | 24 × 50 × 37 | MakeX kit part |
| 1.20 | [`1.20_CH_motor_180_encoder_tras_der_caja.stl`](v22/1.20_CH_motor_180_encoder_tras_der_caja.stl) | 24 × 50 × 37 | MakeX kit part |
| 1.21 | [`1.21_CH_chumacera_impresa_del_izq.stl`](v22/1.21_CH_chumacera_impresa_del_izq.stl) | 24 × 32 × 36 | FDM print |
| 1.22 | [`1.22_CH_chumacera_impresa_del_der.stl`](v22/1.22_CH_chumacera_impresa_del_der.stl) | 24 × 32 × 36 | FDM print |
| 1.23 | [`1.23_CH_engranes_40T_impresos_del_der.stl`](v22/1.23_CH_engranes_40T_impresos_del_der.stl) | 10 × 42.1 × 82.1 | FDM print |
| 1.24 | [`1.24_CH_engranes_40T_impresos_del_izq.stl`](v22/1.24_CH_engranes_40T_impresos_del_izq.stl) | 10 × 42.1 × 82.1 | FDM print |
| 1.25 | [`1.25_CH_separadores_placa_intake_impresos_x4.stl`](v22/1.25_CH_separadores_placa_intake_impresos_x4.stl) | 350 × 95 × 24 | FDM print |
| 1.26 | [`1.26_CH_motor_180_encoder_del_izq_lata.stl`](v22/1.26_CH_motor_180_encoder_del_izq_lata.stl) | 41.3 × 20.4 × 20.4 | MakeX kit part |
| 1.27 | [`1.27_CH_motor_180_encoder_del_der_lata.stl`](v22/1.27_CH_motor_180_encoder_del_der_lata.stl) | 41.3 × 20.4 × 20.4 | MakeX kit part |
| 1.28 | [`1.28_CH_motor_180_encoder_tras_izq_lata.stl`](v22/1.28_CH_motor_180_encoder_tras_izq_lata.stl) | 41.3 × 20.4 × 20.4 | MakeX kit part |
| 1.29 | [`1.29_CH_motor_180_encoder_tras_der_lata.stl`](v22/1.29_CH_motor_180_encoder_tras_der_lata.stl) | 41.3 × 20.4 × 20.4 | MakeX kit part |
| 1.30 | [`1.30_CH_coupling_mecanum_80_tras_der.stl`](v22/1.30_CH_coupling_mecanum_80_tras_der.stl) | 38 × 11.5 × 10 | MakeX kit / purchase |
| 1.31 | [`1.31_CH_coupling_mecanum_80_del_der.stl`](v22/1.31_CH_coupling_mecanum_80_del_der.stl) | 38 × 11.5 × 10 | MakeX kit / purchase |
| 1.32 | [`1.32_CH_coupling_mecanum_80_tras_izq.stl`](v22/1.32_CH_coupling_mecanum_80_tras_izq.stl) | 38 × 11.5 × 10 | MakeX kit / purchase |
| 1.33 | [`1.33_CH_coupling_mecanum_80_del_izq.stl`](v22/1.33_CH_coupling_mecanum_80_del_izq.stl) | 38 × 11.5 × 10 | MakeX kit / purchase |
| 1.34 | [`1.34_CH_hub_mecanum_80_del_der.stl`](v22/1.34_CH_hub_mecanum_80_del_der.stl) | 9 × 30 × 30 | MakeX kit / purchase |
| 1.35 | [`1.35_CH_hub_mecanum_80_tras_izq.stl`](v22/1.35_CH_hub_mecanum_80_tras_izq.stl) | 9 × 30 × 30 | MakeX kit / purchase |
| 1.36 | [`1.36_CH_hub_mecanum_80_tras_der.stl`](v22/1.36_CH_hub_mecanum_80_tras_der.stl) | 9 × 30 × 30 | MakeX kit / purchase |
| 1.37 | [`1.37_CH_hub_mecanum_80_del_izq.stl`](v22/1.37_CH_hub_mecanum_80_del_izq.stl) | 9 × 30 × 30 | MakeX kit / purchase |
| 1.38 | [`1.38_CH_eje_rueda_D8_del_izq.stl`](v22/1.38_CH_eje_rueda_D8_del_izq.stl) | 43 × 8 × 8 | Cut to length from rod |
| 1.39 | [`1.39_CH_eje_rueda_D8_del_der.stl`](v22/1.39_CH_eje_rueda_D8_del_der.stl) | 43 × 8 × 8 | Cut to length from rod |
| 1.40 | [`1.40_CH_tornillos_M4x20_motor_tras_izq.stl`](v22/1.40_CH_tornillos_M4x20_motor_tras_izq.stl) | 7 × 39 × 23 | Hardware (purchase) |
| 1.41 | [`1.41_CH_tornillos_M4x20_motor_tras_der.stl`](v22/1.41_CH_tornillos_M4x20_motor_tras_der.stl) | 7 × 39 × 23 | Hardware (purchase) |
| 1.42 | [`1.42_CH_motor_180_encoder_del_izq_eje_salida.stl`](v22/1.42_CH_motor_180_encoder_del_izq_eje_salida.stl) | 16 × 6 × 6 | MakeX kit part |
| 1.43 | [`1.43_CH_motor_180_encoder_del_der_eje_salida.stl`](v22/1.43_CH_motor_180_encoder_del_der_eje_salida.stl) | 16 × 6 × 6 | MakeX kit part |
| 1.44 | [`1.44_CH_tornillo_M2_5x30_tras_izq.stl`](v22/1.44_CH_tornillo_M2_5x30_tras_izq.stl) | 31.5 × 4.6 × 4.6 | Hardware (purchase) |
| 1.45 | [`1.45_CH_tornillo_M2_5x30_tras_der.stl`](v22/1.45_CH_tornillo_M2_5x30_tras_der.stl) | 31.5 × 4.6 × 4.6 | Hardware (purchase) |
| 1.46 | [`1.46_CH_tornillo_M2_5x30_del_der.stl`](v22/1.46_CH_tornillo_M2_5x30_del_der.stl) | 31.5 × 4.6 × 4.6 | Hardware (purchase) |
| 1.47 | [`1.47_CH_tornillo_M2_5x30_del_izq.stl`](v22/1.47_CH_tornillo_M2_5x30_del_izq.stl) | 31.5 × 4.6 × 4.6 | Hardware (purchase) |
| 1.48 | [`1.48_CH_motor_180_encoder_tras_der_eje_salida.stl`](v22/1.48_CH_motor_180_encoder_tras_der_eje_salida.stl) | 6 × 6 × 6 | MakeX kit part |
| 1.49 | [`1.49_CH_motor_180_encoder_tras_izq_eje_salida.stl`](v22/1.49_CH_motor_180_encoder_tras_izq_eje_salida.stl) | 6 × 6 × 6 | MakeX kit part |

### 2. Electronics box (10 parts)

| No. | File | Size X × Y × Z (mm) | Process |
| --- | --- | --- | --- |
| 2.1 | [`2.1_ELEC_bateria_LiPo_3S_4200mAh.stl`](v22/2.1_ELEC_bateria_LiPo_3S_4200mAh.stl) | 138 × 46 × 30 | Electronics (MakeX kit / purchase) |
| 2.2 | [`2.2_ELEC_NovaPi_con_case.stl`](v22/2.2_ELEC_NovaPi_con_case.stl) | 100 × 45 × 33 | Electronics (MakeX kit / purchase) |
| 2.3 | [`2.3_ELEC_power_expansion_y_management.stl`](v22/2.3_ELEC_power_expansion_y_management.stl) | 82 × 33 × 24 | Electronics (MakeX kit / purchase) |
| 2.4 | [`2.4_ELB_caja_piso_CF2_estructural.stl`](v22/2.4_ELB_caja_piso_CF2_estructural.stl) | 398 × 71 × 2 | CNC / water-jet cut plate, 2 mm |
| 2.5 | [`2.5_ELEC_drivers_y_bluetooth.stl`](v22/2.5_ELEC_drivers_y_bluetooth.stl) | 56 × 19 × 33 | Electronics (MakeX kit / purchase) |
| 2.6 | [`2.6_ELB_caja_paredes_CF1_ventiladas.stl`](v22/2.6_ELB_caja_paredes_CF1_ventiladas.stl) | 333 × 71 × 37 | CNC / water-jet cut plate, 1 mm |
| 2.7 | [`2.7_ELB_caja_tapa_CF1_removible.stl`](v22/2.7_ELB_caja_tapa_CF1_removible.stl) | 333 × 71 × 1 | CNC / water-jet cut plate, 1 mm |
| 2.8 | [`2.8_ELB_caja_esquineros_PETG_x4.stl`](v22/2.8_ELB_caja_esquineros_PETG_x4.stl) | 331 × 69 × 37 | FDM print |
| 2.9 | [`2.9_ELB_calzas_piso_rieles_PETG_x4.stl`](v22/2.9_ELB_calzas_piso_rieles_PETG_x4.stl) | 386 × 30 × 3 | FDM print |
| 2.10 | [`2.10_ELB_cinchos_bateria_velcro_x2.stl`](v22/2.10_ELB_cinchos_bateria_velcro_x2.stl) | 48 × 46 × 1.5 | Purchase |

