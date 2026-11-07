# Flag System CAD

Removable flag mast, installed during the Modification Stage (subsystem 9). The receptor that stays on the robot is part 6.17 in [gripper](../../gripper/cad/README.md).

## Revisions

| Revision | Parts | Integration |
| --- | --- | --- |
| [v22](v22/) | 4 numbered STL (this page) | [Storm Breaker v22](../../assemblies/full_robot/v22/README.md) |

## v22 · Numbered parts

File name = `<subsystem>.<part>_<CAD name>.stl`, the same numbering as the [assembly manual](../../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf) (sheet 11). Within a subsystem, part 1 is the largest by volume.

- Every STL is exported in the **robot frame at its assembled position** (mm; origin on the floor at the centre of the 500 × 500 envelope; `+y` forward, `+x` right, `+z` up), so the files drop into place together. Re-orient each part on the build plate before printing.
- Mesh tolerance 0.1 mm linear / 0.2 rad angular. Use the STEP in [full_robot/v22](../../assemblies/full_robot/v22/cad/) for engineering changes.
- Kit parts (motors, wheels, beams, gears, belts) and electronics are included only as **reference geometry** for fit checks; do not print them.
- A file whose name ends in `_xN` holds N identical instances in one mesh.

### 9. Flag mast (Modification Stage) (4 parts)

| No. | File | Size X × Y × Z (mm) | Process |
| --- | --- | --- | --- |
| 9.1 | [`9.1_FLAG_cabeza_C_PETG.stl`](v22/9.1_FLAG_cabeza_C_PETG.stl) | 25 × 30 × 52.6 | FDM print |
| 9.2 | [`9.2_FLAG_mastil_tubo_CF_8x6.stl`](v22/9.2_FLAG_mastil_tubo_CF_8x6.stl) | 8 × 8 × 537 | Cut to length from CF tube |
| 9.3 | [`9.3_FLAG_ligas_x2.stl`](v22/9.3_FLAG_ligas_x2.stl) | 1.5 × 19 × 52 | Purchase |
| 9.4 | [`9.4_FLAG_pasador_R_D3.stl`](v22/9.4_FLAG_pasador_R_D3.stl) | 18 × 3 × 3 | Purchase (R clip) |

