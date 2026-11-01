"""Referee actions between stages and the match score (rules guide V1.1 p.30-50).

At the start of the manual stage (p.30, p.32):
  - the bonus cubes are judged (props.bonus_state: in the own exchange area, one per area, at
    most two on the alliance's side, not touching the robot); the referees put the exchanged
    balls (X3..X12) into the alliance's own resource area 1
  - the observers remove the baffles: the balls of both own resource areas, bonus balls
    included, roll onto the floor in front of them (positions: balls.RELEASE_GAP, estimate)

Match score at the end (p.36-50, table p.53-54), per alliance:
  precision throwing  balls completely inside the opponent fortress upper area: 20 each up to
                      the bonus quantity, 10 each beyond
  cones               20 each, hung on the alliance's cone posts
  letter cubes        30 each in a strategy channel (+50 per complete MAKE side, not judged)
  team flag           50, hung on an own flagpole in the final stage (flag.py)
  penalties           -20 per R06 violation (body outside the area > 3 s), -20 if moving at 30 s (R19)
  not simulated       pins (10 / 30), X mark (30)

End of the manual stage (p.53): the robot goes back (partly) into its starting area, is taken out
for the modification stage (60 s, flag mast installed) and returns to the starting area.
"""

from typing import Dict, List

import field_layout as fl
from ball_physics import R, fortress_regions
from balls import BALL_D, RELEASE_GAP, Ball
from props import bonus_state, score_preview

MANUAL_START_S = 30.0
MODIFICATION_START_S = 130.0     # after the manual stage (100 s); the final stage starts at 190 s
FINAL_START_S = 190.0
OPPONENT = {"red": "blue", "blue": "red"}


def _release_rows(el: fl.Element, first_row: int, count: int, prefix: str) -> List[Ball]:
    sign = 1 if el.y < fl.CY else -1
    front = el.y + sign * el.h / 2
    out = []
    for i in range(count):
        row, k = first_row + i // 5, i % 5
        out.append(Ball(f"{prefix}_{i}", el.x + (k - 2) * (BALL_D + 10),
                        front + sign * (RELEASE_GAP + BALL_D / 2 + row * (BALL_D + 10)), BALL_D / 2))
    return out


def manual_stage_start(sim) -> Dict[str, dict]:
    """Bonus exchange and baffles removed; returns the bonus judgement per alliance."""
    judged = {a: bonus_state(sim.props, sim.elements, a) for a in ("red", "blue")}
    areas = {el.name: el for el in sim.elements if el.kind == "overhead" and "_resource_" in el.name}
    for name, el in areas.items():
        on_shelf = [b for b in sim.balls if b.name.startswith(name + "_ball_") and b.state == "field" and b.z > 500]
        for b, spot in zip(on_shelf, _release_rows(el, 0, len(on_shelf), "spot")):
            b.x, b.y, b.z, b.vx, b.vy, b.vz, b.asleep = spot.x, spot.y, spot.z, 0.0, 0.0, 0.0, True
    for alliance, bonus in judged.items():
        area = areas.get(f"{alliance}_resource_1")
        if area is not None and bonus["bonus_balls"]:
            sim.balls.extend(_release_rows(area, 2, bonus["bonus_balls"], f"{alliance}_bonus_ball"))
    return judged


def modification_stage(sim) -> Dict[str, object]:
    """End of the manual stage: the robot must be (partly) in its starting area to be taken out and
    modified (p.53); it comes back in the starting area with the flag mast for the final stage."""
    area = next(el for el in sim.elements if el.name == sim.cfg.start_area)
    x0, y0, x1, y1 = area.bounds()
    corners = sim.pose.corners(sim.cfg)
    cx = [x for x, _ in corners]
    cy = [y for _, y in corners]
    in_start = min(cx) < x1 and max(cx) > x0 and min(cy) < y1 and max(cy) > y0
    sim.pose = sim.start_pose                  # back in the starting area after the modification
    if sim.flag is not None and in_start:
        sim.flag.state = "carried"
    return {"in_start_area": in_start, "flag_mounted": bool(sim.flag and in_start)}


def balls_scored(sim, alliance: str) -> int:
    """Balls with their projection completely inside the opponent fortress upper area (p.36)."""
    if not sim.world:
        return 0
    x0, y0, z0, x1, y1, z1 = fortress_regions(sim.elements)[OPPONENT[alliance]]
    return sum(1 for b in sim.balls if b.state == "field" and x0 + R <= b.x <= x1 - R
               and y0 + R <= b.y <= y1 - R and z0 <= b.z <= z1)


def match_score(sim, alliance: str = "red") -> Dict[str, object]:
    bonus = (getattr(sim, "bonus_judged", None) or {}).get(alliance, {"bonus_balls": 0, "valid": []})
    n, extra = balls_scored(sim, alliance), bonus["bonus_balls"]
    precision = min(n, extra) * 20 + max(0, n - extra) * 10
    prev = score_preview(sim.props, sim.elements, alliance)
    cones, letters = prev["cones"] * 20, prev["letter_cubes"] * 30
    flag = sim.flag.points if getattr(sim, "flag", None) and alliance == sim.cfg.alliance else 0
    penalties = 0
    monitor = getattr(sim, "monitor", None)
    if monitor is not None and alliance == sim.cfg.alliance:
        penalties += 20 * monitor.r06_penalties                                  # R06: outside > 3 s
        if monitor.auto_end is not None and not monitor.auto_end["stationary"]:
            penalties += 20                                                      # R19: moving at 30 s
    return {"balls": n, "bonus_balls": extra, "bonus_cubes": bonus["valid"], "precision": precision,
            "cones": cones, "letter_cubes": letters, "flag": flag, "penalties": penalties,
            "total": precision + cones + letters + flag - penalties, "not_simulated": "pins, X mark"}
