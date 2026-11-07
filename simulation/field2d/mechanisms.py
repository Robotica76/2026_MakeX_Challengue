"""Mechanism motors driven by power expansion board ports (robot_config.json "mechanisms").

Kinematic only, like the drive model: no load, no inertia.

  linear   a slide driven by a DC motor (elevator carriage, intake lift). Its position
           (mm above the lowest point) moves at power / 100 * speed_mm_s, clamped to
           0..travel_mm.
  spinner  a roller, belt or wheel set. Its angle advances at power / 100 * rpm.

The 3D viewer reads positions and angles to animate the CAD parts; the intake model
uses the intake lift (balls are only collected with the head down).
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from robot import DEFAULT_CONFIG


@dataclass
class Linear:
    port: str
    travel_mm: float
    speed_mm_s: float
    direction: int = 1
    start_mm: float = 0.0
    position: float = 0.0

    def step(self, power: float, dt: float) -> None:
        self.nudge(self.direction * power / 100.0 * self.speed_mm_s * dt)

    def nudge(self, delta_mm: float) -> None:
        self.position = max(0.0, min(self.travel_mm, self.position + delta_mm))

    def reset(self) -> None:
        self.position = max(0.0, min(self.travel_mm, self.start_mm))


@dataclass
class Spinner:
    port: str
    rpm: float
    direction: int = 1
    angle: float = 0.0      # degrees, unbounded

    def step(self, power: float, dt: float) -> None:
        self.angle += self.direction * power / 100.0 * self.rpm * 6.0 * dt

    def reset(self) -> None:
        self.angle = 0.0


class Mechanisms:
    def __init__(self, linear: Optional[Dict[str, Linear]] = None, spinners: Optional[Dict[str, Spinner]] = None):
        self.linear = dict(linear or {})
        self.spinners = dict(spinners or {})
        self.reset()

    def step(self, dc, dt: float) -> None:
        """dc: the simulation's DCBus (power per port)."""
        for m in self.linear.values():
            m.step(dc.power(m.port), dt)
        for m in self.spinners.values():
            m.step(dc.power(m.port), dt)

    def position(self, name: str, default: float = 0.0) -> float:
        m = self.linear.get(name)
        return m.position if m else default

    def angle(self, name: str) -> float:
        m = self.spinners.get(name)
        return m.angle if m else 0.0

    def reset(self) -> None:
        for m in list(self.linear.values()) + list(self.spinners.values()):
            m.reset()


def load_mechanisms(path: Path = DEFAULT_CONFIG) -> Mechanisms:
    data = json.loads(Path(path).read_text()).get("mechanisms", {})
    linear = {name: Linear(str(spec["port"]), float(spec["travel_mm"]), float(spec["speed_mm_s"]),
                           int(spec.get("direction", 1)), float(spec.get("start_mm", 0.0)))
              for name, spec in data.get("linear", {}).items()}
    spinners = {name: Spinner(str(spec["port"]), float(spec["rpm"]), int(spec.get("direction", 1)))
                for name, spec in data.get("spinners", {}).items()}
    return Mechanisms(linear, spinners)
