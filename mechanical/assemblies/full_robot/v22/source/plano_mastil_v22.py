"""Plano 2D del mastil de bandera v22: detalle de la cabeza en C (corte en y = eje) y alturas con el carro abajo / arriba."""
import sys; sys.path.insert(0, "/home/claude")
import numpy as np, robot_v22 as r
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
def sec(shape, y):
    s = BRepAlgoAPI_Section(shape.val().wrapped, gp_Pln(gp_Pnt(0, y, 0), gp_Dir(0, 1, 0))); s.Build(); L = []
    ex = TopExp_Explorer(s.Shape(), TopAbs_EDGE)
    while ex.More():
        cu = BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); ts = np.linspace(cu.FirstParameter(), cu.LastParameter(), 30)
        L.append([(cu.Value(t).X(), cu.Value(t).Z()) for t in ts]); ex.Next()
    return L
P = {n: s for n, s, c in r.mast_parts(0.0, flag=True)}
y_cut = r.MY - r.HEAD_W / 2 + 8.0                   # plano de una liga
fig, axs = plt.subplots(1, 2, figsize=(22, 11), gridspec_kw=dict(width_ratios=[1.1, 1]))
ax = axs[0]
for n, col, lw in (("FLAG_cabeza_C_PETG", "tab:orange", 2), ("FLAG_mastil_tubo_CF_8x6", "k", 2), ("FLAG_ligas_x2", "tab:red", 3), ("REF_bandera_palo_8x8_300", "crimson", 1.5), ("REF_bandera_tela_400x300", "tab:blue", 1.5), ("REF_bandera_lazo", "tab:blue", 1.5)):
    ax.add_collection(LineCollection(sec(P[n], y_cut if "ligas" in n else r.MY), colors=col, lw=lw, label=n.replace("FLAG_", "").replace("REF_", "")))
h, (x_sp0, x_sp1, x_tip, zb, zt) = r.head()
def dim(a, b, txt, off=(0, 0), **k):
    ax.annotate("", a, b, arrowprops=dict(arrowstyle="<->", color="0.3", lw=1)); ax.text((a[0] + b[0]) / 2 + off[0], (a[1] + b[1]) / 2 + off[1], txt, fontsize=11, ha="center", **k)
dim((x_sp1, zb - 6), (x_tip, zb - 6), f"{x_tip - x_sp1:.0f}", (0, -5))
dim((x_tip + 6, zb + r.ARM_T), (x_tip + 6, zt), f"{zt - zb - r.ARM_T:.0f}", (8, 0))
dim((r.MX - 30, zb), (r.MX - 30, zt + r.ARM_T), f"{zt + r.ARM_T - zb:.0f}", (-9, 0))
dim((r.MX - 4, zb - 22), (x_tip, zb - 22), f"{x_tip - r.MX + 4:.0f}", (0, -5))
ax.text(x_tip + 3, zt + 10, "liga (2) en ranuras\nde las puntas", color="tab:red", fontsize=11)
ax.text(x_sp1 + 1.5, zb + r.ARM_T + 16, "palo de la\nbandera\n8x8 (<10x10)", color="crimson", fontsize=9)
ax.text(r.MX - 28, zt - 45, "tubo CF 8x6\n(entra 28 mm\nen la cabeza)", fontsize=10)
ax.set_xlim(r.MX - 45, x_tip + 40); ax.set_ylim(zb - 40, zt + 60); ax.set_aspect("equal"); ax.grid(alpha=.3)
ax.set_title("Cabeza en C (corte por el eje del mástil; ligas proyectadas). Medidas en mm", fontsize=13); ax.set_xlabel("x robot [mm] (→ afuera, lado derecho)"); ax.set_ylabel("z [mm] (carro abajo)")
ax.legend(loc="lower right", fontsize=9)
ax = axs[1]
lift = 386.0 - 28.0
ax.add_patch(plt.Rectangle((-250, 0), 500, 642, fc="0.85", ec="k")); ax.text(0, 320, "robot v22\n(642 mm sin mástil)", ha="center", fontsize=12)
for dz, col, lab in ((0.0, "tab:green", "carro ABAJO"), (lift, "tab:purple", "carro ARRIBA (+358)")):
    ax.plot([r.MX, r.MX], [r.SOCK_Z0 + dz, r.MAST_TOP + dz], color=col, lw=3)
    ax.add_patch(plt.Rectangle((r.MX - 4, zb + dz), x_tip - r.MX + 4, zt + r.ARM_T - zb, fc=col, alpha=0.6))
    pz = zb + r.ARM_T + 4.5 + dz
    ax.add_patch(plt.Rectangle((x_sp1 + 1, pz - 404), 3, 400, fc="tab:blue", alpha=0.25)); ax.text(x_tip + 8, zt + dz - 5, f"{lab}: punta {zt + r.ARM_T + dz:.0f}, palo {pz:.0f}", color=col, fontsize=11, va="top")
ax.axhspan(950, 965, color="tab:red", alpha=0.3); ax.text(-245, 970, "barra del campo para la bandera ≈ 950–965 mm (fig. 4.2-11)", color="tab:red", fontsize=11)
ax.axhline(700, color="0.4", ls=":"); ax.text(-245, 705, "700: límite de altura solo ANTES del Modification Stage", fontsize=9, color="0.3")
ax.set_xlim(-260, 520); ax.set_ylim(0, 1150); ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_xlabel("x robot [mm]"); ax.set_ylabel("z [mm]")
ax.set_title("Vista de frente: alturas del mástil con el elevador de la pinza", fontsize=13)
fig.suptitle("v22 — Mástil de bandera desmontable (se pone en el Modification Stage): tubo CF 8x6 en el receptor del bloque de la pinza + cabeza en C con liga", fontsize=14)
plt.tight_layout(rect=(0, 0, 1, 0.95)); plt.savefig("/home/claude/out22/plano_mastil_bandera_v22.png", dpi=90); print("ok")
