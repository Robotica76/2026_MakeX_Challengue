# test_chassis_control_manual.py - manual (gamepad) check of chassis.py
# Left stick: drive and strafe. Right stick (x): turn. Heading hold keeps the
# robot straight while driving without turning.
# Fronts (v22: intake ahead, gripper on the right, launcher on the left); stick up
# drives toward the chosen side:
#   N2          front = F_INTAKE (start)
#   "+" (plus)  front = F_GRIPPER
#   "≡" (menu)  front = F_LAUNCHER
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

FRONTS = (("N2", ch.F_INTAKE, "intake"), ("+", ch.F_GRIPPER, "gripper"), ("≡", ch.F_LAUNCHER, "launcher"))
front = ch.F_INTAKE
last_print = time.time()
while True:
    for key, side, name in FRONTS:
        if gamepad.is_key_pressed(key) and front != side:
            front = side
            print("front:", name)
    if gamepad.is_key_pressed("N1"):
        ch.odo.reset()
        print("odometry reset")

    ch.joystick_drive(front)

    if time.time() - last_print >= 1.0:
        last_print = time.time()
        print("x=%7.1f cm  y=%7.1f cm  heading=%7.1f deg" % (ch.odo.x, ch.odo.y, ch.odo.heading))
    time.sleep(ch.PERIOD)
