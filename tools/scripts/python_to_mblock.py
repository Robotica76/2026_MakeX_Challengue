"""Turn a block-friendly mBlock Python program into an mBlock 5 block project (.mblock).

The inverse of simulation/field2d/mblock_project.py: the blocks this writes are translated back by
mBlock (and by mblock_project.py) into the same program, which the tests check.

Block-friendly Python (what blocks can express), as mBlock itself writes it:
  - module variables `NAME = number` (blocks start them at 0 on the robot: set real values in code)
  - custom blocks: `def name_N_N(a, b):` -> custom block "name %n %n" with number inputs; every
    function starts with `global <all variables>`; no return values, no local variables
  - statements: `var = expr`, `var += expr`, `if` / `else`, `while True:`, `while not (cond):`,
    `for count in range(n):` (loops start with mBlock's `time.sleep(0.001)`), `time.sleep(s)`,
    custom block calls, device calls (encoder motors, power expansion board, gamepad, timer)
  - expressions: numbers, variables, inputs, + - * / %, < > ==, and / or / not, abs(x),
    math.sqrt(x), math.sin/cos/tan(math.radians(x)), math.degrees(math.atan(x)), round(x), sensors
Comments directly above a statement become block comments.

Assets (stage, sprites, sounds) come from the 2025 project, so mBlock opens the file as one of its own.

    python tools/scripts/python_to_mblock.py software/robot/main/storm_breaker_2026.py
"""

import argparse
import ast
import io
import json
import random
import sys
import tokenize
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "simulation" / "field2d"))
from mblock_project import (BL_POWER, BL_STOP, ENCODER_GET, ROTATION_RESET, SENSORS, TIMER_RESET,  # noqa: E402
                            identifier)

TEMPLATE = REPO / "software" / "legacy" / "challenge_2025" / "Challenge_2025.n2.mblock"
ID_CHARS = "!#%()*+,-./:;=?@[]^_`{|}~ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
BIN = {ast.Add: "operator_add", ast.Sub: "operator_subtract", ast.Mult: "operator_multiply",
       ast.Div: "operator_divide", ast.Mod: "operator_mod"}
CMP = {ast.Lt: "operator_lt", ast.Gt: "operator_gt", ast.Eq: "operator_equals"}
MATH_DIRECT = {"sqrt": "sqrt", "floor": "floor", "ceil": "ceiling", "log": "ln", "log10": "log", "exp": "e ^"}
SENSOR_BY_CALL = {t.split("(")[0]: (op, f) for op, (t, f) in SENSORS.items()}
ENCODER_BY_VALUE = {v: op for op, v in ENCODER_GET.items()}


class BlockError(Exception):
    pass


def proccode(name: str) -> str:
    code = " ".join("%n" if part == "N" else part for part in name.split("_"))
    if identifier(code) != name:
        raise BlockError(f"function name {name!r} has no matching custom block name")
    return code


