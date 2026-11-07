"""Can the gripper take the letter cubes out of our mobile fortress? (simulator geometry)

For each red letter cube in our half of the fortress and each side the robot could come from,
the robot is placed so its grab point (robot_config.json "gripper", right side) is at the cube,
with the carriage at the cube height, and its body height bands are checked against the field
structures (fortress plate and posts, pin placement area, cone posts, walls) and the partner
half. Prints the overlap: 0 means that grab pose is free.

    .venv/bin/python simulation/analysis/letter_cube_reach.py
"""

import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "simulation" / "field2d"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import json  # noqa: E402

import field_layout as fl  # noqa: E402
from ball_physics import named_colliders  # noqa: E402
from match import obb_aabb_depth  # noqa: E402
from props import field_props, load_gripper  # noqa: E402
from robot import DEFAULT_CONFIG, RobotPose  # noqa: E402

SIDES = {"south (gripper toward +y)": 180.0, "north (toward -y)": 0.0,
         "east (toward -x)": -90.0, "west (toward +x)": 90.0}


def check(extra_reach=0.0):
    elements = fl.build_field()
    colliders = named_colliders(elements)
    data = json.loads(DEFAULT_CONFIG.read_text())
    bands = data["ball_path"]["body_bands_mm"]
    g = load_gripper()
    gx, gy, gz = g.grab_point                      # robot frame, carriage down
    gy -= extra_reach                              # a gripper reaching farther out to the right
    rows = []
    for cube in [p for p in field_props(elements) if p.kind == "letter" and p.alliance == "red" and p.y < fl.CY]:
        carriage = max(0.0, cube.z + 60 - gz)
        for side, heading in SIDES.items():
            th = math.radians(heading)
            c, s = math.cos(th), math.sin(th)
            x = cube.x - (gx * c - gy * s)
            y = cube.y - (gx * s + gy * c)
            pose = RobotPose(x, y, th)
            worst, what = 0.0, ""
            for name, (bx0, by0, bz0, bx1, by1, bz1) in colliders:
                for x0, y0, z0, x1, y1, z1 in bands:
                    if min(z1, bz1) - max(z0, bz0) <= 2:
                        continue
                    d = obb_aabb_depth(pose, (x0, y0, x1, y1), (bx0, by0, bx1, by1))
                    if d > worst:
                        worst, what = d, name
            corners = pose.corners_of((-250, -250, 115, 250)) if hasattr(pose, "corners_of") else \
                [pose.to_field(px, py) for px in (-250, 115) for py in (-250, 250)]
            off_field = any(not (0 <= cx <= fl.FIELD_W and 0 <= cy <= fl.FIELD_H) for cx, cy in corners)
            half = max(cy for _, cy in corners) - fl.CY
            rows.append((cube.label, round(cube.x), round(cube.y), side, round(x), round(y), round(carriage),
                         round(worst), what, off_field, round(max(0.0, half))))
    return rows


def main():
    for extra in (0.0, 150.0):
        print(f"\n== gripper reach {'as in the v22 CAD' if not extra else f'+{extra:.0f} mm to the right'}")
        best = {}
        for r in check(extra):
            label, cx, cy, side, x, y, car, depth, what, off, half = r
            ok = depth == 0 and not off and half == 0
            print(f"{label} ({cx},{cy}) from the {side:26s} robot ({x},{y}) carriage {car:3d}  "
                  f"{'FREE' if ok else f'overlap {depth} mm with {what}' + (' off field' if off else '') + (f' partner half +{half}' if half else '')}")
            if ok:
                best.setdefault(label, side)
        print("reachable:", best or "none")


if __name__ == "__main__":
    main()
