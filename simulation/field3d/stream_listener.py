"""Minimal receiver for the 3D viewer's state stream (state_stream.py).

    python stream_listener.py              # listens on 127.0.0.1:5005
    python stream_listener.py 0.0.0.0:5005 # from another computer

Prints one line per message. Use it as the starting point for a bridge: an Unreal
Engine UDP receiver or a ROS 2 node would parse the same JSON and publish, e.g.,
the pose as a transform and the wheel angles as joint states.
"""

import json
import socket
import sys

from state_stream import DEFAULT_TARGET, parse_target


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    host, port = parse_target(argv[0]) if argv else DEFAULT_TARGET
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"listening on {host}:{port} (Ctrl+C to stop)")
    try:
        while True:
            data, _ = sock.recvfrom(65536)
            msg = json.loads(data)
            p = msg["pose"]
            print(f"t={msg['t']:7.2f} s  {msg['status']:<13} x={p['x_mm']:7.1f}  y={p['y_mm']:7.1f} mm  "
                  f"theta={p['theta_deg']:7.1f} deg  carriage={msg['carriage_mm']:5.0f} mm")
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
