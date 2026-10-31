"""3D field built from the 2D layout (simulation/field2d/field_layout.py), with the
structure details of the 2026 MakeX Challenge Storm Breaker Rules Guide V1.1
(resources/rules/, section 4.2-4.3; "p.N" = printed page number).

Every field_layout element keeps its footprint and top height `z`; the shape inside
the footprint follows the rules figures:

  Own resource area (p.13, Fig 4.2-5/4.2-6, 4.4-5/4.4-8): 1040 mm wide, 318 deep,
    posts to 965 mm, two side shelves at 758.5 mm with 2 pins each, a central ball
    box (373 outer / 293 inner) with 10 balls, mesh below the shelf.
  Pin placement area (p.14-16, Fig 4.2-9/4.2-11): 985 x 195 mm shelf at 405 mm,
    MAKEX board below it, posts to 965 mm carrying the flag poles (961 mm).
  Cone hanging posts (p.17): 40 mm, 405 mm high.
  Strategy area (p.17-18, Fig 4.2-14): 960 x 215 x 259 mm frame, top rail 52.5 mm,
    four 140 mm channel windows with 80 mm dividers.
  Central resource area (p.19-21, Fig 4.2-17): table top at 654 mm, ball levels
    200 mm apart (15 balls each, p.26), X mark 447 mm wide from 654 to 947 mm.
  Mobile fortress (p.21-22, Fig 4.2-19): 640 x 640 x 646 mm, letter-cube level at
    171 mm (8 cubes, p.23), ball level at 407 mm, walls with a V cut-out.
  Props (p.23-26): letter / bonus cubes 120 mm, cone 170 mm (120 mm base, 20 mm
    high, 100 -> 60 mm body), pin 290 mm (70 mm base, 100 mm max), ball 70 mm.
  Frame (p.10): 900 mm high, drawn semi-transparent.

Dimensions marked "estimate" are read off the figures (scale) or chosen for
display, e.g. plate thicknesses and post sections. It is a visual aid, not a
collision model; placements carry the estimates noted in field_layout.py.
"""

import math
from typing import List, Optional, Sequence, Tuple

import numpy as np

import field_layout as fl
from balls import field_balls
from robot_model import Part, _geom_node

MM = 1 / 1000.0
FLOOR_RGBA = (0.16, 0.17, 0.20, 1.0)
ALLIANCE_RGBA = {"red": (0.86, 0.25, 0.25, 1.0), "blue": (0.22, 0.45, 0.88, 1.0), "neutral": (0.55, 0.57, 0.62, 1.0)}
METAL_RGBA = (0.20, 0.21, 0.23, 1.0)       # black aluminium profiles
PLATE_RGBA = (0.30, 0.31, 0.34, 1.0)
MESH_RGBA = (0.80, 0.82, 0.86, 0.22)
FRAME_RGBA = (0.70, 0.72, 0.76, 0.16)
BALL_RGBA = (0.98, 0.82, 0.10, 1.0)
CONE_RGBA = (0.98, 0.78, 0.12, 1.0)
X_RED, X_BLUE = (0.85, 0.15, 0.15, 1.0), (0.15, 0.35, 0.85, 1.0)

FRAME_T = 30.0          # mm, perimeter frame thickness (display)
POST = 30.0             # mm, aluminium post section (estimate)
PLATE_T = 20.0          # mm, shelf / plate thickness (estimate)
OVERHEAD_T = 30.0
# Own resource area (p.13 Fig 4.2-6)
RES_SHELF_Z = 758.5
RES_BOX_OUTER, RES_BOX_INNER = 373.0, 293.0
RES_PIN_EDGE, RES_PIN_PITCH = 127.0, 120.0
RES_MESH_TOP = 700.0    # estimate (Fig 4.2-6)
# Pin placement area (p.15 Fig 4.2-9)
PIN_SHELF_L, PIN_POST_SPAN = 985.0, 1040.0
# Strategy area channel (p.18 Fig 4.2-14)
STRATEGY_TOP_RAIL = 52.5
STRATEGY_BOTTOM_RAIL = 25.0   # estimate
# Central resource area (p.21 Fig 4.2-17)
CENTRAL_BALL_LEVELS = (50.0, 250.0)   # estimate from the figure; 200 mm apart (stated)
X_BOTTOM = 654.0
X_ARM = 90.0            # chevron arm width (estimate)
# Mobile fortress (p.22 Fig 4.2-19)
FORT_CUBE_Z, FORT_BALL_Z = 171.0, 407.0
FORT_NOTCH_Z = 495.0    # estimate (figure scale)
FORT_EAR_TOP, FORT_EAR_BOTTOM = 55.0, 220.0   # estimate
# Props (p.23-26)
CUBE = 120.0
BALL_D = 70.0
PIN_H = 290.0
PIN_PROFILE = ((0, 35), (30, 42), (100, 50), (160, 42), (200, 27), (240, 24), (275, 25), (290, 20))  # (z, r), estimate shape


