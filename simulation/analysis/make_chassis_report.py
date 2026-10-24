"""Builds the Monte Carlo report of chassis.py: runs the scenarios, draws the figures
and writes reports/chassis_montecarlo/README.md (committed, unlike results/).
The README holds the report in Spanish and in English; each language has its own
set of figures (figures/es, figures/en).

    .venv/bin/pip install -r simulation/analysis/requirements.txt   # matplotlib
    .venv/bin/python simulation/analysis/make_chassis_report.py      # ~3 min on 6 cores
    .venv/bin/python simulation/analysis/make_chassis_report.py --trials 60   # quicker draft

Same seed -> same numbers. The report text quotes the computed values, so re-running
after changing montecarlo_config*.json updates tables, figures and text in both
languages.
"""

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import montecarlo_chassis as mc  # noqa: E402

OUT = HERE / "reports" / "chassis_montecarlo"
FIG = OUT / "figures"
TIGHT = {"TOL_CM": 0.3, "TOL_DEGREES": 0.5}
LANGS = ("es", "en")

# Reference data-viz palette (dataviz skill, references/palette.md), light surface.
# Colour follows the scenario everywhere; slots 1-2 (blue, orange) are the pair used
# in two-series scatter plots, which is the all-pairs-safe range of the palette.
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"

SCENARIOS = [
    # key, config file, chassis.py overrides, colour, marker, shown in figures
    ("asis", "montecarlo_config.json", {}, ORANGE, "o", True),
    ("A", "montecarlo_config.json", TIGHT, AQUA, "s", True),
    ("B", "montecarlo_config.json", dict(TIGHT, STRAFE_FACTOR=1.075), YELLOW, "D", True),
    ("C", "montecarlo_config_calibrated.json", TIGHT, BLUE, "^", True),
    ("D", "montecarlo_config_calibrated.json", TIGHT, INK_2, "v", False),
]

# ---------------------------------------------------------------- language
STR = {
    "es": {
        "scenario": {"asis": "chassis.py tal cual", "A": "A: tolerancias finas",
                     "B": "B: A + STRAFE_FACTOR 1.075", "C": "C: A + robot calibrado",
                     "D": "D: C sin GYRO_SCALE"},
        "ecdf_drive_title": "Avanzar, retroceder, lateral y diagonal",
        "ecdf_turn_title": "Giros de 90°",
        "ecdf_drive_x": "Error de posición por movimiento (cm)",
        "ecdf_turn_x": "Error de orientación por giro (°)",
        "ecdf_y": "Movimientos con error ≤ x",
        "tolerance": "tolerancia",
        "bounds_title": "Pasa un movimiento si su cota inferior llega a la meta",
        "bounds_x": "Cota inferior 95 % de la tasa de movimientos dentro de tolerancia",
        "goal": "meta",
        "sens_drive": "Movimientos: peor error de posición",
        "sens_turn": "Giros: peor error de orientación",
        "sens_x": "|ρ de Spearman| con el error (signo en la etiqueta)",
        "end_title": "Punto final real",
        "end_x": "Desviación perpendicular al movimiento (cm)",
        "end_y": "Corto (−) / largo (+) respecto al objetivo (cm)",
        "trail_x": "x en la pista desde el inicio (cm)",
        "trail_y": "y en la pista desde el inicio (cm)",
        "ideal": "robot ideal",
        "move_head": "| Movimiento | Tolerancia | Dentro / total | Cota inf. 95 % | Resultado | Error medio | p95 | Máx. | Tiempo medio |",
        "summary_head": "| Escenario | Movimientos que pasan | Peor p95 avance/lateral | Peor p95 giro | Rutina completa (media) |",
        "pass": "PASA", "fail": "FALLA",
    },
    "en": {
        "scenario": {"asis": "chassis.py as is", "A": "A: tight tolerances",
                     "B": "B: A + STRAFE_FACTOR 1.075", "C": "C: A + calibrated robot",
                     "D": "D: C without GYRO_SCALE"},
        "ecdf_drive_title": "Forward, backward, strafe and diagonal",
        "ecdf_turn_title": "90° turns",
        "ecdf_drive_x": "Position error per move (cm)",
        "ecdf_turn_x": "Heading error per turn (°)",
        "ecdf_y": "Moves with error ≤ x",
        "tolerance": "tolerance",
        "bounds_title": "A move passes when its lower bound reaches the goal",
        "bounds_x": "95% lower bound of the in-tolerance rate",
        "goal": "goal",
        "sens_drive": "Moves: worst position error",
        "sens_turn": "Turns: worst heading error",
        "sens_x": "|Spearman ρ| with the error (sign on the label)",
        "end_title": "Real end point",
        "end_x": "Deviation across the move (cm)",
        "end_y": "Short (−) / long (+) of the target (cm)",
        "trail_x": "field x from the start (cm)",
        "trail_y": "field y from the start (cm)",
        "ideal": "ideal robot",
        "move_head": "| Move | Tolerance | In tolerance / total | 95% lower bound | Result | Mean error | p95 | Max | Mean time |",
        "summary_head": "| Scenario | Moves that pass | Worst p95 drive/strafe | Worst p95 turn | Full routine (mean) |",
        "pass": "PASS", "fail": "FAIL",
    },
}
_lang = "es"


