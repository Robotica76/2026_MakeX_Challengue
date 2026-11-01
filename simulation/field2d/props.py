"""Game props the gripper handles, and the automatic-stage score preview.

Props (rules guide V1.1 p.23-26, 29-30, 37-43):
  bonus cube   120 mm, on top of the strategy areas (259 mm); X3/X6/X9/X12 from the prop
               card. Valid at the end of the automatic stage if its vertical projection is
               partly in the alliance's bonus exchange area, at most one per area and at most
               two on the alliance's side, and it does not touch a robot (p.30).
  cone         170 mm, 120 mm base, on top of the strategy areas; scores 20 when suspended on
               the alliance's cone hanging post (p.43).
  letter cube  120 mm, 8 per alliance on the fortress cube level (171 mm); scores 30 when its
               projection is partly in a strategy channel and it does not touch the map (p.38).

Gripper (robot_config.json "gripper"): the jaw closure follows the jaw slide mechanism
(mechanisms.py "gripper_jaw", port DC6); the grab point rides on the elevator carriage. A prop
whose centre is at the grab point (within the tolerance) is held once the jaws close to its
width, and released when they open again. A released prop drops onto the highest support under
it: a strategy area top or a channel rail, a cone post (cones), the fortress cube level, or the
floor. No prop physics beyond that (props do not slide, tip or get pushed).
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import field_layout as fl
from robot import DEFAULT_CONFIG

CUBE = 120.0
CONE_H, CONE_BASE, CONE_GRIP_W = 170.0, 120.0, 90.0   # grip the cone body (100 -> 60 mm), estimate
CHANNEL_RAIL_Z = 25.0                                  # strategy channel bottom rail, estimate
FORTRESS_CUBE_Z = 171.0
POST_CATCH_MM = 20.0                                   # cone hole centre this close to a post: hung


@dataclass
class Prop:
    name: str
    kind: str              # bonus | cone | letter
    label: str             # X3.. / cone / M A K E
    alliance: str          # neutral for bonus cubes and cones
    x: float               # centre, field mm
    y: float
    z: float               # bottom, mm
    held: bool = False
    dragged: bool = False  # being pulled under the intake head (pull mode)

    @property
    def height(self) -> float:
        return CONE_H if self.kind == "cone" else CUBE

    @property
    def width(self) -> float:
        return CONE_GRIP_W if self.kind == "cone" else CUBE


def _strategy_top(elements, x, y) -> Optional[float]:
    for el in elements:
        if el.name.startswith("strategy_") and el.kind == "obstacle" and el.contains(x, y):
            return el.z
    return None


def field_props(elements: List[fl.Element]) -> List[Prop]:
    props = []
    for el in elements:
        if el.kind == "prop":
            base = _strategy_top(elements, el.x, el.y) or 0.0
            kind = "cone" if el.label == "cone" else "bonus"
            props.append(Prop(el.name, kind, el.label, "neutral", el.x, el.y, base))
        elif el.kind == "movable":            # fortress: 8 letter cubes, two per side (Fig 4.4-13)
            half = el.w / 2
            r = half - 30.0 - CUBE / 2 - 5.0
            letters = "MAKEMAKE"
            n = 0
            for ux, uy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                vx, vy = -uy, ux
                for s in (-1, 1):
                    props.append(Prop(f"{el.name}_cube_{n}", "letter", letters[n], el.alliance,
                                      el.x + ux * r + vx * s * (CUBE / 2 + 15), el.y + uy * r + vy * s * (CUBE / 2 + 15),
                                      FORTRESS_CUBE_Z))
                    n += 1
    return props


@dataclass
class Gripper:
    grab_point: Tuple[float, float, float]     # robot frame (x fwd, y left, z) with the carriage down
    open_gap: float = 138.0                    # jaw gap fully open, mm (v22 CAD)
    tol_forward: float = 25.0                  # prop centre to grab point, mm
    tol_lateral: float = 40.0
    tol_z: float = 45.0
    held: Optional[Prop] = None

    def gap(self, closure: float) -> float:
        return self.open_gap - closure

    def grab_field(self, pose, carriage: float) -> Tuple[float, float, float]:
        gx, gy, gz = self.grab_point
        x, y = pose.to_field(gx, gy)
        return x, y, gz + carriage

    def update(self, pose, carriage: float, closure: float, props: List[Prop], elements) -> None:
        gx, gy, gz = self.grab_field(pose, carriage)
        gap = self.gap(closure)
        if self.held is not None:
            p = self.held
            if gap > p.width + 4.0:                    # jaws opened: release
                p.held = False
                self.held = None
                p.x, p.y = gx, gy
                p.z = support_under(p, elements)
            else:
                p.x, p.y, p.z = gx, gy, gz - p.height / 2
            return
        for p in props:
            if p.held:
                continue
            dx, dy = p.x - gx, p.y - gy
            c, s = math.cos(pose.theta), math.sin(pose.theta)
            fwd, lat = dx * c + dy * s, -dx * s + dy * c
            centre_z = p.z + p.height / 2
            if (abs(fwd) <= self.tol_forward and abs(lat) <= self.tol_lateral and abs(centre_z - gz) <= self.tol_z
                    and gap <= p.width):                 # jaws closed onto it
                p.held = True
                self.held = p
                p.x, p.y, p.z = gx, gy, gz - p.height / 2
                return


def rake_props(pose, lift: float, pulling: bool, props: List[Prop], elements, dt: float, intake,
               head_z: Tuple[float, float]) -> None:
    """Pull mode for props: a prop the intake head touches (front band, width, height overlap) is
    pulled against the head and rides with the robot (no closer than the body front). When the
    robot backs away the prop is dragged off the strategy area and drops onto the floor; if the
    pull stops, it drops onto whatever is below."""
    pinned = intake.body_front_mm + CUBE / 2 + 2.0
    c, s = math.cos(pose.theta), math.sin(pose.theta)
    hz0, hz1 = head_z[0] + lift, head_z[1] + lift
    for p in props:
        if p.held:
            continue
        dx, dy = p.x - pose.x, p.y - pose.y
        fwd, lat = dx * c + dy * s, -dx * s + dy * c
        if not p.dragged:
            touching = (pinned - 1.0 <= fwd <= intake.x_max + CUBE / 2
                        and intake.y_min - 40 <= lat <= intake.y_max + 40
                        and min(hz1, p.z + p.height) - max(hz0, p.z) >= 20.0)
            if not (pulling and touching):
                continue
            p.dragged = True
            p.local = (fwd, lat)
        fwd, lat = p.local
        if not pulling:
            p.dragged = False
            p.z = _sliding_support(p, elements)
            continue
        fwd = max(pinned, fwd - intake.pull_speed * dt)
        p.local = (fwd, lat)
        p.x, p.y = pose.to_field(fwd, lat)
        below = _sliding_support(p, elements)
        if below < p.z - 1.0:                       # off the strategy area: falls to the floor
            p.z = below
            p.dragged = False


def _sliding_support(p: Prop, elements) -> float:
    """Support of a prop sliding on a surface: it stays on the strategy area top while it is over
    it (the channels are below the top plate), else it drops like a released prop."""
    top = _strategy_top(elements, p.x, p.y)
    if top is not None and p.z >= top - 1.0:
        return top
    return support_under(p, elements)


def _mtv(pose, rect, cx, cy, half):
    """Smallest translation (dx, dy) that takes the square prop (centre cx, cy, half size) out of the
    robot-frame rectangle rect = (x0, y0, x1, y1) placed at pose; None if they do not overlap."""
    x0, y0, x1, y1 = rect
    corners = [pose.to_field(x, y) for x in (x0, x1) for y in (y0, y1)]
    square = [(cx - half, cy - half), (cx - half, cy + half), (cx + half, cy - half), (cx + half, cy + half)]
    c, s = math.cos(pose.theta), math.sin(pose.theta)
    best = None
    for ax, ay in ((1.0, 0.0), (0.0, 1.0), (c, s), (-s, c)):
        a = [px * ax + py * ay for px, py in corners]
        b = [px * ax + py * ay for px, py in square]
        overlap = min(max(a), max(b)) - max(min(a), min(b))
        if overlap <= 0:
            return None
        sign = 1.0 if (min(b) + max(b)) / 2 >= (min(a) + max(a)) / 2 else -1.0
        if best is None or overlap < best[0]:
            best = (overlap, ax * sign, ay * sign)
    depth, ux, uy = best
    return ux * (depth + 0.5), uy * (depth + 0.5)


def push_props(pose, parts, props: List[Prop], elements, colliders, openings=()) -> List[str]:
    """The robot pushes the props it runs into (cubes and cones are light EVA): each prop that
    overlaps a robot part (robot-frame boxes x0, y0, z0, x1, y1, z1, the head at its lift) in
    plan and height is moved out along the smallest overlap. A prop never goes into a field
    structure: then it stays and its name is returned (the robot is jammed against it). A prop
    pushed off a strategy-area top drops to what is below. `openings`: robot-frame boxes left
    free inside the bounding bands (the gripper slot between the jaws): a prop centred in one
    is not pushed."""
    jammed = []
    c, s = math.cos(pose.theta), math.sin(pose.theta)
    for p in props:
        if p.held or p.dragged:
            continue
        lx = (p.x - pose.x) * c + (p.y - pose.y) * s
        ly = -(p.x - pose.x) * s + (p.y - pose.y) * c
        if any(x0 <= lx <= x1 and y0 <= ly <= y1 and min(z1, p.z + p.height) - max(z0, p.z) > 0
               for x0, y0, z0, x1, y1, z1 in openings):
            continue
        half = (CONE_BASE if p.kind == "cone" else CUBE) / 2
        top = p.z + p.height
        for x0, y0, z0, x1, y1, z1 in parts:
            if min(z1, top) - max(z0, p.z) <= 2.0:
                continue
            move = _mtv(pose, (x0, y0, x1, y1), p.x, p.y, half)
            if move is None:
                continue
            nx, ny = p.x + move[0], p.y + move[1]
            blocked = any(bx0 < nx + half and bx1 > nx - half and by0 < ny + half and by1 > ny - half
                          and min(bz1, top) - max(bz0, p.z) > 2.0 and not (p.z >= bz1 - 1.0)
                          for bx0, by0, bz0, bx1, by1, bz1 in colliders)
            inside = half <= nx <= fl.FIELD_W - half and half <= ny <= fl.FIELD_H - half
            if blocked or not inside:
                jammed.append(p.name)
                continue
            p.x, p.y = nx, ny
            p.z = _sliding_support(p, elements)
    return jammed


def denial_count(props: List[Prop], balls, alliance: str) -> Dict[str, int]:
    """Central props and balls now completely on the alliance's side of the field (the opponent
    cannot reach them there), central balls on the opponent side, and props dropped on the floor
    across the centre line (partly on the opponent side, R23 risk)."""
    lo, hi = fl.alliance_x_limits(alliance)
    r = 35.0
    central_balls = [b for b in balls if b.name.startswith("central")]
    return {
        "balls": sum(1 for b in central_balls if b.state == "field" and lo + r <= b.x <= hi - r),
        "balls_opponent_side": sum(1 for b in central_balls if b.state == "field"
                                   and not (lo - r <= b.x <= hi + r) and not (hi - r < b.x < hi + 250)),
        "cones": sum(1 for p in props if p.kind == "cone" and lo + CUBE / 2 <= p.x <= hi - CUBE / 2),
        "bonus": sum(1 for p in props if p.kind == "bonus" and lo + CUBE / 2 <= p.x <= hi - CUBE / 2),
        "props_on_line": sum(1 for p in props if p.kind in ("bonus", "cone") and p.z < 1.0
                             and hi - CUBE / 2 < p.x < hi + CUBE / 2),   # on the floor across the line
    }


def support_under(p: Prop, elements) -> float:
    """Height of the bottom of a released prop (drops straight down)."""
    if p.kind == "cone":
        for el in elements:
            if el.name.endswith(("cone_post_1", "cone_post_2")) and math.hypot(p.x - el.x, p.y - el.y) <= POST_CATCH_MM:
                return el.z - CONE_H + 40.0               # hanging on the post (estimate)
    for el in elements:
        if el.kind == "slot" and el.contains(p.x, p.y):
            return CHANNEL_RAIL_Z
    top = _strategy_top(elements, p.x, p.y)
    if top is not None:
        return top
    for el in elements:
        if el.kind == "movable" and el.contains(p.x, p.y):
            return FORTRESS_CUBE_Z
    return 0.0


def load_gripper(path: Path = DEFAULT_CONFIG) -> Optional[Gripper]:
    data = json.loads(Path(path).read_text()).get("gripper")
    if not data:
        return None
    cx, cy, cz = data["grab_point_cad_mm"]
    tol = data.get("tolerance_mm", {})
    return Gripper((cy, -cx, cz), float(data.get("open_gap_mm", 138.0)), float(tol.get("forward", 25.0)),
                   float(tol.get("lateral", 40.0)), float(tol.get("z", 45.0)))


# --- automatic-stage score preview ----------------------------------------------------------
def _overlaps(p: Prop, el, size=CUBE) -> bool:
    x0, y0, x1, y1 = el.bounds()
    h = size / 2
    return p.x + h > x0 and p.x - h < x1 and p.y + h > y0 and p.y - h < y1


def bonus_state(props: List[Prop], elements, alliance: str) -> Dict[str, object]:
    """Valid bonus cubes for an alliance at the end of the automatic stage (p.30)."""
    areas = [el for el in elements if el.kind == "zone" and el.name.startswith(f"{alliance}_exchange")]
    lo, hi = fl.alliance_x_limits(alliance)
    cubes = [p for p in props if p.kind == "bonus"]
    on_side = [p for p in cubes if p.x + CUBE / 2 > lo and p.x - CUBE / 2 < hi and not p.held]
    valid = []
    if len(on_side) <= 2:                                   # rule d
        for area in areas:
            inside = [p for p in on_side if _overlaps(p, area) and p.z <= 1.0]
            if len(inside) == 1:                            # rules b, c
                valid.append(inside[0])
    balls = sum(int(p.label[1:]) for p in valid)
    return {"valid": [p.label for p in valid], "bonus_balls": balls, "on_side": len(on_side)}


def score_preview(props: List[Prop], elements, alliance: str) -> Dict[str, object]:
    cones = sum(1 for p in props if p.kind == "cone" and not p.held and any(
        el.alliance == alliance and el.name.endswith(("cone_post_1", "cone_post_2"))
        and math.hypot(p.x - el.x, p.y - el.y) <= POST_CATCH_MM for el in elements))
    letters = sum(1 for p in props if p.kind == "letter" and p.alliance == alliance and not p.held and p.z > 1.0
                  and any(el.kind == "slot" and _overlaps(p, el) for el in elements))
    bonus = bonus_state(props, elements, alliance)
    return {"cones": cones, "letter_cubes": letters, "bonus": bonus,
            "points_now": cones * 20 + letters * 30}
