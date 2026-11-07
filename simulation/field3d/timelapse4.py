"""Timelapse of a detailed 4-robot match (simulation/analysis/four_robots.py) in the 3D viewer,
rendered offscreen: one frame every --every simulated seconds, as an animated GIF, plus the match
report next to it (.txt).

    ../../.venv/bin/python timelapse4.py --red 13 --red-options '{"main": {"x_fire_at": 277.8}}' --out ganador.gif
"""

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (HERE, ROOT / "simulation" / "analysis", ROOT / "simulation" / "control", ROOT / "simulation" / "field2d"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

PROGRAM = ROOT / "software" / "robot" / "main" / "storm_breaker_2026.mblock"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--red", type=int, default=12)
    ap.add_argument("--blue", type=int, default=12)
    ap.add_argument("--red-options", default="{}", help="JSON, four_robots.play red_options")
    ap.add_argument("--blue-options", default="{}")
    ap.add_argument("--delay", type=int, default=0)
    ap.add_argument("--seconds", type=float, default=280.0)
    ap.add_argument("--seed", type=int, help="sampled robots and props (mc_four.py); default ideal robots")
    ap.add_argument("--every", type=float, default=1.0)
    ap.add_argument("--fps", type=int, default=14)
    ap.add_argument("--size", default="960x600")
    ap.add_argument("--camera", default="orbit")
    ap.add_argument("--out", type=Path, default=HERE / "timelapse4.gif")
    args = ap.parse_args()

    import four_robots
    import viewer3d
    from panda3d.core import Filename
    from PIL import Image
    from robot_model import RobotModel, load_model_spec
    vargs = viewer3d.parse_args(["--program", str(PROGRAM), "--time-limit", "280", "--size", args.size,
                                 "--camera", args.camera, "--no-stream", "--screenshot", str(args.out.with_suffix(".png"))])
    viewer = viewer3d.Viewer3D(vargs)
    folder = Path(tempfile.mkdtemp())
    frames, state = [], {"next": 0.0, "models": None}

    def on_frame(robots):
        host = robots[0]
        if state["models"] is None:
            viewer.sim = host.sim
            viewer._x_state = None
            viewer.robot.root.set_color_scale(1.25, 0.85, 0.85, 1.0)
            models = [viewer.robot]
            for r in robots[1:]:
                m = RobotModel(load_model_spec(vargs.model))
                m.root.reparent_to(viewer.base.render)
                if r.alliance == "blue":
                    m.root.set_color_scale(0.55, 0.7, 1.35, 1.0)
                else:
                    m.root.set_color_scale(1.25, 0.85, 0.85, 1.0)
                models.append(m)
            state["models"] = models
        if host.sim.time < state["next"]:
            return
        state["next"] += args.every
        for r, m in zip(robots, state["models"]):
            sim = r.sim
            m.set_pose(sim.pose.x, sim.pose.y, sim.pose.theta)
            mech = sim.mechanisms
            m.set_carriage(mech.position("elevator"))
            m.set_intake_lift(mech.position("intake_lift"))
            m.set_gripper_jaw(mech.position("gripper_jaw"))
            m.show_mast(bool(sim.flag and sim.flag.state != "stowed"))
        viewer._sync_balls()
        viewer._sync_props()
        viewer._sync_fortresses()
        viewer._sync_x_mark()
        viewer._apply_camera()
        viewer._refresh_hud()
        red, blue = (four_robots.alliance_score(robots, a) for a in ("red", "blue"))
        viewer.score_total.setText(f"RED {red['total']}  BLUE {blue['total']}")
        viewer.score_detail.setText(
            f"red: balls {red['precision']}  cones {red['cones']}  letters {red['letter_cubes']}  flags {red['flag']}  X {red['x_mark']}\n"
            f"blue: balls {blue['precision']}  cones {blue['cones']}  letters {blue['letter_cubes']}  flags {blue['flag']}  X {blue['x_mark']}")
        path = folder / f"f{len(frames):04d}.png"
        viewer.base.graphics_engine.render_frame()
        viewer.base.graphics_engine.render_frame()
        viewer.base.win.save_screenshot(Filename.from_os_specific(str(path)))
        frames.append(path)

    out = four_robots.play(args.red, args.blue, args.delay, seconds=args.seconds, seed=args.seed, red_options=json.loads(args.red_options),
                           blue_options=json.loads(args.blue_options), on_frame=on_frame)
    text = four_robots.report(out)
    print(text)
    images = [Image.open(p).convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT) for p in frames]
    images[0].save(args.out, save_all=True, append_images=images[1:], duration=int(1000 / args.fps), loop=0, optimize=True)
    args.out.with_suffix(".txt").write_text(text + "\n")
    for p in frames:
        p.unlink()
    folder.rmdir()
    print(f"timelapse: {args.out} ({len(images)} frames, {args.out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
