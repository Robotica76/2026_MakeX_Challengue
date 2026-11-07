# match_2026.py - the winning strategy over the whole match (280 s), red alliance, Red Start 1,
# two robots per alliance: this robot plays only the lower half of our area (y <= 1527.5 mm), the
# partner the upper half (resource area 2, flagpole 1, the upper strategy area).
#
# The automatic stage is the robot program (auto_pull_central.run("bonus")); the manual and final
# stages are a scripted driver: what the driver does with robot_2026.py, written as moves so the
# simulator can play, time and score it (referee.py). Not robot code for those stages.
#
# Points (rules guide V1.1 p.30-54) and why this order:
#   a valid X12 at the end of the automatic stage: 12 extra balls in our resource area 1 and the
#   first 12 balls we score count 20 (up to +240), the biggest single item
#   balls in the blue fortress upper area: 10 each (20 for the bonus ones)
#   team flag on our flagpole in the final stage: 50
#
# Automatic (0-30 s): X12 into red exchange area 1 (pull it off the strategy area, then the gripper),
#   park, stationary at 30 s.
# Manual (30-130 s): resource area 1 (own 10 + 12 bonus), shoot from (1600, 1000) over the lower
#   strategy area; the rest of area 1 and the strays of our half; back to the starting area before
#   130 s (the robot must be partly in it to be taken out for the modification stage).
# Modification (130-190 s): the team installs the flag mast (simulator: robot back on its start pose).
# Final (190-280 s): hang the flag on flagpole 2 (y 1010, our half) first, timed, then balls.
# Not simulated: pins (10 / 30), the X mark (30), letter cubes, hanging the cone.
#
# Simulator: viewer3d.py --program ../control/match_2026.py --time-limit 280 --camera follow
#            or simulation/analysis/simulate_match.py (headless, prints the timeline and the score)
import math
import time
from mbuild import power_expand_board as pb
import chassis as ch
import auto_pull_central as auto

MANUAL_START, MANUAL_END = 30.0, 130.0
FINAL_START, MATCH_END = 190.0, 280.0
START_AREA_SPOT = (450.0, 450.0)      # robot centre partly inside Red Start 1 (x, y 75-575)
FLAG_POLE_Y = 1010.0                  # red flagpole 2 (x 0-120 mm from the back wall, 961 mm high)
FLAG_ROD_LEFT = 194.0                 # flag rod on the left side (robot_config.json "team_flag" proposal)
FLAG_X = 330.0                        # robot centre facing the wall: chassis front 215 (pin area < 195),
                                      # rod front end 81 (pole 0-120): the 37 mm window is 312-349
CARRIAGE_MM_S = 150.0
FLAG_CARRIAGE_UP, FLAG_CARRIAGE_DOWN = 230.0, 160.0   # rod 1000 mm (over the pole), then 930 (on it)
HEAD_OVER_PINS = 370.0                # intake head above the pin area (405 mm) near the wall
BLUE_FORTRESS = (3993.0, 1527.5)
LAUNCH_SPEED_MM_S = 8000.0      # at 100 % shooter power (simulator estimate, test_full_intake.py)
HOOD_DEG = 40.0
EXIT_LEFT_MM = 290.0            # launcher exit, left of the robot centre
EXIT_Z_MM, TARGET_Z_MM = 402.0, 442.0
G = 9810.0
AIM_SHORT_MM = 150.0            # land in the near half: deep shots bounce off the back wall and out
SHOT_S = 0.95                   # seconds per ball through the feeder (simulator: 10 balls in ~9 s)
CAPACITY = 18
PASS_OVER_HEAD = 80.0           # head bottom 126 mm: over the floor balls (70 mm) while moving to a sweep
FLOOR_HEAD = 10.0               # head lift for floor balls (reach: ball centre 0-60 mm above it)
LEAVE_PARK = ((2000.0, 900.0), (1955.0, 1000.0))   # head up over the strategy area, then off it,
                                                  # body above the released rows (y <= 688 at x 1680)
TURN_SPOT = (1870.0, 1150.0)   # turning here clears the released rows (y <= 768) and the strategy area
COLLECT_SPEED = 40             # RPM: slow enough that the head takes the balls instead of pushing them
SPOT_LOW = (1600.0, 1000.0)    # shots cross the centre line over the lower strategy area (259 mm),
                               # clear of the table top (654 mm) and the X mark; our half
held = [0]                      # balls the driver thinks are inside (counted from the plan)
stage_end = [MANUAL_END]


carriage = [0.0, 0.0, 0.0, 0.0]


def carriage_now():
    c0, c1, t0, t1 = carriage
    return c1 if auto.now() >= t1 else c0 + (c1 - c0) * (auto.now() - t0) / (t1 - t0)


def carriage_to(height):
    """Elevator carriage (DC3, open loop at 150 mm/s) to `height`; returns at once."""
    start = carriage_now()
    for job in [j for j in auto.jobs if j[0] == "DC3"]:
        auto.jobs.remove(job)
    delta = height - start
    if abs(delta) < 1:
        return
    pb.set_power("DC3", 100 if delta > 0 else -100)
    seconds = abs(delta) / CARRIAGE_MM_S
    auto.jobs.append(["DC3", auto.now() + seconds])
    carriage[:] = [start, height, auto.now(), auto.now() + seconds]


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
    end = min(auto.now() + held[0] * SHOT_S + 0.8, stage_end[0] - 1.0)
    while auto.now() < end:
        auto.tick()
        time.sleep(0.02)
    ports(0, "DC5", "DC4", "BL1")
    print("%5.1f s  %s: %d balls at %.0f %% power (%.0f mm)" % (auto.now(), label, held[0], power, distance))
    held[0] = 0


