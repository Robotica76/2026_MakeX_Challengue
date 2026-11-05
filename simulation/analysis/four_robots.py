"""A whole 2 vs 2 match with four identical robots in the detailed simulator, all on one field:

  red lower   ours: storm_breaker_2026.py (ORDER), ai_driver.py           Red Start 1
  red upper   partner: the same program (START_Y 2730, ORDER 0), partner_driver.py   Red Start 2
  blue upper  our robot turned 180 deg about the field centre (two_robots.py)       Blue Start 2
  blue lower  the partner turned 180 deg                                            Blue Start 1

Each lower robot faces the other alliance's lower robot across the lower strategy area and the
central table (contested bonus cubes, cones and balls), all four can turn the X mark, each alliance
shoots into the other's fortress. Alliance score: the shared items (balls, bonus, cones, letters, X)
once, plus each robot's flag and penalties.

    .venv/bin/python simulation/analysis/four_robots.py --red 12 --blue 12
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
for _p in (ROOT / "simulation" / "field2d", ROOT / "simulation" / "control", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from montecarlo_strategy import program_text  # noqa: E402
from two_robots import Robot, obb_overlap, turned  # noqa: E402


class Agent(Robot):
    """A robot of the 2 vs 2 match: `role` main (lower in its own frame) or partner (upper)."""

    def __init__(self, alliance, role, order, delay, constants=None, driver_options=None):
        import field_layout as fl
        from ai_driver import Driver
        from balls import load_intake
        from kinematics import load_drive_train
        from mechanisms import load_mechanisms
        from partner_driver import PartnerDriver
        from props import load_gripper
        from robot import RobotPose, load_config
        from simulation import Simulation, load_gyro_sign
        cfg = load_config()
        elements = fl.build_field()
        x, y = (325.0, 325.0) if role == "main" else (325.0, 2730.0)
        deg = 0.0
        if alliance == "blue":
            x, y, deg = turned(x, y, deg)
        area = next(el.name for el in elements if el.kind == "zone" and el.name.startswith(f"{alliance}_start")
                    and el.contains(x, y))
        cfg = replace(cfg, alliance=alliance, start_area=area, heading_deg=deg)
        self.alliance, self.role, self.order, self.delay = alliance, role, order, delay
        self.sim = Simulation(cfg, RobotPose(x, y, math.radians(deg)), load_drive_train(), 280.0, load_gyro_sign(),
                              ball_scenario="initial", intake=load_intake(), mechanisms=load_mechanisms(),
                              gripper=load_gripper())
        consts = {"ORDER": order if role == "main" else 0, "START_Y": 325 if role == "main" else 2730}
        consts.update(constants or {})
        folder = Path(tempfile.mkdtemp())
        self.program = folder / f"storm_breaker_{alliance}_{role}.py"
        self.program.write_text(program_text(consts), encoding="utf-8")
        self.sim.program = self.program
        self.driver = Driver() if role == "main" else PartnerDriver()
        for k, v in (driver_options or {}).items():
            setattr(self.driver, k, v)
        self.queue = []

    @property
    def half(self):                      # real half of the field
        own = "lower" if self.role == "main" else "upper"
        return own if self.alliance == "red" else {"lower": "upper", "upper": "lower"}[own]


def share_all(host, guests):
    """One field for all: the guests' ball worlds only handle their own robot."""
    from ball_physics import BallWorld
    from flag import load_flag
    from match import HalfMonitor
    from simulation import load_ball_path
    h = host.sim
    for guest in guests:
        g = guest.sim
        g.elements, g.balls, g.props, g.fortresses = h.elements, h.balls, h.props, h.fortresses
        g.referee_balls = False
        data = g._path_data or {}
        body, head = tuple(data.get("body_box_mm")), tuple(data.get("head_box_mm"))
        g.world = BallWorld(h.elements, h.balls, g.intake, load_ball_path(data), body, head, field_physics=False)
        g.world.x_mark_host = h.world
        g.collisions = g._new_collisions()
        g.channels = g._new_channels()
        g.flag = load_flag(guest.alliance, elements=h.elements)
        bx0, by0, _, bx1, by1, _ = body
        g.half = HalfMonitor(guest.half, (bx0, by0, bx1, by1))
        g._refresh_structures()
    sims = [host.sim] + [g.sim for g in guests]
    for s in sims:
        s.linked = [o for o in sims if o is not s]


