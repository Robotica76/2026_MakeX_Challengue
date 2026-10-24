"""Emulated gamepad checks (headless): python -m unittest (this directory)."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

import gamepad as gp  # noqa: E402

PHYSICAL = {"L1", "L2", "R1", "R2", "up", "down", "left", "right", "menu", "bluetooth", "plus",
            "button_1", "button_2", "button_3", "button_4", "left_stick", "right_stick", "power"}


class GamepadTest(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.addCleanup(pygame.quit)
        self.events = []
        self.state = gp.GamepadState(self.events.append)
        self.controls = {c.name: c for c in gp.build_controls()}

    def test_every_physical_control_is_present(self):
        self.assertEqual(set(self.controls), PHYSICAL)

    def test_each_control_is_hit_at_its_centre_only(self):
        for name, c in self.controls.items():
            centre = gp.to_px(c.x, c.y)
            hits = [o.name for o in self.controls.values() if o.hit(centre)]
            self.assertEqual(hits, [name], f"{name} overlaps {hits}")

    def test_press_and_release_emit_events(self):
        self.state.press(self.controls["L1"])
        self.state.release()
        self.assertEqual(self.events, [{"event": "press", "control": "L1"},
                                       {"event": "release", "control": "L1"}])

    def test_stick_drag_is_clamped_and_springs_back(self):
        stick = self.controls["left_stick"]
        self.state.press(stick)
        x, y = gp.to_px(stick.x, stick.y)
        self.state.drag(stick, (x + 500, y))  # far right, beyond the stick's reach
        self.assertEqual(self.state.axes["left_stick"], (1.0, 0.0))
        self.state.drag(stick, (x, y - 500))  # far up -> +y
        self.assertEqual(self.state.axes["left_stick"], (0.0, 1.0))
        self.state.release()
        self.assertEqual(self.state.axes["left_stick"], (0.0, 0.0))
        self.assertEqual(self.events[-1], {"event": "axis", "control": "left_stick", "x": 0.0, "y": 0.0})

    def test_power_off_blocks_input(self):
        self.state.press(self.controls["power"])
        self.assertFalse(self.state.on)
        self.state.press(self.controls["button_1"])
        self.assertIsNone(self.state.pressed)
        self.assertEqual(self.events, [{"event": "power", "control": "power", "on": False}])

    def test_window_renders(self):
        screen = pygame.display.set_mode(gp.WINDOW)
        controls = list(self.controls.values())
        gp.draw(screen, gp.Fonts(), gp.render_static(gp.WINDOW), controls, self.state, hover="R1")


if __name__ == "__main__":
    unittest.main()
