#!/bin/bash
# Launch the MakeX Storm Breaker 3D simulator (macOS; also works on Linux).
#   double-click run_simulator_3d.command      menu: viewer or a chassis demo
#   ./run_simulator_3d.command [viewer3d args] e.g. --program ../control/my_test.py --camera follow
# First run creates ../../.venv (shared with the 2D simulator) and installs
# panda3d, trimesh and pygame (needs python3 and internet).
cd "$(dirname "$0")" || exit 1

VENV="../../.venv"
PY="$VENV/bin/python"

fail() {
    echo
    echo "$1"
    read -r -p "Press Return to close."
    exit 1
}

if [ ! -x "$PY" ]; then
    command -v python3 >/dev/null 2>&1 ||
        fail "python3 was not found. Install it from https://www.python.org/downloads/ and run this again."
    echo "Creating the Python environment in .venv ..."
    python3 -m venv "$VENV" || fail "Could not create $VENV."
fi

if ! "$PY" -c "import pygame" >/dev/null 2>&1; then
    echo "Installing pygame ..."
    "$PY" -m pip install -r ../field2d/requirements.txt ||
        fail "Could not install pygame. Check the internet connection and run this again."
fi
if ! "$PY" -c "import panda3d, trimesh" >/dev/null 2>&1; then
    echo "Installing panda3d and trimesh ..."
    "$PY" -m pip install -r requirements.txt ||
        fail "Could not install the 3D simulator packages. Check the internet connection and run this again."
fi

if [ $# -gt 0 ]; then
    exec "$PY" viewer3d.py "$@"
fi

echo
echo "  MakeX Storm Breaker - 3D simulator"
echo "  1. Simulator (empty)"
echo "  2. Chassis demo - automatic  (Space starts it, about 44 s)"
echo "  3. Chassis demo - manual     (J opens the gamepad, then Space)"
echo "  4. Ball collection demo      (Space starts it, about 19 s)"
echo "  5. Mechanisms demo           (Space starts it: intake head, rollers, carriage)"
echo "  6. Intake shelf demo         (Space starts it: central resource upper level)"
echo "  7. Full ball system demo     (Space: collect, tower, basket, shoot into the blue fortress)"
echo "  8. Automatic stage routine   (Space: 30 s, central balls then cubes, match clock)"
echo
read -r -p "Choose 1-8: " choice
case "$choice" in
    2) "$PY" viewer3d.py --program ../control/test_chassis_control_automatico.py --time-limit 60 ;;
    3) "$PY" viewer3d.py --program ../control/test_chassis_control_manual.py --time-limit 100 --camera follow ;;
    4) "$PY" viewer3d.py --program ../control/test_ball_collection.py --balls released --time-limit 100 ;;
    5) "$PY" viewer3d.py --program ../control/test_mechanisms.py --camera follow ;;
    6) "$PY" viewer3d.py --program ../control/test_intake_shelf.py --camera follow --time-limit 60 ;;
    7) "$PY" viewer3d.py --program ../control/test_full_intake.py --balls released --time-limit 100 --xray ;;
    8) "$PY" viewer3d.py --program ../../software/autonomous/task_execution/auto_central_then_cubes.py --time-limit 30 ;;
    *) "$PY" viewer3d.py ;;
esac
status=$?
[ $status -ne 0 ] && read -r -p "The simulator exited with an error (see above). Press Return to close."
exit $status
