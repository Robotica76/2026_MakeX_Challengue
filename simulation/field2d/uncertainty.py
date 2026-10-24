"""Optional error model: one sampled "robot instance" for Monte Carlo studies.

Variation() with no arguments is the ideal robot (what the viewer and the tests
use). A sampled Variation perturbs the simulation where a real robot differs from
the nominal model:

  wheel_scale      real wheel diameter / nominal, per wheel (odometry assumes nominal)
  motor_gain       real speed / commanded speed, per motor port (encoders see it)
  motor_tau_s      first-order lag of every motor's speed (0 = instant)
  slip_forward     ground speed / wheel speed when driving forward (<= 1)
  slip_strafe      same when strafing (mecanum rollers slip most here)
  slip_turn        same for rotation
  gyro_bias_dps    constant offset, removed by chassis odo.calibrate()
  gyro_drift_dps   random-walk std (deg/s per sqrt(s)): bias change calibrate() misses
  gyro_noise_dps   white noise std per reading
  gyro_scale       relative scale error (0.01 = reads 1 % high)
  encoder_res_deg  encoder resolution (readings are rounded to it)
  sleep_jitter_s   extra delay added to each time.sleep, uniform in [0, jitter]
  start_*          error placing the robot at its start pose

Ranges for sampling live in a JSON spec, see sample_variation().
"""

import math
import random
from dataclasses import dataclass, field, fields
from typing import Dict

WHEELS = ("front_left", "front_right", "rear_left", "rear_right")


@dataclass
class Variation:
    wheel_scale: Dict[str, float] = field(default_factory=dict)
    motor_gain: Dict[str, float] = field(default_factory=dict)
    motor_tau_s: float = 0.0
    slip_forward: float = 1.0
    slip_strafe: float = 1.0
    slip_turn: float = 1.0
    gyro_bias_dps: float = 0.0
    gyro_drift_dps: float = 0.0
    gyro_noise_dps: float = 0.0
    gyro_scale: float = 0.0
    encoder_res_deg: float = 0.0
    sleep_jitter_s: float = 0.0
    start_dx_mm: float = 0.0
    start_dy_mm: float = 0.0
    start_dtheta_deg: float = 0.0
    seed: int = 0

    def __post_init__(self):
        # Independent streams so the sim thread and the program thread never share one.
        self.sim_rng = random.Random(self.seed * 2 + 1)
        self.program_rng = random.Random(self.seed * 2 + 2)

    @property
    def ideal(self) -> bool:
        return self.flat() == Variation().flat()

    def flat(self) -> Dict[str, float]:
        """All sampled values as name -> number (dict fields expanded), for reports."""
        out = {}
        for f in fields(self):
            if f.name == "seed":
                continue
            value = getattr(self, f.name)
            if isinstance(value, dict):
                out.update({f"{f.name}.{k}": v for k, v in sorted(value.items())})
            else:
                out[f.name] = value
        return out


def _draw(rng: random.Random, spec, name: str) -> float:
    """spec: a number (fixed) or {"dist": "normal", "mean", "sd"} /
    {"dist": "uniform", "low", "high"}, optional "min"/"max" clamps."""
    if isinstance(spec, (int, float)):
        return float(spec)
    dist = spec.get("dist")
    if dist == "normal":
        value = rng.gauss(spec["mean"], spec["sd"])
    elif dist == "uniform":
        value = rng.uniform(spec["low"], spec["high"])
    else:
        raise ValueError(f"{name}: dist must be 'normal' or 'uniform', got {dist!r}")
    return min(spec.get("max", math.inf), max(spec.get("min", -math.inf), value))


def sample_variation(ranges: dict, seed: int, ports=("M1", "M2", "M3", "M4")) -> Variation:
    """One robot instance. `ranges` maps Variation field names to specs; wheel_scale
    and motor_gain specs are drawn independently per wheel / port. Missing names
    stay ideal."""
    rng = random.Random(seed)
    known = {f.name for f in fields(Variation)} - {"seed"}
    unknown = set(ranges) - known
    if unknown:
        raise ValueError(f"unknown uncertainty parameters: {sorted(unknown)}")
    values = {}
    for name in sorted(ranges):
        spec = ranges[name]
        if name == "wheel_scale":
            values[name] = {w: _draw(rng, spec, f"{name}.{w}") for w in WHEELS}
        elif name == "motor_gain":
            values[name] = {p: _draw(rng, spec, f"{name}.{p}") for p in ports}
        else:
            values[name] = _draw(rng, spec, name)
    return Variation(seed=seed, **values)
