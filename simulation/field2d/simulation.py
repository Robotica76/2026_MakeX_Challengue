"""Steps the robot pose from the motor speeds an mBlock program commands.

States: idle -> running -> one of finished-by-time-limit, out_of_bounds, error,
stopped. The program thread keeps the last commanded speeds after it returns
(like the real robot, motors keep turning), so the run ends on the time limit,
leaving the field, or Stop.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import field_layout as fl
from kinematics import DriveTrain, body_velocity, integrate
from mblock_runtime import MotorBus, ProgramRunner, SimClock
from robot import RobotConfig, RobotPose

SUBSTEP_S = 1 / 240          # integration step
AUTO_STAGE_S = 30.0          # rules p.52: automatic stage lasts 30 s
MAX_FRAME_S = 0.1            # clamp long frames (e.g. while a file dialog is open)


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
                 time_limit: float = AUTO_STAGE_S):
        self.cfg, self.start_pose, self.drive = cfg, start, drive
        self.time_limit = time_limit  # 0 = no limit
        self.program: Optional[Path] = None
        self.pose = start
        self.state = SimState()
        self.clock = SimClock()
        self.motors = MotorBus(drive.max_rpm)
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
        self.state = SimState()

    def run(self) -> None:
        if self.program is None:
            self._end("error", "Load a program first")
            return
        self.reset()
        self._runner = ProgramRunner(self.program, self.clock, self.motors)
        try:
            self._runner.start()
        except SyntaxError as exc:
            self._runner = None
            self._end("error", f"SyntaxError: {exc.msg} (line {exc.lineno})")
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
            vx, vy, omega = body_velocity(self.cfg, self.drive.wheel_rpms(self.motors.snapshot()))
            self.pose = integrate(self.pose, vx, vy, omega, dt)
            self.clock.advance(dt)
            self._check()
        if self.running and self.state.trail[-1] != (self.pose.x, self.pose.y):
            self.state.trail.append((self.pose.x, self.pose.y))

    def _check(self) -> None:
        if out_of_bounds(self.cfg, self.pose):
            self._end("out_of_bounds", f"Out of boundaries at t = {self.time:.2f} s "
                                       f"(x {self.pose.x:.0f}, y {self.pose.y:.0f} mm)")
        elif self._runner and self._runner.error:
            self._end("error", self._runner.error)
        elif self.time_limit and self.time >= self.time_limit - 1e-9:
            self._end("done", f"Time limit reached ({self.time_limit:g} s)")

    def _end(self, status: str, message: str) -> None:
        self._stop_runner()
        trail = self.state.trail + [(self.pose.x, self.pose.y)]
        self.state = SimState(status, message, trail)

    def _stop_runner(self) -> None:
        if self._runner:
            self._runner.stop()
            self._runner = None
