# chassis.py - mecanum drive reused from makeX 2025, adapted to 8 cm wheels
# 2026 stage: odometry with encoders + gyroscope, accelerometer for collision detection.
import math
import time
import novapi
from mbuild import gamepad
from mbuild.encoder_motor import encoder_motor_class

# ---------------- mechanical constants ----------------
WHEEL_DIAMETER = 8.0                              # cm (2025: 6 cm)
DEGREES_PER_CM = 360 / (3.14159 * WHEEL_DIAMETER)  # 14.32 degrees/cm (2025: 19.10)

# Arc each wheel travels while the robot spins. Depends on the chassis, not the wheel:
# v22 CAD: half track 22.12 cm + half wheelbase 12.40 cm = 34.52 cm (2025 robot: 47 cm / 90 deg).
CM_PER_TURN_DEGREE = 34.52 * math.pi / 180    # 0.603 cm/deg

# The wheel rectangle (center of rotation) sits behind the footprint center.
# Odometry reports the footprint center, this far ahead of the wheel center (v22 CAD: 7.9 cm).
ODOM_CENTER_OFFSET_CM = 7.9

STRAFE_FACTOR = 1.0    # wheel travel / real travel when strafing (2025 used a fixed "+5 cm")
MAX_SPEED = 100        # max RPM sent to the motors
DEADZONE = 8           # joystick: values with |v| < DEADZONE are treated as 0
AUTO_SPEED = 80        # RPM for autonomous routines

# Fronts: which side of the robot the driver (or a routine) treats as "forward",
# in degrees clockwise from the robot's forward axis. v22 layout:
F_INTAKE = 0       # intake, front wheels (robot forward axis)
F_GRIPPER = 90     # gripper, right side
F_REAR = 180       # electronics box
F_LAUNCHER = -90   # launcher, left side
F1 = F_LAUNCHER    # button "≡" (2025 name)
F2 = F_GRIPPER     # button "+" (2025 name)

# True:  closed loop with encoders + gyroscope + accelerometer.
# False: purely mechanical (open loop with move(), like 2025). Use if a sensor fails or misbehaves.
#        Position and heading are then estimated from the commanded moves only.
USE_SENSORS = True

# ---------------- control constants (calibrate on the field) ----------------
GYRO_SIGN = 1            # set to -1 if heading decreases when turning clockwise
GYRO_DEADZONE = 0.5      # degrees/s: below this the robot is considered still (reduces drift)
KP_HEADING = 2.0         # RPM per degree of heading error (heading hold)
KP_TURN = 3.0            # RPM per degree of error in turn_to() (1 wheel RPM = ~0.8 robot degrees/s)
KP_DIST = 4.0            # RPM per cm of error in drive()
MIN_SPEED = 12           # min RPM to overcome friction at the end of a move
RAMP = 6                 # max RPM change per cycle: keeps the wheels from slipping
TOL_CM = 1.0
TOL_DEGREES = 1.5
IMPACT_THRESHOLD = 15.0  # horizontal acceleration (novapi units) considered a collision
PERIOD = 0.01            # seconds per control cycle

# ---------------- manual smoothing (S-curve) ----------------
# Velocity follows the joystick with an S-shaped profile: acceleration grows and fades
# gradually (limited jerk), so the robot does not rock or slip on quick stick changes.
# Units: RPM/s for acceleration, RPM/s^2 for jerk. Higher = more responsive, lower = smoother.
SMOOTHING = True
ACCEL = 400.0         # 0 -> 100 RPM in about 0.35 s
JERK = 3000.0
DECEL = 700.0         # braking is allowed to be quicker than speeding up
DECEL_JERK = 5000.0
TURN_ACCEL = 500.0
TURN_JERK = 4000.0

