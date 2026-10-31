# Flag System CAD

Reserve local space for future component and subsystem concepts only if verified tasks justify them. TBD: contact frame, mounting references, clearances, and revisions. Full-robot integration stays in [full_robot](../../assemblies/full_robot/README.md).

## Revisions

| Revision | Parts | Integration |
| --- | --- | --- |
| [v22](v22/) | Removable flag mast, printable STL (see below) | [Storm Breaker v22](../../assemblies/full_robot/v22/README.md) |

### v22 · Removable flag mast

Installed during the Modification Stage; before that only the receptor is on the
robot. The CF tube enters the receptor on the gripper mounting block (rises and
lowers with the elevator carriage), is pinned with an R clip, and passes through a
D10 guide hole in the elevator tower lid. The C-shaped head holds the flagpole
(< 10 × 10 mm) against its spine with a crossed rubber band. To hang the flag:
raise the carriage, put the field bar inside the flag loop, lower the carriage, and
strafe toward `−x` so the pole slides out of the C. Source: comments in
[`robot_v22.py`](../../assemblies/full_robot/v22/source/robot_v22.py).

| File | Part | Material | Where |
| --- | --- | --- | --- |
| `FLAG_receptor_mastil_PETG_(va_en_el_robot).stl` | Mast receptor | PETG print | On the robot from inspection |
| `FLAG_mastil_tubo_CF_8x6.stl` | Mast tube 8 × 6 mm | Carbon fiber tube | Added in Modification Stage |
| `FLAG_cabeza_C_PETG.stl` | C-shaped head | PETG print | Added in Modification Stage |
| `FLAG_pasador_R_D3.stl` | R clip, D3 | Steel | Added in Modification Stage |
| `FLAG_ligas_x2.stl` | 2 rubber bands (reference shape) | Rubber | Added in Modification Stage |

Heights in CAD: mast top at about 700 mm with the carriage down and 1062.6 mm with the
carriage up; flag loop up to 1128.3 mm. Footprint stays 499.5 × 499.0 mm (T16-R5).
