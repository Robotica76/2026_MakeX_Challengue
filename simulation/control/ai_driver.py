"""Scripted driver for storm_breaker_2026 in the simulator: plays the Bluetooth gamepad the way the
driver would, closing the loop on the robot pose from the state stream.

    viewer3d.py --program ../../software/robot/main/storm_breaker_2026.mblock --time-limit 280 \\
                --driver ../control/ai_driver.py --autorun

Protocol: reads the viewer's UDP state stream (state_stream.py, 127.0.0.1:5005) and prints gamepad
events (gamepad.py JSON lines) that the viewer feeds to the program. The same Driver class runs
inside a headless simulation (simulation/analysis/simulate_driver.py) to test and time the plan.

Plan (red alliance, Red Start 1, lower half of our area; robot_2026 controls of the program):
  0 s      N1: the program runs the automatic stage (X12 into exchange area 1, X9 and cones ours)
  30 s     manual: cone a hung on red cone post 2 (gripper, 430 mm elevator); sweep resource area 1
           twice and shoot (R2 aims at the blue fortress; N3 at the X mark if the opponent turned
           it); cone b hung; back into the starting area before 130 s (modification stage)
  190 s    final: K and E pulled off the fortress cube level (N2 pull mode), dragged clear, put
           into channels 3 and 4 with the gripper; back to Red Start 1, N4 hangs the flag
           (the flag routine pushes the fortress north on its casters, simulation fortress.py)
"""

import json
import math
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

STREAM = ("127.0.0.1", 5005)
STICK_MM_S = 800.0          # program: stick 100 % = 800 mm/s (drive_joystick_N)
TURN_DPS_PER_STICK = 200.0  # program: Rx 100 % = 200 deg/s
ACCEL_MM_S2 = 1000.0        # driver's braking profile
STICK_STEP = 0.1            # max stick change per update (~30 per second): smooth, no jumps
LATENCY_S = 0.12            # stream + event delay the driver compensates (predicted pose)
GRAB = (-89.0, -228.5)      # gripper grab point, robot frame (x forward, y left): right side
CARRIAGE_MM_S = 150.0       # elevator (Up/Down in gripper mode, power 100)
JAW_MM_S = 24.0             # jaw (Right closes / Left opens, power 60 of 40 mm/s)
CONE_POST = (200.0, 888.0)  # red_cone_post_2, the one in our half (405 mm tall)
CONE_LIFT = 425.0           # carriage: the cone bottom clears the post top (needs the 430 mm elevator)
CONE_LOWER = 300.0          # carriage: post 105 mm into the cone before opening the jaws
LETTER_LAT = -40.0          # a letter cube is taken 40 mm outward of the grab point: it sticks out past
                            # the jaws, so its centre gets over the channel rail with the robot outside
CHANNEL_RAIL_X = 2220.0     # strategy area west face: the channel rails start here
CHANNELS = {"M": 437.5, "A": 657.5, "K": 877.5, "E": 1097.5}   # lower side, outside to inside (MAKE)
FORTRESS_START = (662.0, 1527.5)
CONE_HEADING = 250.0       # at the post: gripper to the west-north-west, robot inside the field (cone_post_reach.py)


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


