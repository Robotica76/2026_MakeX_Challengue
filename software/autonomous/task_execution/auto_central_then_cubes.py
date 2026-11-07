# auto_central_then_cubes.py - automatic stage (30 s), red alliance, Red Start 1
#
# Strategy (team): take as many balls as possible from the central resource area so the
# opponent cannot get them (no shooting in this stage; the balls are kept for the manual
# stage), then bring props from the central strip to our side, where the opponent cannot
# reach them. Props are placed in the manual stage, except a bonus cube: it only counts if it
# is in our bonus exchange area when the automatic stage ends (p.30), so it goes there now.
#
# Phase 1 - central balls (rules p.32: collecting central balls is allowed in this stage;
#   no limit on how many a robot holds). The intake head starts rising at the start and
#   reaches the upper level (~254 mm) while the robot drives diagonally to the table.
#   Two passes take the upper level; a third, optional pass takes lower-level balls
#   until the robot is full (18). The head overhang crossing into the central strip is
#   allowed (team decision); the body stays at x <= 2220 mm.
# Phase 2 - props with the gripper (right side): the X12 bonus cube from the lower strategy
#   area into red exchange area 1 (valid if it is there at 30 s and touches no robot), then a
#   cone dropped on our side if there is time. The body crosses the line for ~2.5 s per grab
#   (R06 allows 3 s). Positions follow the default prop card; on the robot the AI camera
#   must find the X12 (Bonus Battle, p.28).
# The robot must be stationary when the stage ends (R19, -20 points): every step checks the
# time and everything stops before END_BY.
#
# Ports (robot_config.json "mechanisms", assumptions): DC1 intake rollers, DC2 intake head,
# DC3 elevator carriage, DC4 tower, DC6 gripper jaw (positive closes).
# Simulator: viewer3d.py --program ../../software/autonomous/task_execution/auto_central_then_cubes.py
import math
import time
from mbuild import power_expand_board as pb
import chassis as ch

TRAVEL_SPEED = 150          # RPM for long moves (MAX_SPEED raised for this routine)
APPROACH_SPEED = 90         # RPM with the head inside the table
HEAD_UP_S = 4.8             # DC2 at 100 %: ~254 mm, upper level in reach (53 mm/s)
HEAD_LOWER_LEVEL_S = 3.8    # from the upper to the lower level (~53 mm)
LOWER_PASS = False          # True: third pass at the lower level (max denial, 18 balls, no time for cubes)
END_BY = 29.0               # s: no new step may end after this
HARD_STOP = 29.5            # s: safety: if a step overruns, everything stops here (R19)
START_X, START_Y = 325.0, 325.0                 # Red Start 1 centre, field mm (odometry origin)
X12 = (2327.5, 839.5)                           # default prop card: lower strategy area, 3rd spot
CONE = (2327.5, 1063.5)                         # lower strategy area, spot next to the table
GRAB_RIGHT, GRAB_BACK = 228.5, 89.0             # grab point: right of / behind the robot centre (mm)
CARRIAGE_UP_S = 268.0 / 150.0                   # jaws above the cone base, both prop kinds in reach
EXCHANGE_DROP = (1520.0, 340.0)                 # cube centre: overlaps red exchange area 1 (y <= 318)

ch.MAX_SPEED = TRAVEL_SPEED
T0 = time.time()
jobs = []                   # [port, stop time]: mechanisms running while the robot drives


def now():
    return time.time() - T0


def run_for(port, power, seconds):
    pb.set_power(port, power)
    jobs.append([port, now() + seconds])


class Abort(Exception):
    pass


def stop_all():
    for port in ("DC1", "DC2", "DC3", "DC4", "DC6"):
        pb.stop(port)
    ch.stop()


def tick():
    if now() >= HARD_STOP:
        stop_all()
        raise Abort()
    for job in list(jobs):
        if now() >= job[1]:
            pb.stop(job[0])
            jobs.remove(job)


def finish_jobs():
    while jobs:
        tick()
        time.sleep(0.01)


def report(step, arrived=True):
    print("%5.1f s  %-30s %-6s x=%7.1f cm  y=%7.1f cm  heading=%6.1f deg" % (
        now(), step, "ok" if arrived else "MISSED", ch.odo.x, ch.odo.y, ch.odo.heading))


def shelf_pass(name):
    report(name + " in", ch.drive(forward_cm=38, speed=APPROACH_SPEED, timeout=6, on_cycle=tick))
    time.sleep(0.15)
    report(name + " out", ch.drive(forward_cm=-38, speed=TRAVEL_SPEED, timeout=4, on_cycle=tick))


