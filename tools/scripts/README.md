# Development Scripts

Reserve this directory for justified future support automation, such as organizing development artifacts or preparing experiment records. It must not host production robot control or firmware.

TBD before adding any utility: purpose, owner, inputs/outputs, execution requirements, permissions, failure behavior, and verification plan.

| Script | Purpose | Inputs / outputs | Requirements | Verification |
| --- | --- | --- | --- | --- |
| [`step_to_glb.py`](step_to_glb.py) | Convert a robot STEP assembly into the GLB mesh used by the [3D simulator](../../simulation/field3d/README.md) | `.step` or `.step.zip` → `.glb` (metres, CAD axes, one node per part); prints part count, size, parts per prefix | [`requirements-cad.txt`](requirements-cad.txt) (`cascadio`, `trimesh`) | `simulation/field3d/test_field3d.py` checks the generated asset against the v22 CAD |
