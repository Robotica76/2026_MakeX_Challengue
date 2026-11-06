"""Reinforcement learning of the 2 vs 2 strategy on strategy_game.py (self-play policy gradient), then
Monte Carlo evaluation against opponent styles and an exploitability check.

Policy: for each robot of the alliance (lower = ours, upper = partner), independent softmax choices of
the automatic order, the manual plan, the final plan and the time of the last shots at the X mark
(11 x 12 x 10 x 4 per robot: ~28 million alliance plans). REINFORCE with a batch-mean baseline and
an entropy bonus; reward = (our points - their points) / 100. Opponents: the current policy
(self-play), snapshots of earlier policies (fictitious play) and the styles in ARCHETYPES; their aim
is fixed (odometry) or adaptive (vision / driver) at random, ours is fixed (storm_breaker_2026 aims
at fixed coordinates) unless --our-aim adaptive.

    .venv/bin/python simulation/analysis/rl_strategy.py --iterations 3000
Writes simulation/analysis/results/rl_strategy.json and reports/rl_strategy/*.png.
"""

import argparse
import json
import math
import random
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from strategy_game import (ARCHETYPES, AUTO_PLANS, CODES, FINAL_PLANS, MANUAL_PLANS, X_TIMES, Plan,  # noqa: E402
                           play)

CHOICES = [("auto", AUTO_PLANS), ("manual", MANUAL_PLANS), ("final", FINAL_PLANS), ("x_time", X_TIMES)]
ROLES = ("lower", "upper")
OUT = HERE / "reports" / "rl_strategy"
REPORT = HERE / "results" / "rl_strategy.json"


class Policy:
    def __init__(self):
        self.logits = {(role, name): [0.0] * len(opts) for role in ROLES for name, opts in CHOICES}

    def probs(self, key):
        z = self.logits[key]
        m = max(z)
        e = [math.exp(v - m) for v in z]
        s = sum(e)
        return [v / s for v in e]

    def sample(self, rng):
        picks = {}
        for key in self.logits:
            p = self.probs(key)
            picks[key] = rng.choices(range(len(p)), weights=p)[0]
        return picks

    def greedy(self):
        return {key: max(range(len(z)), key=lambda i: z[i]) for key, z in self.logits.items()}

    def copy(self):
        q = Policy()
        q.logits = {k: list(v) for k, v in self.logits.items()}
        return q


def plans(picks):
    out = []
    for role in ROLES:
        kw = {name: opts[picks[(role, name)]] for name, opts in CHOICES}
        out.append(Plan(kw["auto"], kw["manual"], kw["final"], kw["x_time"]))
    return tuple(out)


def describe(picks):
    lines = []
    for role, plan in zip(("ours (lower)", "partner (upper)"), plans(picks)):
        def words(codes):
            return ", ".join(CODES[c] for c in codes) or "nothing"
        lines.append(f"{role}: auto [{plan.auto or '-'}] {words(plan.auto)} | manual [{plan.manual}] {words(plan.manual)} | "
                     f"final [{plan.final}] {words(plan.final)} | X at {plan.x_time:g} s")
    return lines


def margin(red, blue, seed, aims):
    m = play(red, blue, seed=seed, aims=aims)
    return m["red"]["total"] - m["blue"]["total"], m


