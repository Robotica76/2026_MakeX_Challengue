"""Robot footprint loaded from robot_config.json (a box with 4 mecanum wheels).

Robot frame: x forward (along length), y left (along width), origin at the
footprint centre. Length and width are the overall footprint, wheels included.
Wheels sit in the footprint corners unless robot_config.json gives explicit
"wheel_centers_mm" (e.g. from CAD, when the wheel rectangle is off-centre).
"""

import json
import math
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from field_layout import Element, get

MAX_FOOTPRINT_MM = 500.0  # rules p.54 T01: 500 x 500 mm before and after modification
DEFAULT_CONFIG = Path(__file__).with_name("robot_config.json")

Point = Tuple[float, float]
WHEEL_NAMES = ("front_left", "front_right", "rear_left", "rear_right")


@dataclass(frozen=True)
class RobotConfig:
    name: str
    drive: str
    length_mm: float
    width_mm: float
    wheel_diameter_mm: float
    alliance: str
    start_area: str
    heading_deg: float
    wheel_width_mm: float = 40.0
    # Explicit wheel centres, robot frame mm: ((name, x, y), ...) in WHEEL_NAMES order.
    wheel_centers_mm: Optional[Tuple[Tuple[str, float, float], ...]] = None

    def validate(self) -> None:
        for dim in ("length_mm", "width_mm"):
            value = getattr(self, dim)
            if not 0 < value <= MAX_FOOTPRINT_MM:
                raise ValueError(f"{dim}={value:g} must be in (0, {MAX_FOOTPRINT_MM:g}] mm (rules T01)")
        # Two wheels must fit along each side without overlapping.
        if self.length_mm < 2 * self.wheel_diameter_mm:
            raise ValueError(f"length_mm={self.length_mm:g} is shorter than two wheels "
                             f"({2 * self.wheel_diameter_mm:g} mm)")
        if self.width_mm < 2 * self.wheel_width_mm:
            raise ValueError(f"width_mm={self.width_mm:g} is narrower than two wheels "
                             f"({2 * self.wheel_width_mm:g} mm)")
        if self.wheel_centers_mm is not None:
            if tuple(name for name, _, _ in self.wheel_centers_mm) != WHEEL_NAMES:
                raise ValueError(f"wheel_centers_mm must list {WHEEL_NAMES}")
            for name, x, y in self.wheel_centers_mm:
                if (abs(x) + self.wheel_diameter_mm / 2 > self.length_mm / 2 + 0.5
                        or abs(y) + self.wheel_width_mm / 2 > self.width_mm / 2 + 0.5):
                    raise ValueError(f"wheel {name} at ({x:g}, {y:g}) mm sticks out of the "
                                     f"{self.length_mm:g} x {self.width_mm:g} mm footprint")

    def resized(self, length_mm: float, width_mm: float) -> "RobotConfig":
        """Copy with new footprint; raises ValueError if it breaks the limits.

        Explicit CAD wheel centres belong to the CAD footprint, so a resized robot
        goes back to wheels in the corners."""
        cfg = replace(self, length_mm=float(length_mm), width_mm=float(width_mm), wheel_centers_mm=None)
        cfg.validate()
        return cfg


def _wheel_centers_from_json(value: Optional[Dict[str, List[float]]]):
    if value is None:
        return None
    missing = [name for name in WHEEL_NAMES if name not in value]
    if missing:
        raise ValueError(f"wheel_centers_mm is missing {missing}")
    return tuple((name, float(value[name][0]), float(value[name][1])) for name in WHEEL_NAMES)


def load_config(path: Path = DEFAULT_CONFIG) -> RobotConfig:
    """Footprint/start fields only; other sections (e.g. drive_train) are read elsewhere."""
    data = json.loads(Path(path).read_text())
    values = {f.name: data[f.name] for f in fields(RobotConfig) if f.name in data}
    values["wheel_centers_mm"] = _wheel_centers_from_json(values.get("wheel_centers_mm"))
    cfg = RobotConfig(**values)
    cfg.validate()
    return cfg


def save_config(cfg: RobotConfig, path: Path = DEFAULT_CONFIG) -> None:
    """Update the footprint/start fields, keeping any other sections in the file."""
    path = Path(path)
    data = json.loads(path.read_text()) if path.exists() else {}
    values = asdict(cfg)
    if cfg.wheel_centers_mm is None:
        values.pop("wheel_centers_mm")
        data.pop("wheel_centers_mm", None)   # a resized robot has its wheels in the corners
    else:
        values["wheel_centers_mm"] = {name: [x, y] for name, x, y in cfg.wheel_centers_mm}
    data.update(values)
    path.write_text(json.dumps(data, indent=2) + "\n")


@dataclass(frozen=True)
class Wheel:
    name: str              # front_left | front_right | rear_left | rear_right
    center: Point          # robot frame, mm
    roller_dir: Point      # unit vector of the top-visible rollers, robot frame


def mecanum_wheels(cfg: RobotConfig) -> List[Wheel]:
    """Wheels in the corners of the footprint (or at wheel_centers_mm), rollers in the
    standard "X" layout.

    Seen from above, the top rollers of each wheel point along the diagonal from the
    robot centre to that corner (front-left and rear-right parallel, front-right and
    rear-left parallel), so the ground-contact rollers form an "O".
    """
    cx = cfg.length_mm / 2 - cfg.wheel_diameter_mm / 2
    cy = cfg.width_mm / 2 - cfg.wheel_width_mm / 2
    explicit = {name: (x, y) for name, x, y in cfg.wheel_centers_mm or ()}
    k = math.sqrt(0.5)
    wheels = []
    for name, sx, sy in (("front_left", 1, 1), ("front_right", 1, -1),
                         ("rear_left", -1, 1), ("rear_right", -1, -1)):
        wheels.append(Wheel(name, explicit.get(name, (sx * cx, sy * cy)), (sx * sy * k, k)))
    return wheels


@dataclass
class RobotPose:
    x: float
    y: float
    theta: float  # rad, CCW from +x

    def to_field(self, px: float, py: float) -> Point:
        c, s = math.cos(self.theta), math.sin(self.theta)
        return self.x + px * c - py * s, self.y + px * s + py * c

    def box(self, cx: float, cy: float, length: float, width: float) -> List[Point]:
        """Corners (field mm) of a box centred at (cx, cy) in the robot frame."""
        hl, hw = length / 2, width / 2
        return [self.to_field(cx + dx, cy + dy)
                for dx, dy in ((hl, hw), (-hl, hw), (-hl, -hw), (hl, -hw))]

    def corners(self, cfg: RobotConfig) -> List[Point]:
        """Footprint corners in field mm; length runs along the heading."""
        return self.box(0.0, 0.0, cfg.length_mm, cfg.width_mm)


def start_pose(cfg: RobotConfig, elements: List[Element]) -> RobotPose:
    area = get(elements, cfg.start_area)
    return RobotPose(area.x, area.y, math.radians(cfg.heading_deg))
