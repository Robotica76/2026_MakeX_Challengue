# auto_pull_central.py - automatic stage (30 s), red alliance, Red Start 1: pull the central
# resources onto our side of the field
#
# Strategy (team, 2026-10-31): do not store or shoot; drag as many central elements as possible
# onto our side, where the opponent cannot reach them (R06), and use them in the manual stage.
#   1. upper level of the central resource area: pull the balls off toward our side
#   2. lower level: the same
#   3. cones and bonus cubes on the strategy areas: pull them off (only if there is time)
# Moving balls and props onto our own side is allowed (R23 only forbids the opponent's side or
# out of the arena).
#
# Pull mode: the intake head roller runs (DC7) with the throat off (DC1): what the head touches
# slides under the head toward the robot and drops in front of the body. Each table pass enters
# with the head above the balls (no contact, nothing pushed to the opponent), lowers it onto the
# level, and backs out pulling.
#
# Route (simulation/analysis/optimize_auto_route.py, 2D simulator, 2026-10-31): 4 table passes,
# upper b, upper a, lower a, lower b; 23 of the 30 central balls end on our side, done at 27 s,
# no contact with the field structures, no R06, stationary at 30 s (R19).
#   - one diagonal from the start to (1240, 950): clear of the cone post (200, 888) and the
#     resource-area legs (y <= 318); the body passes the fortress corner (982, 1208)
#   - lanes at y 1437 / 1600 (the head fits between the table legs, y 1238-1817), x 1800 -> 2100
#     (body front 2215 <= 2220)
#   - the head starts toward the next pass height once it is clear of the table (x < 1920)
#   - a pass is only started if it can end before END_BY (a cut pass leaves the balls behind)
# Props do not fit in 30 s with the head lift at 53 mm/s: a prop pulled off the strategy area
# drops at the centre line (x ~2200, half on the opponent side); bringing it to our side needs
# the head down at the floor (~4 s more). Leave them for the manual stage, or add "props_low_b"
# to the tasks if the head gets faster.
#
import math
import time
from mbuild import power_expand_board as pb
import chassis as ch

PLAN = {
    "tasks": ["upper_b", "upper_a", "lower_a", "lower_b"],
    "travel_speed": 200,       # RPM
    "approach_speed": 90,      # RPM, entering the table / strategy area
    "pull_out_speed": 60,      # RPM, backing out while pulling
    "tol_cm": 3.0,             # arrival tolerance at the lanes and after pulling out (in the table: 1 cm)
    "waypoint_tol_cm": 8.0,    # pass-by waypoint (fortress corner)
    "x_far": 1800.0,           # lane x, robot centre (body front 1915)
    "x_in": 2100.0,            # table depth: head over both ball rows, body front 2215 < 2220
    "x_in_props": 2000.0,      # strategy-area depth for props
    "upper_heights": (290.0, 250.0),   # head approach / pull height, upper level (ball centres 285)
    "lower_heights": (85.0, 50.0),     # lower level (ball centres 85)
    "prop_height": 250.0,      # head on the props (cones and cubes from 259 mm)
}
try:                           # simulator only: route optimizer overrides
    import simtrace
    PLAN.update(simtrace.options())
except ImportError:
    pass

LANES = {"upper_a": 1437.0, "upper_b": 1600.0, "lower_a": 1437.0, "lower_b": 1600.0,
         "props_low_a": 570.0, "props_low_b": 951.0, "props_up_a": 2103.0, "props_up_b": 2487.0}
HEAD_MM_S = 53.0
START_X, START_Y = 325.0, 325.0
END_BY = 29.0
HARD_STOP = 29.5
PASS_S = {"upper": 7.0, "lower": 7.0, "props": 5.5}   # first estimate of a pass (s); then the longest measured
CLEAR_X = 1920.0           # robot centre x with the head (front 285 mm) clear of the central strip

ch.MAX_SPEED = max(ch.MAX_SPEED, PLAN["travel_speed"])
T0 = time.time()
jobs = []
pass_time = {}
head = [0.0, 0.0, 0.0, 0.0]          # from mm, to mm, start s, end s


class Abort(Exception):
    pass


def now():
    return time.time() - T0


def stop_all():
    for port in ("DC1", "DC2", "DC7"):
        pb.stop(port)
    ch.stop()


def tick():
    if now() >= HARD_STOP:
        stop_all()
        raise Abort()
    for job in list(jobs):
        if now() >= job[1]:
            pb.stop(job[0])
            jobs.remove(job)


def finish_jobs():
    while jobs:
        tick()
        time.sleep(0.01)


