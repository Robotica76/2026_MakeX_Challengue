"""Monte Carlo robustness study of software/controls/drivetrain/chassis.py.

Each trial samples one imperfect robot (uncertainty.Variation, ranges in
montecarlo_config.json), runs mc_routine_chassis.py on it in the simulator, and
measures every move against the simulator's TRUE pose (simtrace marks):

  drive moves: position error (cm) between commanded and real displacement, in
               the robot frame at the start of the move; also relative to distance
  turns:       error (deg) between commanded and real heading change

A move kind passes when the fraction of trials within tolerance is >= the
required rate with the given confidence: the exact one-sided Clopper-Pearson
lower bound of that fraction must reach `required_rate`. Trials are independent
robots, so each move kind has n = trials independent samples.

Usage (from the repository root or anywhere):
    .venv/bin/python simulation/analysis/montecarlo_chassis.py
    .venv/bin/python simulation/analysis/montecarlo_chassis.py --trials 60 --jobs 4
    .venv/bin/python simulation/analysis/montecarlo_chassis.py --ideal     # sanity check
    .venv/bin/python simulation/analysis/montecarlo_chassis.py --set TOL_CM=0.3 --set TOL_DEGREES=0.5
      (--set overrides chassis.py constants for the study only; the file is not changed)
Writes report.md, trials.csv and moves.csv under simulation/analysis/results/.
"""

import argparse
import contextlib
import csv
import io
import json
import math
import multiprocessing
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELD2D = HERE.parent / "field2d"
sys.path.insert(0, str(FIELD2D))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # nothing here opens a window

import field_layout as fl  # noqa: E402
from kinematics import load_drive_train  # noqa: E402
from robot import RobotPose, load_config  # noqa: E402
from simulation import Simulation, load_gyro_sign  # noqa: E402
from uncertainty import Variation, sample_variation  # noqa: E402

DEFAULT_CONFIG = HERE / "montecarlo_config.json"
RESULTS = HERE / "results"
MAX_SIM_S = 120.0


# ---------------------------------------------------------------- statistics
def _binom_tail(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p), summed in log space."""
    if k <= 0:
        return 1.0
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    log_p, log_q = math.log(p), math.log1p(-p)
    lg = math.lgamma
    terms = [lg(n + 1) - lg(i + 1) - lg(n - i + 1) + i * log_p + (n - i) * log_q for i in range(k, n + 1)]
    top = max(terms)
    return min(1.0, math.exp(top) * sum(math.exp(t - top) for t in terms))


def lower_bound(successes: int, n: int, confidence: float = 0.95) -> float:
    """Exact one-sided Clopper-Pearson lower confidence bound of a proportion."""
    if n == 0 or successes == 0:
        return 0.0
    alpha = 1.0 - confidence
    lo, hi = 0.0, successes / n
    for _ in range(60):  # bisection: smallest p with P(X >= successes | p) >= alpha
        mid = (lo + hi) / 2
        if _binom_tail(successes, n, mid) < alpha:
            lo = mid
        else:
            hi = mid
    return hi


def trials_needed(required_rate: float, confidence: float = 0.95) -> int:
    """Trials needed to pass with zero failures: required_rate ** n <= 1 - confidence."""
    return math.ceil(math.log(1 - confidence) / math.log(required_rate))


def percentile(values, q):
    values = sorted(values)
    if not values:
        return float("nan")
    pos = (len(values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)


def spearman(xs, ys):
    """Rank correlation (average ranks for ties); nan when a series is constant."""
    def ranks(v):
        order = sorted(range(len(v)), key=v.__getitem__)
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")


# ---------------------------------------------------------------- one trial
def _wrap_deg(a):
    return (a + 180.0) % 360.0 - 180.0


def measure_moves(marks):
    """Pair start/end marks and compute each move's real error."""
    moves, start = [], None
    for m in marks:
        if m.get("phase") == "start":
            start = m
            continue
        if start is None or m["label"] != start["label"]:
            continue
        th0 = start["theta"]
        dx, dy = (m["x"] - start["x"]) / 10.0, (m["y"] - start["y"]) / 10.0  # cm, field frame
        forward = dx * math.cos(th0) + dy * math.sin(th0)
        right = -(-dx * math.sin(th0) + dy * math.cos(th0))
        turned_cw = -math.degrees(_wrap_deg_rad(m["theta"] - th0))
        row = {"move": start["label"], "kind": start["kind"], "arrived": bool(m.get("arrived")),
               "duration_s": m["t"] - start["t"]}
        if start["kind"] == "drive":
            cf, cr = start["forward_cm"], start["right_cm"]
            error = math.hypot(forward - cf, right - cr)
            row.update(error=error, relative=error / math.hypot(cf, cr), heading_drift_deg=abs(turned_cw),
                       real_forward_cm=forward, real_right_cm=right)
        else:
            row.update(error=abs(turned_cw - start["turn_deg"]), real_turn_deg=turned_cw,
                       commanded_turn_deg=start["turn_deg"])
        moves.append(row)
        start = None
    return moves


