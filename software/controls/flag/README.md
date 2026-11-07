# Flag controls

`hang_flag()` in [`storm_breaker_2026.py`](../../robot/main/storm_breaker_2026.py) runs on N4 with the
robot in Red Start 1 after the Modification Stage: raises the head and the carriage, pushes the
fortress north slowly (R02: no tilt), places the rod over flagpole 2 (y 1010) and lowers.

**Mismatch to fix (KI-008):** the v22 mast is on the gripper carriage on the **right** side (rod front
end 86 mm). In the simulated field the red cone post keeps that rod ≥ 150 mm short of flagpole 2, so
the simulator (`robot_config.json` `team_flag` overrides) and this routine use a **proposed** rod on
the **left** side reaching the front edge (249 mm), approached facing the back wall with a 37 mm
window over the pin area. Either the CAD moves the mast / C head to the left front, or a new
approach that clears the cone post is needed. Hardware: [flag_system](../../../mechanical/flag_system/README.md)
(DEC-M12). Simulated success of the current routine: 55 / 80 matches.
