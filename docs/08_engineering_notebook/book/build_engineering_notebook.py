#!/usr/bin/env python3
"""Genera el Libro de Ingeniería (PDF) del equipo Robotica76 - MakeX 2026 StormBreaker.

Reúne en un solo documento LaTeX:
  * los documentos markdown del repositorio (requisitos, diseño, control, pruebas, ...),
  * el capítulo de Software generado desde los comentarios Doxygen de Robot.py,
  * datos vivos de GitHub: tablero del proyecto (organización/proyecto), issues, pull
    requests y commits (equipo, gestión, cronología).

Uso (desde cualquier carpeta del repositorio):
    python3 docs/08_engineering_notebook/book/build_engineering_notebook.py [opciones]

Opciones:
    --offline            No consulta GitHub; usa data/github_snapshot.json.
    --project-json FILE  Usa un export de `gh project item-list N --owner ORG --format json`.
    --no-pdf             Solo genera build/libro.tex (no compila).
    --skip-software      No regenera el capítulo Software (usa lo que haya en software_doc/generated).
    --config FILE        Otro book_config.json.
    --output FILE        Ruta del PDF final (por defecto output/Libro_de_Ingenieria.pdf).

Requisitos: python3, pandoc (>= 3), lualatex con fvextra/listings/tikz, fuente DejaVu, y
`gh` autenticado para los datos de GitHub (el tablero del proyecto necesita el permiso
`read:project`; sin él se usan los issues como respaldo y se avisa en el libro).
"""
import argparse
import collections
import datetime as dt
import glob
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
BUILD = os.path.join(HERE, "build")
DATA = os.path.join(HERE, "data")
SNAPSHOT = os.path.join(DATA, "github_snapshot.json")
FILTER = os.path.join(HERE, "filters", "notebook.lua")
PREAMBLE = os.path.join(HERE, "templates", "preamble.tex")
SOFTWARE_DOC = os.path.join(ROOT, "docs", "04_controls", "software_doc")

BOTS = ("app/", "copilot", "dependabot", "github-actions")
warnings = []


