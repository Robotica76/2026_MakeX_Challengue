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
