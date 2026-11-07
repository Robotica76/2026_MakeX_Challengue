"""Team flag (final stage, rules guide V1.1 p.15-16, p.47, T17).

The flag is mounted on the mast in the modification stage (FLAG_mastil on the elevator carriage,
v22 CAD) and carried into the final stage. Its top edge (the suspension rod, at most
400 x 10 x 10 mm) runs along the robot's forward axis on the right side; robot_config.json
"team_flag" gives the rod in the robot frame with the carriage down.

Hanging (model): the rod must be parallel to a flagpole of the alliance (the horizontal pole,
x 0-120 mm from the back wall, 961 mm high), overlap it along its length by `min_overlap_mm`, be
within `y_tolerance_mm` of it sideways, and come down onto it: when the rod is over the pole and
the carriage lowers it below the pole top, the flag stays on the pole. It scores 50 if it hangs
and nothing of the robot touches it (the holder has moved `clear_mm` away).
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import field_layout as fl
from robot import DEFAULT_CONFIG

FLAG_POINTS = 50


@dataclass
class TeamFlag:
    rod_front: float                 # robot frame x of the rod's front end (mm)
    rod_back: float
    rod_y: float                     # robot frame y (left +)
    rod_z: float                     # rod height with the carriage down
    poles: List[Tuple[str, float, float, float, float, float]]   # name, x0, y0, x1, y1, top z
    min_overlap_mm: float = 30.0
    y_tolerance_mm: float = 15.0
    angle_tolerance_deg: float = 10.0
    clear_mm: float = 50.0
    state: str = "stowed"            # stowed (no mast) | carried | hung
    pole: Optional[str] = None
    hung_at: Optional[float] = None
    touching: bool = False
    _hang_x: Tuple[float, float] = field(default=(0.0, 0.0))

    def rod_field(self, pose, carriage: float):
        (x0, y0), (x1, y1) = pose.to_field(self.rod_back, self.rod_y), pose.to_field(self.rod_front, self.rod_y)
        return (x0, y0), (x1, y1), self.rod_z + carriage

    def best_pole(self, pose, carriage: float):
        """(pole name, overlap along the pole, sideways offset, angle off) of the nearest pole."""
        (ax, ay), (bx, by), _ = self.rod_field(pose, carriage)
        best = None
        for name, x0, y0, x1, y1, top in self.poles:
            py = (y0 + y1) / 2
            overlap = min(max(ax, bx), x1) - max(min(ax, bx), x0)
            angle = abs((math.degrees(math.atan2(by - ay, bx - ax)) + 90) % 180 - 90)
            off = abs((ay + by) / 2 - py)
            if best is None or off < best[2]:
                best = (name, overlap, off, angle, top)
        return best

    def update(self, t: float, pose, carriage: float) -> None:
        if self.state == "carried":
            pole = self.best_pole(pose, carriage)
            if pole is None:
                return
            name, overlap, off, angle, top = pole
            _, _, z = self.rod_field(pose, carriage)
            if (overlap >= self.min_overlap_mm and off <= self.y_tolerance_mm
                    and angle <= self.angle_tolerance_deg and z <= top):
                self.state, self.pole, self.hung_at, self.touching = "hung", name, t, True
                (ax, _), (bx, _), _ = self.rod_field(pose, carriage)
                self._hang_x = (min(ax, bx), max(ax, bx))
        elif self.state == "hung" and self.touching:
            (ax, ay), (bx, by), _ = self.rod_field(pose, carriage)
            lo, hi = self._hang_x
            pole_y = next((p[2] + p[4]) / 2 for p in self.poles if p[0] == self.pole)
            gap = max(lo - max(ax, bx), min(ax, bx) - hi, abs((ay + by) / 2 - pole_y) - self.y_tolerance_mm)
            self.touching = gap < self.clear_mm

    @property
    def points(self) -> int:
        return FLAG_POINTS if self.state == "hung" and not self.touching else 0


def load_flag(alliance: str, path: Path = DEFAULT_CONFIG, elements=None) -> Optional[TeamFlag]:
    data = json.loads(Path(path).read_text()).get("team_flag")
    if not data:
        return None
    elements = elements or fl.build_field()
    poles = [(el.name, *el.bounds(), el.z) for el in elements
             if el.alliance == alliance and el.name.startswith(f"{alliance}_flag_")]
    front = float(data.get("rod_front_override_mm") or data["rod_front_mm"])
    side = float(data.get("rod_y_override_mm") or data["rod_y_mm"])
    return TeamFlag(front, float(data["rod_back_mm"]), side, float(data["rod_z_mm"]), poles,
                    float(data.get("min_overlap_mm", 30.0)), float(data.get("y_tolerance_mm", 15.0)))
