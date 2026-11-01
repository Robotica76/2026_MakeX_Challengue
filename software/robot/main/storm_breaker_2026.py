# storm_breaker_2026.py - ROBOTICA 76 competition program, 2026 robot (v22), Red Start 1, lower half
# Written in the subset of Python that mBlock blocks can express (global variables, custom blocks
# with number inputs, no lists, no return values): tools/scripts/python_to_mblock.py turns it into
# storm_breaker_2026.mblock, and mBlock's Python view of those blocks is this same program.
#
# Strategy (Monte Carlo search, simulation/analysis/montecarlo_strategy.py):
#   automatic  the X12 bonus cube into red exchange area 1 (+12 balls worth 20 each), taken from
#              the lower strategy area: the intake head pulls it off the top, pulls it again from
#              the floor onto our side, the gripper puts it in the exchange area; optionally the
#              X9 and the second cone pulled onto our side (DENY_X9: lane a 50 mm farther in so the
#              body clears the X12 in the exchange area; the robot then waits at (1200, 800))
#   manual     driver: "≡" ball mode, "+" gripper mode (see manual_loop); R2 held: the robot aims
#              its launcher at the blue fortress and sets the power from the distance (odometry)
#   final      N4, with the robot in Red Start 1, hangs the flag on flagpole 2 by itself
# Two robots per alliance: this robot stays at y <= 1527.5 mm (lower half of the red area).
#
# Chassis control (instead of 2025's move() by degrees):
#   odometry   4 encoders (mecanum unmix) + gyro angle (bias calibrated at the start); the strafe
#              distance is scaled by STRAFE_SLIP (mecanum rollers slip sideways: measure it on the
#              field by strafing 1 m and comparing with the encoders)
#   motion     go_N_N_N_N_N(x, y, heading, v_max, v_end): field coordinates (mm, deg), the robot
#              translates and turns at the same time (mecanum); speed profile limited by
#              acceleration A_MAX and braking D_MAX, v = sqrt(v_end^2 + 2 D d) so the robot brakes
#              as late as possible and does not crawl at the end like a P controller; v_end > 0
#              passes a waypoint without stopping; feedback every cycle from the odometry
#   mechanisms timed jobs (head, carriage, jaw) run while the robot drives
#
# Ports (robot_config.json, assumptions until the electrical team confirms): drive M1 FR, M2 RR,
# M3 RL, M4 FL; DC1 intake throat, DC2 intake head lift (53 mm/s), DC3 elevator carriage
# (150 mm/s), DC4 tower, DC5 feeder, DC6 gripper jaw (+ closes), DC7 intake head roller, BL1 shooter.
import novapi
from mbuild import gamepad
from mbuild import power_expand_board
from mbuild.encoder_motor import encoder_motor_class
import math
import time

