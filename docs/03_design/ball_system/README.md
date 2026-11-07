# Ball System Design Study

Acquisition, storage and transfer of balls for **Precision Throwing** (rules guide V1.1, p.32–36).
Selected concept (CAD v22): intake → 3-wide tower → elbow → basket → feed roller → launcher.
Hardware lives in [mechanical](../../../mechanical/README.md); this page records the concept and
its evidence. Status: CAD and 2D single-ball simulation only.

## Selected concept and decisions

| Stage | Hardware (v22 part numbers) | Decision | Evidence |
| --- | --- | --- | --- |
| Acquisition | Intake rollers R3 (wide), R2 (straight), lower roller LR, UR head on a lift (4.x) | [DEC-M08](../../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | Floor / both shelf levels reach the tower top in 1.0–1.4 s ([sim](../../../mechanical/ball_intake/prototypes/README.md)) |
| Storage 1 | Tower 3 balls wide, 15°, top z 430, ~15 balls (3.x) | [DEC-M03](../../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | Roof clearance checked in CAD |
| Transfer | Elbow roller + concentric cover (3.6, 3.5) | [DEC-M04](../../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | Works 0.42–1.26 m/s |
| Storage 2 | Basket in front of the tower, floor sloped 10 % to the launcher, 6–8 balls (8.x) | [DEC-M05](../../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | — |
| Feed / gate | Feed roller TPU D30, DC-25 3:1 under the floor (8.2, 8.4) | [DEC-M05, DEC-M06](../../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md) | Holds when stopped, fires at 0.94 m/s |

## Transfer contracts

| Interface | Sender → receiver | Agreement | Jam / loss response | Test |
| --- | --- | --- | --- | --- |
| IF-B1 | Intake → tower | Ramp edge flush with the tower lower window; 3 lanes | Reverse intake + tower | [ball_intake prototypes](../../../mechanical/ball_intake/prototypes/README.md) |
| IF-B2 | Tower → basket | Elbow drops one ball at a time; S2 sensor counts entries | Stop tower when the basket is full (software TBD) | [feeder prototypes](../../../mechanical/feeder/prototypes/README.md) |
| IF-B3 | Basket → launcher | Feed roller runs only with the brushless at speed (software interlock) | Stop feed roller | [ball_storage prototypes](../../../mechanical/ball_storage/prototypes/README.md) |

Software: intake / tower / feeder ports `DC1`, `DC2`, `DC7`, `DC4`, `DC5` in
[`robot_config.json`](../../../simulation/field2d/robot_config.json) (assumptions until wired) and
[ball system controls](../../../software/controls/ball_system/README.md).

## Open questions

- Multi-ball behaviour (two balls entering the launcher together) is not simulated.
- Basket-full detection: no sensor in the basket; S2 counts tower entries only.

Coordinate with the [shooter design](../shooter/README.md); record prototypes in the [notebook](../../08_engineering_notebook/README.md).
