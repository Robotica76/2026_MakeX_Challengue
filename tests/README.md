# Testing and verification

## Verification hierarchy

```text
Component Test → Subsystem Test → Subsystem Integration Test → Robot Integration Test → Competition Mission Test → Full Match Black-Box Test
```

| Directory | Scope | Plan |
| --- | --- | --- |
| [mechanical](mechanical/README.md) | Parts and mechanisms | per subsystem `prototypes/` in [mechanical](../mechanical/README.md) |
| [electrical](electrical/README.md) | Wiring, power, sensors | [electrical](../electrical/README.md) |
| [software](software/README.md) | Units and contracts | automated tests in `simulation/` (below) |
| [subsystem](subsystem/README.md) | Complete subsystems | [subsystem tests](../docs/06_verification/subsystem_tests/README.md) |
| [integration](integration/README.md) | Hand-offs, robot integration, missions | [integration tests](../docs/06_verification/integration_tests/README.md) |
| [full_match](full_match/README.md) | Full match | [competition tests](../docs/06_verification/competition_tests/README.md) |

**Physical tests executed: none** (robot not built). Proposed campaign, in order:
[verification README](../docs/06_verification/README.md#proposed-test-campaign-from-the-cad-and-simulation-predictions).

## Automated tests that exist (simulation and tools)

| Suite | Command (from the repository root) | Checks |
| --- | --- | --- |
| 2D simulator | `cd simulation/field2d && ../../.venv/bin/python -m unittest` | Field layout, kinematics, runtime, gamepad, balls, props, fortress, match clock, referee, mechanisms, mBlock translation, chassis programs |
| 3D simulator | `cd simulation/field3d && ../../.venv/bin/python -m unittest` | 22 tests: CAD groups, footprint, field details, state stream, offscreen render |
| Analysis | `.venv/bin/python -m unittest discover simulation/analysis` | Monte Carlo statistics, strategy game, reach studies, two / four robots |
| Control demos | `simulation/control/test_*.py` (loaded in the simulator) | Chassis, mechanisms, intake, shelf, ball collection |

Use the [test report template](test_report_template.md); never mark an unperformed test as passed.
