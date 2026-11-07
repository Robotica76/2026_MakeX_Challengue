# Feeder Manufacturing

Manufacturing plan for revision v22, derived from the CAD part names. **Nothing has been fabricated yet;** processes and materials are the CAD intent and must be confirmed against stock, kit contents, and the released [drawings](../drawings/README.md).

## v22 · Bill of materials and process

| No. | Part (CAD name) | Qty | Process | Material | STL |
| --- | --- | --- | --- | --- | --- |
| 3.1 | `TW_placa_lateral_der_CF3` | 1 | CNC / water-jet cut plate, 3 mm | Carbon fibre | [STL](../cad/v22/3.1_TW_placa_lateral_der_CF3.stl) |
| 3.2 | `TW_placa_lateral_izq_CF3` | 1 | CNC / water-jet cut plate, 3 mm | Carbon fibre | [STL](../cad/v22/3.2_TW_placa_lateral_izq_CF3.stl) |
| 3.3 | `TW_placa_respaldo_bandas_PC` | 1 | MakeX kit / purchase | — | [STL](../cad/v22/3.3_TW_placa_respaldo_bandas_PC.stl) |
| 3.4 | `TW_motor_DC37_200rpm_kit` | 1 | MakeX kit part | — | [STL](../cad/v22/3.4_TW_motor_DC37_200rpm_kit.stl) |
| 3.5 | `TW_cubierta_codo_PC_1_5` | 1 | Cut / bend sheet | Polycarbonate | [STL](../cad/v22/3.5_TW_cubierta_codo_PC_1_5.stl) |
| 3.6 | `TW_rodillo_codo_manga_PETG_TPU_D40` | 1 | FDM print | PETG + TPU | [STL](../cad/v22/3.6_TW_rodillo_codo_manga_PETG_TPU_D40.stl) |
| 3.7 | `TW_pared_frontal_PC_con_ventana` | 1 | Cut / bend sheet | Polycarbonate | [STL](../cad/v22/3.7_TW_pared_frontal_PC_con_ventana.stl) |
| 3.8 | `TW_poleas_PU_30mm_kit_x12` | 12 | MakeX kit / purchase | — | [STL](../cad/v22/3.8_TW_poleas_PU_30mm_kit_x12.stl) |
| 3.9 | `TW_bandas_PU_redondas_kit_x6_L800` | 6 | MakeX kit / purchase | — | [STL](../cad/v22/3.9_TW_bandas_PU_redondas_kit_x6_L800.stl) |
| 3.10 | `TW_aleta_antirretorno_TPU_1_5` | 1 | FDM print | TPU | [STL](../cad/v22/3.10_TW_aleta_antirretorno_TPU_1_5.stl) |
| 3.11 | `TW_motor_DC25_interno_codo` | 1 | MakeX kit part | — | [STL](../cad/v22/3.11_TW_motor_DC25_interno_codo.stl) |
| 3.12 | `TW_engrane_48T_kit_motor` | 1 | MakeX kit part | — | [STL](../cad/v22/3.12_TW_engrane_48T_kit_motor.stl) |
| 3.13 | `TW_engrane_48T_kit_loco` | 1 | MakeX kit / purchase | — | [STL](../cad/v22/3.13_TW_engrane_48T_kit_loco.stl) |
| 3.14 | `TW_ejes_D8_tubo_Al_x2` | 2 | Cut to length (rod / tube) | Aluminium | [STL](../cad/v22/3.14_TW_ejes_D8_tubo_Al_x2.stl) |
| 3.15 | `TW_tobogan_salida_codo_PC_1_5` | 1 | Cut / bend sheet | Polycarbonate | [STL](../cad/v22/3.15_TW_tobogan_salida_codo_PC_1_5.stl) |
| 3.16 | `TW_soporte_DC37_kit` | 1 | MakeX kit / purchase | — | [STL](../cad/v22/3.16_TW_soporte_DC37_kit.stl) |
| 3.17 | `TW_munones_codo_D8_x2` | 2 | Cut to length from rod | Steel | [STL](../cad/v22/3.17_TW_munones_codo_D8_x2.stl) |
| 3.18 | `TW_S2_sensor_entrada` | 1 | MakeX kit part | — | [STL](../cad/v22/3.18_TW_S2_sensor_entrada.stl) |
| 3.19 | `TW_topes_aleta_PETG` | 1 | FDM print | PETG | [STL](../cad/v22/3.19_TW_topes_aleta_PETG.stl) |
| 3.20 | `TW_engrane_16T_kit_eje` | 1 | MakeX kit / purchase | — | [STL](../cad/v22/3.20_TW_engrane_16T_kit_eje.stl) |
| 3.21 | `TW_eje_loco` | 1 | Cut to length from rod | Steel | [STL](../cad/v22/3.21_TW_eje_loco.stl) |

### Summary by process

| Process | Lines |
| --- | --- |
| MakeX kit / purchase | 6 |
| MakeX kit part | 4 |
| Cut / bend sheet | 3 |
| FDM print | 3 |
| CNC / water-jet cut plate, 3 mm | 2 |
| Cut to length from rod | 2 |
| Cut to length (rod / tube) | 1 |

## Assembly

1. Side plates CF3 (3.1, 3.2) on the crossbars; right plate bolted to the elevator bulkhead; three spacers to the mast (5.24–5.26).
2. D8 aluminium axles, 12 PU pulleys D30 and 6 round belts (3 rows × 2).
3. Backing plate and front wall with window, anti-return TPU flap and stops.
4. Elbow: roller (PETG sleeve + TPU, D40) with internal DC-25, journals, PC cover 165°…−15°, exit chute.
5. DC-37 with 48T/48T/16T gears on the left side.

## Inspection checkpoints

- [ ] Belts tensioned equally on the 3 rows
- [ ] Tower tilt 15° and top at z = 430
- [ ] Nothing above z 543 for y > −67 (Central Area roof)
- [ ] Elbow cover concentric with the roller (ball gap 51 ± 1 mm)
- [ ] S2 sensor window clear
