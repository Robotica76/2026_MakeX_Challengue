# Stateflow and Arbitration Specification

Proposed mode chain: `INIT → WAIT_START → AUTONOMOUS → MANUAL → MODIFICATION → FINAL → STOP`.
The rules guide V1.1 defines an automatic stage (30 s), a manual stage, a Modification Stage
(60 s, robot off the field) and a final stage (90 s; team flag) — check the current edition.

## As implemented (competition program `storm_breaker_2026.py`)

| Proposed mode | Implementation today | Trigger |
| --- | --- | --- |
| INIT | `constants()`, motor objects | Program start |
| WAIT_START | Busy-wait for N1 at the end of the file (`robot_2026.py`: `wait_for_start()`, where N2/N3/N4 choose the strategy first) | N1 |
| AUTONOMOUS | `automatic()` → `mission_N()` in `ORDER` (only if `STRATEGY > 0`) | N1 |
| MANUAL | `manual_loop()` | End of `automatic()` |
| MODIFICATION | Robot off the field; flag mast installed by hand ([flag_system](../../../mechanical/flag_system/README.md)) | Referee |
| FINAL | `hang_flag()` on N4 | Driver |
| STOP | Not explicit | Power off |

There is no separate arbitration module: one loop owns all actuators. Fault, loss of
communication and emergency stop are **not handled** yet.

## Transition contracts to complete

| Transition | Authoritative trigger | Guard | Test |
| --- | --- | --- | --- |
| WAIT_START → AUTONOMOUS | N1 / referee start | Robot stationary, gyro calibrated | Full-match rehearsal |
| AUTONOMOUS → MANUAL | 30 s | All actuators stopped (R19) | Same |
| MANUAL → MODIFICATION | Referee | — | — |
| FINAL → STOP | End of match | — | — |
