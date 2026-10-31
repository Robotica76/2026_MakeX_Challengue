"""Estimate the robot's mass, centre of mass and inertia from the simulator GLB.

    python tools/scripts/mass_properties.py simulation/field3d/assets/storm_breaker_v22.glb \\
        simulation/field3d/robot_mass.json

The STEP has no material data, so this is an ESTIMATE:
  * each part's volume comes from its mesh (vertices merged so the solids close; the
    few open meshes, finned TPU rollers, use their bounding box x OPEN_FILL);
  * density from keywords in the part name (CF, PETG, TPU, PC, Al, steel, ...), with an
    effective fill factor for 3D-printed parts;
  * motors, battery and electronics use typical catalogue masses (KNOWN_MASS_KG),
    spread over their mesh volume.
The robot is taken as it enters the field: carriage down (the GLB has it 358 mm up)
and without the flag mast or reference objects. Replace the estimates with weighed
values as parts are built (T01-R3: <= 10 kg; T02 budget 9.2 kg).

Output (CAD frame, metres, kg): total mass, centre of mass, inertia tensor about the
centre of mass, and mass per subsystem prefix.
"""

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np

CARRIAGE_PREFIXES = ("CAR_", "GR_", "FLAG_receptor")
CARRIAGE_DROP_M = 0.358
EXCLUDE_PREFIXES = ("REF_", "FLAG_mastil", "FLAG_cabeza", "FLAG_pasador", "FLAG_ligas")
OPEN_FILL = 0.4            # finned roller in its bounding box (cylinder 0.785 x fins), estimate
PRINT_FILL = 0.45          # effective solid fraction of FDM parts (walls + ~30 % infill), estimate

# (keyword in part name, density g/cm^3), first match wins
DENSITY = [
    ("tornillo", 7.85), ("acero", 7.85), ("pasador", 7.85), ("bisagra", 7.85), ("munon", 7.85),
    ("rodamiento", 7.85),
    ("PETG", 1.27 * PRINT_FILL), ("impres", 1.27 * PRINT_FILL), ("nucleo", 1.27 * PRINT_FILL),
    ("TPU", 1.21 * 0.6),
    ("_CF", 1.55), ("CF1", 1.55), ("CF2", 1.55), ("CF3", 1.55),
    ("_PC", 1.20), ("PC_", 1.20),
    ("_Al", 2.70), ("Al3", 2.70), ("Al_", 2.70),
    ("PU", 1.20), ("velcro", 0.5), ("banda", 1.2),
    ("kit", 2.70 * 0.5),      # Makeblock aluminium kit parts: slotted / hollow profiles
    ("beam", 2.70 * 0.5),
]
DEFAULT_DENSITY = 1.2

# Typical catalogue masses (kg), estimates; matched by name prefix, split by volume.
KNOWN_MASS_KG = {
    "CH_motor_180_encoder_del_der": 0.075, "CH_motor_180_encoder_del_izq": 0.075,
    "CH_motor_180_encoder_tras_der": 0.075, "CH_motor_180_encoder_tras_izq": 0.075,
    "INT_motor_DC37": 0.17, "TW_motor_DC37": 0.17, "ELV_motor_DC37": 0.17,
    "INT_LR_motor_DC25": 0.08, "INT_UR_motor_DC25_elevacion": 0.08, "INT_UR_motor_DC25_giro": 0.08,
    "CN_motor_DC25": 0.08, "TW_motor_DC25": 0.08, "GR_motor_DC25": 0.08,
    "SH_brushless_kit_horario": 0.045, "SH_brushless_kit_antihorario": 0.045, "SH_brushless_ESC": 0.03,
    "SH_servo_MS12A": 0.055,
    "ELEC_NovaPi": 0.12, "ELEC_bateria": 0.33, "ELEC_power_expansion": 0.10, "ELEC_drivers": 0.05,
    "ELV_AI_camera": 0.06, "GR_sensor_distancia": 0.02, "TW_S2_sensor": 0.01,
}


