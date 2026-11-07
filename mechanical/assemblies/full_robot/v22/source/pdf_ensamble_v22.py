"""PDF de ensamble v22: portada, explosionada global, una hoja por subsistema con piezas numeradas, secuencia de ensamble y lista."""
import json, textwrap, numpy as np
from PIL import Image
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
D = "/home/claude/out22/explosionada"; OUT = "/home/claude/out22/Ensamble_StormBreaker_v22.pdf"
M = json.load(open(f"{D}/meta.json")); G = {int(k): v for k, v in M["groups"].items()}; BOM = M["bom"]
A3 = (16.54, 11.69)
def crop(fn, meta=None, pad=30):
    im = Image.open(f"{D}/{fn}.png").convert("RGB"); a = np.asarray(im)
    mask = (a < 245).any(2); ys, xs = np.where(mask)
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, a.shape[1]); y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, a.shape[0])
    W, H = a.shape[1], a.shape[0]
    out = []
    for e in meta or []:
        out.append(dict(e, x=(e["x"] * W - x0) / (x1 - x0), y=(e["y"] * H - y0) / (y1 - y0)))
    return a[y0:y1, x0:x1], out
def pretty(n):
    return n.replace("_", " ")
def header(fig, title, sub=""):
    fig.text(0.03, 0.965, title, fontsize=20, weight="bold", va="top")
    if sub: fig.text(0.03, 0.928, sub, fontsize=11, color="0.35", va="top")
    fig.text(0.97, 0.965, "MakeX Challenge 2026 · Storm Breaker v22", fontsize=10, ha="right", va="top", color="0.4")
def footer(fig, page):
    fig.text(0.97, 0.015, f"Hoja {page}", fontsize=9, ha="right", color="0.4")
    fig.text(0.03, 0.015, "Medidas en mm. Numeración: subsistema.pieza (piezas ordenadas de mayor a menor volumen). Tornillería no se muestra en las explosionadas.", fontsize=8, color="0.45")
def balloons(fig, rect, img, labs, fs=8, r=0.012):
    ax = fig.add_axes(rect); ax.imshow(img); ax.set_axis_off()
    h, w = img.shape[:2]
    # columnas de etiquetas fuera de la imagen (coordenadas de figura)
    fx0, fy0, fw, fh = rect
    left = sorted([e for e in labs if e["x"] < 0.5], key=lambda e: e["y"]); right = sorted([e for e in labs if e["x"] >= 0.5], key=lambda e: e["y"])
    asp = (fh * A3[1]) / (fw * A3[0]); iw, ih = w, h
    # posicion real de la imagen dentro del axes (aspect equal)
    sx = min(fw * A3[0] / iw, fh * A3[1] / ih); dw, dh = iw * sx / A3[0], ih * sx / A3[1]
    ox, oy = fx0 + (fw - dw) / 2, fy0 + (fh - dh) / 2
    def to_fig(e): return ox + e["x"] * dw, oy + (1 - e["y"]) * dh
    for col, xs in ((left, fx0 - 0.005), (right, fx0 + fw + 0.005)):
        n = len(col)
        if not n: continue
        ys = np.linspace(fy0 + fh - 0.02, fy0 + 0.02, n) if n > 1 else [to_fig(col[0])[1]]
        for e, yl in zip(col, ys):
            px, py = to_fig(e)
            fig.add_artist(plt.Line2D([xs, px], [yl, py], transform=fig.transFigure, color="0.35", lw=0.6))
            fig.add_artist(plt.Circle((px, py), 0.0025, transform=fig.transFigure, color="crimson"))
            fig.text(xs, yl, e["num"], fontsize=fs, ha="right" if col is left else "left", va="center", weight="bold",
                     bbox=dict(boxstyle="circle,pad=0.25" if len(e["num"]) <= 2 else "round,pad=0.25", fc="white", ec="crimson", lw=0.8))
