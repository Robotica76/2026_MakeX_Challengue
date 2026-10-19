"""Shared look for the viewer: a soft, low-contrast dark palette and fonts."""

import pygame

# Desaturated slate background with muted alliance tints; accents are pastel so the
# field reads calmly while the robot (mint green) and warnings (coral) still stand out.
PALETTE = {
    # field
    "background": (27, 30, 36),
    "floor": (44, 48, 57),
    "red_half": (60, 47, 54),
    "blue_half": (43, 52, 66),
    "grid": (255, 255, 255, 14),
    "frame": (120, 128, 142),
    "obstacle": (86, 93, 107),
    "obstacle_edge": (110, 118, 134),
    "movable": (150, 128, 98),
    "movable_edge": (176, 154, 122),
    "overhead": (170, 178, 194, 38),
    "overhead_edge": (150, 158, 174),
    "no_touch": (232, 200, 120),
    "slot": (70, 76, 89),
    "prop_cone": (238, 203, 106),
    "prop_cube": (226, 228, 234),
    "zone_red": (226, 128, 128),
    "zone_blue": (124, 166, 222),
    "robot": (118, 214, 160),
    "robot_body": (52, 92, 76, 230),
    "wheel": (30, 33, 38),
    "roller": (150, 156, 166),
    # text
    "text": (226, 229, 235),
    "muted": (150, 157, 170),
    "label": (200, 205, 214),
    "label_dark": (52, 56, 64),
    "warning": (240, 150, 128),
    # panel and widgets
    "panel": (34, 37, 44),
    "panel_edge": (48, 52, 61),
    "button": (52, 57, 67),
    "button_hover": (64, 70, 82),
    "button_selected": (86, 160, 124),
    "button_primary": (92, 132, 214),
    "border": (78, 84, 97),
    "focus": (124, 166, 222),
    "error": (240, 150, 128),
    "box": (27, 30, 36),
    "dial_face": (40, 44, 52),
    "dial_tick": (70, 76, 89),
    "dial_tick_major": (120, 128, 142),
    "dial_pending": (118, 214, 160),
    "dial_applied": (120, 128, 142),
}

RADIUS = 6  # corner radius for panels, buttons and boxes
_FONT_NAMES = "avenirnext,helveticaneue,segoeui,dejavusans,arial"
_MONO_NAMES = "menlo,sfmono,consolas,dejavusansmono,couriernew"


class Fonts:
    def __init__(self):
        self.body = pygame.font.SysFont(_FONT_NAMES, 14)
        self.small = pygame.font.SysFont(_FONT_NAMES, 12)
        self.label = pygame.font.SysFont(_FONT_NAMES, 12, bold=True)
        self.title = pygame.font.SysFont(_FONT_NAMES, 20, bold=True)
        self.mono = pygame.font.SysFont(_MONO_NAMES, 12)
