# Flag System Manufacturing

Manufacturing plan for revision v22, derived from the CAD part names. **Nothing has been fabricated yet;** processes and materials are the CAD intent and must be confirmed against stock, kit contents, and the released [drawings](../drawings/README.md).

## v22 · Bill of materials and process

| No. | Part (CAD name) | Qty | Process | Material | STL |
| --- | --- | --- | --- | --- | --- |
| 9.1 | `FLAG_cabeza_C_PETG` | 1 | FDM print | PETG | [STL](../cad/v22/9.1_FLAG_cabeza_C_PETG.stl) |
| 9.2 | `FLAG_mastil_tubo_CF_8x6` | 1 | Cut to length from CF tube | Carbon fibre tube | [STL](../cad/v22/9.2_FLAG_mastil_tubo_CF_8x6.stl) |
| 9.3 | `FLAG_ligas_x2` | 2 | Purchase | Rubber band | [STL](../cad/v22/9.3_FLAG_ligas_x2.stl) |
| 9.4 | `FLAG_pasador_R_D3` | 1 | Purchase (R clip) | Steel | [STL](../cad/v22/9.4_FLAG_pasador_R_D3.stl) |

### Summary by process

| Process | Lines |
| --- | --- |
| FDM print | 1 |
| Cut to length from CF tube | 1 |
| Purchase | 1 |
| Purchase (R clip) | 1 |

## Assembly

Modification Stage (60 s): insert the CF 8×6 tube (9.2) through the lid notch into the receptor, fit the R clip (9.4), put the flag pole in the C head (9.1) and close it with the 2 rubber bands (9.3).

## Inspection checkpoints

- [ ] Pole (< 10 × 10 mm) held by the bands against the spine
- [ ] Mast top 704 mm (carriage down) / 1062 mm (up)
- [ ] Robot + mast ≤ 10 kg (CAD 9.92 kg)
