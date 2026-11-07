"""Vistas explosionadas, numeracion de piezas y secuencia de ensamble del Storm Breaker v22 (renders VTK + metadatos JSON)."""
import sys, json, math, os
sys.path.insert(0, "/home/claude")
import vtk, numpy as np, cadquery as cq
import robot_v22 as m
O = "/home/claude/out22/explosionada"
GROUPS = [  # (id, nombre, prefijos, offset explosion global)
    (1, "Chasis y tracción", ("CH_",), (0, 0, -330)),
    (2, "Caja de electrónica", ("ELB_", "ELEC_"), (0, -430, -140)),
    (3, "Torre de pelotas", ("TW_",), (0, -40, 60)),
    (4, "Intake y brazo UR", ("INT_",), (0, 430, -60)),
    (5, "Mástil del elevador y estructura", ("MAS_", "ELV_", "RIG_separador", "RIG_cuaderna"), (420, -80, 40)),
    (6, "Carro y pinza", ("CAR_", "GR_", "FLAG_receptor"), (760, -60, 40)),
    (7, "Lanzador", ("SH_", "RIG_base", "RIG_postes"), (-480, 0, 160)),
    (8, "Canasta y alimentador", ("CN_",), (-60, 260, 460)),
    (9, "Mástil de bandera (Modification Stage)", ("FLAG_",), (760, -60, 520)),
    (10, "Tornillería", ("HW_",), None),
]
def group_of(n):
    for gid, gname, pre, off in GROUPS:
        if n.startswith(pre): return gid
    return None