# initialize variables
STRATEGY = 0
DENY_X9 = 0
V_MAX = 0
V_APPROACH = 0
V_PULL = 0
A_MAX = 0
D_MAX = 0
V_MIN = 0
W_MAX = 0
K_HEADING = 0
POS_TOL = 0
HEAD_TOL = 0
PASS_RADIUS = 0
FACE_DIST = 0
GO_TIMEOUT = 0
PERIOD = 0
MAX_RPM = 0
RPM_TO_MM_S = 0
WHEEL_MM_PER_DEG = 0
TURN_MM_PER_DEG = 0
ODOM_OFFSET = 0
STRAFE_SLIP = 0
LANE_B = 0
LANE_A = 0
X_LANE = 0
X_PROPS_IN = 0
X_FLOOR_IN = 0
PROP_HEAD = 0
FLOOR_HEAD = 0
CONE_CLEAR_HEAD = 0
X12_Y = 0
GRAB_RIGHT = 0
GRAB_BACK = 0
GRAB_SHORT = 0
PINNED = 0
EXCHANGE_X = 0
EXCHANGE_Y = 0
PARK_X = 0
PARK_Y = 0
PARK_HEAD = 0
END_BY = 0
pos_x = 0
pos_y = 0
heading = 0
wheel_x = 0
wheel_y = 0
enc_fl = 0
enc_fr = 0
enc_rl = 0
enc_rr = 0
gyro_bias = 0
rot_start = 0
t_cal = 0
v_now = 0
t_prev = 0
go_done = 0
go_end = 0
dx = 0
dy = 0
dist = 0
herr = 0
v_des = 0
v_dec = 0
ux = 0
uy = 0
fwd = 0
right = 0
turn_rate = 0
w_cw = 0
w_fl = 0
w_fr = 0
w_rl = 0
w_rr = 0
w_big = 0
w_k = 0
d_fl = 0
d_fr = 0
d_rl = 0
d_rr = 0
a_fl = 0
a_fr = 0
a_rl = 0
a_rr = 0
yaw = 0
step_f = 0
step_r = 0
mid_h = 0
dt = 0
head_mm = 0
head_from = 0
head_t0 = 0
head_t1 = 0
head_moving = 0
carriage_mm = 0
carriage_from = 0
carriage_t0 = 0
carriage_t1 = 0
carriage_moving = 0
jaw_t1 = 0
jaw_moving = 0
estimate = 0
cube_x = 0
mode = 0
front = 0
stick_f = 0
stick_r = 0
stick_w = 0
cmd_f = 0
cmd_r = 0
cmd_w = 0
hold_heading = 0
k = 0
total = 0
samples = 0
in_auto = 0
face = 0
angle = 0
h_goal = 0
SHOT_SPEED_FULL = 0
HOOD_DEG = 0
EXIT_LEFT = 0
AIM_SHORT = 0
SHOT_RISE = 0
FORT_X = 0
FORT_Y = 0
aim_d = 0
aim_v = 0
shot_power = 0
t_feed = 0
t_loop = 0
X_LANE_A = 0
PARK2_X = 0
PARK2_Y = 0
x_far = 0

# new class
encoder_motor_M1 = encoder_motor_class("M1", "INDEX1")
encoder_motor_M2 = encoder_motor_class("M2", "INDEX1")
encoder_motor_M3 = encoder_motor_class("M3", "INDEX1")
encoder_motor_M4 = encoder_motor_class("M4", "INDEX1")


def constants():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # tuned values (simulation/analysis/montecarlo_strategy.py); blocks start every variable at 0
    STRATEGY = 1
    DENY_X9 = 1
    V_MAX = 700
    V_APPROACH = 500
    V_PULL = 400
    A_MAX = 1200
    D_MAX = 1400
    V_MIN = 60
    W_MAX = 200
    K_HEADING = 5
    POS_TOL = 8
    HEAD_TOL = 2
    PASS_RADIUS = 40
    FACE_DIST = 500
    GO_TIMEOUT = 5
    PERIOD = 0.01
    MAX_RPM = 300
    RPM_TO_MM_S = 4.18879
    WHEEL_MM_PER_DEG = 0.69813
    TURN_MM_PER_DEG = 6.03
    ODOM_OFFSET = 79
    STRAFE_SLIP = 1
    LANE_B = 951
    LANE_A = 590
    X_LANE = 1800
    X_LANE_A = 1850
    PARK2_X = 1200
    PARK2_Y = 800
    X_PROPS_IN = 2000
    X_FLOOR_IN = 1925
    PROP_HEAD = 250
    FLOOR_HEAD = 50
    CONE_CLEAR_HEAD = 150
    X12_Y = 839.5
    GRAB_RIGHT = 228.5
    GRAB_BACK = 89
    GRAB_SHORT = 0
    PINNED = 177
    EXCHANGE_X = 1520
    EXCHANGE_Y = 360
    PARK_X = 2000
    PARK_Y = 745
    PARK_HEAD = 250
    END_BY = 29
    SHOT_SPEED_FULL = 8000
    HOOD_DEG = 40
    EXIT_LEFT = 290
    AIM_SHORT = 150
    SHOT_RISE = 40
    FORT_X = 3993
    FORT_Y = 1527.5


def calibrate_N_N_N(x, y, h):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # robot still: gyro bias, then the odometry starts at field (x, y) mm, heading h deg
    total = 0
    samples = 0
    t_cal = novapi.timer() + 0.5
    while not (novapi.timer() > t_cal):
        time.sleep(0.001)
        total = total + novapi.get_gyroscope("z")
        samples = samples + 1
        time.sleep(PERIOD)
    gyro_bias = total / samples
    t_cal = novapi.timer()
    rot_start = novapi.get_rotation("z")
    set_pose_N_N_N(x, y, h)