def report(step, arrived=True):
    fx, fy = field_xy()
    print("%5.1f s  %-26s %-6s x %5.0f  y %5.0f  head %3.0f mm" % (
        now(), step, "ok" if arrived else "MISSED", fx, fy, head_now()))


def head_now():
    """Open-loop estimate of the intake head height (mm) from the last command."""
    h0, h1, t0, t1 = head
    if now() >= t1:
        return h1
    return h0 + (h1 - h0) * (now() - t0) / (t1 - t0)


def head_to(height):
    """Start moving the intake head to `height` (open loop, 53 mm/s); returns at once. A new
    command replaces a move still in progress, starting from where the head is estimated to be."""
    start = head_now()
    for job in [j for j in jobs if j[0] == "DC2"]:
        jobs.remove(job)
    delta = height - start
    if abs(delta) < 1:
        pb.stop("DC2")
        head[:] = [height, height, now(), now()]
        return
    pb.set_power("DC2", 100 if delta > 0 else -100)
    seconds = abs(delta) / HEAD_MM_S
    jobs.append(["DC2", now() + seconds])
    head[:] = [start, height, now(), now() + seconds]


def field_xy():
    return START_X + ch.odo.y * 10, START_Y - ch.odo.x * 10


def go_to(x, y, speed=None, timeout=6, on_cycle=tick, tol=None):
    fx, fy = field_xy()
    odx, ody = -(y - fy) / 10.0, (x - fx) / 10.0
    h = math.radians(ch.odo.heading)
    fwd = odx * math.sin(h) + ody * math.cos(h)
    right = odx * math.cos(h) - ody * math.sin(h)
    return ch.drive(forward_cm=fwd, right_cm=right, speed=speed or PLAN["travel_speed"],
                    timeout=timeout, on_cycle=on_cycle, tol_cm=tol or PLAN["tol_cm"])


def pull_out(name, next_height):
    """Back out to the lane with the head roller pulling. Once the head is clear of the table or
    the strategy area, the head starts moving to the next pass height (saves the wait)."""
    state = {"moved": False}

    def cycle():
        tick()
        if not state["moved"] and next_height is not None and field_xy()[0] < CLEAR_X:
            head_to(next_height)
            state["moved"] = True

    pb.set_power("DC7", 100)
    arrived = go_to(PLAN["x_far"], LANES[name], speed=PLAN["pull_out_speed"], on_cycle=cycle)
    pb.stop("DC7")
    report(name + " out", arrived)


def table_pass(name, next_height):
    approach, pull = PLAN[TASKS[name] + "_heights"]
    head_to(approach)
    report(name + " lane", go_to(PLAN["x_far"], LANES[name]))
    finish_jobs()
    report(name + " in", go_to(PLAN["x_in"], LANES[name], speed=PLAN["approach_speed"], tol=1.0))
    head_to(pull)
    finish_jobs()
    pull_out(name, next_height)


def props_pass(name, next_height):
    head_to(PLAN["prop_height"])
    report(name + " lane", go_to(PLAN["x_far"], LANES[name]))
    finish_jobs()
    pb.set_power("DC7", 100)
    report(name + " in", go_to(PLAN["x_in_props"], LANES[name], speed=PLAN["approach_speed"], tol=1.0))
    time.sleep(0.2)
    pull_out(name, next_height)


TASKS = {"upper_a": "upper", "upper_b": "upper", "lower_a": "lower", "lower_b": "lower",
         "props_low_a": "props", "props_low_b": "props", "props_up_a": "props", "props_up_b": "props"}


def estimate(name):
    return pass_time.get(name[:5], PASS_S[name[:5]])


def approach_height(name):
    level = TASKS[name]
    return PLAN["prop_height"] if level == "props" else PLAN[level + "_heights"][0]


def main():
    ch.odo.calibrate(0.5)
    ch.odo.reset()
    tasks = PLAN["tasks"]
    head_to(approach_height(tasks[0]))                # head up while travelling
    report("past the fortress corner", go_to(1240.0, 950.0, timeout=5, tol=PLAN["waypoint_tol_cm"]))
    for i, name in enumerate(tasks):
        if now() + estimate(name) > END_BY:          # a cut pass leaves the balls on the table
            report("no time for " + name)
            break
        nxt = None                                    # head pre-move only if the next pass will run
        if i + 1 < len(tasks) and now() + estimate(name) + estimate(tasks[i + 1]) <= END_BY:
            nxt = approach_height(tasks[i + 1])
        t = now()
        (props_pass if TASKS[name] == "props" else table_pass)(name, nxt)
        pass_time[name[:5]] = max(pass_time.get(name[:5], 0.0), now() - t)
    finish_jobs()


try:
    main()
except Abort:
    report("safety stop")
stop_all()
report("stopped")
