"""Scripted driver for the alliance partner: the same robot and program (storm_breaker_2026.py with
START_Y 2730, ORDER 0: it stays in Red Start 2 in the automatic stage) in the upper half of the red
area. Mirrored in y our robot's routines would need the gripper on the left, so the partner plays
what needs no gripper: the balls of resource area 2, the team flag on flagpole 1 (by hand: head and
carriage with the manual controls; from y 2239 the robot is clear of the fortress) and the X mark.

Plan (field coordinates, red frame):
  0 s      N1: the program calibrates at (325, 2730) and waits (ORDER 0)
  30 s     sweep resource area 2 (rows y 2562-2642) facing -x at y 2455, shoot from (1600, 2155)
           (R2 aims at the blue fortress, over the X mark's side), twice; keep 2 balls for the X
  108 s    back into Red Start 2 (modification stage)
  190 s    flag on flagpole 1 (y 2045): head 370 mm, carriage 230, along y 2239 facing -x to x 322,
           carriage 160; then the X mark at the end from (1000, 2175)
"""

import math

from ai_driver import X_RESERVE, Driver

START = (325.0, 2730.0)
POLE_ROD_Y = 2045.0 + 194.0      # robot y with the flag rod (left side, 194 mm) over flagpole 1


class PartnerDriver(Driver):
    x_reserve = True             # keep X_RESERVE balls for the X mark at the end
    def sweep_area_2(self, x_end, label):
        """Resource area 2 (upper): the mirror of sweep_area_1 at y 3055 - 600."""
        yield from self.go(1870, 1935, 180, label=label + " turn spot")
        _, py, _ = self.pose
        yield from self.go(1900, py, 180, tol=30, label=label + " line up")
        yield from self.go(1900, 2415, 180, vmax=500, tol=25, label=label + " beside the rows")
        yield from self.go(1900, 2455, 180, vmax=200, tol=20, label=label + " sweep start")
        self.press("L1")
        self.head_to(0)
        self.say(f"{label}: intake on")
        yield from self.go(x_end, 2455, 180, vmax=260, tol=25, timeout=6, label=label + " sweep")
        if self.t < self.deadline:
            yield from self.wait(0.8)
        self.release("L1")
        self.say(f"{label}: {self.state.get('stored', 0)} balls inside")

    def hang_flag_1(self):
        """Team flag on flagpole 1 with the manual controls (the program's N4 routine is for pole 2)."""
        yield from self.mode(0)
        self.head_to(370)
        yield from self.go(700, 2500, 180, tol=30, label="flag: out of the start area")
        yield from self.head_at(370, tol=6)
        yield from self.mode(90)
        self.carriage_to(230)
        yield from self.wait(max(0.0, abs(230 - self.state.get("carriage_mm", 0.0)) / 150.0 + 0.2))
        yield from self.mode(0)
        yield from self.go(700, POLE_ROD_Y, 180, tol=10, label="flag: lane", htol=1.5)
        # x 336: the front (115 mm) clears cone post 1 (x 180-220) and the rod tip (249 mm) is 32 mm
        # over the pole (30 needed)
        yield from self.go(336, POLE_ROD_Y, 180, vmax=200, tol=5, timeout=6, label="flag: over the pole", htol=1.5)
        yield from self.mode(90)
        self.carriage_to(160)
        yield from self.wait(1.2)
        end = self.t + 3.0
        while self.t < end and self.state.get("flag") != "hung":
            yield
        yield from self.mode(0)
        yield from self.go(700, POLE_ROD_Y, 180, vmax=300, tol=30, label="flag: away")
        self.say(f"flag {self.state.get('flag')}, score {self.state.get('score')}")

    def x_mark_from_2(self):
        if not self.state.get("stored"):
            self.say("X mark: no ball left")
            return
        self.deadline = 279.6
        yield from self.go(1000, 2175, None, tol=40, timeout=4, label="X mark spot")
        yield from self.wait_until(self.x_fire_at)
        n = self.state.get("stored", 0)
        yield from self.shoot("X mark (end)", max_s=self.deadline - self.t, key="button_3")
        self.say(f"X mark: {self.state.get('x_mark')} after {n} ball(s), score {self.state.get('score')}")

    def plan(self):
        while self.state is None:
            yield
        yield from self.wait_until(0.3)
        self.say("N1: automatic stage (partner: stays in Red Start 2)")
        yield from self.tap("button_1")
        yield from self.wait_until(30.4)
        self.say(f"manual stage, score {self.state.get('score')}")
        self.deadline = 117.0
        yield from self.go(700, 2300, 0, label="out of the start area")
        self.head_to(80)
        yield from self.sweep_area_2(1460, "area 2")
        yield from self.go(1600, 2155, None, label="shooting spot")
        yield from self.shoot("shot 1", keep=X_RESERVE if self.x_reserve else 0)
        self.head_to(80)
        yield from self.sweep_area_2(1380, "area 2 again")
        yield from self.go(1600, 2155, None, label="shooting spot")
        yield from self.shoot("shot 2", max_s=10.0, keep=X_RESERVE if self.x_reserve else 0)
        if self.t < 98:                                     # time for a third sweep
            self.head_to(80)
            yield from self.sweep_area_2(1300, "area 2 third")
            yield from self.go(1600, 2155, None, label="shooting spot")
            yield from self.shoot("shot 3", max_s=8.0, keep=X_RESERVE if self.x_reserve else 0)
        self.release("L1")
        self.release("R2")
        self.deadline = 129.5
        self.say("to the starting area")
        yield from self.go(900, 2300, 0, tol=40, label="clear of the shelf legs")
        yield from self.go(450, 2605, 0, timeout=12)
        self.deadline = 1e9
        yield from self.wait_until(130.5)
        self.say("modification stage (flag mast)")
        yield from self.wait_until(190.6)
        self.deadline = 278.0
        self.say("final stage: flag on pole 1")
        yield from self.hang_flag_1()
        yield from self.x_mark_from_2()
        self.say(f"end, score {self.state.get('score')}")
        while True:
            self.sticks(0, 0, 0)
            yield