def dotted(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return ""


def is_mblock_sleep(stmt) -> bool:
    return (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and dotted(stmt.value.func) == "time.sleep"
            and isinstance(stmt.value.args[0], ast.Constant) and stmt.value.args[0].value == 0.001)


def number_text(value) -> str:
    return str(int(value)) if float(value).is_integer() and not isinstance(value, float) else repr(value)


class Writer:
    def __init__(self, source: str, seed: int = 76):
        self.tree = ast.parse(source)
        self.rng = random.Random(seed)
        self.blocks, self.comments = {}, {}
        self.var_ids, self.var_values = {}, {}
        self.procs = {}                                   # name -> (proccode, [arg ids], [arg names])
        self.args = []                                    # arg names of the function being written
        self.comment_at = {}
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                self.comment_at[tok.start[0]] = tok.string.lstrip("#").strip()
        self.used_comments = set()

    def new_id(self) -> str:
        while True:
            bid = "".join(self.rng.choice(ID_CHARS) for _ in range(20))
            if bid not in self.blocks and bid not in self.var_ids.values():
                return bid

    def block(self, opcode, parent, inputs=None, fields=None, **extra):
        bid = self.new_id()
        self.blocks[bid] = {"opcode": opcode, "next": None, "parent": parent, "inputs": inputs or {},
                            "fields": fields or {}, "shadow": False, "topLevel": parent is None, **extra}
        return bid

    # -- expressions -------------------------------------------------------------------------
    def number(self, node, parent, text_slot=False):
        """Input for a number slot: literal, variable, input or reporter block."""
        kind = 10 if text_slot else 4
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return [1, [kind, number_text(node.value)]]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
            return [1, [kind, "-" + number_text(node.operand.value)]]
        if isinstance(node, ast.Name) and node.id in self.var_ids and node.id not in self.args:
            return [3, [12, node.id, self.var_ids[node.id]], [kind, ""]]
        return [3, self.reporter(node, parent), [kind, ""]]

    def boolean(self, node, parent):
        return [2, self.reporter(node, parent)]

    def reporter(self, node, parent) -> str:
        if isinstance(node, ast.Name):
            if node.id in self.args:
                return self.block("argument_reporter_string_number", parent, fields={"VALUE": [node.id, None]})
            raise BlockError(f"line {node.lineno}: {node.id} is not a variable or an input")
        if isinstance(node, ast.BinOp) and type(node.op) in BIN:
            bid = self.block(BIN[type(node.op)], parent)
            self.blocks[bid]["inputs"] = {"NUM1": self.number(node.left, bid), "NUM2": self.number(node.right, bid)}
            return bid
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in CMP:
            bid = self.block(CMP[type(node.ops[0])], parent)
            self.blocks[bid]["inputs"] = {"OPERAND1": self.number(node.left, bid),
                                          "OPERAND2": self.number(node.comparators[0], bid)}
            return bid
        if isinstance(node, ast.BoolOp):
            op = "operator_and" if isinstance(node.op, ast.And) else "operator_or"
            bid = self.block(op, parent)
            rest = node.values[1:]
            right_node = rest[0] if len(rest) == 1 else ast.BoolOp(op=node.op, values=rest)
            self.blocks[bid]["inputs"] = {"OPERAND1": self.boolean(node.values[0], bid),
                                          "OPERAND2": self.boolean(right_node, bid)}
            return bid
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            bid = self.block("operator_not", parent)
            self.blocks[bid]["inputs"] = {"OPERAND": self.boolean(node.operand, bid)}
            return bid
        if isinstance(node, ast.Call):
            return self.call_reporter(node, parent)
        raise BlockError(f"line {node.lineno}: {ast.unparse(node)!r} has no block")

    def mathop(self, op, arg, parent):
        bid = self.block("operator_mathop", parent, fields={"OPERATOR": [op, None]})
        self.blocks[bid]["inputs"] = {"NUM": self.number(arg, bid)}
        return bid

    def call_reporter(self, node, parent) -> str:
        name = dotted(node.func)
        a = node.args
        if name == "abs":
            return self.mathop("abs", a[0], parent)
        if name == "round":
            bid = self.block("operator_round", parent)
            self.blocks[bid]["inputs"] = {"NUM": self.number(a[0], bid)}
            return bid
        if name in ("math.sin", "math.cos", "math.tan") and isinstance(a[0], ast.Call) and dotted(a[0].func) == "math.radians":
            return self.mathop(name.split(".")[1], a[0].args[0], parent)
        if name == "math.degrees" and isinstance(a[0], ast.Call) and dotted(a[0].func) in ("math.atan", "math.asin", "math.acos"):
            return self.mathop(dotted(a[0].func).split(".")[1], a[0].args[0], parent)
        if name.startswith("math.") and name[5:] in MATH_DIRECT:
            return self.mathop(MATH_DIRECT[name[5:]], a[0], parent)
        if name == "gamepad.get_joystick":
            return self.block("novapi.BT_CONTROLLER_JOYSTICK", parent, fields={"POSITION": [a[0].value, None]})
        if name == "gamepad.is_key_pressed":
            return self.block("novapi.BT_CONTROLLER_BUTTON_PRESSED", parent, fields={"BUTTON": [a[0].value, None]})
        if name in SENSOR_BY_CALL:
            op, fname = SENSOR_BY_CALL[name]
            return self.block(op, parent, fields={fname: [a[0].value, None]} if fname else {})
        if name.startswith("encoder_motor_") and name.endswith(".get_value"):
            port = name.split(".")[0][len("encoder_motor_"):]
            return self.block(ENCODER_BY_VALUE[a[0].value], parent, fields={"PORT": [port, None]})
        raise BlockError(f"line {node.lineno}: {name}() has no reporter block")

    # -- statements --------------------------------------------------------------------------
    def stack(self, stmts, parent) -> str:
        first = prev = None
        for stmt in stmts:
            if isinstance(stmt, (ast.Global, ast.Pass)):
                continue
            bid = self.statement(stmt, prev or parent)
            if bid is None:
                continue
            self.attach_comment(stmt, bid)
            if prev:
                self.blocks[prev]["next"] = bid
                self.blocks[bid]["parent"] = prev
                self.blocks[bid]["topLevel"] = False
            first, prev = first or bid, bid
        return first

    def attach_comment(self, stmt, bid):
        lines, line = [], stmt.lineno - 1
        while line in self.comment_at and line not in self.used_comments:
            lines.insert(0, self.comment_at[line])
            self.used_comments.add(line)
            line -= 1
        lines = [t for t in lines if t != "DO SOMETHING"]
        if lines:
            self.comments[self.new_id()] = {"blockId": bid, "x": 0, "y": 0, "width": 300, "height": 120,
                                            "minimized": False, "text": "\n".join(lines)}

    def substack(self, body, bid, loop=False):
        if loop and body and is_mblock_sleep(body[0]):
            body = body[1:]
        first = self.stack(body, bid)
        return [2, first] if first else None

    def statement(self, stmt, parent):
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            var = stmt.targets[0].id
            bid = self.block("data_setvariableto", parent, fields={"VARIABLE": [var, self.var_id(var)]})
            self.blocks[bid]["inputs"] = {"VALUE": self.number(stmt.value, bid, text_slot=True)}
            return bid
        if isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add):
            var = stmt.target.id
            bid = self.block("data_changevariableby", parent, fields={"VARIABLE": [var, self.var_id(var)]})
            self.blocks[bid]["inputs"] = {"VALUE": self.number(stmt.value, bid)}
            return bid
        if isinstance(stmt, ast.If):
            has_else = bool(stmt.orelse)
            bid = self.block("control_if_else" if has_else else "control_if", parent)
            inputs = {"CONDITION": self.boolean(stmt.test, bid)}
            sub = self.substack(stmt.body, bid)
            if sub:
                inputs["SUBSTACK"] = sub
            if has_else:
                sub2 = self.substack(stmt.orelse, bid)
                if sub2:
                    inputs["SUBSTACK2"] = sub2
            self.blocks[bid]["inputs"] = inputs
            return bid
        if isinstance(stmt, ast.While):
            test = stmt.test
            if isinstance(test, ast.Constant) and test.value is True:
                bid = self.block("control_forever", parent)
                sub = self.substack(stmt.body, bid, loop=True)
                self.blocks[bid]["inputs"] = {"SUBSTACK": sub} if sub else {}
                return bid
            if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
                if all(isinstance(s, ast.Pass) for s in stmt.body):
                    bid = self.block("control_wait_until", parent)
                    self.blocks[bid]["inputs"] = {"CONDITION": self.boolean(test.operand, bid)}
                    return bid
                bid = self.block("control_repeat_until", parent)
                inputs = {"CONDITION": self.boolean(test.operand, bid)}
                sub = self.substack(stmt.body, bid, loop=True)
                if sub:
                    inputs["SUBSTACK"] = sub
                self.blocks[bid]["inputs"] = inputs
                return bid
            raise BlockError(f"line {stmt.lineno}: use 'while True:' or 'while not (...):'")
        if isinstance(stmt, ast.For) and isinstance(stmt.iter, ast.Call) and dotted(stmt.iter.func) == "range":
            times = stmt.iter.args[0]
            times = times.args[0] if isinstance(times, ast.Call) and dotted(times.func) == "int" else times
            bid = self.block("control_repeat", parent)
            inputs = {"TIMES": self.number(times, bid)}
            sub = self.substack(stmt.body, bid, loop=True)
            if sub:
                inputs["SUBSTACK"] = sub
            self.blocks[bid]["inputs"] = inputs
            return bid
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            return self.call_statement(stmt.value, parent)
        raise BlockError(f"line {stmt.lineno}: {ast.unparse(stmt)!r} has no block")

    def call_statement(self, call, parent):
        name, a = dotted(call.func), call.args
        if name == "time.sleep":
            bid = self.block("control_wait", parent)
            self.blocks[bid]["inputs"] = {"DURATION": self.number(a[0], bid)}
            return bid
        if name == "novapi.reset_timer":
            return self.block(TIMER_RESET, parent)
        if name == "novapi.reset_rotation":
            return self.block(ROTATION_RESET, parent, fields={"AXIS": [a[0].value, None]})
        if name in self.procs:
            code, ids, _ = self.procs[name]
            bid = self.block("procedures_call", parent, mutation={
                "tagName": "mutation", "children": [], "proccode": code, "argumentids": json.dumps(ids), "warp": "false"})
            self.blocks[bid]["inputs"] = {i: self.number(v, bid) for i, v in zip(ids, a)}
            return bid
        if name.startswith("power_expand_board."):
            port = a[0].value
            brushless = port.startswith("BL")                # BL1 / BL2 have their own blocks
            if name.endswith(".set_power"):
                op = BL_POWER if brushless else "novapi.POWER_EXPAND_DCmotor_power"
                bid = self.block(op, parent, fields={"CHANNEL": [port, None]})
                self.blocks[bid]["inputs"] = {"POWER": self.number(a[1], bid)}
                return bid
            op = BL_STOP if brushless else "novapi.POWER_EXPAND_DCmotor_stop"
            return self.block(op, parent, fields={"CHANNEL": [port, None]})
        if name.startswith("encoder_motor_"):
            port, method = name[len("encoder_motor_"):].split(".")
            if method == "set_speed":
                bid = self.block("novapi.encoder_motor_speed", parent, fields={"PORT": [port, None]})
                self.blocks[bid]["inputs"] = {"SPEED": self.number(a[0], bid)}
                return bid
            if method == "move":
                bid = self.block("novapi.encoder_motor_move", parent, fields={"PORT": [port, None]})
                self.blocks[bid]["inputs"] = {"POSITION": self.number(a[0], bid), "SPEED": self.number(a[1], bid)}
                return bid
        raise BlockError(f"line {call.lineno}: {name}() has no block")

    def var_id(self, name):
        if name not in self.var_ids:
            raise BlockError(f"{name} is not a module variable")
        return self.var_ids[name]

    # -- program -----------------------------------------------------------------------------
    def build(self):
        functions, main = [], []
        for node in self.tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                name = node.targets[0].id
                self.var_ids[name], self.var_values[name] = self.new_id(), node.value.value
            elif isinstance(node, ast.Assign):
                continue                                  # device objects: mBlock declares them itself
            elif isinstance(node, ast.FunctionDef):
                functions.append(node)
            else:
                main.append(node)
        for f in functions:
            names = [a.arg for a in f.args.args]
            self.procs[f.name] = (proccode(f.name), [self.new_id() for _ in names], names)
        x = 0
        for f in functions:
            code, ids, names = self.procs[f.name]
            self.args = names
            define = self.block("procedures_definition", None, x=x, y=0)
            proto = self.block("procedures_prototype", define, mutation={
                "tagName": "mutation", "children": [], "proccode": code, "argumentids": json.dumps(ids),
                "argumentnames": json.dumps(names), "argumentdefaults": json.dumps([""] * len(names)), "warp": "false"})
            self.blocks[proto]["shadow"] = True
            for aid, aname in zip(ids, names):
                shadow = self.block("argument_reporter_string_number", proto, fields={"VALUE": [aname, None]})
                self.blocks[shadow]["shadow"] = True
                self.blocks[proto]["inputs"][aid] = [1, shadow]
            self.blocks[define]["inputs"] = {"custom_block": [1, proto]}
            self.attach_comment(f.body[1] if len(f.body) > 1 else f.body[0], define)
            first = self.stack(f.body, define)
            if first:
                self.blocks[define]["next"] = first
                self.blocks[first]["parent"] = define
                self.blocks[first]["topLevel"] = False
            x += 700
        self.args = []
        hat = self.block("novapi.NovaPi main program setup", None, x=-700, y=0)
        first = self.stack(main, hat)
        if first:
            self.blocks[hat]["next"] = first
            self.blocks[first]["parent"] = hat
            self.blocks[first]["topLevel"] = False
        return self

    def project(self) -> dict:
        with zipfile.ZipFile(TEMPLATE) as z:
            data = json.loads(z.read("project.json"))
        for t in data["targets"]:
            if t.get("isStage"):
                t["variables"] = {vid: [name, self.var_values[name]] for name, vid in self.var_ids.items()}
            elif t["name"] == "novapi":
                t["blocks"], t["comments"] = self.blocks, self.comments
        data["monitors"] = [m for m in data["monitors"] if m["opcode"].startswith("novapi.motion_sensor")]
        return data


def python_to_project(source: str) -> dict:
    return Writer(source).build().project()


def write_mblock(source: str, out: Path) -> None:
    data = python_to_project(source)
    with zipfile.ZipFile(TEMPLATE) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            if item.filename == "project.json":
                dst.writestr("project.json", json.dumps(data, ensure_ascii=False))
            else:
                dst.writestr(item, src.read(item.filename))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("program", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="default: next to the program, .mblock")
    args = ap.parse_args(argv)
    out = args.output or args.program.with_suffix(".mblock")
    write_mblock(args.program.read_text(encoding="utf-8"), out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
