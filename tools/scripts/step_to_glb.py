"""Convert a robot STEP assembly (or a .step.zip from mechanical/) into a GLB mesh
for the 3D simulator, keeping one named node per CAD part.

    python tools/scripts/step_to_glb.py \\
        mechanical/assemblies/full_robot/v22/cad/Robot_StormBreaker_v22_con_mastil_y_bandera_carro_arriba.step.zip \\
        simulation/field3d/assets/storm_breaker_v22.glb

Units: the GLB is in metres with the CAD axes kept (z up). Needs `cascadio` and
`trimesh` (tools/scripts/requirements-cad.txt). Prints the part count, the size
of the model and the parts per name prefix so a renamed or missing subsystem is
easy to spot.
"""

import argparse
import collections
import sys
import tempfile
import zipfile
from pathlib import Path


def extract_step(path: Path, workdir: Path) -> Path:
    if path.suffix.lower() != ".zip":
        return path
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith((".step", ".stp"))]
        if len(names) != 1:
            raise SystemExit(f"{path.name}: expected one .step inside, found {names}")
        target = workdir / Path(names[0]).name
        with zf.open(names[0]) as src, open(target, "wb") as dst:
            while True:
                chunk = src.read(1 << 20)
                if not chunk:
                    break
                dst.write(chunk)
        return target


def summarize(glb: Path) -> None:
    import trimesh
    scene = trimesh.load(glb)
    nodes = list(scene.graph.nodes_geometry)
    prefixes = collections.Counter(n.split("_")[0] for n in nodes)
    size_mm = (scene.bounds[1] - scene.bounds[0]) * 1000
    faces = sum(len(g.faces) for g in scene.geometry.values())
    print(f"{glb.name}: {len(nodes)} parts, {faces} triangles, "
          f"size {size_mm[0]:.1f} x {size_mm[1]:.1f} x {size_mm[2]:.1f} mm, {glb.stat().st_size / 1e6:.1f} MB")
    print("parts per prefix:", ", ".join(f"{k} {v}" for k, v in sorted(prefixes.items())))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", type=Path, help=".step/.stp file or a .zip containing one")
    parser.add_argument("glb", type=Path, help="output .glb")
    parser.add_argument("--tolerance", type=float, default=0.5,
                        help="linear tessellation tolerance in mm (default 0.5; larger = smaller file)")
    args = parser.parse_args(argv)

    import cascadio
    args.glb.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        step = extract_step(args.step, Path(tmp))
        cascadio.step_to_glb(str(step), str(args.glb), args.tolerance, 0.5)
    summarize(args.glb)
    return 0


if __name__ == "__main__":
    sys.exit(main())
