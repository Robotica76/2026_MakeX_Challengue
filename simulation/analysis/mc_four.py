"""Monte Carlo of whole 4-robot matches (four_robots.py): each match with its own seed (four sampled
robots, props within +-5 mm, a driver delay); the same seeds for every matchup (common random
numbers: paired differences). Results are appended as they arrive, so a stopped run keeps them.

    .venv/bin/python simulation/analysis/mc_four.py --seeds 16
Writes results/mc_four.json and reports/mc_four/*.png.
"""

import argparse
import json
import math
import os
import statistics as st
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
REPORT = HERE / "results" / "mc_four.json"
OUT = HERE / "reports" / "mc_four"
X = lambda t: {"main": {"x_fire_at": t}, "partner": {"x_fire_at": t}}  # noqa: E731
MATCHUPS = {
    "12 vs 12": (12, X(277.3), 12, {}),
    "13 vs 12": (13, X(277.3), 12, {}),
    "13 X277.8 vs 12": (13, X(277.8), 12, {}),
    "12 vs 13": (12, X(277.3), 13, {}),
    "13 X277.8 vs 13": (13, X(277.8), 13, {}),
}
DELAYS = (0, 4, 6, 8)                  # frames; 0 and 2 are the same delay


def match(job):
    name, seed = job
    import contextlib
    import io
    import four_robots
    ro, rop, bo, bop = MATCHUPS[name]
    delay = DELAYS[seed % len(DELAYS)]
    with contextlib.redirect_stdout(io.StringIO()):
        out = four_robots.play(ro, bo, delay, red_options=rop, blue_options=bop, trace_every=0, seed=seed)
    keep = ("total", "precision", "balls", "bonus_balls", "cones", "letter_cubes", "flag", "x_mark", "penalties")
    rs = out["robots"]
    return {"matchup": name, "seed": seed, "delay": delay,
            "red": {k: out["scores"]["red"][k] for k in keep}, "blue": {k: out["scores"]["blue"][k] for k in keep},
            "x": out["x_mark"], "contacts": len(out["contacts"]),
            "collisions": sum(len(r.sim.collisions.collisions) for r in rs),
            "errors": [r.sim.state.status for r in rs if r.sim.state.status not in ("done", "running")]}


def summary(rows):
    out = {}
    for name in MATCHUPS:
        rs = [r for r in rows if r["matchup"] == name]
        if not rs:
            continue
        m = [r["red"]["total"] - r["blue"]["total"] for r in rs]
        sd = st.stdev(m) if len(m) > 1 else 0.0
        out[name] = {"n": len(m), "margin": st.mean(m), "sd": sd, "ci95": 1.96 * sd / math.sqrt(len(m)),
                     "win": sum(v > 0 for v in m) / len(m), "worst": min(m), "best": max(m),
                     "red": {k: st.mean(r["red"][k] for r in rs) for k in rs[0]["red"]},
                     "blue": {k: st.mean(r["blue"][k] for r in rs) for k in rs[0]["blue"]},
                     "x_red": sum(r["x"] == "red" for r in rs) / len(rs), "x_blue": sum(r["x"] == "blue" for r in rs) / len(rs),
                     "contacts": st.mean(r["contacts"] for r in rs), "collisions": st.mean(r["collisions"] for r in rs),
                     "failed": sum(bool(r["errors"]) for r in rs)}
    return out


def paired(rows, a, b):
    ra = {r["seed"]: r["red"]["total"] - r["blue"]["total"] for r in rows if r["matchup"] == a}
    rb = {r["seed"]: r["red"]["total"] - r["blue"]["total"] for r in rows if r["matchup"] == b}
    d = [ra[s] - rb[s] for s in ra if s in rb]
    if len(d) < 2:
        return None
    return {"n": len(d), "mean": st.mean(d), "ci95": 1.96 * st.stdev(d) / math.sqrt(len(d))}


def figures(rows, table):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    OUT.mkdir(parents=True, exist_ok=True)
    names = list(table)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    ax = axes[0]
    ax.boxplot([[r["red"]["total"] - r["blue"]["total"] for r in rows if r["matchup"] == n] for n in names],
               labels=[f"{n}\n(n={table[n]['n']})" for n in names])
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylabel("margin red - blue (points)")
    ax.set_title("4-robot matches: margin over sampled robots")
    ax.tick_params(axis="x", labelsize=8)
    ax = axes[1]
    items = [("precision", "#2980b9"), ("cones", "#f39c12"), ("letter_cubes", "#8e44ad"), ("flag", "#27ae60"), ("x_mark", "#7f8c8d")]
    bottom = [0.0] * len(names)
    for key, color in items:
        vals = [table[n]["red"][key] for n in names]
        ax.bar(names, vals, bottom=bottom, color=color, label=key)
        bottom = [a + b for a, b in zip(bottom, vals)]
    ax.set_title("Red points by item (mean)")
    ax.tick_params(axis="x", labelsize=8)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "mc_four.png", dpi=140)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", type=int, default=16)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()
    rows = []
    jobs = [(n, 2000 + s) for s in range(args.seeds) for n in MATCHUPS]     # seed by seed: every matchup advances
    with ProcessPoolExecutor(args.workers) as pool:
        futures = [pool.submit(match, j) for j in jobs]
        for f in as_completed(futures):
            r = f.result()
            rows.append(r)
            print(f"{len(rows):3d}/{len(jobs)} {r['matchup']:18s} seed {r['seed']} d{r['delay']}: red {r['red']['total']:4d} "
                  f"blue {r['blue']['total']:4d} X {r['x']} coll {r['collisions']} {r['errors'] or ''}", flush=True)
            REPORT.write_text(json.dumps({"rows": rows}, indent=1))
    table = summary(rows)
    pairs = {f"{a} - {b}": paired(rows, a, b) for a, b in (("13 vs 12", "12 vs 12"), ("13 X277.8 vs 12", "12 vs 12"),
                                                            ("13 X277.8 vs 12", "13 vs 12"), ("13 X277.8 vs 13", "12 vs 13"))}
    REPORT.write_text(json.dumps({"rows": rows, "table": table, "paired": pairs}, indent=1))
    print("\n== margin red - blue")
    for n, t in table.items():
        print(f"{n:18s} n={t['n']:3d} margin {t['margin']:+6.1f} +-{t['ci95']:5.1f}  win {t['win']:.2f}  worst {t['worst']:+5d}  "
              f"red {t['red']['total']:5.1f} blue {t['blue']['total']:5.1f}  X red {t['x_red']:.2f} blue {t['x_blue']:.2f}  "
              f"coll {t['collisions']:.1f} failed {t['failed']}")
    print("paired:", pairs)
    figures(rows, table)


if __name__ == "__main__":
    main()
