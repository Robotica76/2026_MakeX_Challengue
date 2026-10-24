"""Builds the Monte Carlo report of chassis.py: runs the scenarios, draws the figures
and writes reports/chassis_montecarlo/README.md (committed, unlike results/).

    .venv/bin/pip install -r simulation/analysis/requirements.txt   # matplotlib
    .venv/bin/python simulation/analysis/make_chassis_report.py      # ~4 min on 6 cores
    .venv/bin/python simulation/analysis/make_chassis_report.py --trials 60   # quicker draft

Same seed -> same numbers. The report text below quotes the computed values, so
re-running after changing montecarlo_config*.json updates tables, figures and text.
"""

import argparse
import json
import math
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

# Reference data-viz palette (dataviz skill, references/palette.md), light surface.
# Colour follows the scenario everywhere; slots 1-2 (blue, orange) are the pair used
# in two-series scatter plots, which is the all-pairs-safe range of the palette.
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
CRITICAL = "#d03b3b"

SCENARIOS = [
    # key, label, config file, overrides, colour, marker, in figures
    ("asis", "chassis.py tal cual", "montecarlo_config.json", {}, ORANGE, "o", True),
    ("A", "A: tolerancias finas", "montecarlo_config.json", TIGHT, AQUA, "s", True),
    ("B", "B: A + STRAFE_FACTOR 1.075", "montecarlo_config.json", dict(TIGHT, STRAFE_FACTOR=1.075),
     YELLOW, "D", True),
    ("C", "C: A + robot calibrado", "montecarlo_config_calibrated.json", TIGHT, BLUE, "^", True),
    ("D", "D: C sin GYRO_SCALE", "montecarlo_config_calibrated.json", TIGHT, INK_2, "v", False),
]


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
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=150, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    return f"figures/{name}"


def errors(results, kind):
    return [m["error"] for r in results for m in r["moves"] if m["kind"] == kind]


# ---------------------------------------------------------------- figures
def fig_ecdf(runs, criteria):
    fig, (a1, a2) = new_figure(10, 4.2, cols=2)
    panels = ((a1, "drive", criteria["drive_error_cm"], "cm", "Error de posición por movimiento (cm)",
               "Avanzar, retroceder, lateral y diagonal"),
              (a2, "turn", criteria["turn_error_deg"], "°", "Error de orientación por giro (°)", "Giros de 90°"))
    for ax, kind, tol, unit, xlabel, title in panels:
        xmax = 0
        for key, label, *_rest in SCENARIOS:
            if not runs[key]["show"]:
                continue
            e = sorted(errors(runs[key]["results"], kind))
            y = [(i + 1) / len(e) for i in range(len(e))]
            ax.step(e, y, where="post", color=runs[key]["color"], linewidth=2, label=label)
            xmax = max(xmax, e[-1])
        ax.axvline(tol, color=INK, linewidth=1.2, linestyle="--")
        ax.axhline(criteria["required_rate"], color=INK_2, linewidth=1, linestyle=":")
        label = f"{num(tol, 0 if tol == int(tol) else 1)} cm" if unit == "cm" else deg(tol)
        ax.text(tol, 0.03, f" tolerancia {label}", color=INK, fontsize=8.5, va="bottom")
        ax.text(xmax * 0.02, criteria["required_rate"] + 0.01, "95 %", color=INK_2, fontsize=8.5, va="bottom")
        ax.set_xlim(0, xmax * 1.12)
        ax.set_ylim(0, 1.02)
        ax.set_xlabel(xlabel, color=INK, fontsize=9.5)
        ax.set_title(title, color=INK, fontsize=10.5, loc="left")
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    a1.set_ylabel("Movimientos con error ≤ x", color=INK, fontsize=9.5)
    handles, labels = a1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=9, labelcolor=INK,
               bbox_to_anchor=(0.5, -0.06))
    return save(fig, "ecdf_errores.png")


