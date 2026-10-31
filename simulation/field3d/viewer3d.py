"""3D viewer for the Storm Breaker field and the v22 robot (Panda3D).

Runs the same simulation as the 2D viewer (simulation/field2d: mecanum kinematics,
sensors, mBlock programs, emulated gamepad) and draws it in 3D with the CAD model
from mechanical/assemblies/full_robot/v22. The robot state is also streamed over
UDP (state_stream.py) so other tools, such as Unreal Engine or a ROS 2 bridge,
can follow the same run.

    python viewer3d.py
    python viewer3d.py --program ../control/test_chassis_control_automatico.py
    python viewer3d.py --screenshot shot.png --run-for 5 --program ...   # headless

Keys: O open program, Space run/stop, R reset, J gamepad window, 1-4 cameras
(orbit, follow, top, driver), mouse drag rotate, right drag pan, wheel zoom,
E/Q carriage up/down, T/G intake head up/down, M flag mast, V vectors, X x-ray, L labels,
S screenshot, H help, Esc quit. The carriage, intake head and rollers also
follow the program's power_expand_board ports (robot_config.json "mechanisms").
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELD2D = HERE.parent / "field2d"
for p in (str(HERE), str(FIELD2D)):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import field_layout as fl  # noqa: E402
from balls import SCENARIOS as BALL_SCENARIOS, Ball, load_intake  # noqa: E402
from kinematics import load_drive_train  # noqa: E402
from mechanisms import load_mechanisms  # noqa: E402
from mblock_runtime import GamepadInput  # noqa: E402
from robot import DEFAULT_CONFIG, load_config, mecanum_wheels, start_pose  # noqa: E402
from simulation import AUTO_STAGE_S, Simulation, load_gyro_sign  # noqa: E402
from state_stream import DEFAULT_RATE_HZ, DEFAULT_TARGET, StatePublisher, parse_target, state_message  # noqa: E402

CAMERAS = ("orbit", "follow", "top", "driver")
CARRIAGE_SPEED_MM_S = 200.0
INTAKE_LIFT_KEY_MM_S = 120.0
SPIN_DISPLAY_CAP_DPS = 900.0   # faster rollers (e.g. the brushless shooter) would strobe on screen
VEL_ARROW_S = 0.4              # m of arrow per m/s
FORCE_ARROW_S = 0.03           # m of arrow per N
TORQUE_ARROW_S = 0.3           # m of arrow per N m
ACCEL_TAU_S = 0.08             # low-pass on the differentiated velocity (display)
MM = 1 / 1000.0
HELP = ("O open program   Space run/stop   R reset   J gamepad   1-4 cameras (orbit, follow, top, driver)\n"
        "drag rotate   right-drag pan   wheel zoom   E/Q carriage   T/G intake head   M flag mast   V vectors   "
        "X x-ray   L labels   S screenshot   H help")


def wheel_state(sim):
    """Per wheel (rpm, angle deg), positive = rolling forward, from the motor ports."""
    drive = sim.drive
    commanded = sim.motors.snapshot()
    out = {}
    for port, m in drive.motors.items():
        rpm = m.direction * commanded.get(port, 0.0) * drive.gear_ratio
        angle = m.direction * sim.motors.angle(port) * drive.gear_ratio
        out[m.wheel] = (rpm, angle)
    return out


def build_simulation(args, gamepad):
    cfg = load_config(args.config)
    elements = fl.build_field()
    sim = Simulation(cfg, start_pose(cfg, elements), load_drive_train(args.config), args.time_limit,
                     load_gyro_sign(args.config), gamepad, ball_scenario=args.balls,
                     intake=load_intake(args.config), mechanisms=load_mechanisms(args.config))
    if "elevator" in sim.mechanisms.linear:
        sim.mechanisms.linear["elevator"].start_mm = args.carriage
        sim.mechanisms.reset()
    if args.program:
        sim.program = args.program.resolve()
    return sim, elements


class Viewer3D:
    def __init__(self, args):
        from panda3d.core import load_prc_file_data
        width, height = (int(v) for v in args.size.lower().split("x"))
        load_prc_file_data("", f"win-size {width} {height}\nwindow-title Storm Breaker 3D\n"
                               "framebuffer-multisample 1\nmultisamples 4\nsync-video 1\n"
                               + ("window-type offscreen\naudio-library-name null\n" if args.screenshot else ""))
        from direct.showbase.ShowBase import ShowBase
        self.base = ShowBase()
        self.args = args
        self.gamepad = GamepadInput()
        self.sim, self.elements = build_simulation(args, self.gamepad)
        self.message, self.message_error = "", False
        self.publisher = None
        if not args.no_stream:
            self.publisher = StatePublisher(parse_target(args.stream) if args.stream else DEFAULT_TARGET,
                                            args.stream_rate)
        self._setup_scene()
        self._setup_camera()
        self._setup_hud()
        if not args.screenshot:
            self._setup_controls()
            self.base.task_mgr.add(self._update, "update")
            self.say(f"Loaded {self.sim.program.name}, press Space" if self.sim.program else
                     "Press O to open an mBlock program")

    # --- scene -------------------------------------------------------------------
    def _setup_scene(self):
        from panda3d.core import AmbientLight, DirectionalLight, LineSegs, TextNode
        from field_model import build_field_node
        from robot_model import RobotModel, load_model_spec
        base = self.base
        base.set_background_color(0.86, 0.88, 0.91, 1)
        base.disable_mouse()
        render = base.render
        self.field = build_field_node(self.elements)
        self.field.reparent_to(render)
        self.ball_root = render.attach_new_node("balls")
        self.ball_nodes = []
        self._sync_balls()
        self.robot = RobotModel(load_model_spec(self.args.model))
        self.robot.root.reparent_to(render)
        self.robot.show_mast(self.args.mast)
        self.xray = False
        if self.args.xray:
            self._toggle_xray()
        ambient = AmbientLight("ambient")
        ambient.set_color((0.45, 0.45, 0.48, 1))
        sun = DirectionalLight("sun")
        sun.set_color((0.75, 0.74, 0.70, 1))
        sun_np = render.attach_new_node(sun)
        sun_np.set_hpr(35, -55, 0)
        render.set_light(render.attach_new_node(ambient))
        render.set_light(sun_np)
        render.set_shader_auto()
        self.trail_np = render.attach_new_node("trail")
        self._trail_len = -1
        self._line_segs = LineSegs
        self.labels = render.attach_new_node("labels")
        for el in self.elements:
            if not el.label or el.kind == "slot":
                continue
            text = TextNode(el.name)
            text.set_text(el.label)
            text.set_align(TextNode.A_center)
            text.set_text_color(1, 1, 1, 1)
            text.set_shadow(0.04, 0.04)
            text.set_shadow_color(0, 0, 0, 0.8)
            np_ = self.labels.attach_new_node(text)
            np_.set_pos(el.x * MM, el.y * MM, max(el.z, 0) * MM + 0.08)
            np_.set_scale(0.08)
            np_.set_billboard_point_eye()
            np_.set_light_off()
        self.labels.hide()
        self._setup_vectors()
        self._place_robot()

    def _sync_balls(self):
        """One node per simulated ball; collected balls are hidden. Rebuilt when the
        simulation resets (new Ball objects)."""
        from field_model import ball_part
        from robot_model import _geom_node
        balls = self.sim.balls
        if [id(n.get_python_tag("ball")) for n in self.ball_nodes] != [id(b) for b in balls]:
            self.ball_root.get_children().detach()
            self.ball_nodes = []
            for b in balls:
                part = ball_part(Ball(b.name, 0.0, 0.0, 0.0))     # geometry at the origin, moved each frame
                node = self.ball_root.attach_new_node(_geom_node(part))
                node.set_color(*part.rgba)
                node.set_python_tag("ball", b)
                self.ball_nodes.append(node)
        for node in self.ball_nodes:
            b = node.get_python_tag("ball")
            node.set_pos(b.x * MM, b.y * MM, b.z * MM)

    # --- vectors: wheel speeds and inertia at the centre of mass -------------------------
    def _setup_vectors(self):
        self.vectors = self.base.render.attach_new_node("vectors")
        self.vectors.set_light_off()
        self.vectors.set_depth_test(False)
        self.vectors.set_bin("fixed", 50)
        self.show_vectors = not self.args.no_vectors
        mass_file = HERE / "robot_mass.json"
        self.mass = json.loads(mass_file.read_text()) if mass_file.exists() else None
        self._wheels = mecanum_wheels(self.sim.cfg)
        self._com_v = None
        self._accel = (0.0, 0.0)
        self._alpha = 0.0
        self._omega_prev = 0.0
        self.inertia_text = ""

    def _com_robot(self):
        """Centre of mass in the simulator robot frame (x fwd, y left, z), mm, with the
        carriage height (CAR_/GR_ mass moves with it)."""
        m = self.mass
        cx, cy, cz = (c * 1000 for c in m["center_of_mass_m"])
        moving = sum(v for k, v in m["mass_by_prefix_kg"].items() if k in ("CAR", "GR"))
        cz += moving * self.robot.carriage_mm / m["mass_kg"]
        return cy, -cx, cz

    @staticmethod
    def _arrow(segs, p, v, scale, color):
        """3D arrow from p (m) along v (any unit) * scale."""
        x, y, z = (p[i] + v[i] * scale for i in range(3))
        length = math.sqrt(sum((v[i] * scale) ** 2 for i in range(3)))
        if length < 0.01:
            return
        segs.set_color(*color)
        segs.move_to(*p)
        segs.draw_to(x, y, z)
        ux, uy, uz = ((v[i] * scale) / length for i in range(3))
        head = min(0.05, length * 0.35)
        px, py = (-uy, ux) if abs(uz) < 0.9 else (1.0, 0.0)   # perpendicular in the floor plane
        for side in (-1, 1):
            segs.move_to(x, y, z)
            segs.draw_to(x - ux * head + side * px * head * 0.5, y - uy * head + side * py * head * 0.5,
                         z - uz * head + (side * head * 0.5 if abs(uz) >= 0.9 else 0))

    def _update_vectors(self, dt):
        from panda3d.core import LineSegs
        self.vectors.get_children().detach()
        sim, pose = self.sim, self.sim.pose
        vx, vy, omega = sim._velocity                    # robot frame, mm/s, rad/s (CCW)
        c, s = math.cos(pose.theta), math.sin(pose.theta)
        to_field = lambda ax, ay: (ax * c - ay * s, ax * s + ay * c)  # noqa: E731
        segs = LineSegs("vectors")
        segs.set_thickness(3)
        # wheels: rim (drive) speed along the wheel and the hub's real velocity
        rpms = {w: rpm for w, (rpm, _) in wheel_state(sim).items()}
        circ = math.pi * sim.cfg.wheel_diameter_mm
        for wheel in self._wheels:
            wx, wy = wheel.center
            fx, fy = pose.to_field(wx, wy)
            p = (fx * MM, fy * MM, 0.09)
            rim = rpms.get(wheel.name, 0.0) / 60.0 * circ * MM
            self._arrow(segs, p, (*to_field(rim, 0.0), 0.0), VEL_ARROW_S, (1.0, 0.55, 0.1, 1))
            hx, hy = (vx - omega * wy) * MM, (vy + omega * wx) * MM
            self._arrow(segs, (p[0], p[1], 0.11), (*to_field(hx, hy), 0.0), VEL_ARROW_S, (0.2, 0.9, 1.0, 1))
        if self.mass:
            m = self.mass["mass_kg"]
            izz = self.mass["inertia_kg_m2"][2][2]
            rx, ry, rz = self._com_robot()
            fx, fy = pose.to_field(rx, ry)
            com = (fx * MM, fy * MM, rz * MM)
            v_com = to_field((vx - omega * ry) * MM, (vy + omega * rx) * MM)   # m/s, field
            if self._com_v is not None and dt > 0:
                k = dt / (ACCEL_TAU_S + dt)
                ax = (v_com[0] - self._com_v[0]) / dt
                ay = (v_com[1] - self._com_v[1]) / dt
                self._accel = (self._accel[0] + k * (ax - self._accel[0]), self._accel[1] + k * (ay - self._accel[1]))
                alpha = (omega - self._omega_prev) / dt
                self._alpha += k * (alpha - self._alpha)
            self._com_v, self._omega_prev = v_com, omega
            force = (-m * self._accel[0], -m * self._accel[1], 0.0)           # N, inertial (d'Alembert)
            torque = -izz * self._alpha                                     # N m about z
            self._arrow(segs, com, (*v_com, 0.0), VEL_ARROW_S, (1, 1, 1, 1))
            self._arrow(segs, com, force, FORCE_ARROW_S, (1.0, 0.25, 0.25, 1))
            self._arrow(segs, com, (0.0, 0.0, torque), TORQUE_ARROW_S, (0.9, 0.3, 1.0, 1))
            # centre-of-mass marker
            segs.set_color(1, 1, 0.3, 1)
            for d in ((0.04, 0, 0), (0, 0.04, 0), (0, 0, 0.04)):
                segs.move_to(com[0] - d[0], com[1] - d[1], com[2] - d[2])
                segs.draw_to(com[0] + d[0], com[1] + d[1], com[2] + d[2])
            self.inertia_text = ("centre of mass (estimate): m %.2f kg  Izz %.3f kg m2   |v| %.2f m/s   |a| %.2f m/s2   "
                                 "F inertial %.1f N   torque inertial %+.2f N m"
                                 % (m, izz, math.hypot(*v_com), math.hypot(*self._accel),
                                    math.hypot(force[0], force[1]), torque))
        self.vectors.attach_new_node(segs.create())
        self.vectors.show() if self.show_vectors else self.vectors.hide()

    def _place_robot(self, dt=0.0):
        pose = self.sim.pose
        self.robot.set_pose(pose.x, pose.y, pose.theta)
        self.robot.set_wheel_angles({w: a for w, (_, a) in wheel_state(self.sim).items()})
        mech = self.sim.mechanisms
        if "elevator" in mech.linear:
            self.robot.set_carriage(mech.position("elevator"))
        self.robot.set_intake_lift(mech.position("intake_lift"))
        self.robot.set_spinner_angles(self._spin_display(dt))

    def _spin_display(self, dt):
        """Displayed spinner angles: follow the simulation, but never faster than
        SPIN_DISPLAY_CAP_DPS so fast rollers do not strobe."""
        state = getattr(self, "_spin_state", {})
        out = {}
        for name, spinner in self.sim.mechanisms.spinners.items():
            last_true, shown = state.get(name, (spinner.angle, spinner.angle))
            delta = spinner.angle - last_true
            cap = SPIN_DISPLAY_CAP_DPS * dt if dt > 0 else abs(delta)
            shown += max(-cap, min(cap, delta))
            state[name] = (spinner.angle, shown)
            out[name] = shown
        self._spin_state = state
        return out

    def _update_trail(self):
        trail = self.sim.state.trail
        if len(trail) == self._trail_len:
            return
        self._trail_len = len(trail)
        self.trail_np.get_children().detach()
        if len(trail) < 2:
            return
        segs = self._line_segs("trail")
        segs.set_thickness(3)
        segs.set_color(0.15, 0.6, 0.35, 1)
        step = max(1, len(trail) // 2000)
        segs.move_to(trail[0][0] * MM, trail[0][1] * MM, 0.004)
        for x, y in trail[1::step] + [trail[-1]]:
            segs.draw_to(x * MM, y * MM, 0.004)
        node = self.trail_np.attach_new_node(segs.create())
        node.set_light_off()

    # --- camera ------------------------------------------------------------------
    def _setup_camera(self):
        self.cam_mode = self.args.camera
        from panda3d.core import OrthographicLens
        self.yaw, self.pitch, self.dist = -90.0, 50.0, 6.2
        self.target = [fl.CX * MM, fl.CY * MM, 0.0]
        self.perspective = self.base.cam.node().get_lens()
        self.perspective.set_fov(55)
        self.perspective.set_near_far(0.02, 100)
        self.ortho = OrthographicLens()       # top view: no perspective lean on the tall robot
        self.ortho.set_near_far(0.1, 20)
        width = (fl.FIELD_W + 300) * MM
        self.ortho.set_film_size(width, width / max(self.base.get_aspect_ratio(), 0.1))
        self._drag = None
        self._apply_camera()

    def _apply_camera(self):
        cam = self.base.camera
        pose = self.sim.pose
        lens = self.ortho if self.cam_mode == "top" else self.perspective
        if self.base.cam.node().get_lens() is not lens:
            self.base.cam.node().set_lens(lens)
        if self.cam_mode == "top":
            cam.set_pos(fl.CX * MM, fl.CY * MM, 8.0)
            cam.look_at(fl.CX * MM, fl.CY * MM + 0.001, 0)
            return
        if self.cam_mode == "driver":
            cam.set_pos(-0.9, fl.CY * MM, 1.7)
            cam.look_at(fl.CX * MM * 0.7, fl.CY * MM, 0)
            return
        if self.cam_mode == "follow":
            tx, ty, tz = pose.x * MM, pose.y * MM, 0.3
            yaw = math.degrees(pose.theta) + 180.0 + self.yaw + 70.0
            dist = min(self.dist, 2.5)
        else:
            tx, ty, tz = self.target
            yaw, dist = self.yaw, self.dist
        p, y = math.radians(self.pitch), math.radians(yaw)
        cam.set_pos(tx + dist * math.cos(p) * math.cos(y), ty + dist * math.cos(p) * math.sin(y), tz + dist * math.sin(p))
        cam.look_at(tx, ty, tz)

    def _mouse(self):
        watcher = self.base.mouseWatcherNode
        return (watcher.get_mouse_x(), watcher.get_mouse_y()) if watcher.has_mouse() else None

    def _start_drag(self, kind):
        self._drag = (kind, self._mouse())

    def _drag_camera(self):
        if not self._drag or self._drag[1] is None:
            return
        now = self._mouse()
        if now is None:
            return
        kind, last = self._drag
        dx, dy = now[0] - last[0], now[1] - last[1]
        if kind == "rotate":
            self.yaw -= dx * 120
            self.pitch = max(5.0, min(88.0, self.pitch - dy * 80))
        elif self.cam_mode == "orbit":
            y = math.radians(self.yaw)
            right = (-math.sin(y), math.cos(y))
            fwd = (-math.cos(y), -math.sin(y))
            scale = self.dist * 0.6
            self.target[0] -= (dx * right[0] + dy * fwd[0]) * scale
            self.target[1] -= (dx * right[1] + dy * fwd[1]) * scale
        self._drag = (kind, now)

    def _zoom(self, factor):
        self.dist = max(0.6, min(12.0, self.dist * factor))

    def set_camera(self, mode):
        self.cam_mode = mode
        self.say(f"Camera: {mode}")

    # --- HUD and controls ----------------------------------------------------------
    def _setup_hud(self):
        from direct.gui.OnscreenText import OnscreenText
        from panda3d.core import TextNode
        base = self.base
        self.hud = OnscreenText(text="", parent=base.a2dTopLeft, pos=(0.04, -0.07), scale=0.045,
                                align=TextNode.A_left, fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.85), mayChange=True)
        self.status_text = OnscreenText(text="", parent=base.a2dBottomLeft, pos=(0.04, 0.16), scale=0.042,
                                        align=TextNode.A_left, fg=(1, 1, 1, 1), shadow=(0, 0, 0, 0.85), mayChange=True)
        self.help = OnscreenText(text=HELP, parent=base.a2dBottomLeft, pos=(0.04, 0.08), scale=0.034,
                                 align=TextNode.A_left, fg=(0.9, 0.92, 0.95, 1), shadow=(0, 0, 0, 0.85), mayChange=False)
        self._refresh_hud()

    def say(self, text, error=False):
        self.message, self.message_error = text, error

    def _ball_text(self):
        w = self.sim.world
        if not w:
            return f"\nballs collected {self.sim.balls_collected} / {self.sim.intake.capacity}"
        cap = w.path.capacity if w.path else self.sim.intake.capacity
        return (f"\nballs captured {w.captured}   in robot {w.stored} / {cap}   shots {w.shots}   "
                f"in fortress: blue {len(w.in_fortress.get('blue', []))}  red {len(w.in_fortress.get('red', []))}")

    def _refresh_hud(self):
        sim, pose = self.sim, self.sim.pose
        name = sim.program.name if sim.program else "no program"
        limit = f" / {sim.time_limit:g}" if sim.time_limit else ""
        stream = f"   stream {self.publisher.target[0]}:{self.publisher.target[1]}" if self.publisher else ""
        self.hud.setText(f"{name}   t = {sim.time:5.1f}{limit} s   {sim.state.status}\n"
                         f"x {pose.x:6.0f}  y {pose.y:6.0f} mm   heading {math.degrees(pose.theta) % 360:5.1f} deg   "
                         f"carriage {self.robot.carriage_mm:3.0f} mm   intake head {self.robot.intake_lift_mm:3.0f} mm   mast {'on' if self.robot.mast_visible else 'off'}   "
                         f"camera {self.cam_mode}{stream}"
                         + (self._ball_text() if sim.intake and sim.balls else "")
                         + (f"\n{self.inertia_text}" if self.show_vectors and self.inertia_text else ""))
        message = sim.state.message if sim.state.status in ("error", "out_of_bounds", "done", "stopped") else self.message
        error = sim.state.status in ("error", "out_of_bounds") or self.message_error
        self.status_text.setText(message or "")
        self.status_text.setFg((1.0, 0.45, 0.45, 1) if error else (0.55, 1.0, 0.65, 1))

    def _setup_controls(self):
        from viewer import GamepadLauncher, ProgramController   # 2D viewer helpers
        base = self.base
        self.programs = ProgramController(self.sim, self.say)
        self.gamepad_window = GamepadLauncher(self.gamepad, self.say)
        self._keys = {"e": False, "q": False, "t": False, "g": False}
        base.accept("escape", self.quit)
        base.accept("o", self.programs.load)
        base.accept("space", self.programs.toggle)
        base.accept("r", self.programs.stop)
        base.accept("j", self.gamepad_window.open)
        for i, mode in enumerate(CAMERAS, 1):
            base.accept(str(i), self.set_camera, [mode])
        base.accept("mouse1", self._start_drag, ["rotate"])
        base.accept("mouse3", self._start_drag, ["pan"])
        base.accept("mouse1-up", setattr, [self, "_drag", None])
        base.accept("mouse3-up", setattr, [self, "_drag", None])
        base.accept("wheel_up", self._zoom, [0.9])
        base.accept("wheel_down", self._zoom, [1.1])
        for key in ("e", "q", "t", "g"):
            base.accept(key, self._keys.__setitem__, [key, True])
            base.accept(f"{key}-up", self._keys.__setitem__, [key, False])
        base.accept("m", self._toggle_mast)
        base.accept("v", self._toggle_vectors)
        base.accept("x", self._toggle_xray)
        base.accept("l", lambda: self.labels.hide() if not self.labels.is_hidden() else self.labels.show())
        base.accept("h", lambda: self.help.hide() if not self.help.is_hidden() else self.help.show())
        base.accept("s", self.screenshot)
        base.userExit = self.quit

    def _toggle_xray(self):
        """Semi-transparent robot, to watch the balls inside the intake, tower and basket."""
        from panda3d.core import TransparencyAttrib
        self.xray = not self.xray
        root = self.robot.root
        if self.xray:
            root.set_transparency(TransparencyAttrib.M_alpha, 1)
            root.set_alpha_scale(0.28)
            root.set_depth_write(False, 1)
            root.set_bin("transparent", 20, 1)
        else:
            root.clear_transparency()
            root.clear_color_scale()
            root.clear_depth_write()
            root.clear_bin()
        self.say("X-ray " + ("on" if self.xray else "off"))

    def _toggle_vectors(self):
        self.show_vectors = not self.show_vectors
        self.say("Vectors " + ("on: wheel rim (orange) / hub (cyan) speed, centre of mass velocity (white), "
                               "inertial force (red), inertial torque (magenta)" if self.show_vectors else "off"))

    def _toggle_mast(self):
        self.robot.show_mast(not self.robot.mast_visible)
        self.say("Flag mast " + ("installed (Modification Stage)" if self.robot.mast_visible else "removed"))

    def screenshot(self, path=None):
        from panda3d.core import Filename
        path = Path(path) if path else Path.cwd() / "field3d_screenshot.png"
        self.base.graphics_engine.render_frame()
        self.base.win.save_screenshot(Filename.from_os_specific(str(path)))
        self.say(f"Saved {path.name}")
        return path

    # --- loop ----------------------------------------------------------------------
    def _publish(self, now):
        if not self.publisher:
            return
        msg = state_message(self.robot.spec["name"], self.sim.time, self.sim.state.status, self.sim.pose,
                            self.sim._velocity, wheel_state(self.sim), self.robot.carriage_mm,
                            self.robot.mast_visible, self.sim.balls_collected, self.robot.intake_lift_mm)
        self.publisher.maybe_send(now, msg)

    def _update(self, task):
        from direct.task.Task import Task
        from panda3d.core import ClockObject
        clock = ClockObject.get_global_clock()
        dt = clock.get_dt()
        self.sim.step(dt)
        mech = self.sim.mechanisms
        if self._keys["e"] != self._keys["q"]:
            sign = 1 if self._keys["e"] else -1
            if "elevator" in mech.linear:
                mech.linear["elevator"].nudge(sign * CARRIAGE_SPEED_MM_S * dt)
            else:
                self.robot.set_carriage(self.robot.carriage_mm + sign * CARRIAGE_SPEED_MM_S * dt)
        if self._keys["t"] != self._keys["g"] and "intake_lift" in mech.linear:
            mech.linear["intake_lift"].nudge((1 if self._keys["t"] else -1) * INTAKE_LIFT_KEY_MM_S * dt)
        self._place_robot(dt)
        self._sync_balls()
        self._update_vectors(dt)
        self._update_trail()
        self._drag_camera()
        self._apply_camera()
        self._refresh_hud()
        self._publish(clock.get_frame_time())
        return Task.cont

    def run_headless(self, seconds, frame_s=1 / 60):
        """Advance the simulation without real time (screenshots and tests)."""
        if self.sim.program and seconds > 0:
            self.sim.run()
            t = 0.0
            while t < seconds and self.sim.running:
                self.sim.step(frame_s)
                t += frame_s
                if seconds - t < 0.3:          # settle the displayed acceleration
                    self._update_vectors(frame_s)
        self._place_robot()
        self._sync_balls()
        self._update_vectors(frame_s)
        self._update_trail()
        self._apply_camera()
        self._refresh_hud()

    def quit(self):
        self.sim.stop()
        if getattr(self, "gamepad_window", None):
            self.gamepad_window.close()
        if self.publisher:
            self.publisher.close()
        self.base.destroy()
        sys.exit(0)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="robot config JSON (2D simulator)")
    parser.add_argument("--model", type=Path, default=HERE / "robot_model.json", help="3D model description")
    parser.add_argument("--program", type=Path, help="mBlock Python program to preload")
    parser.add_argument("--time-limit", type=float, default=AUTO_STAGE_S,
                        help="stop the run after this many simulated seconds (0 = no limit)")
    parser.add_argument("--size", default="1440x900", help="window size WxH in px")
    parser.add_argument("--camera", choices=CAMERAS, default="orbit")
    parser.add_argument("--carriage", type=float, default=0.0, help="initial carriage height in mm (0..358)")
    parser.add_argument("--mast", action="store_true", help="start with the flag mast installed")
    parser.add_argument("--balls", choices=BALL_SCENARIOS, default="initial",
                        help="balls on the field: initial (rules), released (own resource balls on the floor, "
                             "manual stage) or none")
    parser.add_argument("--no-vectors", action="store_true", help="start with the wheel / inertia vectors hidden")
    parser.add_argument("--xray", action="store_true", help="start with the robot semi-transparent")
    parser.add_argument("--stream", help="UDP target HOST:PORT for the state stream (default 127.0.0.1:5005)")
    parser.add_argument("--stream-rate", type=float, default=DEFAULT_RATE_HZ, help="state messages per second")
    parser.add_argument("--no-stream", action="store_true", help="do not send the state stream")
    parser.add_argument("--screenshot", type=Path, help="render once (offscreen) to this PNG and exit")
    parser.add_argument("--run-for", type=float, default=0, help="with --screenshot: simulate this many seconds first")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    viewer = Viewer3D(args)
    if args.screenshot:
        viewer.run_headless(args.run_for)
        print("saved", viewer.screenshot(args.screenshot.resolve()))
        viewer.sim.stop()
        return 0
    viewer.base.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
