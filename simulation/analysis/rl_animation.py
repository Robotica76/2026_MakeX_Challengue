"""Animation of the reinforcement learning on the 2 vs 2 game (strategy_game.py): every 100 iterations
the policy's choices and a Monte Carlo of its greedy plan against the six opponent styles.

    .venv/bin/python simulation/analysis/rl_animation.py
writes reports/rl_strategy_robust/aprendizaje.gif
"""

import io
import random
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

from rl_strategy import CHOICES, ROLES, margin, plans, train  # noqa: E402
from strategy_game import ARCHETYPES  # noqa: E402

OUT = HERE / "reports" / "rl_strategy_robust" / "aprendizaje.gif"
AIMS = ("adaptive", "adaptive")
NAMES = {"auto": "automático", "manual": "manual", "final": "final", "x_time": "hora del X"}
GAMES = 40                                  # Monte Carlo matches per style and frame


def monte_carlo(red, seed):
    rows = {}
    for name, opp in ARCHETYPES.items():
        rows[name] = [margin(red, opp, seed + k, AIMS)[0] for k in range(GAMES)]
    return rows


def main():
    frames, history = [], []
    current = monte_carlo(ARCHETYPES["current (ours)"], 777_000)
    base = st.mean(v for r in current.values() for v in r)

    def snapshot(it, pol):
        red = plans(pol.greedy())
        mc = monte_carlo(red, 900_000 + it)
        allm = [v for r in mc.values() for v in r]
        history.append((it, st.mean(allm), sum(v > 0 for v in allm) / len(allm)))
        fig = plt.figure(figsize=(12, 6.6))
        grid = fig.add_gridspec(2, 4, height_ratios=(1.05, 1))
        ax = fig.add_subplot(grid[0, :2])
        ax.plot([h[0] for h in history], [h[1] for h in history], color="#c0392b", lw=2, label="plan aprendido")
        ax.axhline(base, color="#7f8c8d", ls="--", label=f"plan actual ({base:+.0f})")
        ax.axhline(0, color="k", lw=0.5)
        ax.set_xlim(0, 4000)
        ax.set_ylim(min(-150, base - 50), 400)
        ax.set_xlabel("iteración (64 partidos cada una)")
        ax.set_ylabel("margen medio (puntos)")
        ax.set_title(f"Iteración {it}: {it * 64:,} partidos de entrenamiento".replace(",", " "))
        ax.legend(loc="lower right", fontsize=8)
        ax = fig.add_subplot(grid[0, 2:])
        ax.hist(allm, bins=range(-500, 901, 50), color="#2980b9")
        ax.axvline(0, color="k", lw=0.8)
        ax.axvline(st.mean(allm), color="#c0392b", lw=2)
        ax.set_xlim(-500, 900)
        ax.set_ylim(0, 90)
        ax.set_xlabel("margen del partido (nosotros − rival)")
        ax.set_title(f"Monte Carlo del plan actual de la política: {len(allm)} partidos, gana {history[-1][2]:.0%}")
        for c, (name, opts) in enumerate(CHOICES):
            ax = fig.add_subplot(grid[1, c])
            w = 0.4
            for k, (role, color) in enumerate(zip(ROLES, ("#c0392b", "#e59866"))):
                ax.bar([i + (k - 0.5) * w for i in range(len(opts))], pol.probs((role, name)), w, color=color,
                       label="nuestro" if k == 0 else "compañero")
            ax.set_xticks(range(len(opts)))
            ax.set_xticklabels([str(o) or "-" for o in opts], rotation=70, fontsize=7)
            ax.set_ylim(0, 1)
            ax.set_title(f"Probabilidad: {NAMES[name]}", fontsize=9)
            if c == 0:
                ax.legend(fontsize=7)
        l, p = red
        fig.suptitle(f"Plan: nuestro {l.auto or '-'}/{l.manual}/{l.final}  ·  compañero {p.auto or '-'}/{p.manual}/{p.final}", fontsize=12)
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, dpi=75)
        plt.close(fig)
        buf.seek(0)
        frames.append(Image.open(buf).convert("RGB").quantize(colors=96))

    train(4000, 64, 0.08, 0.002, "adaptive", seed=1, opp_aims=("adaptive",), on_snapshot=snapshot)
    frames[0].save(OUT, save_all=True, append_images=frames[1:] + [frames[-1]] * 12, duration=280, loop=0, optimize=True)
    print(OUT, len(frames), round(OUT.stat().st_size / 1e6, 1), "MB", "final", history[-1], "base", round(base, 1))


if __name__ == "__main__":
    main()
