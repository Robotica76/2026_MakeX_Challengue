#!/usr/bin/env python3
"""Genera el capítulo LaTeX "Software" a partir de los comentarios Doxygen de Robot.py.

Uso:
    python3 generate_software_doc.py [ruta/Robot.py] [--pdf]

Salida: generated/software.tex (incluido por main.tex). Con --pdf además
compila main.tex con pdflatex (si está instalado).

Cada ejecución regenera todo (listados de código, tablas, diagramas), por lo
que basta con volver a correrlo después de cambiar Robot.py o
design_decisions.json. Diagramas opcionales hechos a mano en TikZ:
diagrams/autonomous_flow.tex (se incluye si existe).
"""
import ast
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "software", "robot", "main", "Robot.py"))
OUT_DIR = os.path.join(HERE, "generated")
DECISIONS = os.path.join(HERE, "design_decisions.json")
MANUAL_DIAGRAM = os.path.join(HERE, "diagrams", "autonomous_flow.tex")

LATEX_SPECIAL = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def tex(text):
    """Escapa caracteres especiales de LaTeX."""
    return "".join(LATEX_SPECIAL.get(c, c) for c in text)


def tt(text):
    return r"\texttt{%s}" % tex(text)


# --------------------------------------------------------------------------
# Lectura de comentarios Doxygen
# --------------------------------------------------------------------------
def parse_doxygen(lines):
    """Devuelve {línea_siguiente_no_comentario: [(tag, texto), ...]}."""
    blocks, current = {}, []
    for i, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("#"):
            body = line.lstrip("#").strip()
            if body.startswith("@"):
                m = re.match(r"@(\S+)\s*(.*)", body)
                current.append([m.group(1), m.group(2)])
            elif current and body:
                current[-1][1] += " " + body
            continue
        if current and line:
            blocks[i + 1] = [tuple(t) for t in current]
        if line:
            current = []
    return blocks


def tag_values(tags, name):
    return [v for t, v in tags if t == name]


def first(tags, name, default=""):
    v = tag_values(tags, name)
    return v[0] if v else default


# --------------------------------------------------------------------------
# Análisis del código (AST)
# --------------------------------------------------------------------------
def call_name(node):
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            return f.attr
    return None


def analyse(src_text):
    tree = ast.parse(src_text)
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    calls = {}
    for name, fn in funcs.items():
        called = []
        for n in ast.walk(fn):
            c = call_name(n)
            if c in funcs and c != name and c not in called:
                called.append(c)
        calls[name] = called
    entry = [call_name(n.value) or "?" for n in tree.body
             if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
    entry_args = []
    for n in tree.body:
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):
            c = n.value
            entry_args.append((call_name(c), [ast.unparse(a) for a in c.args]))
    return tree, funcs, calls, entry_args


def key_bindings(fn, user_names=()):
    """Extrae (tecla, acción) de la cadena if/elif con is_key_pressed."""
    rows = []

    def key_of(test):
        for n in ast.walk(test):
            if (isinstance(n, ast.Call) and call_name(n) == "is_key_pressed"
                    and n.args and isinstance(n.args[0], ast.Constant)):
                return n.args[0].value
        return None

    user_funcs = set(user_names)

    def visit(stmts):
        for s in stmts:
            if isinstance(s, ast.If):
                k = key_of(s.test)
                if k:
                    # Se prefiere la primera llamada a una función propia del programa.
                    calls_in = [n for b in s.body for n in ast.walk(b) if call_name(n)]
                    own = [n for n in calls_in if call_name(n) in user_funcs]
                    acts = [ast.unparse((own or calls_in)[0])] if calls_in else []
                    rows.append((k, acts[0] if acts else "..."))
                    visit(s.orelse)
                else:
                    visit(s.body)
                    visit(s.orelse)
            elif isinstance(s, (ast.While, ast.For)):
                visit(s.body)

    visit(fn.body)
    return rows


# --------------------------------------------------------------------------
# Diagramas TikZ
# --------------------------------------------------------------------------
def tikz_id(name):
    return re.sub(r"[^A-Za-z0-9]", "", name)


def call_graph_tikz(funcs, calls):
    callers = {f: set() for f in funcs}
    for f, cs in calls.items():
        for c in cs:
            callers[c].add(f)
    level = {}

    def depth(f, stack=()):
        if f in level:
            return level[f]
        if f in stack:
            return 0
        d = 0 if not callers[f] else 1 + max(depth(p, stack + (f,)) for p in callers[f])
        level[f] = d
        return d

    for f in funcs:
        depth(f)
    cols = {}
    for f in funcs:
        cols.setdefault(level[f], []).append(f)
    out = [r"\begin{tikzpicture}[node distance=1cm, >=Stealth,",
           r"  fn/.style={draw,rounded corners,fill=blue!8,font=\footnotesize\ttfamily,minimum height=0.7cm,inner sep=4pt}]"]
    for lv in sorted(cols):
        for row, f in enumerate(cols[lv]):
            out.append(r"\node[fn] (%s) at (%.2f,%.2f) {%s};" %
                       (tikz_id(f), lv * 5.2, -row * 1.1, tex(f)))
    for f, cs in calls.items():
        for c in cs:
            out.append(r"\draw[->] (%s) -- (%s);" % (tikz_id(f), tikz_id(c)))
    out.append(r"\end{tikzpicture}")
    return "\n".join(out)


