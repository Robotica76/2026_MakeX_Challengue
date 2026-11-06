"""Which red plan and which match of the 4-robot Monte Carlo (results/mc_four.json) scored most, and
which plan is most efficient (mean points per point of spread).

    .venv/bin/python simulation/analysis/plot_mc_efficiency.py
writes reports/mc_four/eficiencia.png
"""

import json
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
PLANS = {"ORDER 12": ("12 vs 12", "12 vs 13"), "ORDER 13": ("13 vs 12",),
         "ORDER 13, X 277.8": ("13 X277.8 vs 12", "13 X277.8 vs 13")}
COLOR = {"ORDER 12": "#7f8c8d", "ORDER 13": "#2980b9", "ORDER 13, X 277.8": "#c0392b"}
ITEMS = (("precision", "Precisión", "#2980b9"), ("cones", "Conos", "#f39c12"), ("letter_cubes", "Letras", "#8e44ad"),
         ("flag", "Banderas", "#27ae60"), ("x_mark", "X", "#7f8c8d"))


def main():
    rows = json.loads((HERE / "results" / "mc_four.json").read_text())["rows"]
    stats = {}
    for plan, ups in PLANS.items():
        pts = [r["red"]["total"] for r in rows if r["matchup"] in ups]
        stats[plan] = {"pts": pts, "mean": st.mean(pts), "sd": st.stdev(pts), "eff": st.mean(pts) / st.stdev(pts),
                       "max": max(pts), "n": len(pts)}
    best = max(rows, key=lambda r: r["red"]["total"])
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.6))
    ax = axes[0]
    for i, (plan, s) in enumerate(stats.items()):
        ax.scatter([i + (k % 7 - 3) * 0.035 for k in range(s["n"])], s["pts"], color=COLOR[plan], alpha=0.65, s=28)
        ax.hlines(s["mean"], i - 0.3, i + 0.3, color="k", lw=2)
        ax.text(i + 0.32, s["mean"], f"{s['mean']:.0f}", va="center", fontsize=10)
    ax.scatter([list(stats).index(next(p for p, u in PLANS.items() if best["matchup"] in u))], [best["red"]["total"]],
               marker="*", s=320, color="gold", edgecolor="k", zorder=5, label=f"Más puntos: {best['red']['total']}")
    ax.set_xticks(range(len(stats)))
    ax.set_xticklabels([f"{p}\n(n={s['n']})" for p, s in stats.items()], fontsize=9)
    ax.set_ylabel("Puntos de la alianza roja por partido")
    ax.set_title("Todos los partidos (línea: promedio)")
    ax.legend(loc="lower right")
    ax = axes[1]
    top = max(stats, key=lambda p: stats[p]["eff"])
    for plan, s in stats.items():
        ax.scatter(s["sd"], s["mean"], s=220, color=COLOR[plan], edgecolor="k" if plan == top else "none", lw=2)
        ax.annotate(f"{plan}\n{s['eff']:.2f} pts por pt de variación", (s["sd"], s["mean"]),
                    textcoords="offset points", xytext=(10, -8), fontsize=8)
    ax.set_xlabel("Variación entre partidos (desviación estándar, puntos)")
    ax.set_ylabel("Puntos promedio")
    ax.set_title(f"Eficiencia: arriba a la izquierda es mejor\nMás eficiente: {top}")
    ax.margins(0.3)
    ax = axes[2]
    x, bottom = 0, 0
    labels = ["Mejor partido"] + list(stats)
    bars = [best["red"]] + [{k: st.mean(r["red"][k] for r in rows if r["matchup"] in PLANS[p]) for k, _, _ in ITEMS} for p in stats]
    bottom = [0.0] * len(bars)
    for key, label, color in ITEMS:
        vals = [b[key] for b in bars]
        ax.bar(range(len(bars)), vals, bottom=bottom, color=color, label=label)
        bottom = [a + b for a, b in zip(bottom, vals)]
    ax.set_xticks(range(len(bars)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title(f"De dónde salen los puntos\nMejor: {best['matchup']}, semilla {best['seed']}")
    ax.set_ylabel("Puntos (antes de penalizaciones)")
    ax.legend(fontsize=8)
    fig.suptitle("Monte Carlo de 80 partidos con 4 robots muestreados: alianza roja", fontsize=13)
    fig.tight_layout()
    fig.savefig(HERE / "reports" / "mc_four" / "eficiencia.png", dpi=140)
    for p, s in stats.items():
        print(p, {k: round(v, 2) for k, v in s.items() if k != "pts"})
    print("best", best["matchup"], best["seed"], best["delay"], best["red"], "blue", best["blue"]["total"], best["x"], best["errors"])


if __name__ == "__main__":
    main()
