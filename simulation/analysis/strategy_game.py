"""2 vs 2 Storm Breaker match at the level of robot missions (macro actions), fast enough for Monte
Carlo and reinforcement learning (~0.1 ms a match). Four identical robots (the v22 robot with the
430 mm elevator): red lower (ours), red upper (partner), blue lower and blue upper; each lower robot
faces the other alliance's lower robot across the lower strategy area and the central table.

Durations, yields and success rates come from the detailed simulator runs (simulate_driver.py,
montecarlo_routes.py, two_robots.py, fortress tests): see CALIBRATION. Shared, contested resources:
the bonus cubes and cones of each strategy area (whoever pulls first gets them; more than two bonus
cubes on an alliance's side invalidates all of them, p.30 d), the central table balls of each half,
the X mark (the last hit before the end wins; "both" colours score for both alliances) and the two
mobile fortresses: a robot can push its own fortress up to 300 mm within its area (p.25), and a
shooter that aims at fixed coordinates (odometry, like storm_breaker_2026) then misses (measured:
13 shots, 10 in at 0 mm, 0 at 150 mm north or east, 7 at 150 mm south). Physical blocking of the
opponents is not modelled: R27 forbids it (-20, then -120).

Plans (per robot, chosen at the start): an automatic order, a manual plan, a final plan and the time
of the last shots at the X mark. A step that does not fit in its stage is skipped.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

STAGES = {"auto": (0.0, 29.0), "manual": (30.0, 124.0), "final": (190.0, 279.0)}
CALIBRATION = {
    # automatic stage (montecarlo_routes.py, storm_breaker_2026 missions)
    "start_s": 3.0,
    "bonus": {"s": 14.0, "p": 0.97, "reach_s": 5.0},       # X12 in the exchange area at 15.2 s (3 s start)
    "deny": {"s": 9.0, "p": 0.95},                          # X9 + cone a to our side: done ~26 s after B
    "table": {"s": 8.0, "take": 11, "p": 0.95},             # one table level, intake on
    "auto_shot": {"s": 6.0, "conv": 0.80},                  # shot after the table passes (9 of 11)
    "evade": {"s": 7.0, "mm": 200.0, "p_tilt": 0.01},       # push our own fortress (150 mm/s, gently)
    # manual stage (simulate_driver.py: sweeps of resource area 1, shots from (1600, 900))
    "sweep": {"s": 16.0, "first": 0.75, "cap": 14, "conv": 0.85},
    "cone": {"s": 19.0, "p": 0.95},                         # hang a cone on our post (430 mm elevator)
    "pull": {"s": 9.0, "p": 0.9},                           # pull a prop off the strategy area (N2)
    "table_manual": {"s": 15.0, "take": 11},
    "return_s": 6.0,                                        # into the starting area before 130 s
    # final stage
    "letters": {"s": 63.0, "n": 2, "p": 0.9},               # K, E (fortress cube level -> channels)
    "letter1": {"s": 35.0, "n": 1, "p": 0.9},
    "flag": {"s": 15.0, "p": 0.95, "push_mm": 290.0},      # the routine pushes our fortress
    "final_sweep": {"s": 12.0},
    "x": {"keep": 2, "flight_s": 1.9, "gap_s": 0.45, "jitter_s": 0.25, "p_hit": 0.6},
    "own_balls": 10, "table_balls_half": 15, "capacity": 18,
}

AUTO_PLANS = ["", "B", "BD", "BT", "T", "TT", "D", "BE", "E", "TE", "DB"]
MANUAL_PLANS = ["SS", "SSC", "SC", "SCC", "PC", "PCC", "SST", "ST", "SSE", "ESS", "SCE", "TT"]
FINAL_PLANS = ["LF", "FL", "F", "FS", "L", "LFX", "FX", "FSX", "lF", "lFX"]
X_TIMES = [276.8, 277.3, 277.8, 270.0]
CODES = {"B": "bonus cube to the exchange area", "D": "deny: second cube + cone to our side",
         "T": "central table balls (in, then shot)", "E": "push our fortress (evade fixed-aim shots)",
         "S": "sweep own resource area + shoot", "C": "hang a cone", "P": "pull a prop off the strategy area",
         "L": "letter cubes K and E", "l": "one letter cube", "F": "team flag", "X": "keep 2 balls for the X at the end"}


@dataclass
class Plan:
    auto: str = "BD"
    manual: str = "SSC"
    final: str = "LFX"
    x_time: float = 276.8

    def label(self) -> str:
        return f"{self.auto or '-'}/{self.manual}/{self.final}@{self.x_time:g}"


@dataclass
class Robot:
    team: str
    half: str                      # lower | upper
    plan: Plan
    aim: str = "fixed"             # fixed (odometry coordinates) | adaptive (vision / driver)
    t: float = 0.0
    stored: int = 0
    cones_floor: int = 0
    log: List[str] = field(default_factory=list)
    out: bool = False              # disqualified (tilted the fortress, R02)
    reach: float = 5.0             # seconds to reach a bonus cube from the start of the mission


def fixed_aim_factor(offset_mm: float) -> float:
    """Fraction of fixed-aim shots still in a fortress moved `offset_mm` away / sideways from the
    shooters (measured, 13 shots: 10 in at 0, 9-11 at 50-100 mm, 0 at 150 mm north or east, 7 at
    150 mm south): the landings cluster 110-150 mm from the far edge, so it is a cliff."""
    d = abs(offset_mm)
    return 1.0 if d <= 100.0 else max(0.0, 1.0 - (d - 100.0) / 50.0)


class Match:
    def __init__(self, red: Tuple[Plan, Plan], blue: Tuple[Plan, Plan], rng: random.Random,
                 aims=("fixed", "fixed"), cal=CALIBRATION):
        self.rng, self.cal = rng, cal
        values = [3, 6, 9, 12]
        rng.shuffle(values)                                  # prop card
        self.cubes = {"lower": sorted(values[:2], reverse=True), "upper": sorted(values[2:], reverse=True)}
        self.cones = {"lower": 2, "upper": 2}
        self.table = {"lower": cal["table_balls_half"], "upper": cal["table_balls_half"]}
        self.robots = [Robot("red", "lower", red[0], aims[0]), Robot("red", "upper", red[1], aims[0]),
                       Robot("blue", "lower", blue[0], aims[1]), Robot("blue", "upper", blue[1], aims[1])]
        self.side_cubes = {"red": [], "blue": []}            # bonus cubes on the alliance's side
        self.exchange = {"red": [], "blue": []}              # in an exchange area at 30 s
        self.area = {}                                       # own resource-area balls per robot
        self.fort = {"red": [], "blue": []}                  # (time, offset mm) history
        self.shots = {"red": [], "blue": []}                 # (time, balls in the opponent fortress, aim)
        self.points = {"red": {}, "blue": {}}
        self.x_hits = []                                     # (time, team)

    # -- helpers -------------------------------------------------------------------------
    def add(self, team, key, v):
        self.points[team][key] = self.points[team].get(key, 0) + v

    def offset(self, team, t) -> float:
        off = 0.0
        for tt, o in self.fort[team]:
            if tt <= t:
                off = o
        return off

    def jitter(self, s):
        return s * self.rng.uniform(0.9, 1.15)

    def fits(self, r, s, stage):
        return r.t + s <= STAGES[stage][1]

    def shoot(self, r, n, conv, t):
        if n <= 0:
            return
        opp = "blue" if r.team == "red" else "red"
        self.shots[r.team].append((t, sum(self.rng.random() < conv for _ in range(n)), r.aim, opp))

    # -- steps ---------------------------------------------------------------------------
    def step(self, r: Robot, code: str, stage: str):
        c, rng = self.cal, self.rng
        team, opp = r.team, ("blue" if r.team == "red" else "red")
        if code == "B":                                      # best cube left in our half -> exchange area
            s = self.jitter(c["bonus"]["s"])
            if not self.fits(r, s, stage):
                return
            if not self.cubes[r.half]:                       # the facing robot got there first
                r.t += r.reach + 2.0
                r.log.append("B lost")
                return
            value = self.cubes[r.half].pop(0)
            if rng.random() < c["bonus"]["p"]:
                self.side_cubes[team].append(value)
                self.exchange[team].append(value)
                if self.cones[r.half] > 0:
                    r.cones_floor += 1
                    self.cones[r.half] -= 1
                r.log.append(f"B {value}")
            else:
                self.cubes[r.half].append(value)
            r.t += s
        elif code == "D":                                    # deny: a cube and a cone to our side
            s = self.jitter(c["deny"]["s"])
            if not self.fits(r, s, stage):
                return
            if rng.random() < c["deny"]["p"]:
                if self.cubes[r.half]:
                    value = self.cubes[r.half].pop()
                    self.side_cubes[team].append(value)
                if self.cones[r.half] > 0:
                    self.cones[r.half] -= 1
                    r.cones_floor += 1
            r.t += s
        elif code == "T":                                    # table balls taken in
            key = "table" if stage == "auto" else "table_manual"
            s = self.jitter(c[key]["s"])
            if not self.fits(r, s, stage):
                return
            take = min(c[key]["take"], self.table[r.half], c["capacity"] - r.stored)
            self.table[r.half] -= take
            r.stored += take
            r.t += s
        elif code == "E":                                    # push our own fortress (gently)
            s = self.jitter(c["evade"]["s"])
            if not self.fits(r, s, stage):
                return
            now = self.offset(team, r.t)
            if abs(now) < 300:
                r.t += s
                self.fort[team].append((r.t, now + c["evade"]["mm"]))
                if rng.random() < c["evade"]["p_tilt"]:
                    r.out = True
                    self.add(team, "penalties", -20)
        elif code == "S":                                    # sweep own resource area, shoot
            s = self.jitter(c["sweep"]["s"])
            if not self.fits(r, s, stage):
                return
            avail = self.area[id(r)]
            take = min(c["sweep"]["cap"], c["capacity"] - r.stored, max(1, round(avail * c["sweep"]["first"])), avail)
            self.area[id(r)] -= take
            r.stored += take
            r.t += s
            keep = c["x"]["keep"] if "X" in r.plan.final else 0
            n = max(0, r.stored - keep)
            self.shoot(r, n, c["sweep"]["conv"], r.t)
            r.stored -= n
        elif code == "C":
            s = self.jitter(c["cone"]["s"])
            if not self.fits(r, s, stage) or r.cones_floor <= 0:
                return
            r.cones_floor -= 1
            r.t += s
            if rng.random() < c["cone"]["p"]:
                self.add(team, "cones", 20)
        elif code == "P":
            s = self.jitter(c["pull"]["s"])
            if not self.fits(r, s, stage):
                return
            r.t += s
            if self.cones[r.half] > 0 and rng.random() < c["pull"]["p"]:
                self.cones[r.half] -= 1
                r.cones_floor += 1
        elif code in ("L", "l"):
            key = "letters" if code == "L" else "letter1"
            s = self.jitter(c[key]["s"])
            if not self.fits(r, s, stage):
                return
            r.t += s
            self.add(team, "letters", 30 * sum(rng.random() < c[key]["p"] for _ in range(c[key]["n"])))
        elif code == "F":
            s = self.jitter(c["flag"]["s"])
            if not self.fits(r, s, stage):
                return
            r.t += s
            if rng.random() < c["flag"]["p"]:
                self.add(team, "flag", 50)
            sign = 1 if r.half == "lower" else -1            # the lower robot pushes it north, the upper south
            self.fort[team].append((r.t, self.offset(team, r.t) + sign * c["flag"]["push_mm"]))

    def run_stage(self, stage, codes_of):
        for r in self.robots:
            r.t = STAGES[stage][0] + (self.cal["start_s"] if stage == "auto" else 0.5) + self.rng.uniform(0.0, 0.3)
        # interleave by time so contested resources go to whoever gets there first
        queues = {id(r): list(codes_of(r)) for r in self.robots}
        for r in self.robots:
            r.reach = self.cal["bonus"]["reach_s"] * self.rng.uniform(0.85, 1.2)

        def when(r):                                         # a cube goes to whoever reaches it first
            return r.t + (r.reach if queues[id(r)][0] == "B" else 0.0)
        while any(queues.values()):
            r = min((r for r in self.robots if queues[id(r)]), key=when)
            code = queues[id(r)].pop(0)
            if not r.out:
                self.step(r, code, stage)
            r.reach = self.cal["bonus"]["reach_s"] * self.rng.uniform(0.85, 1.2)
        if stage == "auto":
            for r in self.robots:                            # balls taken in: shot before parking
                if r.stored and not r.out:
                    self.shoot(r, r.stored, self.cal["auto_shot"]["conv"], 29.0)
                    r.stored = 0

    def x_mark(self):
        c = self.cal["x"]
        for r in self.robots:
            if "X" not in r.plan.final or r.out or r.stored <= 0:
                continue
            t0 = r.plan.x_time
            for k in range(r.stored):
                hit_t = t0 + c["flight_s"] + k * c["gap_s"] + self.rng.gauss(0.0, c["jitter_s"])
                if hit_t < 280.0 and self.rng.random() < c["p_hit"]:
                    self.x_hits.append((hit_t, r.team))
            r.stored = 0
        state = "both"
        for _, team in sorted(self.x_hits):
            state = team
        for team in ("red", "blue"):
            if state in ("both", team):
                self.add(team, "x_mark", 30)
        return state

    def play(self) -> Dict[str, dict]:
        c = self.cal
        for r in self.robots:
            self.area[id(r)] = c["own_balls"]
        self.run_stage("auto", lambda r: r.plan.auto)
        for team in ("red", "blue"):                          # bonus judged at 30 s (p.30)
            valid = self.exchange[team] if len(self.side_cubes[team]) <= 2 else []
            self.points[team]["bonus_balls"] = sum(valid)
            lower = next(r for r in self.robots if r.team == team and r.half == "lower")
            self.area[id(lower)] += sum(valid)               # bonus balls in resource area 1
        self.run_stage("manual", lambda r: r.plan.manual)
        self.run_stage("final", lambda r: [ch for ch in r.plan.final if ch in "LlFS"])
        x = self.x_mark()
        for team in ("red", "blue"):                          # precision throwing at scoring time
            opp = "blue" if team == "red" else "red"
            n = 0
            for t, k, aim, target in self.shots[team]:
                factor = fixed_aim_factor(self.offset(target, t)) if aim == "fixed" else 0.95
                n += sum(self.rng.random() < factor for _ in range(k))
            bonus = self.points[team]["bonus_balls"]
            self.points[team]["precision"] = min(n, bonus) * 20 + max(0, n - bonus) * 10
            self.points[team]["balls"] = n
        out = {}
        for team in ("red", "blue"):
            p = self.points[team]
            total = sum(v for k, v in p.items() if k not in ("bonus_balls", "balls"))
            out[team] = {**p, "total": total}
        out["x_mark"] = x
        out["cubes"] = {k: list(v) for k, v in self.side_cubes.items()}
        return out


def play(red, blue, seed=None, aims=("fixed", "fixed")):
    return Match(red, blue, random.Random(seed), aims).play()


# opponent / partner styles, built from the detailed simulator's plans
ARCHETYPES = {
    "current (ours)": (Plan("BD", "SSC", "LFX", 277.3), Plan("B", "SSC", "LFX", 277.3)),
    "bonus greedy": (Plan("B", "SS", "FS", 276.8), Plan("B", "SS", "FS", 276.8)),
    "ball rush": (Plan("TT", "SST", "FS", 276.8), Plan("TT", "SST", "FS", 276.8)),
    "denial": (Plan("BD", "PCC", "LF", 276.8), Plan("DB", "PC", "LF", 276.8)),
    "evader": (Plan("BE", "SSC", "LFX", 277.8), Plan("B", "ESS", "LFX", 277.8)),
    "late X": (Plan("B", "SS", "FSX", 277.8), Plan("B", "SS", "FSX", 277.8)),
}
