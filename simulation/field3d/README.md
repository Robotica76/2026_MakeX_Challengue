# 3D simulator (Storm Breaker + robot v22)

3D view of the 2026 MakeX Challenge "Storm Breaker" field with the
[Storm Breaker v22](../../mechanical/assemblies/full_robot/v22/README.md) CAD model.
It runs the **same simulation as the [2D simulator](../field2d/README.md)**: mecanum
kinematics, encoders, gyroscope and accelerometer, mBlock Python programs
(`novapi` / `mbuild`), the emulated gamepad and `chassis.py`. Only the drawing is new,
so 2D and 3D give identical motion, and the Monte Carlo results apply to both.

![3D view](docs/run_orbit.png)

## Run

**Windows:** double-click `run_simulator_3d.bat`. **macOS:** double-click
`run_simulator_3d.command` (right-click > Open the first time if macOS blocks it).
The first run uses the same `.venv` as the 2D simulator and installs panda3d and
trimesh (and pygame if it is missing), then shows a menu: empty simulator,
automatic chassis demo or manual chassis demo.

**Manual setup:**

```bash
python3 -m venv .venv
.venv/bin/pip install -r simulation/field2d/requirements.txt -r simulation/field3d/requirements.txt
cd simulation/field3d
../../.venv/bin/python viewer3d.py
../../.venv/bin/python viewer3d.py --program ../control/test_chassis_control_automatico.py --camera follow
../../.venv/bin/python viewer3d.py --mast --carriage 358          # after the Modification Stage
../../.venv/bin/python viewer3d.py --screenshot shot.png --run-for 5 --program ...   # headless
../../.venv/bin/python -m unittest                                # checks
```

| Key / mouse | Action |
| --- | --- |
| `O` | Open an mBlock program (file picker in `simulation/control/`) |
| `Space` | Run / stop the program; `R` stops, a second `R` puts the robot back on its start pose |
| `J` | Open the emulated gamepad window (manual programs) |
| `1` `2` `3` `4` | Cameras: orbit (field), follow (behind the robot), top (orthographic), driver (red side) |
| Drag / right-drag / wheel | Rotate / pan / zoom |
| `E` / `Q` | Elevator carriage up / down (0–358 mm, visual) |
| `M` | Flag mast on/off (installed in the Modification Stage) |
| `L` | Field labels |
| `S` | Screenshot (`field3d_screenshot.png`) |
| `H` / `Esc` | Help on/off / quit |

Run limits are the same as in 2D: 30 s by default (`--time-limit`, 0 = none), the run
stops when a footprint corner leaves the field, on a program error, or on Stop.

## What moves

| Group | Parts (from `robot_model.json`) | Driven by |
| --- | --- | --- |
| Robot pose | Whole model | Simulated pose (`Simulation.pose`) |
| 4 mecanum wheels | Tyre, rollers, hub, coupling per corner | Encoder angle of each drive motor port |
| Elevator carriage | `CAR_`, `GR_`, `FLAG_receptor` (the 18 parts that move 358 mm between the two v22 STEP files) | `E`/`Q` keys or `--carriage` (the simulator has no elevator motor model yet) |
| Flag mast | `FLAG_mastil`, `FLAG_cabeza`, `FLAG_pasador`, `FLAG_ligas`, reference flag | `M` key or `--mast` |

The field comes from `simulation/field2d/field_layout.py` (footprints and heights,
with the sources and estimates recorded there): obstacles as solids up to their
height, overhead structures as slabs the robot can drive under, zones as floor
patches, the perimeter frame semi-transparent.

## Robot model pipeline

1. CAD: `mechanical/assemblies/full_robot/v22/cad/*.step.zip`.
2. Convert with [`tools/scripts/step_to_glb.py`](../../tools/scripts/step_to_glb.py)
   (Open CASCADE through `cascadio`, 0.5 mm tolerance) into
   [`assets/storm_breaker_v22.glb`](assets/storm_breaker_v22.glb): 235 named parts,
   246 k triangles, 8.7 MB, metres, CAD axes (+y forward, +x right, +z up).
3. [`robot_model.json`](robot_model.json) lists the wheel, carriage and mast parts.
   A new CAD revision needs a new GLB and, only if part names change, an edited JSON;
   `test_field3d.py` checks the groups against the CAD.

```bash
pip install -r tools/scripts/requirements-cad.txt
python tools/scripts/step_to_glb.py mechanical/assemblies/full_robot/v22/cad/Robot_StormBreaker_v22_con_mastil_y_bandera_carro_arriba.step.zip simulation/field3d/assets/storm_breaker_v22.glb
```

The 2D simulator uses the same drive geometry: `simulation/field2d/robot_config.json`
holds the v22 footprint (499.0 × 499.5 mm) and the measured wheel centres
(wheel rectangle 79 mm behind the footprint centre).

## State stream (Unreal Engine, ROS 2, other tools)

While running, the viewer sends the robot state as JSON over UDP to `127.0.0.1:5005`,
30 times per second (`--stream HOST:PORT`, `--stream-rate`, `--no-stream`). The schema
is documented in [`state_stream.py`](state_stream.py):

```json
{"v": 1, "robot": "storm_breaker_v22", "t": 12.34, "status": "running",
 "pose": {"x_mm": 1234.5, "y_mm": 567.8, "theta_deg": 90.0},
 "velocity": {"vx_mm_s": 0.0, "vy_mm_s": 0.0, "omega_deg_s": 0.0},
 "wheels": {"front_left": {"rpm": 0.0, "angle_deg": 0.0}, "...": {}},
 "carriage_mm": 0.0, "mast": false}
```

`python stream_listener.py` prints the messages and is the starting point for a bridge:

- **Unreal Engine:** import `assets/storm_breaker_v22.glb` (Unreal's glTF importer), receive
  the UDP JSON in a Blueprint or C++ actor, and set the actor transform from `pose`
  (heading `theta_deg - 90`, because the CAD forward axis is +y) and the wheel rotations
  from `wheels`.
- **ROS 2:** a small node that receives the same JSON and publishes `pose` as a TF / odometry
  message and `wheels` as `sensor_msgs/JointState`, so RViz can show it. ROS 2 runs best on
  Ubuntu; this simulator keeps running on Windows and macOS.

The stream is one-way (simulator → tools); nothing outside can drive the simulation yet.

## Checks

`python -m unittest` in this directory (14 tests): wheel, carriage and mast groups match
the CAD; the model stands on the floor with the 499.5 × 499.0 mm footprint; wheel pivots at
the measured axles; the CAD forward axis follows the simulated heading; every field element
is built at its height; stream messages round-trip and respect the rate; and an offscreen
render of the automatic demo (skipped when no graphics context is available).

## Limits

- Visual only: the 3D field has no collisions; the simulation still checks only the field
  boundary, as in 2D. Physics (contacts, tipping, the fortress) is not modelled.
- The elevator, intake, shooter and gripper motors are not simulated; the carriage height
  is set by hand.
- Field element placements carry the estimates noted in `field_layout.py`.