def table(fig, rect, rows, fs=7.5, cols=1):
    ax = fig.add_axes(rect); ax.set_axis_off()
    per = int(np.ceil(len(rows) / cols))
    for c in range(cols):
        chunk = rows[c * per:(c + 1) * per]; x = c / cols
        ax.text(x, 1.0, "N.º", fontsize=fs + 0.5, weight="bold", va="top"); ax.text(x + 0.07 / cols * 1.6, 1.0, "Pieza", fontsize=fs + 0.5, weight="bold", va="top")
        dy = min(0.03, 0.97 / max(len(chunk), 1))
        for k, (n, t) in enumerate(chunk):
            y = 0.97 - (k + 1) * dy
            if k % 2 == 0: ax.add_patch(plt.Rectangle((x - 0.005, y - dy * 0.15), 1 / cols - 0.01, dy, color="0.95", lw=0))
            ax.text(x, y, n, fontsize=fs, va="bottom", weight="bold", color="crimson"); ax.text(x + 0.07 / cols * 1.6, y, t[:70], fontsize=fs, va="bottom")
STEPS = {
    1: "Chasis: rieles (slide beam), 3 travesaños 2424, 4 motores 180 Smart Encoder con ruedas mecanum y guardas. Revisar que el chasis quede a escuadra antes de seguir.",
    2: "Caja de electrónica: 4 calzas y piso CF 2 mm atornillado a los dos rieles (4 x M4). Batería con 2 cinchos, NovaPi, módulo de potencia, drivers + bluetooth. Paredes CF 1 mm con esquineros. La tapa va al final, después de cablear.",
    3: "Torre de pelotas: placas laterales CF3 (paso D34 para el núcleo de R2), ejes D8 Al, 12 poleas y 6 bandas (3 filas), respaldo y pared frontal, codo con su DC-25 interno, DC-37 con engranes 48T.",
    4: "Intake y brazo UR: placas laterales, R2 (recto), R3 ancho, rodillo inferior con su DC-25, DC-37 con tren de engranes 48T/16T, rieles de tubo CF 20x20, husillo T8, patines, brazo UR con su DC-25 y DC-25 de elevación arriba.",
    5: "Mástil del elevador: piso, placas y costillas CF3, mamparo, riel lineal, banda dentada GT2, DC-37 50 RPM con polea 90T y tapa con la cámara IA (con muesca guía del mástil de bandera). Separadores torre-mástil y cuadernas del intake.",
    6: "Carro y pinza: placa del carro, bloque de montaje, husillo y DC-25 de la pinza, mordazas. Pegar/atornillar el receptor del mástil de bandera en el bloque de montaje.",
    7: "Lanzador: postes CF 16x16 y base CF3, placas laterales, ruedas de fricción D45 con brushless y ESC, capucha inferior PC con aleta y servo MS-12A.",
    8: "Canasta y alimentador: piso PC inclinado y paredes, rodillo alimentador TPU con DC-25 3:1 (48T/16T) debajo del piso, buje en la pared trasera.",
    10: "Tornillería: apretar todas las uniones (M3 de botón + M4 del chasis). Usar fijador de roscas azul en las que tienen vibración (motores, ruedas, lanzador).",
    9: "Mástil de bandera — SOLO en el Modification Stage (60 s): meter el tubo CF 8x6 en el receptor por la muesca de la tapa, poner el pasador R, colocar el palo de la bandera en la C y cerrar con las 2 ligas.",
}
with PdfPages(OUT) as pdf:
    page = 1
    # portada
    fig = plt.figure(figsize=A3); header(fig, "Storm Breaker v22 — Manual de ensamble", "Vista explosionada, piezas numeradas por subsistema y secuencia de ensamble")
    for k, (fn, rect) in enumerate((("00_ensamblado_iso", [0.02, 0.12, 0.55, 0.78]), ("00_ensamblado_iso_atras", [0.55, 0.36, 0.43, 0.55]))):
        img, _ = crop(fn); ax = fig.add_axes(rect); ax.imshow(img); ax.set_axis_off()
    info = ("Datos generales\n\n• Huella 500 x 500 mm, altura 642 mm (sin mástil de bandera)\n• Con mástil (Modification Stage): hasta 1062 mm con el carro arriba\n"
            "• Masa CAD: 9.88 kg (robot) / 9.92 kg con mástil (+~0.08 kg tornillos por definir)\n• Motores DC: 13/13 · Brushless 2/2 · Servos 1/6\n"
            f"• {len(BOM)} piezas modeladas en {len(G)} subsistemas\n\nSubsistemas\n" + "\n".join(f"  {g}. {n}  ({sum(1 for b in BOM if b['g'] == g)} piezas)" for g, n in G.items()))
    fig.text(0.58, 0.33, info, fontsize=11, va="top", family="DejaVu Sans")
    footer(fig, page); pdf.savefig(fig); plt.close(fig); page += 1
    # explosionada global
    fig = plt.figure(figsize=A3); header(fig, "Vista explosionada general", "Globos = número de subsistema (ver hojas siguientes)")
    img, labs = crop("01_explosionada_global", M["meta"]["01_explosionada_global"])
    balloons(fig, [0.08, 0.06, 0.62, 0.84], img, labs, fs=13)
    img2, _ = crop("01b_explosionada_global_atras"); ax = fig.add_axes([0.73, 0.45, 0.25, 0.42]); ax.imshow(img2); ax.set_axis_off(); ax.set_title("Desde atrás", fontsize=10)
    fig.text(0.74, 0.40, "\n".join(f"{g}. {n}" for g, n in G.items()), fontsize=11, va="top")
    footer(fig, page); pdf.savefig(fig); plt.close(fig); page += 1
    # subsistemas
    for g in range(1, 10):
        rows = [(b["num"], pretty(b["name"])) for b in BOM if b["g"] == g]
        fig = plt.figure(figsize=A3); header(fig, f"{g}. {G[g]}", f"{len(rows)} piezas · explosión radial del subsistema")
        img, labs = crop(f"g{g}_explosionada", M["meta"][f"g{g}"])
        fs = 8 if len(labs) <= 30 else 6.5
        balloons(fig, [0.07, 0.05, 0.50, 0.85], img, labs, fs=fs)
        table(fig, [0.66, 0.05, 0.33, 0.86], rows, fs=7.5 if len(rows) <= 32 else 6.0, cols=1 if len(rows) <= 32 else 2)
        footer(fig, page); pdf.savefig(fig); plt.close(fig); page += 1
    # secuencia
    order = M["order"]
    for k0 in range(0, len(order), 2):
        fig = plt.figure(figsize=A3); header(fig, "Secuencia de ensamble", "En color: lo que se agrega en el paso · En gris: lo ya armado")
        for j, k in enumerate(range(k0, min(k0 + 2, len(order)))):
            gid = order[k]; img, _ = crop(f"s{k + 1:02d}_paso_{gid}")
            x = 0.03 + j * 0.49
            ax = fig.add_axes([x, 0.22, 0.45, 0.66]); ax.imshow(img); ax.set_axis_off()
            fig.text(x, 0.885, f"Paso {k + 1}: {G[gid]}", fontsize=14, weight="bold")
            fig.text(x, 0.19, "\n".join(textwrap.wrap(STEPS[gid], 78)), fontsize=10.5, va="top")
        footer(fig, page); pdf.savefig(fig); plt.close(fig); page += 1
    # lista completa
    rows = [(b["num"], f"{pretty(b['name'])}") for b in BOM]
    per = 150
    for k0 in range(0, len(rows), per):
        fig = plt.figure(figsize=A3); header(fig, "Lista de piezas (completa)", "Subsistema.pieza — nombre en el CAD (STEP)")
        table(fig, [0.03, 0.05, 0.94, 0.86], rows[k0:k0 + per], fs=6.3, cols=3)
        footer(fig, page); pdf.savefig(fig); plt.close(fig); page += 1
print("ok", page - 1, "hojas")
