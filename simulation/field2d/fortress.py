"""Mobile fortresses on casters (rules p.25: "allowing it to move freely within its own alliance
area"). A robot part that runs into a fortress structure box (corner posts, cube level, ball level,
upper walls: ball_physics._element_boxes) pushes the fortress out along the smallest overlap. The
fortress stays inside its alliance area (p.70, R06) and does not go into other field structures:
then it does not move and the robot is jammed against it. It carries its letter cubes and the balls
inside it. Tilting (R02) is not modelled: the push is reported (speed, contact height) so a plan
can keep it gentle.

    motion = FortressMotion.for_elements(elements)
    moved = motion.update(pose, parts, elements)   # -> {name: (dx, dy)} applied this step
"""

import math
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple

import field_layout as fl
from ball_physics import _element_boxes, named_colliders

Box = Tuple[float, float, float, float, float, float]
CONTACT_MIN_MM = 0.5
MIN_GAP_MM = 1.0               # clearance kept to the other structures


def mtv_box(pose, rect, box) -> Optional[Tuple[float, float]]:
    """Smallest translation (dx, dy) that takes the field axis-aligned box (x0, y0, x1, y1) out of
    the robot-frame rectangle rect = (x0, y0, x1, y1) placed at pose; None if they do not overlap."""
    rx0, ry0, rx1, ry1 = rect
    corners = [pose.to_field(x, y) for x in (rx0, rx1) for y in (ry0, ry1)]
    bx0, by0, bx1, by1 = box
    bcorners = [(bx0, by0), (bx0, by1), (bx1, by0), (bx1, by1)]
    c, s = math.cos(pose.theta), math.sin(pose.theta)
    best = None
    for ax, ay in ((1.0, 0.0), (0.0, 1.0), (c, s), (-s, c)):
        a = [px * ax + py * ay for px, py in corners]
        b = [px * ax + py * ay for px, py in bcorners]
        overlap = min(max(a), max(b)) - max(min(a), min(b))
        if overlap <= CONTACT_MIN_MM:
            return None
        sign = 1.0 if (min(b) + max(b)) / 2 >= (min(a) + max(a)) / 2 else -1.0
        if best is None or overlap < best[0]:
            best = (overlap, ax * sign, ay * sign)
    depth, ux, uy = best
    return ux * depth, uy * depth


def _depth_along(pose, rect, box, ux, uy) -> float:
    """How far the box must move along (ux, uy) to leave the robot-frame rectangle at pose."""
    rx0, ry0, rx1, ry1 = rect
    a = [px * ux + py * uy for px, py in (pose.to_field(x, y) for x in (rx0, rx1) for y in (ry0, ry1))]
    bx0, by0, bx1, by1 = box
    b = [px * ux + py * uy for px, py in ((bx0, by0), (bx0, by1), (bx1, by0), (bx1, by1))]
    return max(0.0, max(a) - min(b))