def train(iterations, batch, lr, entropy, our_aim, seed=1, opp_aims=("fixed", "adaptive")):
    rng = random.Random(seed)
    pol = Policy()
    pool, curve = [], []
    arche = list(ARCHETYPES.values())
    for it in range(iterations):
        samples, rewards = [], []
        for _ in range(batch):
            picks = pol.sample(rng)
            u = rng.random()
            if u < 0.4:
                opp = plans(pol.sample(rng))
            elif u < 0.7 and pool:
                opp = plans(rng.choice(pool))
            else:
                opp = rng.choice(arche)
            aims = (our_aim, rng.choice(opp_aims))
            r, _ = margin(plans(picks), opp, rng.randrange(1 << 30), aims)
            samples.append(picks)
            rewards.append(r / 100.0)
        base = sum(rewards) / batch
        for key, z in pol.logits.items():
            p = pol.probs(key)
            grad = [0.0] * len(z)
            for picks, r in zip(samples, rewards):
                a = r - base
                for i in range(len(z)):
                    grad[i] += a * ((1.0 if picks[key] == i else 0.0) - p[i])
            ent = [-p[i] * (math.log(p[i] + 1e-12) - sum(q * math.log(q + 1e-12) for q in p)) for i in range(len(z))]
            for i in range(len(z)):
                z[i] += lr * (grad[i] / batch + entropy * ent[i])
        if it % 100 == 99:
            pool.append(pol.greedy())
            g = plans(pol.greedy())
            ev = [margin(g, a, 10_000 + k, (our_aim, "fixed"))[0] for a in arche for k in range(40)]
            curve.append((it + 1, sum(ev) / len(ev), base * 100))
            print(f"iteration {it + 1:5d}: mean margin vs styles {curve[-1][1]:7.1f}, batch {base * 100:7.1f}", flush=True)
    return pol, curve


def evaluate(red, n, our_aim, opp_aim, seed0=50_000):
    rows = {}
    for name, opp in ARCHETYPES.items():
        ms = [margin(red, opp, seed0 + k, (our_aim, opp_aim)) for k in range(n)]
        rows[name] = {"margin": st.mean(m for m, _ in ms), "win": sum(m > 0 for m, _ in ms) / n,
                      "ours": st.mean(x["red"]["total"] for _, x in ms), "theirs": st.mean(x["blue"]["total"] for _, x in ms),
                      "items": {k: round(st.mean(x["red"].get(k, 0) for _, x in ms), 1)
                                for k in ("precision", "bonus_balls", "cones", "letters", "flag", "x_mark", "penalties")}}
    return rows


def best_response(target, iterations, batch, lr, our_aim, seed=7):
    """How much an opponent that learns against `target` (fixed) can win: exploitability."""
    rng = random.Random(seed)
    pol = Policy()
    for _ in range(iterations):
        samples, rewards = [], []
        for _ in range(batch):
            picks = pol.sample(rng)
            r, _ = margin(plans(picks), target, rng.randrange(1 << 30), ("fixed", our_aim))
            samples.append(picks)
            rewards.append(r / 100.0)
        base = sum(rewards) / batch
        for key, z in pol.logits.items():
            p = pol.probs(key)
            for i in range(len(z)):
                z[i] += lr * sum((r - base) * ((1.0 if s[key] == i else 0.0) - p[i]) for s, r in zip(samples, rewards)) / batch
    br = plans(pol.greedy())
    ms = [margin(br, target, 90_000 + k, ("fixed", our_aim))[0] for k in range(2000)]
    return pol.greedy(), st.mean(ms)


