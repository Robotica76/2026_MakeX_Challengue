"""Robot state over UDP (JSON, one message per datagram) for external viewers or
bridges such as Unreal Engine or a ROS 2 node.

Default target: 127.0.0.1:5005, 30 messages per second. Message (schema v1):

    {
      "v": 1,
      "robot": "storm_breaker_v22",
      "t": 12.34,                      simulated time, s
      "status": "running",             idle | running | done | out_of_bounds | error | stopped
      "pose": {"x_mm": 1234.5, "y_mm": 567.8, "theta_deg": 90.0},
      "velocity": {"vx_mm_s": 0.0, "vy_mm_s": 0.0, "omega_deg_s": 0.0},
      "wheels": {"front_left": {"rpm": 0.0, "angle_deg": 0.0}, ...},
      "carriage_mm": 0.0,              elevator carriage above its lowest position
      "mast": false                    flag mast installed (Modification Stage)
    }

Frames: pose in the field frame (origin at the red-side field corner, x toward the
blue side, y across, mm, theta CCW from +x along the robot forward axis, i.e. the
intake side). velocity in the robot frame (x forward, y left, omega CCW).
Wheel rpm and angle are positive when the wheel rolls forward. A receiver can
place the CAD model (simulation/field3d/assets) with a heading of theta - 90 deg,
because the CAD forward axis is +y.
"""

import json
import math
import socket
from typing import Dict, Optional, Tuple

SCHEMA_VERSION = 1
DEFAULT_TARGET = ("127.0.0.1", 5005)
DEFAULT_RATE_HZ = 30.0


def parse_target(text: str) -> Tuple[str, int]:
    host, _, port = text.rpartition(":")
    if not host or not port.isdigit():
        raise ValueError(f"expected HOST:PORT, got {text!r}")
    return host, int(port)


def state_message(robot: str, t: float, status: str, pose, velocity: Tuple[float, float, float],
                  wheels: Dict[str, Tuple[float, float]], carriage_mm: float, mast: bool) -> dict:
    vx, vy, omega = velocity
    return {
        "v": SCHEMA_VERSION,
        "robot": robot,
        "t": round(t, 4),
        "status": status,
        "pose": {"x_mm": round(pose.x, 2), "y_mm": round(pose.y, 2),
                 "theta_deg": round(math.degrees(pose.theta), 3)},
        "velocity": {"vx_mm_s": round(vx, 2), "vy_mm_s": round(vy, 2),
                     "omega_deg_s": round(math.degrees(omega), 3)},
        "wheels": {name: {"rpm": round(rpm, 2), "angle_deg": round(angle, 2)}
                   for name, (rpm, angle) in wheels.items()},
        "carriage_mm": round(carriage_mm, 1),
        "mast": bool(mast),
    }


class StatePublisher:
    """Sends state messages at most rate_hz times per second; never blocks the viewer."""

    def __init__(self, target: Tuple[str, int] = DEFAULT_TARGET, rate_hz: float = DEFAULT_RATE_HZ):
        self.target = target
        self.period = 1.0 / rate_hz if rate_hz > 0 else 0.0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self._last: Optional[float] = None
        self.sent = 0

    def maybe_send(self, now: float, message: dict) -> bool:
        if self._last is not None and now - self._last < self.period:
            return False
        self._last = now
        try:
            self.sock.sendto(json.dumps(message, separators=(",", ":")).encode(), self.target)
        except OSError:
            return False   # nobody listening or network down: the viewer keeps running
        self.sent += 1
        return True

    def close(self) -> None:
        self.sock.close()
