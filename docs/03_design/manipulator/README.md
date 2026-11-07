# Manipulator and Gripper Trade Study

Elements under study: **Pins, Cones, Letter Cubes, Bonus Cubes** (rules p.27–43). Current
hardware (v22): one **lead-screw jaw gripper** on a belt elevator (358 mm stroke) on the right
side, plus the intake head used as a "puller" for props ([mechanical/gripper](../../../mechanical/gripper/README.md),
[gripper_elevation](../../../mechanical/gripper_elevation/README.md)).

## Element coverage today (simulation)

| Element | How the v22 robot handles it | Simulated result | Evidence |
| --- | --- | --- | --- |
| Bonus cube (X12) | Intake head pulls it off the strategy area, gripper places it in exchange area 1 | P(valid) 0.96 with a start jig | [Monte Carlo strategy](../../07_strategy/montecarlo_strategy.md) |
| Cones | Gripper lifts and lowers onto the cone post from above | +40 (both lower cones), needs 430 mm travel (KI-009) | [manual strategy](../../07_strategy/manual_strategy.md) |
| Letter cubes | Intake head (pull mode) pulls K and E off the fortress cube level | +60 | [scoring strategy](../../07_strategy/scoring_strategy.md) |
| Pins | Not reachable (pins stand at 760–1050 mm) | 0 | [pin_reach.py](../../../simulation/analysis/pin_reach.py) |

## Trade study (universal vs dedicated)

| Criterion | Universal (current jaw) | Dedicated tools | Evidence needed |
| --- | --- | --- | --- |
| Coverage | Cubes, cones; no pins | A pin tool would add a motor (none left) | Pin value vs motor reserve |
| Repeatability | V pads, single jaw | — | Grip tests per element |
| Mass / envelope | Inside 500 mm (jaw tip at x = 250, KI-001) | More mass | Weighing |

Decision so far: keep the single jaw; pins are not pursued (no motor available, KI-002).
