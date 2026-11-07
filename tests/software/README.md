# Software component tests

Unit tests of the robot code run in the simulator (stand-in `novapi` / `mbuild`): see
[tests/README](../README.md#automated-tests-that-exist-simulation-and-tools). Pending on the robot: the NovaPi
sensor API names (`get_gyroscope`, `get_acceleration`, encoder angle) and a bundled one-file upload
([`bundle_for_mblock.py`](../../tools/scripts/README.md)).
