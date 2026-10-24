"""Pygame viewer for the 2D field layout, with a side panel for the robot.

Usage:
    python viewer.py                          # interactive window
    python viewer.py --length 480 --width 420 --heading 90  # override robot size/heading
    python viewer.py --screenshot field.png   # render once and exit (headless OK)

    python viewer.py --program programs/all_motors_forward.py  # preload an mBlock program

Side panel: pick start, orientation and length/width, then Apply (or Enter).
Reset reloads robot_config.json, Save writes the applied values to it.
mBlock program: Load .py, Run (real time, stops at the time limit or when the robot
leaves the field: "Out of boundaries"), Stop. Space also runs/stops.
Keys (outside the text boxes): G grid, L labels, S screenshot, Esc quit,
Up/Down length +/-10 mm, Right/Left width +/-10 mm (Shift: 1 mm).
Hover shows the cursor position in field mm and the elements under it.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
from dataclasses import replace
from pathlib import Path

import field_layout as fl
from panel import PANEL_W, RobotPanel
from kinematics import load_drive_train
from robot import DEFAULT_CONFIG, load_config, mecanum_wheels, start_pose
from simulation import AUTO_STAGE_S, Simulation, load_gyro_sign

from theme import PALETTE as COLORS, RADIUS, Fonts

MARGIN_PX = 30
HUD_PX = 34
SUPERSAMPLE = 3  # the field is drawn at 3x and smooth-scaled down for soft edges


class View:
    """Field mm <-> screen px. `ss` scales the whole view for supersampled drawing."""

    def __init__(self, width_px: int, height_px: int, ss: int = 1):
        margin, hud = MARGIN_PX * ss, HUD_PX * ss
        usable_w = width_px - 2 * margin
        usable_h = height_px - 2 * margin - hud
        self.scale = min(usable_w / fl.FIELD_W, usable_h / fl.FIELD_H)  # px per mm
        self.ox = (width_px - fl.FIELD_W * self.scale) / 2
        self.oy = margin + fl.FIELD_H * self.scale  # screen y of field y = 0

    def to_screen(self, x, y):
        return int(round(self.ox + x * self.scale)), int(round(self.oy - y * self.scale))

    def to_field(self, sx, sy):
        return (sx - self.ox) / self.scale, (self.oy - sy) / self.scale

    def rect(self, x0, y0, x1, y1):
        import pygame
        ax, ay = self.to_screen(x0, y1)
        bx, by = self.to_screen(x1, y0)
        return pygame.Rect(ax, ay, max(1, bx - ax), max(1, by - ay))


def _blend_rect(surface, color, rect, radius=0):
    """Rounded rect with alpha (pygame.draw ignores alpha on opaque surfaces)."""
    import pygame
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, color, layer.get_rect(), border_radius=radius)
    surface.blit(layer, rect.topleft)


def _blend_polygon(surface, color, points):
    import pygame
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    x0, y0 = min(xs), min(ys)
    layer = pygame.Surface((max(xs) - x0 + 1, max(ys) - y0 + 1), pygame.SRCALPHA)
    pygame.draw.polygon(layer, color, [(x - x0, y - y0) for x, y in points])
    surface.blit(layer, (x0, y0))


def draw_robot(screen, view, cfg, pose, ss=1, alert=False):
    """Chassis box, a mecanum wheel in each corner, and a heading arrow."""
    import pygame

    accent = COLORS["robot_alert"] if alert else COLORS["robot"]
    body = [view.to_screen(*c) for c in pose.corners(cfg)]
    _blend_polygon(screen, COLORS["robot_alert_body"] if alert else COLORS["robot_body"], body)
    for wheel in mecanum_wheels(cfg):
        wx, wy = wheel.center
        tire = [view.to_screen(*c) for c in pose.box(wx, wy, cfg.wheel_diameter_mm, cfg.wheel_width_mm)]
        pygame.draw.polygon(screen, COLORS["wheel"], tire)
        # Rollers: short diagonal strokes across the tread, spaced along the wheel.
        dx, dy = wheel.roller_dir
        half = cfg.wheel_width_mm / 2 * 1.1
        for i in range(-2, 3):
            ox = wx + i * cfg.wheel_diameter_mm / 6
            a = pose.to_field(ox - dx * half, wy - dy * half)
            b = pose.to_field(ox + dx * half, wy + dy * half)
            pygame.draw.line(screen, COLORS["roller"], view.to_screen(*a), view.to_screen(*b), ss)
    pygame.draw.polygon(screen, accent, body, 2 * ss)
    center = view.to_screen(pose.x, pose.y)
    tip = view.to_screen(*pose.to_field(cfg.length_mm / 2 - cfg.wheel_diameter_mm / 2, 0))
    pygame.draw.line(screen, accent, center, tip, 3 * ss)
    pygame.draw.circle(screen, accent, tip, 4 * ss)
    pygame.draw.circle(screen, accent, center, 3 * ss)


class _SpriteView:
    """Maps field mm into a supersampled sprite whose top-left is (x0, y0) on screen."""

    def __init__(self, view, x0, y0, ss):
        self.view, self.x0, self.y0, self.ss = view, x0, y0, ss

    def to_screen(self, x, y):
        v = self.view
        return (int(round((v.ox + x * v.scale - self.x0) * self.ss)),
                int(round((v.oy - y * v.scale - self.y0) * self.ss)))


def blit_robot(screen, view, cfg, pose, alert=False):
    """Draw the robot supersampled in its own small sprite (cheap enough per frame)."""
    import pygame
    pts = [view.to_screen(*c) for c in pose.corners(cfg)]
    pad = 8
    x0, y0 = min(p[0] for p in pts) - pad, min(p[1] for p in pts) - pad
    w, h = max(p[0] for p in pts) + pad - x0, max(p[1] for p in pts) + pad - y0
    big = pygame.Surface((w * SUPERSAMPLE, h * SUPERSAMPLE), pygame.SRCALPHA)
    draw_robot(big, _SpriteView(view, x0, y0, SUPERSAMPLE), cfg, pose, SUPERSAMPLE, alert)
    screen.blit(pygame.transform.smoothscale(big, (w, h)), (x0, y0))


def draw_trail(screen, view, trail):
    import pygame
    if len(trail) > 1:
        pygame.draw.aalines(screen, COLORS["trail"], False, [view.to_screen(x, y) for x, y in trail])


def draw_field(surface, view, elements, show_grid, ss=1):
    """The static field: redrawn only when the grid toggle changes."""
    import pygame

    surface.fill(COLORS["background"])
    field = view.rect(0, 0, fl.FIELD_W, fl.FIELD_H)
    radius = RADIUS * ss
    pygame.draw.rect(surface, COLORS["floor"], field, border_radius=radius)
    red_x0, red_x1 = fl.alliance_x_limits("red")
    blue_x0, blue_x1 = fl.alliance_x_limits("blue")
    pygame.draw.rect(surface, COLORS["red_half"], view.rect(red_x0, 0, red_x1, fl.FIELD_H),
                     border_top_left_radius=radius, border_bottom_left_radius=radius)
    pygame.draw.rect(surface, COLORS["blue_half"], view.rect(blue_x0, 0, blue_x1, fl.FIELD_H),
                     border_top_right_radius=radius, border_bottom_right_radius=radius)

    if show_grid:
        grid = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        step = 500
        for gx in range(step, int(fl.FIELD_W), step):
            pygame.draw.line(grid, COLORS["grid"], view.to_screen(gx, 0), view.to_screen(gx, fl.FIELD_H), ss)
        for gy in range(step, int(fl.FIELD_H), step):
            pygame.draw.line(grid, COLORS["grid"], view.to_screen(0, gy), view.to_screen(fl.FIELD_W, gy), ss)
        surface.blit(grid, (0, 0))

    # Floor items first, overhead structures last as translucent shapes.
    small = 3 * ss
    for kind in ["zone", "obstacle", "slot", "movable", "prop", "no_touch", "overhead"]:
        for el in (e for e in elements if e.kind == kind):
            if el.shape == "circle":
                c = view.to_screen(el.x, el.y)
                r = max(2 * ss, int(el.r * view.scale))
                pygame.draw.circle(surface, COLORS["obstacle_edge"], c, r)
                continue
            r = view.rect(*el.bounds())
            if kind == "zone":
                color = COLORS["zone_red"] if el.alliance == "red" else COLORS["zone_blue"]
                _blend_rect(surface, color + (28,), r, radius)
                pygame.draw.rect(surface, color, r, 2 * ss, border_radius=radius)
            elif kind == "obstacle":
                pygame.draw.rect(surface, COLORS["obstacle"], r, border_radius=small)
                pygame.draw.rect(surface, COLORS["obstacle_edge"], r, ss, border_radius=small)
            elif kind == "slot":
                pygame.draw.rect(surface, COLORS["slot"], r.inflate(-2 * ss, -2 * ss), border_radius=small)
            elif kind == "movable":
                pygame.draw.rect(surface, COLORS["movable"], r, border_radius=radius)
                pygame.draw.rect(surface, COLORS["movable_edge"], r, 2 * ss, border_radius=radius)
            elif kind == "prop":
                color = COLORS["prop_cone"] if el.label == "cone" else COLORS["prop_cube"]
                pygame.draw.rect(surface, color, r, border_radius=small)
            elif kind == "no_touch":
                pygame.draw.rect(surface, COLORS["no_touch"], r, 2 * ss, border_radius=small)
            elif kind == "overhead":
                _blend_rect(surface, COLORS["overhead"], r, small)
                pygame.draw.rect(surface, COLORS["overhead_edge"], r, ss, border_radius=small)

    pygame.draw.rect(surface, COLORS["frame"], field, 2 * ss, border_radius=radius)


class FieldLayer:
    """Caches the supersampled field image; redrawn only when its inputs change."""

    def __init__(self, size):
        self.size = size
        self.view = View(*size)
        self.big_view = View(size[0] * SUPERSAMPLE, size[1] * SUPERSAMPLE, SUPERSAMPLE)
        self._key, self._image = None, None

    def image(self, elements, show_grid):
        import pygame
        key = show_grid
        if key != self._key:
            big = pygame.Surface((self.size[0] * SUPERSAMPLE, self.size[1] * SUPERSAMPLE))
            draw_field(big, self.big_view, elements, show_grid, SUPERSAMPLE)
            self._image = pygame.transform.smoothscale(big, self.size)
            self._key = key
        return self._image


def draw_labels(screen, view, elements, fonts, robot_cfg=None):
    for el in (e for e in elements if e.label):
        if robot_cfg and el.name == robot_cfg.start_area:
            continue  # the robot sits on top of its start-area label
        if el.kind == "prop" and el.label == "cone":
            continue  # the yellow square already reads as a cone; the word does not fit
        dark = el.kind == "prop"
        font = fonts.label if el.kind in ("prop", "slot") else fonts.small
        img = font.render(el.label, True, COLORS["label_dark"] if dark else COLORS["label"])
        sx, sy = view.to_screen(el.x, el.y)
        if el.kind == "slot":  # channel letters sit beside the strip, props sit on top of it
            sx -= int(el.w * view.scale / 2) + 10
        elif el.shape == "circle" or el.name.endswith(("flag_1", "flag_2")):
            # Small posts and poles: put the label beside them, toward the field centre.
            gap = int(max(el.r, el.w / 2) * view.scale) + 6
            if el.alliance == "blue":
                screen.blit(img, img.get_rect(midright=(sx - gap, sy)))
            else:
                screen.blit(img, img.get_rect(midleft=(sx + gap, sy)))
            continue
        screen.blit(img, img.get_rect(center=(sx, sy)))


def draw_hud(screen, view, elements, fonts, hover=None, status=""):
    import pygame
    width = int(view.ox * 2 + fl.FIELD_W * view.scale)
    bar = pygame.Rect(MARGIN_PX, screen.get_height() - HUD_PX - 8, width - 2 * MARGIN_PX, HUD_PX)
    pygame.draw.rect(screen, COLORS["panel"], bar, border_radius=RADIUS)
    if hover:
        hx, hy = hover
        names = [f"{e.name} (z={e.z:.0f})" for e in elements if e.contains(hx, hy)]
        text, font = f"x {hx:6.0f} mm   y {hy:6.0f} mm   {', '.join(names)}", fonts.mono
    else:
        text = (f"Field {fl.FIELD_W:.0f} x {fl.FIELD_H:.0f} mm  ·  floor {fl.FLOOR_PROFILE}  ·  "
                f"G grid   L labels   S screenshot   arrows resize robot")
        font = fonts.body
    img = font.render(text, True, COLORS["muted"])
    screen.blit(img, (bar.x + 12, bar.centery - img.get_height() // 2))
    if status:
        img = fonts.body.render(status, True, COLORS["warning"])
        screen.blit(img, (bar.x + 4, bar.y - img.get_height() - 6))


def draw_banner(screen, view, fonts, text):
    import pygame
    img = fonts.title.render(text, True, COLORS["background"])
    box = img.get_rect(center=(int(view.ox + fl.FIELD_W * view.scale / 2), int(view.oy - fl.FIELD_H * view.scale / 2)))
    pygame.draw.rect(screen, COLORS["warning"], box.inflate(36, 18), border_radius=RADIUS)
    screen.blit(img, box)


def draw(screen, layer, elements, robot_cfg, pose, show_grid, show_labels, fonts, hover=None,
         status="", trail=(), alert=False):
    screen.blit(layer.image(elements, show_grid), (0, 0))
    if show_labels:
        draw_labels(screen, layer.view, elements, fonts, robot_cfg)
    draw_trail(screen, layer.view, trail)
    blit_robot(screen, layer.view, robot_cfg, pose, alert)
    if alert:
        draw_banner(screen, layer.view, fonts, "OUT OF BOUNDARIES")
    draw_hud(screen, layer.view, elements, fonts, hover, status)


def footprint_warning(cfg, pose, elements) -> str:
    """Warn (without blocking) when the footprint does not fit its start area."""
    area = fl.get(elements, cfg.start_area)
    if all(area.contains(x, y) for x, y in pose.corners(cfg)):
        return ""
    return f"Footprint leaves {cfg.start_area} at {cfg.heading_deg:g}° (start area is 500 x 500 mm)"


PROGRAMS_DIR = Path(__file__).resolve().parent.parent / "control"  # simulation/control

_TK_DIALOG = """
import sys, tkinter, tkinter.filedialog
root = tkinter.Tk(); root.withdraw()
print(tkinter.filedialog.askopenfilename(initialdir=sys.argv[1], title="Select an mBlock Python program",
                                         filetypes=[("Python", "*.py")]) or "")
