"""3D viewer checks: python -m unittest (this directory). Needs panda3d and trimesh;
the offscreen render test is skipped when no graphics context is available."""

import json
import math
import socket
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "field2d")]

import field_layout as fl  # noqa: E402
from field_model import field_parts, prop_base  # noqa: E402
from robot import RobotPose  # noqa: E402
from robot_model import RobotModel, classify, load_model_spec, load_parts, spinner_centres  # noqa: E402
from state_stream import SCHEMA_VERSION, StatePublisher, parse_target, state_message  # noqa: E402

# Parts that move 358 mm between the carriage-down and carriage-up v22 STEP files.
CARRIAGE_PARTS_V22 = {
    "CAR_belt_connector_kit", "CAR_linear_motion_slide_unit_kit_x2", "CAR_placa_carro_CF3",
    "FLAG_receptor_mastil_PETG", "GR_acople_motor", "GR_almohadilla_V_fija_TPU", "GR_almohadilla_V_movil_TPU",
    "GR_bloque_extremo_fijo_PETG", "GR_bloque_extremo_libre_PETG", "GR_bloque_montaje_PETG",
    "GR_carro_tuerca_PETG", "GR_guia_D8_tubo_Al", "GR_mordaza_fija_Al3", "GR_mordaza_movil_Al3",
    "GR_motor_DC25_pinza", "GR_sensor_distancia_kit", "GR_tabla_marco_CF3", "GR_tornillo_avance_T8x8"}

_PARTS = None


def parts():
    global _PARTS
    if _PARTS is None:
        _PARTS = load_parts(load_model_spec()["asset_path"])
    return _PARTS


class ModelSpecTest(unittest.TestCase):
    def setUp(self):
        self.spec = load_model_spec()
        self.groups = {p.name: classify(p.name, self.spec) for p in parts()}

    def test_asset_matches_cad_envelope(self):
        body = [p for p in parts() if not p.name.startswith("REF_")]
        lo = [min(p.vertices[:, i].min() for p in body) for i in range(3)]
        hi = [max(p.vertices[:, i].max() for p in body) for i in range(3)]
        self.assertAlmostEqual((hi[0] - lo[0]) * 1000, 499.5, delta=1.0)   # v22 footprint
        self.assertAlmostEqual((hi[1] - lo[1]) * 1000, 499.0, delta=1.0)
        self.assertAlmostEqual(lo[2] * 1000, 0.0, delta=1.0)               # standing on the floor

    def test_every_wheel_has_tyre_rollers_and_hub(self):
        for wheel in self.spec["wheels"]:
            names = [n for n, g in self.groups.items() if g["wheel"] == wheel]
            self.assertTrue(any(n.endswith("_llanta") for n in names), (wheel, names))
            self.assertTrue(any(n.endswith("_rodillos") for n in names), (wheel, names))
            self.assertTrue(any("hub" in n for n in names), (wheel, names))

    def test_wheel_centres_match_mesh(self):
        for wheel, info in self.spec["wheels"].items():
            tyre = next(p for p in parts() if self.groups[p.name]["wheel"] == wheel and p.name.endswith("_llanta"))
            centre = (tyre.vertices.min(0) + tyre.vertices.max(0)) / 2 * 1000
            for got, want in zip(centre, info["center_mm"]):
                self.assertAlmostEqual(got, want, delta=1.0, msg=wheel)

    def test_carriage_group_is_what_moves_in_the_cad(self):
        carriage = {n for n, g in self.groups.items() if g["carriage"] and not g["mast"]}
        self.assertEqual(carriage, CARRIAGE_PARTS_V22)
        mast = {n for n, g in self.groups.items() if g["mast"]}
        self.assertTrue({"FLAG_mastil_tubo_CF_8x6", "FLAG_cabeza_C_PETG"} <= mast)
        self.assertNotIn("FLAG_receptor_mastil_PETG", mast)   # the receptor stays on the robot

    def test_intake_lift_and_spinner_parts_exist(self):
        names = {p.name for p in parts()}
        lift = self.spec["intake_lift"]["parts"]
        self.assertTrue(set(lift) <= names, set(lift) - names)
        spun = [n for sp in self.spec["spinners"] for n in sp["parts"]]
        self.assertTrue(set(spun) <= names, set(spun) - names)
        self.assertEqual(len(spun), len(set(spun)))                 # no part in two spinners
        rails = [n for n in names if n.startswith("INT_UR_riel")]
        self.assertTrue(rails and not set(rails) & set(lift))        # the rails stay put

    def test_spinner_centres_lie_on_the_roller_axes(self):
        centres = {k: [c * 1000 for c in v] for k, v in spinner_centres(parts(), self.spec).items()}
        for name, (y, z) in {"intake_head_roller": (208, 95), "intake_lower_roller": (71, 22),
                             "intake_star_roller": (19, 150), "tower_elbow_roller": (-59, 443)}.items():
            self.assertAlmostEqual(centres[name][1], y, delta=1.5, msg=name)
            self.assertAlmostEqual(centres[name][2], z, delta=1.5, msg=name)

    def test_reference_balls_are_hidden(self):
        balls = [n for n, g in self.groups.items() if n.startswith("REF_pelota")]
        self.assertTrue(balls)
        self.assertTrue(all(self.groups[n]["hidden"] for n in balls))


