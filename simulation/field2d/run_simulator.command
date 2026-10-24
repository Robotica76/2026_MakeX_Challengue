#!/bin/bash
# Launch the MakeX Storm Breaker 2D simulator (macOS; also works on Linux).
#   double-click run_simulator.command      menu: viewer or a chassis demo
#   ./run_simulator.command [viewer args]   e.g. --program ../control/my_test.py --time-limit 60
# First run creates ../../.venv and installs pygame (needs python3 and internet).
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
    "$PY" -m pip install -r requirements.txt ||
        fail "Could not install pygame. Check the internet connection and run this again."
fi

if [ $# -gt 0 ]; then
    exec "$PY" viewer.py "$@"
fi

echo
echo "  MakeX Storm Breaker - 2D simulator"
echo "  1. Simulator (empty)"
echo "  2. Chassis demo - automatic  (Run starts it, about 44 s)"
echo "  3. Chassis demo - manual     (Open gamepad first, then Run)"
echo
read -r -p "Choose 1, 2 or 3: " choice
case "$choice" in
    2) "$PY" viewer.py --program ../control/test_chassis_control_automatico.py --time-limit 60 ;;
    3) "$PY" viewer.py --program ../control/test_chassis_control_manual.py --time-limit 100 ;;
    *) "$PY" viewer.py ;;
esac
status=$?
[ $status -ne 0 ] && read -r -p "The simulator exited with an error (see above). Press Return to close."
exit $status
