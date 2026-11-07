"""Can the launcher knock the pins off the resource-area shelves onto the floor?

Ballistic Monte Carlo with the simulator's ball model (hood 40 deg, gravity, restitution E_WALL on the
field frame, stopped by the structures): for each pin and robot spot in our half the program's aim
(aim_N_N_N_N) with noise (heading, speed). A ball that reaches a standing pin knocks it over along
the ball's horizontal direction (estimate: EVA pin, tips above ~MIN_HIT_MM_S): lying down its centre
of mass moves FALL_MM along that direction, plus a slide SLIDE_MM at random; if that point is off the
shelf it falls to the floor (out of the resource area: 10 points, the gripper can pick it up),
otherwise it stays on the shelf out of reach.

    .venv/bin/python simulation/analysis/pin_shots.py
"""

import json
import math
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "simulation" / "field2d"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import field_layout as fl  # noqa: E402
from ball_physics import E_WALL, G, R, named_colliders  # noqa: E402
from props import PIN_H, RES_SHELF_Z, field_props  # noqa: E402

HOOD = math.radians(40.0)
V_FULL = 8000.0                  # mm/s at 100 % power
EXIT_LEFT = 290.0
PIN_R = 45.0                     # mean radius of the pin
MIN_HIT_MM_S = 1000.0            # slower hits do not knock it over (estimate)
FALL_MM = 120.0                  # centre of mass height: how far it moves when the pin lies down
SLIDE_MM = (0.0, 150.0)          # slide after the hit (EVA on the shelf, estimate)
DT = 0.002


def exit_height():
    data = json.loads((ROOT / "simulation" / "field2d" / "robot_config.json").read_text())["ball_path"]
    return data["exit_cad_mm"][2]


def fly(x, y, z, vx, vy, vz, boxes, pins):
    """Returns (pin, vx, vy) of the first standing pin hit, or None."""
    for _ in range(int(2.5 / DT)):
        vz -= G / 1000.0 * 0 + G * DT
        x, y, z = x + vx * DT, y + vy * DT, z + vz * DT
        if z < R:
            return None
        if y < R:
            y, vy = R, -vy * E_WALL
        if x < R:
            x, vx = R, -vx * E_WALL
        for p in pins:
            if p.z - R < z < p.z + PIN_H + R and math.hypot(x - p.x, y - p.y) < PIN_R + R:
                return p, vx, vy
        for b in boxes:
            if b[0] - R < x < b[3] + R and b[1] - R < y < b[4] + R and b[2] - R < z < b[5] + R:
                return None
    return None


def outcome(p, vx, vy, shelf, rng):
    """floor | shelf after a hit with horizontal velocity (vx, vy)."""
    v = math.hypot(vx, vy)
    if v < MIN_HIT_MM_S:
        return "weak"
    d = FALL_MM + rng.uniform(*SLIDE_MM)
    cx, cy = p.x + vx / v * d, p.y + vy / v * d
    # the field frame (y 0) and the ball box in the middle of the shelf stop it; the front edge
    # (y 318) and the outer end of the side shelf are open
    west = p.x < (shelf[0] + shelf[2]) / 2
    if cy > shelf[3]:
        return "floor"
    if (west and cx < shelf[0]) or (not west and cx > shelf[2]):
        return "floor"
    return "shelf"


def shot(rx, ry, p, boxes, pins, rng, z_exit, shelf, noise=True, aim_z=None):
    dist = math.hypot(p.x - rx, p.y - ry) - EXIT_LEFT
    if dist < 100:
        return "none"
    rise = (aim_z if aim_z is not None else p.z + 170.0) - z_exit
    den = 2 * math.cos(HOOD) ** 2 * (dist * math.tan(HOOD) - rise)
    if den <= 0:
        return "none"
    v = math.sqrt(G * dist * dist / den)
    if v > V_FULL:
        return "none"
    ang = math.atan2(p.y - ry, p.x - rx)
    if noise:
        ang += math.radians(rng.gauss(0.0, 1.0))
        v *= 1.0 + rng.gauss(0.0, 0.03)
    ex, ey = rx + EXIT_LEFT * math.cos(ang), ry + EXIT_LEFT * math.sin(ang)
    hit = fly(ex, ey, z_exit, v * math.cos(HOOD) * math.cos(ang), v * math.cos(HOOD) * math.sin(ang),
              v * math.sin(HOOD), boxes, pins)
    if hit is None:
        return "miss"
    q, vx, vy = hit
    return ("target " if q is p else "other ") + outcome(q, vx, vy, shelf, rng)


