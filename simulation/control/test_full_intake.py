# test_full_intake.py - the whole ball system: collect, lift, store, feed and shoot
#
# Scenario: balls released from the own resource areas (viewer3d.py --balls released).
# Robot v22 in Red Start 1 facing 0 deg. Ports (robot_config.json, assumptions):
#   DC1 intake rollers  DC4 tower  DC5 basket feeder  BL1 shooter wheels
#
#   1. collect the 10 balls of resource area 1 with the intake and the tower running:
#      the balls climb the tower and fill the basket (6), the rest wait in the tower
#   2. drive to a shooting spot in the red half, turn so the launcher (left side) faces
#      the blue mobile fortress
#   3. compute the shooter power for a ballistic shot into the fortress upper level
#      (407 mm) and fire: feeder + shooter + tower until the robot is empty
#
# The launch model (speed 8 m/s at 100 % power, 40 deg hood) is a simulator estimate;
# on the robot, calibrate the power against distance with real shots.
#
# Simulator: viewer3d.py --balls released --program ../control/test_full_intake.py --time-limit 100
import math
import time
from mbuild import power_expand_board as pb
import chassis as ch

LAUNCH_SPEED_MM_S = 8000.0      # at 100 % shooter power (simulator estimate)
HOOD_DEG = 40.0
EXIT_LEFT_MM = 290.0            # launcher exit, left of the robot centre
EXIT_Z_MM, TARGET_Z_MM = 402.0, 442.0     # ball centre at launch / resting on the fortress mesh
G = 9810.0
# blue fortress centre in odometry coordinates (start: Red Start 1 at 325, 325 mm, facing +x)
TARGET_X_CM, TARGET_Y_CM = -(1527.5 - 325) / 10, (3993.0 - 325) / 10


def report(step, arrived):
    print("%-26s %-6s x=%7.1f cm  y=%7.1f cm  heading=%6.1f deg" % (
        step, "ok" if arrived else "MISSED", ch.odo.x, ch.odo.y, ch.odo.heading))


def ports(power, *names):
    for name in names:
        if power:
            pb.set_power(name, power)
        else:
            pb.stop(name)


def aim():
    """Heading (clockwise deg) that points the left side at the target, and the distance."""
    dx, dy = TARGET_X_CM - ch.odo.x, TARGET_Y_CM - ch.odo.y
    return math.degrees(math.atan2(dy, -dx)), math.hypot(dx, dy) * 10


def shooter_power(distance_mm):
    """Power for a ballistic shot over distance_mm (flat ground, no drag)."""
    h = math.radians(HOOD_DEG)
    rise = TARGET_Z_MM - EXIT_Z_MM
    v = math.sqrt(G * distance_mm ** 2 / (2 * math.cos(h) ** 2 * (distance_mm * math.tan(h) - rise)))
    return min(100.0, 100.0 * v / LAUNCH_SPEED_MM_S)


print("full intake test")
ch.odo.calibrate(1.0)
ch.odo.reset()

report("leave start area", ch.left(27.5))
ports(80, "DC1", "DC4")
report("collect area 1", ch.drive(forward_cm=115, timeout=8))
time.sleep(1.0)                                    # let the last balls climb
ports(0, "DC1")

report("shooting spot", ch.drive(forward_cm=12.5, right_cm=-41, timeout=6))   # field (1600, 1000)
heading, distance = aim()
report("aim at blue fortress", ch.turn_to(heading))
heading, distance = aim()
power = shooter_power(distance - EXIT_LEFT_MM)
print("distance %.0f mm -> shooter power %.0f %%" % (distance - EXIT_LEFT_MM, power))

pb.set_power("BL1", power)
time.sleep(0.5)                                    # wheels up to speed
ports(80, "DC5", "DC4")
time.sleep(9.0)
ports(0, "DC5", "DC4", "BL1")
ch.stop()
print("done")
