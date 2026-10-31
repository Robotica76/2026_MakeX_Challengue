# test_ball_collection.py - collects the balls released from both red own resource areas
#
# Scenario: manual stage after the observer removes the barriers (rules p.32), balls on
# the floor in front of each resource box. Robot v22 in Red Start 1 facing 0 deg (intake
# toward the blue side). Intake motor on DC1 (assumption, robot_config.json "intake").
#
# Route (field mm; the robot stays in front of the resource-area legs at y = 318 and
# 2737 and away from the fortress, x 342-982):
#   1. leave the start area: strafe left to y = 600
#   2. intake on, drive forward over the 10 balls of resource area 1
#   3. intake off, strafe left to y = 2455 at x = 1475 (clear of fortress and strategy area)
#   4. back up to x = 1050, intake on, drive forward over the balls of resource area 2
# The intake holds 18 balls (6 basket + 12 tower in the v22 CAD), so the second pass
# fills it with 8 of the 10.
#
# Tight corridors: to clear the legs and still reach both ball rows with the intake
# (398 mm wide, y_left -190..208 mm), the robot centre must be at y 588-603 mm for area 1
# and y 2434-2467 mm for area 2. drive() stops up to TOL_CM (1 cm) short, so the
# strafes aim a little past the target.
#
# Simulator: viewer3d.py --balls released --program ../control/test_ball_collection.py
# Robot: upload together with chassis.py; robot still when the program starts.
import time
from mbuild import power_expand_board
import chassis as ch

INTAKE_PORT = "DC1"
INTAKE_POWER = 80


def intake(on):
    if on:
        power_expand_board.set_power(INTAKE_PORT, INTAKE_POWER)
    else:
        power_expand_board.stop(INTAKE_PORT)


def report(step, arrived):
    print("%-26s %-6s x=%7.1f cm  y=%7.1f cm  heading=%6.1f deg" % (
        step, "ok" if arrived else "MISSED", ch.odo.x, ch.odo.y, ch.odo.heading))


print("ball collection test: USE_SENSORS =", ch.USE_SENSORS)
ch.odo.calibrate(1.0)
ch.odo.reset()

report("leave start area", ch.left(27.5))

intake(True)
report("pass 1 (resource area 1)", ch.drive(forward_cm=115, timeout=8))
intake(False)

report("cross to resource area 2", ch.drive(right_cm=-186.5, timeout=12))
report("back up", ch.drive(forward_cm=-42.5, timeout=6))

intake(True)
report("pass 2 (resource area 2)", ch.drive(forward_cm=45, timeout=6))
time.sleep(0.5)
intake(False)
ch.stop()
print("done")
