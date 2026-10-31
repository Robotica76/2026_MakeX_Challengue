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