def set_lang(lang):
    global _lang
    _lang = lang


def T(key):
    return STR[_lang][key]


def label(key):
    return T("scenario")[key]


def num(x, d=2):
    s = f"{x:.{d}f}"
    return s.replace(".", ",") if _lang == "es" else s


def pct(x, d=1):
    """0.99 -> '99,0 %' (es) / '99.0%' (en)."""
    return f"{num(x * 100, d)} %" if _lang == "es" else f"{num(x * 100, d)}%"


def signed(x):
    return ("+" if x > 0 else "") + num(x)


def deg(x):
    return f"{num(x, 1)}°"


def cm(x):
    return f"{num(x, 0 if x == int(x) else 1)} cm"


# ---------------------------------------------------------------- figures
def style_axes(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def new_figure(width, height, cols=1, **kw):
    fig, axes = plt.subplots(1, cols, figsize=(width, height), facecolor=SURFACE, **kw)
    for ax in (axes if cols > 1 else [axes]):
        style_axes(ax)
    return fig, axes


def save(fig, name):
    folder = FIG / _lang
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, dpi=150, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    return f"figures/{_lang}/{name}"


def errors(results, kind):
    return [m["error"] for r in results for m in r["moves"] if m["kind"] == kind]


def percent_axis(axis):
    axis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: pct(v, 0)))


def fig_ecdf(runs, criteria):
    fig, (a1, a2) = new_figure(10, 4.2, cols=2)
    panels = ((a1, "drive", cm(criteria["drive_error_cm"]), criteria["drive_error_cm"],
               T("ecdf_drive_x"), T("ecdf_drive_title")),
              (a2, "turn", deg(criteria["turn_error_deg"]), criteria["turn_error_deg"],
               T("ecdf_turn_x"), T("ecdf_turn_title")))
    for ax, kind, tol_text, tol, xlabel, title in panels:
        xmax = 0
        for key, *_rest, show in SCENARIOS:
            if not show:
                continue
            e = sorted(errors(runs[key]["results"], kind))
            y = [(i + 1) / len(e) for i in range(len(e))]
            ax.step(e, y, where="post", color=runs[key]["color"], linewidth=2, label=label(key))
            xmax = max(xmax, e[-1])
        ax.axvline(tol, color=INK, linewidth=1.2, linestyle="--")
        ax.axhline(criteria["required_rate"], color=INK_2, linewidth=1, linestyle=":")
        ax.text(tol, 0.03, f" {T('tolerance')} {tol_text}", color=INK, fontsize=8.5, va="bottom")
        ax.text(xmax * 0.02, criteria["required_rate"] + 0.01, pct(criteria["required_rate"], 0),
                color=INK_2, fontsize=8.5, va="bottom")
        ax.set_xlim(0, xmax * 1.12)
        ax.set_ylim(0, 1.02)
        ax.set_xlabel(xlabel, color=INK, fontsize=9.5)
        ax.set_title(title, color=INK, fontsize=10.5, loc="left")
        percent_axis(ax.yaxis)
    a1.set_ylabel(T("ecdf_y"), color=INK, fontsize=9.5)
    handles, labels = a1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=9, labelcolor=INK,
               bbox_to_anchor=(0.5, -0.06))
    return save(fig, "ecdf_errors.png")


def fig_lower_bounds(runs, criteria):
    rows = [r["move"] for r in runs["asis"]["rows"]]
    fig, ax = new_figure(9, 5.2)
    shown = [s for s in SCENARIOS if s[-1]]
    offsets = {s[0]: (i - (len(shown) - 1) / 2) * 0.17 for i, s in enumerate(shown)}
    for key, _cfg, _ov, color, marker, _show in shown:
        by_move = {r["move"]: r for r in runs[key]["rows"]}
        ys = [i + offsets[key] for i in range(len(rows))]
        ax.scatter([by_move[m]["lower95"] for m in rows], ys, color=color, marker=marker, s=46,
                   edgecolors=SURFACE, linewidths=1.2, label=label(key), zorder=3)
    ax.axvline(criteria["required_rate"], color=INK, linewidth=1.2, linestyle="--")
    ax.text(criteria["required_rate"], -0.9, f" {T('goal')} {pct(criteria['required_rate'], 0)}",
            color=INK, fontsize=8.5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows)
    ax.invert_yaxis()
    ax.set_xlim(-0.02, 1.02)
    percent_axis(ax.xaxis)
    ax.set_xlabel(T("bounds_x"), color=INK, fontsize=9.5)
    ax.set_title(T("bounds_title"), color=INK, fontsize=10.5, loc="left")
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, -0.25), ncol=4, frameon=False, fontsize=9,
              labelcolor=INK)
    return save(fig, "lower_bound_per_move.png")