class RobotNodeTest(unittest.TestCase):
    def setUp(self):
        self.robot = RobotModel(parts=parts())

    def test_carriage_starts_down_and_clamps(self):
        self.assertAlmostEqual(self.robot.carriage.get_z(), -0.358, places=6)
        self.robot.set_carriage(500)
        self.assertEqual(self.robot.carriage_mm, 358.0)
        self.assertAlmostEqual(self.robot.carriage.get_z(), 0.0, places=6)
        self.robot.set_carriage(-10)
        self.assertEqual(self.robot.carriage_mm, 0.0)

    def test_pose_points_cad_forward_along_heading(self):
        from panda3d.core import Point3
        for theta in (0.0, math.pi / 2, 2.0):
            self.robot.set_pose(1000, 500, theta)
            p = self.robot.root.get_parent().get_relative_point(self.robot.root, Point3(0, 1, 0))
            self.assertAlmostEqual(p.x, 1.0 + math.cos(theta), places=5)
            self.assertAlmostEqual(p.y, 0.5 + math.sin(theta), places=5)

    def test_wheel_pivots_at_axles_and_spin(self):
        info = self.robot.spec["wheels"]["front_left"]
        pivot = self.robot.wheels["front_left"]
        for got, want in zip(pivot.get_pos(), info["center_mm"]):
            self.assertAlmostEqual(got * 1000, want, places=3)
        self.robot.set_wheel_angles({"front_left": 90})
        self.assertAlmostEqual(pivot.get_p(), 90)

    def test_intake_lift_carries_its_roller(self):
        pivot = self.robot.spinners["intake_head_roller"]
        z0 = pivot.get_pos(self.robot.root).z
        self.robot.set_intake_lift(150)
        self.assertAlmostEqual(pivot.get_pos(self.robot.root).z - z0, 0.150, places=5)
        lower = self.robot.spinners["intake_lower_roller"]
        self.assertAlmostEqual(lower.get_pos(self.robot.root).z, 0.022, delta=0.002)   # not on the lift

    def test_spinner_angles_follow_mechanism_and_ratio(self):
        self.robot.set_spinner_angles({"intake_rollers": 30.0, "feeder": 10.0})
        self.assertAlmostEqual(self.robot.spinners["intake_star_roller"].get_p(), -90.0, places=4)   # ratio -3, axis x
        self.assertAlmostEqual(self.robot.spinners["feeder_roller"].get_r(), 30.0, places=4)        # ratio 3, axis y
        self.assertAlmostEqual(self.robot.spinners["shooter_wheels"].get_r(), 0.0, places=4)

    def test_mast_hidden_by_default(self):
        self.assertFalse(self.robot.mast_visible)
        self.assertTrue(self.robot.mast.is_hidden())


class MechanismViewerTest(unittest.TestCase):
    def test_mechanism_demo_moves_the_cad_parts(self):
        import viewer3d
        args = viewer3d.parse_args(["--screenshot", "unused.png", "--no-stream", "--size", "320x200",
                                    "--program", str(HERE.parent / "control" / "test_mechanisms.py")])
        try:
            viewer = viewer3d.Viewer3D(args)
        except Exception as exc:  # no OpenGL context (e.g. headless CI)
            self.skipTest(f"no offscreen graphics: {exc}")
        viewer.run_headless(7.5)            # intake head up, carriage at the top
        self.assertAlmostEqual(viewer.robot.carriage.get_z(), 0.0, places=3)          # 358 mm = asset height
        self.assertGreater(viewer.robot.intake_lift.get_z(), 0.2)
        self.assertNotEqual(viewer.robot.spinners["shooter_wheels"].get_r(), 0.0)
        viewer.sim.stop()
        viewer.base.destroy()


