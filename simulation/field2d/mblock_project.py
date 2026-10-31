"""Translate an mBlock 5 block project (.mblock) for the NovaPi into the Python mBlock generates.

The output follows mBlock's own Python view of the same blocks (checked against the 2025
project, test_mblock_project.py): `import novapi`, `from mbuild ...` imports, the variables
initialised to 0, one object per device (encoder_motor_M1, smartservo_2, distance_sensor_1),
one function per custom block with every variable declared global, and the program under
"when NovaPi starts" at the end. Loops get `time.sleep(0.001)` and "wait until" a busy
`while not (...): pass`, as in mBlock. The file can be pasted into mBlock's Python editor.

Only what the file needs is read: project.json from the zip (no code in it is run). Blocks
the translator does not know raise MblockError with their opcodes, so a missing one is obvious.

    python mblock_project.py Challenge_2025.mblock -o challenge_2025.py
"""

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Optional


class MblockError(Exception):
    """The project cannot be translated (not an mBlock NovaPi project, or unknown blocks)."""


def read_project(path: Path) -> dict:
    try:
        with zipfile.ZipFile(path) as z:
            return json.loads(z.read("project.json").decode("utf-8"))
    except (zipfile.BadZipFile, KeyError, ValueError) as exc:
        raise MblockError(f"{Path(path).name} is not an mBlock 5 project: {exc}") from exc


def identifier(name: str) -> str:
    """mBlock's Python name for a custom block or variable: 'Avanzar %n' -> 'Avanzar_N',
    'cerrar_pinza-auto %n' -> 'cerrar_pinza_auto_N', 'girar_90°' -> 'girar_90_C2_B0'."""
    name = re.sub(r"%([nsb])", lambda m: m.group(1).upper(), name.strip())
    out = []
    for ch in name:
        if ch.isascii() and (ch.isalnum() or ch == "_"):
            out.append(ch)
        elif ch in " -":
            out.append("_")
        else:
            out.append("".join(f"_{b:02X}" for b in ch.encode("utf-8")))
    text = "".join(out)
    return "_" + text if text[:1].isdigit() else text


def literal(value) -> str:
    text = str(value)
    try:
        number = float(text)
    except ValueError:
        return repr(text)
    if text.strip() == "" or number != number:
        return repr(text)
    return str(int(number)) if number.is_integer() and "." not in text and "e" not in text.lower() else text.strip()


BINARY = {"operator_add": "+", "operator_subtract": "-", "operator_multiply": "*", "operator_divide": "/",
          "operator_mod": "%", "operator_lt": "<", "operator_gt": ">", "operator_equals": "==",
          "operator_and": "and", "operator_or": "or"}
MATHOP = {"abs": "abs({})", "floor": "math.floor({})", "ceiling": "math.ceil({})", "sqrt": "math.sqrt({})",
          "sin": "math.sin(math.radians({}))", "cos": "math.cos(math.radians({}))",
          "tan": "math.tan(math.radians({}))", "asin": "math.degrees(math.asin({}))",
          "acos": "math.degrees(math.acos({}))", "atan": "math.degrees(math.atan({}))",
          "ln": "math.log({})", "log": "math.log10({})", "e ^": "math.exp({})", "10 ^": "math.pow(10, {})"}
DECLARATIONS = {"novapi.smartservo_init", "novapi.distance_sensor_init"}