"""


def choose_python_file(initial_dir: Path):
    """Native file picker in a separate process (keeps it out of the pygame event loop)."""
    try:
        if sys.platform == "darwin":
            script = (f'POSIX path of (choose file with prompt "Select an mBlock Python program" '
                      f'default location (POSIX file "{initial_dir}"))')
            out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        else:
            out = subprocess.run([sys.executable, "-c", _TK_DIALOG, str(initial_dir)],
                                 capture_output=True, text=True)
    except OSError:
        return None
    path = out.stdout.strip()
    return Path(path) if path else None


class GamepadLauncher:
    """Opens the emulated gamepad (gamepad.py) in its own process and window, and
    feeds its JSON event lines to the simulation as the Bluetooth link."""

    SCRIPT = Path(__file__).with_name("gamepad.py")

    def __init__(self, gamepad_input, say):
        self.input, self.say = gamepad_input, say
        self.proc = None

    @property
    def connected(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def open(self):
        if self.connected:
            self.say("Gamepad window is already open")
            return
        try:
            self.proc = subprocess.Popen([sys.executable, str(self.SCRIPT)], stdout=subprocess.PIPE,
                                         text=True, bufsize=1)
        except OSError as exc:
            self.say(f"Could not open the gamepad: {exc}", True)
            return
        threading.Thread(target=self._read, args=(self.proc,), name="gamepad-link", daemon=True).start()
        self.say("Gamepad connected")

    def _read(self, proc):
        for line in proc.stdout:
            try:
                self.input.apply_event(json.loads(line))
            except (ValueError, TypeError):
                continue  # not an event line
        self.input.disconnect()  # window closed: sticks to 0, keys released

    def close(self):
        if self.connected:
            self.proc.terminate()


class ProgramController:
    """Glue between the panel's Load / Run / Stop buttons and the simulation."""

    def __init__(self, sim: Simulation, say):
        self.sim, self.say = sim, say

    def load(self):
        if self.sim.running:
            self.sim.stop()
        path = choose_python_file(self.sim.program.parent if self.sim.program else PROGRAMS_DIR)
        if path is None:
            return
        if path.suffix != ".py":
            self.say(f"{path.name} is not a .py file", True)
            return
        self.sim.program = path
        self.sim.reset()
        self.say(f"Loaded {path.name}, press Run")

    def run(self):
        self.sim.run()
        if self.sim.state.status == "error":
            self.say(self.sim.state.message, True)

    def stop(self):
        if self.sim.running:
            self.sim.stop()
        else:
            self.sim.reset()  # second press puts the robot back on its start pose

    def toggle(self):
        self.stop() if self.sim.running else self.run()

    def status(self):
        name = self.sim.program.name if self.sim.program else None
        st = self.sim.state
        return name, self.sim.time, self.sim.time_limit, st.status, st.message


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="robot config JSON")
    parser.add_argument("--size", default="1440x900", help="window size WxH in px (panel included)")
    parser.add_argument("--screenshot", type=Path, help="render once to this PNG and exit")
    parser.add_argument("--length", type=float, help="robot length in mm (overrides config)")
    parser.add_argument("--width", type=float, help="robot width in mm (overrides config)")
    parser.add_argument("--heading", type=float, help="robot heading in degrees, CCW from +x")
    parser.add_argument("--program", type=Path, help="mBlock Python program to preload")
    parser.add_argument("--time-limit", type=float, default=AUTO_STAGE_S,
                        help="stop the run after this many simulated seconds (0 = no limit)")
    parser.add_argument("--run-for", type=float, default=0,
                        help="with --screenshot: run the program this many seconds first")
    args = parser.parse_args(argv)

    if args.screenshot:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame

    width, height = (int(v) for v in args.size.lower().split("x"))
    elements = fl.build_field()
    robot_cfg = load_config(args.config)
    if args.length is not None or args.width is not None:
        try:
            robot_cfg = robot_cfg.resized(args.length or robot_cfg.length_mm,
                                          args.width or robot_cfg.width_mm)
        except ValueError as exc:
            parser.error(str(exc))
    if args.heading is not None:
        robot_cfg = replace(robot_cfg, heading_deg=args.heading)
    sim = Simulation(robot_cfg, start_pose(robot_cfg, elements), load_drive_train(args.config),
                     args.time_limit, load_gyro_sign(args.config))
    if args.program:
        if not args.program.is_file():
            parser.error(f"--program {args.program} not found")
        sim.program = args.program

    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("MakeX Storm Breaker - 2D field")
    fonts = Fonts()
    layer = FieldLayer((width - PANEL_W, height))
    view = layer.view

    def apply_config(cfg) -> str:
        nonlocal robot_cfg
        robot_cfg = cfg
        sim.reset(cfg, start_pose(cfg, elements))
        return footprint_warning(cfg, sim.pose, elements)

    controller = ProgramController(sim, say=None)
    gamepad = GamepadLauncher(sim.gamepad, say=None)
    panel = RobotPanel(width - PANEL_W, height, robot_cfg, args.config, apply_config, controller, gamepad)
    controller.say = gamepad.say = panel.say
    note = footprint_warning(robot_cfg, sim.pose, elements)

    def render(hover=None):
        st = sim.state
        alert = st.status == "out_of_bounds"
        message = st.message if st.status in ("out_of_bounds", "error") else note
        draw(screen, layer, elements, robot_cfg, sim.pose, show_grid, show_labels, fonts, hover,
             message, st.trail, alert)
        panel.draw(screen, fonts)

    show_grid, show_labels = True, True
    if args.screenshot:
        if args.run_for and sim.program:
            sim.run()
            for _ in range(int(args.run_for * 60)):
                sim.step(1 / 60)
        render()
        pygame.image.save(screen, str(args.screenshot))
        sim.reset()
        pygame.quit()
        return 0

    clock = pygame.time.Clock()
    running = True
    while running:
        frame_s = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif panel.handle(event):
                continue
            elif event.type == pygame.KEYDOWN:
                step = 1 if event.mod & pygame.KMOD_SHIFT else 10
                sizes = {
                    pygame.K_UP: (step, 0), pygame.K_DOWN: (-step, 0),
                    pygame.K_RIGHT: (0, step), pygame.K_LEFT: (0, -step),
                }
                if event.key in sizes:
                    dl, dw = sizes[event.key]
                    try:
                        cfg = robot_cfg.resized(robot_cfg.length_mm + dl, robot_cfg.width_mm + dw)
                        note = apply_config(cfg)
                        panel.set_config(cfg)
                    except ValueError as exc:
                        note = str(exc)
                elif event.key == pygame.K_SPACE:
                    controller.toggle()
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_g:
                    show_grid = not show_grid
                elif event.key == pygame.K_l:
                    show_labels = not show_labels
                elif event.key == pygame.K_s:
                    pygame.image.save(screen, "field_screenshot.png")
        was_running = sim.running
        sim.step(frame_s)
        if was_running and not sim.running:
            panel.say(sim.state.message, sim.state.status in ("out_of_bounds", "error"))
        mx, my = pygame.mouse.get_pos()
        hx, hy = view.to_field(mx, my)
        inside = mx < width - PANEL_W and 0 <= hx <= fl.FIELD_W and 0 <= hy <= fl.FIELD_H
        render((hx, hy) if inside else None)
        pygame.display.flip()
    sim.reset()
    gamepad.close()
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
