# Vision Architecture Study

Hardware: Makeblock **AI camera 2.0** on the gripper-elevator lid (v22 part 5.7). Planned use:
locate the bonus cube for **Bonus Battle** (rules p.28) and correct the X12 grab, and aim at the
fortress where it actually is ([DEC-S06](../../08_engineering_notebook/design_log/DL-SYS-001_design_decisions.md)).

| Observation | Approach | Output / frame | Consumer | Status |
| --- | --- | --- | --- | --- |
| Bonus cube identity / position | AI camera colour / tag recognition; prop-card statistics in [`vision_reference`](../../../software/vision/README.md) | Bearing + distance, robot frame | Automatic X12 grab | Not coded |
| Fortress position | Same | Bearing | R2 aim assist | Not coded |

The simulator does not model the camera. Evaluation plan: lighting / occlusion cases on a field
mock-up, error in mm and degrees, invalid-data response = fall back to odometry.