def figures(curve, evals, learned, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot([c[0] for c in curve], [c[1] for c in curve], "-", color="#c0392b", label="greedy policy vs the styles")
    ax.plot([c[0] for c in curve], [c[2] for c in curve], "-", color="#7f8c8d", alpha=0.6, label="training batch")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("iteration (64 matches each)")
    ax.set_ylabel("point margin (ours - theirs)")
    ax.set_title("Self-play policy gradient on the 2 vs 2 strategy game")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "1_learning_curve.png", dpi=140)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    names = list(next(iter(evals.values())).keys())
    width = 0.8 / len(evals)
    for k, (label, rows) in enumerate(evals.items()):
        ax.bar([i + k * width for i in range(len(names))], [rows[n]["margin"] for n in names], width, label=label)
    ax.set_xticks([i + 0.4 - width / 2 for i in range(len(names))])
    ax.set_xticklabels(names, fontsize=8)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel("mean point margin (2000+ matches)")
    ax.set_title("Monte Carlo: our alliance plan vs opponent styles")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "2_margin_vs_styles.png", dpi=140)
    plt.close(fig)
    fig, axes = plt.subplots(2, 4, figsize=(14, 6))
    for r, role in enumerate(ROLES):
        for c, (name, opts) in enumerate(CHOICES):
            p = learned.probs((role, name))
            ax = axes[r][c]
            ax.bar(range(len(opts)), p, color="#2980b9")
            ax.set_xticks(range(len(opts)))
            ax.set_xticklabels([str(o) or "-" for o in opts], rotation=60, fontsize=7)
            ax.set_title(f"{'ours' if role == 'lower' else 'partner'}: {name}", fontsize=9)
    fig.suptitle("Learned policy (probability of each choice)")
    fig.tight_layout()
    fig.savefig(out / "3_policy.png", dpi=140)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iterations", type=int, default=3000)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=0.08)
    ap.add_argument("--entropy", type=float, default=0.002)
    ap.add_argument("--our-aim", default="fixed", choices=("fixed", "adaptive"))
    ap.add_argument("--eval", type=int, default=3000, help="Monte Carlo matches per opponent style")
    ap.add_argument("--opp-aim", default="mix", choices=("mix", "fixed", "adaptive"),
                    help="opponents' aim during training")
    ap.add_argument("--tag", default="", help="suffix for the report and figure folder")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    global OUT, REPORT
    if args.tag:
        OUT = OUT.with_name(OUT.name + "_" + args.tag)
        REPORT = REPORT.with_name(REPORT.stem + "_" + args.tag + ".json")
    opp_aims = ("fixed", "adaptive") if args.opp_aim == "mix" else (args.opp_aim,)
    pol, curve = train(args.iterations, args.batch, args.lr, args.entropy, args.our_aim, seed=args.seed,
                       opp_aims=opp_aims)
    best = pol.greedy()
    learned = plans(best)
    print("\n== learned alliance plan")
    print("\n".join(describe(best)))
    evals = {}
    for label, red, opp_aim in (("learned, opponents aim fixed", learned, "fixed"),
                                ("learned, opponents aim adaptive", learned, "adaptive"),
                                ("current plan, opponents aim fixed", ARCHETYPES["current (ours)"], "fixed"),
                                ("current plan, opponents aim adaptive", ARCHETYPES["current (ours)"], "adaptive")):
        evals[label] = evaluate(red, args.eval, args.our_aim, opp_aim)
    print("\n== Monte Carlo (mean margin / win rate / our points)")
    for label, rows in evals.items():
        print(label)
        for name, r in rows.items():
            print(f"   vs {name:16s} margin {r['margin']:7.1f}  win {r['win']:.2f}  ours {r['ours']:6.1f}  theirs {r['theirs']:6.1f}  {r['items']}")
    br, exploit = best_response(learned, 600, 48, 0.1, args.our_aim)
    cur_br, cur_exploit = best_response(ARCHETYPES["current (ours)"], 600, 48, 0.1, args.our_aim)
    print(f"\nexploitability: an opponent trained against the learned plan wins by {exploit:.1f} "
          f"({plans(br)[0].label()} / {plans(br)[1].label()}); against the current plan by {cur_exploit:.1f} "
          f"({plans(cur_br)[0].label()} / {plans(cur_br)[1].label()})")
    figures(curve, evals, pol, OUT)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"learned": [p.__dict__ for p in learned], "describe": describe(best),
                                  "curve": curve, "evals": evals, "exploitability": exploit,
                                  "best_response": [p.__dict__ for p in plans(br)],
                                  "current_exploitability": cur_exploit,
                                  "current_best_response": [p.__dict__ for p in plans(cur_br)]}, indent=1))
    print("report:", REPORT.relative_to(HERE.parents[1]), "| figures:", OUT.relative_to(HERE.parents[1]))


if __name__ == "__main__":
    main()