def fig_lower_bounds(runs, criteria):
    rows = [r["move"] for r in runs["asis"]["rows"]]
    fig, ax = new_figure(9, 5.2)
    shown = [s for s in SCENARIOS if runs[s[0]]["show"]]
    offsets = {s[0]: (i - (len(shown) - 1) / 2) * 0.17 for i, s in enumerate(shown)}
    for key, label, _cfg, _ov, color, marker, _show in shown:
        by_move = {r["move"]: r for r in runs[key]["rows"]}
        ys = [i + offsets[key] for i in range(len(rows))]
        ax.scatter([by_move[m]["lower95"] for m in rows], ys, color=color, marker=marker, s=46,
                   edgecolors=SURFACE, linewidths=1.2, label=label, zorder=3)
    ax.axvline(criteria["required_rate"], color=INK, linewidth=1.2, linestyle="--")
    ax.text(criteria["required_rate"], -0.9, " meta 95 %", color=INK, fontsize=8.5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows)
    ax.invert_yaxis()
    ax.set_xlim(-0.02, 1.02)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlabel("Cota inferior 95 % de la tasa de movimientos dentro de tolerancia", color=INK, fontsize=9.5)
    ax.set_title("Pasa un movimiento si su cota inferior llega a la meta", color=INK, fontsize=10.5, loc="left")
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, -0.25), ncol=4, frameon=False, fontsize=9,
              labelcolor=INK)
    return save(fig, "cota_inferior_por_movimiento.png")


def fig_sensitivity(results):
    fig, axes = new_figure(10, 3.6, cols=2)
    for ax, kind, title in ((axes[0], "drive", "Movimientos: peor error de posición"),
                            (axes[1], "turn", "Giros: peor error de orientación")):
        sens = mc.sensitivity(results, kind)[:6][::-1]
        names = [n for n, _ in sens]
        rhos = [r for _, r in sens]
        ax.barh(range(len(sens)), [abs(r) for r in rhos], color=BLUE, height=0.6)
        for i, rho in enumerate(rhos):
            ax.text(abs(rho) + 0.02, i, f"{rho:+.2f}", va="center", color=INK, fontsize=8.5)
        ax.set_yticks(range(len(sens)))
        ax.set_yticklabels(names, fontsize=8.5)
        ax.set_xlim(0, 1.15)
        ax.set_xlabel("|ρ de Spearman| con el error (signo en la etiqueta)", color=INK, fontsize=9)
        ax.set_title(title, color=INK, fontsize=10.5, loc="left")
    fig.tight_layout()
    return save(fig, "sensibilidad.png")


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
            xs = [m[across] for m in ms]                 # lateral deviation
            ys = [m[along] - cmd for m in ms]            # short (-) / long (+)
            ax.scatter(xs, ys, s=16, color=run["color"], marker=run["marker"], alpha=0.75,
                       edgecolors="none", label=run["label"])
            lim = max(lim, max(map(abs, xs + ys)))
        ax.add_patch(plt.Circle((0, 0), tol, fill=False, color=INK, linewidth=1.2, linestyle="--"))
        ax.text(tol * 0.72, tol * 0.72, f"{tol:g} cm", color=INK, fontsize=8.5)
        ax.plot([0], [0], marker="+", color=INK, markersize=10)
        lim = max(lim * 1.1, tol * 1.6)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xlabel("Desviación perpendicular al movimiento (cm)", color=INK, fontsize=9)
        ax.set_ylabel("Corto (−) / largo (+) respecto al objetivo (cm)", color=INK, fontsize=9)
        ax.set_title(f"Punto final real: {move} cm", color=INK, fontsize=10.5, loc="left")
    axes[0].legend(loc="upper left", frameon=False, fontsize=8.5, labelcolor=INK)
    fig.tight_layout()
    return save(fig, "puntos_finales.png")


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
        ax.plot(xs, ys, color=INK, linewidth=1.4, label="robot ideal")
        ax.plot([0], [0], marker="o", color=INK, markersize=6)
        ax.set_aspect("equal")
        ax.set_xlabel("x en la pista desde el inicio (cm)", color=INK, fontsize=9)
        ax.set_title(f"{run['label']}: {len(shown)} robots", color=INK, fontsize=10.5, loc="left")
        ax.legend(loc="upper right", frameon=False, fontsize=8.5, labelcolor=INK)
    axes[0].set_ylabel("y en la pista desde el inicio (cm)", color=INK, fontsize=9)
    fig.tight_layout()
    return save(fig, "trayectorias.png")


# ---------------------------------------------------------------- report text
def pct(x, d=1):
    """Spanish percent: 0.99 -> '99,0 %'."""
    return f"{x * 100:.{d}f} %".replace(".", ",")


def signed(x):
    return ("+" if x > 0 else "") + num(x)


def deg(x):
    return f"{num(x, 1)}°"