# --- primitives ------------------------------------------------------------------------
def _part(name, verts, norms, tris, rgba) -> Part:
    return Part(name, np.asarray(verts, np.float32), np.asarray(norms, np.float32), np.asarray(tris, np.uint32), rgba)


def box(name, cx, cy, w, d, z0, z1, rgba) -> Part:
    """Axis-aligned box from its centre (mm) and size; flat normals."""
    return hexa(name, [(cx - w / 2, cy - d / 2, z0), (cx + w / 2, cy - d / 2, z0),
                       (cx + w / 2, cy + d / 2, z0), (cx - w / 2, cy + d / 2, z0)], (0, 0, z1 - z0), rgba)


def hexa(name, base: Sequence[Tuple[float, float, float]], offset: Tuple[float, float, float], rgba) -> Part:
    """Convex prism: a planar quad (mm) swept by `offset` (mm). Normals point outward."""
    b = np.asarray(base, float) * MM
    t = b + np.asarray(offset, float) * MM
    pts = np.vstack([b, t])
    centre = pts.mean(0)
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    verts, norms, tris = [], [], []
    for f in faces:
        q = pts[list(f)]
        n = np.cross(q[1] - q[0], q[2] - q[0])
        if np.linalg.norm(n) < 1e-12:
            n = np.cross(q[2] - q[0], q[3] - q[0])
        n = n / (np.linalg.norm(n) or 1.0)
        if np.dot(n, q.mean(0) - centre) < 0:   # make the face point outward
            q, n = q[::-1], -n
        base_i = len(verts)
        verts += list(q)
        norms += [n] * 4
        tris += [(base_i, base_i + 1, base_i + 2), (base_i, base_i + 2, base_i + 3)]
    return _part(name, verts, norms, tris, rgba)


def lathe(name, cx, cy, z0, profile: Sequence[Tuple[float, float]], rgba, segments=20) -> Part:
    """Solid of revolution from (z, r) pairs (mm, bottom to top), with caps."""
    verts, norms, tris = [], [], []
    prof = [(z0 + z, r) for z, r in profile]
    ring = len(prof)
    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        c, s = math.cos(a), math.sin(a)
        for k, (z, r) in enumerate(prof):
            z_prev, r_prev = prof[max(k - 1, 0)]
            z_next, r_next = prof[min(k + 1, ring - 1)]
            dz, dr = z_next - z_prev, r_next - r_prev
            length = math.hypot(dz, dr) or 1.0
            nr, nz = dz / length, -dr / length
            verts.append(((cx + r * c) * MM, (cy + r * s) * MM, z * MM))
            norms.append((nr * c, nr * s, nz))
    for i in range(segments):
        for k in range(ring - 1):
            a, b = i * ring + k, (i + 1) * ring + k
            tris += [(a, b, b + 1), (a, b + 1, a + 1)]
    for (z, r), nz in ((prof[-1], 1), (prof[0], -1)):
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
    return _part(name, verts, norms, tris, rgba)


def cylinder(name, cx, cy, r, z0, z1, rgba, r_top=None, segments=24) -> Part:
    return lathe(name, cx, cy, z0, [(0, r), (z1 - z0, r if r_top is None else r_top)], rgba, segments)


def sphere(name, cx, cy, cz, r, rgba, rings=8, segments=12) -> Part:
    profile = [(r - r * math.cos(math.pi * k / rings), max(r * math.sin(math.pi * k / rings), 0.01))
               for k in range(rings + 1)]
    return lathe(name, cx, cy, cz - r, profile, rgba, segments)


def _shade(rgba, factor, alpha=None):
    r, g, b, a = rgba
    return (min(1, r * factor), min(1, g * factor), min(1, b * factor), a if alpha is None else alpha)