def collect_line(start, end, heading, expected, label, speed=COLLECT_SPEED, turn_at=None, via=()):
    """Drive from start to end with the intake and the tower on (floor balls). The robot turns at
    `turn_at`, away from the balls: a turn next to them sweeps them under the resource shelf.
    `via`: waypoints first, with the head still where it was (e.g. up over the strategy area)."""
    for x, y in via:
        auto.go_to(x, y, timeout=5)
    auto.head_to(PASS_OVER_HEAD)                     # head over the balls until the sweep starts
    if turn_at:
        fx, _ = auto.field_xy()                      # straight up first, then across: never over the rows
        auto.go_to(max(fx, turn_at[0]), turn_at[1], timeout=6)
        auto.report(label + " turn spot", auto.go_to(turn_at[0], turn_at[1], timeout=4))
        auto.report(label + " turn", ch.turn_to(heading, speed=150, timeout=4, on_cycle=auto.tick))
        _, fy = auto.field_xy()                      # the turn moves the centre ~158 mm: line up in x
        auto.go_to(start[0], fy, timeout=4)          # first, then straight down beside the rows
    auto.report(label + " start", auto.go_to(start[0], start[1], timeout=6, tol=1.0))
    auto.head_to(FLOOR_HEAD)
    if not turn_at:
        auto.report(label + " turn", ch.turn_to(heading, speed=150, timeout=4, on_cycle=auto.tick))
        auto.report(label + " line", auto.go_to(start[0], start[1], timeout=3, tol=1.0))
    auto.finish_jobs()
    ports(80, "DC1", "DC4")
    auto.report(label + " sweep", auto.go_to(end[0], end[1], speed=speed, timeout=8))
    time.sleep(0.8)                                  # the last balls climb the tower
    held[0] = min(CAPACITY, held[0] + expected)


def manual_stage():
    wait_until(MANUAL_START + 0.3)                   # observers release the balls at 30 s
    auto.report("manual stage")
    # resource area 1 (own 10 + bonus 12; 18 fit), facing -x along the released rows
    collect_line((1900.0, 590.0), (1480.0, 590.0), 180, 18, "area 1", turn_at=TURN_SPOT,
                 via=LEAVE_PARK)
    shoot(SPOT_LOW, "shot 1")
    # what is left of area 1 and the balls pushed around it (our half only)
    collect_line((1900.0, 590.0), (1430.0, 590.0), 180, 4, "area 1 rest", turn_at=TURN_SPOT)
    collect_line((1900.0, 760.0), (1300.0, 760.0), 180, 2, "strays")
    shoot(SPOT_LOW, "shot 2")
    ports(0, "DC1", "DC4")
    auto.head_to(FLOOR_HEAD)
    # partly in the starting area before the end of the stage (modification stage, p.53)
    auto.report("to the starting area", auto.go_to(START_AREA_SPOT[0], START_AREA_SPOT[1], timeout=8))
    ch.turn_to(0, speed=150, timeout=3, on_cycle=auto.tick)
    ch.stop()
    auto.finish_jobs()
    auto.report("manual stage over")


def hang_flag():
    """Flagpole 2: face the back wall, rod on the left over the pole, carriage down, back out."""
    t0 = auto.now()
    auto.head_to(HEAD_OVER_PINS)                     # 7 s from the floor: started first
    carriage_to(FLAG_CARRIAGE_UP)
    y = FLAG_POLE_Y + FLAG_ROD_LEFT                  # facing -x the left side is toward -y
    auto.report("flag: out of the corner", auto.go_to(700.0, 600.0, timeout=5))   # clear of the cone post
    auto.report("flag: lane", auto.go_to(700.0, y, timeout=5))
    auto.report("flag: face the wall", ch.turn_to(180, speed=150, timeout=4, on_cycle=auto.tick))
    auto.report("flag: lane again", auto.go_to(700.0, y, timeout=3, tol=1.0))
    auto.finish_jobs()                               # head over the pin area, rod over the pole
    auto.report("flag: rod over the pole", auto.go_to(FLAG_X, y, speed=40, timeout=6, tol=0.5))
    carriage_to(FLAG_CARRIAGE_DOWN)
    auto.finish_jobs()
    auto.report("flag: back out", auto.go_to(700.0, y, speed=60, timeout=5))
    print("%5.1f s  flag hung in %.1f s from the start of the final stage" % (auto.now(), auto.now() - t0))


def final_stage():
    wait_until(FINAL_START + 0.2)
    stage_end[0] = MATCH_END
    ch.odo.reset()                                   # robot placed back on the start pose
    carriage[:] = [carriage_now()] * 2 + [auto.now()] * 2
    auto.report("final stage")
    hang_flag()
    auto.head_to(FLOOR_HEAD)
    carriage_to(0.0)
    collect_line((1900.0, 590.0), (1300.0, 590.0), 180, 4, "final sweep", turn_at=TURN_SPOT)
    shoot(SPOT_LOW, "final shot")
    ports(0, "DC1", "DC2", "DC3", "DC4")
    ch.stop()
    auto.report("match over")


STRATEGY = "bonus"
try:                                                 # simulator studies: compare the strategies
    import simtrace
    STRATEGY = simtrace.options().get("strategy", STRATEGY)
except ImportError:
    pass
auto.run(STRATEGY)
auto.HARD_STOP = MANUAL_END - 0.5                    # the manual stage keeps the same safety stop
manual_stage()
auto.HARD_STOP = MATCH_END - 0.5
final_stage()
