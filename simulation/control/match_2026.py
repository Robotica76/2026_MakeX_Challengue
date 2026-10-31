# match_2026.py - the winning strategy over the automatic and manual stages (130 s), red alliance,
# Red Start 1. The automatic stage is the robot program (auto_pull_central.run("bonus")); the
# manual stage is a scripted driver: what the driver does with robot_2026.py, written as moves so
# the simulator can play it and score it (referee.py). Not robot code for the manual stage.
#
# Points (rules guide V1.1 p.30-54) and why this order:
#   balls in the blue fortress upper area: 10 each, 20 each up to the bonus quantity
#   a valid X12 at the end of the automatic stage: the referees add 12 balls to our resource
#   area 1 and the first 12 balls we score count 20: up to +240 points, the biggest single item
#   so: automatic = X12 into exchange area 1; manual = ball cycles (collect, then shoot from the
#   red half), bonus balls first
#
# Automatic (0-30 s): props_low_b pulls the X12 and a cone off the strategy area to the line,
#   floor_low_b pulls them onto our floor, the gripper puts the X12 in exchange area 1, park.
# Manual (30-130 s), driver cycles:
#   1. resource area 1: own balls + 12 bonus balls (observers release them at 30 s)
#   2. shoot from (1600, 1000): the ball crosses the centre line over the lower strategy area
#   3. the rest of area 1, resource area 2
#   4. shoot from (1600, 2300), over the upper strategy area (a path over the table clips its
#      top or the X mark)
#   5. central table, upper level (capture with the head at 255 mm), shoot, as time allows
# Not simulated (more points for the real match): pins (10 / 30), the X mark (30), hanging the
# cone (20; the carriage cannot lift a cone over the 405 mm post in the model), letter cubes.
#
# Simulator: viewer3d.py --program ../control/match_2026.py --time-limit 130 --camera follow
#            or simulation/analysis/simulate_match.py (headless, prints the score)
import math
import time
from mbuild import power_expand_board as pb
import chassis as ch
import auto_pull_central as auto

MANUAL_START, MATCH_END = 30.0, 130.0
BLUE_FORTRESS = (3993.0, 1527.5)
LAUNCH_SPEED_MM_S = 8000.0      # at 100 % shooter power (simulator estimate, test_full_intake.py)
HOOD_DEG = 40.0
EXIT_LEFT_MM = 290.0            # launcher exit, left of the robot centre
EXIT_Z_MM, TARGET_Z_MM = 402.0, 442.0
G = 9810.0
AIM_SHORT_MM = 150.0            # land in the near half: deep shots bounce off the back wall and out
SHOT_S = 0.95                   # seconds per ball through the feeder (simulator: 10 balls in ~9 s)
CAPACITY = 18
FLOOR_HEAD = 10.0               # head lift for floor balls (reach: ball centre 0-60 mm above it)
SHELF_HEAD = 255.0              # upper central level (ball centres 285 mm)
COLLECT_SPEED = 40             # RPM: slow enough that the head takes the balls instead of pushing them
SPOT_LOW = (1600.0, 1000.0)    # shots cross the centre line over the lower strategy area (259 mm),
SPOT_HIGH = (1600.0, 2300.0)   # or the upper one: clear of the table top (654 mm) and the X mark
held = [0]                      # balls the driver thinks are inside (counted from the plan)


def wait_until(t):
    while auto.now() < t:
        auto.tick()
        time.sleep(0.02)


def ports(power, *names):
    for name in names:
        if power:
            pb.set_power(name, power)
        else:
            pb.stop(name)


def heading_to_aim(x, y):
    """chassis heading (clockwise deg) that points the launcher (left side) at the blue fortress."""
    phi = math.degrees(math.atan2(BLUE_FORTRESS[1] - y, BLUE_FORTRESS[0] - x))
    return 90.0 - phi


def shooter_power(distance_mm):
    h = math.radians(HOOD_DEG)
    rise = TARGET_Z_MM - EXIT_Z_MM
    v = math.sqrt(G * distance_mm ** 2 / (2 * math.cos(h) ** 2 * (distance_mm * math.tan(h) - rise)))
    return min(100.0, 100.0 * v / LAUNCH_SPEED_MM_S)


