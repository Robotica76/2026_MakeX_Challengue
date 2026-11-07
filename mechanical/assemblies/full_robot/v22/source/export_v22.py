import sys, re; sys.path.insert(0, "/home/claude")
import cadquery as cq, robot_v22 as r
O = "/home/claude/out22"
dens = {"FLAG_mastil_tubo_CF_8x6": 1.6, "FLAG_cabeza_C_PETG": 0.75, "FLAG_ligas_x2": 1.1, "FLAG_pasador_R_D3": 7.85}
tot = 0.0
import os; os.makedirs(f"{O}/mastil_bandera_stl", exist_ok=True)
for n, s, c in r.mast_parts(0.0, flag=False):
    m = s.val().Volume() * dens[n] / 1000; tot += m; print(f"{n:30s} {m:6.1f} g")
    cq.exporters.export(s, f"{O}/mastil_bandera_stl/{n}.stl", tolerance=0.05, angularTolerance=0.1)
rc = r.receptor(); mr = rc.val().Volume() * 0.75 / 1000
cq.exporters.export(rc, f"{O}/mastil_bandera_stl/FLAG_receptor_mastil_PETG_(va_en_el_robot).stl", tolerance=0.05, angularTolerance=0.1)
print(f"MASTIL (pieza aparte) total {tot:.1f} g | receptor en el robot {mr:.1f} g")
a0 = r.build(mast=False, refs=False); a0.save(f"{O}/Robot_StormBreaker_v22_inicial.step")
shapes = []
for c in a0.children:
    s = c.obj.val() if hasattr(c.obj, "val") else c.obj
    shapes.append(s.moved(c.loc) if c.loc else s)
cq.exporters.export(cq.Workplane().add(cq.Compound.makeCompound(shapes)), f"{O}/Robot_StormBreaker_v22_inicial.stl", tolerance=0.2, angularTolerance=0.3)
a1 = r.build(mast=True, refs=True, zc=386.0); a1.save(f"{O}/Robot_StormBreaker_v22_con_mastil_y_bandera_carro_arriba.step")
print("ok")
