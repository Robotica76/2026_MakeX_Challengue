import sys, os; sys.path.insert(0,"/home/claude")
import robot_v22 as r
HR=float(os.environ.get("HR","0")); TH=float(os.environ.get("TH","0")); ZC=float(os.environ.get("ZC",r.elv.CAR_Z_RANGE[0])); OP=float(os.environ.get("OP",r.elv.OPEN_RANGE[1])); OBJ=os.environ.get("OBJ") or None; LRT=float(os.environ.get("LRT","0")); URZ=float(os.environ.get("URZ","93"))
asm=r.build(hood_rot=HR, theta=TH, zc=ZC, opening=OP, obj=OBJ, refs=bool(os.environ.get("REFS")), lr_t=LRT, ur_z=URZ, stop_open=bool(os.environ.get("SO")), screws=False, mast=bool(os.environ.get("MAST")))
items=[]
for c in asm.children:
    if c.name.startswith("REF_") and not c.name.startswith(("REF_cubo","REF_pino","REF_pelota_torre","REF_pelota_canasta")): continue
    s=c.obj.val() if hasattr(c.obj,"val") else c.obj
    items.append((c.name,s,s.BoundingBox()))
def ov(a,b): return a.xmin<b.xmax and b.xmin<a.xmax and a.ymin<b.ymax and b.ymin<a.ymax and a.zmin<b.zmax and b.zmin<a.zmax
hits=[]
for i in range(len(items)):
    n1,s1,b1=items[i]
    for j in range(i+1,len(items)):
        n2,s2,b2=items[j]
        if not ov(b1,b2): continue
        try: v=s1.intersect(s2).Volume()
        except Exception: v=-1
        if v>3: hits.append((round(v,1),n1,n2))
for h in sorted(hits,reverse=True): print(h)
print("TOTAL",len(hits),"| HR",HR,"TH",TH,"LRT",LRT,"URZ",URZ,flush=True)
bb=asm.toCompound().BoundingBox(); print("envolvente",round(bb.xmin,1),round(bb.xmax,1),round(bb.ymin,1),round(bb.ymax,1),round(bb.zmax,1))
