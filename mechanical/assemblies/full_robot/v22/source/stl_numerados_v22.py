"""STL por pieza del v22 con la numeracion del manual (subsistema.pieza), en el marco del robot, repartidos por subsistema."""
import sys, json, os, re; sys.path.insert(0, "/home/claude")
import cadquery as cq, robot_v22 as m
O = "/home/claude/out22/stl_numerados/mechanical"
FOLD = {1: "chassis", 2: "chassis", 3: "feeder", 4: "ball_intake", 5: "gripper_elevation", 6: "gripper", 7: "shooter", 8: "ball_storage", 9: "flag_system", 10: "common_parts"}
bom = json.load(open("/home/claude/out22/explosionada/meta.json"))["bom"]
num = {b["name"]: (b["num"], b["g"]) for b in bom}
asm = m.build(mast=True, refs=False, screws=True, zc=28.0)
rows = []
for c in asm.children:
    if c.name not in num: print("sin numero", c.name); continue
    n, g = num[c.name]
    s = c.obj.val() if hasattr(c.obj, "val") else c.obj
    s = s.moved(c.loc) if c.loc else s
    d = f"{O}/{FOLD[g]}/cad/v22"; os.makedirs(d, exist_ok=True)
    fn = f"{n}_{re.sub(r'[^A-Za-z0-9_.-]', '_', c.name)}.stl"
    cq.exporters.export(cq.Workplane().add(s), f"{d}/{fn}", tolerance=0.1, angularTolerance=0.2)
    bb = s.BoundingBox()
    rows.append(dict(num=n, g=g, folder=FOLD[g], file=fn, name=c.name, size=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)]))
json.dump(rows, open("/home/claude/out22/stl_numerados/index.json", "w"), indent=0)
print(len(rows), "STL")
