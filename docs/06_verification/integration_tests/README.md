# Integration Test Planning

| Test | Interfaces | Procedure | Criterion |
| --- | --- | --- | --- |
| IT-01 Ball path | Intake → tower → elbow → basket → launcher (IF-B1…B3) | 20 balls from the floor, shoot all | No jam; every ball fired |
| IT-02 Port map | NovaPi / power board ↔ every motor | Run [`test_mechanisms.py`](../../../simulation/control/test_mechanisms.py) on the robot | Each port moves the expected mechanism and direction |
| IT-03 Gripper + elevator + flag mast | Receptor, guide notch, camera clearance | Full stroke with the mast installed | No contact, mast top 1062 mm |
| IT-04 Odometry + mechanisms while driving | `on_cycle` jobs during moves | Automatic routine on the field | Timing within the simulated values |

Reports: [`tests/integration`](../../../tests/integration/README.md).