def warn(msg):
    warnings.append(msg)
    print("AVISO:", msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
LATEX_SPECIAL = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def tex(text):
    return "".join(LATEX_SPECIAL.get(c, c) for c in str(text if text is not None else ""))


def tt(text):
    return r"\texttt{%s}" % tex(text)


def run(cmd, cwd=ROOT, env=None, check=True):
    return subprocess.run(cmd, cwd=cwd, env=env, check=check, capture_output=True,
                          text=True, encoding="utf-8")


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def is_bot(login):
    return not login or login.lower().startswith(BOTS) or login.endswith("[bot]")


def display_login(login):
    return "Copilot (agente)" if login and login.startswith("app/copilot") else (login or "?")


# ---------------------------------------------------------------------------
# GitHub: proyecto, issues, PRs, commits
# ---------------------------------------------------------------------------
def gh_json(args):
    try:
        out = run(["gh"] + args).stdout
        return json.loads(out) if out.strip() else None
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        detail = getattr(e, "stderr", "") or str(e)
        warn("gh %s falló: %s" % (" ".join(args[:3]), detail.strip().splitlines()[-1] if detail.strip() else e))
        return None


def gh_paginated(endpoint, jq):
    try:
        out = run(["gh", "api", "--paginate", endpoint, "--jq", jq]).stdout
        return [json.loads(l) for l in out.splitlines() if l.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        warn("gh api %s falló: %s" % (endpoint, str(getattr(e, "stderr", e)).strip()[:120]))
        return None


def repo_slug(cfg):
    if cfg.get("repo"):
        return cfg["repo"]
    try:
        url = run(["git", "config", "--get", "remote.origin.url"]).stdout.strip()
        m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", url)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def collect_github(cfg, offline, project_json):
    """Devuelve {issues, prs, commits, project, project_source, fetched_at}."""
    cache = {}
    if os.path.exists(SNAPSHOT):
        with open(SNAPSHOT, encoding="utf-8") as f:
            cache = json.load(f)
    if offline:
        if not cache:
            warn("--offline sin data/github_snapshot.json: el libro no tendrá datos de GitHub")
        cache.setdefault("project_source", "snapshot")
        return cache

    data = dict(cache)
    slug = repo_slug(cfg)
    proj = cfg.get("project", {})
    if slug:
        issues = gh_json(["issue", "list", "-R", slug, "--state", "all", "--limit", "500", "--json",
                          "number,title,state,assignees,labels,createdAt,closedAt,url"])
        prs = gh_json(["pr", "list", "-R", slug, "--state", "all", "--limit", "500", "--json",
                       "number,title,state,author,createdAt,mergedAt,headRefName,url"])
        commits = gh_paginated(
            "repos/%s/commits?per_page=100" % slug,
            '.[]|{sha:.sha[0:7],date:.commit.author.date,name:.commit.author.name,'
            'login:(.author.login//""),msg:(.commit.message|split("\\n")[0])}')
        if issues is not None:
            data["issues"] = issues
        if prs is not None:
            data["prs"] = prs
        if commits is not None:
            data["commits"] = commits
    else:
        warn("No se pudo determinar el repositorio de GitHub")

    items = None
    if project_json:
        with open(project_json, encoding="utf-8") as f:
            items = json.load(f)
        data["project_source"] = "export manual (%s)" % os.path.basename(project_json)
    elif proj.get("owner") and proj.get("number"):
        items = gh_json(["project", "item-list", str(proj["number"]), "--owner", proj["owner"],
                         "--limit", "500", "--format", "json"])
        if items is not None:
            data["project_source"] = "API de GitHub Projects (proyecto %s/%s)" % (proj["owner"], proj["number"])
    if items is not None:
        data["project"] = items.get("items", items) if isinstance(items, dict) else items
    elif data.get("project"):
        warn("Tablero del proyecto no accesible: se usa la última copia guardada")
        data["project_source"] = data.get("project_source", "copia guardada") + " (copia anterior)"
    else:
        data.pop("project", None)
        data["project_source"] = "issues del repositorio (el tablero del proyecto no fue accesible)"

    data["fetched_at"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    os.makedirs(DATA, exist_ok=True)
    with open(SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


def board_items(gh):
    """Normaliza el tablero: lista de dicts {title, status, assignees, number, kind}."""
    items = []
    if gh.get("project"):
        for it in gh["project"]:
            content = it.get("content") or {}
            items.append({
                "title": it.get("title") or content.get("title") or "?",
                "status": it.get("status") or "Sin estado",
                "assignees": it.get("assignees") or [],
                "number": content.get("number"),
                "kind": content.get("type", "Issue"),
            })
    else:
        for i in gh.get("issues", []):
            items.append({
                "title": i["title"],
                "status": "Cerrado" if i["state"] == "CLOSED" else "Abierto",
                "assignees": [a["login"] for a in i.get("assignees", [])],
                "number": i["number"], "kind": "Issue",
            })
    return items


# ---------------------------------------------------------------------------
# Markdown -> LaTeX con pandoc
# ---------------------------------------------------------------------------
def md_title(text, path):
    m = re.search(r"^# +(.+?)\s*$", text, re.M)
    title = m.group(1) if m else os.path.splitext(os.path.basename(path))[0]
    if m:
        text = text[:m.start()] + text[m.end():]
    title = re.sub(r"[`*_]", "", title)
    return title, text


def md_to_tex(path, idx):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    title, body = md_title(text, path)
    env = dict(os.environ, NB_SRC_DIR=os.path.dirname(path), NB_REPO_ROOT=ROOT)
    cmd = ["pandoc", "-f", "gfm+footnotes", "-t", "latex", "--no-highlight", "--wrap=preserve",
           "--shift-heading-level-by=1", "--top-level-division=chapter",
           "--id-prefix=f%d-" % idx, "--lua-filter", FILTER]
    res = subprocess.run(cmd, input=body, env=env, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        warn("pandoc falló con %s: %s" % (rel(path), res.stderr.strip()[:200]))
        return title, r"\emph{No se pudo convertir este documento.}"
    out = res.stdout.replace(r"\begin{verbatim}", r"\begin{Verbatim}").replace(
        r"\end{verbatim}", r"\end{Verbatim}")
    return title, out


def expand_sources(specs):
    files, seen = [], set()
    for spec in specs:
        if isinstance(spec, str):
            spec = {"path": spec}
        min_chars = spec.get("min_chars", 0)
        excl = [re.compile(p) for p in spec.get("exclude", [])]
        paths = [spec["path"]] if "path" in spec else sorted(
            glob.glob(os.path.join(ROOT, spec["glob"]), recursive=True))
        for p in paths:
            p = p if os.path.isabs(p) else os.path.join(ROOT, p)
            if not os.path.isfile(p) or p in seen:
                if "path" in spec and not os.path.isfile(p):
                    warn("No existe %s (capítulo configurado)" % rel(p))
                continue
            r = rel(p)
            if any(e.search(r) for e in excl) or os.path.getsize(p) < min_chars:
                continue
            seen.add(p)
            files.append(p)
    return files


# ---------------------------------------------------------------------------
# Gráficas TikZ
# ---------------------------------------------------------------------------
def bar_chart(rows, width_cm=8.0, color="nbblue"):
    rows = [(l, v) for l, v in rows if v is not None]
    if not rows:
        return ""
    vmax = max(v for _, v in rows) or 1
    sc = width_cm / vmax
    out = [r"\begin{center}\begin{tikzpicture}"]
    for i, (label, v) in enumerate(rows):
        y = -i * 0.55
        out.append(r"\node[anchor=east,font=\scriptsize] at (0,%.2f) {%s};" % (y, tex(label)))
        out.append(r"\fill[%s] (0.1,%.2f) rectangle (%.2f,%.2f);" % (color, y - 0.18, 0.1 + v * sc, y + 0.18))
        out.append(r"\node[anchor=west,font=\scriptsize] at (%.2f,%.2f) {%s};" % (0.15 + v * sc, y, v))
    out.append(r"\end{tikzpicture}\end{center}")
    return "\n".join(out)


def longtable(headers, rows, spec):
    spec = spec.replace("p{", r">{\raggedright\arraybackslash}p{")
    out = [r"\begin{longtable}{%s}" % spec, r"\toprule",
           " & ".join(r"\textbf{%s}" % tex(h) for h in headers) + r" \\ \midrule\endhead"]
    for r in rows:
        out.append(" & ".join(r) + r" \\")
    out.append(r"\bottomrule\end{longtable}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Capítulos generados
# ---------------------------------------------------------------------------
def fmt_date(iso):
    return (iso or "")[:10]


def people(cfg, gh):
    """Une miembros configurados, asignados de issues, autores de commits y de PRs."""
    members = collections.OrderedDict()
    for m in cfg.get("members", []):
        members[m["github"]] = dict(m, tasks=[], commits=0, prs=0)
    def get(login):
        if login not in members:
            members[login] = {"github": login, "name": "", "role": "", "tasks": [], "commits": 0, "prs": 0}
        return members[login]
    for it in board_items(gh):
        for a in it["assignees"]:
            if not is_bot(a) and it["number"]:
                get(a)["tasks"].append(it)
    for c in gh.get("commits", []):
        if c.get("login") and not is_bot(c["login"]):
            p = get(c["login"])
            p["commits"] += 1
            if not p["name"]:
                p["name"] = c.get("name", "")
    for pr in gh.get("prs", []):
        login = (pr.get("author") or {}).get("login")
        if login and not is_bot(login):
            get(login)["prs"] += 1
    return members


def chapter_team(cfg, gh):
    ppl = people(cfg, gh)
    out = [r"\section{Integrantes y roles}",
           "Tabla generada con la configuraci\\'on del equipo (\\texttt{book\\_config.json}) y la "
           "actividad real registrada en GitHub: tareas asignadas en el tablero, commits y pull requests. "
           "Los roles vac\\'ios se completan editando \\texttt{book\\_config.json}.\n"]
    rows = []
    for p in ppl.values():
        tasks = ", ".join("T%s" % re.match(r"T(\d+)", t["title"]).group(1) if re.match(r"T\d+", t["title"])
                          else "#%s" % t["number"] for t in p["tasks"])
        rows.append([tt(p["github"]), tex(p["name"] or "--"), tex(p["role"] or "Por definir"),
                     tex(tasks or "--"), str(p["commits"]), str(p["prs"])])
    out.append(longtable(["GitHub", "Nombre", "Rol", "Tareas asignadas", "Commits", "PRs"], rows,
                         r"@{}p{2.8cm}p{3.2cm}p{2.8cm}p{4.2cm}p{1.2cm}p{0.9cm}@{}"))
    out.append(r"\subsection*{Participaci\'on: tareas asignadas}")
    out.append(bar_chart([(p["github"], len(p["tasks"])) for p in ppl.values() if p["tasks"]]))
    out.append(r"\subsection*{Participaci\'on: commits}")
    out.append(bar_chart([(p["github"], p["commits"]) for p in ppl.values() if p["commits"]], color="orange!80!black"))
    return "\n".join(out)


def chapter_project(cfg, gh):
    items = board_items(gh)
    proj = cfg.get("project", {})
    out = [r"\section{Tablero del proyecto}",
           "Fuente de los datos: %s. Actualizado: %s.\n" % (tex(gh.get("project_source", "?")), tex(gh.get("fetched_at", "?")))]
    if proj.get("owner"):
        out.append("Tablero: \\url{https://github.com/orgs/%s/projects/%s}\n" % (proj["owner"], proj["number"]))
    by_status = collections.OrderedDict()
    for it in items:
        by_status.setdefault(it["status"], []).append(it)
    out.append(bar_chart([(s, len(v)) for s, v in by_status.items()]))
    def key(it):
        m = re.match(r"T(\d+)", it["title"])
        return int(m.group(1)) if m else 999
    rows = []
    for status, its in by_status.items():
        for it in sorted(its, key=key):
            rows.append([tex("#%s" % it["number"] if it["number"] else ""), tex(it["title"]), tex(status),
                         tex(", ".join(it["assignees"]) or "Sin asignar")])
    out.append(longtable(["#", "Tarea", "Estado", "Responsables"], rows, r"@{}p{1cm}p{8cm}p{2.5cm}p{4.5cm}@{}"))
    return "\n".join(out)


def week_label(d):
    y, w, _ = dt.date.fromisoformat(d).isocalendar()
    return "%d-S%02d" % (y, w)


def chapter_timeline(cfg, gh):
    events = []
    for pr in gh.get("prs", []):
        who = display_login((pr.get("author") or {}).get("login"))
        events.append((fmt_date(pr["createdAt"]), "PR abierto", "#%s %s" % (pr["number"], pr["title"]), who))
        if pr.get("mergedAt"):
            events.append((fmt_date(pr["mergedAt"]), "PR integrado", "#%s %s" % (pr["number"], pr["title"]), who))
    for i in gh.get("issues", []):
        events.append((fmt_date(i["createdAt"]), "Tarea creada", "#%s %s" % (i["number"], i["title"]),
                       ", ".join(a["login"] for a in i.get("assignees", []))))
        if i.get("closedAt"):
            events.append((fmt_date(i["closedAt"]), "Tarea cerrada", "#%s %s" % (i["number"], i["title"]), ""))
    day_commits = collections.OrderedDict()
    for c in sorted(gh.get("commits", []), key=lambda c: c["date"]):
        if c["msg"].startswith("Merge pull request") or c["msg"].startswith("Merge branch"):
            continue
        day_commits.setdefault((fmt_date(c["date"]), c.get("name") or c.get("login") or "?"), []).append(c["msg"])
    for (d, who), msgs in day_commits.items():
        shown = "; ".join(msgs[:4]) + (" (+%d m\u00e1s)" % (len(msgs) - 4) if len(msgs) > 4 else "")
        events.append((d, "Cambios (%d commit%s)" % (len(msgs), "s" if len(msgs) != 1 else ""), shown, who))
    events.sort(key=lambda e: (e[0], e[1]))
    out = [r"\section{Cronolog\'ia del proceso}",
           "Registro cronol\\'ogico generado de GitHub: tareas, pull requests (ideas y cambios de dise\\~no o "
           "c\\'odigo) y commits. Las decisiones y sus justificaciones est\\'an en la bit\\'acora de dise\\~no.\n"]
    if not events:
        out.append(r"\emph{Sin datos de GitHub (ejecutar sin \texttt{--offline} para actualizar).}")
        return "\n".join(out)
    weekly = collections.Counter(week_label(e[0]) for e in events if e[0])
    out.append(r"\subsection*{Actividad por semana (eventos)}")
    out.append(bar_chart(sorted(weekly.items()), width_cm=7.5, color="green!50!black"))
    rows = [[tex(d), tex(k), tex(desc), tex(who)] for d, k, desc, who in events]
    out.append(longtable(["Fecha", "Tipo", "Descripci\u00f3n", "Autor"], rows, r"@{}p{1.9cm}p{2.6cm}p{8cm}p{3cm}@{}"))
    return "\n".join(out)


def chapter_software(skip):
    spec = importlib.util.spec_from_file_location("gen_sw", os.path.join(SOFTWARE_DOC, "generate_software_doc.py"))
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    src = gen.DEFAULT_SRC
    if skip:
        path = os.path.join(SOFTWARE_DOC, "generated", "software.tex")
        if not os.path.exists(path):
            warn("--skip-software pero no existe %s" % rel(path))
            return ""
        return open(path, encoding="utf-8").read()
    if not os.path.exists(src):
        warn("No existe %s" % rel(src))
        return ""
    return gen.build(src, tex_base=BUILD)


def judges_guide(cfg, chapters):
    keymap = {c.get("key"): c for c in chapters if c.get("key")}
    rows = []
    for crit in cfg.get("judging_criteria", []):
        refs = ", ".join(r"cap\'itulo~\ref{chap:%s}" % k for k in crit["chapters"] if k in keymap)
        rows.append([r"\textbf{%s}" % tex(crit["criterion"]), tex(crit["what"]), refs])
    return "\n".join([
        r"\section{C\'omo leer este libro}",
        tex(cfg.get("how_to_read", "")) + "\n",
        longtable(["Criterio de evaluaci\u00f3n", "Qu\u00e9 se documenta", "D\u00f3nde"], rows,
                  r"@{}p{3.6cm}p{7.2cm}p{4.2cm}@{}")])


def pending_report(included):
    rows = []
    for path, text in included:
        n = len(re.findall(r"\bTBD\b", text))
        if n:
            rows.append((n, path))
    rows.sort(reverse=True)
    out = [r"\section{Pendientes detectados en los documentos}",
           "Cada documento incluido se revisa en busca de marcadores \\texttt{TBD}; sirve de lista de "
           "pendientes antes de entregar el libro.\n"]
    if rows:
        out.append(longtable(["TBD", "Documento"], [[str(n), tt(p)] for n, p in rows], r"@{}p{1.2cm}p{13cm}@{}"))
    else:
        out.append("No se encontraron marcadores TBD.")
    return "\n".join(out)


def sources_index(included):
    rows = [[tt(p)] for p, _ in included]
    return "\n".join([r"\section{\'Indice de documentos fuente}",
                      "Archivos del repositorio incluidos en este libro (%d).\n" % len(rows),
                      longtable(["Archivo"], rows, r"@{}p{15cm}@{}")])


def cover(cfg):
    try:
        rev = run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()
        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    except Exception:
        rev, branch = "?", "?"
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    return "\n".join([
        r"\begin{titlepage}\centering\vspace*{3cm}",
        r"{\Huge\bfseries\color{nbblue} %s\par}\vspace{1cm}" % tex(cfg.get("title", "Libro de Ingenier\u00eda")),
        r"{\Large %s\par}\vspace{0.5cm}" % tex(cfg.get("subtitle", "")),
        r"{\large %s\par}\vspace{2cm}" % tex(cfg.get("team", "")),
        r"{\normalsize %s\par}" % tex(cfg.get("competition", "")),
        r"\vfill{\footnotesize Revisi\'on del repositorio: %s (%s) \\ Generado: %s \\ "
        r"Generado autom\'aticamente con \texttt{build\_engineering\_notebook.py}}" % (tt(rev), tex(branch), now),
        r"\end{titlepage}",
        r"\tableofcontents\clearpage"])


# ---------------------------------------------------------------------------
# Ensamblado
# ---------------------------------------------------------------------------
def build_book(cfg, gh, skip_software):
    chapters = cfg["chapters"]
    body, included = [], []
    idx = 0
    for ch in chapters:
        kind = ch.get("builtin")
        if kind == "software":
            sw = chapter_software(skip_software)
            if sw:
                intro = ch.get("intro", "")
                sw = sw.replace(r"\chapter{Software}", r"\chapter{%s}" % tex(ch["title"]), 1)
                sw = sw.replace(r"\label{chap:software}", r"\label{chap:%s}" % ch.get("key", "software"), 1)
                body.append(sw)
                if intro:
                    body.append(tex(intro) + "\n")
            continue
        parts = [r"\chapter{%s}" % tex(ch["title"])]
        if ch.get("key"):
            parts.append(r"\label{chap:%s}" % ch["key"])
        if ch.get("intro"):
            parts.append(tex(ch["intro"]) + "\n")
        for b in ch.get("builtin_sections", []):
            if b == "guide":
                parts.append(judges_guide(cfg, chapters))
            elif b == "team":
                parts.append(chapter_team(cfg, gh))
            elif b == "project":
                parts.append(chapter_project(cfg, gh))
            elif b == "timeline":
                parts.append(chapter_timeline(cfg, gh))
        for p in expand_sources(ch.get("sources", [])):
            idx += 1
            title, content = md_to_tex(p, idx)
            with open(p, encoding="utf-8") as f:
                included.append((rel(p), f.read()))
            parts.append(r"\section{%s}" % tex(title))
            parts.append(r"\nbsource{%s}" % tex(rel(p)))
            parts.append(content)
        if kind == "pending":
            parts.append(pending_report(included))
            parts.append(sources_index(included))
        body.append("\n".join(parts))
    return "\n\n".join(body), included


def compile_pdf(output):
    engine = shutil.which("lualatex")
    if not engine:
        sys.exit("No se encontró lualatex (instalar texlive-luatex y texlive-latex-extra).")
    log = ""
    for _ in range(2):
        res = subprocess.run([engine, "-interaction=nonstopmode", "libro.tex"], cwd=BUILD,
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        log = res.stdout
    pdf = os.path.join(BUILD, "libro.pdf")
    errors = re.findall(r"^! .*$", log, re.M)
    for e in errors[:10]:
        warn("LaTeX: " + e)
    if not os.path.exists(pdf):
        print(log[-3000:])
        sys.exit("No se generó el PDF (ver build/libro.log).")
    os.makedirs(os.path.dirname(output), exist_ok=True)
    shutil.copyfile(pdf, output)
    m = re.search(r"Output written on .*\((\d+) pages", log)
    return m.group(1) if m else "?"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--project-json")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--skip-software", action="store_true")
    ap.add_argument("--config", default=os.path.join(HERE, "book_config.json"))
    ap.add_argument("--output", default=os.path.join(HERE, "output", "Libro_de_Ingenieria.pdf"))
    a = ap.parse_args()

    if not shutil.which("pandoc"):
        sys.exit("Falta pandoc (>= 3): sudo apt install pandoc")
    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)

    os.makedirs(BUILD, exist_ok=True)
    print("1/4 Datos de GitHub...")
    gh = collect_github(cfg, a.offline, a.project_json)
    print("2/4 Convirtiendo documentos...")
    body, included = build_book(cfg, gh, a.skip_software)
    print("3/4 Escribiendo build/libro.tex (%d documentos)..." % len(included))
    with open(PREAMBLE, encoding="utf-8") as f:
        pre = f.read()
    doc = pre + "\n\\begin{document}\n" + cover(cfg) + "\n" + body + "\n\\end{document}\n"
    with open(os.path.join(BUILD, "libro.tex"), "w", encoding="utf-8") as f:
        f.write(doc)
    if a.no_pdf:
        return
    print("4/4 Compilando con lualatex (2 pasadas)...")
    pages = compile_pdf(a.output)
    print("Listo: %s (%s páginas)" % (rel(a.output), pages))
    if warnings:
        print("%d aviso(s); revisar arriba." % len(warnings))


if __name__ == "__main__":
    main()
