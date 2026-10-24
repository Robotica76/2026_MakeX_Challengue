"""Steps the robot pose from the motor speeds an mBlock program commands.

States: idle -> running -> one of finished-by-time-limit, out_of_bounds, error,
stopped. The program thread keeps the last commanded speeds after it returns
(like the real robot, motors keep turning), so the run ends on the time limit,
leaving the field, or Stop.

Each step also produces what the robot's sensors would read: encoder angles
(MotorBus), the gyroscope z rate and the accelerometer (Sensors). The gamepad
state (GamepadInput) outlives runs, like the Bluetooth link.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import field_layout as fl
from kinematics import DriveTrain, body_velocity, integrate
from mblock_runtime import GamepadInput, MotorBus, ProgramRunner, Sensors, SimClock
from robot import DEFAULT_CONFIG, RobotConfig, RobotPose

SUBSTEP_S = 1 / 240          # integration step
AUTO_STAGE_S = 30.0          # rules p.52: automatic stage lasts 30 s
MAX_FRAME_S = 0.1            # clamp long frames (e.g. while a file dialog is open)
REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_ROOTS = (REPO_ROOT / "software",)  # where `import chassis` & co. are found
ACCEL_TAU_S = 0.02           # low-pass on the accelerometer: ideal wheels change speed instantly
GRAVITY = 9.81


def load_gyro_sign(path: Path = DEFAULT_CONFIG) -> int:
    """Multiplier from the simulator's CCW-positive yaw rate to the gyro reading.

    robot_config.json "sensors": {"gyro_z_positive": "clockwise" | "counterclockwise"}.
    """
    data = json.loads(Path(path).read_text()).get("sensors", {})
    direction = data.get("gyro_z_positive", "counterclockwise")
    if direction not in ("clockwise", "counterclockwise"):
        raise ValueError('sensors.gyro_z_positive must be "clockwise" or "counterclockwise"')
    return -1 if direction == "clockwise" else 1


@dataclass
class SimState:
    status: str = "idle"     # idle | running | done | out_of_bounds | error | stopped
    message: str = ""
    trail: List[Tuple[float, float]] = field(default_factory=list)


def out_of_bounds(cfg: RobotConfig, pose: RobotPose) -> bool:
    """True when any footprint corner leaves the field (rules p.10: 4655 x 3055 mm)."""
    return any(not (0 <= x <= fl.FIELD_W and 0 <= y <= fl.FIELD_H) for x, y in pose.corners(cfg))


class Simulation:
    def __init__(self, cfg: RobotConfig, start: RobotPose, drive: DriveTrain,
                 time_limit: float = AUTO_STAGE_S, gyro_sign: int = 1,
                 gamepad: Optional[GamepadInput] = None):
        self.cfg, self.start_pose, self.drive = cfg, start, drive
        self.time_limit = time_limit  # 0 = no limit
        self.gyro_sign = gyro_sign
        self.gamepad = gamepad or GamepadInput()
        self.program: Optional[Path] = None
        self.pose = start
        self.state = SimState()
        self.clock = SimClock()
        self.motors = MotorBus(drive.max_rpm)
        self.sensors = Sensors()
        self._velocity = (0.0, 0.0, 0.0)   # robot frame vx, vy (mm/s), omega (rad/s)
        self._accel = (0.0, 0.0)           # low-passed, m/s^2
        self._runner: Optional[ProgramRunner] = None

    @property
    def running(self) -> bool:
        return self.state.status == "running"

    @property
    def time(self) -> float:
        return self.clock.now

    def reset(self, cfg: Optional[RobotConfig] = None, start: Optional[RobotPose] = None) -> None:
        """Stop any run and put the robot back on its start pose."""
        self._stop_runner()
        if cfg is not None:
            self.cfg = cfg
        if start is not None:
            self.start_pose = start
        self.pose = self.start_pose
        self.clock = SimClock()
        self.motors = MotorBus(self.drive.max_rpm)
        self.sensors = Sensors()
        self._velocity, self._accel = (0.0, 0.0, 0.0), (0.0, 0.0)
        self.state = SimState()

    def run(self) -> None:
        if self.program is None:
            self._end("error", "Load a program first")
            return
        self.reset()
        self._runner = ProgramRunner(self.program, self.clock, self.motors, self.sensors, self.gamepad,
                                     MODULE_ROOTS)
        try:
            self._runner.start()
        except SyntaxError as exc:
            self._runner = None
            self._end("error", f"SyntaxError: {exc.msg} (line {exc.lineno})")
            return
        except (OSError, UnicodeDecodeError) as exc:
            self._runner = None
            self._end("error", f"Cannot read {self.program.name}: {exc}")
            return
        self.state = SimState("running", f"Running {self.program.name}", [(self.pose.x, self.pose.y)])

    def stop(self) -> None:
        if self.running:
            self._end("stopped", f"Stopped at t = {self.time:.1f} s")

    def step(self, frame_s: float) -> None:
        """Advance by one viewer frame of wall time (real-time playback)."""
        if not self.running:
            return
        remaining = min(frame_s, MAX_FRAME_S)
        lockstep = True
        while remaining > 1e-9 and self.running:
            allowed = self.clock.sync() if lockstep else float("inf")
            if allowed <= 0:  # program did not block again in time: free-run this frame
                lockstep, allowed = False, float("inf")
            dt = min(SUBSTEP_S, remaining, allowed)
            if self.time_limit:
                dt = min(dt, self.time_limit - self.time)
            if dt <= 0:
                self._check()
                break
            remaining -= dt
            rpms = self.motors.integrate(dt)  # also advances encoders and move()
            vx, vy, omega = body_velocity(self.cfg, self.drive.wheel_rpms(rpms))
            self.pose = integrate(self.pose, vx, vy, omega, dt)
            self._update_sensors(vx, vy, omega, dt)
            self.clock.advance(dt)
            self._check()
        if self.running and self.state.trail[-1] != (self.pose.x, self.pose.y):
            self.state.trail.append((self.pose.x, self.pose.y))

    def _update_sensors(self, vx: float, vy: float, omega: float, dt: float) -> None:
        """Gyro z = yaw rate; accelerometer = d(v)/dt in the rotating robot frame
        plus the centripetal term, low-passed so ideal speed steps stay finite."""
        pvx, pvy, _ = self._velocity
        ax = ((vx - pvx) / dt - omega * vy) / 1000.0
        ay = ((vy - pvy) / dt + omega * vx) / 1000.0
        k = dt / (ACCEL_TAU_S + dt)
        fx, fy = self._accel
        self._accel = (fx + k * (ax - fx), fy + k * (ay - fy))
        self._velocity = (vx, vy, omega)
        self.sensors.set(self.gyro_sign * math.degrees(omega), *self._accel)

    def _check(self) -> None:
        if out_of_bounds(self.cfg, self.pose):
            self._end("out_of_bounds", f"Out of boundaries at t = {self.time:.2f} s "
                                       f"(x {self.pose.x:.0f}, y {self.pose.y:.0f} mm)")
        elif self._runner and self._runner.error:
            self._end("error", self._runner.error)
        elif self.time_limit and self.time >= self.time_limit - 1e-9:
            self._end("done", f"Time limit reached ({self.time_limit:g} s)")

    def _end(self, status: str, message: str) -> None:
        if not self._stop_runner():
            message += " (warning: the program thread is stuck in a long call and did not exit)"
        trail = self.state.trail + [(self.pose.x, self.pose.y)]
        self.state = SimState(status, message, trail)

    def _stop_runner(self) -> bool:
        """Stop and drop the runner; False if its thread is still alive."""
        stopped = True
        if self._runner:
            stopped = self._runner.stop()
            self._runner = None
        return stopped