# Adaptive smoothing: scales the limits above on every cycle.
#  - by speed: snappier near standstill, gentler near top speed (no sensors needed)
#  - by vibration measured with the accelerometer (only when USE_SENSORS)
ADAPTIVE_SMOOTHING = True
LOW_SPEED_SCALE = 1.8    # limit multiplier at 0 RPM
HIGH_SPEED_SCALE = 0.7   # limit multiplier at MAX_SPEED
VIB_OK = 1.0             # vibration level (accelerometer units) with no penalty
VIB_MAX = 4.0            # vibration level where the penalty is full
VIB_MIN_SCALE = 0.4      # multiplier applied at VIB_MAX or above
VIB_BASE_TAU = 0.1       # s: slower than this is robot motion, faster is vibration
VIB_ENVELOPE_TAU = 0.2   # s: how quickly the vibration level reacts

# ---------------- motors ----------------
# Mapping deduced from the 2025 code, relative to the robot forward axis (v22: intake side):
#   M4 = FL   M1 = FR
#   M3 = RL   M2 = RR
# Left side motors are mirror-mounted, hence sign -1.
motor_FL = encoder_motor_class("M4", "INDEX1")
motor_FR = encoder_motor_class("M1", "INDEX1")
motor_RL = encoder_motor_class("M3", "INDEX1")
motor_RR = encoder_motor_class("M2", "INDEX1")
MOTORS = (motor_FL, motor_FR, motor_RL, motor_RR)
SIGNS = (-1, 1, -1, 1)


# ---------------- sensors ----------------
# The only place that reads measurement hardware. If mBlock uses other names,
# drag the equivalent block, check the generated Python and change it only here.
def read_gyro_z():
    # angular speed around the vertical axis, degrees/s
    return novapi.get_gyroscope("z")


def read_accel(axis):
    return novapi.get_acceleration(axis)


def read_motor_angle(motor):
    # accumulated encoder degrees
    return motor.get_value("angle")


try:
    _ticks_ms = time.ticks_ms
    def now():
        return _ticks_ms() / 1000.0
except AttributeError:
    def now():
        return time.time()


def normalize(degrees):
    # wraps an angle to [-180, 180)
    return (degrees + 180) % 360 - 180


def clamp(value, low, high):
    return max(low, min(high, value))


def to_robot_frame(forward, right, front):
    # Rotates a (forward, right) command given for a front (F_INTAKE, F_GRIPPER, ...)
    # into the robot frame. Returns (robot_forward, robot_right).
    a = math.radians(front)
    c = round(math.cos(a), 12)
    s = round(math.sin(a), 12)
    return forward * c - right * s, forward * s + right * c


# ---------------- kinematics ----------------
def mecanum_mix(vy, vx, w):
    # vy: forward (+) / backward (-), vx: right (+) / left (-), w: clockwise turn (+)
    # Output order: FL, FR, RL, RR
    return (vy + vx + w,
            vy - vx - w,
            vy - vx + w,
            vy + vx - w)


def mecanum_unmix(fl, fr, rl, rr):
    # inverse of mecanum_mix: wheel travel -> (forward, right, turn)
    return ((fl + fr + rl + rr) / 4.0,
            (fl - fr - rl + rr) / 4.0,
            (fl - fr + rl - rr) / 4.0)


def set_wheel_speeds(speeds):
    largest = max(abs(v) for v in speeds)
    scale = MAX_SPEED / largest if largest > MAX_SPEED else 1
    for motor, sign, v in zip(MOTORS, SIGNS, speeds):
        motor.set_speed(sign * v * scale)


def stop():
    for motor in MOTORS:
        motor.set_speed(0)


