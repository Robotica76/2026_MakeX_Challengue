"""Side panel to set the robot start area, orientation and footprint, applied with Apply."""

from dataclasses import replace
from pathlib import Path
from typing import Callable

import pygame

from robot import RobotConfig, load_config, save_config
from ui import UI_COLORS, Button, Dial, Dropdown, TextBox

START_OPTIONS = [
    ("red_start_1", "Red - Start 1"),
    ("red_start_2", "Red - Start 2"),
    ("blue_start_1", "Blue - Start 1"),
    ("blue_start_2", "Blue - Start 2"),
]
HEADING_STEP_DEG = 5
DIAL_RADIUS = 72
PANEL_W = 260
PAD = 16


class RobotPanel:
    """Holds pending edits; nothing changes on the field until Apply (or Enter)."""

    def __init__(self, x: int, height: int, cfg: RobotConfig, config_path: Path,
                 on_apply: Callable[[RobotConfig], str]):
        self.rect = pygame.Rect(x, 0, PANEL_W, height)
        self.cfg = cfg
        self.config_path = config_path
        self.on_apply = on_apply
        self.message, self.message_is_error = "", False

        left, inner, gap = x + PAD, PANEL_W - 2 * PAD, 6
        y = 64
        self.start_label_y = y - 22
        self.start_dropdown = Dropdown((left, y, inner, 30), START_OPTIONS, cfg.start_area,
                                       self._select_start)

        y += 30 + 40
        self.headings_label_y = y - 22
        self.dial = Dial((x + PANEL_W // 2, y + 12 + DIAL_RADIUS), DIAL_RADIUS, cfg.heading_deg,
                         HEADING_STEP_DEG, self._select_heading)

        y += 2 * DIAL_RADIUS + 50
        self.length_label_y = y
        self.length_box = TextBox((left, y + 20, inner, 32), f"{cfg.length_mm:g}")
        y += 70
        self.width_label_y = y
        self.width_box = TextBox((left, y + 20, inner, 32), f"{cfg.width_mm:g}")
        y += 76
        self.apply_button = Button((left, y, inner, 38), "Apply", self.apply, primary=True)
        y += 48
        half = (inner - gap) // 2
        self.reset_button = Button((left, y, half, 30), "Reset", self.reset)
        self.save_button = Button((left + half + gap, y, half, 30), "Save", self.save)
        self.message_y = y + 44
        self.boxes = [self.length_box, self.width_box]
        self.buttons = [self.apply_button, self.reset_button, self.save_button]

    # --- actions ---------------------------------------------------------------
    @property
    def pending_heading(self) -> float:
        return self.dial.value

    @property
    def pending_start(self) -> str:
        return self.start_dropdown.value

    def _select_start(self, start_area: str) -> None:
        self._say(f"{self.start_dropdown.label()} selected, press Apply")

    def _select_heading(self, deg: float) -> None:
        self._say(f"Heading {deg:g}° selected, press Apply")

    def _say(self, text: str, error: bool = False) -> None:
        self.message, self.message_is_error = text, error

    def apply(self) -> None:
        length, width = self.length_box.value(), self.width_box.value()
        self.length_box.invalid, self.width_box.invalid = length is None, width is None
        if length is None or width is None:
            self._say("Length and width must be numbers in mm", error=True)
            return
        try:
            cfg = replace(self.cfg.resized(length, width), heading_deg=float(self.pending_heading),
                          start_area=self.pending_start, alliance=self.pending_start.split("_")[0])
        except ValueError as exc:
            self._say(str(exc), error=True)
            return
        self.set_config(cfg)
        warning = self.on_apply(cfg)
        self._say(warning or f"Applied {self.start_dropdown.label()}, {length:g} x {width:g} mm, "
                             f"{self.pending_heading:g}°", bool(warning))

    def reset(self) -> None:
        self.set_config(load_config(self.config_path))
        self.on_apply(self.cfg)
        self._say(f"Reloaded {self.config_path.name}")

    def save(self) -> None:
        save_config(self.cfg, self.config_path)
        self._say(f"Saved applied values to {self.config_path.name}")

    def set_config(self, cfg: RobotConfig) -> None:
        """Show an externally changed config (e.g. arrow keys) in the boxes."""
        self.cfg = cfg
        self.dial.value = self.dial.applied = self.dial.snap(cfg.heading_deg)
        self.start_dropdown.value = cfg.start_area
        self.length_box.text, self.width_box.text = f"{cfg.length_mm:g}", f"{cfg.width_mm:g}"
        self.length_box.invalid = self.width_box.invalid = False

    @property
    def editing(self) -> bool:
        return any(b.focused for b in self.boxes)

    # --- events / drawing -----------------------------------------------------
    def handle(self, event) -> bool:
        """Returns True when the panel consumed the event."""
        if self.start_dropdown.handle(event):
            for box in self.boxes:
                box.focused = False
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.dial.contains(event.pos):
            for box in self.boxes:
                box.focused = False
        if self.dial.handle(event):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            for box in self.boxes:
                box.handle(event)
            return any(b.handle(event) for b in self.buttons) or self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.editing:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.apply()
            elif event.key == pygame.K_TAB:
                focused = self.length_box.focused
                self.length_box.focused, self.width_box.focused = not focused, focused
            elif event.key == pygame.K_ESCAPE:
                for box in self.boxes:
                    box.focused = False
            else:
                for box in self.boxes:
                    box.handle(event)
            return True
        return False

    def draw(self, screen, fonts) -> None:
        font = fonts.body
        pygame.draw.rect(screen, UI_COLORS["panel"], self.rect)
        pygame.draw.line(screen, UI_COLORS["panel_edge"], self.rect.topleft, self.rect.bottomleft)
        left = self.rect.x + PAD
        screen.blit(fonts.title.render("Robot", True, UI_COLORS["text"]), (left, 12))
        labels = (
            (self.start_label_y, "Start position"),
            (self.headings_label_y, "Orientation · 5° steps"),
            (self.length_label_y, "Length (mm, along heading)"),
            (self.width_label_y, "Width (mm)"),
        )
        for y, text in labels:
            screen.blit(fonts.small.render(text.upper(), True, UI_COLORS["muted"]), (left, y + 2))
        for widget in [self.start_dropdown, self.dial] + self.buttons + self.boxes:
            widget.draw(screen, font)

        start = dict(START_OPTIONS).get(self.cfg.start_area, self.cfg.start_area)
        current = [f"Current: {start}",
                   f"{self.cfg.length_mm:g} x {self.cfg.width_mm:g} mm, {self.cfg.heading_deg:g}°"]
        for i, line in enumerate(current):
            screen.blit(font.render(line, True, UI_COLORS["text"]), (left, self.message_y + i * 18))
        if self.message:
            color = UI_COLORS["error"] if self.message_is_error else UI_COLORS["muted"]
            for i, line in enumerate(_wrap(self.message, font, PANEL_W - 2 * PAD)):
                screen.blit(font.render(line, True, color), (left, self.message_y + 46 + i * 18))
        self.start_dropdown.draw_list(screen, font)  # open list goes on top of everything


def _wrap(text, font, width):
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if font.size(candidate)[0] <= width:
            line = candidate
        else:
            lines.append(line)
            line = word
    return lines + [line] if line else lines