def set_pose_N_N_N(x, y, h):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    enc_fl = encoder_motor_M4.get_value("angle")
    enc_fr = encoder_motor_M1.get_value("angle")
    enc_rl = encoder_motor_M3.get_value("angle")
    enc_rr = encoder_motor_M2.get_value("angle")
    heading = h
    rot_start = novapi.get_rotation("z") - gyro_bias * (novapi.timer() - t_cal)
    rot_start = rot_start + h
    wheel_x = x - ODOM_OFFSET * math.cos(math.radians(h))
    wheel_y = y - ODOM_OFFSET * math.sin(math.radians(h))
    pos_x = x
    pos_y = y
    v_now = 0
    t_prev = novapi.timer()


def read_odometry():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # heading: field degrees counterclockwise (the gyro angle grows clockwise)
    yaw = rot_start - (novapi.get_rotation("z") - gyro_bias * (novapi.timer() - t_cal))
    a_fl = encoder_motor_M4.get_value("angle")
    a_fr = encoder_motor_M1.get_value("angle")
    a_rl = encoder_motor_M3.get_value("angle")
    a_rr = encoder_motor_M2.get_value("angle")
    d_fl = (enc_fl - a_fl) * WHEEL_MM_PER_DEG
    d_fr = (a_fr - enc_fr) * WHEEL_MM_PER_DEG
    d_rl = (enc_rl - a_rl) * WHEEL_MM_PER_DEG
    d_rr = (a_rr - enc_rr) * WHEEL_MM_PER_DEG
    enc_fl = a_fl
    enc_fr = a_fr
    enc_rl = a_rl
    enc_rr = a_rr
    step_f = (d_fl + d_fr + d_rl + d_rr) / 4
    step_r = (d_fl - d_fr - d_rl + d_rr) / 4 * STRAFE_SLIP
    mid_h = (heading + yaw) / 2
    wheel_x = wheel_x + step_f * math.cos(math.radians(mid_h)) + step_r * math.sin(math.radians(mid_h))
    wheel_y = wheel_y + step_f * math.sin(math.radians(mid_h)) - step_r * math.cos(math.radians(mid_h))
    heading = yaw
    pos_x = wheel_x + ODOM_OFFSET * math.cos(math.radians(heading))
    pos_y = wheel_y + ODOM_OFFSET * math.sin(math.radians(heading))


def set_wheels_N_N_N(f, r, w):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # f, r: wheel-centre speed forward / right (mm/s); w: turn rate, deg/s counterclockwise
    w_cw = 0 - w * TURN_MM_PER_DEG
    w_fl = f + r + w_cw
    w_fr = f - r - w_cw
    w_rl = f - r + w_cw
    w_rr = f + r - w_cw
    w_big = abs(w_fl)
    if abs(w_fr) > w_big:
        w_big = abs(w_fr)
    if abs(w_rl) > w_big:
        w_big = abs(w_rl)
    if abs(w_rr) > w_big:
        w_big = abs(w_rr)
    w_k = 1 / RPM_TO_MM_S
    if w_big > MAX_RPM * RPM_TO_MM_S:
        w_k = MAX_RPM / w_big
    encoder_motor_M4.set_speed(0 - w_fl * w_k)
    encoder_motor_M1.set_speed(w_fr * w_k)
    encoder_motor_M3.set_speed(0 - w_rl * w_k)
    encoder_motor_M2.set_speed(w_rr * w_k)


