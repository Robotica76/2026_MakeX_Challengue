"""Monte Carlo study checks: python -m unittest (from simulation/analysis)."""

import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "field2d"))
sys.path.insert(0, str(HERE))

import montecarlo_chassis as mc  # noqa: E402
from kinematics import body_velocity  # noqa: E402
from mblock_runtime import MotorBus  # noqa: E402
from robot import load_config  # noqa: E402
from uncertainty import Variation, sample_variation  # noqa: E402


class StatisticsTest(unittest.TestCase):
    def test_clopper_pearson_lower_bound(self):
        # All successes: bound = alpha ** (1/n); 59 trials is the minimum to reach 95 %.
        self.assertAlmostEqual(mc.lower_bound(59, 59), 0.05 ** (1 / 59), places=6)
        self.assertGreaterEqual(mc.lower_bound(59, 59), 0.95)
        self.assertLess(mc.lower_bound(58, 58), 0.95)
        self.assertEqual(mc.trials_needed(0.95, 0.95), 59)
        self.assertEqual(mc.lower_bound(0, 30), 0.0)
        # Definition: at the bound, P(X >= k) equals alpha.
        lb = mc.lower_bound(80, 100)
        self.assertAlmostEqual(mc._binom_tail(80, 100, lb), 0.05, places=4)

    def test_percentile_and_spearman(self):
        self.assertEqual(mc.percentile([1, 2, 3, 4, 5], 0.5), 3)
        self.assertAlmostEqual(mc.percentile(list(range(101)), 0.95), 95)
        self.assertAlmostEqual(mc.spearman([1, 2, 3, 4], [10, 20, 30, 45]), 1.0)
        self.assertAlmostEqual(mc.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertTrue(math.isnan(mc.spearman([1, 1, 1], [1, 2, 3])))


class UncertaintyModelTest(unittest.TestCase):
    def test_default_variation_is_ideal_and_sampling_is_reproducible(self):
        self.assertTrue(Variation().ideal)
        ranges = {"wheel_scale": {"dist": "normal", "mean": 1, "sd": 0.01},
                  "slip_strafe": {"dist": "uniform", "low": 0.9, "high": 0.95}, "encoder_res_deg": 1}
        a, b = sample_variation(ranges, 7), sample_variation(ranges, 7)
        self.assertEqual(a.flat(), b.flat())
        self.assertNotEqual(a.flat(), sample_variation(ranges, 8).flat())
        self.assertEqual(set(a.wheel_scale), {"front_left", "front_right", "rear_left", "rear_right"})
        self.assertTrue(0.9 <= a.slip_strafe <= 0.95)
        with self.assertRaises(ValueError):
            sample_variation({"wheel_size": 1}, 1)

    def test_motor_gain_lag_and_encoder_resolution(self):
        bus = MotorBus(580, gains={"M1": 0.9}, tau_s=0.05, encoder_res_deg=1.0)
        bus.set("M1", 100)
        first = bus.integrate(0.01)["M1"]
        self.assertLess(first, 90)           # lags behind the command
        for _ in range(200):
            rpm = bus.integrate(0.01)["M1"]
        self.assertAlmostEqual(rpm, 90, places=3)  # settles at command x gain
        self.assertEqual(bus.angle("M1"), round(bus.angle("M1")))

    def test_wheel_scale_changes_ground_speed(self):
        cfg = load_config()
        rpms = dict.fromkeys(("front_left", "front_right", "rear_left", "rear_right"), 60)
        vx_nominal = body_velocity(cfg, rpms)[0]
        vx_big = body_velocity(cfg, rpms, dict.fromkeys(rpms, 1.02))[0]
        self.assertAlmostEqual(vx_big / vx_nominal, 1.02)


class StudyTest(unittest.TestCase):
    CFG = {"seed": 1, "routine": "mc_routine_chassis.py", "ranges": {},
           "start": {"x_mm": 1400, "y_mm": 1527.5, "heading_deg": 0}}

    def test_measure_moves_from_marks(self):
        marks = [
            {"label": "fwd", "phase": "start", "kind": "drive", "forward_cm": 60, "right_cm": 0,
             "t": 0, "x": 0, "y": 0, "theta": math.pi / 2},
            {"label": "fwd", "phase": "end", "arrived": True, "t": 2, "x": 5, "y": 595, "theta": math.pi / 2},
        ]
        (m,) = mc.measure_moves(marks)
        self.assertAlmostEqual(m["real_forward_cm"], 59.5)
        self.assertAlmostEqual(m["real_right_cm"], 0.5)  # +x is to the right when facing +y
        self.assertAlmostEqual(m["error"], math.hypot(0.5, 0.5))

    def test_ideal_trial_runs_the_whole_routine(self):
        r = mc.run_trial((0, dict(self.CFG, chassis_overrides={}), True))
        self.assertEqual(r["failed"], "")
        self.assertEqual(len(r["moves"]), 10)
        drives = [m for m in r["moves"] if m["kind"] == "drive"]
        # Ideal robot: drive() stops inside TOL_CM = 1 cm of the target, never beyond it.
        self.assertTrue(all(m["arrived"] and m["error"] <= 1.0 for m in drives), drives)

    def test_override_reaches_chassis_and_unknown_name_fails(self):
        r = mc.run_trial((0, dict(self.CFG, chassis_overrides={"TOL_CM": 0.3}), True))
        drives = [m for m in r["moves"] if m["kind"] == "drive"]
        self.assertTrue(all(m["error"] <= 0.35 for m in drives), drives)
        bad = mc.run_trial((0, dict(self.CFG, chassis_overrides={"NOT_A_CONSTANT": 1}), True))
        self.assertIn("NOT_A_CONSTANT", bad["failed"])


if __name__ == "__main__":
    unittest.main()
