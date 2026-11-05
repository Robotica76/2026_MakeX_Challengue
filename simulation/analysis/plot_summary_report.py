"""Summary figure of the strategy simulations (values from the detailed and the 2 vs 2 runs).

    .venv/bin/python simulation/analysis/plot_summary_report.py
writes simulation/analysis/reports/summary/summary.png
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "reports" / "summary"

# detailed simulator runs (docs/07_strategy/montecarlo_strategy.md)
CLIFF = [("0", 10), ("50 E", 9), ("100 E", 10), ("50 N", 10), ("100 N", 11), ("150 S", 7), ("150 N", 0),
         ("150 E", 0), ("300 N", 0)]
TWO = [("nobody moves", 420, 280), ("blue twin moves\nits fortress 190 mm", 320, 220),
       ("we move ours\n190 mm north", 310, 310)]
ROUTES = [("13 X12, table low", 443), ("124", 427), ("123", 423), ("1234", 423), ("12 X12, deny (current)", 410),
          ("1243", 407)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    ax = axes[0][0]
    ax.bar([c[0] for c in CLIFF], [c[1] for c in CLIFF],
           color=["#27ae60" if v >= 9 else "#f39c12" if v > 0 else "#c0392b" for _, v in CLIFF])
    ax.set_title("Our fixed-aim shots (13) in the blue fortress when it is moved (mm, direction)")
    ax.set_ylabel("balls in")
    ax.axhline(10, color="k", lw=0.5, ls=":")
    ax = axes[0][1]
    x = range(len(TWO))
    ax.bar([i - 0.2 for i in x], [t[1] for t in TWO], 0.4, color="#c0392b", label="red (ours)")
    ax.bar([i + 0.2 for i in x], [t[2] for t in TWO], 0.4, color="#2471a3", label="blue twin")
    for i, t in enumerate(TWO):
        ax.text(i - 0.2, t[1] + 5, str(t[1]), ha="center")
        ax.text(i + 0.2, t[2] + 5, str(t[2]), ha="center")
    ax.set_xticks(list(x))
    ax.set_xticklabels([t[0] for t in TWO], fontsize=9)
    ax.set_title("Two identical robots, detailed simulator (280 s)")
    ax.set_ylabel("points")
    ax.legend()
    ax = axes[1][0]
    ax.barh([r[0] for r in ROUTES][::-1], [r[1] for r in ROUTES][::-1], color="#8e44ad")
    for i, r in enumerate(ROUTES[::-1]):
        ax.text(r[1] + 3, i, str(r[1]), va="center")
    ax.set_xlim(350, 460)
    ax.set_title("Route Monte Carlo: whole matches of the best automatic orders (mean)")
    ax.set_xlabel("points")
    ax = axes[1][1]
    plans = []
    for tag, label in (("", "learned\n(our aim fixed)"), ("_robust", "learned\n(our aim adaptive)")):
        path = HERE / "results" / f"rl_strategy{tag}.json"
        if path.exists():
            d = json.loads(path.read_text())
            ev = d["evals"]
            learned_keys = [k for k in ev if k.startswith("learned")]
            current_keys = [k for k in ev if k.startswith("current")]
            plans.append((label, [min(r["margin"] for r in ev[k].values()) for k in learned_keys],
                          [sum(r["margin"] for r in ev[k].values()) / len(ev[k]) for k in learned_keys]))
            if not tag:
                plans.insert(0, ("current plan", [min(r["margin"] for r in ev[k].values()) for k in current_keys],
                                 [sum(r["margin"] for r in ev[k].values()) / len(ev[k]) for k in current_keys]))
    x = range(len(plans))
    ax.bar([i - 0.2 for i in x], [sum(p[2]) / len(p[2]) for p in plans], 0.4, color="#2980b9", label="mean vs the 6 styles")
    ax.bar([i + 0.2 for i in x], [min(p[1]) for p in plans], 0.4, color="#e74c3c", label="worst style")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xticks(list(x))
    ax.set_xticklabels([p[0] for p in plans])
    ax.set_ylabel("point margin (ours - theirs)")
    ax.set_title("2 vs 2 strategy game: Monte Carlo of each alliance plan")
    ax.legend()
    fig.suptitle("Storm Breaker 2026 - simulation results (ROBOTICA 76)", fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / "summary.png", dpi=130)
    print("figure:", OUT / "summary.png")


if __name__ == "__main__":
    main()