def go_N_N_N_N_N(x, y, h, vmax, vend):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # field (x, y) mm, heading h deg; vmax mm/s; vend > 0: pass the point without stopping
    go_done = 0
    go_end = novapi.timer() + GO_TIMEOUT
    while not (go_done == 1):
        time.sleep(0.001)
        read_odometry()
        service_jobs()
        dx = x - pos_x
        dy = y - pos_y
        dist = math.sqrt(dx * dx + dy * dy)
        h_goal = h
        if face == 1:
            if dist > FACE_DIST:
                atan2_N_N(dy, dx)
                h_goal = angle
        herr = h_goal - heading
        if herr > 180:
            herr = herr - 360
        if herr < -180:
            herr = herr + 360
        dt = novapi.timer() - t_prev
        t_prev = novapi.timer()
        v_dec = math.sqrt(vend * vend + 2 * D_MAX * dist)
        v_des = vmax
        if v_dec < v_des:
            v_des = v_dec
        if v_des > v_now + A_MAX * dt:
            v_des = v_now + A_MAX * dt
        if vend == 0:
            if v_des < V_MIN:
                if dist > POS_TOL:
                    v_des = V_MIN
        v_now = v_des
        ux = 0
        uy = 0
        if dist > 0.5:
            ux = dx / dist
            uy = dy / dist
        fwd = v_now * (ux * math.cos(math.radians(heading)) + uy * math.sin(math.radians(heading)))
        right = v_now * (ux * math.sin(math.radians(heading)) - uy * math.cos(math.radians(heading)))
        turn_rate = K_HEADING * herr
        if turn_rate > W_MAX:
            turn_rate = W_MAX
        if turn_rate < 0 - W_MAX:
            turn_rate = 0 - W_MAX
        right = right + turn_rate * 0.0174533 * ODOM_OFFSET
        set_wheels_N_N_N(fwd, right, turn_rate)
        if vend > 0:
            if dist < PASS_RADIUS:
                go_done = 1
        else:
            if dist < POS_TOL:
                if abs(herr) < HEAD_TOL:
                    go_done = 1
        if novapi.timer() > go_end:
            go_done = 1
        if in_auto == 1:
            if novapi.timer() > END_BY:
                go_done = 1
        time.sleep(PERIOD)
    if vend == 0:
        set_wheels_N_N_N(0, 0, 0)
        v_now = 0


def travel_N_N_N_N_N(x, y, h, vmax, vend):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # long move facing the way it goes (forward travel slips ~1 %, strafing ~7 %), turning to h
    # in the last FACE_DIST mm
    face = 1
    go_N_N_N_N_N(x, y, h, vmax, vend)
    face = 0


def atan2_N_N(ay, ax):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # angle of (ax, ay) in degrees, -180..180 (blocks have atan only)
    if ax > 0:
        angle = math.degrees(math.atan(ay / ax))
    else:
        if ax < 0:
            angle = math.degrees(math.atan(ay / ax)) + 180
            if angle > 180:
                angle = angle - 360
        else:
            angle = 90
            if ay < 0:
                angle = -90


def stop_wheels():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    set_wheels_N_N_N(0, 0, 0)
    v_now = 0


def head_estimate():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    estimate = head_mm
    if head_moving == 1:
        if novapi.timer() < head_t1:
            estimate = head_from + (head_mm - head_from) * (novapi.timer() - head_t0) / (head_t1 - head_t0)


def head_to_N(mm):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # intake head lift, open loop at 53 mm/s; returns at once (service_jobs stops it)
    head_estimate()
    head_from = estimate
    head_mm = mm
    head_t0 = novapi.timer()
    head_t1 = head_t0 + abs(mm - head_from) / 53
    head_moving = 1
    if mm > head_from:
        power_expand_board.set_power("DC2", 100)
    else:
        power_expand_board.set_power("DC2", -100)


def carriage_to_N(mm):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    carriage_from = carriage_mm
    carriage_mm = mm
    carriage_t0 = novapi.timer()
    carriage_t1 = carriage_t0 + abs(mm - carriage_from) / 150
    carriage_moving = 1
    if mm > carriage_from:
        power_expand_board.set_power("DC3", 100)
    else:
        power_expand_board.set_power("DC3", -100)


def jaw_N(seconds):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # gripper jaw: seconds > 0 closes, < 0 opens
    jaw_t1 = novapi.timer() + abs(seconds)
    jaw_moving = 1
    if seconds > 0:
        power_expand_board.set_power("DC6", 100)
    else:
        power_expand_board.set_power("DC6", -100)


def service_jobs():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    if head_moving == 1:
        if novapi.timer() > head_t1:
            power_expand_board.stop("DC2")
            head_moving = 0
    if carriage_moving == 1:
        if novapi.timer() > carriage_t1:
            power_expand_board.stop("DC3")
            carriage_moving = 0
    if jaw_moving == 1:
        if novapi.timer() > jaw_t1:
            power_expand_board.stop("DC6")
            jaw_moving = 0


