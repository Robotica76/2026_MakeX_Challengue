# auto_central_then_cubes.py - automatic stage (30 s), red alliance, Red Start 1
#
# Strategy (team): take as many balls as possible from the central resource area so the
# opponent cannot get them (no shooting in this stage; the balls are kept for the manual
# stage), then use the remaining time for letter cubes.
#
# Phase 1 - central balls (rules p.32: collecting central balls is allowed in this stage;
#   no limit on how many a robot holds). The intake head starts rising at the start and
#   reaches the upper level (~254 mm) while the robot drives diagonally to the table.
#   Two passes take the upper level; a third, optional pass takes lower-level balls
#   until the robot is full (18). The head overhang crossing into the central strip is
#   allowed (team decision); the body stays at x <= 2220 mm.
# Phase 2 - letter cubes: route from the table to the fortress and to the strategy
#   channel, with timed placeholders for the gripper (carriage DC3, jaw DC6). The cubes
#   and the gripper are not simulated yet, so this phase only measures the time budget.
# The robot must be stationary when the stage ends (R19, -20 points): everything stops
# before END_BY.
#
# Ports (robot_config.json "mechanisms", assumptions): DC1 intake rollers, DC2 intake head,
# DC3 elevator carriage, DC4 tower, DC6 gripper jaw (assumed).
# Simulator: viewer3d.py --program ../../software/autonomous/task_execution/auto_central_then_cubes.py
import time
from mbuild import power_expand_board as pb
import chassis as ch

TRAVEL_SPEED = 150          # RPM for long moves (MAX_SPEED raised for this routine)
APPROACH_SPEED = 90         # RPM with the head inside the table
HEAD_UP_S = 4.8             # DC2 at 100 %: ~254 mm, upper level in reach (53 mm/s)
HEAD_LOWER_LEVEL_S = 3.8    # from the upper to the lower level (~53 mm)
LOWER_PASS = False          # True: third pass at the lower level (max denial, 18 balls, no time for cubes)
END_BY = 29.0               # s: everything stopped before the 30 s stage ends

ch.MAX_SPEED = TRAVEL_SPEED
T0 = time.time()
jobs = []                   # [port, stop time]: mechanisms running while the robot drives


def now():
    return time.time() - T0


def run_for(port, power, seconds):
    pb.set_power(port, power)
    jobs.append([port, now() + seconds])


def tick():
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

# ---- phase 2: letter cubes (route and timing only) ----
# Each step runs only if it can finish before END_BY (R19). Step times measured in simulation.
run_for("DC2", -100, 2.0)                                       # head down while travelling
time.sleep(0.4)                                                 # last balls up the tower
pb.stop("DC4")
cube_taken = False
if time_for(2.5 + 1.5 + 1.6):
    report("to the fortress", ch.drive(forward_cm=-48, speed=TRAVEL_SPEED, timeout=4, on_cycle=tick))
    report("gripper toward the fortress", ch.turn_to(90, speed=TRAVEL_SPEED, timeout=3, on_cycle=tick))
    run_for("DC3", 100, 1.1)                                    # carriage to the cube level
    finish_jobs()
    run_for("DC6", 60, 0.5)                                     # close the jaw (placeholder)
    finish_jobs()
    cube_taken = True
    report("cube taken (placeholder)")
if cube_taken and time_for(1.5 + 3.0 + 0.6):
    report("toward the strategy channel", ch.turn_to(-90, speed=TRAVEL_SPEED, timeout=3, on_cycle=tick))
    run_for("DC3", -100, 1.1)
    report("at the E window", ch.drive(forward_cm=-40, speed=TRAVEL_SPEED, timeout=4, on_cycle=tick))
    finish_jobs()
    run_for("DC6", -60, 0.5)                                    # open the jaw (placeholder)
    finish_jobs()
    report("cube released (placeholder)")
finish_jobs()
for port in ("DC1", "DC2", "DC3", "DC4", "DC6"):
    pb.stop(port)
ch.stop()
report("stopped")
