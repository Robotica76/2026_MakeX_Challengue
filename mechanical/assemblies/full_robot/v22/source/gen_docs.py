"""Genera la documentacion v22 del repo (mechanical/<subsistema>/{README,cad,drawings,manufacturing,prototypes}) a partir del CAD."""
import json, os, re, shutil, subprocess
SRC = "/home/claude/out22/stl_numerados/mechanical"
OUT = "/mnt/user-data/outputs/mech_v22/mechanical"
PDF = "/home/claude/out22/Ensamble_StormBreaker_v22.pdf"
rows = json.load(open("/home/claude/out22/stl_numerados/index.json"))
G = {1: "Chassis and drive", 2: "Electronics box", 3: "Ball tower (transfer to basket)", 4: "Ball intake and UR arm", 5: "Gripper elevator and structure",
     6: "Carriage and gripper", 7: "Shooter (inverted launcher)", 8: "Basket and feed roller", 9: "Flag mast (Modification Stage)", 10: "Hardware"}
GES = {1: "Chasis y tracción", 2: "Caja de electrónica", 3: "Torre de pelotas", 4: "Intake y brazo UR", 5: "Mástil del elevador y estructura", 6: "Carro y pinza",
       7: "Lanzador", 8: "Canasta y alimentador", 9: "Mástil de bandera (Modification Stage)", 10: "Tornillería"}
FOLDERS = {"chassis": [1, 2], "feeder": [3], "ball_intake": [4], "gripper_elevation": [5], "gripper": [6], "shooter": [7], "ball_storage": [8], "flag_system": [9], "common_parts": [10]}
PDFPAGE = {g: 2 + g for g in range(1, 10)}          # hoja del manual de cada subsistema (portada=1, explosionada=2)
ASM = "../assemblies/full_robot/v22/README.md"
MANUAL = "../assemblies/full_robot/v22/docs/Ensamble_StormBreaker_v22.pdf"
def key(n): a, b = n.split("."); return (int(a), int(b))
def qty(name):
    m = re.search(r"_x(\d+)", name); return int(m.group(1)) if m else 1
def process(n):
    l = n.lower()
    if n.startswith("ELEC_"): return "Electronics (MakeX kit / purchase)", "—"
    if n.startswith("HW_") or re.search(r"tornillos?_m\d", l): return "Hardware (purchase)", "Steel"
    if "velcro" in l or "ligas" in l: return "Purchase", "Velcro" if "velcro" in l else "Rubber band"
    if "rodamiento" in l: return "Purchase (bearing 8x16x5)", "Steel"
    if "tornillo_t8" in l or "tornillo_avance" in l: return "Purchase (T8 lead screw + nut)", "Steel"
    if "pasador_r" in l: return "Purchase (R clip)", "Steel"
    if "_kit" not in l and ("tpu" in l or "petg" in l or "impres" in l):
        return "FDM print", "TPU" if "tpu" in l and "petg" not in l else ("PETG + TPU" if "tpu" in l else "PETG")
    if "collarin" in l: return "Purchase (8 mm shaft collar)", "Steel"
    if "nucleo" in l or "buje" in l: return "FDM print", "PETG"
    if re.search(r"motor|brushless|servo|esc_kit|sensor|camera", l): return "MakeX kit part", "—"
    if re.search(r"mecanum|slide_beam|square_beam|linear_motion|coupling|hub_|belt_connector|friction_wheel|bracket_kit|polea|poleas|banda|bandas|engrane|_kit", l) and "impres" not in l:
        return "MakeX kit / purchase", "—"
    if "tubo_cf" in l: return "Cut to length from CF tube", "Carbon fibre tube"
    m = re.search(r"cf(\d)", l)
    if m: return f"CNC / water-jet cut plate, {m.group(1)} mm", "Carbon fibre"
    if "al3" in l: return "CNC cut plate, 3 mm", "Aluminium"
    if re.search(r"tubo_al|_al$|d8_al|_al_|al_d8", l): return "Cut to length (rod / tube)", "Aluminium"
    if re.search(r"acero|eje|munon|munones|bisagra|collarin", l): return "Cut to length from rod", "Steel"
    if "tpu" in l: return "FDM print", "TPU"
    if "petg" in l or "impres" in l or "engranes_40t" in l: return "FDM print", "PETG"
    if re.search(r"_pc|pc_|pc\d", l):
        m = re.search(r"pc_?(\d)(?:_(\d))?mm|pc_(\d)(?:_(\d))?|pc(\d)mm", l)
        return "Cut / bend sheet", "Polycarbonate"
    if "chumacera" in l or "guarda" in l or "calzas" in l or "separador" in l or "patin" in l: return "FDM print", "PETG"
    return "TBD", "TBD"