class Driver:
    def __init__(self):
        self.state = None
        self.events = []
        self.log = []
        self._plan = self.plan()
        self._sticks = (0.0, 0.0, 0.0)
        self.deadline = 1e9          # actions give up at this match time (stage ends)
        self.timed = []              # (release time, key): keys held while the robot does other things
        self.moves = []              # (label, seconds, reached / close / timeout)
        self.side = 0                # program front: 0 intake (mode ≡), 90 gripper (mode +)

    # -- gamepad -------------------------------------------------------------------------
    def press(self, key):
        self.events.append({"event": "press", "control": key})

    def release(self, key):
        self.events.append({"event": "release", "control": key})

    def sticks(self, lx, ly, rx):
        lx, ly, rx = (max(-1.0, min(1.0, v)) for v in (lx, ly, rx))
        if (round(lx, 2), round(ly, 2), round(rx, 2)) != self._sticks:
            self._sticks = (round(lx, 2), round(ly, 2), round(rx, 2))
            self.events.append({"event": "axis", "control": "left_stick", "x": lx, "y": ly})
            self.events.append({"event": "axis", "control": "right_stick", "x": rx, "y": 0.0})

    def say(self, text):
        self.log.append(f"{self.t:6.1f} s  {text}")

    @property
    def t(self):
        return self.state["t"] if self.state else 0.0

    @property
    def pose(self):
        p = self.state["pose"]
        return p["x_mm"], p["y_mm"], p["theta_deg"]

    def press_for(self, key, seconds):
        """Hold a key for `seconds` without waiting (e.g. the head moving while the robot drives).
        It replaces a hold of the same key or of the opposite arrow still running (an earlier
        release would cut it short)."""
        other = {"up": "down", "down": "up", "left": "right", "right": "left"}.get(key)
        if other and any(k == other for _, k in self.timed):
            self.release(other)
        self.timed = [i for i in self.timed if i[1] not in (key, other)]
        self.press(key)
        self.timed.append((self.t + seconds, key))

    def tick(self, state):
        self.state = state
        self.events = []
        for item in [i for i in self.timed if self.t >= i[0]]:
            self.release(item[1])
            self.timed.remove(item)
        try:
            next(self._plan)
        except StopIteration:
            self.sticks(0, 0, 0)
        return self.events

    # -- plan helpers (generators: yield = wait one tick) ----------------------------------
    def wait_until(self, t):
        while self.t < t:
            self.sticks(0, 0, 0)
            yield

    def wait(self, seconds):
        yield from self.wait_until(self.t + seconds)

    def tap(self, key, seconds=0.3):
        self.press(key)
        yield from self.wait(seconds)
        self.release(key)
        yield

    def head_to(self, mm):
        """Intake head to `mm` (53 mm/s) from its streamed height, while the robot does other things."""
        now = self.state.get("intake_lift_mm", 0.0)
        if abs(mm - now) > 5:
            self.press_for("up" if mm > now else "down", abs(mm - now) / 53.0)

    def predicted(self):
        """Pose LATENCY_S ahead, from the streamed velocity: the stream and the events each take
        about a frame, so the driver steers from where the robot will be."""
        px, py, th = self.pose
        v = self.state.get("velocity") or {}
        vx, vy, w = v.get("vx_mm_s", 0.0), v.get("vy_mm_s", 0.0), v.get("omega_deg_s", 0.0)
        c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
        return (px + (vx * c - vy * s) * LATENCY_S, py + (vx * s + vy * c) * LATENCY_S,
                th + w * LATENCY_S, math.hypot(vx, vy))

    def go(self, x, y, heading=None, vmax=800.0, tol=25.0, timeout=5.0, label="", htol=4.0):
        """Drive to field (x, y) mm (and heading, deg) with the sticks: speed profile sqrt(2 a d),
        rate-limited sticks, turning with hysteresis and while translating; steers from the
        predicted pose; done when inside `tol`, or close and nearly still (no hunting). It turns
        when the heading is more than `htol` deg off (1 for placing props)."""
        start = self.t
        end = min(self.t + timeout, self.deadline)
        turning, still_since, reason = False, None, "timeout"
        while self.t < end:
            px, py, th, speed_now = self.predicted()
            ex, ey = x - px, y - py
            dist = math.hypot(ex, ey)
            herr = wrap(heading - th) if heading is not None else 0.0
            if abs(herr) > htol:
                turning = True
            elif abs(herr) < htol / 2:
                turning = False
            if dist < tol and not turning:
                reason = "reached"
                break
            if dist < 2.5 * tol and abs(herr) < 1.5 * htol and speed_now < 40.0:
                still_since = self.t if still_since is None else still_since
                if self.t - still_since > 0.4:
                    reason = "close"
                    break
            else:
                still_since = None
            c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
            speed = 0.0 if dist < tol else min(vmax, math.sqrt(2 * ACCEL_MM_S2 * dist), 2.0 * dist)
            f = (ex * c + ey * s) / max(dist, 1e-6) * speed
            r = (ex * s - ey * c) / max(dist, 1e-6) * speed
            ly, lx = f / STICK_MM_S, r / STICK_MM_S
            if self.side == 90:                              # gripper front: Ly drives right, Lx back
                ly, lx = r / STICK_MM_S, -f / STICK_MM_S
            big = max(abs(lx), abs(ly))
            if 0 < big < 0.1:                                # past the program's deadzone (per axis), same direction
                lx, ly = lx / big * 0.1, ly / big * 0.1
            rx = 0.0
            if turning:
                ccw = max(-180.0, min(180.0, 3.5 * herr))
                rx = -ccw / TURN_DPS_PER_STICK
                if abs(rx) < 0.1:
                    rx = math.copysign(0.1, rx)
            plx, ply, prx = self._sticks
            lx = plx + max(-STICK_STEP, min(STICK_STEP, lx - plx))
            ly = ply + max(-STICK_STEP, min(STICK_STEP, ly - ply))
            rx = prx + max(-STICK_STEP, min(STICK_STEP, rx - prx))
            self.sticks(lx, ly, rx)
            yield
        while any(abs(v) > 1e-3 for v in self._sticks):     # ease the sticks back to zero
            plx, ply, prx = self._sticks
            self.sticks(*(v - max(-STICK_STEP, min(STICK_STEP, v)) for v in (plx, ply, prx)))
            yield
        self.moves.append((label or f"({x:.0f},{y:.0f})", round(self.t - start, 2), reason))
        if reason == "timeout":
            self.say(f"move to ({x:.0f}, {y:.0f}) timed out")

    def shoot(self, label, max_s=22.0, keep=0, key="R2"):
        """Hold R2 (fortress) or N3 (X mark): the program aims and sets the power; until `keep`
        balls are left inside."""
        start, n = self.t, self.state.get("stored", 0)
        self.say(f"{label}: {key} with {n} balls inside")
        self.press(key)
        end = min(self.t + max_s, self.deadline)
        while self.t < end and (self.state.get("stored", 0) > keep or self.t < start + 2.5):
            yield
        if not keep:
            yield from self.wait(0.8)
        self.release(key)
        yield from self.wait(0.3)
        self.say(f"{label}: done, score {self.state.get('score')}")

    def sweep_area_1(self, x_end, label, head_down_s=None):
        """Resource area 1: turn away from the balls, line up beside them with the head just over
        them, head to the floor and intake on while driving along the rows."""
        yield from self.go(1870, 1120, 180, label=label + " turn spot")
        _, py, _ = self.pose
        yield from self.go(1900, py, 180, tol=30, label=label + " line up")
        yield from self.go(1900, 640, 180, vmax=500, tol=25, label=label + " beside the rows")
        yield from self.go(1900, 600, 180, vmax=200, tol=20, label=label + " sweep start")
        self.press("L1")
        self.head_to(0)                                     # floor balls: head down at the sweep
        self.say(f"{label}: intake on")
        yield from self.go(x_end, 600, 180, vmax=260, tol=25, timeout=6, label=label + " sweep")
        if self.t < self.deadline:
            yield from self.wait(0.8)
        self.release("L1")
        self.say(f"{label}: {self.state.get('stored', 0)} balls inside")

    # -- cones ---------------------------------------------------------------------------
    @staticmethod
    def grab_pose(x, y, heading, out=0.0, lat=0.0):
        """Robot centre that puts the grab point on field (x, y) at `heading`; `out` mm further
        away on the gripper side (the slot is open to the right: the prop goes in sideways);
        `lat`: the prop centre that far beside the grab point (robot y, negative = outward)."""
        gx, gy = GRAB[0], GRAB[1] + lat - out
        c, s = math.cos(math.radians(heading)), math.sin(math.radians(heading))
        return x - (gx * c - gy * s), y - (gx * s + gy * c)

    def grab_error(self, x, y):
        px, py, th = self.pose
        c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
        return math.hypot(px + GRAB[0] * c - GRAB[1] * s - x, py + GRAB[0] * s + GRAB[1] * c - y)

    def mode(self, side):
        """"+" (90, gripper front: Up/Down carriage) or "≡" (0: Up/Down head), after the timed
        Up/Down holds of the other mode end."""
        if side != self.side:
            end = min(self.t + 8.0, self.deadline)
            while self.t < end and any(k in ("up", "down", "left", "right") for _, k in self.timed):
                yield
            yield from self.tap("plus" if side == 90 else "menu", 0.15)
            self.side = side

    def carriage_to(self, mm):
        now = self.state.get("carriage_mm", 0.0)
        if abs(mm - now) > 5:
            self.press_for("up" if mm > now else "down", abs(mm - now) / CARRIAGE_MM_S)

    def jaw(self, close, seconds):
        self.press_for("right" if close else "left", seconds)
        yield from self.wait(seconds + 0.1)

    def place(self, x, y, heading, label, tol=6.0):
        """Grab point onto (x, y) from the outside: turn north of the shelf legs (y >= 850), line up
        220 mm away (8 mm: the post must slide in between the jaws), then slide in."""
        lx, ly = self.grab_pose(x, y, heading, 220)
        if ly < 850 and self.pose[1] >= 600:
            yield from self.go(lx, 850, heading, tol=40, label=label + " turn spot")
        yield from self.go(lx, ly, heading, tol=20, label=label + " line up")
        yield from self.go(lx, ly, heading, vmax=200, tol=8, timeout=3, label=label + " line up fine")
        th = heading
        for _ in range(4):                                  # slide in, then correct with the heading it has
            yield from self.go(*self.grab_pose(x, y, th), th, vmax=250, tol=tol, timeout=4, label=label + " in")
            if self.grab_error(x, y) < 8.0:
                break
            th = self.pose[2]                               # a 4 deg heading error moves the jaws 17 mm

    @staticmethod
    def grab_heading(x, y, prefer=90.0):
        """Robot heading to take a floor cone at (x, y): the one nearest `prefer` where the robot
        clears the field structures (what the driver sees)."""
        from cone_post_reach import poses
        free = [r[0] for r in poses((x, y), 5) if r[3] == 0 and r[5] and r[6]]
        return min(free, key=lambda h: abs(wrap(h - prefer))) if free else None

    def free_cones(self):
        return [c for c in self.state.get("cones", []) if not c.get("post") and c["z_mm"] < 1.0
                and 300 < c["x_mm"] < 2300 and c["y_mm"] < 1400]

    def hang_cone(self, cone, label, prefer=90.0, via=()):
        """Floor cone -> red cone post 2 (20 points): gripper mode, carriage down, jaws open, grab
        it (heading nearest `prefer`), lift it over the post top (by the `via` waypoints), come in from the east-south-east, lower, open."""
        x, y = cone["x_mm"], cone["y_mm"]
        heading = self.grab_heading(x, y, prefer)
        self.say(f"{label}: cone at ({x:.0f}, {y:.0f}), grab heading {heading}")
        if heading is None:
            return False
        yield from self.mode(90)
        self.carriage_to(0)
        if self.state.get("jaw_mm", 0.0) > 1:
            self.press_for("left", self.state["jaw_mm"] / JAW_MM_S + 0.3)
        yield from self.place(x, y, heading, label + " grab")
        yield from self.wait(max(0.0, max(t for t, _ in self.timed) - self.t) if self.timed else 0.0)
        yield from self.jaw(True, 56.0 / JAW_MM_S)          # 138 -> 82 mm on the 90 mm body
        if self.state.get("held") != "cone":
            self.say(f"{label}: missed the cone")
            yield from self.jaw(False, 2.5)
            return False
        self.carriage_to(CONE_LIFT)                         # lifts while driving
        yield from self.go(*self.grab_pose(x, y, heading, 220), heading, tol=40, label=label + " out")
        for wx, wy, wh in via:
            yield from self.go(wx, wy, wh, tol=60, label=label + " via")
        yield from self.place(*CONE_POST, CONE_HEADING, label + " post")
        while self.t < self.deadline and self.state.get("carriage_mm", 0) < CONE_LIFT - 5:
            yield
        yield from self.wait(0.2)
        self.carriage_to(CONE_LOWER)
        yield from self.wait((CONE_LIFT - CONE_LOWER) / CARRIAGE_MM_S + 0.2)
        yield from self.jaw(False, 2.6)
        yield from self.go(*self.grab_pose(*CONE_POST, CONE_HEADING, 250), CONE_HEADING, tol=40, label=label + " away")
        cones = self.state.get("cones", [])
        hung = sum(1 for c in cones if c.get("post"))
        self.say(f"{label}: {hung} cone(s) on the post, score {self.state.get('score')}")
        return True

    # -- letter cubes ----------------------------------------------------------------------
    def letter(self, label, on_fortress=None):
        """Our letter cube `label` in the lower half (streamed); None if there is none."""
        for c in self.state.get("letters", []):
            if c["label"] == label and c["y_mm"] < 1527.5 - 60 and (
                    on_fortress is None or (c["z_mm"] > 100) == on_fortress):
                return c
        return None

    def fortress_xy(self):
        dx, dy = (self.state.get("fortress") or {}).get("red_fortress", (0.0, 0.0))
        return FORTRESS_START[0] + dx, FORTRESS_START[1] + dy

    def head_at(self, mm, tol=8.0):
        """Head to `mm` and wait until it is there (intake front only)."""
        self.head_to(mm)
        end = min(self.t + 9.0, self.deadline)
        while self.t < end and abs(self.state.get("intake_lift_mm", 0.0) - mm) > tol:
            yield

    def drag(self, cube, lat, to_x, to_y, label):
        """Intake front north (heading 90): the head low on the floor cube `cube` (at `lat` beside
        the robot axis), pull mode on, drive so the cube ends at (to_x, to_y); pull off."""
        x, y = cube["x_mm"], cube["y_mm"]
        # head front 250 mm short of the cube: out of the fortress footprint (its corner posts and
        # cube level would push it); the pull brings the cube to the head
        yield from self.go(x + lat, y - 250.0, 90, tol=8, vmax=400, label=label + " behind it", htol=2.5)
        yield from self.head_at(40)
        self.press("button_2")
        yield from self.wait(0.5)
        yield from self.go(to_x + lat, to_y - 177.0, 90, vmax=300, tol=15, label=label + " drag", htol=2.5)
        self.release("button_2")
        yield from self.wait(0.2)
        yield from self.head_at(85, tol=5)                  # over the cube (top 120 mm) while driving away
        px, py, _ = self.pose
        yield from self.go(px - 450, py, 90, tol=30, label=label + " away west")   # along its row

    def held_lat(self, cube):
        """Where the cube centre is beside the grab point (robot y, negative = outward)."""
        px, py, th = self.pose
        c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
        dx, dy = cube["x_mm"] - px, cube["y_mm"] - py
        return -dx * s_ + dy * c - GRAB[1]

    def place_letter(self, label, approach, carry):
        """Floor cube -> its channel: gripper mode, carriage down, jaws open; by the `approach`
        waypoints to 220 mm west of it (heading 90), slide in until it is 40 mm outward of the grab
        point, close; carriage 10 (its bottom 35 mm, over the 25 mm rail); by the `carry` waypoints
        in front of the channel window, centre it on the window, slide in until its centre is past
        the rail edge with the robot outside (R26), open, back away."""
        cube = self.letter(label, on_fortress=False)
        if cube is None:
            return False
        x, y, cy = cube["x_mm"], cube["y_mm"], CHANNELS[label]
        yield from self.mode(90)
        self.carriage_to(0)
        if self.state.get("jaw_mm", 0.0) > 1:
            self.press_for("left", self.state["jaw_mm"] / JAW_MM_S + 0.3)
        lx, ly = self.grab_pose(x, y, 90, 220, LETTER_LAT)
        for wx, wy in approach(lx, ly):
            yield from self.go(wx, wy, 90, tol=30, label=label + " approach")
        yield from self.go(lx, ly, 90, tol=8, label=label + " line up", htol=2.0)
        yield from self.wait(max(0.0, max((t for t, _ in self.timed), default=self.t) - self.t))
        for _ in range(4):                                  # slide in with the heading it has (no turning:
            th = self.pose[2]                               # no hunting); correct with where the cube is
            cube = self.letter(label, on_fortress=False)
            tx, ty = self.grab_pose(cube["x_mm"], cube["y_mm"], th, 0, LETTER_LAT)
            yield from self.go(tx, ty, None, vmax=150, tol=4, timeout=3, label=label + " in")
            cube = self.letter(label, on_fortress=False)
            if abs(self.held_lat(cube) - LETTER_LAT) < 5.0:
                break
        yield from self.jaw(True, 28.0 / JAW_MM_S)          # 138 -> 110 mm on the 120 mm cube
        if self.state.get("held") != "letter":
            self.say(f"{label}: missed the cube (lat {self.held_lat(cube):.0f})")
            yield from self.jaw(False, 1.5)
            return False
        self.carriage_to(10)
        for wx, wy in carry:
            yield from self.go(wx, wy, 90, tol=40, label=label + " carry")
        held = lambda: next((c for c in self.state.get("letters", []) if c.get("held")), None)  # noqa: E731
        c = held()
        out = -self.held_lat(c) if c else -LETTER_LAT     # cube centre beyond the grab point, mm
        def body_max():                                     # robot x with the body corner 3 mm off the
            e = math.radians(abs(wrap(self.pose[2] - 90)))  # strategy area at the heading it has
            return CHANNEL_RAIL_X - 250.0 * (math.cos(e) + math.sin(e)) - 3.0
        rx = min(CHANNEL_RAIL_X - 253.0 - 5.0, CHANNEL_RAIL_X + 12.0 + GRAB[1] - out)
        target_y = cy + 89.0
        for stand_off in (220.0, 70.0, 70.0):               # the cube centre on the window centre line,
            # again 70 mm before the window (the cube's leading face still outside it)
            yield from self.go(rx - stand_off, target_y, 90 if stand_off > 100 else None, vmax=250, tol=4, timeout=4,
                               label=label + " channel line up", htol=2.0)
            c = held()
            if c is None:
                break
            target_y -= c["y_mm"] - cy
            if stand_off < 100 and abs(c["y_mm"] - cy) < 4.0:
                break
        # last stretch at the slowest stick (gripper front: Ly drives right = +x), stopped from the
        # predicted cube position (no hunting around a target): cube centre 8 mm over the rail, or the
        # body corner at the strategy area
        horizon = 0.3                                       # s: more than the stream + event delay
        end = min(self.t + 6.0, self.deadline)
        while self.t < end:
            c = held()
            speed_x = -(self.state.get("velocity") or {}).get("vy_mm_s", 0.0)   # heading 90: right = +x
            if c is None or c["x_mm"] + speed_x * horizon >= CHANNEL_RAIL_X + 8.0 or \
                    self.pose[0] + speed_x * horizon >= body_max():
                break
            self.sticks(0.0, 0.11, 0.0)
            yield
        self.sticks(0.0, 0.0, 0.0)
        yield from self.wait(0.5)
        for _ in range(8):                                  # then short pulses, settling after each
            c = held()
            if c is None or c["x_mm"] >= CHANNEL_RAIL_X + 4.0 or self.pose[0] >= body_max() - 4.0 or \
                    self.t > self.deadline:
                break
            self.sticks(0.0, 0.11, 0.0)
            yield
            yield
            self.sticks(0.0, 0.0, 0.0)
            yield from self.wait(0.4)
        self.say(f"{label}: cube at ({c['x_mm']:.0f}, {c['y_mm']:.0f}), window {cy}" if c else f"{label}: dropped")
        yield from self.jaw(False, 1.6)
        yield from self.go(rx - 250, target_y, 90, tol=40, label=label + " back")
        placed = self.letter(label)
        self.say(f"{label}: {'in the channel' if placed and placed['z_mm'] > 1 else 'NOT in'}, "
                 f"score {self.state.get('score')}")
        return True

    def letter_cubes(self):
        """K and E (south side of our fortress, 171 mm cube level) -> channels 3 and 4: the head
        (150 mm, over the cube level) pulls both off onto the floor, then drags each one clear of
        the fortress and of the cone post; the gripper takes each from the floor."""
        k, e = self.letter("K", True), self.letter("E", True)
        if not (k and e):
            return
        fx, fy = self.fortress_xy()
        x, y = (k["x_mm"] + e["x_mm"]) / 2, k["y_mm"]
        yield from self.mode(0)
        self.say(f"letters: K and E off the fortress ({fx:.0f}, {fy:.0f})")
        self.head_to(150)
        yield from self.go(x, y - 420, 90, label="letters below the fortress")
        yield from self.head_at(150)
        yield from self.go(x, y - 300, 90, vmax=200, tol=8, label="letters head over the cube level")
        self.press("button_2")
        end = self.t + 2.0
        while self.t < end and (self.letter("K", True) or self.letter("E", True)):
            yield
        yield from self.wait(0.3)
        self.release("button_2")
        yield from self.go(x, y - 380, 90, tol=20, label="letters back")
        e, k = self.letter("E", False), self.letter("K", False)
        if e:
            yield from self.drag(e, 113.0, 1500, 760, "E")  # K stays out of the head (263 mm aside)
        k = self.letter("K", False)
        if k:
            yield from self.drag(k, 0.0, 1100, 760, "K")
        # routes: y <= 950 where the head (front 249 mm) is over the fortress x range, y 1080 east of
        # x 1250 (clear of the cube left at (1500, 760))
        east = CHANNEL_RAIL_X - 250.0 - 6.0 - 220.0
        if self.t < self.deadline - 15:
            yield from self.place_letter("K", lambda lx, ly: [(lx, self.pose[1])],
                                         [(1150, 950), (1250, 1080), (east, 1080)])
        if self.t < self.deadline - 19:                     # E takes ~19 s
            yield from self.place_letter("E", lambda lx, ly: [(self.pose[0], 1080), (1250, 1080), (lx, 950)],
                                         [(self.pose[0], 950), (1250, 1080), (east, 1080)])
        yield from self.mode(0)

    # -- the match -----------------------------------------------------------------------
    def plan(self):
        while self.state is None:
            yield
        yield from self.wait_until(0.3)
        self.say("N1: automatic stage")
        yield from self.tap("button_1")
        yield from self.wait_until(30.4)
        self.say(f"manual stage, score {self.state.get('score')}")
        px, py, _ = self.pose
        if px > 1900:                                       # parked next to the strategy area
            yield from self.go(1940, 950, 0, label="off the park spot")   # head front 2189, still high
        else:                                               # parked west of the released balls
            yield from self.go(1300, 830, 0, tol=40, label="east of the fortress")
            yield from self.go(1300, 1100, 0, label="north of the balls")
        self.deadline = 117.0                               # then: to the starting area
        south = [c for c in self.free_cones() if c["y_mm"] < 750]
        if south:
            # the lane a cone (next to the strategy area, y ~535) is where the sweep pushes it
            # against the shelf legs: hang it first, coming from the north (heading 35: the robot
            # stays clear of the balls released in resource area 1)
            self.head_to(250)                               # head over the strategy-area top (R26)
            yield from self.go(max(self.pose[0], 1250), 1120, None, label="north of the rows")
            yield from self.go(1800, 1120, 35, label="toward cone a")
            while self.t < self.deadline and self.state.get("intake_lift_mm", 0.0) < 240:
                yield
            # west between the ball rows (top y 815) and the fortress (bottom y 1207): facing south,
            # the body reaches 250 mm north and 115 south of the centre; the head (250 mm) is over the balls
            yield from self.hang_cone(south[0], "cone a", prefer=35.0,
                                      via=((1800, 1100, 270), (1700, 945, 270), (900, 945, 270)))
            yield from self.mode(0)
            yield from self.go(900, 945, 270, tol=40, label="from the cone post")
            yield from self.go(1700, 945, 270, tol=40, label="east between rows and fortress")
        self.head_to(80)                                    # just over the balls while driving
        yield from self.sweep_area_1(1460, "area 1")
        yield from self.go(1600, 900, None, label="shooting spot")
        yield from self.shoot("shot 1")
        if self.t < 95:                                     # a second sweep fits
            self.head_to(80)                                # head over the balls again
            yield from self.sweep_area_1(1380, "area 1 again")
            yield from self.go(1600, 900, None, label="shooting spot")
            flipped = self.state.get("x_mark") == "blue"   # the opponent turned it: win it back
            yield from self.shoot("shot 2", max_s=14.0, keep=2 if flipped else 0)
            if flipped and self.state.get("stored", 0) > 0:
                yield from self.shoot("X mark", max_s=6.0, key="button_3")
                self.say(f"X mark: {self.state.get('x_mark')}")
        self.release("L1")
        self.release("R2")
        self.deadline = 124.0
        for k in range(2):                                  # cones lying on our side -> cone post 2
            free = self.free_cones()
            if not free or self.t > 108:
                break
            px, py, _ = self.pose
            cone = min(free, key=lambda c: math.hypot(c["x_mm"] - px, c["y_mm"] - py))
            yield from self.hang_cone(cone, f"cone {k + 1}", via=((1700, 945, 270), (900, 945, 270)))
        yield from self.mode(0)
        self.deadline = 129.5
        self.say("to the starting area")
        yield from self.go(450, 450, 0, timeout=12)
        self.deadline = 1e9
        yield from self.wait_until(130.5)
        self.say("modification stage (flag mast)")
        yield from self.wait_until(190.6)
        # letter cubes first: the flag routine drives along y 1204, 3 mm from the fortress, and
        # shoves it ~290 mm north (fortress.py), with K and E on it
        self.say("final stage: letter cubes, then the flag")
        self.deadline = 263.0                               # leaves the return and the flag routine (~13 s)
        self.head_to(150)
        yield from self.go(662, 700, 90, label="toward the fortress")
        yield from self.letter_cubes()
        if self.state.get("held"):
            yield from self.jaw(False, 1.6)
        yield from self.mode(0)
        self.deadline = 278.0
        self.say("back to Red Start 1: N4 hangs the flag")
        if self.pose[0] > 1100:                             # round the shelf legs (y 298)
            yield from self.go(900, 750, 0, tol=40, label="past the shelf legs")
        yield from self.go(450, 450, 0, tol=30, label="to the starting area")
        yield from self.go(325, 325, 0, vmax=300, tol=6, timeout=5, label="start pose", htol=1.5)  # the routine resets its pose here
        yield from self.tap("button_4")
        yield from self.wait(1.0)
        end = self.t + 18
        while self.t < end and self.state.get("flag") != "hung":
            yield
        self.say(f"flag {self.state.get('flag')}, score {self.state.get('score')}")
        self.release("L1")
        self.release("R2")
        self.say(f"end, score {self.state.get('score')}")
        slow = [m for m in self.moves if m[2] == "timeout"]
        self.say(f"moves: {len(self.moves)}, timed out: {len(slow)} {slow[:4]}")
        while True:
            self.sticks(0, 0, 0)
            yield


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(STREAM)
    sock.settimeout(0.5)
    driver = Driver()
    shown = 0
    while True:
        try:
            data, _ = sock.recvfrom(65536)
        except socket.timeout:
            continue
        state = json.loads(data)
        for ev in driver.tick(state):
            print(json.dumps(ev), flush=True)
        for line in driver.log[shown:]:
            print(line, file=sys.stderr, flush=True)
        shown = len(driver.log)


if __name__ == "__main__":
    main()
