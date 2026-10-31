"""3D field built from the 2D layout (simulation/field2d/field_layout.py).

Every element keeps its 2D footprint and its top height `z`:
  zone, slot      -> coloured floor patch
  obstacle        -> solid box or cylinder from the floor to z
  movable         -> the fortress, a box to z (semi-transparent)
  overhead        -> a slab at its height: robots drive under it
  no_touch        -> the X mark, a plate between 654 mm and z (field_layout comment)
  prop            -> cube (box) or cone on top of the strategy area
The perimeter frame uses fl.FRAME_HEIGHT and is drawn semi-transparent so the
cameras can see through it. Shapes are as accurate as field_layout, which marks
estimated placements; it is a visual aid, not a collision model.
"""

import math
from typing import List

import numpy as np

import field_layout as fl
from robot_model import Part, _geom_node

MM = 1 / 1000.0
FLOOR_RGBA = (0.80, 0.82, 0.85, 1.0)
ALLIANCE_RGBA = {"red": (0.86, 0.33, 0.33, 1.0), "blue": (0.30, 0.47, 0.86, 1.0), "neutral": (0.55, 0.57, 0.62, 1.0)}
FRAME_RGBA = (0.35, 0.37, 0.42, 0.25)
FRAME_T = 30.0          # mm, drawn thickness of the perimeter frame (visual only)
OVERHEAD_T = 30.0       # mm, slab thickness for overhead elements
X_MARK_BOTTOM = 654.0   # mm, field_layout: "X spans 654-947 mm"


def _quad_box(x0, y0, z0, x1, y1, z1):
    """24 vertices (flat normals) and 12 triangles of an axis-aligned box, metres."""
    faces = [
        ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (0, 0, 1)),
        ((x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0), (0, 0, -1)),
        ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), (0, -1, 0)),
        ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (0, 1, 0)),
        ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (-1, 0, 0)),
        ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (1, 0, 0)),
    ]
    verts, norms, tris = [], [], []
    for a, b, c, d, n in faces:
        base = len(verts)
        verts += [a, b, c, d]
        norms += [n] * 4
        tris += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
    return verts, norms, tris


def box(name, cx, cy, w, d, z0, z1, rgba) -> Part:
    v, n, t = _quad_box((cx - w / 2) * MM, (cy - d / 2) * MM, z0 * MM, (cx + w / 2) * MM, (cy + d / 2) * MM, z1 * MM)
    return Part(name, np.array(v, np.float32), np.array(n, np.float32), np.array(t, np.uint32), rgba)


def cylinder(name, cx, cy, r_bottom, z0, z1, rgba, r_top=None, segments=24) -> Part:
    """Cylinder (or cone/frustum with r_top) with caps, metres."""
    r_top = r_bottom if r_top is None else r_top
    verts, norms, tris = [], [], []
    slope = (r_bottom - r_top) / max(z1 - z0, 1e-6)
    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        c, s = math.cos(a), math.sin(a)
        nz = slope / math.sqrt(1 + slope * slope)
        nr = 1 / math.sqrt(1 + slope * slope)
        verts += [((cx + r_bottom * c) * MM, (cy + r_bottom * s) * MM, z0 * MM),
                  ((cx + r_top * c) * MM, (cy + r_top * s) * MM, z1 * MM)]
        norms += [(c * nr, s * nr, nz)] * 2
    for i in range(segments):
        a, b = 2 * i, 2 * i + 2
        tris += [(a, b, b + 1), (a, b + 1, a + 1)]
    for z, r, nz in ((z1, r_top, 1), (z0, r_bottom, -1)):
        if r <= 0:
            continue
        centre = len(verts)
        verts.append((cx * MM, cy * MM, z * MM))
        norms.append((0, 0, nz))
        for i in range(segments + 1):
            a = 2 * math.pi * i / segments
            verts.append(((cx + r * math.cos(a)) * MM, (cy + r * math.sin(a)) * MM, z * MM))
            norms.append((0, 0, nz))
        for i in range(segments):
            p, q = centre + 1 + i, centre + 2 + i
            tris.append((centre, p, q) if nz > 0 else (centre, q, p))
    return Part(name, np.array(verts, np.float32), np.array(norms, np.float32), np.array(tris, np.uint32), rgba)


def _shade(rgba, factor, alpha=None):
    r, g, b, a = rgba
    return (min(1, r * factor), min(1, g * factor), min(1, b * factor), a if alpha is None else alpha)


def element_parts(el: fl.Element) -> List[Part]:
    color = ALLIANCE_RGBA.get(el.alliance, ALLIANCE_RGBA["neutral"])
    if el.kind in ("zone", "slot") or el.z <= 0:
        patch = _shade(color, 1.15 if el.kind == "zone" else 0.9)
        if el.shape == "circle":
            return [cylinder(el.name, el.x, el.y, el.r, 0.5, 2.0, patch)]
        return [box(el.name, el.x, el.y, el.w, el.h, 0.5, 2.0, patch)]
    if el.kind == "overhead":
        return [box(el.name, el.x, el.y, el.w, el.h, el.z - min(OVERHEAD_T, el.h), el.z, _shade(color, 0.8))]
    if el.kind == "no_touch":
        return [box(el.name, el.x, el.y, el.w, el.h, X_MARK_BOTTOM, el.z, (0.95, 0.75, 0.15, 1.0))]
    if el.kind == "prop":
        if el.label == "cone":
            return [cylinder(el.name, el.x, el.y, el.w / 2, 0, el.z, (0.98, 0.55, 0.15, 1.0), r_top=8)]
        return [box(el.name, el.x, el.y, el.w, el.h, 0, el.z, (0.95, 0.93, 0.85, 1.0))]
    alpha = 0.55 if el.kind == "movable" else None
    shade = _shade(color, 0.75 if el.kind == "obstacle" else 1.0, alpha)
    if el.shape == "circle":
        return [cylinder(el.name, el.x, el.y, el.r, 0, el.z, shade)]
    return [box(el.name, el.x, el.y, el.w, el.h, 0, el.z, shade)]


def field_parts(elements: List[fl.Element]) -> List[Part]:
    parts = [box("floor", fl.CX, fl.CY, fl.FIELD_W, fl.FIELD_H, -10, 0, FLOOR_RGBA)]
    t, h = FRAME_T, fl.FRAME_HEIGHT
    parts += [box("frame_south", fl.CX, -t / 2, fl.FIELD_W + 2 * t, t, 0, h, FRAME_RGBA),
              box("frame_north", fl.CX, fl.FIELD_H + t / 2, fl.FIELD_W + 2 * t, t, 0, h, FRAME_RGBA),
              box("frame_west", -t / 2, fl.CY, t, fl.FIELD_H, 0, h, FRAME_RGBA),
              box("frame_east", fl.FIELD_W + t / 2, fl.CY, t, fl.FIELD_H, 0, h, FRAME_RGBA)]
    for el in elements:
        parts += element_parts(el)
    return parts


def build_field_node(elements: List[fl.Element]):
    """Panda3D NodePath with the whole field."""
    from panda3d.core import NodePath, TransparencyAttrib
    root = NodePath("field")
    for part in field_parts(elements):
        node = root.attach_new_node(_geom_node(part))
        node.set_color(*part.rgba)
        if part.rgba[3] < 0.99:
            node.set_transparency(TransparencyAttrib.M_alpha)
            node.set_depth_write(False)
            node.set_bin("transparent", 10)
    return root