def time_for(seconds):
    """True if a step of about `seconds` still ends before END_BY."""
    return now() + seconds < END_BY


def field_xy():
    return START_X + ch.odo.y * 10, START_Y - ch.odo.x * 10


def go_to(x, y, speed=TRAVEL_SPEED, timeout=4):
    """Drive the robot centre to field (x, y) mm without turning."""
    fx, fy = field_xy()
    odx, ody = -(y - fy) / 10.0, (x - fx) / 10.0              # field delta -> odometry cm
    h = math.radians(ch.odo.heading)
    fwd = odx * math.sin(h) + ody * math.cos(h)
    right = odx * math.cos(h) - ody * math.sin(h)
    return ch.drive(forward_cm=fwd, right_cm=right, speed=speed, timeout=timeout, on_cycle=tick)


def grab(prop, preclose_s, close_s):
    """Gripper facing +x (heading -90 cw): straddle the prop from our side, close, back out."""
    px, py = prop
    run_for("DC6", 100, preclose_s)                           # jaws almost at the prop width
    report("prop approach", go_to(px - GRAB_RIGHT - 200, py + GRAB_BACK))
    finish_jobs()
    report("prop in reach", go_to(px - GRAB_RIGHT, py + GRAB_BACK, speed=APPROACH_SPEED, timeout=3))
    run_for("DC6", 100, close_s)
    finish_jobs()
    report("prop out", go_to(px - GRAB_RIGHT - 200, py + GRAB_BACK))


def main():
    # ---- phase 1: central balls ----
    ch.odo.calibrate(0.5)
    ch.odo.reset()
    run_for("DC2", 100, HEAD_UP_S)                                  # head up while travelling
    report("to the central table", ch.drive(forward_cm=139.5, right_cm=-110.25, speed=TRAVEL_SPEED,
                                            timeout=7, on_cycle=tick))   # field (1720, 1427.5)
    finish_jobs()
    pb.set_power("DC1", 80)                                         # intake rollers
    pb.set_power("DC4", 80)                                         # tower: balls up into the basket
    shelf_pass("pass A (upper)")
    report("pass B position", ch.drive(right_cm=-19.2, speed=TRAVEL_SPEED, timeout=3, on_cycle=tick))
    shelf_pass("pass B (upper)")
    if LOWER_PASS:
        run_for("DC2", -100, HEAD_LOWER_LEVEL_S)
        report("pass C position", ch.drive(right_cm=10.0, speed=TRAVEL_SPEED, timeout=3, on_cycle=tick))
        finish_jobs()
        shelf_pass("pass C (lower)")
    pb.stop("DC1")
    report("phase 1 done")

    # ---- phase 2: props from the central strip ----
    run_for("DC2", -100, 2.0)                                       # head down while travelling
    pb.stop("DC1")
    if time_for(9.5):
        run_for("DC3", 100, CARRIAGE_UP_S)
        report("gripper toward the strategy area", ch.turn_to(-90, speed=TRAVEL_SPEED, timeout=3, on_cycle=tick))
        pb.stop("DC4")
        grab(X12, preclose_s=0.35, close_s=0.3)                   # cube: 120 mm, close to ~26 mm
        run_for("DC3", -100, CARRIAGE_UP_S)
        report("gripper toward the exchange area", ch.turn_to(0, speed=TRAVEL_SPEED, timeout=3, on_cycle=tick))
        report("over exchange area 1", go_to(EXCHANGE_DROP[0] + GRAB_BACK, EXCHANGE_DROP[1] + GRAB_RIGHT))
        finish_jobs()
        run_for("DC6", -100, 0.8)                                 # open: the cube drops into the area
        finish_jobs()
        report("X12 in exchange area 1")
    if time_for(9.0):
        run_for("DC3", 100, CARRIAGE_UP_S)
        report("gripper toward the strategy area", ch.turn_to(-90, speed=TRAVEL_SPEED, timeout=3, on_cycle=tick))
        grab(CONE, preclose_s=0.95, close_s=0.3)                  # cone body ~90 mm: close to ~50 mm
        run_for("DC3", -100, CARRIAGE_UP_S)
        report("cone on our side", go_to(1500.0, CONE[1] + GRAB_BACK))
        finish_jobs()
        run_for("DC6", -100, 1.4)
        finish_jobs()
        report("cone dropped (place it in the manual stage)")
    finish_jobs()


try:
    main()
except Abort:
    report("time limit: stopped by the safety stop")
for port in ("DC1", "DC2", "DC3", "DC4", "DC6"):
    pb.stop(port)
ch.stop()
report("stopped")