asm = m.build(mast=True, refs=False, screws=True, zc=28.0)
parts = []
for c in asm.children:
    g = group_of(c.name)
    if g is None: print("sin grupo:", c.name); continue
    s = c.obj.val() if hasattr(c.obj, "val") else c.obj
    s = s.moved(c.loc) if c.loc else s
    V, F = s.tessellate(0.12 if "mecanum" in c.name else 0.3, 0.25)
    pts = vtk.vtkPoints()
    for p in V: pts.InsertNextPoint(p.x, p.y, p.z)
    cells = vtk.vtkCellArray()
    for f in F:
        cells.InsertNextCell(3); [cells.InsertCellPoint(i) for i in f]
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells)
    nrm = vtk.vtkPolyDataNormals(); nrm.SetInputData(pd); nrm.SetFeatureAngle(35)
    mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(nrm.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(mp)
    col = c.color.toTuple() if c.color else (0.7, 0.7, 0.7, 1)
    if "guarda" in c.name: col = (col[0], col[1], col[2], 0.25)
    bb = s.BoundingBox()
    V3 = np.array([(p.x, p.y, p.z) for p in V]) if len(V) else np.zeros((1, 3))
    cen = np.array([bb.center.x, bb.center.y, bb.center.z])
    anchor = V3[np.argmin(((V3 - cen) ** 2).sum(1))]          # punto de la pieza mas cercano al centro de su caja (para la flecha)
    parts.append(dict(name=c.name, g=g, actor=a, col=col, cen=cen, anchor=anchor, vol=s.Volume()))
print(len(parts), "piezas")
# numeracion: por grupo, piezas ordenadas de mayor a menor volumen
num = {}
for gid, *_ in GROUPS:
    ps = sorted([p for p in parts if p["g"] == gid], key=lambda p: -p["vol"])
    for k, p in enumerate(ps, 1): p["num"] = f"{gid}.{k}"
ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
for p in parts: ren.AddActor(p["actor"])
hl = vtk.vtkLight(); hl.SetLightTypeToHeadlight(); hl.SetIntensity(0.85); ren.AddLight(hl)
l1 = vtk.vtkLight(); l1.SetLightTypeToSceneLight(); l1.SetPosition(600, 900, 2200); l1.SetFocalPoint(0, 0, 300); l1.SetIntensity(0.35); ren.AddLight(l1)
ren.UseFXAAOn(); ren.UseDepthPeelingOn(); ren.SetMaximumNumberOfPeels(6)
W, H = 2000, 1400
rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.AddRenderer(ren); rw.SetSize(W, H); rw.SetAlphaBitPlanes(1); rw.SetMultiSamples(0)
def setup(vis, offsets=None, style=None, local=None):
    """vis: set de ids de pieza visibles; offsets: dict g->vec; local: dict idx->vec extra; style: idx->('gray'|None)"""
    for i, p in enumerate(parts):
        a = p["actor"]; a.SetVisibility(i in vis)
        off = np.zeros(3)
        if offsets and p["g"] in offsets and offsets[p["g"]] is not None: off = off + np.array(offsets[p["g"]], float)
        if local and i in local: off = off + local[i]
        a.SetPosition(*off); p["off"] = off
        pr = a.GetProperty(); r, g, b, al = p["col"]
        if style and style.get(i) == "gray": pr.SetColor(0.80, 0.81, 0.83); pr.SetOpacity(0.35)
        else: pr.SetColor(r, g, b); pr.SetOpacity(al)
        pr.SetSpecular(0.2); pr.SetSpecularPower(20)
def snap(fn, direction=(1.0, 0.85, 0.65), zoom=1.0, labels=None):
    cam = ren.GetActiveCamera()
    vis = [p for p in parts if p["actor"].GetVisibility()]
    lo = np.min([p["cen"] + p["off"] for p in vis], 0); hi = np.max([p["cen"] + p["off"] for p in vis], 0)
    fp = (lo + hi) / 2; d = np.array(direction, float); d /= np.linalg.norm(d)
    cam.SetFocalPoint(*fp); cam.SetPosition(*(fp + d * 3000)); cam.SetViewUp(0, 0, 1); cam.SetViewAngle(30)
    ren.ResetCamera(); cam.Zoom(zoom); ren.ResetCameraClippingRange(); rw.Render()
    w = vtk.vtkWindowToImageFilter(); w.SetInput(rw); w.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(f"{O}/{fn}.png"); wr.SetInputConnection(w.GetOutputPort()); wr.Write()
    meta = []
    if labels is not None:
        for i in labels:
            p = parts[i]; wpt = p["anchor"] + p["off"]
            ren.SetWorldPoint(*wpt, 1.0); ren.WorldToDisplay(); x, y, z = ren.GetDisplayPoint()
            meta.append(dict(num=p["num"], name=p["name"], x=x / W, y=1 - y / H))
    return meta
META = {}
ALL = set(range(len(parts)))
NOHW = {i for i, p in enumerate(parts) if p["g"] != 10}
offs = {gid: off for gid, _, _, off in GROUPS}
gname = {gid: n for gid, n, _, _ in GROUPS}
# 1) ensamblado completo
setup(ALL); snap("00_ensamblado_iso", (1.0, 0.9, 0.6), 1.15); snap("00_ensamblado_iso_atras", (-0.9, -1.0, 0.6), 1.15)
# 2) explosionada global (sin tornilleria) con globos por subsistema
setup(NOHW, offs)
lab = []
for gid in range(1, 10):
    idx = [i for i in NOHW if parts[i]["g"] == gid]
    big = max(idx, key=lambda i: parts[i]["vol"]); lab.append(big)
META["01_explosionada_global"] = snap("01_explosionada_global", (1.0, 0.75, 0.55), 1.12, lab)
for e in META["01_explosionada_global"]: e["num"] = e["num"].split(".")[0]; e["name"] = gname[int(e["num"])]
META["01b_explosionada_global_atras"] = None; snap("01b_explosionada_global_atras", (-0.9, -0.85, 0.55), 1.12)
# 3) cada subsistema: explosion radial de sus piezas + numero de cada pieza
DIRS = {1: (1, 0.8, 0.9), 2: (0.6, -1, 0.9), 3: (1, 0.3, 0.4), 4: (1, 0.9, 0.6), 5: (1, -0.6, 0.5), 6: (1, 0.4, 0.5), 7: (-1, 0.6, 0.5), 8: (0.6, 0.9, 1.0), 9: (1, 0.6, 0.4)}
K = {1: 0.9, 2: 1.4, 3: 0.75, 4: 0.9, 5: 1.0, 6: 1.1, 7: 1.0, 8: 1.0, 9: 1.6}
for gid in range(1, 10):
    idx = [i for i in NOHW if parts[i]["g"] == gid]
    c0 = np.mean([parts[i]["cen"] for i in idx], 0)
    loc = {i: (parts[i]["cen"] - c0) * K[gid] for i in idx}
    setup(set(idx), None, None, loc)
    META[f"g{gid}"] = snap(f"g{gid}_explosionada", DIRS[gid], 1.0, sorted(idx, key=lambda i: parts[i]["num"]))
# 4) secuencia de ensamble (acumulativa)
ORDER = [1, 2, 3, 4, 5, 6, 7, 8, 10, 9]
done = []
for k, gid in enumerate(ORDER, 1):
    vis = {i for i, p in enumerate(parts) if p["g"] in done + [gid]}
    style = {i: "gray" for i in vis if parts[i]["g"] in done}
    setup(vis, None, style); snap(f"s{k:02d}_paso_{gid}", (1.0, 0.9, 0.6) if gid != 2 else (-0.8, -1.0, 0.7), 1.1)
    done.append(gid)
bom = [dict(num=p["num"], name=p["name"], g=p["g"]) for p in sorted(parts, key=lambda p: (p["g"], int(p["num"].split(".")[1])))]
json.dump(dict(meta=META, bom=bom, groups={g: n for g, n, _, _ in GROUPS}, order=ORDER), open(f"{O}/meta.json", "w"), ensure_ascii=False, indent=0)
print("ok")
