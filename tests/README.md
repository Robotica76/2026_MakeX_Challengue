# Testing and verification

## Verification hierarchy

```text
Component Test
    ↓
Subsystem Test
    ↓
Subsystem Integration Test
    ↓
Robot Integration Test
    ↓
Competition Mission Test
    ↓
Full Match Black-Box Test
```

Start with component evidence and progress through reviewed integration gates.
Full-match testing checks observable inputs and outcomes rather than assuming
internal behavior is correct.

| Directory | Test scope |
| --- | --- |
| [mechanical](mechanical/README.md) | Mechanical components and mechanisms |
| [electrical](electrical/README.md) | Electrical components and circuits |
| [software](software/README.md) | Software units and contracts |
| [subsystem](subsystem/README.md) | Isolated complete subsystems |
| [integration](integration/README.md) | Subsystem interfaces, robot integration, and competition missions |
| [full_match](full_match/README.md) | Full Match Black-Box Test |

Use the [test report template](test_report_template.md). Link each test to a
requirement, issue, tested configuration, and evidence. Define expected results,
measurements with units, and pass/fail criteria before execution; record failures
and corrective actions rather than deleting unsuccessful results.

Verification planning lives in
[docs/06_verification](../docs/06_verification/README.md). Reference test reports
from the [engineering notebook](../docs/08_engineering_notebook/README.md) without
duplicating evidence. This scaffold has no implemented tests or selected test
framework; future executable tests and their documented commands belong here.
