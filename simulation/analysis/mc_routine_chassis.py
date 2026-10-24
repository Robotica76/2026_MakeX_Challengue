# mc_routine_chassis.py - chassis.py moves measured one by one (simulator only).
# Each move is wrapped in simtrace.mark() calls, which record the simulator's TRUE
# pose; montecarlo_chassis.py compares it with the commanded move. simtrace does
# not exist on the robot, so this file is for the simulator.
import simtrace
import chassis as ch

# (label, kind, command)  kind: "drive" -> (forward_cm, right_cm), "turn_to" -> deg,
# "turn" -> relative deg (clockwise +). Starts in open floor, see montecarlo_config.json.
MOVES = [
    ("forward 60", "drive", (60, 0)),
    ("backward 60", "drive", (-60, 0)),
    ("right 30", "drive", (0, 30)),
    ("left 30", "drive", (0, -30)),
    ("diagonal 30/30", "drive", (30, 30)),
    ("diagonal back", "drive", (-30, -30)),
    ("turn_to 90", "turn_to", 90),
    ("turn_to 0", "turn_to", 0),
    ("turn -90", "turn", -90),
    ("turn 90", "turn", 90),
]

# Study overrides of chassis.py constants (montecarlo_chassis.py --set NAME=VALUE),
# applied here only; chassis.py itself is not modified.
for name, value in simtrace.options().get("chassis", {}).items():
    if not hasattr(ch, name):
        raise NameError("chassis.py has no constant " + name)
    setattr(ch, name, value)

ch.odo.calibrate(1.0)
ch.odo.reset()
for label, kind, command in MOVES:
    ch.odo.update()
    if kind == "drive":
        simtrace.mark(label, phase="start", kind=kind, forward_cm=command[0], right_cm=command[1])
        arrived = ch.drive(forward_cm=command[0], right_cm=command[1])
    elif kind == "turn_to":
        simtrace.mark(label, phase="start", kind="turn", turn_deg=ch.normalize(command - ch.odo.heading))
        arrived = ch.turn_to(command)
    else:
        simtrace.mark(label, phase="start", kind="turn", turn_deg=command)
        arrived = ch.turn(command)
    simtrace.mark(label, phase="end", arrived=arrived)
ch.stop()