# ---------------- odometry ----------------
class Odometry:
    # Field position (cm) and heading (degrees, clockwise +) relative to where reset() was called.
    # x: right of the initial robot forward axis, y: forward of it.
    # Distance: encoders. Heading: gyroscope (unaffected by wheel slip).
    # The robot turns about the wheel center, which is tracked internally (_wx, _wy);
    # x and y report the footprint center, ODOM_CENTER_OFFSET_CM ahead of it.

    def __init__(self):
        self.gyro_bias = 0.0
        self.impact = False
        self.vibration = 0.0     # high-frequency acceleration level, see VIB_* constants
        self._accel_base = None
        self.reset()

    def calibrate(self, seconds=1.0):
        # The robot must be STILL. Measures gyroscope drift to subtract it later.
        if not USE_SENSORS:
            return
        total = 0.0
        n = 0
        end = now() + seconds
        while now() < end:
            total += read_gyro_z()
            n += 1
            time.sleep(PERIOD)
        self.gyro_bias = total / n if n else 0.0

    @property
    def x(self):
        return self._wx + ODOM_CENTER_OFFSET_CM * math.sin(math.radians(self.heading))

    @property
    def y(self):
        return self._wy + ODOM_CENTER_OFFSET_CM * math.cos(math.radians(self.heading))

    def reset(self, x=0.0, y=0.0, heading=0.0):
        # x, y: footprint center
        self.heading = heading
        self._wx = x - ODOM_CENTER_OFFSET_CM * math.sin(math.radians(heading))
        self._wy = y - ODOM_CENTER_OFFSET_CM * math.cos(math.radians(heading))
        self.angles = [read_motor_angle(m) for m in MOTORS] if USE_SENSORS else None
        self.t = now()

    def _translate(self, forward_cm, right_cm, heading):
        r = math.radians(heading)
        self._wx += right_cm * math.cos(r) + forward_cm * math.sin(r)
        self._wy += -right_cm * math.sin(r) + forward_cm * math.cos(r)

    def add_commanded(self, forward_cm, right_cm, turn_degrees):
        # Mechanical mode: assume the robot did exactly what it was told (robot frame)
        self._translate(forward_cm, right_cm, self.heading)
        self.heading += turn_degrees

    def update(self):
        if not USE_SENSORS:
            return
        t = now()
        dt = t - self.t
        self.t = t

        w = (read_gyro_z() - self.gyro_bias) * GYRO_SIGN
        if abs(w) < GYRO_DEADZONE:
            w = 0
        previous_heading = self.heading
        self.heading += w * dt

        angles = [read_motor_angle(m) for m in MOTORS]
        cm = [s * (a - a0) / DEGREES_PER_CM for s, a, a0 in zip(SIGNS, angles, self.angles)]
        self.angles = angles
        forward, right, _ = mecanum_unmix(*cm)
        right /= STRAFE_FACTOR

        # project onto the field using the mid-cycle heading
        self._translate(forward, right, (previous_heading + self.heading) / 2)

        ax = read_accel("x")
        ay = read_accel("y")
        if math.sqrt(ax * ax + ay * ay) > IMPACT_THRESHOLD:
            self.impact = True
        self._update_vibration(ax, ay, dt)

    def _update_vibration(self, ax, ay, dt):
        # Splits acceleration into slow (robot motion, gravity from tilt) and fast (vibration),
        # then keeps a smoothed level of the fast part.
        if self._accel_base is None or dt <= 0:
            self._accel_base = [ax, ay]
            return
        k = dt / (VIB_BASE_TAU + dt)
        self._accel_base[0] += k * (ax - self._accel_base[0])
        self._accel_base[1] += k * (ay - self._accel_base[1])
        hx = ax - self._accel_base[0]
        hy = ay - self._accel_base[1]
        k = dt / (VIB_ENVELOPE_TAU + dt)
        self.vibration += k * (math.sqrt(hx * hx + hy * hy) - self.vibration)


odo = Odometry()


# ---------------- S-curve smoothing ----------------
class SCurve:
    # Jerk-limited follower: the output reaches the target with an S-shaped velocity profile.
    # Speeding up uses accel/jerk, slowing down (toward 0 or reversing) uses decel/decel_jerk.

    def __init__(self, accel, jerk, decel=None, decel_jerk=None):
        self.accel = accel
        self.jerk = jerk
        self.decel = decel or accel
        self.decel_jerk = decel_jerk or jerk
        self.reset()

    def reset(self, value=0.0):
        self.value = value
        self.rate = 0.0

    def update(self, target, dt, scale=1.0):
        # scale multiplies the acceleration and jerk limits for this cycle
        error = target - self.value
        if error == 0 and self.rate == 0:
            return self.value
        slowing = abs(target) < abs(self.value) or target * self.value < 0
        a_max = (self.decel if slowing else self.accel) * scale
        j_max = (self.decel_jerk if slowing else self.jerk) * scale
        # largest rate that can still fade to 0 exactly at the target
        desired = math.copysign(min(a_max, math.sqrt(2 * j_max * abs(error))), error)
        self.rate += clamp(desired - self.rate, -j_max * dt, j_max * dt)
        step = self.rate * dt
        if abs(step) >= abs(error) and step * error >= 0:
            self.value = target
            self.rate = 0.0
        else:
            self.value += step
        return self.value