def bank_shot(rx, ry, p, boxes, pins, rng, z_exit, shelf, wall_z):
    """Over the pin into the field frame behind it at height wall_z: the rebound hits the pin from
    behind and knocks it toward the front edge of the shelf."""
    tx, ty = p.x, R
    dist = math.hypot(tx - rx, ty - ry) - EXIT_LEFT
    rise = wall_z - z_exit
    den = 2 * math.cos(HOOD) ** 2 * (dist * math.tan(HOOD) - rise)
    if den <= 0:
        return "none"
    v = math.sqrt(G * dist * dist / den)
    if v > V_FULL:
        return "none"
    ang = math.atan2(ty - ry, tx - rx) + math.radians(rng.gauss(0.0, 1.0))
    v *= 1.0 + rng.gauss(0.0, 0.03)
    ex, ey = rx + EXIT_LEFT * math.cos(ang), ry + EXIT_LEFT * math.sin(ang)
    hit = fly(ex, ey, z_exit, v * math.cos(HOOD) * math.cos(ang), v * math.cos(HOOD) * math.sin(ang),
              v * math.sin(HOOD), boxes, pins)
    if hit is None:
        return "miss"
    q, vx, vy = hit
    return ("target " if q is p else "other ") + ("from behind " if vy > 0 else "") + outcome(q, vx, vy, shelf, rng)


def main_bank(boxes, pins, shelf, z_exit, rng):
    print("bank shots off the field frame (E_WALL %.1f):" % E_WALL)
    n = 40
    for p in sorted(pins, key=lambda q: q.x):
        best = (0.0, None)
        for rx in range(int(p.x) - 300, int(p.x) + 301, 100):
            for ry in range(570, 1350, 50):
                for wz in (900.0, 960.0, 1020.0, 1080.0):
                    res = [bank_shot(rx, ry, p, boxes, pins, rng, z_exit, shelf, wz) for _ in range(n)]
                    f = sum(r == "target from behind floor" for r in res) / n
                    if f > best[0]:
                        best = (f, (rx, ry, wz))
        cnt = {}
        if best[1]:
            for _ in range(300):
                r = bank_shot(best[1][0], best[1][1], p, boxes, pins, rng, z_exit, shelf, best[1][2])
                cnt[r] = cnt.get(r, 0) + 1
        print(f"pin x {p.x:.0f}: best {best}", {k: round(v / 300, 2) for k, v in sorted(cnt.items())})


def main():
    rng = random.Random(3)
    elements = fl.build_field()
    z_exit = exit_height()
    boxes = [b for n, b in named_colliders(elements) if b[5] > 300 and b[0] < 2300]
    legs = [(e.x - 20, e.y - 20, 0.0, e.x + 20, e.y + 20, e.z) for e in elements if "_resource_1_leg" in e.name]
    boxes += legs
    pins = [p for p in field_props(elements) if p.kind == "pin" and p.alliance == "red" and p.y < fl.CY]
    shelf = fl.get(elements, "red_resource_1").bounds()
    print(f"exit z {z_exit:.0f} mm, shelf {RES_SHELF_Z} mm; {len(boxes)} structures")
    n = 60
    for p in sorted(pins, key=lambda q: q.x):
        spots = []
        for rx in range(650, 2180, 50):
            for ry in range(570, 1250, 50):
                for aim in (p.z + 100.0, p.z + 170.0, p.z + 250.0):
                    res = [shot(rx, ry, p, boxes, pins, rng, z_exit, shelf, aim_z=aim) for _ in range(n)]
                    floor = sum(r == "target floor" for r in res) / n
                    hit = sum(r.startswith("target") for r in res) / n
                    spots.append((floor, hit, rx, ry, aim - p.z))
        spots.sort(reverse=True)
        cnt = {}
        f, h, rx, ry, up = spots[0]
        for _ in range(400):
            r = shot(rx, ry, p, boxes, pins, rng, z_exit, shelf, aim_z=p.z + up)
            cnt[r] = cnt.get(r, 0) + 1
        print("   best spot, 400 shots:", {k: round(v / 400, 2) for k, v in sorted(cnt.items())})
        anyhit = max(s[1] for s in spots)
        print(f"pin x {p.x:.0f}: best P(falls to the floor) {spots[0][0]:.2f} at robot ({spots[0][2]}, {spots[0][3]}), "
              f"aim {spots[0][4]:.0f} mm up (P hit {spots[0][1]:.2f}); best P(hit) anywhere {anyhit:.2f}")


if __name__ == "__main__":
    main()
    rng0 = random.Random(9)
    el = fl.build_field()
    bx = [b for n, b in named_colliders(el) if b[5] > 300 and b[0] < 2300]
    bx += [(e.x - 20, e.y - 20, 0.0, e.x + 20, e.y + 20, e.z) for e in el if "_resource_1_leg" in e.name]
    main_bank(bx, [q for q in field_props(el) if q.kind == "pin" and q.alliance == "red" and q.y < fl.CY],
              fl.get(el, "red_resource_1").bounds(), exit_height(), rng0)