def wait_jobs():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    while not (head_moving + carriage_moving + jaw_moving == 0):
        time.sleep(0.001)
        service_jobs()
        read_odometry()
        time.sleep(PERIOD)


def lane_x_N(lane):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # lane a runs 50 mm farther in: the body (back at x - 250) clears the X12 already in the
    # exchange area (x <= 1580)
    x_far = X_LANE
    if lane == LANE_A:
        x_far = X_LANE_A


def props_pass_N(lane):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # head on the props of the strategy area top: they come off and drop at the centre line
    lane_x_N(lane)
    head_to_N(PROP_HEAD)
    go_N_N_N_N_N(x_far, lane, 0, V_MAX, 0)
    wait_jobs()
    power_expand_board.set_power("DC7", 100)
    go_N_N_N_N_N(X_PROPS_IN, lane, 0, V_APPROACH, 0)
    time.sleep(0.2)
    go_N_N_N_N_N(x_far, lane, 0, V_PULL, 0)
    power_expand_board.stop("DC7")


def floor_pass_N(lane):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # head at the floor: the props at the line come onto our side
    lane_x_N(lane)
    head_to_N(FLOOR_HEAD)
    go_N_N_N_N_N(x_far, lane, 0, V_MAX, 0)
    wait_jobs()
    power_expand_board.set_power("DC7", 100)
    go_N_N_N_N_N(X_FLOOR_IN, lane, 0, V_APPROACH, 0)
    time.sleep(0.2)
    go_N_N_N_N_N(x_far, lane, 0, V_PULL, 0)
    power_expand_board.stop("DC7")


def x12_to_exchange():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # gripper (right side) toward +x, straddle the cube from our side, close, turn while carrying
    cube_x = pos_x + PINNED
    head_to_N(CONE_CLEAR_HEAD)
    jaw_N(0.35)
    # straight back first: the cube touches the robot front and a turn here would shove it
    go_N_N_N_N_N(pos_x - 150, pos_y, 0, V_APPROACH, 0)
    go_N_N_N_N_N(cube_x - GRAB_RIGHT - 200, X12_Y + GRAB_BACK - GRAB_SHORT, 90, V_MAX, 0)
    wait_jobs()
    go_N_N_N_N_N(cube_x - GRAB_RIGHT, X12_Y + GRAB_BACK - GRAB_SHORT, 90, V_APPROACH, 0)
    jaw_N(0.3)
    wait_jobs()
    go_N_N_N_N_N(EXCHANGE_X + GRAB_BACK, EXCHANGE_Y + GRAB_RIGHT, 0, V_APPROACH, 0)
    jaw_N(-0.8)
    wait_jobs()


def park():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # clear of the cube and of the balls the observers release at 30 s; head over the strategy area
    head_to_N(PARK_HEAD)
    go_N_N_N_N_N(PARK_X - 100, PARK_Y, 0, V_MAX, 0)
    wait_jobs()
    go_N_N_N_N_N(PARK_X, PARK_Y, 0, V_APPROACH, 0)


def park_west():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # with the X9 and the cone next to the strategy area, wait west of the released balls
    # (x >= 1325), clear of the fortress (y <= 1208) and of the shelf legs (y >= 318)
    go_N_N_N_N_N(PARK2_X, PARK2_Y, 0, V_MAX, 0)


def automatic():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    in_auto = 1
    novapi.reset_timer()
    calibrate_N_N_N(325, 325, 0)
    head_to_N(PROP_HEAD)
    travel_N_N_N_N_N(600, 600, 0, V_MAX, 400)
    travel_N_N_N_N_N(X_LANE, LANE_B, 0, V_MAX, 0)
    props_pass_N(LANE_B)
    floor_pass_N(LANE_B)
    x12_to_exchange()
    if DENY_X9 == 1:
        props_pass_N(LANE_A)
        floor_pass_N(LANE_A)
        park_west()
    else:
        park()
    wait_jobs()
    stop_wheels()
    power_expand_board.stop("DC2")
    power_expand_board.stop("DC3")
    power_expand_board.stop("DC6")
    power_expand_board.stop("DC7")
    in_auto = 0
    while not (novapi.timer() > 30):
        # DO SOMETHING
        pass


