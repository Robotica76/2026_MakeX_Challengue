"""Scripted driver for storm_breaker_2026 in the simulator: plays the Bluetooth gamepad the way the
driver would, closing the loop on the robot pose from the state stream.

    viewer3d.py --program ../../software/robot/main/storm_breaker_2026.mblock --time-limit 280 \\
                --driver ../control/ai_driver.py --autorun

Protocol: reads the viewer's UDP state stream (state_stream.py, 127.0.0.1:5005) and prints gamepad
events (gamepad.py JSON lines) that the viewer feeds to the program. The same Driver class runs
inside a headless simulation (simulation/analysis/simulate_driver.py) to test and time the plan.

Plan (red alliance, Red Start 1, lower half of our area; robot_2026 controls of the program):
  0 s      N1: the program runs the automatic stage (X12 into exchange area 1, X9 and cones ours)
  30 s     manual: head down, sweep resource area 1 (own 10 + 12 bonus balls) with L1 (intake),
           hold R2 (the program aims at the blue fortress and sets the power); sweep the rest and
           shoot again; back into the starting area before 130 s (modification stage)
  190 s    final: N4 (the program hangs the flag from Red Start 1), then the remaining balls
"""

import json
import math
import socket
import sys
import time

STREAM = ("127.0.0.1", 5005)
STICK_MM_S = 800.0          # program: stick 100 % = 800 mm/s (drive_joystick_N)
TURN_DPS_PER_STICK = 200.0  # program: Rx 100 % = 200 deg/s


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


class Driver:
    def __init__(self):
        self.state = None
        self.events = []
        self.log = []
        self._plan = self.plan()
        self._sticks = (0.0, 0.0, 0.0)

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

    def tick(self, state):
        self.state = state
        self.events = []
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

    def go(self, x, y, heading=None, vmax=650.0, tol=25.0, timeout=8.0):
        """Drive to field (x, y) mm (and heading, deg) with the sticks: P control on the pose."""
        end = self.t + timeout
        while self.t < end:
            px, py, th = self.pose
            ex, ey = x - px, y - py
            dist = math.hypot(ex, ey)
            herr = wrap(heading - th) if heading is not None else 0.0
            if dist < tol and abs(herr) < 3.0:
                break
            c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
            speed = min(vmax, 2.2 * dist)
            f = (ex * c + ey * s) / max(dist, 1e-6) * speed
            r = (ex * s - ey * c) / max(dist, 1e-6) * speed
            ly, lx = f / STICK_MM_S, r / STICK_MM_S
            for comp in ("ly", "lx"):                       # past the program's deadzone (8 %)
                v = ly if comp == "ly" else lx
                if 0.004 < abs(v) < 0.09:
                    v = math.copysign(0.09, v)
                if comp == "ly":
                    ly = v
                else:
                    lx = v
            ccw = max(-150.0, min(150.0, 4.0 * herr)) if abs(herr) >= 3.0 else 0.0
            rx = -ccw / TURN_DPS_PER_STICK
            if 0 < abs(rx) < 0.09:
                rx = math.copysign(0.09, rx)
            self.sticks(lx, ly, rx)
            yield
        self.sticks(0, 0, 0)
        yield from self.wait(0.15)

    def shoot(self, label, max_s=22.0):
        """Hold R2 (the program aims and sets the power) until the robot is empty."""
        start, n = self.t, self.state.get("stored", 0)
        self.say(f"{label}: R2 with {n} balls inside")
        self.press("R2")
        end = self.t + max_s
        while self.t < end and (self.state.get("stored", 0) > 0 or self.t < start + 2.5):
            yield
        yield from self.wait(0.8)
        self.release("R2")
        yield from self.wait(0.3)
        self.say(f"{label}: done, score {self.state.get('score')}")

    def sweep_area_1(self, x_end, label):
        """Resource area 1: turn away from the balls, line up beside them, intake on, drive along."""
        yield from self.go(1870, 1120, None)               # turning here: clear of the rows and
        yield from self.go(1870, 1120, 180)                # of the partner half
        _, py, _ = self.pose
        yield from self.go(1900, py, 180)
        yield from self.go(1900, 640, 180, vmax=400, tol=20)
        yield from self.go(1900, 600, 180, vmax=150, tol=10)   # slow: 22 mm from the shelf legs
        self.press("L1")
        self.say(f"{label}: intake on")
        yield from self.go(x_end, 600, 180, vmax=180, tol=20, timeout=10)
        yield from self.wait(1.0)
        self.release("L1")
        self.say(f"{label}: {self.state.get('stored', 0)} balls inside")

    # -- the match -----------------------------------------------------------------------
    def plan(self):
        while self.state is None:
            yield
        yield from self.wait_until(0.3)
        self.say("N1: automatic stage")
        yield from self.tap("button_1")
        yield from self.wait_until(30.4)
        self.say(f"manual stage, score {self.state.get('score')}")
        yield from self.go(2000, 900, 0)                    # head still over the strategy area
        yield from self.go(1955, 1000, 0)
        self.press("down")                                  # intake head to the floor
        yield from self.wait(5.0)
        self.release("down")
        yield from self.sweep_area_1(1480, "area 1")
        yield from self.go(1600, 900, None)
        yield from self.shoot("shot 1")
        yield from self.sweep_area_1(1400, "area 1 again")
        yield from self.go(1600, 900, None)
        yield from self.shoot("shot 2", max_s=14.0)
        if self.t < 118:
            self.say("to the starting area")
            yield from self.go(450, 450, 0, timeout=9)
        yield from self.wait_until(130.5)
        self.say("modification stage (flag mast)")
        yield from self.wait_until(190.6)
        self.say("final stage: N4 hangs the flag")
        yield from self.tap("button_4")
        yield from self.wait(1.0)
        end = self.t + 25
        while self.t < end and self.state.get("flag") != "hung":
            yield
        yield from self.wait(4.0)
        self.say(f"flag {self.state.get('flag')}, score {self.state.get('score')}")
        yield from self.go(700, 700, 0)
        self.press("down")
        yield from self.wait(7.0)
        self.release("down")
        yield from self.sweep_area_1(1300, "final sweep")
        yield from self.go(1600, 900, None)
        yield from self.shoot("final shot", max_s=12.0)
        self.say(f"end, score {self.state.get('score')}")
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
