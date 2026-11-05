"""Timelapse of a whole match in the 3D viewer, rendered offscreen: our robot with the scripted driver
(ai_driver.py, in this process) and, with --twin, its blue twin; one frame every --every simulated
seconds, put together as an animated GIF (PIL; no video encoder needed).

    ../../.venv/bin/python timelapse.py --twin 12 --out timelapse.gif
    ../../.venv/bin/python timelapse.py --every 0.5 --fps 20 --size 1280x800
"""

import argparse
import contextlib
import io
import os
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
    ap.add_argument("--program", type=Path, default=PROGRAM)
    ap.add_argument("--twin", type=int, help="blue twin running this ORDER (two_robots.py)")
    ap.add_argument("--seconds", type=float, default=280.0)
    ap.add_argument("--every", type=float, default=1.0, help="simulated seconds between frames")
    ap.add_argument("--fps", type=int, default=14, help="GIF frames per second")
    ap.add_argument("--size", default="960x600", help="frame size WxH")
    ap.add_argument("--camera", default="orbit")
    ap.add_argument("--out", type=Path, default=HERE / "timelapse.gif")
    args = ap.parse_args()

    import viewer3d
    from PIL import Image
    from two_robots import Robot
    from ai_driver import Driver
    vargs = viewer3d.parse_args(["--program", str(args.program), "--time-limit", str(args.seconds),
                                 "--size", args.size, "--camera", args.camera, "--no-stream",
                                 "--screenshot", str(args.out.with_suffix(".png"))]
                                + (["--twin", str(args.twin)] if args.twin is not None else []))
    viewer = viewer3d.Viewer3D(vargs)
    red = Robot.__new__(Robot)                  # our robot's driver on the viewer's simulation
    red.sim, red.alliance, red.delay, red.driver, red.queue = viewer.sim, "red", 0, Driver(), []
    frames, folder = [], Path(tempfile.mkdtemp())
    frame_s, k, next_shot, logged, twin_logged = 1 / 60, 0, 0.0, 0, 0
    with contextlib.redirect_stdout(io.StringIO()):
        viewer.sim.run()
    while viewer.sim.running and viewer.sim.time < args.seconds:
        with contextlib.redirect_stdout(io.StringIO()):
            viewer.sim.step(frame_s)
            viewer._step_twin(frame_s)
            k += 1
            red.drive(k)
        for line in red.driver.log[logged:]:
            print(line, flush=True)
        logged = len(red.driver.log)
        if viewer.twin is not None:
            for line in viewer.twin.driver.log[twin_logged:]:
                print("[twin]" + line, flush=True)
            twin_logged = len(viewer.twin.driver.log)
        if viewer.sim.time >= next_shot:
            next_shot += args.every
            viewer._place_robot()
            viewer._place_twin()
            viewer._sync_balls()
            viewer._sync_props()
            viewer._sync_fortresses()
            viewer._sync_x_mark()
            viewer._update_trail()
            viewer._apply_camera()
            viewer._refresh_hud()
            path = folder / f"f{len(frames):04d}.png"
            viewer.base.graphics_engine.render_frame()
            viewer.base.graphics_engine.render_frame()
            from panda3d.core import Filename
            viewer.base.win.save_screenshot(Filename.from_os_specific(str(path)))
            frames.append(path)
    images = [Image.open(p).convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT) for p in frames]
    images[0].save(args.out, save_all=True, append_images=images[1:], duration=int(1000 / args.fps), loop=0,
                   optimize=True)
    for p in frames:
        p.unlink()
    folder.rmdir()
    viewer.sim.stop()
    print(f"timelapse: {args.out} ({len(images)} frames, {args.out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