def fig_sensitivity(results):
    fig, axes = new_figure(10, 3.6, cols=2)
    for ax, kind, title in ((axes[0], "drive", T("sens_drive")), (axes[1], "turn", T("sens_turn"))):
        sens = mc.sensitivity(results, kind)[:6][::-1]
        names = [n for n, _ in sens]
        rhos = [r for _, r in sens]
        ax.barh(range(len(sens)), [abs(r) for r in rhos], color=BLUE, height=0.6)
        for i, rho in enumerate(rhos):
            ax.text(abs(rho) + 0.02, i, signed(rho), va="center", color=INK, fontsize=8.5)
        ax.set_yticks(range(len(sens)))
        ax.set_yticklabels(names, fontsize=8.5)
        ax.set_xlim(0, 1.15)
        ax.set_xlabel(T("sens_x"), color=INK, fontsize=9)
        ax.set_title(title, color=INK, fontsize=10.5, loc="left")
    fig.tight_layout()
    return save(fig, "sensitivity.png")


def fig_endpoints(runs, criteria):
    fig, axes = new_figure(10, 4.6, cols=2)
    tol = criteria["drive_error_cm"]
    for ax, move, along, across in ((axes[0], "forward 60", "real_forward_cm", "real_right_cm"),
                                    (axes[1], "right 30", "real_right_cm", "real_forward_cm")):
        lim = 0
        for key in ("asis", "C"):
            run = runs[key]
            ms = [m for r in run["results"] for m in r["moves"] if m["move"] == move]
            cmd = 60 if move == "forward 60" else 30
            xs = [m[across] for m in ms]                 # deviation across the move
            ys = [m[along] - cmd for m in ms]            # short (-) / long (+)
            ax.scatter(xs, ys, s=16, color=run["color"], marker=run["marker"], alpha=0.75,
                       edgecolors="none", label=label(key))
            lim = max(lim, max(map(abs, xs + ys)))
        ax.add_patch(plt.Circle((0, 0), tol, fill=False, color=INK, linewidth=1.2, linestyle="--"))
        ax.text(tol * 0.72, tol * 0.72, cm(tol), color=INK, fontsize=8.5)
        ax.plot([0], [0], marker="+", color=INK, markersize=10)
        lim = max(lim * 1.1, tol * 1.6)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xlabel(T("end_x"), color=INK, fontsize=9)
        ax.set_ylabel(T("end_y"), color=INK, fontsize=9)
        ax.set_title(f"{T('end_title')}: {move} cm", color=INK, fontsize=10.5, loc="left")
    axes[0].legend(loc="upper left", frameon=False, fontsize=8.5, labelcolor=INK)
    fig.tight_layout()
    return save(fig, "end_points.png")


def fig_trails(runs, ideal_trail, start):
    fig, axes = new_figure(10, 5, cols=2, sharey=True)
    for ax, key in zip(axes, ("asis", "C")):
        run = runs[key]
        shown = run["results"][:60]
        for r in shown:
            if r.get("trail"):
                xs = [(p[0] - start[0]) / 10 for p in r["trail"]]
                ys = [(p[1] - start[1]) / 10 for p in r["trail"]]
                ax.plot(xs, ys, color=run["color"], linewidth=0.8, alpha=0.35)
        xs = [(p[0] - start[0]) / 10 for p in ideal_trail]
        ys = [(p[1] - start[1]) / 10 for p in ideal_trail]
        ax.plot(xs, ys, color=INK, linewidth=1.4, label=T("ideal"))
        ax.plot([0], [0], marker="o", color=INK, markersize=6)
        ax.set_aspect("equal")
        ax.set_xlabel(T("trail_x"), color=INK, fontsize=9)
        ax.set_title(f"{label(key)}: {len(shown)} robots", color=INK, fontsize=10.5, loc="left")
        ax.legend(loc="upper right", frameon=False, fontsize=8.5, labelcolor=INK)
    axes[0].set_ylabel(T("trail_y"), color=INK, fontsize=9)
    fig.tight_layout()
    return save(fig, "trajectories.png")


def draw_figures(runs, criteria, ideal_trail, start):
    return {
        "ecdf": fig_ecdf(runs, criteria),
        "bounds": fig_lower_bounds(runs, criteria),
        "endpoints": fig_endpoints(runs, criteria),
        "sensitivity": fig_sensitivity(runs["asis"]["results"]),
        "trails": fig_trails(runs, ideal_trail, start),
    }


