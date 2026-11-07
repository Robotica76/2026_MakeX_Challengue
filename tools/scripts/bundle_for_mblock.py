"""Bundle a robot program and the project modules it imports into one file for mBlock.

mBlock's Python editor uploads a single file to the NovaPi, while the project code is split
in modules (`import chassis as ch`, `import auto_pull_central as auto`). This tool inlines
every project module the program imports (recursively) and rewrites the references:

    ch.drive(...)  ->  chassis_drive(...)      (module-level names get the module prefix,
    ch.MAX_SPEED = 200  ->  chassis_MAX_SPEED   a `global` is added where a function assigns)

Other imports (novapi, mbuild, time, math) are kept once at the top. An inlined module's
`if __name__ == "__main__":` block is dropped. Comments are not kept (the bundle is generated:
edit the source files and bundle again).

    python tools/scripts/bundle_for_mblock.py software/robot/main/robot_2026.py
    python tools/scripts/bundle_for_mblock.py software/robot/main/robot_2026.py -o build/robot.py

Modules are searched next to the program first, then under software/ (like the simulator).
"""

import argparse
import ast
from pathlib import Path
from typing import Dict, List, Optional, Set

REPO = Path(__file__).resolve().parents[2]
ROOTS = (REPO / "software",)


class BundleError(Exception):
    pass


def find_module(name: str, beside: Path, roots=ROOTS) -> Optional[Path]:
    near = beside / f"{name}.py"
    if near.is_file():
        return near
    found = sorted({p.resolve() for r in roots if r.is_dir() for p in r.rglob(f"{name}.py")
                    if "__pycache__" not in p.parts})
    if len(found) > 1:
        raise BundleError(f"'import {name}' is ambiguous: " + ", ".join(str(p) for p in found))
    return found[0] if found else None


