# test_mechanisms.py - moves every simulated mechanism of the v22 robot
#
# Ports (robot_config.json "mechanisms"; assumptions until the wiring is fixed):
#   DC1 intake rollers   DC2 intake head lift   DC3 elevator carriage
#   DC4 tower            DC5 basket feeder      BL1 shooter wheels
#
# Sequence: spin the intake rollers, raise the intake head, run the tower, feeder
# and shooter, raise the carriage to the top, then lower everything and stop.
#
# Simulator: viewer3d.py --program ../control/test_mechanisms.py --camera follow
import time
from mbuild import power_expand_board as pb


def run(port, power, seconds):
    pb.set_power(port, power)
    time.sleep(seconds)


print("mechanisms test")
pb.set_power("DC1", 80)                 # intake rollers on
time.sleep(1.0)
run("DC2", 100, 4.0)                    # intake head up ~210 mm (53 mm/s at 100 %)
pb.stop("DC2")
pb.set_power("DC4", 80)                 # tower
pb.set_power("DC5", 80)                 # feeder
pb.set_power("BL1", 100)                # shooter wheels
run("DC3", 100, 2.5)                    # carriage to the top (358 mm at 150 mm/s)
pb.stop("DC3")
time.sleep(1.5)
run("DC3", -100, 2.5)                   # carriage down
pb.stop("DC3")
run("DC2", -100, 4.5)                   # intake head down
for port in ("DC1", "DC2", "DC4", "DC5", "BL1"):
    pb.stop(port)
print("done")
