# Power

| Item | Value | Source |
| --- | --- | --- |
| Battery | LiPo 3S 11.1 V 4200 mAh, 25–30C, one per robot | Rules T11, T14 (T17-R1) |
| Battery mass | ~330 g (138 × 46 × 30 mm) | v22 CAD part 2.1 |
| Distribution | Power management / expansion board → DC1–DC8, BL1–BL2; NovaPi → M1–M4 | Kit |
| Mounting | Electronics box on the rear rails, battery strapped with Velcro | DEC-M10 |
| Power module visibility | Must be visible with the antenna away from metal | Rules Appendix 6 (T17-R7); **at risk** with the CF lid (KI-003) |

Load budget and peak current: to measure ([weight and power budget](../../docs/02_system_architecture/weight_power_budget.md)).
Starter registers: [power_distribution.md](power_distribution.md), [battery_power_management.md](battery_power_management.md).