def aim_and_shoot():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # R2 held: launcher (left side) toward the blue fortress, power from the distance (ballistic,
    # SHOT_SPEED_FULL mm/s at 100 %: calibrate with real shots), feed while R2 is held
    read_odometry()
    atan2_N_N(FORT_Y - pos_y, FORT_X - pos_x)
    stop_wheels()
    go_N_N_N_N_N(pos_x, pos_y, angle - 90, 300, 0)
    aim_d = math.sqrt((FORT_X - pos_x) * (FORT_X - pos_x) + (FORT_Y - pos_y) * (FORT_Y - pos_y)) - EXIT_LEFT - AIM_SHORT
    aim_v = math.sqrt(9810 * aim_d * aim_d / (2 * math.cos(math.radians(HOOD_DEG)) * math.cos(math.radians(HOOD_DEG)) * (aim_d * math.tan(math.radians(HOOD_DEG)) - SHOT_RISE)))
    shot_power = 100 * aim_v / SHOT_SPEED_FULL
    if shot_power > 100:
        shot_power = 100
    power_expand_board.set_power("BL1", shot_power)
    t_feed = novapi.timer() + 0.5
    while not (not gamepad.is_key_pressed("R2")):
        time.sleep(0.001)
        read_odometry()
        if novapi.timer() > t_feed:
            power_expand_board.set_power("DC5", 80)
            power_expand_board.set_power("DC4", 80)
        time.sleep(PERIOD)
    power_expand_board.stop("DC5")
    power_expand_board.stop("DC4")
    power_expand_board.stop("BL1")
    hold_heading = heading


def hang_flag():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # final stage, N4 with the robot in Red Start 1 (where the team puts it after the modification
    # stage): flag rod on the left side, facing the back wall over flagpole 2 (y 1010)
    set_pose_N_N_N(325, 325, 0)
    head_to_N(370)
    carriage_to_N(230)
    go_N_N_N_N_N(700, 600, 0, V_MAX, 300)
    go_N_N_N_N_N(700, 1204, 180, V_MAX, 0)
    wait_jobs()
    go_N_N_N_N_N(330, 1204, 180, 200, 0)
    carriage_to_N(160)
    wait_jobs()
    go_N_N_N_N_N(700, 1204, 180, 400, 0)


def drive_joystick_N(side):
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    # manual driving: sticks toward the chosen front (0 intake, 90 gripper), acceleration
    # limited like the automatic profile, heading held by the gyro while not turning
    read_odometry()
    stick_f = gamepad.get_joystick("Ly") * 8
    stick_r = gamepad.get_joystick("Lx") * 8
    stick_w = 0 - gamepad.get_joystick("Rx") * 2
    if abs(stick_f) < 64:
        stick_f = 0
    if abs(stick_r) < 64:
        stick_r = 0
    if abs(stick_w) < 16:
        stick_w = 0
    if side == 90:
        k = stick_f
        stick_f = 0 - stick_r
        stick_r = k
    k = A_MAX * PERIOD * 2
    if stick_f > cmd_f + k:
        cmd_f = cmd_f + k
    else:
        if stick_f < cmd_f - k:
            cmd_f = cmd_f - k
        else:
            cmd_f = stick_f
    if stick_r > cmd_r + k:
        cmd_r = cmd_r + k
    else:
        if stick_r < cmd_r - k:
            cmd_r = cmd_r - k
        else:
            cmd_r = stick_r
    cmd_w = stick_w
    if stick_w == 0:
        herr = hold_heading - heading
        if herr > 180:
            herr = herr - 360
        if herr < -180:
            herr = herr + 360
        cmd_w = K_HEADING * herr
    else:
        hold_heading = heading
    set_wheels_N_N_N(cmd_f, cmd_r, cmd_w)


