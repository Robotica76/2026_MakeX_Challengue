# Wiring

No harness yet. Inputs for the first wiring diagram: the [motor allocation](../architecture/README.md) (ports),
the electronics box grommets (front wall: motors and sensors; left wall: launcher and ESCs; v22 part 2.6),
and cable mass budget 0.15 kg. Register: [wiring_diagrams.md](wiring_diagrams.md). After wiring, update the
port map in [`robot_config.json`](../../simulation/field2d/robot_config.json) and run the port check
([tests/electrical](../../tests/electrical/README.md)).