# ---------------- manual mode ----------------
_held_heading = None
_smooth_vy = SCurve(ACCEL, JERK, DECEL, DECEL_JERK)
_smooth_vx = SCurve(ACCEL, JERK, DECEL, DECEL_JERK)
_smooth_w = SCurve(TURN_ACCEL, TURN_JERK)
_last_drive_time = None


def apply_deadzone(value):
    return 0 if abs(value) < DEADZONE else value


def smoothing_scale():
    # Multiplier for the S-curve limits: high near standstill, low near top speed,
    # and lower still if the accelerometer reports vibration.
    if not ADAPTIVE_SMOOTHING:
        return 1.0
    speed = max(math.sqrt(_smooth_vy.value ** 2 + _smooth_vx.value ** 2), abs(_smooth_w.value))
    fraction = clamp(speed / MAX_SPEED, 0, 1)
    scale = LOW_SPEED_SCALE + (HIGH_SPEED_SCALE - LOW_SPEED_SCALE) * fraction
    if USE_SENSORS:
        excess = clamp((odo.vibration - VIB_OK) / (VIB_MAX - VIB_OK), 0, 1)
        scale *= 1 - (1 - VIB_MIN_SCALE) * excess
    return scale


def reset_smoothing():
    # Call when entering manual mode so it does not start from stale values
    global _last_drive_time
    for s in (_smooth_vy, _smooth_vx, _smooth_w):
        s.reset()
    _last_drive_time = None


def joystick_drive(front, hold_heading=True):
    # front = F_INTAKE, F_GRIPPER, F_LAUNCHER or F_REAR. The front rotates forward and strafe
    # (stick up drives toward that side), never the turn
    # (with SMOOTHING the reversal is gradual too).
    # With hold_heading, once the turn has settled the gyroscope corrects drift (bumps, slipping wheels).
    global _held_heading, _last_drive_time
    odo.update()
    vy, vx = to_robot_frame(apply_deadzone(gamepad.get_joystick("Ly")),
                            apply_deadzone(gamepad.get_joystick("Lx")), front)
    w = apply_deadzone(gamepad.get_joystick("Rx"))

    if SMOOTHING:
        t = now()
        # cap dt so a long pause does not produce a jump
        dt = PERIOD if _last_drive_time is None else clamp(t - _last_drive_time, 0.001, 0.05)
        _last_drive_time = t
        scale = smoothing_scale()
        vy = _smooth_vy.update(vy, dt, scale)
        vx = _smooth_vx.update(vx, dt, scale)
        w = _smooth_w.update(w, dt, scale)

    turning = abs(w) > 1
    moving = abs(vx) > 1 or abs(vy) > 1
    if not USE_SENSORS or not hold_heading or turning or not moving:
        _held_heading = odo.heading
    else:
        w = clamp(KP_HEADING * normalize(_held_heading - odo.heading), -30, 30)
    set_wheel_speeds(mecanum_mix(vy, vx, w))


# ---------------- closed-loop autonomous ----------------
def _ramp(current, target):
    return current + clamp(target - current, -RAMP, RAMP)


