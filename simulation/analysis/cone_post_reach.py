"""Hanging a cone on our cone post with the gripper (simulator geometry).

The gripper holds a cone by its body: the cone bottom is at the carriage height (the jaws reach
from 14 mm above the cone bottom). To hang it, the bottom must pass over the post top (405 mm,
p.17) and come down onto it, with the grab point over the post and the post inside the gripper
slot (the free space between the jaws, robot_config.json "gripper" "slot_mm"). For each robot
heading the pose that puts the grab point on the post is checked against the field structures
(pin placement area, walls, fortress), the field boundary and our half. The v22 carriage (358 mm)
is 57 mm short; robot_config.json has the 430 mm proposal. poses((x, y)) does the same for a
cone on the floor (the scripted driver picks its grab heading with it, ai_driver.py).

    .venv/bin/python simulation/analysis/cone_post_reach.py
"""

import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "simulation" / "field2d"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import field_layout as fl  # noqa: E402
from ball_physics import named_colliders  # noqa: E402
from match import inside_plan, obb_aabb_depth  # noqa: E402
from props import load_gripper  # noqa: E402
from robot import DEFAULT_CONFIG, RobotPose, load_config  # noqa: E402

POST = "red_cone_post_2"          # (200, 888): the post in our half
POST_TOP = 405.0
CLEARANCE = 10.0


def poses(target=None, step_deg=5):
    """(heading, robot x, y, worst overlap mm, with what, footprint in the field, in our half) for
    the grab point on `target` (field x, y; default: our cone post, which may sit in the slot)."""
    elements = fl.build_field()
    post = next(el for el in elements if el.name == POST)
    tx, ty = target or (post.x, post.y)
    data = json.loads(DEFAULT_CONFIG.read_text())
    bands = data["ball_path"]["body_bands_mm"]
    slot = data["gripper"]["slot_mm"]
    gx, gy, _ = load_gripper().grab_point
    colliders = named_colliders(elements)
    cfg = load_config()
    out = []
    for deg in range(0, 360, step_deg):
        th = math.radians(deg)
        c, s = math.cos(th), math.sin(th)
        pose = RobotPose(tx - (gx * c - gy * s), ty - (gx * s + gy * c), th)
        worst, what = 0.0, ""
        for name, box in colliders:
            if target is None and name == POST and inside_plan(pose, box[:2] + box[3:5], slot[:2] + slot[3:5]):
                continue                                    # the post goes into the jaw slot
            for x0, y0, z0, x1, y1, z1 in bands:
                if min(z1, box[5]) - max(z0, box[2]) <= 2:
                    continue
                d = obb_aabb_depth(pose, (x0, y0, x1, y1), box[:2] + box[3:5])
                if d > worst:
                    worst, what = d, name
        corners = pose.corners(cfg)
        inside = all(0 <= x <= fl.FIELD_W and 0 <= y <= fl.FIELD_H for x, y in corners)
        half = max(y for _, y in corners) <= fl.CY
        out.append((deg, round(pose.x), round(pose.y), round(worst), what, inside, half))
    return out


def main():
    elevator = json.loads(DEFAULT_CONFIG.read_text())["mechanisms"]["linear"]["elevator"]
    need = POST_TOP + CLEARANCE
    for label, travel in (("v22", elevator.get("travel_v22_mm", elevator["travel_mm"])), ("config", elevator["travel_mm"])):
        print(f"{label} carriage travel {travel:.0f} mm; the cone bottom must clear the post top: carriage >= {need:.0f} mm"
              f" -> {'OK' if travel >= need else f'{need - travel:.0f} mm short'}")
    free = [r for r in poses() if r[3] == 0 and r[5] and r[6]]
    print("headings (deg CCW) where the gripper reaches the post with the body clear:",
          [f"{d}: robot ({x},{y})" for d, x, y, *_ in free] or "none")


if __name__ == "__main__":
    main()
