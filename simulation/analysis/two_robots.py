"""Two identical robots on the same field: ours (red, Red Start 1) and its twin on the blue side
(Blue Start 2, the same point turned 180 deg about the field centre). The field is symmetric under
that turn, and a turn keeps the gripper on the right side, so the twin runs the very same program
(storm_breaker_2026.py, its own ORDER) with the same scripted driver: the driver sees the twin's
state turned into the red frame. Balls, props and the two mobile fortresses are shared: the shots
of one land in the other's fortress, both can turn the X mark, both pull from the central table;
robot-to-robot contacts are recorded.

    .venv/bin/python simulation/analysis/two_robots.py                    # ORDER 12 for both
    .venv/bin/python simulation/analysis/two_robots.py --red 12 --blue 34 --delay 2
"""

import argparse
import contextlib
import io
import json
import math
import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIELD2D = ROOT / "simulation" / "field2d"
CONTROL = ROOT / "simulation" / "control"
for _p in (FIELD2D, CONTROL, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from montecarlo_strategy import program_text  # noqa: E402

SWAP = {"red": "blue", "blue": "red"}


def turned(x, y, deg=None):
    """Field point (and heading) turned 180 deg about the field centre (red frame <-> blue frame)."""
    import field_layout as fl
    if deg is None:
        return fl.FIELD_W - x, fl.FIELD_H - y
    return fl.FIELD_W - x, fl.FIELD_H - y, (deg + 180.0) % 360.0


def obb_overlap(a, b, half=(250.0, 250.0)) -> float:
    """Penetration depth of two robot footprints (poses a, b; footprint 500 x 500 mm)."""
    def corners(p):
        c, s = math.cos(p.theta), math.sin(p.theta)
        return [(p.x + dx * c - dy * s, p.y + dx * s + dy * c) for dx in (-half[0], half[0]) for dy in (-half[1], half[1])]
    ca, cb = corners(a), corners(b)
    depth = float("inf")
    for p in (a, b):
        for ax, ay in ((math.cos(p.theta), math.sin(p.theta)), (-math.sin(p.theta), math.cos(p.theta))):
            pa = [x * ax + y * ay for x, y in ca]
            pb = [x * ax + y * ay for x, y in cb]
            overlap = min(max(pa), max(pb)) - max(min(pa), min(pb))
            if overlap <= 0:
                return 0.0
            depth = min(depth, overlap)
    return depth


class Robot:
    """One robot: its simulation, program, driver and frame (red or turned)."""

    def __init__(self, alliance, order, delay):
        import field_layout as fl
        from ai_driver import Driver
        from balls import load_intake
        from kinematics import load_drive_train
        from mechanisms import load_mechanisms
        from props import load_gripper
        from robot import RobotPose, load_config, start_pose
        from simulation import Simulation, load_gyro_sign
        cfg = load_config()
        start = start_pose(cfg, fl.build_field())
        if alliance == "blue":
            x, y, deg = turned(start.x, start.y, math.degrees(start.theta))
            cfg = replace(cfg, alliance="blue", start_area=self._area_at(fl.build_field(), x, y), heading_deg=deg)
            start = RobotPose(x, y, math.radians(deg))
        self.alliance, self.order, self.delay = alliance, order, delay
        self.sim = Simulation(cfg, start, load_drive_train(), 280.0, load_gyro_sign(), ball_scenario="initial",
                              intake=load_intake(), mechanisms=load_mechanisms(), gripper=load_gripper())
        folder = Path(tempfile.mkdtemp())
        self.program = folder / f"storm_breaker_{alliance}.py"
        self.program.write_text(program_text({"ORDER": order}), encoding="utf-8")
        self.sim.program = self.program
        self.driver = Driver()
        self.queue = []

    @staticmethod
    def _area_at(elements, x, y):
        return next(el.name for el in elements if el.kind == "zone" and el.name.startswith("blue_start") and el.contains(x, y))

    def state(self):
        """The driver's state stream, in the red frame for the blue twin."""
        import referee
        sim = self.sim
        blue = self.alliance == "blue"
        px, py, deg = sim.pose.x, sim.pose.y, math.degrees(sim.pose.theta)
        if blue:
            px, py, deg = turned(px, py, deg)
        vx, vy, w = sim._velocity

        def pt(x, y):
            return turned(x, y) if blue else (x, y)
        cones = []
        for p in sim.props:
            if p.kind == "cone":
                x, y = pt(p.x, p.y)
                post = p.on_post if p.on_post.startswith(self.alliance) else ""
                cones.append({"x_mm": x, "y_mm": y, "z_mm": p.z, "post": post})
        letters = []
        for p in sim.props:
            if p.kind == "letter" and p.alliance == self.alliance:
                x, y = pt(p.x, p.y)
                letters.append({"label": p.label, "x_mm": x, "y_mm": y, "z_mm": p.z, "held": p.held})
        fx, fy = sim.fortresses.offsets.get(f"{self.alliance}_fortress", (0.0, 0.0))
        x_mark = sim.world.x_mark_state if sim.world else None
        return {"t": sim.time, "pose": {"x_mm": px, "y_mm": py, "theta_deg": deg},
                "velocity": {"vx_mm_s": vx, "vy_mm_s": vy, "omega_deg_s": math.degrees(w)},
                "stored": sim.world.stored if sim.world else 0,
                "intake_lift_mm": sim.mechanisms.position("intake_lift"),
                "score": referee.match_score(sim, self.alliance)["total"],
                "flag": sim.flag.state if sim.flag else None,
                "x_mark": SWAP.get(x_mark, x_mark) if blue else x_mark,
                "carriage_mm": sim.mechanisms.position("elevator"),
                "jaw_mm": sim.mechanisms.position("gripper_jaw"),
                "held": sim.gripper.held.kind if sim.gripper and sim.gripper.held else None,
                "cones": cones, "letters": letters,
                "fortress": {"red_fortress": (-fx, -fy) if blue else (fx, fy)}}

    def drive(self, k, every=2):
        if k % every:
            return
        self.queue.append(self.state())
        if len(self.queue) > max(1, self.delay // every):
            for ev in self.driver.tick(self.queue.pop(0)):
                self.sim.gamepad.apply_event(ev)


def share(host, guest):
    """After both simulations started (run() resets them): one field, ball set, prop set and pair of
    fortresses; the guest's ball world only handles its own robot."""
    from ball_physics import BallWorld
    from flag import load_flag
    from match import HalfMonitor
    from simulation import load_ball_path
    h, g = host.sim, guest.sim
    g.elements, g.balls, g.props, g.fortresses = h.elements, h.balls, h.props, h.fortresses
    g.referee_balls = False
    data = g._path_data or {}
    body = tuple(data.get("body_box_mm"))
    head = tuple(data.get("head_box_mm"))
    g.world = BallWorld(h.elements, h.balls, g.intake, load_ball_path(data), body, head, field_physics=False)
    g.world.x_mark_host = h.world                         # one X mark
    g.collisions = g._new_collisions()
    g.channels = g._new_channels()
    g.flag = load_flag("blue", elements=h.elements)
    bx0, by0, _, bx1, by1, _ = body
    g.half = HalfMonitor("upper", (bx0, by0, bx1, by1))
    g._refresh_structures()
    h.linked, g.linked = [g], [h]


def play(red_order=12, blue_order=12, delay=0, seconds=280.0, trace_every=0.5):
    import referee
    red, blue = Robot("red", red_order, delay), Robot("blue", blue_order, delay)
    contacts, trace = [], []
    touching = False
    with contextlib.redirect_stdout(io.StringIO()):
        red.sim.run()
        blue.sim.run()
        share(red, blue)
        k, last = 0, -1.0
        while red.sim.running and red.sim.time < seconds:
            red.sim.step(1 / 60)
            if blue.sim.running:
                blue.sim.step(1 / 60)
            if blue.sim.bonus_judged is None and red.sim.bonus_judged is not None:
                blue.sim.bonus_judged = red.sim.bonus_judged
            k += 1
            red.drive(k)
            blue.drive(k)
            depth = obb_overlap(red.sim.pose, blue.sim.pose)
            if depth > 2.0 and not touching:
                contacts.append({"t": round(red.sim.time, 1), "depth_mm": round(depth)})
            touching = depth > 2.0
            if trace_every and red.sim.time - last >= trace_every:
                last = red.sim.time
                trace.append([round(red.sim.time, 1)] + [round(v) for r in (red, blue)
                                                         for v in (r.sim.pose.x, r.sim.pose.y)])
    scores = {a: referee.match_score(r.sim, a) for a, r in (("red", red), ("blue", blue))}
    for r in (red, blue):
        try:
            r.program.unlink()
            r.program.parent.rmdir()
        except OSError:
            pass
    return {"red": red, "blue": blue, "scores": scores, "contacts": contacts, "trace": trace,
            "x_mark": red.sim.world.x_mark_state if red.sim.world else None,
            "fortress_offsets": dict(red.sim.fortresses.offsets)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--red", type=int, default=12, help="ORDER of the red robot")
    ap.add_argument("--blue", type=int, default=12, help="ORDER of the blue twin")
    ap.add_argument("--delay", type=int, default=0, help="driver delay, frames")
    ap.add_argument("--json", type=Path, help="write the result here")
    args = ap.parse_args()
    out = play(args.red, args.blue, args.delay)
    for a in ("red", "blue"):
        r = out[a]
        print(f"\n== {a} (ORDER {r.order})")
        print("\n".join(r.driver.log))
        s = out["scores"][a]
        print(f"collisions: {[(e['element'], round(e['start'])) for e in r.sim.collisions.collisions]}  "
              f"half: {r.sim.half.report()}  bonus: {r.sim.bonus_judged and r.sim.bonus_judged[a]}")
        print("SCORE:", {k: v for k, v in s.items() if k != "not_simulated"})
    print("\nrobot contacts:", out["contacts"] or "none", "| X mark:", out["x_mark"],
          "| fortresses moved:", {k: [round(v) for v in o] for k, o in out["fortress_offsets"].items()})
    if args.json:
        args.json.write_text(json.dumps({"scores": out["scores"], "contacts": out["contacts"], "trace": out["trace"],
                                         "x_mark": out["x_mark"]}, indent=1, default=str))


if __name__ == "__main__":
    main()