def drive(forward_cm=0, right_cm=0, front=F_INTAKE, speed=AUTO_SPEED, timeout=5.0):
    # Straight move (diagonals included) holding heading with the gyroscope.
    # Ends on arrival, on collision or on timeout. Returns True if it arrived.
    if not USE_SENSORS:
        return move_open_loop(forward_cm, right_cm, 0, front, speed)
    odo.update()
    heading = odo.heading
    r = math.radians(heading)
    forward_cm, right_cm = to_robot_frame(forward_cm, right_cm, front)
    target_x = odo.x + right_cm * math.cos(r) + forward_cm * math.sin(r)
    target_y = odo.y - right_cm * math.sin(r) + forward_cm * math.cos(r)

    odo.impact = False
    vy = vx = 0.0
    end = now() + timeout
    arrived = False
    while now() < end and not odo.impact:
        odo.update()
        ex = target_x - odo.x
        ey = target_y - odo.y
        dist = math.sqrt(ex * ex + ey * ey)
        if dist < TOL_CM:
            arrived = True
            break
        # error in the robot frame
        rr = math.radians(odo.heading)
        e_forward = ex * math.sin(rr) + ey * math.cos(rr)
        e_right = ex * math.cos(rr) - ey * math.sin(rr)
        magnitude = clamp(KP_DIST * dist, MIN_SPEED, speed)
        vy = _ramp(vy, magnitude * e_forward / dist)
        vx = _ramp(vx, magnitude * e_right / dist * STRAFE_FACTOR)
        w = clamp(KP_HEADING * normalize(heading - odo.heading), -30, 30)
        set_wheel_speeds(mecanum_mix(vy, vx, w))
        time.sleep(PERIOD)
    stop()
    return arrived


def turn_to(target_heading, speed=AUTO_SPEED, timeout=3.0):
    # Turns to an absolute heading (degrees, clockwise +, 0 = heading when odometry was reset).
    if not USE_SENSORS:
        return move_open_loop(turn_degrees=normalize(target_heading - odo.heading), speed=speed)
    w = 0.0
    end = now() + timeout
    arrived = False
    while now() < end:
        odo.update()
        error = normalize(target_heading - odo.heading)
        if abs(error) < TOL_DEGREES:
            arrived = True
            break
        target = clamp(KP_TURN * error, -speed, speed)
        if abs(target) < MIN_SPEED:
            target = math.copysign(MIN_SPEED, target)
        w = _ramp(w, target)
        set_wheel_speeds(mecanum_mix(0, 0, w))
        time.sleep(PERIOD)
    stop()
    return arrived


def turn(degrees, timeout=3.0):
    # relative: degrees > 0 clockwise, < 0 counterclockwise
    odo.update()
    return turn_to(odo.heading + degrees, timeout=timeout)


def forward(cm, front=F_INTAKE):
    return drive(forward_cm=cm, front=front)


def backward(cm, front=F_INTAKE):
    return drive(forward_cm=-cm, front=front)


def right(cm, front=F_INTAKE):
    return drive(right_cm=cm, front=front)


def left(cm, front=F_INTAKE):
    return drive(right_cm=-cm, front=front)


# ---------------- sensorless fallback (open loop, previous version) ----------------
def move_open_loop(forward_cm=0, right_cm=0, turn_degrees=0, front=F_INTAKE, speed=AUTO_SPEED):
    # Mechanical parameters only. Used automatically when USE_SENSORS = False.
    forward_cm, right_cm = to_robot_frame(forward_cm, right_cm, front)
    wheel_cm = mecanum_mix(forward_cm,
                           right_cm * STRAFE_FACTOR,
                           turn_degrees * CM_PER_TURN_DEGREE)
    degrees = [cm * DEGREES_PER_CM for cm in wheel_cm]
    largest = max(abs(d) for d in degrees)
    if largest == 0:
        return True
    for motor, sign, d in zip(MOTORS, SIGNS, degrees):
        motor.move(sign * d, speed * abs(d) / largest)
    # move() does not block: wait the theoretical time (RPM * 6 = degrees/s) + margin
    time.sleep(largest / (speed * 6.0) + 0.15)
    odo.add_commanded(forward_cm, right_cm, turn_degrees)
    return True


# ---------------- usage ----------------
# On power-up (robot still, before N1):
#     odo.calibrate()
#     odo.reset()
# Autonomous (front defaults to F_INTAKE, the robot forward axis):
#     forward(60); forward(20, F_GRIPPER); turn(90); right(30); turn_to(0)
# Manual (inside while True):
#     joystick_drive(F_INTAKE)   # or F_GRIPPER ("+"), F_LAUNCHER ("≡"), F_REAR
