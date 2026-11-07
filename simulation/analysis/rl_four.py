"""Online reinforcement learning on the detailed 4-robot match (four_robots.py): a UCB1 bandit picks
our alliance's configuration (arms proposed by the 2 vs 2 policy of rl_strategy.py) and plays it as a
whole 280 s match against the blue alliance (the same robots with the current plan); reward = our
points - theirs. Several matches run at once (one process each, ~2 min a match).

    .venv/bin/python simulation/analysis/rl_four.py --rounds 4
Writes results/rl_four.json and reports/rl_four/bandit.png.
"""

import argparse
import json
import math
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ARMS = [
    ("current: ORDER 12, X 277.3", 12, {"main": {"x_fire_at": 277.3}, "partner": {"x_fire_at": 277.3}}),
    ("ORDER 13 (X12, table balls)", 13, {"main": {"x_fire_at": 277.3}, "partner": {"x_fire_at": 277.3}}),
    ("ORDER 12, X 277.8", 12, {"main": {"x_fire_at": 277.8}, "partner": {"x_fire_at": 277.8}}),
    ("ORDER 13, X 277.8", 13, {"main": {"x_fire_at": 277.8}, "partner": {"x_fire_at": 277.8}}),
    ("ORDER 12, partner shoots all, X 277.8", 12, {"main": {"x_fire_at": 277.8}, "partner": {"x_reserve": False}}),
    ("ORDER 13, partner shoots all, X 277.8", 13, {"main": {"x_fire_at": 277.8}, "partner": {"x_reserve": False}}),
    ("ORDER 13, X 278.2 / 277.8", 13, {"main": {"x_fire_at": 278.2}, "partner": {"x_fire_at": 277.8}}),
]
REPORT = HERE / "results" / "rl_four.json"
OUT = HERE / "reports" / "rl_four"


def pull(job):
    arm, delay = job
    import contextlib
    import io
    import four_robots
    _, order, opts = ARMS[arm]
    with contextlib.redirect_stdout(io.StringIO()):
        out = four_robots.play(order, 12, delay, red_options=opts, trace_every=0)
    red, blue = out["scores"]["red"], out["scores"]["blue"]
    keep = ("total", "precision", "bonus_cubes", "cones", "letter_cubes", "flag", "x_mark", "penalties")
    return {"arm": arm, "delay": delay, "reward": red["total"] - blue["total"],
            "red": {k: red[k] for k in keep}, "blue": {k: blue[k] for k in keep},
            "contacts": len(out["contacts"]), "x_mark": out["x_mark"]}


def ucb(stats, n_total, c):
    best = []
    for arm, rs in stats.items():
        if not rs:
            return [arm]
        mean = sum(rs) / len(rs)
        best.append((mean + c * math.sqrt(2 * math.log(max(n_total, 2)) / len(rs)), arm))
    return [a for _, a in sorted(best, reverse=True)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rounds", type=int, default=4, help="UCB rounds after every arm was tried once")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--c", type=float, default=60.0, help="exploration (points)")
    args = ap.parse_args()
    rng = random.Random(5)
    stats = {a: [] for a in range(len(ARMS))}
    rows = []
    with ProcessPoolExecutor(args.workers) as pool:
        batches = [list(range(len(ARMS)))]
        for _ in range(args.rounds):
            batches.append(None)
        for batch in batches:
            if batch is None:
                order = ucb(stats, len(rows), args.c)
                batch = order[:args.workers]
            jobs = [(a, rng.choice((0, 2, 4))) for a in batch]
            for res in pool.map(pull, jobs):
                stats[res["arm"]].append(res["reward"])
                rows.append(res)
                print(f"{ARMS[res['arm']][0]:42s} delay {res['delay']}: red {res['red']['total']:4d} "
                      f"blue {res['blue']['total']:4d}  margin {res['reward']:+5d}  X {res['x_mark']}", flush=True)
    table = sorted(((sum(r) / len(r), len(r), min(r), ARMS[a][0], a) for a, r in stats.items() if r), reverse=True)
    print("\n== arms (mean margin, matches, worst)")
    for mean, n, worst, name, _ in table:
        print(f"{mean:+7.1f}  n={n}  worst {worst:+5d}  {name}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"arms": [a[0] for a in ARMS], "rows": rows,
                                  "table": [{"arm": a, "name": name, "mean": mean, "n": n, "worst": worst}
                                            for mean, n, worst, name, a in table]}, indent=1))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    for k, (mean, n, worst, name, a) in enumerate(table[::-1]):
        rs = stats[a]
        ax.scatter(rs, [k] * len(rs), color="#7f8c8d", zorder=3)
        ax.barh(k, mean, color="#c0392b" if k == len(table) - 1 else "#e59866", alpha=0.85)
    ax.set_yticks(range(len(table)))
    ax.set_yticklabels([f"{t[3]} (n={t[1]})" for t in table[::-1]], fontsize=8)
    ax.axvline(0, color="k", lw=0.6)
    ax.set_xlabel("point margin red - blue (bar: mean, dots: matches)")
    ax.set_title("UCB bandit on the detailed 4-robot match: our alliance's configuration")
    fig.tight_layout()
    fig.savefig(OUT / "bandit.png", dpi=140)
    print("report:", REPORT.relative_to(HERE.parents[1]))


if __name__ == "__main__":
    main()
