"""Match clock and rule monitors (rules guide V1.1, p.27-28, 51-53, 66-71).

Stages: automatic 30 s, manual 100 s, modification 60 s, final 90 s (4 min 40 s).
The bonus exchange and the referee's 5 s countdowns between stages do not take
match time, so the clock runs them back to back. Simulated time 0 is the start of
the automatic stage, when the program starts.

Monitors:
  R19  the robot must be stationary at the end of the automatic stage (-20 points);
       the chassis and the slide mechanisms (carriage, intake head) are checked.
  R06  the robot's vertical projection must stay in its alliance area (x <= 2220 mm for
       red); back within 3 s, or -20 points. The intake head overhang is allowed
       (team decision), so only the robot body is checked.
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import field_layout as fl

STAGES: Tuple[Tuple[str, float], ...] = (("automatic", 30.0), ("manual", 100.0),
                                         ("modification", 60.0), ("final", 90.0))
R06_GRACE_S = 3.0
STATIONARY_MM_S = 5.0        # chassis speed below this counts as stationary
STATIONARY_DEG_S = 1.0


def stage_at(t: float) -> Tuple[str, float, float]:
    """(stage name, time left in it, stage length) at match time t."""
    start = 0.0
    for name, length in STAGES:
        if t < start + length:
            return name, start + length - t, length
        start += length
    return "ended", 0.0, 0.0


def format_clock(seconds: float) -> str:
    seconds = max(0.0, seconds)
    return f"{int(seconds // 60)}:{seconds % 60:04.1f}"


@dataclass
class MatchMonitor:
    alliance: str = "red"
    body_box: Tuple[float, float, float, float] = (-249.5, -250.0, 115.0, 250.0)   # robot frame x0, y0, x1, y1
    auto_end: Optional[dict] = None            # R19 check at t = 30 s
    outside_s: float = 0.0                     # current continuous time outside (R06)
    r06_events: List[dict] = field(default_factory=list)
    _outside_since: Optional[float] = None

    def limits(self) -> Tuple[float, float]:
        return fl.alliance_x_limits(self.alliance)

    def body_outside(self, pose) -> bool:
        lo, hi = self.limits()
        x0, y0, x1, y1 = self.body_box
        return any(not (lo <= px <= hi) for px, _ in
                   (pose.to_field(x, y) for x in (x0, x1) for y in (y0, y1)))

    def update(self, t: float, dt: float, pose, velocity, mech_moving: bool) -> None:
        if self.body_outside(pose):
            if self._outside_since is None:
                self._outside_since = t
                self.r06_events.append({"start": t, "seconds": 0.0, "penalty": False})
            self.outside_s = t + dt - self._outside_since
            ev = self.r06_events[-1]
            ev["seconds"] = self.outside_s
            ev["penalty"] = self.outside_s > R06_GRACE_S
        else:
            self._outside_since, self.outside_s = None, 0.0
        auto_len = STAGES[0][1]
        if self.auto_end is None and t + dt >= auto_len - 1e-9:
            vx, vy, omega = velocity
            speed = math.hypot(vx, vy)
            moving = speed > STATIONARY_MM_S or abs(math.degrees(omega)) > STATIONARY_DEG_S or mech_moving
            self.auto_end = {"speed_mm_s": speed, "turn_deg_s": math.degrees(omega),
                             "mechanisms_moving": mech_moving, "stationary": not moving}

    @property
    def r06_penalties(self) -> int:
        return sum(ev["penalty"] for ev in self.r06_events)

    def report(self) -> List[str]:
        lines = []
        if self.auto_end is not None:
            lines.append("R19 end of automatic stage: robot stationary" if self.auto_end["stationary"] else
                         "R19 end of automatic stage: robot MOVING (-20 points)")
        if self.outside_s > 0:
            lines.append(f"R06 body outside the alliance area: {self.outside_s:.1f} s"
                         + (" (-20 points)" if self.outside_s > R06_GRACE_S else f" (return within {R06_GRACE_S:g} s)"))
        elif self.r06_penalties:
            lines.append(f"R06 penalties: {self.r06_penalties}")
        return lines


# --- robot vs field structures ------------------------------------------------------------
COLLISION_MIN_MM = 2.0       # overlaps smaller than this count as touching, not colliding


def obb_aabb_depth(pose, rect, box) -> float:
    """Penetration depth (mm, > 0 if they overlap in plan) between the robot-frame rectangle
    rect = (x0, y0, x1, y1) placed at pose and the field axis-aligned box (x0, y0, x1, y1)."""
    rx0, ry0, rx1, ry1 = rect
    corners = [pose.to_field(x, y) for x in (rx0, rx1) for y in (ry0, ry1)]
    bx0, by0, bx1, by1 = box
    bcorners = [(bx0, by0), (bx0, by1), (bx1, by0), (bx1, by1)]
    c, s = math.cos(pose.theta), math.sin(pose.theta)
    depth = float("inf")
    for ax, ay in ((1.0, 0.0), (0.0, 1.0), (c, s), (-s, c)):
        a = [px * ax + py * ay for px, py in corners]
        b = [px * ax + py * ay for px, py in bcorners]
        overlap = min(max(a), max(b)) - max(min(a), min(b))
        if overlap <= 0:
            return 0.0
        depth = min(depth, overlap)
    return depth


def inside_plan(pose, box, rect) -> bool:
    """True if the field box (x0, y0, x1, y1) lies inside the robot-frame rectangle rect."""
    x0, y0, x1, y1 = box
    rx0, ry0, rx1, ry1 = rect
    c, s = math.cos(pose.theta), math.sin(pose.theta)
    for px in (x0, x1):
        for py in (y0, y1):
            dx, dy = px - pose.x, py - pose.y
            lx, ly = dx * c + dy * s, -dx * s + dy * c
            if not (rx0 <= lx <= rx1 and ry0 <= ly <= ry1):
                return False
    return True


@dataclass
class CollisionMonitor:
    """Robot body and intake head (at its lift) against the field structures (ball_physics
    colliders, props excluded). Contact with the own fortress is reported as a push (allowed,
    R02: it must not tilt). A structure that lies inside the gripper slot (the free space between
    the jaws, open to the outside, its top following the carriage), like a cone post a cone is
    hung on, is no contact."""
    colliders: list
    body_boxes: list                       # robot outline per height band (robot frame)
    head_box: Tuple[float, float, float, float, float, float]
    slot: Optional[Tuple[float, float, float, float, float, float]] = None   # robot frame, carriage down
    events: List[dict] = field(default_factory=list)
    _active: dict = field(default_factory=dict)

    def update(self, t: float, pose, lift: float, carriage: float = 0.0) -> None:
        hx0, hy0, hz0, hx1, hy1, hz1 = self.head_box
        parts = [("body", b) for b in self.body_boxes] + [("head", (hx0, hy0, hz0 + lift, hx1, hy1, hz1 + lift))]
        now_hit = {}
        for name, (bx0, by0, bz0, bx1, by1, bz1) in self.colliders:
            cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
            if math.hypot(cx - pose.x, cy - pose.y) > 450 + max(bx1 - bx0, by1 - by0) / 2:
                continue
            if self.slot and bz1 <= self.slot[5] + carriage and inside_plan(
                    pose, (bx0, by0, bx1, by1), (self.slot[0], self.slot[1], self.slot[3], self.slot[4])):
                continue
            for part, (x0, y0, z0, x1, y1, z1) in parts:
                if min(z1, bz1) - max(z0, bz0) <= COLLISION_MIN_MM:
                    continue
                d = obb_aabb_depth(pose, (x0, y0, x1, y1), (bx0, by0, bx1, by1))
                if d > COLLISION_MIN_MM:
                    key = (name, part)
                    now_hit[key] = max(now_hit.get(key, 0.0), d)
        for key, depth in now_hit.items():
            ev = self._active.get(key)
            if ev is None:
                ev = {"element": key[0], "part": key[1], "start": t, "seconds": 0.0, "depth_mm": depth,
                      "fortress": "fortress" in key[0]}
                self.events.append(ev)
                self._active[key] = ev
            ev["seconds"] = t - ev["start"]
            ev["depth_mm"] = max(ev["depth_mm"], depth)
        for key in list(self._active):
            if key not in now_hit:
                del self._active[key]

    @property
    def collisions(self) -> List[dict]:
        return [e for e in self.events if not e["fortress"]]

    def report(self) -> List[str]:
        out = []
        for e in self._active.values():
            out.append(("fortress push" if e["fortress"] else "COLLISION") +
                       f": {e['part']} vs {e['element']} {e['depth_mm']:.0f} mm")
        if not out and self.collisions:
            out.append(f"collisions so far: {len(self.collisions)}")
        return out


@dataclass
class HalfMonitor:
    """Two robots per alliance: this robot keeps to its half of the alliance area (team rule,
    robot_config.json "own_half"): lower = y <= field centre line (1527.5 mm), upper = y >= it.
    Records the time the body spends over the line and the deepest intrusion."""
    half: str = "lower"
    body_box: Tuple[float, float, float, float] = (-249.5, -250.0, 115.0, 250.0)
    seconds: float = 0.0
    max_mm: float = 0.0
    events: List[float] = field(default_factory=list)   # start times of each crossing
    _over: bool = False

    def intrusion(self, pose) -> float:
        x0, y0, x1, y1 = self.body_box
        ys = [pose.to_field(x, y)[1] for x in (x0, x1) for y in (y0, y1)]
        return max(ys) - fl.CY if self.half == "lower" else fl.CY - min(ys)

    def update(self, t: float, dt: float, pose) -> None:
        depth = self.intrusion(pose)
        over = depth > COLLISION_MIN_MM
        if over:
            if not self._over:
                self.events.append(t)
            self.seconds += dt
            self.max_mm = max(self.max_mm, depth)
        self._over = over

    def report(self) -> List[str]:
        if not self.events:
            return []
        return [f"partner half: {len(self.events)} crossings, {self.seconds:.1f} s, up to {self.max_mm:.0f} mm"]


@dataclass
class ChannelMonitor:
    """R26 (p.73): no part of the robot may enter a strategy-area channel. A channel is the gap
    under the strategy-area top (z < 206 mm) between the dividers; robot parts are the body
    height bands and the intake head at its lift (robot frame boxes)."""
    channels: list                          # (name, x0, y0, x1, y1)
    parts: list
    top_z: float = 206.0
    events: List[dict] = field(default_factory=list)
    _inside: set = field(default_factory=set)

    def update(self, t: float, pose, head_box) -> None:
        inside = set()
        for name, cx0, cy0, cx1, cy1 in self.channels:
            if math.hypot((cx0 + cx1) / 2 - pose.x, (cy0 + cy1) / 2 - pose.y) > 600:
                continue
            for x0, y0, z0, x1, y1, z1 in self.parts + [head_box]:
                if z0 < self.top_z and obb_aabb_depth(pose, (x0, y0, x1, y1), (cx0, cy0, cx1, cy1)) > COLLISION_MIN_MM:
                    inside.add(name)
        for name in inside - self._inside:
            self.events.append({"channel": name, "start": t})
        self._inside = inside

    def report(self) -> List[str]:
        return [f"R26 robot inside {e['channel']} at {e['start']:.1f} s" for e in self.events[-2:]]