def stored_names(nodes) -> Set[str]:
    """Names bound at this level (assignments, defs, classes, loop / with / except targets),
    not looking inside function or class bodies."""
    names: Set[str] = set()

    def visit(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        if isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        if isinstance(node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    for n in nodes:
        visit(n)
    return names


class Rewriter(ast.NodeTransformer):
    """Prefixes the module's top-level names (scope aware) and turns `alias.attr` of an inlined
    module into that module's prefixed name."""

    def __init__(self, prefix: str, toplevel: Set[str], aliases: Dict[str, str]):
        self.prefix, self.toplevel, self.aliases = prefix, toplevel, aliases
        self.scopes: List[Set[str]] = []          # local names of the enclosing functions
        self.function_globals: List[Set[str]] = []

    def new_name(self, name: str) -> str:
        if any(name in s for s in self.scopes):
            return name
        return self.prefix + name if name in self.toplevel else name

    def visit_Name(self, node):
        return ast.copy_location(ast.Name(self.new_name(node.id), node.ctx), node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in self.aliases and \
                not any(node.value.id in s for s in self.scopes):
            name = self.aliases[node.value.id] + node.attr
            if isinstance(node.ctx, ast.Store) and self.function_globals:
                self.function_globals[-1].add(name)
            return ast.copy_location(ast.Name(name, node.ctx), node)
        self.generic_visit(node)
        return node

    def visit_Global(self, node):
        node.names = [self.prefix + n if n in self.toplevel else n for n in node.names]
        return node

    def _function(self, node, args, body_nodes):
        declared = {n for b in ast.walk(ast.Module(body=body_nodes, type_ignores=[]))
                    if isinstance(b, ast.Global) for n in b.names}
        params = {a.arg for a in args.posonlyargs + args.args + args.kwonlyargs}
        params |= {a.arg for a in (args.vararg, args.kwarg) if a}
        self.scopes.append((params | stored_names(body_nodes)) - declared)
        self.function_globals.append(set())

    def visit_FunctionDef(self, node):
        node.name = self.new_name(node.name)
        node.decorator_list = [self.visit(d) for d in node.decorator_list]
        node.args.defaults = [self.visit(d) for d in node.args.defaults]
        self._function(node, node.args, node.body)
        node.body = [self.visit(b) for b in node.body]
        self.scopes.pop()
        extra = sorted(self.function_globals.pop())
        if extra:
            doc = isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant) \
                and isinstance(node.body[0].value.value, str)
            node.body.insert(1 if doc else 0, ast.Global(names=extra))
        return node

    def visit_Lambda(self, node):
        self._function(node, node.args, [ast.Expr(node.body)])
        node.body = self.visit(node.body)
        self.scopes.pop()
        self.function_globals.pop()
        return node

    def visit_ClassDef(self, node):
        node.name = self.new_name(node.name)
        node.bases = [self.visit(b) for b in node.bases]
        node.body = [self.visit(b) for b in node.body]       # methods: their own scopes
        return node

    def _comprehension(self, node):
        targets = {n.id for g in node.generators for n in ast.walk(g.target) if isinstance(n, ast.Name)}
        self.scopes.append(targets)
        self.generic_visit(node)
        self.scopes.pop()
        return node

    visit_ListComp = visit_SetComp = visit_DictComp = visit_GeneratorExp = _comprehension


class Bundler:
    def __init__(self, roots=ROOTS):
        self.roots = roots
        self.imports: List[str] = []
        self.sections: List[str] = []
        self.done: Dict[Path, str] = {}           # module path -> prefix
        self.active: Set[Path] = set()

    def add_import(self, node):
        text = ast.unparse(node)
        if text not in self.imports:
            self.imports.append(text)

    def module(self, path: Path, prefix: str, main: bool) -> None:
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        aliases: Dict[str, str] = {}
        body = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                keep = []
                for a in node.names:
                    local = find_module(a.name, path.parent, self.roots) if "." not in a.name else None
                    if local:
                        aliases[a.asname or a.name] = self.include(local, a.name)
                    else:
                        keep.append(a)
                if keep:
                    self.add_import(ast.Import(names=keep))
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module and find_module(node.module.split(".")[0], path.parent, self.roots):
                    raise BundleError(f"{path.name}: use 'import {node.module} as x', not 'from {node.module} import'")
                self.add_import(node)
            elif (not main and isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                  and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__"):
                continue                                         # module's own entry point
            else:
                body.append(node)
        toplevel = stored_names(body) if not main else set()
        rewritten = [Rewriter(prefix, toplevel, aliases).visit(n) for n in body]
        code = "\n".join(ast.unparse(n) for n in rewritten)
        rel = path.relative_to(REPO) if REPO in path.parents else path.name
        self.sections.append(f"# ---- {rel} ----\n{code}")

    def include(self, path: Path, name: str) -> str:
        path = path.resolve()
        if path in self.done:
            return self.done[path]
        if path in self.active:
            raise BundleError(f"circular import of {name}")
        self.active.add(path)
        prefix = name + "_"
        self.module(path, prefix, main=False)
        self.active.discard(path)
        self.done[path] = prefix
        return prefix

    def bundle(self, program: Path) -> str:
        program = program.resolve()
        self.module(program, "", main=True)
        head = [f"# {program.name} bundled for mBlock with tools/scripts/bundle_for_mblock.py (generated:",
                "# edit the source files and bundle again). Modules: "
                + (", ".join(p.name for p in self.done) or "none")]
        return "\n".join(head + self.imports + [""] + self.sections) + "\n"


def bundle(program: Path, roots=ROOTS) -> str:
    return Bundler(roots).bundle(Path(program))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("program", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="default: build/<program>_mblock.py")
    args = ap.parse_args(argv)
    out = args.output or REPO / "build" / f"{args.program.stem}_mblock.py"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(bundle(args.program), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB): paste it into mBlock's Python editor")


if __name__ == "__main__":
    main()
