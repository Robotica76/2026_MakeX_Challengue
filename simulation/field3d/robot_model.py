"""Robot CAD mesh for the 3D viewer: one node per CAD part, grouped into what moves.

The GLB (tools/scripts/step_to_glb.py) keeps the CAD frame in metres: +y forward
(intake), +x right (gripper), +z up, origin on the floor under the footprint
centre. robot_model.json says which parts belong to each wheel, to the elevator
carriage, and to the flag mast, so a new CAD revision only needs a new GLB and,
if part names change, an edited JSON.

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
    """Which groups a part belongs to: wheel name (or None), carriage, mast, hidden."""
    wheel = next((w for w, info in spec["wheels"].items()
                  if any(name.startswith(p) for p in info["parts"])), None)
    return {
        "wheel": wheel,
        "carriage": any(name.startswith(p) for p in spec["carriage"]["prefixes"]),
        "mast": any(name.startswith(p) for p in spec["mast"]["prefixes"]),
        "hidden": any(name.startswith(p) for p in spec.get("hide_prefixes", [])),
    }


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
    """

    def __init__(self, spec: Optional[dict] = None, parts: Optional[List[Part]] = None):
        from panda3d.core import NodePath, TransparencyAttrib
        self.spec = spec or load_model_spec()
        parts = parts if parts is not None else load_parts(self.spec["asset_path"])
        self.root = NodePath(self.spec["name"])
        self.body = self.root.attach_new_node("body")
        self.carriage = self.root.attach_new_node("carriage")
        self.mast = self.carriage.attach_new_node("mast")
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
            elif groups["mast"]:
                parent = self.mast
            elif groups["carriage"]:
                parent = self.carriage
            else:
                parent = self.body
            node = parent.attach_new_node(_geom_node(part))
            if groups["wheel"]:  # vertices are in the CAD frame; the pivot sits at the axle
                node.set_pos(*(-c / 1000.0 for c in self.spec["wheels"][groups["wheel"]]["center_mm"]))
            node.set_color(*part.rgba)
            if part.rgba[3] < 0.99:
                node.set_transparency(TransparencyAttrib.M_alpha)
        self.carriage_mm = 0.0
        self.set_carriage(0.0)
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

    def show_mast(self, visible: bool) -> None:
        self.mast_visible = bool(visible)
        self.mast.show() if visible else self.mast.hide()
