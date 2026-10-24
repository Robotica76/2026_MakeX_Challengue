# test_chassis_control_automatico.py - autonomous check of chassis.py
# Runs the closed-loop moves (encoders + gyroscope) one by one and prints, after
# each, whether it arrived and where odometry thinks the robot is.
#
# Simulator: Load .py -> this file (chassis.py is found in software/controls/drivetrain), Run.
# Start the robot in Red Start 1 facing 0 deg. It first moves out of the corner
# (a 45 cm robot spinning next to two walls would clip the field edge), then drives
# a square to its left and comes back.
# Robot: upload together with chassis.py; robot still when the program starts.
import time
import chassis as ch

SIDE_CM = 60


def report(step, arrived):
    print("%-22s %-8s x=%7.1f cm  y=%7.1f cm  heading=%7.1f deg" % (
        step, "ok" if arrived else "MISSED", ch.odo.x, ch.odo.y, ch.odo.heading))


print("chassis automatic test: USE_SENSORS =", ch.USE_SENSORS)
ch.odo.calibrate(1.0)      # robot must be still
ch.odo.reset()
report("start", True)

# 0. Out of the start corner: forward, then strafe left (no turning yet).
report("forward 40 cm", ch.forward(40))
report("left 40 cm", ch.left(40))

# 1. Square, counterclockwise. turn_to() uses absolute headings so the 1.5 deg
#    tolerance of each turn does not add up (turn(-90) four times drifts ~4-6 deg).
for side in range(4):
    report("forward %d cm" % SIDE_CM, ch.forward(SIDE_CM))
    heading = -90 * (side + 1)
    report("turn_to %d deg" % heading, ch.turn_to(heading))

# 2. Strafing without turning: right then left, back to the square's corner.
report("right %d cm" % (SIDE_CM // 2), ch.right(SIDE_CM // 2))
report("left %d cm" % (SIDE_CM // 2), ch.left(SIDE_CM // 2))

# 3. Diagonal and absolute heading.
report("diagonal 30/30 cm", ch.drive(forward_cm=30, right_cm=-30))
report("turn_to 45 deg", ch.turn_to(45))
report("turn_to 0 deg", ch.turn_to(0))
report("diagonal back", ch.drive(forward_cm=-30, right_cm=30))

# 4. Back to the start spot.
report("right 40 cm", ch.right(40))
report("backward 40 cm", ch.backward(40))

ch.stop()
error = (ch.odo.x ** 2 + ch.odo.y ** 2) ** 0.5
print("done: %.1f cm from the start by odometry, heading %.1f deg" % (error, ch.normalize(ch.odo.heading)))
