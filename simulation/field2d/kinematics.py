"""Mecanum forward kinematics and the motor-port -> wheel mapping.

Wheel convention: a positive wheel speed drives that wheel forward (robot +x).
Rollers in the standard layout (ground-contact rollers form an "O" seen from
above, top rollers an "X"), so with wheel surface speeds v_fl, v_fr, v_rl, v_rr:

    vx    = ( v_fl + v_fr + v_rl + v_rr) / 4          (forward, mm/s)
    vy    = (-v_fl + v_fr + v_rl - v_rr) / 4          (left, mm/s)
    omega = (-v_fl + v_fr - v_rl + v_rr) / (4 (lx + ly))  (CCW, rad/s)

lx, ly are the distances from the robot centre to the wheel centres along x / y.
Ideal rolling, no slip, no motor dynamics: speeds change instantly.
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from robot import DEFAULT_CONFIG, RobotConfig, RobotPose, mecanum_wheels

WHEELS = ("front_left", "front_right", "rear_left", "rear_right")
FIELD_MOTOR_MAX_RPM = 580.0  # rules p.57: 180 smart encoder motor, no-load 580 RPM


@dataclass(frozen=True)
class MotorPort:
    wheel: str
    direction: int  # +1: positive speed drives the wheel forward, -1: mounted mirrored


@dataclass(frozen=True)
class DriveTrain:
    motors: Dict[str, MotorPort]  # port name ("M1") -> wheel
    gear_ratio: float = 1.0       # wheel rpm = motor rpm * gear_ratio
    max_rpm: float = FIELD_MOTOR_MAX_RPM

    def wheel_rpms(self, motor_rpms: Dict[str, float]) -> Dict[str, float]:
        """Wheel rpm (positive = forward) from commanded motor rpm per port."""
        wheels = {w: 0.0 for w in WHEELS}
        for port, rpm in motor_rpms.items():
            m = self.motors.get(port)
            if m is None:
                continue  # a port not wired to a drive wheel (e.g. a mechanism motor)
            rpm = max(-self.max_rpm, min(self.max_rpm, rpm))
            wheels[m.wheel] += m.direction * rpm * self.gear_ratio
        return wheels


def load_drive_train(path: Path = DEFAULT_CONFIG) -> DriveTrain:
    data = json.loads(Path(path).read_text()).get("drive_train", {})
    motors = {
        port: MotorPort(spec["wheel"], int(spec.get("direction", 1)))
        for port, spec in data.get("motors", {}).items()
    }
    for port, m in motors.items():
        if m.wheel not in WHEELS or m.direction not in (1, -1):
            raise ValueError(f"drive_train motor {port}: wheel must be one of {WHEELS}, direction +/-1")
    return DriveTrain(motors, float(data.get("gear_ratio", 1.0)),
                      float(data.get("max_rpm", FIELD_MOTOR_MAX_RPM)))


def body_velocity(cfg: RobotConfig, wheel_rpms: Dict[str, float],
                  wheel_scale: Optional[Dict[str, float]] = None) -> Tuple[float, float, float]:
    """(vx mm/s, vy mm/s, omega rad/s) in the robot frame. wheel_scale: real /
    nominal diameter per wheel (uncertainty studies); missing wheels are nominal."""
    circumference = math.pi * cfg.wheel_diameter_mm
    scale = wheel_scale or {}
    v = {w: rpm / 60.0 * circumference * scale.get(w, 1.0) for w, rpm in wheel_rpms.items()}
    lx, ly = (abs(c) for c in mecanum_wheels(cfg)[0].center)
    vx = (v["front_left"] + v["front_right"] + v["rear_left"] + v["rear_right"]) / 4
    vy = (-v["front_left"] + v["front_right"] + v["rear_left"] - v["rear_right"]) / 4
    omega = (-v["front_left"] + v["front_right"] - v["rear_left"] + v["rear_right"]) / (4 * (lx + ly))
    return vx, vy, omega


def integrate(pose: RobotPose, vx: float, vy: float, omega: float, dt: float) -> RobotPose:
    """Advance the pose by dt seconds (midpoint heading for the translation)."""
    mid = pose.theta + omega * dt / 2
    c, s = math.cos(mid), math.sin(mid)
    return RobotPose(pose.x + (vx * c - vy * s) * dt,
                     pose.y + (vx * s + vy * c) * dt,
                     (pose.theta + omega * dt) % (2 * math.pi))
