# Shooter Manufacturing

Manufacturing plan for revision v22, derived from the CAD part names. **Nothing has been fabricated yet;** processes and materials are the CAD intent and must be confirmed against stock, kit contents, and the released [drawings](../drawings/README.md).

## v22 · Bill of materials and process

| No. | Part (CAD name) | Qty | Process | Material | STL |
| --- | --- | --- | --- | --- | --- |
| 7.1 | `SH_friction_wheel_D45x19_5_kit_x2` | 2 | MakeX kit / purchase | — | [STL](../cad/v22/7.1_SH_friction_wheel_D45x19_5_kit_x2.stl) |
| 7.2 | `SH_placa_lateral_CF3_der` | 1 | CNC / water-jet cut plate, 3 mm | Carbon fibre | [STL](../cad/v22/7.2_SH_placa_lateral_CF3_der.stl) |
| 7.3 | `SH_placa_lateral_CF3_izq` | 1 | CNC / water-jet cut plate, 3 mm | Carbon fibre | [STL](../cad/v22/7.3_SH_placa_lateral_CF3_izq.stl) |
| 7.4 | `RIG_base_lanzador_CF3` | 1 | CNC / water-jet cut plate, 3 mm | Carbon fibre | [STL](../cad/v22/7.4_RIG_base_lanzador_CF3.stl) |
| 7.5 | `RIG_postes_lanzador_tubo_CF_16_x2` | 2 | Cut to length from CF tube | Carbon fibre tube | [STL](../cad/v22/7.5_RIG_postes_lanzador_tubo_CF_16_x2.stl) |
| 7.6 | `SH_separadores_Al_D8_x4` | 4 | Cut to length (rod / tube) | Aluminium | [STL](../cad/v22/7.6_SH_separadores_Al_D8_x4.stl) |
| 7.7 | `SH_capucha_inferior_PC2mm_R82` | 1 | Cut / bend sheet | Polycarbonate | [STL](../cad/v22/7.7_SH_capucha_inferior_PC2mm_R82.stl) |
| 7.8 | `SH_servo_MS12A_kit` | 1 | MakeX kit part | — | [STL](../cad/v22/7.8_SH_servo_MS12A_kit.stl) |
| 7.9 | `SH_brushless_kit_antihorario` | 1 | MakeX kit part | — | [STL](../cad/v22/7.9_SH_brushless_kit_antihorario.stl) |
| 7.10 | `SH_brushless_kit_horario` | 1 | MakeX kit part | — | [STL](../cad/v22/7.10_SH_brushless_kit_horario.stl) |
| 7.11 | `SH_brushless_ESC_kit_x2` | 2 | MakeX kit part | — | [STL](../cad/v22/7.11_SH_brushless_ESC_kit_x2.stl) |
| 7.12 | `SH_capucha_costillas_PETG_x3` | 3 | FDM print | PETG | [STL](../cad/v22/7.12_SH_capucha_costillas_PETG_x3.stl) |
| 7.13 | `SH_capucha_grip_TPU` | 1 | FDM print | TPU | [STL](../cad/v22/7.13_SH_capucha_grip_TPU.stl) |
| 7.14 | `SH_friction_wheel_ring_D28x7_kit_x2` | 2 | MakeX kit / purchase | — | [STL](../cad/v22/7.14_SH_friction_wheel_ring_D28x7_kit_x2.stl) |
| 7.15 | `SH_guarda_superior_PC` | 1 | Cut / bend sheet | Polycarbonate | [STL](../cad/v22/7.15_SH_guarda_superior_PC.stl) |
| 7.16 | `SH_brushless_motor_bracket_kit_x2` | 2 | MakeX kit part | — | [STL](../cad/v22/7.16_SH_brushless_motor_bracket_kit_x2.stl) |
| 7.17 | `SH_bisagra_aleta_D3` | 1 | Cut to length from rod | Steel | [STL](../cad/v22/7.17_SH_bisagra_aleta_D3.stl) |
| 7.18 | `SH_aleta_capucha_PC2mm_servo` | 1 | MakeX kit part | — | [STL](../cad/v22/7.18_SH_aleta_capucha_PC2mm_servo.stl) |

### Summary by process

| Process | Lines |
| --- | --- |
| MakeX kit part | 6 |
| CNC / water-jet cut plate, 3 mm | 3 |
| MakeX kit / purchase | 2 |
| Cut / bend sheet | 2 |
| FDM print | 2 |
| Cut to length from CF tube | 1 |
| Cut to length (rod / tube) | 1 |
| Cut to length from rod | 1 |

## Assembly

1. CF 16×16 posts on the left rail and the CF3 base.
2. Side plates CF3 with the D8 aluminium spacers.
3. Two D45 friction wheels with rings on the two brushless motors and brackets; ESCs.
4. Lower hood PC 2 mm R82.5 with TPU grip and ribs; flap on hinge driven by servo MS-12A; upper guard.

## Inspection checkpoints

- [ ] Wheel–hood gap matches the CAD (ball squeeze)
- [ ] Flap travel 215° ↔ 198°
- [ ] Exit path clear of the robot in both hood positions
- [ ] Everything below z 543