def boot_tikz(entry_args):
    out = [r"\begin{tikzpicture}[>=Stealth,",
           r"  st/.style={draw,rounded corners,fill=green!10,align=center,minimum width=3.2cm,minimum height=0.8cm,font=\footnotesize},",
           r"  fin/.style={draw,ellipse,fill=gray!15,font=\footnotesize}]",
           r"\node[fin] (start) at (0,0) {Encendido};"]
    prev = "start"
    for i, (name, args) in enumerate(entry_args):
        label = "%s(%s)" % (name, ", ".join(args))
        nid = "b%d" % i
        out.append(r"\node[st,below=0.6cm of %s] (%s) {%s};" % (prev, nid, tt(label)))
        out.append(r"\draw[->] (%s) -- (%s);" % (prev, nid))
        prev = nid
    out.append(r"\end{tikzpicture}")
    return "\n".join(out)


def main_loop_tikz(bindings):
    out = [r"\begin{tikzpicture}[>=Stealth,",
           r"  st/.style={draw,rounded corners,fill=orange!10,align=center,minimum width=3.6cm,font=\footnotesize},",
           r"  dc/.style={draw,diamond,aspect=2.6,fill=yellow!15,align=center,font=\scriptsize,inner sep=1pt}]",
           r"\node[st] (loop) at (0,0) {Inicio de iteraci\'on\\\texttt{while True}};"]
    prev = "loop"
    for i, (key, act) in enumerate(bindings):
        d, a = "d%d" % i, "a%d" % i
        out.append(r"\node[dc,below=0.55cm of %s] (%s) {Tecla \texttt{%s}?};" % (prev, d, tex(key)))
        out.append(r"\node[st,right=1.6cm of %s] (%s) {%s};" % (d, a, tt(act)))
        out.append(r"\draw[->] (%s) -- node[above,font=\scriptsize]{s\'i} (%s);" % (d, a))
        out.append(r"\draw[->] (%s) -- node[right,font=\scriptsize]{no} (%s);" % (prev, d))
        prev = d
    out.append(r"\node[st,below=0.7cm of %s] (drive) {Mover chasis con joysticks\\"
               r"\texttt{Checar\_Velocidades} + \texttt{Vel\_Motores}};" % prev)
    out.append(r"\draw[->] (%s) -- node[right,font=\scriptsize]{no} (drive);" % prev)
    for i in range(len(bindings)):
        out.append(r"\draw[->] (a%d.east) -- ++(0.6,0) |- (drive.east);" % i)
    out.append(r"\draw[->] (drive.west) -- ++(-1.2,0) |- (loop.west);")
    out.append(r"\end{tikzpicture}")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Construcción del capítulo