# --- props ---------------------------------------------------------------------------------
def pin(name, x, y, z0, alliance) -> Part:
    return lathe(name, x, y, z0, PIN_PROFILE, ALLIANCE_RGBA[alliance], 16)


def ball(name, x, y, z0) -> Part:
    return sphere(name, x, y, z0 + BALL_D / 2, BALL_D / 2, BALL_RGBA)


def cone(name, x, y, z0=0.0) -> List[Part]:
    return [box(name, x, y, CUBE, CUBE, z0, z0 + 20, CONE_RGBA),
            cylinder(f"{name}:body", x, y, 50, z0 + 20, z0 + 170, CONE_RGBA, r_top=30)]


def bonus_cube(name, x, y, z0=0.0) -> List[Part]:
    return [box(name, x, y, CUBE, CUBE, z0, z0 + CUBE - 2, (0.10, 0.10, 0.11, 1.0)),
            box(f"{name}:top", x, y, CUBE, CUBE, z0 + CUBE - 2, z0 + CUBE, CONE_RGBA)]


def letter_cube(name, x, y, z0, alliance) -> List[Part]:
    return [box(name, x, y, CUBE, CUBE, z0, z0 + CUBE, ALLIANCE_RGBA[alliance]),
            box(f"{name}:top", x, y, CUBE - 30, CUBE - 30, z0 + CUBE, z0 + CUBE + 1, (0.95, 0.85, 0.2, 1.0))]


# --- structures ------------------------------------------------------------------------------
def _wall_sign_y(el) -> int:
    """+1 if the element's wall is at y = 0 (it opens toward +y), -1 if at y = FIELD_H."""
    return 1 if el.y < fl.CY else -1


def _wall_sign_x(el) -> int:
    return 1 if el.x < fl.CX else -1


def resource_area(el) -> List[Part]:
    """Own resource area shelves, ball box, pins and balls (p.13)."""
    s = _wall_sign_y(el)
    wall = el.y - s * el.h / 2
    mid_y = wall + s * el.h / 2
    parts = []
    half_box = RES_BOX_OUTER / 2
    for side in (-1, 1):
        x0, x1 = el.x + side * half_box, el.x + side * el.w / 2
        cx, w = (x0 + x1) / 2, abs(x1 - x0)
        parts.append(box(f"{el.name}:shelf_{side}", cx, mid_y, w, el.h, RES_SHELF_Z - PLATE_T, RES_SHELF_Z, PLATE_RGBA))
        for k in range(2):
            px = el.x + side * (el.w / 2 - RES_PIN_EDGE - k * RES_PIN_PITCH)
            parts.append(pin(f"detail_{el.name}_pin_{side}_{k}", px, mid_y, RES_SHELF_Z, el.alliance))
    # ball box: floor at the shelf height, dark translucent walls up to the posts
    parts.append(box(el.name, el.x, mid_y, RES_BOX_OUTER, el.h, RES_SHELF_Z - PLATE_T, RES_SHELF_Z, PLATE_RGBA))
    wall_rgba = (0.12, 0.12, 0.14, 0.55)
    t = (RES_BOX_OUTER - RES_BOX_INNER) / 2
    for side in (-1, 1):
        parts.append(box(f"{el.name}:box_side_{side}", el.x + side * (half_box - t / 2), mid_y, t, el.h,
                         RES_SHELF_Z, el.z, wall_rgba))
    parts.append(box(f"{el.name}:box_front", el.x, wall + s * (el.h - 5), RES_BOX_INNER, 10, RES_SHELF_Z, el.z - 60, wall_rgba))
    # the 10 balls come from balls.py (field_parts / the simulation)
    # top rails along the front and back at the post height
    for edge in (wall + s * POST / 2, wall + s * (el.h - POST / 2)):
        parts.append(box(f"{el.name}:rail_{int(edge)}", el.x, edge, el.w + POST, POST, el.z - POST, el.z, METAL_RGBA))
    for k, dx in enumerate((-el.w / 2, el.w / 2)):   # back posts (front posts are the _leg elements)
        parts.append(box(f"{el.name}:back_post_{k}", el.x + dx, wall + s * POST / 2, POST, POST, 0, el.z, METAL_RGBA))
    return parts