def alliance_score(robots, alliance):
    import referee
    mine = [r for r in robots if r.alliance == alliance]
    main = next(r for r in mine if r.role == "main")
    s = dict(referee.match_score(main.sim, alliance))
    for r in mine:
        if r is main:
            continue
        extra = referee.match_score(r.sim, alliance)
        s["flag"] += extra["flag"]
        s["penalties"] += extra["penalties"]
        s["total"] += extra["flag"] - extra["penalties"]
    return s


def play(red_order=12, blue_order=12, delay=0, seconds=280.0, red_options=None, blue_options=None,
         trace_every=0.5, on_frame=None):
    """red_options / blue_options: {"main": {driver attributes}, "partner": {...}, "constants": {...}}."""
    red_options, blue_options = red_options or {}, blue_options or {}
    robots = []
    for alliance, order, opts in (("red", red_order, red_options), ("blue", blue_order, blue_options)):
        for role in ("main", "partner"):
            robots.append(Agent(alliance, role, order, delay, opts.get("constants"), opts.get(role)))
    host, guests = robots[0], robots[1:]
    contacts, trace, touching = [], [], {}
    with contextlib.redirect_stdout(io.StringIO()):
        for r in robots:
            r.sim.run()
        share_all(host, guests)
        k, last = 0, -1.0
        while host.sim.running and host.sim.time < seconds:
            for r in robots:
                if r.sim.running:
                    r.sim.step(1 / 60)
            for g in guests:
                if g.sim.bonus_judged is None and host.sim.bonus_judged is not None:
                    g.sim.bonus_judged = host.sim.bonus_judged
            k += 1
            for r in robots:
                r.drive(k)
            for i in range(len(robots)):
                for j in range(i + 1, len(robots)):
                    d = obb_overlap(robots[i].sim.pose, robots[j].sim.pose)
                    key = (i, j)
                    if d > 2.0 and not touching.get(key):
                        contacts.append({"t": round(host.sim.time, 1), "robots": [f"{robots[i].alliance} {robots[i].role}",
                                                                                  f"{robots[j].alliance} {robots[j].role}"],
                                         "depth_mm": round(d)})
                    touching[key] = d > 2.0
            if trace_every and host.sim.time - last >= trace_every:
                last = host.sim.time
                trace.append([round(host.sim.time, 1)] + [round(v) for r in robots for v in (r.sim.pose.x, r.sim.pose.y)])
            if on_frame:
                on_frame(robots)
    scores = {a: alliance_score(robots, a) for a in ("red", "blue")}
    for r in robots:
        try:
            r.program.unlink()
            r.program.parent.rmdir()
        except OSError:
            pass
    return {"robots": robots, "scores": scores, "contacts": contacts, "trace": trace,
            "x_mark": host.sim.world.x_mark_state if host.sim.world else None,
            "fortress_offsets": dict(host.sim.fortresses.offsets)}


def report(out):
    lines = []
    for r in out["robots"]:
        lines.append(f"\n== {r.alliance} {r.role} (ORDER {r.order if r.role == 'main' else 0})")
        lines += [l for l in r.driver.log]
        lines.append(f"collisions: {[(e['element'], round(e['start'])) for e in r.sim.collisions.collisions] or 'none'}  "
                     f"half: {r.sim.half.report() or 'ok'}  flag: {r.sim.flag.state if r.sim.flag else None}")
    for a in ("red", "blue"):
        s = out["scores"][a]
        lines.append(f"\n{a.upper()}: " + str({k: v for k, v in s.items() if k != "not_simulated"}))
    lines.append(f"\nrobot contacts: {out['contacts'] or 'none'} | X mark: {out['x_mark']} | "
                 f"fortresses moved: {{{', '.join(f'{k}: {[round(v) for v in o]}' for k, o in out['fortress_offsets'].items())}}}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--red", type=int, default=12)
    ap.add_argument("--blue", type=int, default=12)
    ap.add_argument("--delay", type=int, default=0)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    out = play(args.red, args.blue, args.delay)
    print(report(out))
    if args.json:
        args.json.write_text(json.dumps({"scores": out["scores"], "contacts": out["contacts"], "trace": out["trace"],
                                         "x_mark": out["x_mark"]}, indent=1, default=str))


if __name__ == "__main__":
    main()
