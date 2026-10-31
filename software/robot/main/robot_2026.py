# robot_2026.py - competition program, 2026 robot (v22), built on the 2025 blocks program
# (software/legacy/challenge_2025) with the chassis dynamics of chassis.py.
#
# Same flow as 2025:
#   setup -> wait for N1 (match start) -> automatic stage -> manual stage loop
#   manual: "≡" ball mode (2025: launcher mode), "+" gripper mode (2025: gripper mode)
# What changed from 2025:
#   - driving: chassis.py instead of the motor formulas and move() by degrees. Manual:
#     joystick_drive() with the S-curve (adaptive to speed and vibration) and gyro heading hold;
#     automatic: drive() / turn_to() closed loop on encoders + gyro (Avanzar_N -> ch.forward,
#     avance_derecha_N -> ch.right, girar_derecha_90 -> ch.turn(90), ...). With
#     ch.USE_SENSORS = False everything falls back to open-loop move(), like 2025.
#   - automatic stage: the pull strategy (auto_pull_central.run), chosen before the start:
#     N2 "mixed" (default), N3 "balls", N4 "props" (press while waiting for N1)
#   - mechanisms: the v22 ports, DC motors instead of smart servos (robot_config.json
#     "mechanisms"; ports are assumptions until the electrical team confirms them):
#       DC1 intake throat rollers   DC2 intake head lift   DC3 elevator carriage   DC4 tower
#       DC5 feeder                  DC6 gripper jaw (+ closes)   DC7 intake head roller
#       BL1 shooter (brushless)
#
# Controls (manual stage)
#   left stick drive / strafe toward the mode's front, right stick x turn
#   "≡" ball mode, front = intake        "+" gripper mode, front = gripper (right side)
#   ball mode:     L1 intake in (throat, head roller, tower)   L2 spit out
#                  R1 shoot (shooter + feeder)   R2 shooter spin-up only
#                  Up / Down intake head up / down
#   gripper mode:  Up / Down elevator up / down   Left / Right jaw open / close
#                  L1 / L2 intake as in ball mode
#   N1 reset the odometry at the current spot
#
# Robot: one file for mBlock's Python editor:
#   python tools/scripts/bundle_for_mblock.py software/robot/main/robot_2026.py
# Simulator: Load program -> this file (chassis.py and auto_pull_central.py are found in software/).
import time
from mbuild import gamepad
from mbuild import power_expand_board
import chassis as ch
import auto_pull_central as auto

BALL_FRONT = ch.F_INTAKE
GRIP_FRONT = ch.F_GRIPPER
INTAKE_POWER = 80
SHOOTER_POWER = 70           # BL1, % (tune with the shooting tables)
FEEDER_POWER = 80
HEAD_POWER = 100
ELEVATOR_POWER = 100
JAW_POWER = 60
STRATEGY_KEYS = (("N2", "mixed"), ("N3", "balls"), ("N4", "props"))

MODE_BALLS, MODE_GRIPPER = 0, 1


def pressed(key):
    return gamepad.is_key_pressed(key)


def set_power(port, power):
    if power == 0:
        power_expand_board.stop(port)
    else:
        power_expand_board.set_power(port, power)


def stop_mechanisms():
    for port in ("DC1", "DC2", "DC3", "DC4", "DC5", "DC6", "DC7", "BL1"):
        power_expand_board.stop(port)


def hold(up_key, down_key, port, power):
    # power on `port` while a key is held, stopped otherwise (2025: subir_pinza / bajar_pinza)
    if pressed(up_key):
        set_power(port, power)
    elif pressed(down_key):
        set_power(port, -power)
    else:
        set_power(port, 0)


def intake_controls():
    if pressed("L1"):                     # in: throat, head roller and tower
        power = INTAKE_POWER
    elif pressed("L2"):                   # spit out
        power = -INTAKE_POWER
    else:
        power = 0
    for port in ("DC1", "DC7", "DC4"):
        set_power(port, power)


def ball_mode():
    ch.joystick_drive(BALL_FRONT)
    intake_controls()
    hold("Up", "Down", "DC2", HEAD_POWER)
    shooting = pressed("R1")
    set_power("BL1", SHOOTER_POWER if shooting or pressed("R2") else 0)
    set_power("DC5", FEEDER_POWER if shooting else 0)


def gripper_mode():
    ch.joystick_drive(GRIP_FRONT)
    intake_controls()
    hold("Up", "Down", "DC3", ELEVATOR_POWER)
    hold("Right", "Left", "DC6", JAW_POWER)          # Right closes, Left opens (2025 layout)
    set_power("BL1", 0)
    set_power("DC5", 0)


def wait_for_start():
    # Strategy keys before the start, N1 starts the match (2025: wait until N1)
    strategy = auto.STRATEGY
    print("waiting for N1, strategy", strategy)
    while not pressed("N1"):
        for key, name in STRATEGY_KEYS:
            if pressed(key) and strategy != name:
                strategy = name
                print("strategy", strategy)
        time.sleep(ch.PERIOD)
    return strategy


def automatic(strategy):
    auto.run(strategy, calibrate=False)  # stops everything before 29.5 s (R19)


def manual():
    mode = MODE_BALLS
    ch.reset_smoothing()
    while True:
        if pressed("≡") and mode != MODE_BALLS:
            mode = MODE_BALLS
            ch.reset_smoothing()
            print("ball mode")
        if pressed("+") and mode != MODE_GRIPPER:
            mode = MODE_GRIPPER
            ch.reset_smoothing()
            print("gripper mode")
        if pressed("N1"):
            ch.odo.reset()
        if mode == MODE_BALLS:
            ball_mode()
        else:
            gripper_mode()
        time.sleep(ch.PERIOD)


# setup: robot still on the start area while the gyro is calibrated
stop_mechanisms()
ch.stop()
ch.odo.calibrate(1.0)
ch.odo.reset()
chosen = wait_for_start()
automatic(chosen)
manual()
