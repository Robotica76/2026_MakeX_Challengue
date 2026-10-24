# Simulation Analysis and Design Calculations

Future work may include design calculations, parameter sweeps, uncertainty/sensitivity studies, and simulation data analysis. Example questions: which assumptions drive stability, transfer reliability, reach, or release predictions? No answers or numeric design targets are asserted.

TBD per study: equation/model provenance, units, sourced versus estimated inputs, parameter ranges and rationale, input/output revisions, metrics, limitations, reviewer, and decision impact.

Link [model](../robot_model/README.md), [control](../control/README.md), or [trajectory](../trajectories/README.md) studies to reproducible future evidence. Development-only data processing belongs in [tools/data_analysis](../../tools/data_analysis/README.md). No analysis framework or generated dataset is provided.

## Monte Carlo: chassis.py robustness

`montecarlo_chassis.py` checks `software/controls/drivetrain/chassis.py` against an
imperfect robot. Each trial samples one robot from the ranges in a config file
(wheel diameter, motor gain and lag, slip forward / strafing / turning, gyro bias,
drift, noise and scale, encoder resolution, loop timing jitter, start placement),
runs `mc_routine_chassis.py` in the [2D simulator](../field2d/README.md) and measures
every move against the simulator's **true** pose:

- drive moves (forward/backward 60 cm, strafe 30 cm, diagonals): position error, cm;
- turns (`turn_to` and relative `turn`, 90 deg): heading error, deg.

**Criterion** (requested: error <= 0.01 m per move, > 95 % with 95 % confidence): a
move kind passes when the exact one-sided Clopper-Pearson 95 % lower bound of its
in-tolerance rate is >= 95 %. Each trial is an independent robot, so each move kind
has n = trials samples; with zero failures 59 trials is the minimum. Drive tolerance
1 cm (the 1 % of distance rate is reported too); turns use 1.5 deg, the controller's
own `TOL_DEGREES`, since no turn target was given. All in `criteria` of the config.

```bash
.venv/bin/python simulation/analysis/montecarlo_chassis.py                       # chassis.py as is
.venv/bin/python simulation/analysis/montecarlo_chassis.py --set TOL_CM=0.3     # what-if, file unchanged
.venv/bin/python simulation/analysis/montecarlo_chassis.py --ideal --trials 5   # sanity: no errors
.venv/bin/python simulation/analysis/montecarlo_chassis.py \
    --config simulation/analysis/montecarlo_config_calibrated.json --set TOL_CM=0.3 --set TOL_DEGREES=0.5
```

**Full report with figures, calibration steps and the chassis.py parameters to
write: [reports/chassis_montecarlo](reports/chassis_montecarlo/README.md)** (in
Spanish and English), regenerated with `make_chassis_report.py` (needs `pip install -r
simulation/analysis/requirements.txt` for matplotlib; ~3 min).

300 trials take about 40 s on 6 cores. Each run writes `report.md` (table,
sensitivity ranking, failed trials), `trials.csv` (sampled parameters) and
`moves.csv` (every move) under `results/` (not committed). `--set NAME=VALUE`
overrides a `chassis.py` constant inside the simulation only.

### Results (2026-10-23, 300 trials each, seed 2026)

| Scenario | Drive moves, worst p95 error | Turns, worst p95 error | Verdict |
| --- | --- | --- | --- |
| chassis.py as is, estimated ranges | 4.46 cm (strafe) | 3.06 deg | FAIL, every move |
| A: `TOL_CM=0.3`, `TOL_DEGREES=0.5` | 3.87 cm (strafe) | 2.15 deg | FAIL, every move |
| B: A + `STRAFE_FACTOR=1.075` (mean strafe slip corrected) | 2.09 cm | 2.16 deg | FAIL, every move |
| C: A + robot calibrated (`montecarlo_config_calibrated.json`) | 0.63 cm (max 0.76) | 1.27 deg | **PASS**, every move (lower bound 96-99 %) |

What the study shows:

1. **The tolerances sit on the target.** `drive()` stops as soon as it is within
   `TOL_CM = 1.0` cm, so even an ideal robot ends 0.95-1.0 cm short (and turns
   1.46-1.51 deg short of `TOL_DEGREES = 1.5`). A 1 cm requirement needs a smaller
   `TOL_CM`; 0.3 cm was enough in simulation.
2. **The remaining error is what the encoders cannot see.** Every move "arrives"
   by odometry (100 %), yet the robot is elsewhere: with the estimated ranges, strafe
   slip drives the drive error (Spearman rho -0.96) and gyro scale error the turn
   error (rho +0.94); after correcting the mean strafe slip, forward slip and wheel
   diameter dominate. Tuning gains cannot remove this; calibration can.
3. **Calibration is the requirement.** With each robot calibrated to about 0.2 %
   (wheel diameter, gyro scale) and 0.3-0.5 % (slip), plus the tighter tolerances,
   every move passes with margin. chassis.py has `STRAFE_FACTOR` for strafe slip but
   no constant for gyro scale or forward slip / effective wheel diameter.

Limits: the ranges are estimates, not measurements; the model has ideal geometry,
no collisions or field contact, no battery sag, and first-order motor lag only. The
study checks the control logic against those assumptions; it does not prove the
robot meets the target. Measure on the robot (wheel travel over 2-3 m, strafe travel,
gyro reading over 10 full turns, gyro drift at rest) and replace the ranges.

| File | Contents |
| --- | --- |
| `montecarlo_chassis.py` | Study runner: sampling, trials in parallel, statistics, report |
| `mc_routine_chassis.py` | Simulator-only routine: chassis moves wrapped in `simtrace.mark()` |
| `montecarlo_config.json` | Estimated uncertainty ranges and criteria (uncalibrated robot) |
| `montecarlo_config_calibrated.json` | Target residual errors after per-robot calibration |
| `test_montecarlo.py` | Statistics, error model, move measurement, ideal and override trials |
| `../field2d/uncertainty.py` | The error model (`Variation`); ideal by default |