def resource_back(el) -> List[Part]:
    """Mesh structure under the shelf, toward the wall (estimate geometry)."""
    s = _wall_sign_y(el)
    front = el.y + s * el.h / 2
    return [box(el.name, el.x, el.y, el.w, el.h, 0, el.z, (0.10, 0.10, 0.12, 0.35)),
            box(f"{el.name}:mesh", el.x, front - s * 2, el.w, 4, 0, RES_MESH_TOP, MESH_RGBA)]


def pin_area(el) -> List[Part]:
    """Pin placement shelf at 405 mm with the MAKEX board below and flag posts (p.14-16)."""
    s = _wall_sign_x(el)
    wall = el.x - s * el.w / 2
    parts = [box(el.name, el.x, el.y, el.w, PIN_SHELF_L, el.z - PLATE_T, el.z, PLATE_RGBA),
             box(f"{el.name}:board", wall + s * 10, el.y, 20, PIN_SHELF_L, 0, el.z - PLATE_T, (0.08, 0.10, 0.18, 1.0))]
    for side in (-1, 1):
        parts.append(box(f"{el.name}:leg_{side}", el.x + s * (el.w / 2 - POST / 2), el.y + side * (PIN_SHELF_L / 2 - POST / 2),
                         POST, POST, 0, el.z - PLATE_T, METAL_RGBA))
        parts.append(box(f"detail_{el.name}_flag_post_{side}", wall + s * POST / 2, el.y + side * PIN_POST_SPAN / 2,
                         POST, POST, 0, 965.0, METAL_RGBA))
    parts.append(box(f"detail_{el.name}_top_rail", wall + s * POST / 2, el.y, POST, PIN_POST_SPAN, 965.0 - POST, 965.0, METAL_RGBA))
    parts.append(box(f"detail_{el.name}_mesh", wall + s * 3, el.y, 4, PIN_POST_SPAN, el.z, 965.0 - POST, MESH_RGBA))
    return parts


def strategy_area(el, slots: List[fl.Element]) -> List[Part]:
    """Frame with top rail, bottom rail and solid dividers around the channel windows (p.18)."""
    top0 = el.z - STRATEGY_TOP_RAIL
    rgba = (0.14, 0.14, 0.16, 1.0)
    parts = [box(el.name, el.x, el.y, el.w, el.h, top0, el.z - 0.5, rgba),
             box(f"{el.name}:bottom_rail", el.x, el.y, el.w, el.h, 0, STRATEGY_BOTTOM_RAIL, rgba)]
    y0, y1 = el.y - el.h / 2, el.y + el.h / 2
    windows = sorted((s.y - s.h / 2, s.y + s.h / 2) for s in slots if y0 <= s.y <= y1)
    edges = [y0] + [v for w in windows for v in w] + [y1]
    for k in range(0, len(edges), 2):
        a, b = edges[k], edges[k + 1]
        if b - a > 1:
            parts.append(box(f"{el.name}:divider_{k // 2}", el.x, (a + b) / 2, el.w, b - a, STRATEGY_BOTTOM_RAIL, top0, rgba))
    # gold trim along the top edges, as in Fig 4.2-13
    gold = (0.75, 0.62, 0.30, 1.0)
    for side in (-1, 1):
        parts.append(box(f"{el.name}:trim_x{side}", el.x + side * (el.w / 2 - 3), el.y, 8, el.h + 2, el.z - 6, el.z, gold))
        parts.append(box(f"{el.name}:trim_y{side}", el.x, el.y + side * (el.h / 2 - 3), el.w + 2, 8, el.z - 6, el.z, gold))
    return parts


def central_resource(el) -> List[Part]:
    """Table at 654 mm with two ball levels (p.19-21); the 15 balls per level come from balls.py."""
    parts = [box(el.name, el.x, el.y, el.w, el.h, el.z - PLATE_T, el.z, PLATE_RGBA)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box(f"{el.name}:leg_{sx}_{sy}", el.x + sx * (el.w / 2 - POST / 2), el.y + sy * (el.h / 2 - POST / 2),
                             POST, POST, 0, el.z - PLATE_T, METAL_RGBA))
    for level in CENTRAL_BALL_LEVELS:
        parts.append(box(f"{el.name}:level_{int(level)}", el.x, el.y, el.w - POST, el.h - POST, level - 10, level, PLATE_RGBA))
    return parts