class FieldTest(unittest.TestCase):
    def test_every_element_is_built_with_its_height(self):
        elements = fl.build_field()
        parts = field_parts(elements)
        names = {p.name for p in parts}
        for el in elements:
            self.assertIn(el.name, names)
            group = [p for p in parts if p.name == el.name or p.name.startswith(el.name + ":")]
            top = max(p.vertices[:, 2].max() for p in group) * 1000
            want = el.z if el.z > 0 and el.kind not in ("zone", "slot") else 2.0
            if el.kind == "prop":        # standing on the strategy area top (259 mm)
                want = prop_base(el, elements) + el.z
            self.assertAlmostEqual(top, want, delta=0.01, msg=el.name)

    def test_rules_details_are_present(self):
        parts = field_parts(fl.build_field())
        names = [p.name for p in parts]
        self.assertEqual(sum("_resource_" in n and "_pin_" in n for n in names), 16)              # p.24: 16 pins
        self.assertEqual(sum(n.startswith("detail_red_resource") and "_ball_" in n for n in names), 20)  # p.26
        self.assertEqual(sum(n.startswith("detail_central_ball_") for n in names), 30)          # 15 per level
        self.assertEqual(sum(n.startswith("detail_") and "_cube_" in n and ":" not in n for n in names), 16)  # p.23
        shelf = next(p for p in parts if p.name == "red_resource_1:shelf_1")
        self.assertAlmostEqual(shelf.vertices[:, 2].max() * 1000, 758.5, places=3)         # p.13 Fig 4.2-6
        pin = next(p for p in parts if p.name.startswith("detail_red_resource_1_pin"))
        self.assertAlmostEqual((pin.vertices[:, 2].max() - pin.vertices[:, 2].min()) * 1000, 290, places=3)  # p.24

    def test_floor_covers_the_field(self):
        floor = next(p for p in field_parts([]) if p.name == "floor")
        size = (floor.vertices.max(0) - floor.vertices.min(0)) * 1000
        self.assertAlmostEqual(size[0], fl.FIELD_W, places=3)
        self.assertAlmostEqual(size[1], fl.FIELD_H, places=3)


class StreamTest(unittest.TestCase):
    def test_message_round_trip_and_rate(self):
        rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(rx.close)
        rx.bind(("127.0.0.1", 0))
        rx.settimeout(2)
        pub = StatePublisher(rx.getsockname(), rate_hz=10)
        self.addCleanup(pub.close)
        msg = state_message("storm_breaker_v22", 1.25, "running", RobotPose(1000.0, 500.0, math.pi / 2),
                            (100.0, -20.0, 0.5), {"front_left": (60.0, 90.0)}, 120.0, True)
        self.assertTrue(pub.maybe_send(0.0, msg))
        self.assertFalse(pub.maybe_send(0.05, msg))   # faster than 10 Hz: dropped
        data = json.loads(rx.recv(65536))
        self.assertEqual(data["v"], SCHEMA_VERSION)
        self.assertEqual(data["pose"], {"x_mm": 1000.0, "y_mm": 500.0, "theta_deg": 90.0})
        self.assertAlmostEqual(data["velocity"]["omega_deg_s"], math.degrees(0.5), places=2)
        self.assertEqual(data["wheels"]["front_left"], {"rpm": 60.0, "angle_deg": 90.0})
        self.assertTrue(data["mast"])

    def test_parse_target(self):
        self.assertEqual(parse_target("192.168.0.10:7000"), ("192.168.0.10", 7000))
        with self.assertRaises(ValueError):
            parse_target("localhost")


class ViewerRenderTest(unittest.TestCase):
    def test_offscreen_screenshot_after_running_the_demo(self):
        import viewer3d
        with TemporaryDirectory() as tmp:
            shot = Path(tmp) / "shot.png"
            args = viewer3d.parse_args(["--screenshot", str(shot), "--no-stream", "--size", "320x200",
                                        "--program", str(HERE.parent / "control" / "test_chassis_control_automatico.py"),
                                        "--run-for", "3"])
            try:
                viewer = viewer3d.Viewer3D(args)
            except Exception as exc:  # no OpenGL context (e.g. headless CI)
                self.skipTest(f"no offscreen graphics: {exc}")
            viewer.run_headless(args.run_for)
            moved = math.hypot(viewer.sim.pose.x - viewer.sim.start_pose.x, viewer.sim.pose.y - viewer.sim.start_pose.y)
            self.assertGreater(moved, 100)            # the demo drove the robot
            self.assertAlmostEqual(viewer.robot.root.get_x() * 1000, viewer.sim.pose.x, delta=0.01)
            viewer.screenshot(shot)
            self.assertGreater(shot.stat().st_size, 1000)
            viewer.sim.stop()
            viewer.base.destroy()


if __name__ == "__main__":
    unittest.main()
