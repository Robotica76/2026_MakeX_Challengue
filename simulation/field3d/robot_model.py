"""Robot CAD mesh for the 3D viewer: one node per CAD part, grouped into what moves.

The GLB (tools/scripts/step_to_glb.py) keeps the CAD frame in metres: +y forward
(intake), +x right (gripper), +z up, origin on the floor under the footprint
centre. robot_model.json says which parts belong to each wheel, to the elevator
carriage, to the intake lift, to each spinning roller / gear set, and to the flag
mast, so a new CAD revision only needs a new GLB and, if part names change, an
edited JSON.

Mesh loading (load_parts) uses trimesh only, so it can be tested without a window;
RobotModel builds the Panda3D scene graph.
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = HERE / "robot_model.json"


@dataclass
class Part:
    name: str
    vertices: np.ndarray   # (n, 3) float32, CAD frame, metres
    normals: np.ndarray    # (n, 3) float32
    faces: np.ndarray      # (m, 3) uint32
    rgba: tuple            # 0..1


def load_model_spec(path: Path = DEFAULT_MODEL) -> dict:
    spec = json.loads(Path(path).read_text())
    spec["asset_path"] = (Path(path).parent / spec["asset"]).resolve()
    return spec


def _rgba(geometry) -> tuple:
    visual = geometry.visual
    color = None
    material = getattr(visual, "material", None)
    if material is not None:
        color = getattr(material, "baseColorFactor", None)
        if color is None:
            color = getattr(material, "main_color", None)
    if color is None and hasattr(visual, "main_color"):
        color = visual.main_color
    if color is None:
        return (0.6, 0.6, 0.6, 1.0)
    color = np.asarray(color, dtype=float)
    if color.max() > 1.0:
        color = color / 255.0
    return tuple(float(c) for c in color[:4]) if len(color) >= 4 else (*color[:3], 1.0)


def load_parts(asset: Path) -> List[Part]:
    """Every CAD part with its world transform applied (still in the CAD frame)."""
    import trimesh
    scene = trimesh.load(asset)
    parts = []
    for name in scene.graph.nodes_geometry:
        transform, geom_name = scene.graph[name]
        mesh = scene.geometry[geom_name]
        vertices = trimesh.transform_points(mesh.vertices, transform).astype(np.float32)
        with np.errstate(all="ignore"):   # some CAD faces are degenerate (zero area)
            normals = np.nan_to_num(np.asarray(mesh.vertex_normals, dtype=np.float64), posinf=0.0, neginf=0.0)
            normals = normals @ np.asarray(transform)[:3, :3].T
            length = np.linalg.norm(normals, axis=1, keepdims=True)
            normals = np.where(length > 1e-9, normals / np.where(length > 1e-9, length, 1.0), (0.0, 0.0, 1.0))
        normals = normals.astype(np.float32)
        parts.append(Part(name, vertices, normals, mesh.faces.astype(np.uint32), _rgba(mesh)))
    return parts


def classify(name: str, spec: dict) -> Dict[str, Optional[str]]:
    """Which groups a part belongs to: wheel name, spinner name (or None), carriage,
    intake lift, mast, hidden."""
    wheel = next((w for w, info in spec["wheels"].items()
                  if any(name.startswith(p) for p in info["parts"])), None)
    spinner = next((sp["name"] for sp in spec.get("spinners", []) if name in sp["parts"]), None)
    return {
        "wheel": wheel,
        "spinner": spinner,
        "carriage": any(name.startswith(p) for p in spec["carriage"]["prefixes"]),
        "intake_lift": name in spec.get("intake_lift", {}).get("parts", []),
        "jaw": name in spec.get("gripper_jaw", {}).get("parts", []),
        "mast": any(name.startswith(p) for p in spec["mast"]["prefixes"]),
        "hidden": any(name.startswith(p) for p in spec.get("hide_prefixes", [])),
    }


def spinner_centres(parts: List[Part], spec: dict) -> Dict[str, tuple]:
    """Rotation centre (m, CAD frame) of each spinner: bounding-box centre of its parts."""
    by_name = {p.name: p for p in parts}
    out = {}
    for sp in spec.get("spinners", []):
        verts = [by_name[n].vertices for n in sp["parts"] if n in by_name]
        if verts:
            v = np.vstack(verts)
            out[sp["name"]] = tuple(float(c) for c in (v.min(0) + v.max(0)) / 2)
    return out


def _geom_node(part: Part):
    from panda3d.core import (Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat)
    vdata = GeomVertexData(part.name, GeomVertexFormat.get_v3n3(), Geom.UH_static)
    vdata.unclean_set_num_rows(len(part.vertices))
    interleaved = np.hstack([part.vertices, part.normals]).astype(np.float32)
    memoryview(vdata.modify_array(0)).cast("B")[:] = interleaved.tobytes()
    tris = GeomTriangles(Geom.UH_static)
    tris.set_index_type(Geom.NT_uint32)
    index = tris.modify_vertices()
    index.unclean_set_num_rows(part.faces.size)
    memoryview(index).cast("B")[:] = part.faces.astype(np.uint32).tobytes()
    geom = Geom(vdata)
    geom.add_primitive(tris)
    node = GeomNode(part.name)
    node.add_geom(geom)
    return node


class RobotModel:
    """Panda3D node tree:

        root (pose on the field)
          body              static parts
          wheel_<name>      pivot at the wheel axle, spins about +x (CAD right axis)
          carriage          elevator carriage, gripper, mast (moves in z)
            mast            flag mast + flag (Modification Stage)
          intake_lift       intake head on its rails (moves in z)
            spin_<name>     spinners whose parent is the intake lift
          spin_<name>       roller / gear / wheel sets, pivot at their centre
    """

    def __init__(self, spec: Optional[dict] = None, parts: Optional[List[Part]] = None):
        from panda3d.core import NodePath, TransparencyAttrib
        self.spec = spec or load_model_spec()
        parts = parts if parts is not None else load_parts(self.spec["asset_path"])
        self.root = NodePath(self.spec["name"])
        self.body = self.root.attach_new_node("body")
        self.carriage = self.root.attach_new_node("carriage")
        self.mast = self.carriage.attach_new_node("mast")
        self.intake_lift = self.root.attach_new_node("intake_lift")
        self.jaw = self.carriage.attach_new_node("gripper_jaw")
        centres = spinner_centres(parts, self.spec)
        self.spinners = {}
        self.spinner_specs = {}
        for sp in self.spec.get("spinners", []):
            if sp["name"] not in centres:
                continue
            parent = self.intake_lift if sp.get("parent") == "intake_lift" else self.root
            pivot = parent.attach_new_node(f"spin_{sp['name']}")
            pivot.set_pos(*centres[sp["name"]])
            self.spinners[sp["name"]] = pivot
            self.spinner_specs[sp["name"]] = sp
        self.wheels = {}
        for wheel, info in self.spec["wheels"].items():
            pivot = self.root.attach_new_node(f"wheel_{wheel}")
            pivot.set_pos(*(c / 1000.0 for c in info["center_mm"]))
            self.wheels[wheel] = pivot
        self.part_groups: Dict[str, Dict[str, Optional[str]]] = {}
        for part in parts:
            groups = classify(part.name, self.spec)
            self.part_groups[part.name] = groups
            if groups["hidden"]:
                continue
            if groups["wheel"]:
                parent = self.wheels[groups["wheel"]]
            elif groups["spinner"] in self.spinners:
                parent = self.spinners[groups["spinner"]]
            elif groups["jaw"]:
                parent = self.jaw
            elif groups["mast"]:
                parent = self.mast
            elif groups["carriage"]:
                parent = self.carriage
            elif groups["intake_lift"]:
                parent = self.intake_lift
            else:
                parent = self.body
            node = parent.attach_new_node(_geom_node(part))
            if groups["wheel"]:  # vertices are in the CAD frame; the pivot sits at the axle
                node.set_pos(*(-c / 1000.0 for c in self.spec["wheels"][groups["wheel"]]["center_mm"]))
            elif groups["spinner"] in self.spinners:
                node.set_pos(*(-c for c in centres[groups["spinner"]]))
            node.set_color(*part.rgba)
            if part.rgba[3] < 0.99:
                node.set_transparency(TransparencyAttrib.M_alpha)
        self.carriage_mm = 0.0
        self.intake_lift_mm = 0.0
        self.set_carriage(0.0)
        self.set_intake_lift(0.0)
        self.show_mast(False)

    # --- articulation -------------------------------------------------------------
    def set_pose(self, x_mm: float, y_mm: float, theta_rad: float) -> None:
        """Simulator pose: field mm, theta CCW from +x with the robot forward axis.
        The CAD forward axis is +y, hence the -90 degree heading offset."""
        self.root.set_pos(x_mm / 1000.0, y_mm / 1000.0, 0.0)
        self.root.set_h(math.degrees(theta_rad) - 90.0)

    def set_wheel_angles(self, degrees: Dict[str, float]) -> None:
        """Wheel angle per wheel, positive = rolling forward (pitch about the +x axle)."""
        for wheel, angle in degrees.items():
            if wheel in self.wheels:
                self.wheels[wheel].set_p(angle)

    def set_carriage(self, height_mm: float) -> None:
        """Carriage height above its lowest position, 0..travel_mm."""
        info = self.spec["carriage"]
        self.carriage_mm = max(0.0, min(info["travel_mm"], height_mm))
        self.carriage.set_z((self.carriage_mm - info["asset_height_mm"]) / 1000.0)

    def set_gripper_jaw(self, closure_mm: float) -> None:
        """Moving jaw closure from fully open (mm)."""
        self.jaw.set_y(max(0.0, closure_mm) / 1000.0)

    def set_intake_lift(self, height_mm: float) -> None:
        """Intake head height above its lowest position (mm, clamped by the simulation)."""
        self.intake_lift_mm = max(0.0, height_mm)
        self.intake_lift.set_z(self.intake_lift_mm / 1000.0)

    def set_spinner_angles(self, mechanism_angles: Dict[str, float]) -> None:
        """mechanism_angles: angle (deg) per mechanism (e.g. "intake_rollers"); each
        spinner turns by angle x its ratio about its axis."""
        for name, pivot in self.spinners.items():
            sp = self.spinner_specs[name]
            angle = mechanism_angles.get(sp["mechanism"], 0.0) * sp.get("ratio", 1.0)
            axis = sp.get("axis", "x")
            if axis == "x":
                pivot.set_p(angle)
            elif axis == "y":
                pivot.set_r(angle)
            else:
                pivot.set_h(angle)

    def show_mast(self, visible: bool) -> None:
        self.mast_visible = bool(visible)
        self.mast.show() if visible else self.mast.hide()
