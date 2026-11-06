"""How close the 500 x 500 mm footprint gets to the pins on the resource-area side shelves.

The projection may never leave 500 x 500 mm (rules p.55), so nothing reaches out of it. The legs
(LEG_MM, estimate) stand at y 298 and the gaps between them (333 mm) are narrower than the robot,
but a corner goes in first: turned 45 deg the robot's corner enters a gap. Below the shelf (738 mm)
only the body enters; a tower to pin height must stay north of the shelf edge (y 318).

    .venv/bin/python simulation/analysis/pin_reach.py
"""

import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "field2d"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import field_layout as fl  # noqa: E402
from match import obb_aabb_depth  # noqa: E402
from props import field_props  # noqa: E402
from robot import RobotPose  # noqa: E402

LEG_MM = 40.0
HALF = 250.0
PIN_R = 50.0


def corners(p):
    c, s = math.cos(p.theta), math.sin(p.theta)
    return [(p.x + a * c - b * s, p.y + a * s + b * c) for a, b in ((HALF, HALF), (HALF, -HALF), (-HALF, -HALF), (-HALF, HALF))]


def dist_point_square(p, x, y):
    c, s = math.cos(p.theta), math.sin(p.theta)
    dx, dy = x - p.x, y - p.y
    lx, ly = dx * c + dy * s, -dx * s + dy * c
    ex, ey = max(abs(lx) - HALF, 0.0), max(abs(ly) - HALF, 0.0)
    return math.hypot(ex, ey)


def clear(p, boxes):
    return all(obb_aabb_depth(p, (-HALF, -HALF, HALF, HALF), b) <= 0.0 for b in boxes) and \
        all(0.0 <= x <= fl.FIELD_W and 0.0 <= y <= fl.FIELD_H for x, y in corners(p))


def main():
    elements = fl.build_field()
    h = LEG_MM / 2
    boxes = [(e.x - h, e.y - h, e.x + h, e.y + h) for e in elements if e.name.startswith("red_resource_1_leg")]
    boxes.append(fl.get(elements, "red_resource_1_back").bounds()[:4])
    pins = [p for p in field_props(elements) if p.kind == "pin" and p.alliance == "red" and p.y < fl.CY]
    print(f"legs {LEG_MM:.0f} mm; pin radius {PIN_R:.0f}: distance footprint -> pin surface")
    for pin in sorted(pins, key=lambda q: q.x):
        best = {}
        for deg in (0, 15, 30, 40, 45, 50, 60, 75):
            th = math.radians(deg)
            b = (1e9, None)
            for x in range(600, 2450, 5):
                for y in range(250, 800, 5):
                    p = RobotPose(float(x), float(y), th)
                    if abs(x - pin.x) < 500 and clear(p, boxes):
                        d = dist_point_square(p, pin.x, pin.y) - PIN_R
                        if d < b[0]:
                            b = (d, (x, y))
            best[deg] = b
        square, turned = best[0], min(best.items(), key=lambda kv: kv[1][0])
        print(f"pin x {pin.x:.0f}: square to the shelf {square[0]:.0f} mm; best {turned[1][0]:.0f} mm at {turned[0]} deg, robot {turned[1][1]}")


def tool_reach(pin, boxes, chassis=(-250.0, -250.0, 115.0, 250.0), claw=30.0):
    """Best pose with the chassis (no intake head) clear of the legs and the pin centre inside the
    500 mm square, `claw` mm from its edge: a slim tool in the free front of the square reaches it.
    Returns (margin mm, heading, x, y, pin in robot frame, tower distance north of the shelf edge)."""
    best = None
    for deg in range(180, 361, 5):
        th = math.radians(deg)
        c, s = math.cos(th), math.sin(th)
        for x in range(int(pin.x) - 420, int(pin.x) + 421, 5):
            for y in range(260, 640, 5):
                p = RobotPose(float(x), float(y), th)
                dx, dy = pin.x - x, pin.y - y
                lx, ly = dx * c + dy * s, -dx * s + dy * c
                margin = HALF - max(abs(lx), abs(ly))
                if margin < claw or lx <= chassis[2]:
                    continue                                  # in the square, ahead of the chassis front
                if max(cx for cx, _ in corners(p)) > 2220.0:
                    continue                                  # R06: the square stays in our area
                if all(obb_aabb_depth(p, chassis, b) <= 0.0 for b in boxes):
                    tower = p.to_field(chassis[2], max(-200.0, min(200.0, ly)))   # on the chassis front
                    if best is None or margin > best[0]:
                        best = (margin, deg, x, y, (round(lx), round(ly)), round(tower[1] - 318.0))
    return best


def main_tool():
    elements = fl.build_field()
    h = LEG_MM / 2
    boxes = [(e.x - h, e.y - h, e.x + h, e.y + h) for e in elements if e.name.startswith("red_resource_1_leg")]
    boxes.append(fl.get(elements, "red_resource_1_back").bounds()[:4])
    pins = [p for p in field_props(elements) if p.kind == "pin" and p.alliance == "red" and p.y < fl.CY]
    print("slim tool in the free front of the square (chassis front 115 mm, no intake head):")
    for pin in sorted(pins, key=lambda q: q.x):
        print(f"pin x {pin.x:.0f}:", tool_reach(pin, boxes))


if __name__ == "__main__":
    main()
    main_tool()
