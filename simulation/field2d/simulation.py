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
from ball_physics import BallWorld, load_ball_path
from balls import Ball, Intake, field_balls
from kinematics import DriveTrain, body_velocity, integrate
from ball_physics import named_colliders
from fortress import FortressMotion
from match import ChannelMonitor, CollisionMonitor, HalfMonitor, MatchMonitor
from mechanisms import Mechanisms
from props import Gripper, Prop, field_props, push_props, rake_props
import referee
from flag import load_flag
from mblock_runtime import DCBus, GamepadInput, MotorBus, ProgramRunner, Sensors, ServoBus, SimClock
from robot import DEFAULT_CONFIG, RobotConfig, RobotPose
from uncertainty import Variation

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
                 gamepad: Optional[GamepadInput] = None, variation: Optional[Variation] = None,
                 ball_scenario: str = "none", intake: Optional[Intake] = None,
                 mechanisms: Optional[Mechanisms] = None, gripper: Optional[Gripper] = None):
        self.cfg, self.start_pose, self.drive = cfg, start, drive
        self.ball_scenario, self.intake = ball_scenario, intake   # see balls.py
        self.balls: List[Ball] = field_balls(fl.build_field(), ball_scenario)
        self.dc = DCBus()                          # power expansion board ports (intake, ...)
        self.mechanisms = mechanisms or Mechanisms()  # elevator, intake lift, rollers (mechanisms.py)
        self.gripper = gripper                     # props.py: takes bonus cubes, cones, letter cubes
        self.elements = fl.build_field()
        self.props: List[Prop] = field_props(self.elements) if ball_scenario != "none" else []
        self._path_data = json.loads(DEFAULT_CONFIG.read_text()).get("ball_path")
        self.world = self._new_world()
        self.monitor = self._new_monitor()
        self.collisions = self._new_collisions()
        self.variation = variation or Variation()  # ideal robot unless a study passes one
        self.marks: List[dict] = []                # simtrace.mark() records, see Monte Carlo
        self.trace_options: dict = {}              # simtrace.options() for the program
        self.max_frame_s = MAX_FRAME_S             # longest frame simulated in one step (viewers)
        self.time_limit = time_limit  # 0 = no limit
        self.gyro_sign = gyro_sign
        self.gamepad = gamepad or GamepadInput()
        self.program: Optional[Path] = None
        self.pose = start
        self.state = SimState()
        self.clock = SimClock()
        self.motors = self._new_motors()
        self.sensors = Sensors()
        self.bonus_judged = None                   # referee.manual_stage_start() at 30 s
        self.modification = None                   # referee.modification_stage() at 130 s
        self.flag = load_flag(cfg.alliance, elements=self.elements)
        self.half = self._new_half()
        self.channels = self._new_channels()
        self.servos = ServoBus()                   # smart servos (angles), mbuild.smartservo
        self._ranging = json.loads(DEFAULT_CONFIG.read_text()).get("ranging_sensors", {})
        self._colliders = [box for _, box in named_colliders(self.elements)]
        self.prop_jams: List[str] = []             # props the robot presses against a structure
        self.fortresses = FortressMotion.for_elements(self.elements)   # fortress.py: pushed on its casters
        self._gripper_slot = tuple(json.loads(DEFAULT_CONFIG.read_text()).get("gripper", {}).get(
            "slot_mm", (0, 0, 0, 0, 0, 0)))          # free space between the jaws (robot frame)
        self._gyro_drift = 0.0
        self._velocity = (0.0, 0.0, 0.0)   # robot frame vx, vy (mm/s), omega (rad/s)
        self._accel = (0.0, 0.0)           # low-passed, m/s^2
        self._runner: Optional[ProgramRunner] = None
        self.referee_balls = True                  # False: a second robot; the host's referee releases the balls
        self.linked: List["Simulation"] = []       # robots on the same field (analysis/two_robots.py)

    @property
    def running(self) -> bool:
        return self.state.status == "running"

    @property
    def time(self) -> float:
        return self.clock.now

    @property
    def balls_collected(self) -> int:
        if self.world:
            return self.world.captured
        return len(self.intake.collected) if self.intake else 0

    def _new_monitor(self) -> MatchMonitor:
        """Rule monitors (match.py): R19 at the end of the automatic stage, R06 boundary."""
        data = self._path_data or {}
        bx0, by0, _, bx1, by1, _ = data.get("body_box_mm", (-self.cfg.length_mm / 2, -self.cfg.width_mm / 2, 0.0,
                                                           self.cfg.length_mm / 2, self.cfg.width_mm / 2, 642.0))
        return MatchMonitor(self.cfg.alliance, (bx0, by0, bx1, by1))

    def _new_half(self) -> Optional[HalfMonitor]:
        """Own half of the alliance area (two robots per alliance), robot_config.json "own_half"."""
        spec = json.loads(DEFAULT_CONFIG.read_text()).get("own_half")
        if not spec:
            return None
        data = self._path_data or {}
        bx0, by0, _, bx1, by1, _ = data.get("body_box_mm", (-self.cfg.length_mm / 2, -self.cfg.width_mm / 2, 0.0,
                                                           self.cfg.length_mm / 2, self.cfg.width_mm / 2, 642.0))
        return HalfMonitor(spec.get("half", "lower"), (bx0, by0, bx1, by1))

    def _new_channels(self) -> ChannelMonitor:
        """R26: robot parts inside a strategy-area channel."""
        data = self._path_data or {}
        bands = [tuple(b) for b in data.get("body_bands_mm", [])]
        slots = [(el.name, *el.bounds()) for el in self.elements if el.kind == "slot"]
        return ChannelMonitor(slots, bands)

    def _new_collisions(self) -> CollisionMonitor:
        """Robot body and intake head against the field structures (match.py)."""
        data = self._path_data or {}
        body = [tuple(b) for b in data.get("body_bands_mm", [data.get(
            "body_box_mm", (-self.cfg.length_mm / 2, -self.cfg.width_mm / 2, 0.0,
                            self.cfg.length_mm / 2, self.cfg.width_mm / 2, 642.0))])]
        head = tuple(data.get("head_box_mm", (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)))
        slot = json.loads(DEFAULT_CONFIG.read_text()).get("gripper", {}).get("slot_mm")
        return CollisionMonitor(named_colliders(self.elements), body, head, tuple(slot) if slot else None)

    def _new_world(self) -> Optional[BallWorld]:
        """Ball dynamics and the ball path through the robot (ball_physics.py), when
        there are balls."""
        if not self.balls:
            return None
        data = self._path_data or {}
        body = tuple(data.get("body_box_mm", (-self.cfg.length_mm / 2, -self.cfg.width_mm / 2, 0.0,
                                              self.cfg.length_mm / 2, self.cfg.width_mm / 2, 642.0)))
        head = tuple(data.get("head_box_mm", (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)))
        return BallWorld(self.elements, self.balls, self.intake, load_ball_path(data), body, head)

    def reset(self, cfg: Optional[RobotConfig] = None, start: Optional[RobotPose] = None) -> None:
        """Stop any run and put the robot back on its start pose."""
        self._stop_runner()
        if cfg is not None:
            self.cfg = cfg
        if start is not None:
            self.start_pose = start
        self.pose = self.start_pose
        self.clock = SimClock()
        self.elements = fl.build_field()                 # fortresses back where they start
        self._colliders = [box for _, box in named_colliders(self.elements)]
        self.fortresses = FortressMotion.for_elements(self.elements)
        self.motors = self._new_motors()
        self.sensors = Sensors()
        self.bonus_judged = None
        self.modification = None
        self.flag = load_flag(self.cfg.alliance, elements=self.elements)
        self.half = self._new_half()
        self.channels = self._new_channels()
        self.servos = ServoBus()
        self.dc = DCBus()
        self.mechanisms.reset()
        self.balls = field_balls(fl.build_field(), self.ball_scenario)
        self.props = field_props(self.elements) if self.ball_scenario != "none" else []
        if self.gripper:
            self.gripper.held = None
        if self.intake:
            self.intake.reset()
        self.world = self._new_world()
        self.monitor = self._new_monitor()
        self.collisions = self._new_collisions()
        self._velocity, self._accel = (0.0, 0.0, 0.0), (0.0, 0.0)
        self._gyro_drift = 0.0
        self.marks = []
        self.state = SimState()

    def run(self) -> None:
        if self.program is None:
            self._end("error", "Load a program first")
            return
        self.reset()
        self._runner = ProgramRunner(self.program, self.clock, self.motors, self.sensors, self.gamepad,
                                     MODULE_ROOTS, self.variation, self._record_mark, self.trace_options,
                                     self.dc, self.servos)
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
        remaining = min(frame_s, self.max_frame_s)
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
            var = self.variation
            vx, vy, omega = body_velocity(self.cfg, self.drive.wheel_rpms(rpms), var.wheel_scale)
            vx, vy, omega = vx * var.slip_forward, vy * var.slip_strafe, omega * var.slip_turn
            self.pose = integrate(self.pose, vx, vy, omega, dt)
            self.mechanisms.step(self.dc, dt)
            self.servos.integrate(dt)
            if self.world:
                self.world.step(dt, self.pose, (vx, vy, omega), self.mechanisms.position("intake_lift"), self.dc)
            elif self.intake:
                self.intake.update(self.pose, self.balls, self.dc.power(self.intake.port),
                                   self.mechanisms.position("intake_lift"))
            self._update_sensors(vx, vy, omega, dt)
            if self.props and self.intake:
                head = (self._path_data or {}).get("head_box_mm", (0, 0, 46.0, 0, 0, 145.0))
                rake_props(self.pose, self.mechanisms.position("intake_lift"), self.intake.pulling(self.dc),
                           self.props, self.elements, dt, self.intake, (head[2], head[5]), owner=id(self))
            if self._path_data:
                lift = self.mechanisms.position("intake_lift")
                hx0, hy0, hz0, hx1, hy1, hz1 = self._path_data.get("head_box_mm", (0, 0, 0, 0, 0, 0))
                parts = [tuple(b) for b in self._path_data.get("body_bands_mm", [])] + \
                        [(hx0, hy0, hz0 + lift, hx1, hy1, hz1 + lift)]
                if self.fortresses.update(self.clock.now, dt, self.pose, parts, self.elements, self.props,
                                          self.balls):
                    self._fortress_moved()
            if self.props and self._path_data:
                lift = self.mechanisms.position("intake_lift")
                hx0, hy0, hz0, hx1, hy1, hz1 = self._path_data.get("head_box_mm", (0, 0, 0, 0, 0, 0))
                parts = [tuple(b) for b in self._path_data.get("body_bands_mm", [])] + \
                        [(hx0, hy0, hz0 + lift, hx1, hy1, hz1 + lift)]
                car = self.mechanisms.position("elevator")
                ox0, oy0, oz0, ox1, oy1, oz1 = self._gripper_slot
                slot = [(ox0, oy0, oz0, ox1, oy1, oz1 + car),
                        # intake mouth: a prop under the head (the roller rides on it) is not pushed
                        (self.intake.body_front_mm, hy0, 0.0, 300.0, hy1, hz0 + lift + 40.0) if self.intake
                        else (0, 0, 0, 0, 0, 0)]
                self.prop_jams = push_props(self.pose, parts, self.props, self.elements, self._colliders, slot)
            if self.gripper and self.props:
                self.gripper.update(self.pose, self.mechanisms.position("elevator"),
                                    self.mechanisms.position("gripper_jaw"), self.props, self.elements)
            mech_moving = any(abs(self.dc.power(m.port)) >= 5 for m in self.mechanisms.linear.values())
            self.monitor.update(self.clock.now, dt, self.pose, (vx, vy, omega), mech_moving)
            in_play = not (referee.MODIFICATION_START_S <= self.clock.now < referee.FINAL_START_S)
            if in_play:
                self.collisions.update(self.clock.now, self.pose, self.mechanisms.position("intake_lift"),
                                       self.mechanisms.position("elevator"))
                if self.half:
                    self.half.update(self.clock.now, dt, self.pose)
                hx0, hy0, hz0, hx1, hy1, hz1 = (self._path_data or {}).get("head_box_mm", (0, 0, 0, 0, 0, 0))
                lift = self.mechanisms.position("intake_lift")
                self.channels.update(self.clock.now, self.pose, (hx0, hy0, hz0 + lift, hx1, hy1, hz1 + lift))
            if self.flag:
                self.flag.update(self.clock.now, self.pose, self.mechanisms.position("elevator"))
            self.clock.advance(dt)
            self._referee()
            self._check()
        if self.running and self.state.trail[-1] != (self.pose.x, self.pose.y):
            self.state.trail.append((self.pose.x, self.pose.y))

    def ranging_cm(self, spec: dict) -> float:
        """Distance (cm) a ranging sensor reads: robot_config.json "ranging_sensors" gives each
        port {"position_mm": [x fwd, y left, z], "direction_deg": yaw in the robot frame (0 =
        forward)} or "direction": "down". Horizontal rays hit the field structures at the
        sensor height and the field frame; 200 cm when nothing is in range (estimate)."""
        x, y, z = spec.get("position_mm", (0.0, 0.0, 100.0))
        if spec.get("direction") == "down":
            return min(Sensors.RANGE_NONE_CM, z / 10.0)
        ox, oy = self.pose.to_field(x, y)
        a = self.pose.theta + math.radians(spec.get("direction_deg", 0.0))
        dx, dy = math.cos(a), math.sin(a)
        best = 2000.0
        boxes = self._colliders + [(-1e4, -1e4, -1, 0.0, 1e4, 1e4), (fl.FIELD_W, -1e4, -1, 1e4, 1e4, 1e4),
                                   (-1e4, -1e4, -1, 1e4, 0.0, 1e4), (-1e4, fl.FIELD_H, -1, 1e4, 1e4, 1e4)]
        for bx0, by0, bz0, bx1, by1, bz1 in boxes:
            if not bz0 <= z <= bz1:
                continue
            t0, t1 = 0.0, best
            for o, d, lo, hi in ((ox, dx, bx0, bx1), (oy, dy, by0, by1)):
                if abs(d) < 1e-12:
                    if not lo <= o <= hi:
                        t0, t1 = 1.0, 0.0
                    continue
                ta, tb = sorted(((lo - o) / d, (hi - o) / d))
                t0, t1 = max(t0, ta), min(t1, tb)
            if t0 <= t1:
                best = t0
        return Sensors.RANGE_NONE_CM if best >= 2000.0 else best / 10.0

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
        self.sensors.set(self._gyro_reading(omega, dt), *self._accel, dt)
        if self._ranging:
            self.sensors.set_ranging({port: self.ranging_cm(spec) for port, spec in self._ranging.items()})

    def _gyro_reading(self, omega: float, dt: float) -> float:
        """True yaw rate in the configured sign, plus the Variation's gyro errors."""
        var = self.variation
        rate = self.gyro_sign * math.degrees(omega) * (1.0 + var.gyro_scale)
        if var.gyro_drift_dps:
            self._gyro_drift += var.sim_rng.gauss(0.0, var.gyro_drift_dps * math.sqrt(dt))
        noise = var.sim_rng.gauss(0.0, var.gyro_noise_dps) if var.gyro_noise_dps else 0.0
        return rate + var.gyro_bias_dps + self._gyro_drift + noise

    def _new_motors(self) -> MotorBus:
        var = self.variation
        return MotorBus(self.drive.max_rpm, var.motor_gain, var.motor_tau_s, var.encoder_res_deg)

    def _record_mark(self, label: str, info: dict) -> None:
        """simtrace.mark() from the program thread; the sim is paused meanwhile (lockstep)."""
        p = self.pose
        self.marks.append({"label": label, "t": self.clock.now, "x": p.x, "y": p.y, "theta": p.theta, **info})

    def _fortress_moved(self) -> None:
        """A fortress moved (fortress.py): the structure boxes every model uses follow it (also in
        the robots on the same field)."""
        for sim in [self] + self.linked:
            sim._refresh_structures()

    def _refresh_structures(self) -> None:
        named = named_colliders(self.elements)
        self._colliders = [box for _, box in named]
        self.collisions.colliders = named
        if self.world:
            self.world.set_elements(self.elements)

    def _referee(self) -> None:
        """Manual stage start (30 s) in runs that go past the automatic stage: bonus exchange,
        own resource balls released (referee.py)."""
        if (self.bonus_judged is None and self.referee_balls and self.world and self.ball_scenario == "initial"
                and (not self.time_limit or self.time_limit > referee.MANUAL_START_S)
                and self.clock.now >= referee.MANUAL_START_S - 1e-9):
            self.bonus_judged = referee.manual_stage_start(self)
        if (self.modification is None and (not self.time_limit or self.time_limit > referee.MODIFICATION_START_S)
                and self.clock.now >= referee.MODIFICATION_START_S - 1e-9):
            self.modification = referee.modification_stage(self)

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
