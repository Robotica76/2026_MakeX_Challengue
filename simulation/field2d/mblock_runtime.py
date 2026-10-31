"""Run mBlock-generated Python (novapi / mbuild) against the simulator.

The program runs unchanged in a worker thread. Its imports of `novapi`,
`mbuild.*` and `time` are swapped for stand-ins that drive the simulated robot:

- encoder_motor_class(port, index): set_speed(rpm), set_power(%), stop(),
  move(degrees, rpm), get_value("speed" | "angle").
- novapi.get_gyroscope(axis) (deg/s), novapi.get_acceleration(axis), timer(),
  reset_timer(); time.sleep / time / monotonic / ticks_ms follow the simulation
  clock, so sleeps take simulated time.
- mbuild.gamepad: get_joystick("Lx" | "Ly" | "Rx" | "Ry") in -100..100 and
  is_key_pressed(name), fed by the emulated gamepad window (GamepadInput).
- `import x` of a project file loads it with the same stand-ins: x.py next to the
  program first, then the module roots (the repository's software/ folder, searched
  recursively), so a simulation program in simulation/control can use
  software/controls/drivetrain/chassis.py exactly as the robot code does.

Anything else the program calls raises UnsupportedAPI, reported in the viewer,
so missing stand-ins are obvious instead of silently ignored.

Stop works even for loops that never call a simulated API (`while True: pass`)
or that catch everything (`except BaseException`): ProgramRunner.stop() injects
ProgramStopped into the program thread (CPython async exception) repeatedly
until the thread exits. Only a single long call into C code, which never returns
to the interpreter, can outlive Stop; stop() reports that case.
"""

import builtins
import ctypes
import math
import sys
import threading
import time
import traceback
import types
from pathlib import Path
from typing import Dict, Optional, Sequence


class UnsupportedAPI(Exception):
    """The program used an mBlock API the simulator does not provide yet."""


class ProgramStopped(BaseException):
    """Raised inside the program thread to stop it (BaseException so `except
    Exception` in user code cannot swallow it)."""


class SimClock:
    """Simulated time, advanced in lockstep with the program thread.

    The program blocks in wait_until(t) (time.sleep). The main loop calls
    sync() before each step: it waits until the program is blocked or finished
    and returns how far time may advance before the program must run again, so
    commands after a sleep take effect exactly at the right simulated time.
    """

    BUSY_TIMEOUT_S = 0.5  # a program that never sleeps cannot hold the sim forever

    def __init__(self):
        self.now = 0.0
        self.wake_at: Optional[float] = None  # set while the program is sleeping
        self.finished = False
        self.busy = False  # program timed out once without sleeping; stop waiting for it
        self._cond = threading.Condition()

    def sync(self) -> float:
        """Seconds the simulation may advance before the program needs to run
        (0 if the program is still busy after BUSY_TIMEOUT_S)."""
        with self._cond:
            ready = lambda: self.finished or (self.wake_at is not None and self.wake_at > self.now)  # noqa: E731
            if not self.busy and not self._cond.wait_for(ready, timeout=self.BUSY_TIMEOUT_S):
                self.busy = True
            if self.finished:
                return float("inf")
            if self.wake_at is None or self.wake_at <= self.now:
                return 0.0  # the program is busy without sleeping
            return self.wake_at - self.now

    def advance(self, dt: float) -> None:
        with self._cond:
            self.now += dt
            if self.wake_at is not None and self.now >= self.wake_at - 1e-9:
                self.now = max(self.now, self.wake_at)
            self._cond.notify_all()

    def wait_until(self, t: float, stop: threading.Event) -> None:
        with self._cond:
            self.wake_at, self.busy = t, False
            self._cond.notify_all()
            while self.now < t:
                if stop.is_set():
                    raise ProgramStopped()
                self._cond.wait(0.05)
            self.wake_at = None
        if stop.is_set():
            raise ProgramStopped()

    def mark_finished(self) -> None:
        with self._cond:
            self.finished = True
            self._cond.notify_all()


