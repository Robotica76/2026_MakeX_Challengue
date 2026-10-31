# test_intake_shelf.py - takes the balls from the upper level of the central resource area
#
# Robot v22 in Red Start 1 facing 0 deg (intake toward the blue side). Ports as in
# robot_config.json "mechanisms": DC1 intake rollers, DC2 intake head lift.
#
# Geometry (field mm, rules p.19-21; v22 CAD):
#   central table x 2220-2435, y 1207.5-1847.5; upper level ball centres at 285 mm,
#   front row x 2286, back row x 2368; legs leave y 1237.5-1817.5 free.
#   The intake head reaches ball centres 0-60 mm above its lift, so lift ~255 mm puts
#   the upper level in reach with the head above the level's plate (250 mm).
#   The head sticks out 134 mm ahead of the rest of the robot (body front 115 mm from
#   the robot centre), so the head can enter the table while the body stops at the
#   table edge: robot centre x <= 2220 - 115 = 2105.
#   The head is 398 mm wide (190 right, 208 left of the robot centre): two passes,
#   at y = 1427.5 and 1609.5, keep it between the legs and cover all 15 balls.
#
# Simulator: viewer3d.py --program ../control/test_intake_shelf.py --camera follow
# Robot: upload together with chassis.py; robot still when the program starts.
import time
from mbuild import power_expand_board as pb
import chassis as ch

APPROACH_SPEED = 40          # RPM, slow while the head is inside the table


def report(step, arrived):
    print("%-24s %-6s x=%7.1f cm  y=%7.1f cm  heading=%6.1f deg" % (
        step, "ok" if arrived else "MISSED", ch.odo.x, ch.odo.y, ch.odo.heading))


def head(power, seconds):
    pb.set_power("DC2", power)
    time.sleep(seconds)
    pb.stop("DC2")


def shelf_pass(name):
    pb.set_power("DC1", 80)
    report(name + " in", ch.drive(forward_cm=41, speed=APPROACH_SPEED, timeout=10))
    time.sleep(0.5)
    report(name + " out", ch.drive(forward_cm=-40, timeout=6))


print("intake shelf test")
ch.odo.calibrate(1.0)
ch.odo.reset()

report("leave start area", ch.left(27.5))                 # y 600, clear of the resource legs
report("to the central table", ch.drive(forward_cm=137.5, timeout=8))   # x 1700
report("pass A position", ch.left(84.75))                 # y 1427.5
head(100, 4.8)                                            # head up ~254 mm (53 mm/s)
shelf_pass("pass A")
report("pass B position", ch.left(19.2))                  # y 1609.5
shelf_pass("pass B")
pb.stop("DC1")
head(-100, 5.2)                                           # head down
ch.stop()
print("done")
