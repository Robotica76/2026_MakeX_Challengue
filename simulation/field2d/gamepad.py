"""On-screen Makeblock Bluetooth gamepad (emulated), in its own window.

Layout follows the Makeblock controller: shoulder buttons L1/L2/R2/R1, arrow
keys, Menu / Bluetooth / Plus, number buttons 1-4, two joysticks, the indicator
LED and the On/Off switch. Every physical control is clickable:

- buttons light up while held (mouse down),
- joysticks can be dragged and spring back to centre on release,
- On/Off toggles; while off the other controls do nothing.

Each change is printed to stdout as one JSON line, e.g.
    {"event": "press", "control": "L1"}
    {"event": "axis", "control": "left_stick", "x": 0.42, "y": -1.0}
which the viewer reads as the Bluetooth link (mbuild.gamepad in the program).

Run standalone:  python gamepad.py   (the viewer's "Open gamepad" button does this)
"""

import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import pygame
import pygame.gfxdraw

from theme import PALETTE, RADIUS, Fonts

WINDOW = (1000, 640)
SUPERSAMPLE = 3
# Controller drawn in "design" units taken from the reference picture, then
# mapped to the window with this scale/offset (controller centred, room for callouts).
SCALE = 1.5
ORIGIN = (370 - WINDOW[0] / 2 / SCALE, 360 - 340 / SCALE)

PAD = {
    "body": (236, 238, 243),
    "body_edge": (196, 200, 210),
    "shoulder": (212, 215, 222),
    "shoulder_edge": (176, 180, 190),
    "key": (38, 41, 48),
    "key_hover": (62, 66, 76),
    "key_pressed": PALETTE["robot"],
    "key_text": (236, 238, 243),
    "logo": (170, 174, 184),
    "led_off": (176, 180, 190),
    "led_on": PALETTE["zone_blue"],
}


def to_px(x: float, y: float) -> Tuple[int, int]:
    return int(round((x - ORIGIN[0]) * SCALE)), int(round((y - ORIGIN[1]) * SCALE))


@dataclass
class Control:
    name: str            # id sent to the simulator, e.g. "L1", "up", "button_1"
    label: str           # text drawn on/near the control
    shape: str           # circle | rect | stick | switch
    x: float             # centre, design units
    y: float
    w: float = 0.0       # rect size or circle/stick diameter, design units
    h: float = 0.0

    def rect(self) -> pygame.Rect:
        cx, cy = to_px(self.x, self.y)
        w, h = self.w * SCALE, (self.h or self.w) * SCALE
        return pygame.Rect(int(cx - w / 2), int(cy - h / 2), int(w), int(h))

    def hit(self, pos) -> bool:
        if self.shape in ("circle", "stick"):
            cx, cy = to_px(self.x, self.y)
            r = self.w * SCALE / 2 + 4
            return (pos[0] - cx) ** 2 + (pos[1] - cy) ** 2 <= r * r
        return self.rect().inflate(6, 6).collidepoint(pos)


def build_controls():
    d = 18  # D-pad arm size
    return [
        # Shoulders (top edge)
        Control("L1", "L1", "rect", 258, 255, 54, 12),
        Control("L2", "L2", "rect", 318, 253, 36, 10),
        Control("R2", "R2", "rect", 422, 253, 36, 10),
        Control("R1", "R1", "rect", 482, 255, 54, 12),
        # Arrow keys
        Control("up", "", "rect", 262, 322 - d, d, d),
        Control("down", "", "rect", 262, 322 + d, d, d),
        Control("left", "", "rect", 262 - d, 322, d, d),
        Control("right", "", "rect", 262 + d, 322, d, d),
        # Centre buttons
        Control("menu", "", "circle", 343, 322, 14),
        Control("bluetooth", "B", "circle", 370, 322, 14),
        Control("plus", "+", "circle", 398, 322, 14),
        # Number buttons
        Control("button_2", "2", "circle", 472, 294, 24),
        Control("button_1", "1", "circle", 446, 321, 24),
        Control("button_4", "4", "circle", 499, 321, 24),
        Control("button_3", "3", "circle", 472, 348, 24),
        # Joysticks
        Control("left_stick", "", "stick", 322, 382, 36),
        Control("right_stick", "", "stick", 418, 382, 36),
        # Power switch (on the back of the real controller, drawn below it)
        Control("power", "", "switch", 370, 505, 40, 16),
    ]