class Translator:
    def __init__(self, project: dict):
        self.project = project
        targets = project.get("targets", [])
        self.target = next((t for t in targets if any(isinstance(b, dict) and b.get("opcode", "").startswith("novapi.")
                                                      for b in t.get("blocks", {}).values())), None)
        if self.target is None:
            raise MblockError("no NovaPi blocks in this project")
        self.blocks: Dict[str, dict] = self.target["blocks"]
        self.variables: List[str] = []
        for t in targets:
            for name, *_ in t.get("variables", {}).values():
                if identifier(name) not in self.variables:
                    self.variables.append(identifier(name))
        self.comments: Dict[str, List[str]] = {}
        for c in self.target.get("comments", {}).values():
            if c.get("blockId"):
                self.comments.setdefault(c["blockId"], []).extend(c.get("text", "").splitlines())
        self.imports = set()
        self.motors, self.servos, self.sensors = [], {}, {}
        self.unknown = set()
        for b in self.blocks.values():                       # device declarations (init blocks)
            if isinstance(b, dict) and b.get("opcode") in DECLARATIONS:
                num, port = b["fields"]["NUM"][0], b["fields"]["PORT"][0]
                index = b["fields"].get("INDEX", ["INDEX1"])[0]
                (self.servos if "smartservo" in b["opcode"] else self.sensors)[num] = (port, index)

    # -- expressions ---------------------------------------------------------------------
    def value(self, block: dict, name: str, default: str = "0") -> str:
        slot = block.get("inputs", {}).get(name)
        if not slot or len(slot) < 2 or slot[1] is None:
            return default
        v = slot[1]
        if isinstance(v, str):
            return self.expr(v)
        if isinstance(v, list):
            if v[0] in (12, 13):                         # variable / list reporter
                return identifier(v[1])
            return literal(v[1])
        return default

    def field(self, block: dict, name: str) -> str:
        return str(block["fields"][name][0])

    def expr(self, bid: str) -> str:
        b = self.blocks[bid]
        op = b["opcode"]
        if op in BINARY:
            a, c = ("OPERAND1", "OPERAND2") if op in ("operator_lt", "operator_gt", "operator_equals",
                                                      "operator_and", "operator_or") else ("NUM1", "NUM2")
            return f"({self.value(b, a)} {BINARY[op]} {self.value(b, c)})"
        if op == "operator_not":
            return f"(not {self.value(b, 'OPERAND', 'False')})"
        if op == "operator_round":
            return f"round({self.value(b, 'NUM')})"
        if op == "operator_mathop":
            self.imports.add("math")
            return MATHOP[self.field(b, "OPERATOR")].format(self.value(b, "NUM"))
        if op == "operator_random":
            self.imports.add("random")
            return f"random.randint({self.value(b, 'FROM')}, {self.value(b, 'TO')})"
        if op == "operator_join":
            return f"(str({self.value(b, 'STRING1', repr(''))}) + str({self.value(b, 'STRING2', repr(''))}))"
        if op == "data_variable":
            return identifier(self.field(b, "VARIABLE"))
        if op == "argument_reporter_string_number" or op == "argument_reporter_boolean":
            return identifier(self.field(b, "VALUE"))
        if op == "math_number" or op == "text":
            return literal(next(iter(b["fields"].values()))[0])
        if op == "novapi.BT_CONTROLLER_JOYSTICK":
            self.imports.add("gamepad")
            return f'gamepad.get_joystick("{self.field(b, "POSITION")}")'
        if op == "novapi.BT_CONTROLLER_BUTTON_PRESSED":
            self.imports.add("gamepad")
            return f'gamepad.is_key_pressed("{self.field(b, "BUTTON")}")'
        if op == "novapi.distance_sensor_get_data":
            self.imports.add("ranging")
            num = self.field(b, "NUM")
            self.sensors.setdefault(num, ("PORT1", "INDEX1"))
            return f"distance_sensor_{num}.get_distance()"
        self.unknown.add(op)
        return "0"

    # -- statements ----------------------------------------------------------------------
    def stack(self, bid: Optional[str], ind: int) -> List[str]:
        lines = []
        while bid:
            b = self.blocks[bid]
            for text in self.comments.get(bid, []):
                lines.append(" " * ind + "# " + text)
            lines += self.statement(b, ind)
            bid = b.get("next")
        return lines

    def body(self, b: dict, name: str, ind: int, sleep: bool = False) -> List[str]:
        sub = b.get("inputs", {}).get(name)
        lines = [" " * ind + "time.sleep(0.001)"] if sleep else []
        if sleep:
            self.imports.add("time")
        lines += self.stack(sub[1] if sub and isinstance(sub[1], str) else None, ind)
        return lines or [" " * ind + "pass"]

    def statement(self, b: dict, ind: int) -> List[str]:
        op, pad = b["opcode"], " " * ind
        if op == "control_wait":
            self.imports.add("time")
            return [f"{pad}time.sleep({self.value(b, 'DURATION')})"]
        if op == "control_forever":
            return [f"{pad}while True:"] + self.body(b, "SUBSTACK", ind + 4, sleep=True)
        if op == "control_repeat":
            return [f"{pad}for count in range(int({self.value(b, 'TIMES')})):"] + self.body(b, "SUBSTACK", ind + 4, sleep=True)
        if op == "control_repeat_until":
            return [f"{pad}while not ({self.value(b, 'CONDITION', 'False')}):"] + self.body(b, "SUBSTACK", ind + 4, sleep=True)
        if op == "control_wait_until":
            return [f"{pad}while not ({self.value(b, 'CONDITION', 'False')}):", f"{pad}    # DO SOMETHING", f"{pad}    pass"]
        if op == "control_if":
            return [f"{pad}if {self.value(b, 'CONDITION', 'False')}:"] + self.body(b, "SUBSTACK", ind + 4)
        if op == "control_if_else":
            return ([f"{pad}if {self.value(b, 'CONDITION', 'False')}:"] + self.body(b, "SUBSTACK", ind + 4)
                    + [f"{pad}else:"] + self.body(b, "SUBSTACK2", ind + 4))
        if op == "data_setvariableto":
            return [f"{pad}{identifier(self.field(b, 'VARIABLE'))} = {self.value(b, 'VALUE')}"]
        if op == "data_changevariableby":
            return [f"{pad}{identifier(self.field(b, 'VARIABLE'))} += {self.value(b, 'VALUE')}"]
        if op == "procedures_call":
            m = b["mutation"]
            args = [self.value(b, a) for a in json.loads(m.get("argumentids", "[]"))]
            return [f"{pad}{identifier(m['proccode'])}({', '.join(args)})"]
        if op in ("novapi.encoder_motor_move", "novapi.encoder_motor_speed", "novapi.encoder_motor_power",
                  "novapi.encoder_motor_stop"):
            port = self.field(b, "PORT")
            if port not in self.motors:
                self.motors.append(port)
            call = {"novapi.encoder_motor_move": f"move({self.value(b, 'POSITION')}, {self.value(b, 'SPEED')})",
                    "novapi.encoder_motor_speed": f"set_speed({self.value(b, 'SPEED')})",
                    "novapi.encoder_motor_power": f"set_power({self.value(b, 'POWER')})",
                    "novapi.encoder_motor_stop": "stop()"}[op]
            return [f"{pad}encoder_motor_{port}.{call}"]
        if op == "novapi.POWER_EXPAND_DCmotor_power":
            self.imports.add("power")
            return [f'{pad}power_expand_board.set_power("{self.field(b, "CHANNEL")}", {self.value(b, "POWER")})']
        if op == "novapi.POWER_EXPAND_DCmotor_stop":
            self.imports.add("power")
            return [f'{pad}power_expand_board.stop("{self.field(b, "CHANNEL")}")']
        if op in ("novapi.smartservo_move_to", "novapi.smartservo_move"):
            num = self.field(b, "NUM")
            self.servos.setdefault(num, ("M1", "INDEX1"))
            method = "move_to" if op.endswith("move_to") else "move"
            return [f"{pad}smartservo_{num}.{method}({self.value(b, 'POSITION')}, {self.value(b, 'SPEED')})"]
        if op in DECLARATIONS:
            return []                                    # declared with the other devices
        self.unknown.add(op)
        return [f"{pad}pass  # unsupported block {op}"]

    # -- program -------------------------------------------------------------------------
    def translate(self) -> str:
        functions, main = [], []
        glob = f"    global {', '.join(self.variables)}" if self.variables else None
        for bid, b in self.blocks.items():
            if not isinstance(b, dict) or not b.get("topLevel"):
                continue
            if b["opcode"] == "procedures_definition":
                proto = self.blocks[b["inputs"]["custom_block"][1]]["mutation"]
                args = [identifier(a) for a in json.loads(proto.get("argumentnames", "[]"))]
                lines = [f"def {identifier(proto['proccode'])}({', '.join(args)}):"] + ([glob] if glob else [])
                lines += ["    # " + t for t in self.comments.get(bid, [])]
                code = self.stack(b.get("next"), 4)
                functions.append("\n".join(lines + (code or ([] if glob else ["    pass"]))))
            elif b["opcode"] == "novapi.NovaPi main program setup":
                main = self.stack(b.get("next"), 0)
            elif b["opcode"].startswith(("event_", "novapi.")) and b["opcode"].endswith(("pressed", "start", "when")):
                self.unknown.add(b["opcode"])                # other hats: not translated
            # loose stacks without a hat do not run on the robot either
        if self.unknown:
            raise MblockError("blocks the translator does not support yet: " + ", ".join(sorted(self.unknown)))
        head = ["# codes make you happy", "# generated from the blocks by simulation/field2d/mblock_project.py",
                "import novapi"]
        if self.sensors:
            head.append("from mbuild.ranging_sensor import ranging_sensor_class")
        if "gamepad" in self.imports:
            head.append("from mbuild import gamepad")
        if "power" in self.imports:
            head.append("from mbuild import power_expand_board")
        if self.motors:
            head.append("from mbuild.encoder_motor import encoder_motor_class")
        if self.servos:
            head.append("from mbuild.smartservo import smartservo_class")
        head += [f"import {m}" for m in ("math", "random") if m in self.imports] + ["import time"]
        out = head + ["", "# initialize variables"] + [f"{v} = 0" for v in self.variables] + ["", "# new class"]
        out += [f'distance_sensor_{n} = ranging_sensor_class("{p}", "{i}")' for n, (p, i) in sorted(self.sensors.items())]
        out += [f'encoder_motor_{p} = encoder_motor_class("{p}", "INDEX1")' for p in sorted(self.motors)]
        out += [f'smartservo_{n} = smartservo_class("{p}", "{i}")' for n, (p, i) in sorted(self.servos.items())]
        return "\n".join(out + [""] + ["\n\n".join(functions), ""] + main) + "\n"


def mblock_to_python(path: Path) -> str:
    return Translator(read_project(Path(path))).translate()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="write here (default: print)")
    args = ap.parse_args(argv)
    code = mblock_to_python(args.project)
    if args.output:
        args.output.write_text(code, encoding="utf-8")
    else:
        print(code, end="")


if __name__ == "__main__":
    main()