@dataclass
class FortressMotion:
    names: List[str]                                      # fortress element names (kind "movable")
    offsets: Dict[str, Tuple[float, float]] = field(default_factory=dict)   # from the start, mm
    pushes: List[dict] = field(default_factory=list)      # one per push: start, end, distance, speed, contact z
    jams: List[str] = field(default_factory=list)         # fortresses the robot is jammed against now
    _active: Dict[str, dict] = field(default_factory=dict)

    @classmethod
    def for_elements(cls, elements: List[fl.Element]) -> "FortressMotion":
        names = [el.name for el in elements if el.kind == "movable"]
        return cls(names, {n: (0.0, 0.0) for n in names})

    def update(self, t: float, dt: float, pose, parts: List[Box], elements: List[fl.Element],
               props=(), balls=()) -> Dict[str, Tuple[float, float]]:
        """Push the fortresses the robot parts (robot-frame boxes x0, y0, z0, x1, y1, z1) overlap;
        replaces the moved elements in `elements` and moves what rides on them. Returns the moves."""
        moved = {}
        self.jams = []
        slots = [e for e in elements if e.kind == "slot"]
        for i, el in enumerate(elements):
            if el.name not in self.names:
                continue
            if math.hypot(el.x - pose.x, el.y - pose.y) > el.w / 2 + 400:
                self._active.pop(el.name, None)
                continue
            push, contact_z = None, 0.0
            for x0, y0, z0, x1, y1, z1 in parts:
                # direction: out of the part along the fortress footprint (a thin wall is not pushed
                # through); distance: how deep the part is in the structure boxes it touches
                way = mtv_box(pose, (x0, y0, x1, y1), el.bounds())
                if way is None:
                    continue
                n = math.hypot(*way)
                ux, uy = way[0] / n, way[1] / n
                for bx0, by0, bz0, bx1, by1, bz1 in _element_boxes(el, slots):
                    if min(z1, bz1) - max(z0, bz0) <= 2.0 or mtv_box(pose, (x0, y0, x1, y1), (bx0, by0, bx1, by1)) is None:
                        continue
                    depth = _depth_along(pose, (x0, y0, x1, y1), (bx0, by0, bx1, by1), ux, uy)
                    if depth > CONTACT_MIN_MM and (push is None or depth > math.hypot(*push)):
                        push, contact_z = (ux * depth, uy * depth), max(z0, bz0)
            if push is None:
                self._active.pop(el.name, None)
                continue
            dx, dy = self._allowed(el, push, elements)
            if (dx, dy) == (0.0, 0.0):
                self.jams.append(el.name)
                continue
            elements[i] = replace(el, x=el.x + dx, y=el.y + dy)
            ox, oy = self.offsets.get(el.name, (0.0, 0.0))
            self.offsets[el.name] = (ox + dx, oy + dy)
            self._carry(el, dx, dy, props, balls)
            moved[el.name] = (dx, dy)
            ev = self._active.get(el.name) or next(
                (e for e in reversed(self.pushes) if e["fortress"] == el.name and t - e["end"] < 0.25), None)
            if ev is None:
                ev = {"fortress": el.name, "start": t, "end": t, "distance_mm": 0.0, "max_speed_mm_s": 0.0,
                      "contact_z_mm": contact_z}
                self.pushes.append(ev)
            self._active[el.name] = ev
            step = math.hypot(dx, dy)
            ev["end"] = t
            ev["distance_mm"] += step
            ev["max_speed_mm_s"] = max(ev["max_speed_mm_s"], step / dt if dt > 0 else 0.0)
            ev["contact_z_mm"] = max(ev["contact_z_mm"], contact_z)
        return moved

    def _allowed(self, el, push, elements) -> Tuple[float, float]:
        """The push, or its x / y part alone (sliding along a wall), that keeps the fortress in
        its alliance area and clear of the other structures; (0, 0) if none does."""
        lo, hi = fl.alliance_x_limits(el.alliance)
        others = [box for name, box in named_colliders([e for e in elements if e.name != el.name])
                  if box[2] < el.z and box[5] > 0.0]
        for dx, dy in (push, (push[0], 0.0), (0.0, push[1])):
            if abs(dx) + abs(dy) < 1e-6:
                continue
            x0, y0, x1, y1 = el.x + dx - el.w / 2, el.y + dy - el.h / 2, el.x + dx + el.w / 2, el.y + dy + el.h / 2
            if x0 < lo or x1 > hi or y0 < 0.0 or y1 > fl.FIELD_H:
                continue
            if any(bx0 < x1 + MIN_GAP_MM and bx1 > x0 - MIN_GAP_MM and by0 < y1 + MIN_GAP_MM and by1 > y0 - MIN_GAP_MM
                   for bx0, by0, _, bx1, by1, _ in others):
                continue
            return dx, dy
        return 0.0, 0.0

    @staticmethod
    def _carry(el, dx, dy, props, balls) -> None:
        """Letter cubes on the cube level and balls inside ride with the fortress."""
        x0, y0, x1, y1 = el.bounds()
        for p in props:
            if not p.held and not getattr(p, "dragged", False) and p.z > 100.0 and x0 <= p.x <= x1 and y0 <= p.y <= y1:
                p.x, p.y = p.x + dx, p.y + dy
        for b in balls:
            if getattr(b, "state", "field") == "field" and b.z > 150.0 and x0 <= b.x <= x1 and y0 <= b.y <= y1:
                b.x, b.y = b.x + dx, b.y + dy
