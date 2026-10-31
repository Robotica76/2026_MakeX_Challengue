"""Figures of the strategy simulations (automatic-stage Monte Carlo, chassis control, full match).

    .venv/bin/python simulation/analysis/plot_strategy_report.py            # ~5 min on 5 cores
    .venv/bin/python simulation/analysis/plot_strategy_report.py --trials 8 # quicker

Writes simulation/analysis/reports/strategy_montecarlo/figures/*.png and summary.json:
  1_field_paths.png      paths of the winning automatic stage (ideal robot + sampled robots), where
                         the X12 ends, our half and the alliance limit
  2_candidates.png       Monte Carlo comparison of the candidates (P(X12), P(X9), resources, problems)
  3_x12_time.png         when the X12 is in the exchange area, per candidate
  4_speed_profile.png    robot speed over the automatic stage: profiled control vs drive() (2025-style P)
  5_match_points.png     whole-match points per automatic strategy (same scripted manual stage)
"""

import argparse
import contextlib
import io
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "simulation" / "field2d"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

import montecarlo_strategy as mc  # noqa: E402

OUT = HERE / "reports" / "strategy_montecarlo"
CANDIDATES = [
    ("Winner: X12 + X9 denied", {}),
    ("X12 only", {"DENY_X9": 0}),
    ("Grab 7 mm short", {"GRAB_SHORT": 7}),
    ("Faster profile", {"V_MAX": 900, "A_MAX": 1600, "D_MAX": 1800}),
]
KIND_COLOR = {"obstacle": "#8d99ae", "overhead": "#cfd8e3", "movable": "#e5989b", "zone": "#b7e4c7", "slot": "#ffd166"}


def run_trials(trials, workers):
    jobs = [(c, -1, True) for _, c in CANDIDATES[:1]]
    jobs += [(c, 9000 + i, True) for _, c in CANDIDATES for i in range(trials)]
    with ProcessPoolExecutor(workers) as pool:
        rows = list(pool.map(mc.trial, jobs, chunksize=1))
    ideal, rest = rows[0], rows[1:]
    per = {name: rest[k * trials:(k + 1) * trials] for k, (name, _) in enumerate(CANDIDATES)}
    return ideal, per


def old_controller_speed():
    """Speed trace of auto_pull_central.py "bonus" (chassis.drive, P control) on the ideal robot."""
    import field_layout as fl
    from balls import load_intake
    from kinematics import load_drive_train
    from mechanisms import load_mechanisms
    from props import load_gripper
    from robot import load_config, start_pose
    from simulation import Simulation, load_gyro_sign
    cfg = load_config()
    sim = Simulation(cfg, start_pose(cfg, fl.build_field()), load_drive_train(), 30, load_gyro_sign(),
                     ball_scenario="initial", intake=load_intake(), mechanisms=load_mechanisms(), gripper=load_gripper())
    sim.program = ROOT / "software" / "autonomous" / "task_execution" / "auto_pull_central.py"
    sim.trace_options = {"strategy": "bonus"}
    path, k = [], 0
    with contextlib.redirect_stdout(io.StringIO()):
        sim.run()
        while sim.running:
            sim.step(1 / 60)
            k += 1
            if k % 6 == 0:
                vx, vy, _ = sim._velocity
                path.append((sim.time, sim.pose.x, sim.pose.y, 0.0, math.hypot(vx, vy)))
    return path


def match_points():
    from simulate_match import play
    out = {}
    for name in ("bonus", "props", "balls", "mixed"):
        _, _, score = play(ROOT / "simulation" / "control" / "match_2026.py", 280.0, {"strategy": name})
        out[name] = score
    return out


def draw_field(ax):
    import field_layout as fl
    for el in fl.build_field():
        x0, y0, x1, y1 = el.bounds()
        color = KIND_COLOR.get(el.kind)
        if color is None or x0 > 2500:
            continue
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=color, edgecolor="#555", lw=0.4, alpha=0.8, zorder=1))
    ax.axhline(fl.CY, color="#d62828", lw=1.2, ls="--", zorder=2)
    ax.text(60, fl.CY + 25, "partner half (y > 1527.5)", color="#d62828", fontsize=8)
    ax.axvline(2220, color="#1d3557", lw=1.2, ls=":", zorder=2)
    ax.text(2230, 2980, "alliance limit x 2220", color="#1d3557", fontsize=8, va="top")
    ax.set_xlim(0, 2500)
    ax.set_ylim(0, 3055)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")


