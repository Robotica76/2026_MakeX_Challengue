"""Balls on the field and a simple intake model.

Ball positions follow the rules guide V1.1 (p.26, p.32): 70 mm balls, 10 in the box
of each own resource area (shelf at 758.5 mm, rows of 3-4-3, Fig 4.4-5) and 15 on
each of the two levels of the central resource area (Fig 4.2-17).

Scenarios:
  none          no balls (default; keeps earlier studies unchanged)
  initial       the rules' initial state
  released      as initial, but the own resource balls lie on the floor in front of
                their box, as after the observer removes the barrier at the start of
                the manual stage (p.32). Where they come to rest is an estimate.

Intake model (robot_config.json "intake"): while the power on the intake port is at
least min_power (times direction) and the intake head is down (lift <= max_lift_mm,
see mechanisms.py), every ball on the field whose centre is inside
the intake zone (robot frame box at the front) and not higher than
max_ball_center_z_mm is collected, up to capacity. No ball physics: balls do not
roll, bounce or get pushed.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import field_layout as fl
from robot import DEFAULT_CONFIG, RobotPose

BALL_D = 70.0
RES_SHELF_Z = 758.5                 # p.13 Fig 4.2-6
CENTRAL_LEVELS = (50.0, 250.0)      # estimate from Fig 4.2-17; 200 mm apart (stated)
RELEASE_GAP = 60.0                  # estimate: first released row this far in front of the shelf
SCENARIOS = ("none", "initial", "released")


@dataclass
class Ball:
    name: str
    x: float          # field mm, centre
    y: float
    z: float          # centre height, mm
    collected: bool = False


def _resource_box_balls(el: fl.Element) -> List[Ball]:
    sign = 1 if el.y < fl.CY else -1
    mid_y = el.y
    out = []
    for row, count in enumerate((3, 4, 3)):
        for k in range(count):
            out.append(Ball(f"{el.name}_ball_{len(out)}", el.x + (k - (count - 1) / 2) * (BALL_D + 2),
                            mid_y + sign * (row - 1) * (BALL_D - 8), RES_SHELF_Z + BALL_D / 2))
    return out


def _released_balls(el: fl.Element) -> List[Ball]:
    """10 balls on the floor in two rows of 5 in front of the resource box (estimate)."""
    sign = 1 if el.y < fl.CY else -1
    front = el.y + sign * el.h / 2
    out = []
    for row in range(2):
        for k in range(5):
            out.append(Ball(f"{el.name}_ball_{len(out)}", el.x + (k - 2) * (BALL_D + 10),
                            front + sign * (RELEASE_GAP + BALL_D / 2 + row * (BALL_D + 10)), BALL_D / 2))
    return out


def _central_balls(el: fl.Element) -> List[Ball]:
    out = []
    for level in CENTRAL_LEVELS:
        for row, count in ((0, 8), (1, 7)):
            for k in range(count):
                out.append(Ball(f"central_ball_{len(out)}", el.x + (row - 0.5) * (BALL_D + 6),
                                el.y + (k - (count - 1) / 2) * (BALL_D + 4), level + BALL_D / 2))
    return out


def field_balls(elements: List[fl.Element], scenario: str = "initial") -> List[Ball]:
    if scenario not in SCENARIOS:
        raise ValueError(f"ball scenario must be one of {SCENARIOS}")
    if scenario == "none":
        return []
    balls = []
    for el in elements:
        if el.kind == "overhead" and "_resource_" in el.name:
            balls += _released_balls(el) if scenario == "released" else _resource_box_balls(el)
        elif el.name == "central_resource":
            balls += _central_balls(el)
    return balls


@dataclass
class Intake:
    port: str = "DC1"
    direction: int = 1                 # +1: positive power collects
    min_power: float = 30.0            # % on the port to count as running
    x_min: float = 200.0               # zone, robot frame mm (x forward, y left)
    x_max: float = 285.0
    y_min: float = -190.0
    y_max: float = 208.0
    max_ball_center_z: float = 60.0    # floor balls (centre 35 mm) only
    capacity: int = 18
    max_lift_mm: float = 20.0          # intake head must be down (mechanisms "intake_lift")
    collected: List[str] = field(default_factory=list)

    def running(self, power: float) -> bool:
        return power * self.direction >= self.min_power

    def contains(self, pose: RobotPose, ball: Ball) -> bool:
        dx, dy = ball.x - pose.x, ball.y - pose.y
        c, s = math.cos(pose.theta), math.sin(pose.theta)
        fx, ly = dx * c + dy * s, -dx * s + dy * c
        return self.x_min <= fx <= self.x_max and self.y_min <= ly <= self.y_max

    def update(self, pose: RobotPose, balls: List[Ball], power: float) -> int:
        """Collect what is in reach; returns how many balls were collected this call."""
        if not self.running(power):
            return 0
        got = 0
        for ball in balls:
            if len(self.collected) >= self.capacity:
                break
            if not ball.collected and ball.z <= self.max_ball_center_z and self.contains(pose, ball):
                ball.collected = True
                self.collected.append(ball.name)
                got += 1
        return got

    def reset(self) -> None:
        self.collected = []


def load_intake(path: Path = DEFAULT_CONFIG) -> Optional[Intake]:
    """robot_config.json "intake" section, or None if the robot has none."""
    data = json.loads(Path(path).read_text()).get("intake")
    if not data:
        return None
    zone: Dict[str, float] = data.get("zone_mm", {})
    return Intake(port=str(data.get("port", "DC1")), direction=int(data.get("direction", 1)),
                  min_power=float(data.get("min_power", 30.0)),
                  x_min=float(zone.get("x_min", 200.0)), x_max=float(zone.get("x_max", 285.0)),
                  y_min=float(zone.get("y_min", -190.0)), y_max=float(zone.get("y_max", 208.0)),
                  max_ball_center_z=float(data.get("max_ball_center_z_mm", 60.0)),
                  capacity=int(data.get("capacity", 18)),
                  max_lift_mm=float(data.get("max_lift_mm", 20.0)))
