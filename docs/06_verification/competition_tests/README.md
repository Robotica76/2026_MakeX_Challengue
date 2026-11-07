# Competition Test Planning

| Test | Scenario | Measure | Simulated reference |
| --- | --- | --- | --- |
| CT-01 Automatic stage | Red Start 1, start jig, `ORDER` 12 and 13, 10 runs each | X12 valid, X9 on our side, time, R19 | P(X12) 0.96; route Monte Carlo |
| CT-02 Manual cycles | Sweep resource area 1, shoot from (1600, 900) | Balls scored / shot | 18/30 |
| CT-03 Cones | Hang both lower cones on post 2 | Success rate | +40 |
| CT-04 Flag | Final stage, N4 | Hung / not | 55/80 matches |
| CT-05 Full match | 300 s with a partner robot | Score, penalties | 300–440 |

Use the rules guide edition in [resources/rules](../../../resources/rules/README.md); reports go to
[`tests/full_match`](../../../tests/full_match/README.md).