def md_table(head, body):
    s = "| " + " | ".join(head) + " |\n| " + " | ".join("---" for _ in head) + " |\n"
    for r in body: s += "| " + " | ".join(str(x) for x in r) + " |\n"
    return s
def w(path, txt):
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "w").write(txt)
INFO = json.load(open("/home/claude/docs_v22/info.json"))
for folder, gs in FOLDERS.items():
    base = f"{OUT}/{folder}"
    parts = sorted([r for r in rows if r["g"] in gs], key=lambda r: key(r["num"]))
    # --- STL (copiados) ---
    os.makedirs(f"{base}/cad/v22", exist_ok=True)
    for r in parts: shutil.copy(f"{SRC}/{folder}/cad/v22/{r['file']}", f"{base}/cad/v22/{r['file']}")
    I = INFO[folder]
    title = I["title"]
    # --- drawings: hojas del manual ---
    dr = []
    for g in gs:
        if g == 10: continue
        stem = f"v22_{g}_{re.sub(r'[^a-z0-9]+', '_', G[g].lower()).strip('_')}_exploded"
        os.makedirs(f"{base}/drawings/v22", exist_ok=True)
        subprocess.run(["pdfseparate", "-f", str(PDFPAGE[g]), "-l", str(PDFPAGE[g]), PDF, f"{base}/drawings/v22/{stem}.pdf"], check=True)
        subprocess.run(["pdftoppm", "-f", str(PDFPAGE[g]), "-l", str(PDFPAGE[g]), "-r", "110", "-png", "-singlefile", PDF, f"{base}/drawings/v22/{stem}"], check=True)
        dr.append((g, stem))
    for f, cap in I.get("drawings_extra", []):
        shutil.copy(f, f"{base}/drawings/v22/{os.path.basename(f)}"); dr.append((None, os.path.basename(f)[:-4] + "|" + cap))
    # --- prototypes: figuras de simulacion ---
    sims = []
    for f, cap in I.get("sims", []):
        os.makedirs(f"{base}/prototypes/v22", exist_ok=True); shutil.copy(f, f"{base}/prototypes/v22/{os.path.basename(f)}"); sims.append((os.path.basename(f), cap))
    # ===== cad/README.md =====
    t = f"# {title} CAD\n\n" + I["cad_intro"] + "\n\n## Revisions\n\n" + md_table(["Revision", "Parts", "Integration"], [["[v22](v22/)", f"{len(parts)} numbered STL (this page)", f"[Storm Breaker v22](../{ASM})"]])
    t += ("\n## v22 · Numbered parts\n\nFile name = `<subsystem>.<part>_<CAD name>.stl`, the same numbering as the "
          f"[assembly manual](../{MANUAL}) (sheet{'s' if len(gs) > 1 else ''} {', '.join(str(PDFPAGE[g]) for g in gs if g != 10) or '—'}). Within a subsystem, part 1 is the largest by volume.\n\n"
          "- Every STL is exported in the **robot frame at its assembled position** (mm; origin on the floor at the centre of the 500 × 500 envelope; `+y` forward, `+x` right, `+z` up), so the files drop into place together. Re-orient each part on the build plate before printing.\n"
          "- Mesh tolerance 0.1 mm linear / 0.2 rad angular. Use the STEP in [full_robot/v22](../" + ASM.replace("README.md", "cad/") + ") for engineering changes.\n"
          "- Kit parts (motors, wheels, beams, gears, belts) and electronics are included only as **reference geometry** for fit checks; do not print them.\n"
          "- A file whose name ends in `_xN` holds N identical instances in one mesh.\n\n")
    for g in gs:
        pg = [r for r in parts if r["g"] == g]
        t += f"### {g}. {G[g]} ({len(pg)} parts)\n\n" + md_table(["No.", "File", "Size X × Y × Z (mm)", "Process"], [[r["num"], f"[`{r['file']}`](v22/{r['file']})", " × ".join(f"{v:g}" for v in r["size"]), process(r["name"])[0]] for r in pg]) + "\n"
    t += I.get("cad_notes", "")
    w(f"{base}/cad/README.md", t)
    # ===== drawings/README.md =====
    t = f"# {title} Drawings\n\nDrawings reference the local [CAD](../cad/README.md) revision. Released fabrication drawings (dimensions, tolerances, inspection datums) are **not** produced yet; the sheets below are assembly/identification drawings generated from the v22 CAD.\n\n## v22\n\n"
    body = []
    for g, stem in dr:
        if g is not None: body.append([f"[`{stem}.pdf`](v22/{stem}.pdf) · [PNG](v22/{stem}.png)", f"Exploded view of subsystem {g} ({G[g]}) with every part numbered and the parts list (sheet {PDFPAGE[g]} of the manual)"])
        else:
            s, cap = stem.split("|"); body.append([f"[`{s}.png`](v22/{s}.png)", cap])
    t += md_table(["File", "Content"], body) if body else "No subsystem sheet (hardware is listed in the manual's parts list).\n"
    t += f"\nFull manual (all subsystems, assembly sequence, complete parts list): [Ensamble_StormBreaker_v22.pdf](../{MANUAL}).\n\n**Pending for release:** fabrication drawings with dimensions and tolerances for the custom parts (CF plates, PC sheets, prints), hole patterns, and inspection datums.\n"
    w(f"{base}/drawings/README.md", t)
    # ===== manufacturing/README.md =====
    t = f"# {title} Manufacturing\n\nManufacturing plan for revision v22, derived from the CAD part names. **Nothing has been fabricated yet;** processes and materials are the CAD intent and must be confirmed against stock, kit contents, and the released [drawings](../drawings/README.md).\n\n## v22 · Bill of materials and process\n\n"
    t += md_table(["No.", "Part (CAD name)", "Qty", "Process", "Material", "STL"], [[r["num"], f"`{r['name']}`", qty(r["name"]), *process(r["name"]), f"[STL](../cad/v22/{r['file']})"] for r in parts])
    cnt = {}
    for r in parts: cnt[process(r["name"])[0]] = cnt.get(process(r["name"])[0], 0) + 1
    t += "\n### Summary by process\n\n" + md_table(["Process", "Lines"], sorted(cnt.items(), key=lambda x: -x[1]))
    t += "\n## Assembly\n\n" + I["assembly"] + "\n\n## Inspection checkpoints\n\n" + "\n".join(f"- [ ] {c}" for c in I["inspection"]) + "\n"
    w(f"{base}/manufacturing/README.md", t)
    # ===== prototypes/README.md =====
    t = f"# {title} Prototypes\n\n**Status (v22): no physical prototype has been built.** The figures below are CAD-based simulations (2D single-ball contact models or rigid-body estimates); they define what to measure, not results.\n\n"
    if sims: t += "## Simulation evidence (v22 design inputs)\n\n" + md_table(["Figure", "What it shows"], [[f"[`{f}`](v22/{f})", c] for f, c in sims]) + "\n"
    t += "## Test plan\n\n" + md_table(["Test", "Measure", "Pass criterion (from CAD / simulation)"], I["tests"]) + "\nRecord each test with date, robot revision, configuration, number of trials, and raw data before changing the design.\n"
    w(f"{base}/prototypes/README.md", t)
    # ===== README.md del subsistema =====
    t = f"# {title}\n\n> **Revision v22 (CAD only).** Parts {', '.join(f'{g}.x ({G[g]})' for g in gs)} of the [Storm Breaker v22 manual]({MANUAL}). Not built or measured yet.\n\n"
    for sec in ("Purpose", "Competition Capabilities", "Requirements", "Mechanical Interfaces", "Electrical Interfaces", "Software Interfaces", "Design", "Current Status", "Testing", "Known Issues"):
        t += f"## {sec}\n\n{I['readme'][sec]}\n\n"
    t += "## Documentation map\n\n" + md_table(["Folder", "Content"], [["[cad](cad/README.md)", f"{len(parts)} numbered STL, robot frame"], ["[drawings](drawings/README.md)", "Exploded, numbered sheets from the manual"], ["[manufacturing](manufacturing/README.md)", "BOM with process / material, assembly steps, checks"], ["[prototypes](prototypes/README.md)", "Simulation evidence and test plan"]])
    t += "\n## Related GitHub Issues\n\nTBD: link actual design and validation issues when created.\n"
    w(f"{base}/README.md", t)
    print(folder, len(parts), "partes")