# ---------------------------------------------------------------- tables
def move_table(rows):
    lines = [T("move_head"), "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        tol = cm(r["tolerance"]) if r["kind"] == "drive" else deg(r["tolerance"])
        verdict = T("pass") if r["verdict"] == "PASS" else T("fail")
        lines.append(f"| {r['move']} | {tol} | {r['pass']}/{r['n']} | {pct(r['lower95'])} | **{verdict}** |"
                     f" {num(r['mean'])} | {num(r['p95'])} | {num(r['max'])} | {num(r['duration'], 1)} s |")
    return "\n".join(lines)


def scenario_summary(runs):
    lines = [T("summary_head"), "| --- | --- | --- | --- | --- |"]
    for key, *_ in SCENARIOS:
        rows = runs[key]["rows"]
        ok = sum(r["verdict"] == "PASS" for r in rows)
        d = max(r["p95"] for r in rows if r["kind"] == "drive")
        t = max(r["p95"] for r in rows if r["kind"] == "turn")
        dur = sum(r["duration_s"] for r in runs[key]["results"]) / len(runs[key]["results"])
        lines.append(f"| {label(key)} | {ok}/{len(rows)} | {num(d)} cm | {num(t)}° | {num(dur, 1)} s |")
    return "\n".join(lines)


def add_durations(run):
    for row in run["rows"]:
        ds = [m["duration_s"] for r in run["results"] for m in r["moves"] if m["move"] == row["move"]]
        row["duration"] = sum(ds) / len(ds)


# ---------------------------------------------------------------- report text
def facts(runs, cfg_base, cfg_cal, trials, elapsed):
    """Numbers quoted in the text, computed once; formatted per language later."""
    asis, C, D = runs["asis"], runs["C"], runs["D"]
    ideal = [r for r in runs["ideal"]["rows"] if r["kind"] == "drive"]
    return {
        "c": cfg_base["criteria"], "seed": cfg_base["seed"], "trials": trials,
        "minutes": round(elapsed / 60), "rc": cfg_cal["ranges"],
        "ideal_short": min(r["mean"] for r in ideal), "ideal_short_max": max(r["mean"] for r in ideal),
        "arrived": min(r["arrived"] for r in asis["rows"]),
        "rho_strafe": dict(mc.sensitivity(asis["results"], "drive"))["slip_strafe"],
        "rho_gyro": dict(mc.sensitivity(asis["results"], "turn"))["gyro_scale"],
        "c_drive_max": max(r["max"] for r in C["rows"] if r["kind"] == "drive"),
        "c_drive_lb": min(r["lower95"] for r in C["rows"] if r["kind"] == "drive"),
        "c_turn_lb": min(r["lower95"] for r in C["rows"] if r["kind"] == "turn"),
        "d_turn_ok": sum(r["verdict"] == "PASS" for r in D["rows"] if r["kind"] == "turn"),
        "t_asis": sum(r["duration_s"] for r in asis["results"]) / trials,
        "t_c": sum(r["duration_s"] for r in C["results"]) / trials,
        "n_min": mc.trials_needed(cfg_base["criteria"]["required_rate"], cfg_base["criteria"]["confidence"]),
    }


GYRO_CODE = """```python
GYRO_SCALE = 1.0   # real degrees / gyro degrees, from the 10-turn test (calibration step 5)

# in Odometry.update():
w = (read_gyro_z() - self.gyro_bias) * GYRO_SIGN * GYRO_SCALE
```"""


def text_es(runs, figs, f):
    c, rc = f["c"], f["rc"]
    return f"""# Reporte Monte Carlo: robustez del control del chasis

Estudio de `software/controls/drivetrain/chassis.py` en el simulador 2D
(`simulation/field2d`) con {f['trials']} robots simulados por escenario, cada uno con
errores distintos de ruedas, motores, deslizamiento, giroscopio y encoders.
Generado el {date.today():%Y-%m-%d} por `simulation/analysis/make_chassis_report.py`
(semilla {f['seed']}, {f['minutes']} min). Volver a correrlo reproduce estos números.

## Resumen

**Requisito:** error ≤ {cm(c['drive_error_cm'])} por movimiento en más del
{pct(c['required_rate'], 0)} de los movimientos, con {pct(c['confidence'], 0)} de confianza.
Para los giros, que no tenían requisito, se usa {deg(c['turn_error_deg'])}, la tolerancia
actual de `chassis.py`.

{scenario_summary(runs)}

1. **`chassis.py` tal cual no cumple** en ninguno de los 10 tipos de movimiento.
2. **Las tolerancias están en el límite del requisito.** `drive()` se detiene en cuanto
   está a menos de `TOL_CM = 1.0` cm, así que un robot ideal ya termina
   {num(f['ideal_short'])}–{num(f['ideal_short_max'])} cm antes del objetivo.
3. **El resto del error no lo ven los encoders.** En al menos el {pct(f['arrived'])} de los
   casos la odometría dice "llegué", pero el robot real está en otro lugar. El
   deslizamiento lateral explica casi todo el error al moverse (ρ = {signed(f['rho_strafe'])}) y
   el error de escala del giroscopio el de los giros (ρ = {signed(f['rho_gyro'])}).
4. **Con tolerancias finas y el robot calibrado sí cumple** (escenario C): todos los
   movimientos pasan, con peor error de {num(f['c_drive_max'])} cm y cotas inferiores de
   {pct(f['c_drive_lb'])} (movimientos) y {pct(f['c_turn_lb'])} (giros).
5. **La escala del giroscopio hay que corregirla en el código.** Sin `GYRO_SCALE`
   (escenario D) pasan {f['d_turn_ok']} de 4 giros. `chassis.py` todavía no tiene esa constante.
6. **Costo en tiempo:** la rutina pasa de {num(f['t_asis'], 1)} s a {num(f['t_c'], 1)} s de
   media con las tolerancias finas.

Los rangos de error son **estimaciones**, no mediciones del robot. El estudio prueba la
lógica de control contra esas suposiciones; la calibración de abajo convierte las
suposiciones en datos.

## Parámetros a escribir en `chassis.py`

| Constante | Hoy | Escribir | Origen |
| --- | --- | --- | --- |
| `TOL_CM` | 1.0 | **0.3** | Este estudio (escenarios A–C) |
| `TOL_DEGREES` | 1.5 | **0.5** | Este estudio |
| `GYRO_SIGN` | 1 | 1 o −1 | Paso 1 |
| `WHEEL_DIAMETER` | 8.0 | diámetro **efectivo** medido | Paso 3 (`DEGREES_PER_CM` se recalcula solo) |
| `STRAFE_FACTOR` | 1.0 | medido (se estima ≈ 1,05–1,10) | Paso 4 |
| `GYRO_SCALE` | no existe | medido (≈ 1,00) | Paso 5; **requiere el cambio de código siguiente** |

Cambio propuesto en `chassis.py` (dos líneas, no aplicado todavía):

{GYRO_CODE}

Precisión que tiene que lograr la calibración (la que se simuló en el escenario C, 1σ):

| Magnitud | Precisión | En la prueba |
| --- | --- | --- |
| Diámetro efectivo de rueda | {pct(rc['wheel_scale']['sd'])} | ±4 mm en 2 m |
| Deslizamiento al avanzar | {pct(rc['slip_forward']['sd'])} | incluido en el diámetro efectivo |
| Deslizamiento lateral | {pct(rc['slip_strafe']['sd'])} | ±5 mm en 1 m |
| Escala del giroscopio | {pct(rc['gyro_scale']['sd'])} | ±7° en 10 vueltas |

## Pasos de calibración

Hacerlos **en el tapete de competencia** (el deslizamiento cambia con la superficie),
con la batería cargada, el robot con su peso final y las ruedas limpias. Material:
cinta métrica en mm, cinta adhesiva para marcas y un programa que imprima `odo.x`,
`odo.y` y `odo.heading` (por ejemplo `simulation/control/test_chassis_control_manual.py`).
Cada medición se repite **3 veces en cada sentido** y se usa el promedio.

1. **Signo del giroscopio.** Con el programa corriendo, girar el robot a mano 90° en
   sentido horario. Si `odo.heading` aumenta, `GYRO_SIGN = 1`; si disminuye,
   `GYRO_SIGN = -1`.
2. **Deriva en reposo.** Tras `odo.calibrate()`, dejar el robot quieto 60 s. Si
   `odo.heading` cambia más de 1°, alargar la calibración (`odo.calibrate(2.0)`) y
   repetirla justo antes de cada ronda.
3. **Diámetro efectivo de rueda** (corrige diámetro y deslizamiento al avanzar).
   Desde una marca, ejecutar `drive(forward_cm=200, timeout=10)` (el `timeout` por
   defecto de 5 s no alcanza para 2 m a `AUTO_SPEED`). Medir la distancia real `D_real`
   en cm y anotar la de la odometría `D_odo` (≈ 200).
   `WHEEL_DIAMETER = WHEEL_DIAMETER_actual × D_real / D_odo`. Repetir hacia atrás.
4. **Factor lateral** (después del paso 3). Ejecutar `drive(right_cm=100, timeout=10)`,
   medir el desplazamiento lateral real `D_real` y la odometría `D_odo` (≈ 100).
   `STRAFE_FACTOR = STRAFE_FACTOR_actual × D_odo / D_real`. Repetir hacia la izquierda.
5. **Escala del giroscopio** (requiere el cambio de código de arriba). Alinear un borde
   del robot con una línea de cinta, anotar `odo.heading`, girar el robot a mano
   **10 vueltas completas** hasta volver a alinearlo y anotar el cambio total `H` de
   `odo.heading` (no se normaliza, así que puede pasar de 360).
   `GYRO_SCALE = GYRO_SCALE_actual × 3600 / |H|`. Repetir en el otro sentido.
6. **Tolerancias.** Escribir `TOL_CM = 0.3` y `TOL_DEGREES = 0.5`. Revisar que los
   `timeout` de las rutinas sigan alcanzando (cada movimiento tarda algo más, ver la
   tabla del escenario C).
7. **Verificación en la pista.** Correr la rutina del estudio (avanzar/retroceder 60 cm,
   lateral 30 cm, diagonales, giros de 90°) al menos 10 veces y medir cada movimiento.
   Todos deben quedar dentro de 1 cm. Demostrar 95 % con 95 % de confianza **solo con
   pruebas físicas** pide {f['n_min']} repeticiones sin fallas por tipo de movimiento; por
   eso la parte estadística la cubre la simulación, y las pruebas físicas sirven para
   comprobar que el robot se comporta como el modelo.
8. **Actualizar el modelo.** Pasar las dispersiones medidas a
   `simulation/analysis/montecarlo_config_calibrated.json` y volver a generar este
   reporte.

## Figuras

![Distribución acumulada de errores]({figs['ecdf']})

**Distribución acumulada del error.** Cada curva indica qué fracción de los movimientos
quedó por debajo de cada error. Para cumplir, la curva tiene que cruzar la línea de
95 % a la izquierda de la tolerancia. Solo el escenario C lo logra en los dos paneles.

![Cota inferior por movimiento]({figs['bounds']})

**Cota inferior de 95 % por movimiento.** Es el valor que se compara con la meta. Con
{f['trials']} robots, la cota queda algo por debajo de la tasa observada.

![Puntos finales]({figs['endpoints']})

**Dónde termina realmente el robot.** Cada punto es un robot. Tal cual, los robots
terminan cortos (por debajo de 0) y desviados al ir de lado. Calibrados, quedan dentro
del círculo de 1 cm.

![Sensibilidad]({figs['sensitivity']})

**Qué parámetro causa el error** (escenario tal cual). Una barra larga indica que ese
parámetro ordena casi por completo a los robots del peor al mejor.

![Trayectorias]({figs['trails']})

**Trayectorias reales de {min(60, f['trials'])} robots** (la línea negra es el robot
ideal). La dispersión es de pocos centímetros, por eso la escala va en cm desde el
punto de inicio.

## Detalle por movimiento

### chassis.py tal cual

{move_table(runs['asis']['rows'])}

### C: tolerancias finas y robot calibrado

{move_table(runs['C']['rows'])}

### D: como C, sin corregir la escala del giroscopio

{move_table(runs['D']['rows'])}

## Método

- **Rutina:** `simulation/analysis/mc_routine_chassis.py` ejecuta 10 movimientos de
  `chassis.py` y marca la posición *real* del simulador antes y después de cada uno
  (`simtrace.mark`, solo existe en el simulador).
- **Error medido:** desplazamiento real contra el ordenado, en el marco del robot al
  inicio del movimiento (cm), y para los giros, el cambio real de orientación contra
  el ordenado (°).
- **Robots simulados:** cada uno se muestrea con `uncertainty.Variation` a partir de
  los rangos de `montecarlo_config.json` (sin calibrar) o
  `montecarlo_config_calibrated.json` (error residual después de calibrar). Los
  escenarios A–D además cambian constantes de `chassis.py` solo durante la simulación,
  sin modificar el archivo.
- **Criterio estadístico:** cota inferior unilateral exacta de Clopper-Pearson al
  {pct(c['confidence'], 0)} sobre la tasa de movimientos dentro de tolerancia, que tiene
  que llegar al {pct(c['required_rate'], 0)}. Cada robot es independiente, así que cada
  tipo de movimiento tiene n = {f['trials']}. Sin fallas, el mínimo es {f['n_min']} robots.
- **Sensibilidad:** correlación de rangos de Spearman entre cada parámetro muestreado
  y el peor error del robot.

## Límites

- Los rangos son estimaciones hasta tener mediciones.
- El modelo no tiene choques ni contacto con estructuras de la pista, caída de voltaje
  de la batería, ni variaciones de geometría del chasis.
- Los motores tienen solo un retardo de primer orden.

Por todo esto, el estudio no prueba que el robot real cumpla: muestra qué hace falta
para que la lógica de `chassis.py` pueda cumplir.
"""


def text_en(runs, figs, f):
    c, rc = f["c"], f["rc"]
    return f"""# Monte Carlo report: chassis control robustness

Study of `software/controls/drivetrain/chassis.py` in the 2D simulator
(`simulation/field2d`) with {f['trials']} simulated robots per scenario, each with its own
wheel, motor, slip, gyroscope and encoder errors. Generated on {date.today():%Y-%m-%d}
by `simulation/analysis/make_chassis_report.py` (seed {f['seed']}, {f['minutes']} min).
Running it again reproduces these numbers.

## Summary

**Requirement:** error ≤ {cm(c['drive_error_cm'])} per move in more than
{pct(c['required_rate'], 0)} of moves, with {pct(c['confidence'], 0)} confidence. Turns had
no requirement, so they use {deg(c['turn_error_deg'])}, the current tolerance in `chassis.py`.

{scenario_summary(runs)}

1. **`chassis.py` as is does not meet it** for any of the 10 move types.
2. **The tolerances sit on the requirement.** `drive()` stops as soon as it is within
   `TOL_CM = 1.0` cm, so even an ideal robot ends {num(f['ideal_short'])}–{num(f['ideal_short_max'])} cm
   short of the target.
3. **The remaining error is invisible to the encoders.** In at least {pct(f['arrived'])} of
   the cases odometry says "arrived" while the real robot is elsewhere. Strafe slip
   explains almost all of the drive error (ρ = {signed(f['rho_strafe'])}) and gyro scale error
   the turn error (ρ = {signed(f['rho_gyro'])}).
4. **With tight tolerances and a calibrated robot it passes** (scenario C): every move
   passes, worst error {num(f['c_drive_max'])} cm, lower bounds {pct(f['c_drive_lb'])} (moves)
   and {pct(f['c_turn_lb'])} (turns).
5. **The gyro scale has to be corrected in code.** Without `GYRO_SCALE` (scenario D),
   {f['d_turn_ok']} of 4 turns pass. `chassis.py` does not have that constant yet.
6. **Time cost:** the routine goes from {num(f['t_asis'], 1)} s to {num(f['t_c'], 1)} s on
   average with the tight tolerances.

The error ranges are **estimates**, not robot measurements. The study tests the control
logic against those assumptions; the calibration below turns the assumptions into data.

## Parameters to write in `chassis.py`

| Constant | Today | Write | Source |
| --- | --- | --- | --- |
| `TOL_CM` | 1.0 | **0.3** | This study (scenarios A–C) |
| `TOL_DEGREES` | 1.5 | **0.5** | This study |
| `GYRO_SIGN` | 1 | 1 or −1 | Step 1 |
| `WHEEL_DIAMETER` | 8.0 | measured **effective** diameter | Step 3 (`DEGREES_PER_CM` follows) |
| `STRAFE_FACTOR` | 1.0 | measured (estimated ≈ 1.05–1.10) | Step 4 |
| `GYRO_SCALE` | does not exist | measured (≈ 1.00) | Step 5; **needs the code change below** |

Proposed change in `chassis.py` (two lines, not applied yet):

{GYRO_CODE}

Accuracy the calibration has to reach (what scenario C simulated, 1σ):

| Quantity | Accuracy | In the test |
| --- | --- | --- |
| Effective wheel diameter | {pct(rc['wheel_scale']['sd'])} | ±4 mm over 2 m |
| Forward slip | {pct(rc['slip_forward']['sd'])} | included in the effective diameter |
| Strafe slip | {pct(rc['slip_strafe']['sd'])} | ±5 mm over 1 m |
| Gyroscope scale | {pct(rc['gyro_scale']['sd'])} | ±7° over 10 turns |

## Calibration steps

Do them **on the competition mat** (slip depends on the surface), with a charged
battery, the robot at its final weight and clean wheels. You need a tape measure in mm,
tape for marks and a program that prints `odo.x`, `odo.y` and `odo.heading` (for
example `simulation/control/test_chassis_control_manual.py`). Repeat each measurement
**3 times in each direction** and use the average.

1. **Gyro sign.** With the program running, turn the robot by hand 90° clockwise. If
   `odo.heading` increases, `GYRO_SIGN = 1`; if it decreases, `GYRO_SIGN = -1`.
2. **Drift at rest.** After `odo.calibrate()`, leave the robot still for 60 s. If
   `odo.heading` changes by more than 1°, calibrate longer (`odo.calibrate(2.0)`) and
   repeat it right before each round.
3. **Effective wheel diameter** (corrects diameter and forward slip). From a mark, run
   `drive(forward_cm=200, timeout=10)` (the default 5 s `timeout` is too short for 2 m
   at `AUTO_SPEED`). Measure the real distance `D_real` in cm and note the odometry
   distance `D_odo` (≈ 200).
   `WHEEL_DIAMETER = current WHEEL_DIAMETER × D_real / D_odo`. Repeat backward.
4. **Strafe factor** (after step 3). Run `drive(right_cm=100, timeout=10)`, measure the
   real sideways distance `D_real` and the odometry `D_odo` (≈ 100).
   `STRAFE_FACTOR = current STRAFE_FACTOR × D_odo / D_real`. Repeat to the left.
5. **Gyro scale** (needs the code change above). Line up one edge of the robot with a
   tape line, note `odo.heading`, turn the robot by hand **10 full turns** until it lines
   up again and note the total change `H` of `odo.heading` (it is not wrapped, so it can
   go past 360). `GYRO_SCALE = current GYRO_SCALE × 3600 / |H|`. Repeat the other way.
6. **Tolerances.** Write `TOL_CM = 0.3` and `TOL_DEGREES = 0.5`. Check that the
   routines' `timeout` values are still long enough (each move takes slightly longer,
   see the scenario C table).
7. **Check on the field.** Run the study routine (forward/backward 60 cm, strafe 30 cm,
   diagonals, 90° turns) at least 10 times and measure every move. All must be within
   1 cm. Showing 95% with 95% confidence **from physical tests alone** takes
   {f['n_min']} failure-free repetitions per move type; that is why the simulation covers
   the statistics, and the physical tests check that the robot behaves like the model.
8. **Update the model.** Put the measured spreads into
   `simulation/analysis/montecarlo_config_calibrated.json` and regenerate this report.

## Figures

![Cumulative error distribution]({figs['ecdf']})

**Cumulative error distribution.** Each curve shows the fraction of moves below each
error. To pass, a curve has to cross the 95% line to the left of the tolerance. Only
scenario C does, in both panels.

![Lower bound per move]({figs['bounds']})

**95% lower bound per move.** This is the value compared with the goal. With
{f['trials']} robots, the bound sits slightly below the observed rate.

![End points]({figs['endpoints']})

**Where the robot really ends.** Each dot is a robot. As is, robots end short (below 0)
and drift sideways when strafing. Calibrated, they stay inside the 1 cm circle.

![Sensitivity]({figs['sensitivity']})

**Which parameter causes the error** (scenario as is). A long bar means that parameter
almost fully orders the robots from worst to best.

![Trajectories]({figs['trails']})

**Real trajectories of {min(60, f['trials'])} robots** (the black line is the ideal
robot). The spread is a few centimetres, so the axes are in cm from the start point.

## Per-move detail

### chassis.py as is

{move_table(runs['asis']['rows'])}

### C: tight tolerances and calibrated robot

{move_table(runs['C']['rows'])}

### D: like C, without correcting the gyro scale

{move_table(runs['D']['rows'])}

## Method

- **Routine:** `simulation/analysis/mc_routine_chassis.py` runs 10 `chassis.py` moves and
  marks the simulator's *true* pose before and after each (`simtrace.mark`, simulator
  only).
- **Measured error:** real displacement against the commanded one, in the robot frame at
  the start of the move (cm); for turns, real heading change against the commanded one (°).
- **Simulated robots:** each is sampled with `uncertainty.Variation` from the ranges in
  `montecarlo_config.json` (uncalibrated) or `montecarlo_config_calibrated.json`
  (residual error after calibration). Scenarios A–D also change `chassis.py` constants
  during the simulation only, without editing the file.
- **Statistical criterion:** exact one-sided Clopper-Pearson {pct(c['confidence'], 0)}
  lower bound of the in-tolerance rate, which has to reach {pct(c['required_rate'], 0)}.
  Each robot is independent, so each move type has n = {f['trials']}. With no failures,
  the minimum is {f['n_min']} robots.
- **Sensitivity:** Spearman rank correlation between each sampled parameter and the
  robot's worst error.

## Limits

- The ranges are estimates until there are measurements.
- The model has no collisions or contact with field structures, no battery voltage
  sag, and no chassis geometry variation.
- Motors have a first-order lag only.

So the study does not prove that the real robot meets the requirement: it shows what is
needed for the `chassis.py` logic to be able to meet it.
"""


def demote(markdown):
    """One heading level down (outside code blocks), to nest a report under a language."""
    out, in_code = [], False
    for line in markdown.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        out.append("#" + line if line.startswith("#") and not in_code else line)
    return "\n".join(out)


def write_readme(runs, figs_by_lang, f):
    set_lang("es")
    es = text_es(runs, figs_by_lang["es"], f)
    set_lang("en")
    en = text_en(runs, figs_by_lang["en"], f)
    page = f"""# Monte Carlo: chassis.py

**[Español](#español)** · **[English](#english)**

## Español

{demote(es.split(chr(10), 1)[1]).lstrip()}

---

## English

{demote(en.split(chr(10), 1)[1]).lstrip()}
"""
    (OUT / "README.md").write_text(page)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trials", type=int, help="override the trial count of every scenario")
    ap.add_argument("--jobs", type=int, default=0)
    args = ap.parse_args(argv)

    t0 = time.time()
    cfg_base = json.loads((HERE / "montecarlo_config.json").read_text())
    cfg_cal = json.loads((HERE / "montecarlo_config_calibrated.json").read_text())
    trials = args.trials or cfg_base["trials"]
    runs = {}
    for key, cfg_file, overrides, color, marker, show in SCENARIOS:
        cfg = json.loads((HERE / cfg_file).read_text())
        cfg["trials"], cfg["chassis_overrides"] = trials, overrides
        if key == "D":  # calibrated robot, but the gyro scale error is left uncorrected
            cfg["ranges"]["gyro_scale"] = cfg_base["ranges"]["gyro_scale"]
        print(f"{STR['en']['scenario'][key]} ...", flush=True)
        results = mc.run_study(cfg, jobs=args.jobs, keep_trail=key in ("asis", "C"))
        failed = [r for r in results if r["failed"]]
        if failed:
            raise SystemExit(f"{key}: {len(failed)} trials failed, e.g. {failed[0]['failed']}")
        runs[key] = {"color": color, "marker": marker, "results": results,
                     "rows": mc.summarize(results, cfg["criteria"])}
        add_durations(runs[key])

    print("ideal robot ...", flush=True)
    ideal = mc.run_study(dict(cfg_base, trials=1, chassis_overrides={}), ideal=True, jobs=1, keep_trail=True)
    runs["ideal"] = {"rows": mc.summarize(ideal, cfg_base["criteria"])}
    start = (cfg_base["start"]["x_mm"], cfg_base["start"]["y_mm"])

    OUT.mkdir(parents=True, exist_ok=True)
    figs = {}
    for lang in LANGS:
        set_lang(lang)
        figs[lang] = draw_figures(runs, cfg_base["criteria"], ideal[0]["trail"], start)
    summary = {k: v["rows"] for k, v in runs.items()}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    write_readme(runs, figs, facts(runs, cfg_base, cfg_cal, trials, time.time() - t0))
    print(f"Report: {OUT / 'README.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