def x_mark(el) -> List[Part]:
    """X mark: red chevron on the red side, blue on the blue side, 654-947 mm (p.21)."""
    zc = (X_BOTTOM + el.z) / 2
    parts = [box(f"{el.name}:pivot", el.x, el.y, 20, 20, X_BOTTOM - 0.1, zc, METAL_RGBA)]
    half = el.w / 2
    for side, rgba in ((-1, X_RED), (1, X_BLUE)):
        outer = el.x + side * half
        apex = el.x + side * 40
        for zs in (-1, 1):
            z_end = zc + zs * (el.z - zc)
            quad = [(outer, el.y - el.h / 2, z_end), (outer - side * X_ARM, el.y - el.h / 2, z_end),
                    (apex - side * X_ARM, el.y - el.h / 2, zc), (apex, el.y - el.h / 2, zc)]
            name = el.name if (side, zs) == (1, 1) else f"{el.name}:arm_{side}_{zs}"
            parts.append(hexa(name, quad, (0, el.h, 0), rgba))
    return parts


def fortress(el) -> List[Part]:
    """Two-level mobile fortress with V cut-out walls and 8 letter cubes (p.21-23)."""
    rgba = (0.14, 0.14, 0.16, 1.0)
    half = el.w / 2
    parts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box(f"{el.name}:post_{sx}_{sy}", el.x + sx * (half - POST / 2), el.y + sy * (half - POST / 2),
                             POST, POST, 0, el.z, rgba))
    parts.append(box(f"{el.name}:cube_level", el.x, el.y, el.w - POST, el.w - POST, FORT_CUBE_Z - PLATE_T / 2, FORT_CUBE_Z, PLATE_RGBA))
    parts.append(box(f"{el.name}:ball_level", el.x, el.y, el.w - POST, el.w - POST, FORT_BALL_Z - 4, FORT_BALL_Z, MESH_RGBA))
    wall_rgba = (0.18, 0.18, 0.20, 0.85)
    t = 6.0
    for k, (ux, uy) in enumerate(((1, 0), (0, 1), (-1, 0), (0, -1))):
        # wall plane: along (vx, vy), outward normal (ux, uy)
        vx, vy = -uy, ux
        ox, oy = el.x + ux * (half - t), el.y + uy * (half - t)

        def p(s, z):
            return (ox + vx * s, oy + vy * s, z)
        off = (ux * t, uy * t, 0)
        parts.append(hexa(f"{el.name}:wall_{k}", [p(-half, FORT_BALL_Z), p(half, FORT_BALL_Z), p(half, FORT_NOTCH_Z),
                                                  p(-half, FORT_NOTCH_Z)], off, wall_rgba))
        for side in (-1, 1):
            ear = [p(side * half, FORT_NOTCH_Z), p(side * (half - FORT_EAR_BOTTOM), FORT_NOTCH_Z),
                   p(side * (half - FORT_EAR_TOP), el.z), p(side * half, el.z)]
            name = el.name if (k, side) == (0, 1) else f"{el.name}:ear_{k}_{side}"
            parts.append(hexa(name, ear, off, wall_rgba))
    # 8 letter cubes (M A K E x2), two per side as in Fig 4.4-13
    spots = []
    r = half - POST - CUBE / 2 - 5
    for ux, uy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        vx, vy = -uy, ux
        for s in (-1, 1):
            spots.append((el.x + ux * r + vx * s * (CUBE / 2 + 15), el.y + uy * r + vy * s * (CUBE / 2 + 15)))
    for n, (cx, cy) in enumerate(spots):
        parts += letter_cube(f"detail_{el.name}_cube_{n}", cx, cy, FORT_CUBE_Z, el.alliance)
    return parts


def prop_base(el: fl.Element, elements: List[fl.Element]) -> float:
    """Height a prop stands on: the top of the strategy area under it, else the floor.
    (field_layout's z for a prop is the prop's own height.)"""
    for other in elements:
        if other.name.startswith("strategy_") and other.kind == "obstacle" and other.contains(el.x, el.y):
            return other.z
    return 0.0