def manual_loop():
    global STRATEGY, DENY_X9, V_MAX, V_APPROACH, V_PULL, A_MAX, D_MAX, V_MIN, W_MAX, K_HEADING, POS_TOL, HEAD_TOL, PASS_RADIUS, FACE_DIST, GO_TIMEOUT, PERIOD, MAX_RPM, RPM_TO_MM_S, WHEEL_MM_PER_DEG, TURN_MM_PER_DEG, ODOM_OFFSET, STRAFE_SLIP, LANE_B, LANE_A, X_LANE, X_PROPS_IN, X_FLOOR_IN, PROP_HEAD, FLOOR_HEAD, CONE_CLEAR_HEAD, X12_Y, GRAB_RIGHT, GRAB_BACK, GRAB_SHORT, PINNED, EXCHANGE_X, EXCHANGE_Y, PARK_X, PARK_Y, PARK_HEAD, END_BY, pos_x, pos_y, heading, wheel_x, wheel_y, enc_fl, enc_fr, enc_rl, enc_rr, gyro_bias, rot_start, t_cal, v_now, t_prev, go_done, go_end, dx, dy, dist, herr, v_des, v_dec, ux, uy, fwd, right, turn_rate, w_cw, w_fl, w_fr, w_rl, w_rr, w_big, w_k, d_fl, d_fr, d_rl, d_rr, a_fl, a_fr, a_rl, a_rr, yaw, step_f, step_r, mid_h, dt, head_mm, head_from, head_t0, head_t1, head_moving, carriage_mm, carriage_from, carriage_t0, carriage_t1, carriage_moving, jaw_t1, jaw_moving, estimate, cube_x, mode, front, stick_f, stick_r, stick_w, cmd_f, cmd_r, cmd_w, hold_heading, k, total, samples, in_auto, face, angle, h_goal, SHOT_SPEED_FULL, HOOD_DEG, EXIT_LEFT, AIM_SHORT, SHOT_RISE, FORT_X, FORT_Y, aim_d, aim_v, shot_power, t_feed, t_loop, X_LANE_A, PARK2_X, PARK2_Y, x_far
    mode = 0
    hold_heading = heading
    head_moving = 0
    head_estimate()
    head_mm = estimate
    t_loop = novapi.timer()
    while True:
        time.sleep(0.001)
        if gamepad.is_key_pressed("≡"):
            mode = 0
        if gamepad.is_key_pressed("+"):
            mode = 1
        if gamepad.is_key_pressed("N4"):
            hang_flag()
        if gamepad.is_key_pressed("R2"):
            aim_and_shoot()
        dt = novapi.timer() - t_loop
        t_loop = novapi.timer()
        if mode == 0:
            drive_joystick_N(0)
            # the head height is tracked here too, so the flag routine knows where it starts
            if gamepad.is_key_pressed("Up"):
                power_expand_board.set_power("DC2", 100)
                head_mm = head_mm + 53 * dt
                if head_mm > 380:
                    head_mm = 380
            else:
                if gamepad.is_key_pressed("Down"):
                    power_expand_board.set_power("DC2", -100)
                    head_mm = head_mm - 53 * dt
                    if head_mm < 0:
                        head_mm = 0
                else:
                    power_expand_board.stop("DC2")
            if gamepad.is_key_pressed("R1"):
                power_expand_board.set_power("BL1", 70)
                power_expand_board.set_power("DC5", 80)
            else:
                power_expand_board.stop("BL1")
                power_expand_board.stop("DC5")
        else:
            drive_joystick_N(90)
            if gamepad.is_key_pressed("Up"):
                power_expand_board.set_power("DC3", 100)
            else:
                if gamepad.is_key_pressed("Down"):
                    power_expand_board.set_power("DC3", -100)
                else:
                    power_expand_board.stop("DC3")
            if gamepad.is_key_pressed("Right"):
                power_expand_board.set_power("DC6", 60)
            else:
                if gamepad.is_key_pressed("Left"):
                    power_expand_board.set_power("DC6", -60)
                else:
                    power_expand_board.stop("DC6")
        if gamepad.is_key_pressed("L1"):
            power_expand_board.set_power("DC1", 80)
            power_expand_board.set_power("DC7", 80)
            power_expand_board.set_power("DC4", 80)
        else:
            if gamepad.is_key_pressed("L2"):
                power_expand_board.set_power("DC1", -80)
                power_expand_board.set_power("DC7", -80)
                power_expand_board.set_power("DC4", -80)
            else:
                power_expand_board.stop("DC1")
                power_expand_board.stop("DC7")
                power_expand_board.stop("DC4")
        time.sleep(PERIOD)


constants()
stop_wheels()
while not (gamepad.is_key_pressed("N1")):
    # DO SOMETHING
    pass
if STRATEGY > 0:
    automatic()
manual_loop()
