"""Run mBlock-generated Python (novapi / mbuild) against the simulator.

The program runs unchanged in a worker thread. Its imports of `novapi`,
`mbuild.*` and `time` are swapped for stand-ins that drive the simulated robot:

- encoder_motor_class(port, index): set_speed(rpm), set_power(%), stop(),
  get_value("speed").
- time.sleep / time.time / time.monotonic and novapi.timer() / reset_timer()
  follow the simulation clock, so sleeps take simulated time.

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
import sys
import threading
import time
import traceback
import types
from pathlib import Path
from typing import Dict, Optional


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
    """Commanded speed (rpm) per motor port, written by the program, read by the sim."""

    def __init__(self, max_rpm: float):
        self.max_rpm = max_rpm
        self._rpm: Dict[str, float] = {}
        self._lock = threading.Lock()

    def set(self, port: str, rpm: float) -> None:
        """Store the command clamped to the motor limit, so feedback matches motion."""
        rpm = max(-self.max_rpm, min(self.max_rpm, float(rpm)))
        with self._lock:
            self._rpm[port] = rpm

    def snapshot(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._rpm)


def _build_modules(clock: SimClock, motors: MotorBus, stop: threading.Event):
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

        def stop(self):
            check()
            motors.set(self.port, 0.0)

        def get_value(self, name):
            check()
            if name == "speed":
                return motors.snapshot().get(self.port, 0.0)
            raise UnsupportedAPI(f"encoder_motor.get_value({name!r}) is not simulated yet")

        def __getattr__(self, name):
            raise UnsupportedAPI(f"encoder_motor.{name}() is not simulated yet")

    start = {"t": 0.0}

    def sleep(seconds):
        check()
        clock.wait_until(clock.now + max(0.0, float(seconds)), stop)

    def now():
        check()
        return clock.now

    def reset_timer():
        start["t"] = clock.now

    time_mod = types.ModuleType("time")
    time_mod.sleep, time_mod.time, time_mod.monotonic, time_mod.perf_counter = sleep, now, now, now

    novapi = types.ModuleType("novapi")
    novapi.timer = lambda: now() - start["t"]
    novapi.reset_timer = reset_timer

    mbuild = types.ModuleType("mbuild")
    encoder_motor = types.ModuleType("mbuild.encoder_motor")
    encoder_motor.encoder_motor_class = encoder_motor_class
    mbuild.encoder_motor = encoder_motor

    return {"time": time_mod, "novapi": novapi, "mbuild": mbuild, "mbuild.encoder_motor": encoder_motor}


class ProgramRunner:
    """Executes one program file in a daemon thread against a clock and motor bus."""

    def __init__(self, path: Path, clock: SimClock, motors: MotorBus):
        self.path = Path(path)
        self.clock, self.motors = clock, motors
        self.stop_event = threading.Event()
        self.error: Optional[str] = None
        self.finished = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        # OSError / UnicodeDecodeError (unreadable file) and SyntaxError surface here.
        code = compile(self.path.read_text(encoding="utf-8"), str(self.path), "exec")
        fakes = _build_modules(self.clock, self.motors, self.stop_event)
        real_import = builtins.__import__

        def sim_import(name, globals=None, locals=None, fromlist=(), level=0):
            if level == 0 and (name in fakes or name.split(".")[0] in ("novapi", "mbuild")):
                if name not in fakes:
                    raise UnsupportedAPI(f"module {name!r} is not simulated yet")
                return fakes[name] if fromlist else fakes[name.split(".")[0]]
            return real_import(name, globals, locals, fromlist, level)

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
                    self.error = lines[-1] + _user_line(sys.exc_info()[2], self.path)
            except ProgramStopped:  # a stop injected while handling the program's exit
                pass
            finally:
                self.finished = True
                self.clock.mark_finished()

        self._thread = threading.Thread(target=run, name="mblock-program", daemon=True)
        self._thread.start()

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


def _user_line(tb, path: Path) -> str:
    line = None
    while tb:
        if tb.tb_frame.f_code.co_filename == str(path):
            line = tb.tb_lineno
        tb = tb.tb_next
    return f" (line {line})" if line else ""
