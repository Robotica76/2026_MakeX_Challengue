"""Sanity checks for the field layout: python -m unittest (from this directory)."""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import field_layout as fl
from robot import RobotConfig, load_config, mecanum_wheels, start_pose


class FieldLayoutTest(unittest.TestCase):
    def setUp(self):
        self.elements = fl.build_field()

    def test_names_unique(self):
        names = [e.name for e in self.elements]
        self.assertEqual(len(names), len(set(names)))

    def test_everything_inside_field(self):
        for el in self.elements:
            x0, y0, x1, y1 = el.bounds()
            with self.subTest(el.name):
                self.assertGreaterEqual(x0, 0)
                self.assertGreaterEqual(y0, 0)
                self.assertLessEqual(x1, fl.FIELD_W)
                self.assertLessEqual(y1, fl.FIELD_H)

    def test_red_blue_mirror(self):
        for el in self.elements:
            if el.alliance != "red":
                continue
            blue = fl.get(self.elements, el.name.replace("red_", "blue_", 1))
            self.assertAlmostEqual(blue.x, fl.FIELD_W - el.x)
            self.assertAlmostEqual(blue.y, el.y)

    def test_start_areas_clear_of_obstacles(self):
        starts = [e for e in self.elements if e.name.endswith(("start_1", "start_2"))]
        blocking = [e for e in self.elements if e.kind in ("obstacle", "movable")]
        for s in starts:
            for b in blocking:
                sx0, sy0, sx1, sy1 = s.bounds()
                bx0, by0, bx1, by1 = b.bounds()
                overlap = sx0 < bx1 and bx0 < sx1 and sy0 < by1 and by0 < sy1
                self.assertFalse(overlap, f"{s.name} overlaps {b.name}")

    def test_middle_strip_matches_rule_lengths(self):
        # Two strategy areas plus the central rack span the strip between the walls.
        strip = 2 * fl.STRATEGY_L + fl.CENTRAL_L
        self.assertLess(strip, fl.FIELD_H)

    def test_heights(self):
        self.assertEqual(fl.FLOOR_PROFILE, "flat")
        for el in self.elements:
            with self.subTest(el.name):
                if el.kind in ("obstacle", "movable", "overhead", "no_touch", "prop"):
                    self.assertGreater(el.z, 0)
                else:  # floor markings: start areas, exchange pads, channel slots
                    self.assertEqual(el.z, 0)

    def test_robot_fits_start_area(self):
        cfg = load_config()
        area = fl.get(self.elements, cfg.start_area)
        pose = start_pose(cfg, self.elements)
        for cx, cy in pose.corners(cfg):
            self.assertTrue(area.contains(cx, cy))

    def test_robot_size_limit(self):
        cfg = RobotConfig("x", "mecanum", 520, 450, 80, "red", "red_start_1", 0)
        with self.assertRaises(ValueError):
            cfg.validate()

    def test_resize_moves_wheels_to_corners(self):
        cfg = load_config().resized(480, 300)
        self.assertEqual((cfg.length_mm, cfg.width_mm), (480, 300))
        centers = {w.name: w.center for w in mecanum_wheels(cfg)}
        self.assertEqual(centers["front_left"], (240 - 40, 150 - 20))
        self.assertEqual(centers["rear_right"], (-(240 - 40), -(150 - 20)))
        with self.assertRaises(ValueError):
            cfg.resized(150, 300)  # shorter than two 80 mm wheels
        with self.assertRaises(ValueError):
            cfg.resized(480, 501)

    def test_mecanum_rollers_form_x(self):
        rollers = {w.name: w.roller_dir for w in mecanum_wheels(load_config())}
        self.assertEqual(rollers["front_left"], rollers["rear_right"])
        self.assertEqual(rollers["front_right"], rollers["rear_left"])
        fl_dir, fr_dir = rollers["front_left"], rollers["front_right"]
        self.assertAlmostEqual(fl_dir[0] * fr_dir[0] + fl_dir[1] * fr_dir[1], 0)  # perpendicular


def _click(pos):
    import pygame
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


class RobotPanelTest(unittest.TestCase):
    """Drives the side panel headless: edits stay pending until Apply."""

    def setUp(self):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        import pygame
        from panel import RobotPanel

        pygame.init()
        self.addCleanup(pygame.quit)
        self.applied = []
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "robot.json"
        self.path.write_text(Path(__file__).with_name("robot_config.json").read_text())
        self.panel = RobotPanel(0, 800, load_config(self.path), self.path,
                                lambda cfg: self.applied.append(cfg) or "")

    def test_apply_heading_and_size(self):
        dial = self.panel.dial
        dial.set_value(dial.angle_at((dial.center[0], dial.center[1] - 50)))  # straight up = 90 deg
        self.panel.length_box.text, self.panel.width_box.text = "400", "350"
        self.assertEqual(self.applied, [])  # nothing changes before Apply
        self.panel.apply()
        cfg = self.applied[-1]
        self.assertEqual((cfg.length_mm, cfg.width_mm, cfg.heading_deg), (400, 350, 90))

    def test_dial_snaps_to_5_degrees(self):
        dial = self.panel.dial
        self.assertEqual(dial.snap(93), 95)
        self.assertEqual(dial.snap(-2), 0)
        self.assertEqual(dial.snap(358), 0)
        # Point 30 deg below the +x axis on screen -> 330 deg (CCW convention).
        cx, cy = dial.center
        self.assertEqual(dial.angle_at((cx + 50, cy + 28.87)), 330)
        dial.set_value(123)
        self.assertEqual(self.panel.pending_heading, 125)
        self.assertEqual(self.applied, [])  # still pending until Apply

    def test_start_dropdown_moves_robot_on_apply(self):
        dd = self.panel.start_dropdown
        dd.handle(_click(dd.rect.center))  # open
        self.assertTrue(dd.open)
        option = dd._option_rect(3)  # Blue - Start 2
        dd.handle(_click(option.center))
        self.assertFalse(dd.open)
        self.assertEqual(self.panel.pending_start, "blue_start_2")
        self.assertEqual(self.applied, [])  # pending until Apply
        self.panel.apply()
        cfg = self.applied[-1]
        self.assertEqual((cfg.start_area, cfg.alliance), ("blue_start_2", "blue"))
        pose = start_pose(cfg, fl.build_field())
        area = fl.get(fl.build_field(), "blue_start_2")
        self.assertEqual((pose.x, pose.y), (area.x, area.y))

    def test_invalid_input_is_rejected(self):
        self.panel.length_box.text = ""
        self.panel.apply()
        self.assertTrue(self.panel.length_box.invalid)
        self.panel.length_box.text = "520"
        self.panel.apply()
        self.assertTrue(self.panel.message_is_error)
        self.assertEqual(self.applied, [])

    def test_save_and_reset(self):
        self.panel.length_box.text = "420"
        self.panel.apply()
        self.panel.save()
        self.assertEqual(load_config(self.path).length_mm, 420)
        self.panel.length_box.text = "300"
        self.panel.reset()
        self.assertEqual(self.panel.length_box.text, "420")


if __name__ == "__main__":
    unittest.main()
