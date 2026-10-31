"""Ball dynamics and the ball path through the robot.

Free balls (mm, s): gravity, bounces on the floor, the field frame and the field
structures (axis-aligned boxes built from field_layout and the rules dimensions),
ball-ball collisions, rolling resistance, and pushes from the robot body and the
intake head. Balls at rest sleep until something touches them, so 70 balls run in
real time.

Inside the robot (robot_config.json "ball_path", from the v22 CAD reference balls):
a captured ball follows waypoints from the intake head through the tower and the
elbow into the basket, or waits in the tower when the basket is full (18 slots:
6 basket + 12 tower). The feeder moves the first basket ball to the shooter, which
launches it as a free ball. Each stretch moves only while its motor port has power:
intake (DC1), tower (DC4), feeder (DC5), shooter (BL1).

Simplifications: point-mass spheres (no spin), boxes instead of exact shapes, the
robot is infinitely heavy, balls inside the robot do not collide with each other.
Coefficients are estimates for EVA foam balls on the competition mat.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import field_layout as fl
from balls import BALL_D, Ball, Intake

R = BALL_D / 2
G = 9810.0                    # mm/s^2
E_FLOOR, E_WALL, E_BALL, E_ROBOT = 0.45, 0.4, 0.6, 0.3   # restitution, estimates
FRICTION_T = 0.15             # tangential speed lost per contact
ROLL_DECEL = 300.0            # mm/s^2 rolling resistance on the mat, estimate
SLEEP_SPEED = 15.0            # mm/s
SLEEP_TIME = 0.25             # s
CELL = 250.0                  # broad-phase grid, mm
TRANSIT_MIN_POWER = 10.0      # % below which a stretch of the ball path stops

Box = Tuple[float, float, float, float, float, float]   # x0, y0, z0, x1, y1, z1


# --- field colliders --------------------------------------------------------------------
def _rect_box(el, z0, z1, inset=0.0) -> Box:
    x0, y0, x1, y1 = el.bounds()
    return (x0 + inset, y0 + inset, z0, x1 - inset, y1 - inset, z1)


def field_colliders(elements: List[fl.Element]) -> List[Box]:
    """Structures as boxes, following simulation/field3d/field_model.py (rules p.13-22)."""
    boxes: List[Box] = []
    slots = [e for e in elements if e.kind == "slot"]
    for el in elements:
        if el.kind in ("zone", "slot") or el.z <= 0:
            continue
        x0, y0, x1, y1 = el.bounds()
        if el.kind == "overhead" and "_resource_" in el.name:
            sign = 1 if el.y < fl.CY else -1
            wall = el.y - sign * el.h / 2
            boxes.append((x0, y0, 738.5, x1, y1, 758.5))                       # shelves + box floor
            half = 373.0 / 2
            for side in (-1, 1):                                               # ball box walls
                bx = el.x + side * (half - 20)
                boxes.append((bx - 20, y0, 758.5, bx + 20, y1, el.z))
            front = wall + sign * el.h
            boxes.append((el.x - half, min(front, front - sign * 10), 758.5,
                          el.x + half, max(front, front - sign * 10), el.z - 60))
        elif el.kind == "overhead":                                            # flag poles
            boxes.append((x0, y0, el.z - 15, x1, y1, el.z))
        elif el.name.endswith("_back") and "_resource_" in el.name:
            boxes.append((x0, y0, 0.0, x1, y1, 700.0))
        elif el.name.startswith("strategy_"):
            boxes.append((x0, y0, el.z - 52.5, x1, y1, el.z))                  # top rail
            boxes.append((x0, y0, 0.0, x1, y1, 25.0))                          # bottom rail
            windows = sorted((s.y - s.h / 2, s.y + s.h / 2) for s in slots if y0 <= s.y <= y1)
            edges = [y0] + [v for w in windows for v in w] + [y1]
            for k in range(0, len(edges), 2):
                if edges[k + 1] - edges[k] > 1:
                    boxes.append((x0, edges[k], 25.0, x1, edges[k + 1], el.z - 52.5))
        elif el.name == "central_resource":
            boxes.append((x0, y0, el.z - 25, x1, y1, el.z))                    # table top
            for level in (50.0, 250.0):                                        # ball levels
                boxes.append((x0 + 15, y0 + 15, level - 10, x1 - 15, y1 - 15, level))
            for lx in (x0, x1 - 30):
                for ly in (y0, y1 - 30):
                    boxes.append((lx, ly, 0.0, lx + 30, ly + 30, el.z - 25))
        elif el.name == "x_mark":
            boxes.append((x0, y0, 654.0, x1, y1, el.z))
        elif el.kind == "movable":                                             # fortress
            boxes.append((x0 + 15, y0 + 15, 161.0, x1 - 15, y1 - 15, 171.0))     # cube level
            boxes.append((x0 + 15, y0 + 15, 403.0, x1 - 15, y1 - 15, 407.0))     # ball level (mesh)
            t = 8.0
            boxes += [(x0, y0, 407.0, x1, y0 + t, 495.0), (x0, y1 - t, 407.0, x1, y1, 495.0),
                      (x0, y0, 407.0, x0 + t, y1, 495.0), (x1 - t, y0, 407.0, x1, y1, 495.0)]
            for px in (x0, x1 - 30):
                for py in (y0, y1 - 30):
                    boxes.append((px, py, 0.0, px + 30, py + 30, el.z))
        elif el.kind == "prop":
            base = next((o.z for o in elements if o.name.startswith("strategy_") and o.kind == "obstacle"
                         and o.contains(el.x, el.y)), 0.0)
            boxes.append((x0, y0, base, x1, y1, base + el.z))
        elif el.shape == "circle":
            boxes.append((el.x - el.r, el.y - el.r, 0.0, el.x + el.r, el.y + el.r, el.z))
        else:
            boxes.append((x0, y0, 0.0, x1, y1, el.z))
    return boxes


def fortress_regions(elements: List[fl.Element]) -> Dict[str, Box]:
    """Upper (ball) level of each mobile fortress, where thrown balls score (p.21)."""
    return {el.alliance: _rect_box(el, 407.0 - 5, 646.0, inset=8.0) for el in elements if el.kind == "movable"}


# --- ball path inside the robot ---------------------------------------------------------
def cad_to_robot(p: Sequence[float]) -> Tuple[float, float, float]:
    """CAD frame (+y forward, +x right) -> simulator robot frame (x forward, y left)."""
    return (p[1], -p[0], p[2])


@dataclass
class BallPath:
    slots: List[Tuple[float, float, float]]        # robot frame, fill / feed order
    tower_slots: int                               # how many of the last slots are in the tower
    low_entry: List[Tuple[float, float, float]]    # floor capture: head throat -> tower bottom
    high_entry: List[Tuple[float, float, float]]   # shelf capture: head -> high chute -> tower
    tower: List[Tuple[float, float, float]]        # tower top, elbow, chute exit, basket entry
    shooter: Tuple[float, float, float]
    exit: Tuple[float, float, float]
    high_entry_min_z: float = 150.0
    intake_speed: float = 600.0                    # mm/s at 100 %, estimates
    tower_speed: float = 500.0
    feeder_speed: float = 400.0
    shift_speed: float = 300.0
    launch_speed: float = 8000.0                   # mm/s at 100 % shooter power, estimate
    hood_deg: float = 40.0                         # launch elevation, estimate
    ports: Dict[str, str] = field(default_factory=lambda: {"intake": "DC1", "tower": "DC4",
                                                           "feeder": "DC5", "shooter": "BL1"})

    @property
    def capacity(self) -> int:
        return len(self.slots)

    def is_tower(self, slot: int) -> bool:
        return slot >= len(self.slots) - self.tower_slots


def load_ball_path(data: Optional[dict]) -> Optional[BallPath]:
    if not data:
        return None
    pts = lambda key: [cad_to_robot(p) for p in data[key]]  # noqa: E731
    basket, tower = pts("basket_slots_cad_mm"), pts("tower_slots_cad_mm")
    return BallPath(basket + tower, len(tower), pts("low_entry_cad_mm"), pts("high_entry_cad_mm"),
                    pts("tower_cad_mm"), cad_to_robot(data["shooter_cad_mm"]), cad_to_robot(data["exit_cad_mm"]),
                    float(data.get("high_entry_min_z_mm", 150.0)),
                    **{k: float(data[k]) for k in ("intake_speed", "tower_speed", "feeder_speed", "shift_speed",
                                                    "launch_speed", "hood_deg") if k in data},
                    **({"ports": dict(data["ports"])} if data.get("ports") else {}))


@dataclass
class Carry:
    """A ball inside the robot: robot-frame position and the waypoints still ahead,
    each tagged with the stretch (motor) that moves it there."""
    ball: Ball
    pos: Tuple[float, float, float]
    route: List[Tuple[Tuple[float, float, float], str]]
    slot: Optional[int] = None
    to_shooter: bool = False


# --- world ------------------------------------------------------------------------------
class BallWorld:
    def __init__(self, elements: List[fl.Element], balls: List[Ball], intake: Optional[Intake],
                 path: Optional[BallPath], body_box: Box, head_box: Box):
        self.balls = balls
        self.intake, self.path = intake, path
        self.body_box, self.head_box = body_box, head_box    # robot frame (x fwd, y left, z), head at lift 0
        self.colliders = field_colliders(elements)
        self.fortress = fortress_regions(elements)
        self.grid: Dict[Tuple[int, int], List[int]] = {}
        for i, b in enumerate(self.colliders):
            for key in self._cells(b[0], b[1], b[3], b[4]):
                self.grid.setdefault(key, []).append(i)
        self.carried: List[Carry] = []
        self.captured = 0
        self.shots = 0
        self.in_fortress: Dict[str, List[str]] = {k: [] for k in self.fortress}
        for b in balls:
            b.vx = b.vy = b.vz = 0.0
            b.asleep, b.state, b.rest = True, "field", 0.0

    @staticmethod
    def _cells(x0, y0, x1, y1):
        for i in range(int(math.floor(x0 / CELL)), int(math.floor(x1 / CELL)) + 1):
            for j in range(int(math.floor(y0 / CELL)), int(math.floor(y1 / CELL)) + 1):
                yield (i, j)

    @property
    def stored(self) -> int:
        return len(self.carried)

    # -- main step ---------------------------------------------------------------------
    def step(self, dt: float, pose, velocity: Tuple[float, float, float], lift: float, dc) -> None:
        self._capture(pose, lift, dc)
        self._move_carried(dt, pose, velocity, dc)
        awake = [b for b in self.balls if b.state == "field" and not b.asleep]
        for b in awake:
            self._integrate(b, dt)
        for b in self.balls:
            if b.state == "field":
                self._robot_contact(b, pose, velocity, lift)
        self._ball_contacts()
        for b in self.balls:
            if b.state == "field" and not b.asleep:
                self._score(b)

    # -- capture and transport -----------------------------------------------------------
    def _capture(self, pose, lift, dc) -> None:
        intake, path = self.intake, self.path
        if not intake or not intake.running(dc.power(intake.port)):
            return
        capacity = path.capacity if path else intake.capacity
        for b in self.balls:
            if len(self.carried) >= capacity:
                return
            if b.state == "field" and intake.reaches(b, lift) and intake.contains(pose, b):
                b.state, b.asleep, b.collected = "carried", True, True
                intake.collected.append(b.name)
                self.captured += 1
                local = self._to_robot(pose, b)
                slot = len(self.carried)
                route = self._route_in(local, lift, slot) if path else []
                self.carried.append(Carry(b, local, route, slot))
                if not path:            # no path model: the ball just disappears into the robot
                    b.state = "stored"

    def _route_in(self, local, lift, slot):
        p = self.path
        entry = p.high_entry if local[2] >= p.high_entry_min_z else p.low_entry
        route = [(pt, "intake") for pt in entry]
        if p.is_tower(slot):
            route.append((p.tower[0], "tower"))          # wait at the tower top row
            route.append((p.slots[slot], "tower"))
        else:
            route += [(pt, "tower") for pt in p.tower]
            route.append((p.slots[slot], "shift"))
        return route

    def _move_carried(self, dt, pose, velocity, dc) -> None:
        p = self.path
        if not p:
            return
        power = {k: abs(dc.power(port)) for k, port in p.ports.items()}
        speed = {"intake": p.intake_speed * power["intake"] / 100.0 if power["intake"] >= TRANSIT_MIN_POWER else 0.0,
                 "tower": p.tower_speed * power["tower"] / 100.0 if power["tower"] >= TRANSIT_MIN_POWER else 0.0,
                 "feeder": p.feeder_speed * power["feeder"] / 100.0 if power["feeder"] >= TRANSIT_MIN_POWER else 0.0,
                 "shift": p.shift_speed}
        # feed: the first basket ball goes to the shooter when feeder and shooter run
        if (self.carried and not self.carried[0].route and not self.carried[0].to_shooter
                and speed["feeder"] > 0 and power["shooter"] >= TRANSIT_MIN_POWER):
            first = self.carried[0]
            first.to_shooter = True
            first.route = [(p.shooter, "feeder")]
        launched = None
        for c in self.carried:
            budget = dt
            while c.route and budget > 0:
                target, stretch = c.route[0]
                v = speed[stretch]
                if v <= 0:
                    break
                d = math.dist(c.pos, target)
                step = v * budget
                if step >= d:
                    c.pos, budget = target, budget - d / v
                    c.route.pop(0)
                else:
                    f = step / d
                    c.pos = tuple(a + (t - a) * f for a, t in zip(c.pos, target))
                    budget = 0
            if c.to_shooter and not c.route:
                launched = c
            self._place(c.ball, pose, c.pos)
        if launched and power["shooter"] >= TRANSIT_MIN_POWER:
            self._launch(launched, pose, velocity, power["shooter"])

    def _launch(self, c: Carry, pose, velocity, shooter_power) -> None:
        p = self.path
        self.carried.remove(c)
        b = c.ball
        self._place(b, pose, p.exit)
        speed = p.launch_speed * shooter_power / 100.0
        h = math.radians(p.hood_deg)
        # launcher on the robot's left (CAD -x): robot-frame direction (0, cos h, sin h)
        lx, ly, lz = 0.0, speed * math.cos(h), speed * math.sin(h)
        cth, sth = math.cos(pose.theta), math.sin(pose.theta)
        vx_r, vy_r, omega = velocity
        px, py = p.exit[0], p.exit[1]
        vpx, vpy = vx_r - omega * py, vy_r + omega * px          # robot point velocity, robot frame
        fx, fy = lx + vpx, ly + vpy
        b.vx, b.vy, b.vz = fx * cth - fy * sth, fx * sth + fy * cth, lz
        b.state, b.asleep, b.rest = "field", False, 0.0
        self.shots += 1
        # the rest of the queue moves up one slot
        for k, other in enumerate(self.carried):
            old, other.slot = other.slot, k
            if old is not None and old != k:
                if p.is_tower(old) and not p.is_tower(k):
                    other.route += [(pt, "tower") for pt in p.tower[1:]] + [(p.slots[k], "shift")]
                else:
                    other.route.append((p.slots[k], "tower" if p.is_tower(k) else "shift"))

    @staticmethod
    def _to_robot(pose, b) -> Tuple[float, float, float]:
        dx, dy = b.x - pose.x, b.y - pose.y
        c, s = math.cos(pose.theta), math.sin(pose.theta)
        return (dx * c + dy * s, -dx * s + dy * c, b.z)

    @staticmethod
    def _place(b, pose, local) -> None:
        b.x, b.y = pose.to_field(local[0], local[1])
        b.z = local[2]

    # -- free-ball dynamics ----------------------------------------------------------------
    def _integrate(self, b, dt) -> None:
        b.vz -= G * dt
        b.x += b.vx * dt
        b.y += b.vy * dt
        b.z += b.vz * dt
        supported = False
        if b.z < R:                                        # floor
            b.z = R
            if b.vz < 0:
                b.vz = -b.vz * E_FLOOR if -b.vz > 150 else 0.0
            supported = True
        for i in self._near(b):
            supported |= self._box_contact(b, self.colliders[i], E_WALL)
        for axis, hi in (("x", fl.FIELD_W), ("y", fl.FIELD_H)):  # frame
            v = getattr(b, axis)
            if v < R:
                setattr(b, axis, R)
                setattr(b, "v" + axis, abs(getattr(b, "v" + axis)) * E_WALL)
            elif v > hi - R:
                setattr(b, axis, hi - R)
                setattr(b, "v" + axis, -abs(getattr(b, "v" + axis)) * E_WALL)
        if supported:
            h = math.hypot(b.vx, b.vy)
            if h > 0:
                k = max(0.0, h - ROLL_DECEL * dt) / h
                b.vx *= k
                b.vy *= k
            speed = math.sqrt(b.vx * b.vx + b.vy * b.vy + b.vz * b.vz)
            b.rest = b.rest + dt if speed < SLEEP_SPEED else 0.0
            if b.rest > SLEEP_TIME:
                b.vx = b.vy = b.vz = 0.0
                b.asleep = True
        else:
            b.rest = 0.0

    def _near(self, b):
        seen = set()
        for key in self._cells(b.x - R, b.y - R, b.x + R, b.y + R):
            for i in self.grid.get(key, ()):
                if i not in seen:
                    seen.add(i)
                    yield i

    @staticmethod
    def _box_contact(b, box, e) -> bool:
        """Sphere vs box; pushes the ball out and reflects its velocity. True if the box
        supports the ball from below."""
        x0, y0, z0, x1, y1, z1 = box
        qx, qy, qz = min(max(b.x, x0), x1), min(max(b.y, y0), y1), min(max(b.z, z0), z1)
        dx, dy, dz = b.x - qx, b.y - qy, b.z - qz
        d2 = dx * dx + dy * dy + dz * dz
        if d2 >= R * R:
            return False
        if d2 > 1e-9:
            d = math.sqrt(d2)
            nx, ny, nz = dx / d, dy / d, dz / d
            push = R - d
        else:                                              # centre inside: leave by the nearest face
            faces = [(b.x - x0, (-1, 0, 0)), (x1 - b.x, (1, 0, 0)), (b.y - y0, (0, -1, 0)),
                     (y1 - b.y, (0, 1, 0)), (b.z - z0, (0, 0, -1)), (z1 - b.z, (0, 0, 1))]
            depth, (nx, ny, nz) = min(faces)
            push = depth + R
        b.x += nx * push
        b.y += ny * push
        b.z += nz * push
        vn = b.vx * nx + b.vy * ny + b.vz * nz
        if vn < 0:                                         # impact: bounce, lose some tangential speed
            b.vx -= (1 + e) * vn * nx
            b.vy -= (1 + e) * vn * ny
            b.vz -= (1 + e) * vn * nz
            vn = b.vx * nx + b.vy * ny + b.vz * nz
            b.vx = vn * nx + (b.vx - vn * nx) * (1 - FRICTION_T)
            b.vy = vn * ny + (b.vy - vn * ny) * (1 - FRICTION_T)
            b.vz = vn * nz + (b.vz - vn * nz) * (1 - FRICTION_T)
        if nz > 0.7 and b.vz < 150:
            if b.vz < 0:
                b.vz = 0.0
            return True
        return False

    def _robot_contact(self, b, pose, velocity, lift) -> None:
        dx, dy = b.x - pose.x, b.y - pose.y
        if dx * dx + dy * dy > 700.0 ** 2:
            return
        c, s = math.cos(pose.theta), math.sin(pose.theta)
        lx, ly = dx * c + dy * s, -dx * s + dy * c
        hx0, hy0, hz0, hx1, hy1, hz1 = self.head_box
        for box in (self.body_box, (hx0, hy0, hz0 + lift, hx1, hy1, hz1 + lift)):
            x0, y0, z0, x1, y1, z1 = box
            qx, qy, qz = min(max(lx, x0), x1), min(max(ly, y0), y1), min(max(b.z, z0), z1)
            ex, ey, ez = lx - qx, ly - qy, b.z - qz
            d2 = ex * ex + ey * ey + ez * ez
            if d2 >= R * R:
                continue
            if d2 > 1e-9:
                d = math.sqrt(d2)
                nx, ny, nz, push = ex / d, ey / d, ez / d, R - d
            else:
                faces = [(lx - x0, (-1, 0, 0)), (x1 - lx, (1, 0, 0)), (ly - y0, (0, -1, 0)),
                         (y1 - ly, (0, 1, 0)), (z1 - b.z, (0, 0, 1))]
                depth, (nx, ny, nz) = min(faces)
                push = depth + R
            lx, ly = lx + nx * push, ly + ny * push
            b.z += nz * push
            b.x, b.y = pose.to_field(lx, ly)
            vx_r, vy_r, omega = velocity
            # robot surface velocity at the contact, robot frame -> field
            px, py = vx_r - omega * ly, vy_r + omega * lx
            wx, wy = px * c - py * s, px * s + py * c
            fnx, fny = nx * c - ny * s, nx * s + ny * c
            rel_n = (b.vx - wx) * fnx + (b.vy - wy) * fny + b.vz * nz
            if rel_n < 0:
                b.vx -= (1 + E_ROBOT) * rel_n * fnx
                b.vy -= (1 + E_ROBOT) * rel_n * fny
                b.vz -= (1 + E_ROBOT) * rel_n * nz
            b.asleep, b.rest = False, 0.0

    def _ball_contacts(self) -> None:
        free = [b for b in self.balls if b.state == "field"]
        cells: Dict[Tuple[int, int], List[Ball]] = {}
        for b in free:
            cells.setdefault((int(b.x // 100), int(b.y // 100)), []).append(b)
        for b in free:
            if b.asleep:
                continue
            ci, cj = int(b.x // 100), int(b.y // 100)
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    for o in cells.get((ci + di, cj + dj), ()):
                        if o is b or (not o.asleep and id(o) < id(b)):
                            continue
                        dx, dy, dz = o.x - b.x, o.y - b.y, o.z - b.z
                        d2 = dx * dx + dy * dy + dz * dz
                        if d2 >= BALL_D * BALL_D or d2 < 1e-9:
                            continue
                        d = math.sqrt(d2)
                        nx, ny, nz = dx / d, dy / d, dz / d
                        overlap = BALL_D - d
                        share = 0.5 if not o.asleep else 1.0
                        b.x -= nx * overlap * share
                        b.y -= ny * overlap * share
                        b.z -= nz * overlap * share
                        if not o.asleep:
                            o.x += nx * overlap * 0.5
                            o.y += ny * overlap * 0.5
                            o.z += nz * overlap * 0.5
                        rel = (o.vx - b.vx) * nx + (o.vy - b.vy) * ny + (o.vz - b.vz) * nz
                        if rel < 0:
                            j = -(1 + E_BALL) * rel / 2
                            b.vx -= j * nx
                            b.vy -= j * ny
                            b.vz -= j * nz
                            o.vx += j * nx
                            o.vy += j * ny
                            o.vz += j * nz
                            if math.sqrt(o.vx ** 2 + o.vy ** 2 + o.vz ** 2) > SLEEP_SPEED:
                                o.asleep, o.rest = False, 0.0

    def _score(self, b) -> None:
        for alliance, (x0, y0, z0, x1, y1, z1) in self.fortress.items():
            if x0 <= b.x <= x1 and y0 <= b.y <= y1 and z0 <= b.z <= z1 and b.name not in self.in_fortress[alliance]:
                self.in_fortress[alliance].append(b.name)