# Callouts like the reference picture: (text, side, design y or x, target point).
# side "left"/"right": text at the window edge at height y; "top": text above at x.
CALLOUTS = [
    ("Custom button L1", "left", 236, (240, 243)),
    ("Custom button L2", "left", 206, (318, 243)),
    ("Arrow keys", "left", 322, (234, 322)),
    ("Left joystick", "left", 382, (304, 382)),
    ("On / Off (back)", "left", 505, (356, 505)),
    ("Custom button R2", "right", 206, (422, 243)),
    ("Custom button R1", "right", 236, (500, 243)),
    ("Number buttons", "right", 300, (484, 294)),
    ("Right joystick", "right", 382, (436, 382)),
    ("Indicator", "right", 430, (374, 386)),
    ("Menu", "top", 330, (343, 315)),
    ("Bluetooth", "top", 370, (370, 315)),
    ("Plus", "top", 410, (398, 315)),
]


class GamepadState:
    def __init__(self, emit=None):
        self.on = True
        self.pressed: Optional[str] = None             # button held by the mouse
        self.axes: Dict[str, Tuple[float, float]] = {"left_stick": (0.0, 0.0), "right_stick": (0.0, 0.0)}
        self.dragging: Optional[str] = None
        self.last = "Ready"
        self.emit = emit or (lambda event: None)

    def _send(self, **event):
        self.emit(event)
        self.last = " ".join(f"{k}={v}" for k, v in event.items() if k != "event")
        self.last = f"{event['event']}: {self.last}"

    def press(self, control: Control):
        if control.shape == "switch":
            self.on = not self.on
            self.release()
            self.axes = {k: (0.0, 0.0) for k in self.axes}
            self._send(event="power", control="power", on=self.on)
            return
        if not self.on:
            self.last = "Gamepad is off: switch it on first"
            return
        if control.shape == "stick":
            self.dragging = control.name
            return
        self.pressed = control.name
        self._send(event="press", control=control.name)

    def drag(self, control: Control, pos):
        cx, cy = to_px(control.x, control.y)
        reach = control.w * SCALE * 0.6
        dx, dy = (pos[0] - cx) / reach, (pos[1] - cy) / reach
        length = math.hypot(dx, dy)
        if length > 1:
            dx, dy = dx / length, dy / length
        # Up is +y for the robot, screen y grows downward.
        value = (round(dx, 2), round(-dy, 2))
        if value != self.axes[control.name]:
            self.axes[control.name] = value
            self._send(event="axis", control=control.name, x=value[0], y=value[1])

    def release(self):
        if self.pressed:
            self._send(event="release", control=self.pressed)
            self.pressed = None
        if self.dragging:
            name, self.dragging = self.dragging, None
            self.axes[name] = (0.0, 0.0)
            self._send(event="axis", control=name, x=0.0, y=0.0)


def _draw_body(surface, s):
    """Controller shell at supersample factor s (shoulders, body, grips)."""
    def p(x, y):
        px, py = to_px(x, y)
        return px * s, py * s

    def r(v):
        return int(v * SCALE * s)

    body, edge = PAD["body"], PAD["body_edge"]
    grips = [p(gx, 420) for gx in (248, 492)]       # two big circles at the bottom corners
    top = pygame.Rect(*p(196, 262), r(348), r(150))
    bridge = pygame.Rect(*p(248, 380), r(244), r(62))  # fills between the grips
    # Outline of the union first (slightly larger shapes), then the fills on top,
    # so only the outer silhouette gets an edge.
    e = 2 * s
    for c in grips:
        pygame.draw.circle(surface, edge, c, r(56) + e)
    pygame.draw.rect(surface, edge, top.inflate(2 * e, 2 * e), border_radius=r(46))
    pygame.draw.rect(surface, edge, bridge.inflate(2 * e, 2 * e), border_radius=r(26))
    for c in grips:
        pygame.draw.circle(surface, body, c, r(56))
    pygame.draw.rect(surface, body, top, border_radius=r(46))
    pygame.draw.rect(surface, body, bridge, border_radius=r(26))


def render_static(size):
    """Shell drawn supersampled once; controls are drawn on top every frame."""
    big = pygame.Surface((size[0] * SUPERSAMPLE, size[1] * SUPERSAMPLE), pygame.SRCALPHA)
    _draw_body(big, SUPERSAMPLE)
    return pygame.transform.smoothscale(big, size)