def shoot(spot, label):
    if held[0] == 0:
        return
    ports(0, "DC1")
    auto.report(label + " spot", auto.go_to(spot[0], spot[1], timeout=6))
    auto.report(label + " aim", ch.turn_to(heading_to_aim(*spot), speed=150, timeout=3, on_cycle=auto.tick))
    fx, fy = auto.field_xy()
    distance = math.hypot(BLUE_FORTRESS[0] - fx, BLUE_FORTRESS[1] - fy) - EXIT_LEFT_MM - AIM_SHORT_MM
    power = shooter_power(distance)
    pb.set_power("BL1", power)
    time.sleep(0.5)                                  # wheels up to speed
    ports(80, "DC5", "DC4")
    end = min(auto.now() + held[0] * SHOT_S + 0.8, MATCH_END - 1.0)
    while auto.now() < end:
        auto.tick()
        time.sleep(0.02)
    ports(0, "DC5", "DC4", "BL1")
    print("%5.1f s  %s: %d balls at %.0f %% power (%.0f mm)" % (auto.now(), label, held[0], power, distance))
    held[0] = 0


def collect_line(start, end, heading, expected, label, speed=COLLECT_SPEED):
    """Drive from start to end with the intake and the tower on (floor balls)."""
    auto.head_to(FLOOR_HEAD)
    auto.report(label + " start", auto.go_to(start[0], start[1], timeout=6))
    auto.report(label + " turn", ch.turn_to(heading, speed=150, timeout=4, on_cycle=auto.tick))
    auto.report(label + " line", auto.go_to(start[0], start[1], timeout=3, tol=1.0))   # the turn moves the centre
    auto.finish_jobs()
    ports(80, "DC1", "DC4")
    auto.report(label + " sweep", auto.go_to(end[0], end[1], speed=speed, timeout=8))
    time.sleep(0.8)                                  # the last balls climb the tower
    held[0] = min(CAPACITY, held[0] + expected)


def shelf_pass(lane_y, label):
    """Central table, upper level: head at the level, intake on, in and out (capture)."""
    auto.report(label + " lane", auto.go_to(1750.0, lane_y, timeout=6))
    auto.report(label + " face", ch.turn_to(0, speed=150, timeout=4, on_cycle=auto.tick))
    auto.head_to(SHELF_HEAD)               # up only once facing the table, clear of it
    auto.report(label + " lane x", auto.go_to(1800.0, lane_y, timeout=3, tol=1.0))
    auto.finish_jobs()
    ports(80, "DC1", "DC4")
    auto.report(label + " in", auto.go_to(2100.0, lane_y, speed=50, tol=1.0))
    time.sleep(0.3)
    auto.report(label + " out", auto.go_to(1800.0, lane_y, speed=80))
    held[0] = min(CAPACITY, held[0] + 7)


def manual_stage():
    wait_until(MANUAL_START + 0.3)                   # observers release the balls at 30 s
    auto.report("manual stage")
    # 1-2. resource area 1 (own 10 + bonus 12; 18 fit), facing -x along the released rows
    collect_line((1900.0, 590.0), (1480.0, 590.0), 180, 18, "area 1")
    shoot(SPOT_LOW, "shot 1")
    # 3-4. what is left of area 1, then resource area 2 (top side)
    collect_line((1900.0, 590.0), (1430.0, 590.0), 180, 4, "area 1 rest")
    collect_line((1900.0, 2465.0), (1430.0, 2465.0), 180, 10, "area 2")
    shoot(SPOT_HIGH, "shot 2")
    # 5. central table upper level while time allows (each cycle ~25 s)
    for lane in (1600.0, 1437.0):
        if auto.now() > MATCH_END - 25.0:
            break
        shelf_pass(lane, "shelf %.0f" % lane)
        shoot(SPOT_HIGH if lane > 1500 else SPOT_LOW, "shot shelf")
    ports(0, "DC1", "DC4", "DC2")
    ch.stop()
    auto.report("match over")


STRATEGY = "bonus"
try:                                                 # simulator studies: compare the strategies
    import simtrace
    STRATEGY = simtrace.options().get("strategy", STRATEGY)
except ImportError:
    pass
auto.run(STRATEGY)
auto.HARD_STOP = MATCH_END - 0.5                     # the manual stage keeps the same safety stop
manual_stage()