def fig_paths(ideal, rows, path):
    fig, ax = plt.subplots(figsize=(9, 9.5))
    draw_field(ax)
    for r in rows:
        xs = [p[1] for p in r["path"]]
        ys = [p[2] for p in r["path"]]
        ax.plot(xs, ys, color="#457b9d", lw=0.6, alpha=0.35, zorder=3)
    xs = [p[1] for p in ideal["path"]]
    ys = [p[2] for p in ideal["path"]]
    ax.plot(xs, ys, color="#e63946", lw=2.2, zorder=4, label="ideal robot")
    for t_mark in (5, 10, 15, 20, 25):
        p = min(ideal["path"], key=lambda q: abs(q[0] - t_mark))
        ax.annotate(f"{t_mark} s", (p[1], p[2]), fontsize=8, color="#e63946", xytext=(4, 4), textcoords="offset points")
    ends = [r["x12_end"] for r in rows if r["x12_end"]]
    ok = [e for e, r in zip(ends, rows) if r["valid_x12"]]
    bad = [e for e, r in zip(ends, rows) if not r["valid_x12"]]
    if ok:
        ax.scatter(*zip(*ok), marker="s", s=40, color="#2a9d8f", zorder=5, label="X12 final (valid)")
    if bad:
        ax.scatter(*zip(*bad), marker="x", s=60, color="#d00000", zorder=5, label="X12 final (not valid)")
    ax.plot([], [], color="#457b9d", lw=1, label=f"{len(rows)} sampled robots")
    ax.set_title("Winning automatic stage: paths (Red Start 1, lower half)")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def fig_candidates(per, path):
    names = list(per)
    stats = {n: mc.summarize({}, rows) for n, rows in per.items()}
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.2))
    metrics = [("p_x12", "P(X12 valid)", (0, 1.05)), ("p_x9", "P(X9 on our side)", (0, 1.05)),
               ("resources", "resources (mean)", None), ("problems", "rule problems per run", None)]
    colors = ["#e63946", "#457b9d", "#a8dadc", "#f4a261"]
    for ax, (key, label, lim) in zip(axes, metrics):
        vals = [stats[n][key] for n in names]
        bars = ax.bar(range(len(names)), vals, color=colors)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=25, ha="right", fontsize=8)
        ax.set_title(label)
        if lim:
            ax.set_ylim(*lim)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    n = len(next(iter(per.values())))
    fig.suptitle(f"Monte Carlo, {n} sampled robots per candidate (calibrated robot + start jig)")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return stats


def fig_x12_time(per, path):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    data = [[r["x12_time"] for r in rows if r["x12_time"]] for rows in per.values()]
    ax.boxplot(data, labels=list(per), showmeans=True)
    for i, d in enumerate(data, 1):
        ax.scatter([i + (j % 5 - 2) * 0.03 for j in range(len(d))], d, s=10, alpha=0.6, color="#1d3557")
    ax.set_ylabel("X12 in the exchange area (s)")
    ax.set_title("When the X12 is secured (earlier = less risk the opponent takes it)")
    ax.tick_params(axis="x", labelrotation=15, labelsize=8)
    ax.axhline(30, color="#d62828", ls="--", lw=1)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def fig_speed(ideal, old, path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True)
    for trace, label, color in ((ideal["path"], "profiled control (storm_breaker_2026)", "#e63946"),
                                (old, "chassis.drive() P control (previous)", "#457b9d")):
        t = [p[0] for p in trace]
        v = [p[4] for p in trace]
        dist, total = [], 0.0
        for a, b in zip(trace, trace[1:]):
            total += math.hypot(b[1] - a[1], b[2] - a[2])
            dist.append(total / 1000)
        ax1.plot(t, v, color=color, lw=1.2, label=label)
        ax2.plot(t[1:], dist, color=color, lw=1.5, label=label)
    ax1.set_ylabel("speed (mm/s)")
    ax1.legend(fontsize=8)
    ax1.set_title("Automatic stage on the ideal robot: speed and distance")
    ax2.set_ylabel("distance driven (m)")
    ax2.set_xlabel("time (s)")
    for ax in (ax1, ax2):
        ax.axvline(30, color="#d62828", ls="--", lw=1)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def fig_match(points, path):
    names = list(points)
    parts = [("precision", "balls in the blue fortress", "#457b9d"), ("flag", "team flag", "#2a9d8f")]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bottom = [0] * len(names)
    for key, label, color in parts:
        vals = [points[n].get(key, 0) for n in names]
        ax.bar(names, vals, bottom=bottom, color=color, label=label)
        bottom = [b + v for b, v in zip(bottom, vals)]
    for i, n in enumerate(names):
        ax.text(i, bottom[i], f"{points[n]['total']}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("points (simulated)")
    ax.set_xlabel("automatic strategy (same scripted manual stage, our half, flag in the final)")
    ax.set_title("Whole match, 280 s (pins / X mark / letter cubes not simulated)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--trials", type=int, default=24)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()
    figs = OUT / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    ideal, per = run_trials(args.trials, args.workers)
    old = old_controller_speed()
    points = match_points()
    fig_paths(ideal, per[CANDIDATES[0][0]], figs / "1_field_paths.png")
    stats = fig_candidates(per, figs / "2_candidates.png")
    fig_x12_time(per, figs / "3_x12_time.png")
    fig_speed(ideal, old, figs / "4_speed_profile.png")
    fig_match(points, figs / "5_match_points.png")
    summary = {"trials": args.trials, "candidates": {n: {k: v for k, v in s.items() if k != "failures"}
                                                     for n, s in stats.items()},
               "match_points": {n: p["total"] for n, p in points.items()},
               "ideal_x12_time": ideal["x12_time"]}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps(summary, indent=1, default=str))
    print("figures in", figs.relative_to(ROOT))


if __name__ == "__main__":
    main()