def density_for(name: str) -> float:
    for key, rho in DENSITY:
        if key in name:
            return rho
    return DEFAULT_DENSITY


def known_group(name: str):
    return next((k for k in KNOWN_MASS_KG if name.startswith(k)), None)


def part_meshes(glb: Path):
    import trimesh
    scene = trimesh.load(glb)
    for name in scene.graph.nodes_geometry:
        if name.startswith(EXCLUDE_PREFIXES):
            continue
        transform, geom = scene.graph[name]
        mesh = scene.geometry[geom].copy()
        mesh.apply_transform(transform)
        if name.startswith(CARRIAGE_PREFIXES):
            mesh.apply_translation((0, 0, -CARRIAGE_DROP_M))
        mesh.merge_vertices(merge_tex=True, merge_norm=True)
        if not mesh.is_watertight:
            import trimesh
            lo, hi = mesh.bounds
            box = trimesh.creation.box(extents=hi - lo)
            box.apply_translation((lo + hi) / 2)
            mesh, fill = box, OPEN_FILL
        else:
            fill = 1.0
        if mesh.volume < 0:
            mesh.invert()
        yield name, mesh, fill


def estimate(glb: Path) -> dict:
    parts = list(part_meshes(glb))
    # volumes of each known-mass group, to spread the catalogue mass
    group_volume = collections.defaultdict(float)
    for name, mesh, fill in parts:
        g = known_group(name)
        if g:
            group_volume[g] += mesh.volume * fill
    total_m, first_moment = 0.0, np.zeros(3)
    records = []
    for name, mesh, fill in parts:
        volume = mesh.volume * fill                       # m^3
        g = known_group(name)
        if g:
            mass = KNOWN_MASS_KG[g] * volume / group_volume[g]
            source = "catalogue"
        else:
            mass = density_for(name) * 1000.0 * volume    # g/cm^3 -> kg/m^3
            source = "density"
        props = mesh.mass_properties                      # unit density
        com = np.asarray(props["center_mass"])
        inertia = np.asarray(props["inertia"]) / props["mass"] * mass if props["mass"] > 0 else np.zeros((3, 3))
        records.append((name, mass, com, inertia, source))
        total_m += mass
        first_moment += mass * com
    com = first_moment / total_m
    tensor = np.zeros((3, 3))
    for _, mass, c, inertia, _ in records:
        d = c - com
        tensor += inertia + mass * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
    by_prefix = collections.defaultdict(float)
    for name, mass, *_ in records:
        by_prefix[name.split("_")[0]] += mass
    return {
        "note": "ESTIMATE from mesh volumes, keyword densities and catalogue masses (tools/scripts/mass_properties.py); "
                "robot as it enters the field (carriage down, no flag mast). Weigh the robot to replace it.",
        "frame": "CAD frame, metres: +y forward (intake), +x right (gripper), +z up, origin on the floor under the footprint centre",
        "mass_kg": round(total_m, 3),
        "center_of_mass_m": [round(float(c), 4) for c in com],
        "inertia_kg_m2": [[round(float(v), 5) for v in row] for row in tensor],
        "mass_by_prefix_kg": {k: round(v, 3) for k, v in sorted(by_prefix.items(), key=lambda kv: -kv[1])},
        "catalogue_parts": sorted(KNOWN_MASS_KG),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("glb", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    result = estimate(args.glb)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    c = result["center_of_mass_m"]
    print(f"mass {result['mass_kg']:.2f} kg, centre of mass x {c[0] * 1000:.0f} y {c[1] * 1000:.0f} "
          f"z {c[2] * 1000:.0f} mm, Izz {result['inertia_kg_m2'][2][2]:.3f} kg m^2")
    print("by prefix:", ", ".join(f"{k} {v:.2f}" for k, v in result["mass_by_prefix_kg"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