def draw(screen, fonts, shell, controls, state, hover: Optional[str]):
    screen.fill(PALETTE["background"])
    title = fonts.title.render("Makeblock gamepad (emulated)", True, PALETTE["text"])
    screen.blit(title, (24, 18))
    sub = fonts.body.render("Click buttons, drag the joysticks. Opened from the viewer, it drives mbuild.gamepad.",
                            True, PALETTE["muted"])
    screen.blit(sub, (24, 46))

    # Shoulders sit behind the shell.
    for c in controls:
        if c.name in ("L1", "L2", "R1", "R2"):
            color = PAD["key_pressed"] if state.pressed == c.name else \
                PAD["key_hover"] if hover == c.name else PAD["shoulder"]
            rect = c.rect().move(0, -6)
            pygame.draw.rect(screen, color, rect, border_radius=RADIUS)
            pygame.draw.rect(screen, PAD["shoulder_edge"], rect, 1, border_radius=RADIUS)
            img = fonts.label.render(c.label, True, PAD["key"] if color != PAD["key_hover"] else PAD["key_text"])
            screen.blit(img, img.get_rect(center=rect.center))
    screen.blit(shell, (0, 0))
    logo = fonts.small.render("makeblock", True, PAD["logo"])
    screen.blit(logo, logo.get_rect(center=to_px(370, 290)))

    # D-pad base so the four arms read as one cross.
    cx, cy = to_px(262, 322)
    arm = int(18 * SCALE)
    for rect in (pygame.Rect(cx - arm * 3 // 2, cy - arm // 2, arm * 3, arm),
                 pygame.Rect(cx - arm // 2, cy - arm * 3 // 2, arm, arm * 3)):
        pygame.draw.rect(screen, PAD["key"], rect, border_radius=RADIUS)

    for c in controls:
        if c.name in ("L1", "L2", "R1", "R2"):
            continue
        active = state.pressed == c.name or state.dragging == c.name
        color = PAD["key_pressed"] if active else PAD["key_hover"] if hover == c.name else PAD["key"]
        if not state.on and c.shape != "switch":
            color = PAD["key"]
        if c.shape == "rect":  # D-pad arm with an arrow
            rect = c.rect()
            if active or hover == c.name:
                pygame.draw.rect(screen, color, rect.inflate(-4, -4), border_radius=RADIUS)
            _arrow(screen, rect.center, c.name, PAD["key_text"])
        elif c.shape == "circle":
            x, y = to_px(c.x, c.y)
            rad = int(c.w * SCALE / 2)
            pygame.gfxdraw.filled_circle(screen, x, y, rad, color)
            pygame.gfxdraw.aacircle(screen, x, y, rad, color)
            if c.name == "menu":  # three bars; the ≡ glyph is missing from many fonts
                for dy in (-4, 0, 4):
                    pygame.draw.line(screen, PAD["key_text"], (x - 5, y + dy), (x + 5, y + dy), 2)
            else:
                img = (fonts.title if c.w > 20 else fonts.label).render(c.label, True, PAD["key_text"])
                screen.blit(img, img.get_rect(center=(x, y)))
        elif c.shape == "stick":
            x, y = to_px(c.x, c.y)
            rad = int(c.w * SCALE / 2)
            pygame.gfxdraw.filled_circle(screen, x, y, rad + 6, PAD["body_edge"])
            pygame.gfxdraw.aacircle(screen, x, y, rad + 6, PAD["body_edge"])
            ax, ay = state.axes[c.name]
            kx, ky = int(x + ax * rad * 0.6), int(y - ay * rad * 0.6)
            pygame.gfxdraw.filled_circle(screen, kx, ky, rad, color)
            pygame.gfxdraw.aacircle(screen, kx, ky, rad, color)
            pygame.gfxdraw.aacircle(screen, kx, ky, rad - 6, PAD["key_hover"])
        elif c.shape == "switch":
            rect = c.rect()
            pygame.draw.rect(screen, PAD["shoulder"], rect, border_radius=rect.height // 2)
            pygame.draw.rect(screen, PAD["shoulder_edge"], rect, 1, border_radius=rect.height // 2)
            knob_x = rect.right - rect.height // 2 if state.on else rect.left + rect.height // 2
            knob = PALETTE["robot"] if state.on else PAD["key"]
            pygame.gfxdraw.filled_circle(screen, knob_x, rect.centery, rect.height // 2 - 3, knob)
            pygame.gfxdraw.aacircle(screen, knob_x, rect.centery, rect.height // 2 - 3, knob)
            img = fonts.label.render("ON" if state.on else "OFF", True, PALETTE["text"])
            screen.blit(img, img.get_rect(midleft=(rect.right + 10, rect.centery)))

    # Indicator LED: lit while the pad is on, brighter while any input is active.
    lx, ly = to_px(370, 384)
    busy = state.pressed or state.dragging
    led = PAD["led_on"] if state.on else PAD["led_off"]
    pygame.gfxdraw.filled_circle(screen, lx, ly, 6 if busy else 5, led)
    pygame.gfxdraw.aacircle(screen, lx, ly, 6 if busy else 5, led)

    draw_callouts(screen, fonts)

    # Status bar
    bar = pygame.Rect(24, WINDOW[1] - 48, WINDOW[0] - 48, 32)
    pygame.draw.rect(screen, PALETTE["panel"], bar, border_radius=RADIUS)
    sticks = "   ".join(f"{k.split('_')[0]} ({x:+.2f}, {y:+.2f})" for k, (x, y) in state.axes.items())
    img = fonts.mono.render(f"{state.last:<44}  {sticks}", True, PALETTE["muted"])
    screen.blit(img, (bar.x + 12, bar.centery - img.get_height() // 2))


def draw_callouts(screen, fonts):
    """Captions at the window edges with thin leader lines to each control."""
    line = PALETTE["border"]
    for text, side, at, target in CALLOUTS:
        img = fonts.small.render(text, True, PALETTE["muted"])
        tx, ty = to_px(*target)
        if side == "top":
            x = to_px(at, 0)[0]
            box = img.get_rect(midbottom=(x, to_px(0, 205)[1]))
            start = (x, box.bottom + 4)
            elbow = (x, ty - 22)
            pygame.draw.aalines(screen, line, False, [start, elbow, (tx, ty - 10)])
        else:
            y = to_px(0, at)[1]
            if side == "left":
                box = img.get_rect(midleft=(28, y))
                start = (box.right + 8, y)
            else:
                box = img.get_rect(midright=(WINDOW[0] - 28, y))
                start = (box.left - 8, y)
            pygame.draw.aalines(screen, line, False, [start, (tx, y), (tx, ty)] if y != ty else [start, (tx, ty)])
        pygame.gfxdraw.filled_circle(screen, tx, ty, 2, line)
        screen.blit(img, box)


def _arrow(screen, center, direction, color):
    x, y = center
    k = 7
    points = {
        "up": [(x, y - k), (x - k, y + k // 2), (x + k, y + k // 2)],
        "down": [(x, y + k), (x - k, y - k // 2), (x + k, y - k // 2)],
        "left": [(x - k, y), (x + k // 2, y - k), (x + k // 2, y + k)],
        "right": [(x + k, y), (x - k // 2, y - k), (x - k // 2, y + k)],
    }[direction]
    pygame.gfxdraw.filled_polygon(screen, points, color)
    pygame.gfxdraw.aapolygon(screen, points, color)


def emit_json(event):
    print(json.dumps(event), flush=True)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    screenshot = argv[argv.index("--screenshot") + 1] if "--screenshot" in argv else None
    if screenshot:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    screen = pygame.display.set_mode(WINDOW)
    pygame.display.set_caption("MakeX simulator - gamepad")
    fonts = Fonts()
    shell = render_static(WINDOW)
    controls = build_controls()
    state = GamepadState(emit_json)

    if screenshot:
        state.pressed, state.axes["left_stick"] = "button_2", (0.6, 0.5)
        draw(screen, fonts, shell, controls, state, hover="L1")
        pygame.image.save(screen, screenshot)
        pygame.quit()
        return 0

    clock = pygame.time.Clock()
    running = True
    while running:
        mouse = pygame.mouse.get_pos()
        hover = next((c.name for c in reversed(controls) if c.hit(mouse)), None)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                hit = next((c for c in reversed(controls) if c.hit(event.pos)), None)
                if hit:
                    state.press(hit)
                    if hit.shape == "stick" and state.dragging:
                        state.drag(hit, event.pos)
            elif event.type == pygame.MOUSEMOTION and state.dragging:
                stick = next(c for c in controls if c.name == state.dragging)
                state.drag(stick, event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                state.release()
        draw(screen, fonts, shell, controls, state, hover)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