# --------------------------------------------------------------------------
def build(src_path, tex_base=HERE):
    """tex_base: carpeta desde la que se compila el .tex (rutas relativas de listados y diagramas)."""
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    lines = src.splitlines()
    blocks = parse_doxygen(lines)
    tree, funcs, calls, entry_args = analyse(src)
    decisions = {"intro": "", "decisions": []}
    if os.path.exists(DECISIONS):
        with open(DECISIONS, encoding="utf-8") as f:
            decisions = json.load(f)

    rel_src = os.path.relpath(src_path, tex_base).replace("\\", "/")
    file_tags = next((t for t in blocks.values() if any(k == "file" for k, _ in t)), [])
    out = []
    w = out.append

    w("% ARCHIVO GENERADO por generate_software_doc.py -- no editar a mano.")
    w(r"\chapter{Software}")
    w(r"\label{chap:software}")
    w(r"\lstset{language=Python,basicstyle=\ttfamily\scriptsize,numbers=left,numberstyle=\tiny,"
      r"breaklines=true,frame=single,keywordstyle=\color{blue},commentstyle=\color{gray},"
      r"inputencoding=utf8,extendedchars=true,"
      r"literate={á}{{\'a}}1 {é}{{\'e}}1 {í}{{\'i}}1 {ó}{{\'o}}1 {ú}{{\'u}}1 {ñ}{{\~n}}1 "
      r"{Á}{{\'A}}1 {É}{{\'E}}1 {Í}{{\'I}}1 {Ó}{{\'O}}1 {Ú}{{\'U}}1 {Ñ}{{\~N}}1}")
    if decisions.get("intro"):
        w(tex(decisions["intro"]) + "\n")

    # 1. Resumen
    w(r"\section{Descripci\'on general}")
    brief = first(file_tags, "brief")
    details = first(file_tags, "details")
    note = first(file_tags, "note")
    w(tex(brief) + "\n")
    if details:
        w(tex(details) + "\n")
    if note:
        w(r"\emph{Nota:} " + tex(note) + "\n")
    w("Archivo fuente: %s (%d l\\'ineas)." % (tt(os.path.basename(src_path)), len(lines)))

    # 2. Hardware y variables
    w(r"\section{Hardware y variables globales}")
    var_rows = []
    for tags in blocks.values():
        for t, v in tags:
            if t == "var":
                name, _, desc = v.partition(" ")
                var_rows.append((name, desc.strip()))
    if var_rows:
        w(r"\begin{longtable}{@{}p{0.28\linewidth}p{0.66\linewidth}@{}}\toprule")
        w(r"\textbf{Nombre} & \textbf{Descripci\'on} \\\midrule\endhead")
        for n, d in var_rows:
            w("%s & %s \\\\" % (tt(n), tex(d)))
        w(r"\bottomrule\end{longtable}")

    # 3. Ejecución
    w(r"\section{C\'omo se ejecuta el programa}")
    w(r"\subsection{Secuencia de arranque}")
    w("Instrucciones a nivel de m\\'odulo, ejecutadas en orden al encender el NovaPi:\n")
    w(r"\begin{figure}[H]\centering")
    w(boot_tikz(entry_args))
    w(r"\caption{Secuencia de arranque (generada del c\'odigo).}\end{figure}")

    if "main" in funcs:
        binds = key_bindings(funcs["main"], funcs)
        w(r"\subsection{Ciclo principal y botones del gamepad}")
        if binds:
            w(r"\begin{center}\begin{tabular}{@{}ll@{}}\toprule")
            w(r"\textbf{Tecla} & \textbf{Acci\'on} \\\midrule")
            for k, a in binds:
                w("%s & %s \\\\" % (tt(k), tt(a)))
            w(r"\bottomrule\end{tabular}\end{center}")
            w(r"\begin{figure}[H]\centering")
            w(main_loop_tikz(binds))
            w(r"\caption{Ciclo principal \texttt{main()}: se eval\'ua una sola acci\'on por iteraci\'on y siempre se actualiza el chasis.}\end{figure}")

    if os.path.exists(MANUAL_DIAGRAM):
        w(r"\subsection{Flujo de decisi\'on aut\'onomo}")
        w(r"\input{%s}" % os.path.relpath(MANUAL_DIAGRAM, tex_base).replace("\\", "/"))

    # 4. Arquitectura
    w(r"\section{Arquitectura: llamadas entre funciones}")
    w(r"\begin{figure}[H]\centering\resizebox{\linewidth}{!}{%")
    w(call_graph_tikz(funcs, calls))
    w(r"}\caption{Grafo de llamadas (generado con el an\'alisis del c\'odigo).}\end{figure}")

    # 5. Decisiones de diseño
    if decisions.get("decisions"):
        w(r"\section{Decisiones de dise\~no}")
        for d in decisions["decisions"]:
            w(r"\medskip\noindent\textbf{%s -- %s}\par" % (tex(d["id"]), tex(d["title"])))
            w(r"\textbf{Decisi\'on:} %s\\" % tex(d["decision"]))
            w(r"\textbf{Justificaci\'on:} %s" % tex(d["rationale"]) + "\n")

    # 6. Referencia de funciones
    w(r"\section{Referencia de funciones y c\'odigo}")
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        tags = blocks.get(node.lineno, [])
        w(r"\subsection{%s}" % tt(node.name))
        w(r"\label{fn:%s}" % tikz_id(node.name))
        w(tex(first(tags, "brief", "Sin descripci\u00f3n.")) + "\n")
        det = first(tags, "details")
        if det:
            w(tex(det) + "\n")
        params = [v.partition(" ") for v in tag_values(tags, "param")]
        if params:
            w(r"\begin{tabular}{@{}p{0.15\linewidth}p{0.78\linewidth}@{}}")
            w(r"\textbf{Par\'ametro} & \textbf{Descripci\'on} \\")
            for n, _, d in params:
                w("%s & %s \\\\" % (tt(n), tex(d.strip())))
            w(r"\end{tabular}\\[4pt]")
        for t, label in (("post", "Poscondici\u00f3n"), ("note", "Nota")):
            for v in tag_values(tags, t):
                w(r"\emph{%s:} %s\\" % (tex(label), tex(v)))
        if calls.get(node.name):
            w("Llama a: " + ", ".join(
                r"%s (\ref{fn:%s})" % (tt(c), tikz_id(c)) for c in calls[node.name]) + r"\\")
        end = node.end_lineno
        w(r"\lstinputlisting[firstline=%d,lastline=%d,firstnumber=%d]{%s}" %
          (node.lineno, end, node.lineno, rel_src))
    return "\n".join(out) + "\n"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = os.path.abspath(args[0]) if args else DEFAULT_SRC
    if not os.path.exists(src):
        sys.exit("No se encontró %s" % src)
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "software.tex")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build(src))
    print("Generado", os.path.relpath(out))
    if "--pdf" in sys.argv:
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"], cwd=HERE, check=True)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"], cwd=HERE, check=True)


if __name__ == "__main__":
    main()
