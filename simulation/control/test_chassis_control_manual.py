# test_chassis_control_manual.py - manual (gamepad) check of chassis.py
# Left stick: drive and strafe. Right stick (x): turn. Heading hold keeps the
# robot straight while driving without turning.
#   "≡" (menu)  front = F1 (launcher)
#   "+" (plus)  front = F2 (gripper), forward and strafe are inverted
#   N1          reset odometry to (0, 0, 0 deg) at the current spot
# Prints the odometry pose once per second.
#
# Simulator: viewer.py --time-limit 100 (manual stage), click Open gamepad,
# Load .py -> this file (chassis.py is found in software/controls/drivetrain), Run.
import time
from mbuild import gamepad
import chassis as ch

print("chassis manual test: USE_SENSORS =", ch.USE_SENSORS)
ch.odo.calibrate(1.0)      # robot must be still
ch.odo.reset()
ch.reset_smoothing()

front = ch.F1
last_print = time.time()
while True:
    if gamepad.is_key_pressed("≡") and front != ch.F1:
        front = ch.F1
        print("front: F1 (launcher)")
    elif gamepad.is_key_pressed("+") and front != ch.F2:
        front = ch.F2
        print("front: F2 (gripper)")
    if gamepad.is_key_pressed("N1"):
        ch.odo.reset()
        print("odometry reset")

    ch.joystick_drive(front)

    if time.time() - last_print >= 1.0:
        last_print = time.time()
        print("x=%7.1f cm  y=%7.1f cm  heading=%7.1f deg" % (ch.odo.x, ch.odo.y, ch.odo.heading))
    time.sleep(ch.PERIOD)
