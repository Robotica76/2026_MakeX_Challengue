# Ball Storage Manufacturing

Manufacturing plan for revision v22, derived from the CAD part names. **Nothing has been fabricated yet;** processes and materials are the CAD intent and must be confirmed against stock, kit contents, and the released [drawings](../drawings/README.md).

## v22 · Bill of materials and process

| No. | Part (CAD name) | Qty | Process | Material | STL |
| --- | --- | --- | --- | --- | --- |
| 8.1 | `CN_paredes_canasta_PC_1` | 1 | Cut / bend sheet | Polycarbonate | [STL](../cad/v22/8.1_CN_paredes_canasta_PC_1.stl) |
| 8.2 | `CN_rodillo_alimentador_TPU_D30` | 1 | FDM print | TPU | [STL](../cad/v22/8.2_CN_rodillo_alimentador_TPU_D30.stl) |
| 8.3 | `CN_piso_canasta_PC_1_2` | 1 | Cut / bend sheet | Polycarbonate | [STL](../cad/v22/8.3_CN_piso_canasta_PC_1_2.stl) |
| 8.4 | `CN_motor_DC25_200rpm_alimentador_3a1` | 1 | MakeX kit part | — | [STL](../cad/v22/8.4_CN_motor_DC25_200rpm_alimentador_3a1.stl) |
| 8.5 | `CN_engrane_48T_kit_motor_alimentador` | 1 | MakeX kit part | — | [STL](../cad/v22/8.5_CN_engrane_48T_kit_motor_alimentador.stl) |
| 8.6 | `CN_soporte_alimentador_y_motor_PETG` | 1 | FDM print | PETG | [STL](../cad/v22/8.6_CN_soporte_alimentador_y_motor_PETG.stl) |
| 8.7 | `CN_eje_alimentador_D8_Al` | 1 | Cut to length (rod / tube) | Aluminium | [STL](../cad/v22/8.7_CN_eje_alimentador_D8_Al.stl) |
| 8.8 | `CN_engrane_16T_kit_alimentador` | 1 | MakeX kit / purchase | — | [STL](../cad/v22/8.8_CN_engrane_16T_kit_alimentador.stl) |
| 8.9 | `CN_buje_alimentador_en_pared_trasera` | 1 | FDM print | PETG | [STL](../cad/v22/8.9_CN_buje_alimentador_en_pared_trasera.stl) |

### Summary by process

| Process | Lines |
| --- | --- |
| FDM print | 3 |
| Cut / bend sheet | 2 |
| MakeX kit part | 2 |
| Cut to length (rod / tube) | 1 |
| MakeX kit / purchase | 1 |

## Assembly

1. PC 1.2 floor sloped 10 % toward the launcher (and a V slope toward the lane), PC 1 walls.
2. Feed roller TPU D30 on an 8 mm aluminium axle, bushing in the rear wall.
3. DC-25 under the basket floor with 48T → 16T (3:1, 0.94 m/s at the roller) on the PETG support.

## Inspection checkpoints

- [ ] Roller protrudes 12 mm above the floor
- [ ] Floor slot leaves the 16T and the support free
- [ ] Balls roll to the roller from both rows
