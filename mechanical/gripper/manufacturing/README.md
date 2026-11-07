# Gripper Manufacturing

Manufacturing plan for revision v22, derived from the CAD part names. **Nothing has been fabricated yet;** processes and materials are the CAD intent and must be confirmed against stock, kit contents, and the released [drawings](../drawings/README.md).

## v22 · Bill of materials and process

| No. | Part (CAD name) | Qty | Process | Material | STL |
| --- | --- | --- | --- | --- | --- |
| 6.1 | `CAR_linear_motion_slide_unit_kit_x2` | 2 | MakeX kit / purchase | — | [STL](../cad/v22/6.1_CAR_linear_motion_slide_unit_kit_x2.stl) |
| 6.2 | `CAR_placa_carro_CF3` | 1 | CNC / water-jet cut plate, 3 mm | Carbon fibre | [STL](../cad/v22/6.2_CAR_placa_carro_CF3.stl) |
| 6.3 | `GR_motor_DC25_pinza` | 1 | MakeX kit part | — | [STL](../cad/v22/6.3_GR_motor_DC25_pinza.stl) |
| 6.4 | `GR_bloque_montaje_PETG` | 1 | FDM print | PETG | [STL](../cad/v22/6.4_GR_bloque_montaje_PETG.stl) |
| 6.5 | `GR_almohadilla_V_movil_TPU` | 1 | FDM print | TPU | [STL](../cad/v22/6.5_GR_almohadilla_V_movil_TPU.stl) |
| 6.6 | `GR_almohadilla_V_fija_TPU` | 1 | FDM print | TPU | [STL](../cad/v22/6.6_GR_almohadilla_V_fija_TPU.stl) |
| 6.7 | `GR_mordaza_fija_Al3` | 1 | CNC cut plate, 3 mm | Aluminium | [STL](../cad/v22/6.7_GR_mordaza_fija_Al3.stl) |
| 6.8 | `GR_mordaza_movil_Al3` | 1 | CNC cut plate, 3 mm | Aluminium | [STL](../cad/v22/6.8_GR_mordaza_movil_Al3.stl) |
| 6.9 | `GR_tabla_marco_CF3` | 1 | CNC / water-jet cut plate, 3 mm | Carbon fibre | [STL](../cad/v22/6.9_GR_tabla_marco_CF3.stl) |
| 6.10 | `GR_tornillo_avance_T8x8` | 1 | Purchase (T8 lead screw + nut) | Steel | [STL](../cad/v22/6.10_GR_tornillo_avance_T8x8.stl) |
| 6.11 | `GR_guia_D8_tubo_Al` | 1 | Cut to length (rod / tube) | Aluminium | [STL](../cad/v22/6.11_GR_guia_D8_tubo_Al.stl) |
| 6.12 | `GR_carro_tuerca_PETG` | 1 | FDM print | PETG | [STL](../cad/v22/6.12_GR_carro_tuerca_PETG.stl) |
| 6.13 | `CAR_belt_connector_kit` | 1 | MakeX kit / purchase | — | [STL](../cad/v22/6.13_CAR_belt_connector_kit.stl) |
| 6.14 | `GR_sensor_distancia_kit` | 1 | MakeX kit part | — | [STL](../cad/v22/6.14_GR_sensor_distancia_kit.stl) |
| 6.15 | `GR_bloque_extremo_fijo_PETG` | 1 | FDM print | PETG | [STL](../cad/v22/6.15_GR_bloque_extremo_fijo_PETG.stl) |
| 6.16 | `GR_bloque_extremo_libre_PETG` | 1 | FDM print | PETG | [STL](../cad/v22/6.16_GR_bloque_extremo_libre_PETG.stl) |
| 6.17 | `FLAG_receptor_mastil_PETG` | 1 | FDM print | PETG | [STL](../cad/v22/6.17_FLAG_receptor_mastil_PETG.stl) |
| 6.18 | `GR_acople_motor` | 1 | MakeX kit part | — | [STL](../cad/v22/6.18_GR_acople_motor.stl) |

### Summary by process

| Process | Lines |
| --- | --- |
| FDM print | 7 |
| MakeX kit part | 3 |
| MakeX kit / purchase | 2 |
| CNC / water-jet cut plate, 3 mm | 2 |
| CNC cut plate, 3 mm | 2 |
| Purchase (T8 lead screw + nut) | 1 |
| Cut to length (rod / tube) | 1 |

## Assembly

1. Carriage plate CF3 on the two linear-motion slide units; belt connector.
2. Mounting block PETG, frame CF3, end blocks, D8 aluminium guide, T8×8 lead screw with DC-25 and coupling.
3. Fixed and moving aluminium jaws with TPU V pads; distance sensor.
4. Flag-mast receptor (6.17) glued/screwed on the front edge of the mounting block (`x 181.5`, `y −64`).

## Inspection checkpoints

- [ ] Carriage travels 358 mm without binding
- [ ] Jaw opens/closes full stroke
- [ ] Receptor bore 8.3 mm aligned with the guide notch in the elevator lid