def num(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


def move_table(rows, unit_drive="cm"):
    lines = ["| Movimiento | Tolerancia | Dentro / total | Cota inf. 95 % | Resultado | Error medio | p95 | Máx. | Tiempo medio |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        tol = f"{num(r['tolerance'], 1)} {unit_drive}" if r["kind"] == "drive" else deg(r["tolerance"])
        lines.append(f"| {r['move']} | {tol} | {r['pass']}/{r['n']} |"
                     f" {pct(r['lower95'])} | **{'PASA' if r['verdict'] == 'PASS' else 'FALLA'}** |"
                     f" {num(r['mean'])} | {num(r['p95'])} | {num(r['max'])} | {num(r['duration'], 1)} s |")
    return "\n".join(lines)


def scenario_summary(runs):
    lines = ["| Escenario | Movimientos que pasan | Peor p95 avance/lateral | Peor p95 giro | Rutina completa (media) |",
             "| --- | --- | --- | --- | --- |"]
    for key, label, *_ in SCENARIOS:
        rows = runs[key]["rows"]
        ok = sum(r["verdict"] == "PASS" for r in rows)
        d = max(r["p95"] for r in rows if r["kind"] == "drive")
        t = max(r["p95"] for r in rows if r["kind"] == "turn")
        dur = sum(r["duration_s"] for r in runs[key]["results"]) / len(runs[key]["results"])
        lines.append(f"| {label} | {ok}/{len(rows)} | {num(d)} cm | {num(t)}° | {num(dur, 1)} s |")
    return "\n".join(lines)


def add_durations(run):
    for row in run["rows"]:
        ds = [m["duration_s"] for r in run["results"] for m in r["moves"] if m["move"] == row["move"]]
        row["duration"] = sum(ds) / len(ds)


def write_report(runs, figs, cfg_base, cfg_cal, trials, elapsed):
    c = cfg_base["criteria"]
    asis, C, D = runs["asis"], runs["C"], runs["D"]
    sens_drive = mc.sensitivity(asis["results"], "drive")
    sens_turn = mc.sensitivity(asis["results"], "turn")
    ideal_drive = runs["ideal"]["rows"]
    ideal_short = min(r["mean"] for r in ideal_drive if r["kind"] == "drive")
    ideal_short_max = max(r["mean"] for r in ideal_drive if r["kind"] == "drive")
    d_turn_ok = sum(r["verdict"] == "PASS" for r in D["rows"] if r["kind"] == "turn")
    c_drive_max = max(r["max"] for r in C["rows"] if r["kind"] == "drive")
    c_drive_lb = min(r["lower95"] for r in C["rows"] if r["kind"] == "drive")
    c_turn_lb = min(r["lower95"] for r in C["rows"] if r["kind"] == "turn")
    t_asis = sum(r["duration_s"] for r in asis["results"]) / trials
    t_c = sum(r["duration_s"] for r in C["results"]) / trials
    rc = cfg_cal["ranges"]

    text = f"""# Reporte Monte Carlo: robustez del control del chasis

Estudio de `software/controls/drivetrain/chassis.py` en el simulador 2D
(`simulation/field2d`) con {trials} robots simulados por escenario, cada uno con
errores distintos de ruedas, motores, deslizamiento, giroscopio y encoders.
Generado el {date.today():%Y-%m-%d} por `simulation/analysis/make_chassis_report.py`
(semilla {cfg_base['seed']}, {elapsed / 60:.0f} min). Volver a correrlo reproduce
estos números.

## Resumen

**Requisito:** error ≤ {c['drive_error_cm']:g} cm por movimiento en más del
{pct(c['required_rate'], 0)} de los movimientos, con {pct(c['confidence'], 0)} de confianza.
Para los giros, que no tenían requisito, se usa {deg(c['turn_error_deg'])}, la tolerancia
actual de `chassis.py`.

{scenario_summary(runs)}

1. **`chassis.py` tal cual no cumple** en ninguno de los 10 tipos de movimiento.
2. **Las tolerancias están en el límite del requisito.** `drive()` se detiene en cuanto
   está a menos de `TOL_CM = 1.0` cm, así que un robot ideal ya termina
   {num(ideal_short)}–{num(ideal_short_max)} cm antes del objetivo.
3. **El resto del error no lo ven los encoders.** En al menos el {pct(min(r['arrived'] for r in asis['rows']))}
   de los casos la odometría dice "llegué", pero el robot real está en otro lugar.
   El deslizamiento lateral explica casi todo el error al moverse
   (ρ = {signed(dict(sens_drive)['slip_strafe'])}) y el error de escala del giroscopio el de
   los giros (ρ = {signed(dict(sens_turn)['gyro_scale'])}).
4. **Con tolerancias finas y el robot calibrado sí cumple** (escenario C): todos los
   movimientos pasan, con peor error de {num(c_drive_max)} cm y cotas inferiores de
   {pct(c_drive_lb)} (movimientos) y {pct(c_turn_lb)} (giros).
5. **La escala del giroscopio hay que corregirla en el código.** Sin `GYRO_SCALE`
   (escenario D) pasan {d_turn_ok} de 4 giros. `chassis.py` todavía no tiene esa constante.
6. **Costo en tiempo:** la rutina pasa de {num(t_asis, 1)} s a {num(t_c, 1)} s de media
   con las tolerancias finas.

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

```python
GYRO_SCALE = 1.0   # real degrees / gyro degrees, from the 10-turn test (calibration step 5)

# in Odometry.update():
w = (read_gyro_z() - self.gyro_bias) * GYRO_SIGN * GYRO_SCALE
```

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
   Desde una marca, ejecutar `forward(200)` con un `timeout` mayor
   (`drive(forward_cm=200, timeout=10)`: el valor por defecto de 5 s no alcanza para
   2 m a `AUTO_SPEED`). Medir la distancia real `D_real` en cm y anotar la de la
   odometría `D_odo` (≈ 200).
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
   pruebas físicas** pide 59 repeticiones sin fallas por tipo de movimiento; por eso
   la parte estadística la cubre la simulación, y las pruebas físicas sirven para
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
{trials} robots, la cota queda algo por debajo de la tasa observada.

![Puntos finales]({figs['endpoints']})

**Dónde termina realmente el robot.** Cada punto es un robot. Tal cual, los robots
terminan cortos (por debajo de 0) y desviados al ir de lado. Calibrados, quedan dentro
del círculo de 1 cm.

![Sensibilidad]({figs['sensitivity']})

**Qué parámetro causa el error** (escenario tal cual). Una barra larga indica que ese
parámetro ordena casi por completo a los robots del peor al mejor.

![Trayectorias]({figs['trails']})

**Trayectorias reales de {min(60, trials)} robots** (la línea negra es el robot ideal). La dispersión
es de pocos centímetros, por eso la escala va en cm desde el punto de inicio.

## Detalle por movimiento

### chassis.py tal cual

{move_table(asis['rows'])}

### C: tolerancias finas y robot calibrado

{move_table(C['rows'])}

### D: como C, sin corregir la escala del giroscopio

{move_table(D['rows'])}

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
  {pct(c['confidence'], 0)} sobre la tasa de movimientos dentro de tolerancia, que tiene que
  llegar al {pct(c['required_rate'], 0)}. Cada robot es independiente, así que cada tipo de
  movimiento tiene n = {trials}. Sin fallas, el mínimo es
  {mc.trials_needed(c['required_rate'], c['confidence'])} robots.
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
    (OUT / "README.md").write_text(text)


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
    for key, label, cfg_file, overrides, color, marker, show in SCENARIOS:
        cfg = json.loads((HERE / cfg_file).read_text())
        cfg["trials"], cfg["chassis_overrides"] = trials, overrides
        if key == "D":  # calibrated robot, but the gyro scale error is left uncorrected
            cfg["ranges"]["gyro_scale"] = cfg_base["ranges"]["gyro_scale"]
        print(f"{label} ...", flush=True)
        results = mc.run_study(cfg, jobs=args.jobs, keep_trail=key in ("asis", "C"))
        failed = [r for r in results if r["failed"]]
        if failed:
            raise SystemExit(f"{label}: {len(failed)} trials failed, e.g. {failed[0]['failed']}")
        runs[key] = {"label": label, "color": color, "marker": marker, "show": show,
                     "results": results, "rows": mc.summarize(results, cfg["criteria"])}
        add_durations(runs[key])

    print("ideal robot ...", flush=True)
    ideal_cfg = dict(cfg_base, trials=1, chassis_overrides={})
    ideal = mc.run_study(ideal_cfg, ideal=True, jobs=1, keep_trail=True)
    runs["ideal"] = {"rows": mc.summarize(ideal, cfg_base["criteria"])}
    start = (cfg_base["start"]["x_mm"], cfg_base["start"]["y_mm"])

    OUT.mkdir(parents=True, exist_ok=True)
    figs = {
        "ecdf": fig_ecdf(runs, cfg_base["criteria"]),
        "bounds": fig_lower_bounds(runs, cfg_base["criteria"]),
        "endpoints": fig_endpoints(runs, cfg_base["criteria"]),
        "sensitivity": fig_sensitivity(runs["asis"]["results"]),
        "trails": fig_trails(runs, ideal[0]["trail"], start),
    }
    summary = {k: [{kk: vv for kk, vv in r.items()} for r in v["rows"]] for k, v in runs.items()}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    write_report(runs, figs, cfg_base, cfg_cal, trials, time.time() - t0)
    print(f"Report: {OUT / 'README.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
