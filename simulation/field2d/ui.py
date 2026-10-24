"""Minimal pygame widgets for the viewer side panel: buttons, text boxes, dial, dropdown."""

import math

import pygame
import pygame.gfxdraw


from theme import PALETTE as UI_COLORS, RADIUS


class Button:
    def __init__(self, rect, label, on_click, primary=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.primary = primary
        self.selected = False

    def handle(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.on_click()
            return True
        return False

    def draw(self, screen, font):
        if self.selected:
            color = UI_COLORS["button_selected"]
        elif self.primary:
            color = UI_COLORS["button_primary"]
        elif self.rect.collidepoint(pygame.mouse.get_pos()):
            color = UI_COLORS["button_hover"]
        else:
            color = UI_COLORS["button"]
        pygame.draw.rect(screen, color, self.rect, border_radius=RADIUS)
        pygame.draw.rect(screen, UI_COLORS["border"], self.rect, 1, border_radius=RADIUS)
        img = font.render(self.label, True, UI_COLORS["text"])
        screen.blit(img, img.get_rect(center=self.rect.center))


class TextBox:
    """Single-line numeric input. Click to focus, type digits, Enter or Apply to commit."""

    ALLOWED = "0123456789."

    def __init__(self, rect, text="", max_len=6):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.max_len = max_len
        self.focused = False
        self.invalid = False

    def handle(self, event) -> bool:
        """Returns True when the event was consumed by this box."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
            return self.focused
        if event.type != pygame.KEYDOWN or not self.focused:
            return False
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key in (pygame.K_TAB, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
            return False  # let the panel handle focus changes and submit
        elif event.unicode and event.unicode in self.ALLOWED and len(self.text) < self.max_len:
            self.text += event.unicode
        self.invalid = False
        return True

    def value(self):
        """Float value, or None if the text is not a number."""
        try:
            return float(self.text)
        except ValueError:
            return None

    def draw(self, screen, font):
        pygame.draw.rect(screen, UI_COLORS["box"], self.rect, border_radius=RADIUS)
        border = UI_COLORS["error"] if self.invalid else UI_COLORS["focus"] if self.focused else UI_COLORS["border"]
        pygame.draw.rect(screen, border, self.rect, 2 if self.focused or self.invalid else 1, border_radius=RADIUS)
        caret = "|" if self.focused and pygame.time.get_ticks() // 500 % 2 == 0 else ""
        img = font.render(self.text + caret, True, UI_COLORS["text"])
        screen.blit(img, (self.rect.x + 8, self.rect.centery - img.get_height() // 2))


class Dial:
    """Angle picker drawn as a clock face; a knob on the rim marks the angle.

    Angles follow the field convention: 0 deg points right (+x, toward blue) and
    grow counter-clockwise. Click or drag on the face to move the knob; the mouse
    wheel nudges it. Values snap to `step` degrees. `applied` is drawn as a faint
    hand so the pending value can be compared with the one on the field.
    """

    def __init__(self, center, radius, value=0.0, step=5, on_change=None):
        self.center = center
        self.radius = radius
        self.step = step
        self.on_change = on_change
        self.value = self.snap(value)
        self.applied = self.value
        self.dragging = False

    def snap(self, deg: float) -> float:
        return float(round(deg / self.step) * self.step % 360)

    def angle_at(self, pos) -> float:
        dx, dy = pos[0] - self.center[0], self.center[1] - pos[1]  # screen y points down
        return self.snap(math.degrees(math.atan2(dy, dx)))

    def contains(self, pos) -> bool:
        dx, dy = pos[0] - self.center[0], pos[1] - self.center[1]
        return dx * dx + dy * dy <= (self.radius + 12) ** 2

    def set_value(self, deg: float) -> None:
        deg = self.snap(deg)
        if deg != self.value:
            self.value = deg
            if self.on_change:
                self.on_change(deg)

    def handle(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.contains(event.pos):
            self.dragging = True
            self.set_value(self.angle_at(event.pos))
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.set_value(self.angle_at(event.pos))
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True
        if event.type == pygame.MOUSEWHEEL and self.contains(pygame.mouse.get_pos()):
            self.set_value(self.value + event.y * self.step)
            return True
        return False

    def _point(self, deg: float, r: float):
        a = math.radians(deg)
        return self.center[0] + r * math.cos(a), self.center[1] - r * math.sin(a)

    def draw(self, screen, font):
        cx, cy = self.center
        r = self.radius
        pygame.gfxdraw.filled_circle(screen, cx, cy, r, UI_COLORS["dial_face"])
        pygame.gfxdraw.aacircle(screen, cx, cy, r, UI_COLORS["border"])
        pygame.gfxdraw.aacircle(screen, cx, cy, r - 1, UI_COLORS["border"])
        # Ticks every 5 deg, longer every 45 deg, labels on the four axes.
        for deg in range(0, 360, self.step):
            major = deg % 45 == 0
            inner = r - (10 if major else 5)
            color = UI_COLORS["dial_tick_major"] if major else UI_COLORS["dial_tick"]
            if major:
                pygame.draw.line(screen, color, self._point(deg, inner), self._point(deg, r - 3), 2)
            else:
                pygame.draw.aaline(screen, color, self._point(deg, inner), self._point(deg, r - 3))
        for deg in (0, 90, 180, 270):
            gap = abs(deg - self.value) % 360
            if min(gap, 360 - gap) < 15 or abs(gap - 180) < 15:
                continue  # covered by the hand, or by the value label opposite it
            img = font.render(f"{deg}", True, UI_COLORS["muted"])
            screen.blit(img, img.get_rect(center=self._point(deg, r - 28)))
        # Applied heading (faint) and pending heading (hand plus knob on the rim).
        if self.applied != self.value:
            pygame.draw.line(screen, UI_COLORS["dial_applied"], self.center, self._point(self.applied, r - 14), 2)
        tip = self._point(self.value, r)
        pygame.draw.line(screen, UI_COLORS["dial_pending"], self.center, tip, 3)
        kx, ky = int(round(tip[0])), int(round(tip[1]))
        pygame.gfxdraw.filled_circle(screen, kx, ky, 9, UI_COLORS["dial_pending"])
        pygame.gfxdraw.aacircle(screen, kx, ky, 9, UI_COLORS["dial_pending"])
        pygame.gfxdraw.filled_circle(screen, kx, ky, 4, UI_COLORS["dial_face"])
        pygame.gfxdraw.aacircle(screen, kx, ky, 4, UI_COLORS["dial_face"])
        pygame.gfxdraw.filled_circle(screen, cx, cy, 4, UI_COLORS["text"])
        pygame.gfxdraw.aacircle(screen, cx, cy, 4, UI_COLORS["text"])
        img = font.render(f"{self.value:g}°", True, UI_COLORS["text"])
        screen.blit(img, img.get_rect(center=self._point(self.value + 180, 26)))  # opposite the hand


class Dropdown:
    """Closed: a box showing the selected label. Click to open a list below it.

    `options` is a list of (value, label). The open list is drawn on top of the
    other widgets, so call draw() last and handle() first while it is open.
    """

    def __init__(self, rect, options, value, on_change=None):
        self.rect = pygame.Rect(rect)
        self.options = list(options)
        self.value = value
        self.on_change = on_change
        self.open = False

    def label(self) -> str:
        return dict(self.options).get(self.value, str(self.value))

    def _option_rect(self, i: int) -> pygame.Rect:
        return pygame.Rect(self.rect.x, self.rect.bottom + i * self.rect.height,
                           self.rect.width, self.rect.height)

    def handle(self, event) -> bool:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if self.rect.collidepoint(event.pos):
            self.open = not self.open
            return True
        if self.open:
            self.open = False
            for i, (value, _) in enumerate(self.options):
                if self._option_rect(i).collidepoint(event.pos):
                    if value != self.value:
                        self.value = value
                        if self.on_change:
                            self.on_change(value)
                    return True
            return True  # click outside closes the list without passing through
        return False

    def draw(self, screen, font):
        pygame.draw.rect(screen, UI_COLORS["box"], self.rect, border_radius=RADIUS)
        border = UI_COLORS["focus"] if self.open else UI_COLORS["border"]
        pygame.draw.rect(screen, border, self.rect, 2 if self.open else 1, border_radius=RADIUS)
        img = font.render(self.label(), True, UI_COLORS["text"])
        screen.blit(img, (self.rect.x + 8, self.rect.centery - img.get_height() // 2))
        # Caret triangle on the right.
        cx, cy = self.rect.right - 14, self.rect.centery
        tri = [(cx - 5, cy - 2), (cx + 5, cy - 2), (cx, cy + 4)] if not self.open else \
              [(cx - 5, cy + 3), (cx + 5, cy + 3), (cx, cy - 3)]
        pygame.draw.polygon(screen, UI_COLORS["muted"], tri)

    def draw_list(self, screen, font):
        if not self.open:
            return
        mouse = pygame.mouse.get_pos()
        for i, (value, label) in enumerate(self.options):
            r = self._option_rect(i)
            if value == self.value:
                color = UI_COLORS["button_selected"]
            elif r.collidepoint(mouse):
                color = UI_COLORS["button_hover"]
            else:
                color = UI_COLORS["button"]
            pygame.draw.rect(screen, color, r)
            pygame.draw.rect(screen, UI_COLORS["border"], r, 1)
            img = font.render(label, True, UI_COLORS["text"])
            screen.blit(img, (r.x + 8, r.centery - img.get_height() // 2))
