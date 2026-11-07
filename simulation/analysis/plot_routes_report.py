"""Figures of the route Monte Carlo (montecarlo_routes.py) and of the two-robot match (two_robots.py).

    .venv/bin/python simulation/analysis/plot_routes_report.py
reads simulation/analysis/results/montecarlo_routes.json and results/two_robots.json; writes
simulation/analysis/reports/routes_montecarlo/:
  1_auto_routes.png    automatic stage value of every mission order (mean and worst robot)
  2_match_routes.png   whole-match points of the best orders, by scoring item
  3_two_robots.png     paths of the red robot and its blue twin over the match
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "simulation" / "field2d"))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from matplotlib.patches import Rectangle  # noqa: E402

from plot_strategy_report import KIND_COLOR  # noqa: E402

OUT = HERE / "reports" / "routes_montecarlo"
RESULTS = HERE / "results"


def fig_auto(auto, path, top=24):
    rows = auto[:top]
    fig, ax = plt.subplots(figsize=(11, 7))
    y = range(len(rows))[::-1]
    ax.barh(list(y), [r["value"] for r in rows], color="#c0392b", alpha=0.8, label="mean value")
    ax.plot([r["min_value"] for r in rows], list(y), "k|", markersize=12, label="worst robot")
    ax.set_yticks(list(y))
    ax.set_yticklabels([f"{r['order']}: {r['route']}" for r in rows], fontsize=8)
    ax.set_xlabel("automatic stage value (points it makes or makes possible)")
    ax.set_title("Automatic stage: every mission order, sampled robots (best on top)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def fig_match(match, path):
    items = [("precision", "#2980b9"), ("cones", "#f39c12"), ("letter_cubes", "#8e44ad"), ("flag", "#27ae60"),
             ("x_mark", "#7f8c8d")]
    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(match))
    bottom = [0.0] * len(match)
    for key, color in items:
        vals = [r[key] for r in match]
        ax.bar(list(x), vals, bottom=bottom, color=color, label=key.replace("_", " "))
        bottom = [b + v for b, v in zip(bottom, vals)]
    pen = [-r["penalties"] for r in match]
    ax.bar(list(x), pen, color="#e74c3c", label="penalties")
    for i, r in enumerate(match):
        ax.text(i, bottom[i] + 5, f"{r['total']:.0f}", ha="center", fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{r['order']}\n{r['route']}".replace(" > ", "\n") for r in match], fontsize=7)
    ax.set_ylabel("points (mean over driver delays)")
    ax.set_title("Whole matches (scripted driver) of the best automatic orders")
    ax.legend(fontsize=8, ncol=3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def draw_whole_field(ax):
    import field_layout as fl
    for el in fl.build_field():
        x0, y0, x1, y1 = el.bounds()
        color = KIND_COLOR.get(el.kind)
        if color is not None:
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=color, edgecolor="#555", lw=0.4,
                                   alpha=0.8, zorder=1))
    ax.axvline(fl.CX, color="#555", lw=0.8, ls=":")
    ax.set_xlim(0, fl.FIELD_W)
    ax.set_ylim(0, fl.FIELD_H)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")


def fig_two(two, path):
    fig, ax = plt.subplots(figsize=(13, 8.5))
    draw_whole_field(ax)
    tr = two["trace"]
    for k, (color, name) in enumerate((("#c0392b", "red"), ("#2471a3", "blue twin"))):
        xs = [row[1 + 2 * k] for row in tr]
        ys = [row[2 + 2 * k] for row in tr]
        ax.plot(xs, ys, "-", color=color, lw=1.0, alpha=0.8,
                label=f"{name}: {two['scores'][('red', 'blue')[k]]['total']} points")
    for c in two["contacts"]:
        row = min(tr, key=lambda r: abs(r[0] - c["t"]))
        ax.plot([row[1]], [row[2]], "kx", ms=10)
    ax.set_title(f"Two identical robots (same program and driver, the twin turned 180 deg); "
                 f"contacts: {len(two['contacts'])}, X mark: {two['x_mark']}")
    ax.legend(loc="lower center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    routes = json.loads((RESULTS / "montecarlo_routes.json").read_text())
    fig_auto(routes["auto"], OUT / "1_auto_routes.png")
    fig_match(routes["match"], OUT / "2_match_routes.png")
    for name, fig in (("two_robots", "3_two_robots"), ("two_12_13", "4_two_robots_12_vs_13"),
                      ("two_34_34", "5_two_robots_34_vs_34")):
        src = RESULTS / f"{name}.json"
        if src.exists():
            fig_two(json.loads(src.read_text()), OUT / f"{fig}.png")
    print("figures:", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