class MotorBus:
    """Per motor port: commanded speed (rpm), encoder angle and pending move().

    Written by the program, integrated by the simulation every step. Optional
    imperfections (uncertainty.Variation): per-port speed gain, a first-order
    speed lag, and encoder resolution. With the defaults the motor is ideal.
    """

    def __init__(self, max_rpm: float, gains: Optional[Dict[str, float]] = None,
                 tau_s: float = 0.0, encoder_res_deg: float = 0.0):
        self.max_rpm = max_rpm
        self.gains = dict(gains or {})
        self.tau_s = tau_s
        self.encoder_res_deg = encoder_res_deg
        self._actual: Dict[str, float] = {}       # real shaft speed, lags the command
        self._rpm: Dict[str, float] = {}
        self._angle: Dict[str, float] = {}
        self._move_left: Dict[str, float] = {}  # degrees still to turn for move()
        self._lock = threading.Lock()

    def _clamp(self, rpm: float) -> float:
        return max(-self.max_rpm, min(self.max_rpm, float(rpm)))

    def set(self, port: str, rpm: float) -> None:
        """Store the command clamped to the motor limit, so feedback matches motion.
        Cancels a pending move()."""
        rpm = self._clamp(rpm)
        with self._lock:
            self._rpm[port] = rpm
            self._angle.setdefault(port, 0.0)
            self._move_left.pop(port, None)

    def move(self, port: str, degrees: float, rpm: float) -> None:
        """Relative move like mbuild's move(): turn `degrees` at |rpm|, then stop.
        Returns immediately; the motion happens as simulated time advances."""
        degrees = float(degrees)
        with self._lock:
            self._angle.setdefault(port, 0.0)
            if degrees == 0 or rpm == 0:
                self._rpm[port] = 0.0
                self._move_left.pop(port, None)
                return
            self._rpm[port] = abs(self._clamp(rpm)) * (1 if degrees > 0 else -1)
            self._move_left[port] = abs(degrees)

    def integrate(self, dt: float) -> Dict[str, float]:
        """Advance encoders by dt seconds; returns the average real rpm per port over
        the step (a move() that finishes mid-step only counts its remaining part)."""
        avg = {}
        follow = 1.0 if self.tau_s <= 0 else 1.0 - math.exp(-dt / self.tau_s)
        with self._lock:
            for port, command in self._rpm.items():
                target = command * self.gains.get(port, 1.0)
                rpm = self._actual.get(port, 0.0)
                rpm += (target - rpm) * follow
                self._actual[port] = rpm
                step = rpm * 6.0 * dt  # rpm -> degrees per second
                left = self._move_left.get(port)
                if left is not None and abs(step) >= left:
                    step = left if command > 0 else -left
                    self._rpm[port] = self._actual[port] = 0.0  # move() holds its end position
                    del self._move_left[port]
                elif left is not None:
                    self._move_left[port] = left - abs(step)
                self._angle[port] = self._angle.get(port, 0.0) + step
                avg[port] = step / (6.0 * dt) if dt > 0 else 0.0
        return avg

    def snapshot(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._rpm)

    def angle(self, port: str) -> float:
        """Encoder reading, rounded to the encoder resolution when one is set."""
        with self._lock:
            angle = self._angle.get(port, 0.0)
        res = self.encoder_res_deg
        return round(angle / res) * res if res > 0 else angle


class DCBus:
    """Power (-100..100 %) per power expansion board port (DC1..DC8, BL1, BL2), written
    by the program through mbuild.power_expand_board and read by the simulation
    (e.g. the intake). The DC motors themselves are not modelled."""

    def __init__(self):
        self._power: Dict[str, float] = {}
        self._lock = threading.Lock()

    def set(self, port: str, power: float) -> None:
        with self._lock:
            self._power[str(port)] = max(-100.0, min(100.0, float(power)))

    def power(self, port: str) -> float:
        with self._lock:
            return self._power.get(str(port), 0.0)

    def snapshot(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._power)