def _wrap_deg_rad(a):
    return math.atan2(math.sin(a), math.cos(a))


def run_trial(args):
    """Worker: (index, config dict, ideal flag[, keep_trail]) -> trial result dict.
    keep_trail adds the true path (field mm, at most ~400 points) for figures."""
    index, cfg, ideal = args[:3]
    keep_trail = len(args) > 3 and args[3]
    seed = cfg["seed"] + index
    drive = load_drive_train()
    var = Variation(seed=seed) if ideal else sample_variation(cfg["ranges"], seed, tuple(drive.motors))
    robot = load_config()
    st = cfg["start"]
    start = RobotPose(st["x_mm"] + var.start_dx_mm, st["y_mm"] + var.start_dy_mm,
                      math.radians(st["heading_deg"] + var.start_dtheta_deg))
    sim = Simulation(robot, start, drive, MAX_SIM_S, load_gyro_sign(), variation=var)
    sim.program = HERE / cfg["routine"]
    sim.trace_options = {"chassis": cfg.get("chassis_overrides", {})}
    with contextlib.redirect_stdout(io.StringIO()):
        sim.run()
        while sim.running and not (sim._runner and sim._runner.finished):
            sim.step(1 / 60)
        error = sim._runner.error if sim._runner else None
        status, message = sim.state.status, sim.state.message
        sim.stop()
    result = {"index": index, "seed": seed, "failed": "", "moves": [], "params": var.flat(),
              "duration_s": sim.time}
    if keep_trail:
        trail = sim.state.trail
        result["trail"] = trail[::max(1, len(trail) // 400)] + trail[-1:]
    if error or status in ("out_of_bounds", "error"):
        result["failed"] = error or message
        return result
    result["moves"] = measure_moves(sim.marks)
    return result


def run_study(cfg, ideal=False, jobs=0, keep_trail=False, progress=None):
    """All trials of one configuration, in parallel; results sorted by trial index."""
    jobs = jobs or os.cpu_count() or 1
    tasks = [(i, cfg, ideal, keep_trail) for i in range(cfg["trials"])]
    results = []
    with multiprocessing.get_context("spawn").Pool(jobs) as pool:
        for k, r in enumerate(pool.imap_unordered(run_trial, tasks), 1):
            results.append(r)
            if progress and (k % max(1, len(tasks) // 10) == 0 or k == len(tasks)):
                progress(f"  {k}/{len(tasks)} trials")
    return sorted(results, key=lambda r: r["index"])


# ---------------------------------------------------------------- report
def summarize(results, criteria):
    by_move = {}
    for r in results:
        for m in r["moves"]:
            by_move.setdefault(m["move"], []).append(m)
    conf, need = criteria["confidence"], criteria["required_rate"]
    rows = []
    for move, ms in by_move.items():
        kind = ms[0]["kind"]
        tol = criteria["drive_error_cm"] if kind == "drive" else criteria["turn_error_deg"]
        errors = [m["error"] for m in ms]
        ok = sum(e <= tol for e in errors)
        row = {"move": move, "kind": kind, "n": len(ms), "tolerance": tol, "pass": ok,
               "rate": ok / len(ms), "lower95": lower_bound(ok, len(ms), conf),
               "mean": sum(errors) / len(errors), "p95": percentile(errors, 0.95), "max": max(errors),
               "arrived": sum(m["arrived"] for m in ms) / len(ms)}
        if kind == "drive":
            rel_ok = sum(m["relative"] <= criteria["drive_relative"] for m in ms)
            row.update(rel_pass=rel_ok, rel_lower95=lower_bound(rel_ok, len(ms), conf))
        row["verdict"] = "PASS" if row["lower95"] >= need else "FAIL"
        rows.append(row)
    return rows


def sensitivity(results, kind):
    """Spearman rho of each sampled parameter vs the trial's worst error of `kind`."""
    usable = [r for r in results if any(m["kind"] == kind for m in r["moves"])]
    if len(usable) < 5:
        return []
    worst = [max(m["error"] for m in r["moves"] if m["kind"] == kind) for r in usable]
    out = []
    for name in usable[0]["params"]:
        rho = spearman([r["params"][name] for r in usable], worst)
        if not math.isnan(rho):
            out.append((name, rho))
    return sorted(out, key=lambda t: -abs(t[1]))


def write_report(path, cfg, results, rows, elapsed, ideal):
    c = cfg["criteria"]
    n = len(results)
    failed = [r for r in results if r["failed"]]
    lines = [
        "# Monte Carlo: chassis.py robustness",
        "",
        f"- Date: {datetime.now():%Y-%m-%d %H:%M}; trials: {n} ({'IDEAL robot, sanity check' if ideal else 'sampled robots'});"
        f" seed {cfg['seed']}; run time {elapsed:.0f} s",
        f"- Criterion: a move kind PASSES when the exact one-sided {c['confidence']:.0%} lower bound of its"
        f" in-tolerance rate is >= {c['required_rate']:.0%}. Tolerances: drive {c['drive_error_cm']:g} cm"
        f" (also reported: {c['drive_relative']:.0%} of distance), turn {c['turn_error_deg']:g} deg.",
        f"- With zero failures, {trials_needed(c['required_rate'], c['confidence'])} trials are the minimum to pass.",
        f"- chassis.py overrides for this study: {cfg.get('chassis_overrides') or 'none (constants as in the file)'}",
        f"- Trials that crashed or left the field: {len(failed)}",
        "- Ranges are estimates (montecarlo_config.json); results check the control logic against them,"
        " not the real robot.",
        "",
        "| Move | n | Tol | In tol | Rate | Lower 95% | Verdict | Mean err | p95 err | Max err | Arrived | Within 1% (lower 95%) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        unit = "cm" if r["kind"] == "drive" else "deg"
        rel = f"{r['rel_pass']} ({r['rel_lower95']:.1%})" if r["kind"] == "drive" else "-"
        lines.append(f"| {r['move']} | {r['n']} | {r['tolerance']:g} {unit} | {r['pass']} | {r['rate']:.1%} |"
                     f" {r['lower95']:.1%} | **{r['verdict']}** | {r['mean']:.2f} | {r['p95']:.2f} |"
                     f" {r['max']:.2f} | {r['arrived']:.0%} | {rel} |")
    overall = "PASS" if rows and all(r["verdict"] == "PASS" for r in rows) else "FAIL"
    lines += ["", f"**Overall: {overall}**", ""]
    if not ideal:
        for kind, title in (("drive", "drive moves (worst position error per trial)"),
                            ("turn", "turns (worst heading error per trial)")):
            sens = sensitivity(results, kind)[:6]
            if sens:
                lines += [f"## Sensitivity: {title}", "",
                          "Spearman rank correlation; |rho| near 1 = this parameter drives the error.", "",
                          "| Parameter | rho |", "| --- | --- |"]
                lines += [f"| {name} | {rho:+.2f} |" for name, rho in sens]
                lines.append("")
    if failed:
        lines += ["## Failed trials", ""] + [f"- trial {r['index']} (seed {r['seed']}): {r['failed']}"
                                             for r in failed[:20]] + [""]
    path.write_text("\n".join(lines) + "\n")
    return overall


def write_csvs(folder, results):
    params = sorted({k for r in results for k in r["params"]})
    with open(folder / "trials.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["trial", "seed", "failed"] + params)
        for r in results:
            w.writerow([r["index"], r["seed"], r["failed"]] + [r["params"].get(p, "") for p in params])
    keys = sorted({k for r in results for m in r["moves"] for k in m})
    with open(folder / "moves.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["trial"] + keys)
        w.writeheader()
        for r in results:
            for m in r["moves"]:
                w.writerow({"trial": r["index"], **m})


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--trials", type=int, help="override the config's trial count")
    ap.add_argument("--jobs", type=int, default=0, help="worker processes (0 = all CPUs)")
    ap.add_argument("--ideal", action="store_true", help="no uncertainty: every move should pass")
    ap.add_argument("--out", type=Path, help="output folder (default results/<timestamp>)")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE",
                    help="override a chassis.py constant for this study (repeatable)")
    args = ap.parse_args(argv)

    cfg = json.loads(args.config.read_text())
    if args.trials:
        cfg["trials"] = args.trials
    overrides = dict(cfg.get("chassis_overrides", {}))
    for item in args.set:
        name, _, value = item.partition("=")
        if not name or not value:
            ap.error(f"--set expects NAME=VALUE, got {item!r}")
        overrides[name.strip()] = json.loads(value)
    cfg["chassis_overrides"] = overrides
    tag = "_ideal" if args.ideal else ""
    tag += "".join(f"_{k}-{v}" for k, v in sorted(overrides.items()))
    out = args.out or RESULTS / f"chassis_{datetime.now():%Y%m%d_%H%M%S}{tag}"
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    results = run_study(cfg, args.ideal, args.jobs, progress=lambda m: print(m, flush=True))
    rows = summarize(results, cfg["criteria"])
    overall = write_report(out / "report.md", cfg, results, rows, time.time() - t0, args.ideal)
    write_csvs(out, results)
    print((out / "report.md").read_text())
    print(f"Overall: {overall}. Files in {out}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
