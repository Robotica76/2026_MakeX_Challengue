# auto_pull_central.py - automatic stage (30 s), red alliance, Red Start 1: pull the central
# resources onto our side of the field
#
# Strategy (team, 2026-10-31): do not store or shoot; drag as many central elements as possible
# onto our side, where the opponent cannot reach them (R06), and use them in the manual stage.
#   1. upper level of the central resource area: pull the balls off toward our side
#   2. lower level: the same
#   3. cones and bonus cubes on the strategy areas: pull them onto our floor
# Moving balls and props onto our own side is allowed (R23 only forbids the opponent's side or
# out of the arena).
#
# Pull mode: the intake head roller runs (DC7) with the throat off (DC1): what the head touches
# slides under the head toward the robot and drops in front of the body. Each table pass enters
# with the head above the balls (no contact, nothing pushed to the opponent), lowers it onto the
# level, and backs out pulling.
#
# Props: the head on a cone or cube on the strategy area pulls it off, but it drops at the centre
# line (x ~2220, half on the opponent side). A floor pass later, with the head low (50 mm, after
# the lower-level balls or right away), pulls it from the line onto our floor. Each lane takes the
# props under the head width: lane b (y 951) X12 + cone, lane a (y 570) X9 + cone.
#
# Route (simulation/analysis/optimize_auto_route.py, 2D simulator), all strategies: no contact
# with the field structures, no R06, stationary at 30 s (R19).
#   - one diagonal from the start to (1240, 950): clear of the cone post (200, 888) and the
#     resource-area legs (y <= 318); the body passes the fortress corner (982, 1208)
#   - table lanes at y 1437 / 1600 (the head fits between the table legs, y 1238-1817),
#     x 1800 -> 2100 (body front 2215 <= 2220); floor passes stop at x 1925 (head clear of the
#     strategy area dividers)
#   - the head starts toward the next pass height once it is clear of the table (x < 1920)
#   - a pass is only started if it can end before END_BY (a cut pass leaves the elements behind)
# Two bonus cubes on our side at most (p.30 d); they are not in the exchange area, so they only
# deny the opponent.
#
# Runs on its own, or imported by the competition program (software/robot/main/robot_2026.py),
# which calls run(strategy). Ports (robot_config.json, assumptions): DC2 intake head lift,
# DC7 intake head roller, DC1 intake throat.
import math
import time
from mbuild import power_expand_board as pb
import chassis as ch

# Task orders (simulation/analysis/optimize_auto_route.py, 2026-10-31; central elements left on our side):
#   "balls"  21-22 balls                                    done 27.0 s
#   "mixed"  16-17 balls + 1 cone + X12 (lower strategy area) done 25.1 s
#   "props"  11 balls + 2 cones + X9 + X12                  done 28.0 s (1 s margin)
# The props passes go first with the head high; the floor passes come once the head is low.
STRATEGY = "mixed"
STRATEGIES = {
    "balls": ["upper_b", "upper_a", "lower_a", "lower_b"],
    "mixed": ["props_low_b", "upper_b", "lower_b", "floor_low_b"],
    "props": ["props_low_b", "props_low_a", "floor_low_a", "floor_low_b", "lower_b"],
}

PLAN = {
    "tasks": STRATEGIES[STRATEGY],
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
    "floor_prop_height": 50.0,  # head on props lying on the floor (cube top 120 mm)
    "x_in_floor": 1925.0,      # floor props at the line (centre ~2220): head front 2210, clear of the dividers
}
try:                           # simulator only: route optimizer overrides
    import simtrace
    PLAN.update(simtrace.options())
    PLAN["tasks"] = STRATEGIES.get(PLAN.get("strategy"), PLAN["tasks"])
except ImportError:
    pass

LANES = {"upper_a": 1437.0, "upper_b": 1600.0, "lower_a": 1437.0, "lower_b": 1600.0,
         "props_low_a": 570.0, "props_low_b": 951.0, "props_up_a": 2103.0, "props_up_b": 2487.0}
LANES.update({"floor" + k[5:]: v for k, v in LANES.items() if k.startswith("props")})
HEAD_MM_S = 53.0
START_X, START_Y = 325.0, 325.0
END_BY = 29.0
HARD_STOP = 29.5
PASS_S = {"upper": 7.0, "lower": 7.0, "props": 5.5, "floor": 5.0}   # first estimate of a pass (s); then the longest measured
CLEAR_X = 1920.0           # robot centre x with the head (front 285 mm) clear of the central strip

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
    """Props on the strategy area top: the head on them pulls them off; they drop at the centre
    line (x ~2220, half on the opponent side), so a floor pass must follow."""
    head_to(approach_height(name))
    report(name + " lane", go_to(PLAN["x_far"], LANES[name]))
    finish_jobs()
    pb.set_power("DC7", 100)
    depth = PLAN["x_in_props"] if TASKS[name] == "props" else PLAN["x_in_floor"]
    report(name + " in", go_to(depth, LANES[name], speed=PLAN["approach_speed"], tol=1.0))
    time.sleep(0.2)
    pull_out(name, next_height)


TASKS = {"upper_a": "upper", "upper_b": "upper", "lower_a": "lower", "lower_b": "lower",
         "props_low_a": "props", "props_low_b": "props", "props_up_a": "props", "props_up_b": "props",
         "floor_low_a": "floor", "floor_low_b": "floor", "floor_up_a": "floor", "floor_up_b": "floor"}


def estimate(name):
    return pass_time.get(name[:5], PASS_S[name[:5]])


def approach_height(name):
    level = TASKS[name]
    if level == "props":
        return PLAN["prop_height"]
    if level == "floor":
        return PLAN["floor_prop_height"]
    return PLAN[level + "_heights"][0]


def main(calibrate=True):
    if calibrate:
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
        (props_pass if TASKS[name] in ("props", "floor") else table_pass)(name, nxt)
        pass_time[name[:5]] = max(pass_time.get(name[:5], 0.0), now() - t)
    finish_jobs()


def run(strategy=None, calibrate=True):
    """The automatic stage from now: `strategy` is a STRATEGIES key (default STRATEGY). Use it
    from the competition program (software/robot/main/robot_2026.py) with calibrate=False when
    the gyro was calibrated before the match."""
    global T0
    T0 = time.time()
    del jobs[:]
    pass_time.clear()
    head[:] = [0.0, 0.0, 0.0, 0.0]
    if strategy is not None:
        PLAN["tasks"] = STRATEGIES[strategy]
    manual_speed = ch.MAX_SPEED
    ch.MAX_SPEED = max(ch.MAX_SPEED, PLAN["travel_speed"])    # faster moves in this stage only
    try:
        main(calibrate)
    except Abort:
        report("safety stop")
    stop_all()
    ch.MAX_SPEED = manual_speed
    report("stopped")


if __name__ == "__main__":     # run on its own (simulator, or uploaded alone)
    run()