# --- assembly -------------------------------------------------------------------------------
def element_parts(el: fl.Element, elements: Optional[List[fl.Element]] = None) -> List[Part]:
    color = ALLIANCE_RGBA.get(el.alliance, ALLIANCE_RGBA["neutral"])
    name = el.name
    if el.kind in ("zone", "slot") or el.z <= 0:
        patch = _shade(color, 0.85 if el.kind == "zone" else 0.6)
        if el.shape == "circle":
            return [cylinder(name, el.x, el.y, el.r, 0.5, 2.0, patch)]
        return [box(name, el.x, el.y, el.w, el.h, 0.5, 2.0, patch)]
    if el.kind == "overhead" and "_resource_" in name:
        return resource_area(el)
    if name.endswith("_back") and "_resource_" in name:
        return resource_back(el)
    if name.endswith("_pin_area"):
        return pin_area(el)
    if name.startswith("strategy_"):
        return strategy_area(el, [s for s in (elements or []) if s.kind == "slot"])
    if name == "central_resource":
        return central_resource(el)
    if name == "x_mark":
        return x_mark(el)
    if el.kind == "movable":
        return fortress(el)
    if el.kind == "prop":   # props stand on top of the strategy area (p.18 Fig 4.2-13)
        z0 = prop_base(el, elements or [])
        return cone(name, el.x, el.y, z0) if el.label == "cone" else bonus_cube(name, el.x, el.y, z0)
    if el.kind == "overhead":    # flag poles: 15 mm bar at 961 mm
        return [box(name, el.x, el.y, el.w, el.h, el.z - min(OVERHEAD_T, el.h), el.z, (0.75, 0.77, 0.80, 1.0))]
    rgba = METAL_RGBA if el.shape == "circle" else _shade(color, 0.6)
    if el.shape == "circle":
        return [cylinder(name, el.x, el.y, el.r, 0, el.z, rgba)]
    return [box(name, el.x, el.y, el.w, el.h, 0, el.z, rgba)]


def frame_parts() -> List[Part]:
    t, h = FRAME_T, fl.FRAME_HEIGHT
    parts = []
    for name, cx, cy, w, d in (("frame_south", fl.CX, -t / 2, fl.FIELD_W + 2 * t, t),
                               ("frame_north", fl.CX, fl.FIELD_H + t / 2, fl.FIELD_W + 2 * t, t),
                               ("frame_west", -t / 2, fl.CY, t, fl.FIELD_H),
                               ("frame_east", fl.FIELD_W + t / 2, fl.CY, t, fl.FIELD_H)):
        parts.append(box(name, cx, cy, w, d, 0, h, FRAME_RGBA))
        parts.append(box(f"{name}:top", cx, cy, w, d, h - 25, h, METAL_RGBA))
        parts.append(box(f"{name}:kick", cx, cy, w, d, 0, 120, (0.10, 0.10, 0.12, 1.0)))
    for x in (-t / 2, fl.FIELD_W + t / 2):
        for y in (-t / 2, fl.FIELD_H + t / 2):
            parts.append(box(f"frame_post_{int(x)}_{int(y)}", x, y, 40, 40, 0, h, METAL_RGBA))
    return parts


def ball_part(b) -> Part:
    return sphere(f"detail_{b.name}", b.x, b.y, b.z, BALL_D / 2, BALL_RGBA)


def field_parts(elements: List[fl.Element], ball_scenario: str = "initial") -> List[Part]:
    """Static field. ball_scenario (balls.py) adds balls as static parts; the viewer
    passes "none" and draws the simulation's balls itself so they can be collected."""
    parts = [box("floor", fl.CX, fl.CY, fl.FIELD_W, fl.FIELD_H, -10, 0, FLOOR_RGBA)]
    parts += frame_parts()
    for el in elements:
        parts += element_parts(el, elements)
    parts += [ball_part(b) for b in field_balls(elements, ball_scenario)]
    return parts


def build_field_node(elements: List[fl.Element], ball_scenario: str = "none"):
    """Panda3D NodePath with the whole field. Opaque parts are merged into a few
    batches so the field renders fast; transparent parts stay separate."""
    from panda3d.core import NodePath, TransparencyAttrib
    root = NodePath("field")
    opaque = root.attach_new_node("opaque")
    for part in field_parts(elements, ball_scenario):
        transparent = part.rgba[3] < 0.99
        node = (root if transparent else opaque).attach_new_node(_geom_node(part))
        node.set_color(*part.rgba)
        if transparent:
            node.set_transparency(TransparencyAttrib.M_alpha)
            node.set_depth_write(False)
            node.set_bin("transparent", 10)
    opaque.flatten_strong()
    return root