class Sensors:
    """Gyroscope and accelerometer readings, written by the simulation each step.

    gyro_z in deg/s with the sign set by the robot config; accel in m/s^2 in the
    robot frame (x forward, y left, z up with gravity). The floor is flat, so the
    x/y gyro rates are 0.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.gyro = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.accel = {"x": 0.0, "y": 0.0, "z": 9.81}

    def set(self, gyro_z: float, ax: float, ay: float) -> None:
        with self._lock:
            self.gyro["z"] = gyro_z
            self.accel["x"], self.accel["y"] = ax, ay

    def read(self, kind: str, axis: str) -> float:
        table = self.gyro if kind == "gyro" else self.accel
        with self._lock:
            if axis not in table:
                raise UnsupportedAPI(f"axis {axis!r} (use 'x', 'y' or 'z')")
            return table[axis]


class GamepadInput:
    """Latest state of the emulated gamepad, in mBlock terms.

    apply_event() takes the JSON events printed by gamepad.py; the program reads
    it through mbuild.gamepad. Joysticks are -100..100 (+y up, +x right).
    """

    # gamepad.py control id -> mBlock key name. Names follow chassis.py comments
    # ("N1", "≡", "+"); check them against blocks in mBlock if a key never fires.
    KEY_NAMES = {
        "up": "Up", "down": "Down", "left": "Left", "right": "Right",
        "button_1": "N1", "button_2": "N2", "button_3": "N3", "button_4": "N4",
        "L1": "L1", "L2": "L2", "R1": "R1", "R2": "R2",
        "menu": "≡", "plus": "+", "bluetooth": "Bluetooth",
    }
    STICKS = {"left_stick": ("Lx", "Ly"), "right_stick": ("Rx", "Ry")}

    def __init__(self):
        self._lock = threading.Lock()
        self.connected = False
        self.on = True
        self.axes = {"Lx": 0.0, "Ly": 0.0, "Rx": 0.0, "Ry": 0.0}
        self.keys = set()

    def apply_event(self, event: dict) -> None:
        with self._lock:
            self.connected = True
            kind, control = event.get("event"), event.get("control")
            if kind == "power":
                self.on = bool(event.get("on"))
                if not self.on:
                    self.keys.clear()
                    self.axes = {k: 0.0 for k in self.axes}
            elif kind == "press" and control in self.KEY_NAMES:
                self.keys.add(self.KEY_NAMES[control])
            elif kind == "release" and control in self.KEY_NAMES:
                self.keys.discard(self.KEY_NAMES[control])
            elif kind == "axis" and control in self.STICKS:
                ax, ay = self.STICKS[control]
                self.axes[ax] = 100.0 * float(event.get("x", 0.0))
                self.axes[ay] = 100.0 * float(event.get("y", 0.0))

    def joystick(self, name: str) -> float:
        with self._lock:
            if name not in self.axes:
                raise UnsupportedAPI(f"gamepad.get_joystick({name!r}): use one of {sorted(self.axes)}")
            return self.axes[name]

    def pressed(self, name: str) -> bool:
        with self._lock:
            if name not in self.KEY_NAMES.values():
                raise UnsupportedAPI(f"gamepad.is_key_pressed({name!r}): known keys are "
                                     f"{', '.join(self.KEY_NAMES.values())}")
            return name in self.keys

    def disconnect(self) -> None:
        with self._lock:
            self.connected = False
            self.keys.clear()
            self.axes = {k: 0.0 for k in self.axes}


def _build_modules(clock: SimClock, motors: MotorBus, stop: threading.Event,
                   sensors: Sensors, gamepad: GamepadInput, variation=None, trace=None,
                   trace_options=None, dc: Optional[DCBus] = None):
    def check():
        if stop.is_set():
            raise ProgramStopped()

    class encoder_motor_class:  # noqa: N801 - mirrors the mbuild class name
        def __init__(self, port, index="INDEX1"):
            self.port, self.index = str(port), index
            motors.set(self.port, 0.0)

        def set_speed(self, speed):
            check()
            motors.set(self.port, speed)

        def set_power(self, power):
            check()
            motors.set(self.port, max(-100.0, min(100.0, float(power))) / 100.0 * motors.max_rpm)

        def move(self, degrees, speed):
            check()
            motors.move(self.port, degrees, speed)

        def stop(self):
            check()
            motors.set(self.port, 0.0)

        def get_value(self, name):
            check()
            if name == "speed":
                return motors.snapshot().get(self.port, 0.0)
            if name == "angle":
                return motors.angle(self.port)
            raise UnsupportedAPI(f"encoder_motor.get_value({name!r}) is not simulated yet")

        def __getattr__(self, name):
            raise UnsupportedAPI(f"encoder_motor.{name}() is not simulated yet")

    start = {"t": 0.0}

    jitter = variation.sleep_jitter_s if variation else 0.0
    rng = variation.program_rng if variation else None

    def sleep(seconds):
        check()
        extra = rng.uniform(0.0, jitter) if jitter > 0 else 0.0
        clock.wait_until(clock.now + max(0.0, float(seconds)) + extra, stop)

    def now():
        check()
        return clock.now

    def reset_timer():
        start["t"] = clock.now

    time_mod = types.ModuleType("time")
    time_mod.sleep, time_mod.time, time_mod.monotonic, time_mod.perf_counter = sleep, now, now, now
    time_mod.ticks_ms = lambda: int(now() * 1000)   # MicroPython style, used on the NovaPi
    time_mod.ticks_diff = lambda a, b: a - b

    novapi = types.ModuleType("novapi")
    novapi.timer = lambda: now() - start["t"]
    novapi.reset_timer = reset_timer
    novapi.get_gyroscope = lambda axis: (check(), sensors.read("gyro", axis))[1]
    novapi.get_acceleration = lambda axis: (check(), sensors.read("accel", axis))[1]

    class _Gamepad:
        def get_joystick(self, name):
            check()
            return gamepad.joystick(name)

        def is_key_pressed(self, name):
            check()
            return gamepad.pressed(name)

        def __getattr__(self, name):
            raise UnsupportedAPI(f"gamepad.{name}() is not simulated yet")

    dc = dc if dc is not None else DCBus()

    class _PowerExpandBoard:
        def set_power(self, port, power):
            check()
            dc.set(port, power)

        def stop(self, port):
            check()
            dc.set(port, 0.0)

        def __getattr__(self, name):
            raise UnsupportedAPI(f"power_expand_board.{name}() is not simulated yet")

    mbuild = types.ModuleType("mbuild")
    encoder_motor = types.ModuleType("mbuild.encoder_motor")
    encoder_motor.encoder_motor_class = encoder_motor_class
    mbuild.encoder_motor = encoder_motor
    mbuild.gamepad = _Gamepad()
    mbuild.power_expand_board = _PowerExpandBoard()

    # Simulator-only: lets an analysis program record the true pose at chosen
    # moments (Monte Carlo). Not available on the robot.
    simtrace = types.ModuleType("simtrace")
    simtrace.mark = lambda label, **info: (check(), trace(label, info) if trace else None)[1]
    simtrace.options = lambda: dict(trace_options or {})  # study settings, e.g. constant overrides

    return {"time": time_mod, "novapi": novapi, "mbuild": mbuild, "mbuild.encoder_motor": encoder_motor,
            "simtrace": simtrace}


class ProgramRunner:
    """Executes one program file in a daemon thread against a clock and motor bus."""

    def __init__(self, path: Path, clock: SimClock, motors: MotorBus,
                 sensors: Optional[Sensors] = None, gamepad: Optional[GamepadInput] = None,
                 module_roots: Sequence[Path] = (), variation=None, trace=None, trace_options=None,
                 dc: Optional[DCBus] = None):
        self.path = Path(path)
        self.dc = dc if dc is not None else DCBus()
        self.variation, self.trace, self.trace_options = variation, trace, trace_options
        self.module_roots = [Path(r) for r in module_roots]
        self.clock, self.motors = clock, motors
        self.sensors = sensors or Sensors()
        self.gamepad = gamepad or GamepadInput()
        self.stop_event = threading.Event()
        self.error: Optional[str] = None
        self.finished = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        # OSError / UnicodeDecodeError (unreadable file) and SyntaxError surface here.
        code = compile(self.path.read_text(encoding="utf-8"), str(self.path), "exec")
        fakes = _build_modules(self.clock, self.motors, self.stop_event, self.sensors, self.gamepad,
                               self.variation, self.trace, self.trace_options, self.dc)
        real_import = builtins.__import__
        local_modules: Dict[str, types.ModuleType] = {}  # project files, fresh for each run
        self._project_files = {str(self.path)}

        def sim_import(name, globals=None, locals=None, fromlist=(), level=0):
            top = name.split(".")[0]
            if level == 0 and (name in fakes or top in ("novapi", "mbuild", "simtrace")):
                if name not in fakes:
                    raise UnsupportedAPI(f"module {name!r} is not simulated yet")
                return fakes[name] if fromlist else fakes[top]
            if level == 0 and top in local_modules:
                return local_modules[top]
            path = self.find_module(top) if level == 0 else None
            if path:
                return load_local(top, path)
            return real_import(name, globals, locals, fromlist, level)

        def load_local(top, path):
            module = types.ModuleType(top)
            module.__file__ = str(path)
            self._project_files.add(str(path))
            module.__builtins__ = sim_builtins
            local_modules[top] = module  # registered first, like sys.modules, for circular imports
            exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)
            return module

        sim_builtins = dict(vars(builtins), __import__=sim_import)
        program_globals = {"__name__": "__main__", "__file__": str(self.path), "__builtins__": sim_builtins}

        def run():
            try:
                try:
                    exec(code, program_globals)
                except ProgramStopped:
                    pass
                except UnsupportedAPI as exc:
                    self.error = f"Unsupported: {exc}"
                except Exception:  # report the user's traceback, trimmed to their file
                    lines = traceback.format_exc().strip().splitlines()
                    self.error = lines[-1] + _user_line(sys.exc_info()[2], self._project_files)
            except ProgramStopped:  # a stop injected while handling the program's exit
                pass
            finally:
                self.finished = True
                self.clock.mark_finished()

        self._thread = threading.Thread(target=run, name="mblock-program", daemon=True)
        self._thread.start()

    def find_module(self, name: str) -> Optional[Path]:
        """name.py next to the program, else the single match under the module roots."""
        beside = self.path.parent / f"{name}.py"
        if beside.is_file():
            return beside
        matches = sorted({p.resolve() for root in self.module_roots if root.is_dir()
                          for p in root.rglob(f"{name}.py") if "__pycache__" not in p.parts})
        if len(matches) > 1:
            raise ImportError(f"'import {name}' is ambiguous: " + ", ".join(str(m) for m in matches))
        return matches[0] if matches else None

    def stop(self, timeout: float = 1.0) -> bool:
        """Stop the program; True once its thread has exited.

        Cooperative first (simulated APIs check stop_event), then ProgramStopped
        is injected into the thread every few ms, so a loop that swallows one
        injection still gets the next.
        """
        self.stop_event.set()
        thread = self._thread
        if thread is None:
            return True
        thread.join(0.05)
        deadline = time.monotonic() + timeout
        while thread.is_alive() and not self.finished and time.monotonic() < deadline:
            _raise_in_thread(thread, ProgramStopped)
            thread.join(0.01)
        thread.join(max(0.0, deadline - time.monotonic()))  # finished: let it return
        return not thread.is_alive()


def _raise_in_thread(thread: threading.Thread, exc_type) -> None:
    """Ask CPython to raise exc_type in `thread` at its next bytecode boundary."""
    if thread.ident is not None:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(thread.ident), ctypes.py_object(exc_type))


def _user_line(tb, files) -> str:
    """' (file.py line N)' for the deepest frame in the program or a project module."""
    where = None
    while tb:
        filename = tb.tb_frame.f_code.co_filename
        if filename in files:
            where = (Path(filename).name, tb.tb_lineno)
        tb = tb.tb_next
    return f" ({where[0]} line {where[1]})" if where else ""
