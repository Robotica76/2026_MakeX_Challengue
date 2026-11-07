# Development and support tools

Utilities that support development; **not** robot code.

| Directory | Content |
| --- | --- |
| [scripts](scripts/README.md) | `bundle_for_mblock.py` (one-file upload), `python_to_mblock.py` (Python → mBlock blocks), `step_to_glb.py` (CAD → 3D simulator mesh), `mass_properties.py` (mass / CG / inertia estimate) |
| [calibration](calibration/README.md) | Calibration procedures and the constants they set |
| [data_analysis](data_analysis/README.md) | Robot-data analysis (none yet; simulation analysis is in `simulation/analysis`) |

The CAD scripts that generated the v22 STEP, STL, manual and documentation are kept with the
assembly: [`mechanical/assemblies/full_robot/v22/source`](../mechanical/assemblies/full_robot/v22/README.md).
