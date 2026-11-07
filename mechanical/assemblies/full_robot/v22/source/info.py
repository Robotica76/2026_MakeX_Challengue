import json
O15, O18, O19, O21, O22 = "/home/claude/out15/", "/home/claude/out18/", "/home/claude/out19/", "/home/claude/out21/", "/home/claude/out22/"
NOREQ = "Rule references are to the MakeX Challenge 2026 Storm Breaker rules used for the CAD (see [resources](../../resources/rules/README.md)); confirm against the official, current version."
I = {}
I["chassis"] = dict(
 title="Chassis", cad_intro="Chassis, drive, and the electronics box (subsystems 1 and 2 of the v22 numbering). Full-robot CAD stays in [full_robot](../../assemblies/full_robot/README.md).",
 sims=[(O21 + "simulacion_inercia_vuelco_v21.png", "CG (measured in CAD) over the wheel polygon in 5 configurations and the acceleration that tips the robot in each direction"),
       (O21 + "simulacion_inercia_frenado_v21.png", "Forward pitch when braking at 0.35 g and 0.6 g, and the frontal impact speed that tips the robot"),
       (O21 + "simulacion_inercia_maniobra_v21.png", "Yaw time limited by friction and the fastest start / stop without tipping")],
 assembly="1. Rails (slide beam 496) and the three 2424 crossbars on printed shims (1.1, 1.2, 1.9, 1.10).\n2. Each wheel module: 180 smart-encoder motor, printed 40T gears, D8 axle on printed pillow block, hub, coupling, mecanum wheel, PETG guard. Front wheels at `y = +45`, rear at `y = −203`, `x = ±221.2`.\n3. Square the frame (diagonals equal) before mounting anything else.\n4. Electronics box (2.x): four 3 mm PETG shims on the rails, CF 2 mm floor bolted to **both** rails with 4 × M4; battery (2 Velcro straps), NovaPi, power module in the back row; drivers + Bluetooth on edge in the front row; CF 1 mm walls with PETG corner brackets. Fit the lid (4 × M3) only after wiring.",
 inspection=["Frame square: diagonals within 1 mm", "All four wheels touch the floor (no rocking) with the robot loaded", "Box floor bolted to both rails; box does not touch the gripper-elevator motor (x = 139) nor the tower belts (7 mm gap)", "Battery strapped and not movable by hand; cables through the front/left grommets", "Robot mass ≤ 10 kg with all parts and screws (CAD: 9.88 kg)"],
 tests=[["Static tip angle", "Tilt the robot forward until it tips (empty, gripper up + pin)", "≥ 26° / ≥ 22° (CAD CG)"], ["Braking", "Peak deceleration logged from the encoders when stopping from 1.5 m/s", "Software limit 0.35 g; no front-wheel lift"], ["Frontal impact", "Drive into a padded wall at increasing speed", "No tip below 0.85 m/s (CAD estimate, worst case)"], ["Mass and CG", "Scale per wheel", "Total ≤ 10 kg, CG y ≈ −43 mm, z ≈ 176–181 mm"]],
 readme={
 "Purpose": "Mobile base for the whole robot: four mecanum wheels, the rails that carry every other subsystem, and (since v21) a structural electronics box at the rear.",
 "Competition Capabilities": "Omnidirectional driving (strafing is used to place the flag and to align on the resource shelves). " + NOREQ,
 "Requirements": "- Footprint 500 × 500 mm and initial height ≤ 700 mm; mass ≤ 10 kg at any time (flag excluded).\n- Front wheels cannot pass `y = +45`: with the robot face against the Central Resource Area table (y = 93), the lower shelf occupies the space ahead of the wheels.\n- Electronics enclosed and protected; battery LiPo 3S 11.1 V 4200 mAh as required by the rules.",
 "Mechanical Interfaces": "- Rails `x = ±175…199`, top at `z = 69`; three crossbars `y = −164…−18`, top at `z = 61` (tower plates and intake stand on them).\n- Electronics box `x −197…136`, `y −249…−178`, `z 72…112`, floor bolted to both rails (acts as an extra rear crossmember).\n- Track × wheelbase 442.5 × 248 mm; wheel centres `z = 40`.",
 "Electrical Interfaces": "4 × 180 smart encoder motors (4 of the 13 DC-motor slots). Box holds the battery (≈330 g), NovaPi with case, power/expansion module, drivers + Bluetooth; grommets on the front wall (motors, sensors) and left wall (launcher, ESCs). Cable mass is estimated at 0.15 kg, not modelled.",
 "Software Interfaces": "Mecanum kinematics; ramp limits from the stability study: braking ≤ 0.35 g, avoid frontal impacts above ≈ 0.85 m/s.",
 "Design": "Mass 9.88 kg (CAD, robot) with CG at `y ≈ −43`, `z ≈ 181` mm. Forward tip limit is the critical one: 0.49 g empty, 0.41 g with gripper up + pin + balls. Moving motors was studied and rejected (≈ +0.03 g for a large redesign); the limit comes from the front-wheel position.",
 "Current Status": "v22 CAD complete and clash-checked against the rest of the robot. Not built.",
 "Testing": "See [prototypes](prototypes/README.md): tip angle, braking, impact, mass/CG.",
 "Known Issues": "- Mass margin ≈ 0.12 kg, and ~80 screws are not modelled yet (≈ 80 g).\n- Electronics dimensions (NovaPi, power module) are approximations; the box back row is 328 mm of equipment in 330 mm.\n- 3 mm shims are needed because the rear motor M4 heads stand to `z = 72`."})
I["ball_intake"] = dict(
 title="Ball Intake", cad_intro="Floor and shelf intake, rollers, and the UR lift arm (subsystem 4).",
 sims=[(O19 + "simulacion_recoleccion_torre_v19.png", "2D single-ball simulation: floor, lower shelf (rows 2 and 3) and upper shelf (rows 2 and 3) all reach the top of the tower in 1.0–1.4 s"),
       (O15 + "simulacion_cono_v15.png", "Cone handling with the UR band at z = 468 (knocks the cone over); at z = 455 the cone stays leaning")],
 assembly="1. Side plates CF3 (4.8, 4.9) on the chassis spacers.\n2. Rollers: R2 straight centring roller (4.3, 4.7, 4.33), R3 wide entry roller ±108 mm (4.4, 4.22, 4.34), lower roller LR with its internal DC-25 (4.1, 4.17, 4.35).\n3. DC-37 (4.6) on its bracket and the 48T/16T gear train to R3 and R2.\n4. Wide ramp and floor sheets (4.20, 4.13), deflectors.\n5. UR arm: CF 20×20 rails (4.11, 4.12), printed sliders, T8 lead screw with the top DC-25 and GT2 belt 1:1, arms CF3, band nose with internal DC-25 (giro).",
 inspection=["R2 core turns freely inside the D34 clearance in the tower plates", "R3 and R2 gear mesh without binding by hand", "UR arm travels z 95 → 468 without contact; nut lowest at z 113", "Ramp edge flush with the tower entry (no step for the ball)", "Intake left plate cut above z 278 (launcher clearance)"],
 tests=[["Floor pick-up", "Balls per 10 attempts, time to tower top", "≥ 9/10, ≤ 1.4 s"], ["Lower / upper shelf", "Balls per 10 attempts per row", "≥ 8/10"], ["Cone", "Knock-over with band at z 468", "Cone falls in 0.6 s"], ["Jam recovery", "Reverse sequence clears a stuck ball", "Clears in < 1 s"]],
 readme={
 "Purpose": "Acquire balls from the floor and from both levels of the Central Resource Area and hand them to the 3-ball-wide tower; handle cones with the UR arm.",
 "Competition Capabilities": "Ball collection from floor and shelves; cone interaction. " + NOREQ,
 "Requirements": "- Robot face against the Central Resource Area at `y = 93`; nothing fixed beyond `y = 93` below `z = 42`.\n- UR heights: 95 (floor), 128 (lower shelf), 325 (upper shelf), 468 (cone).\n- Hand-off width = tower width (3 balls, 227 mm internal).",
 "Mechanical Interfaces": "Feeds the [feeder tower](../feeder/README.md) at its lower window; side plates on the chassis spacers; left plate trimmed above z 278 for the [shooter](../shooter/README.md).",
 "Electrical Interfaces": "DC-37 (R3 + R2 train), DC-25 lower roller, DC-25 UR lift, DC-25 UR band rotation: 4 of the 13 DC-motor slots.",
 "Software Interfaces": "Run intake with the tower; UR position presets; reverse for jam clearing.",
 "Design": "R2 changed to a straight roller in v19 (no longer needs to centre: the tower is 3 balls wide). Measured clearance to the Central Resource Area: 0 mm contact at the face (stop), 23–52 mm inside the table, 26.5 mm to the posts.",
 "Current Status": "v22 CAD; simulated in 2D only.", "Testing": "See [prototypes](prototypes/README.md).",
 "Known Issues": "- Multi-ball behaviour not simulated.\n- The UR lift motor sits high (z ≈ 500); moving it down was not possible (front wheel motor and lead-screw nut)."})
I["feeder"] = dict(
 title="Feeder", cad_intro="Ball tower: belts that lift the balls from the intake to the elbow at the top, which drops them into the basket (subsystem 3, `TW_`).",
 sims=[(O19 + "simulacion_recoleccion_torre_v19.png", "Ball path from the intake up the tilted tower to the elbow (z = 430)"), (O18 + "simulacion_codo_y_bolsillo_v18.png", "Left panel: elbow roller + cover takes the ball over the top into the basket (works from 0.42 to 1.26 m/s). Right panel is the v18 pocket, no longer used")],
 assembly="1. Side plates CF3 (3.1, 3.2) on the crossbars; right plate bolted to the elevator bulkhead; three spacers to the mast (5.24–5.26).\n2. D8 aluminium axles, 12 PU pulleys D30 and 6 round belts (3 rows × 2).\n3. Backing plate and front wall with window, anti-return TPU flap and stops.\n4. Elbow: roller (PETG sleeve + TPU, D40) with internal DC-25, journals, PC cover 165°…−15°, exit chute.\n5. DC-37 with 48T/48T/16T gears on the left side.",
 inspection=["Belts tensioned equally on the 3 rows", "Tower tilt 15° and top at z = 430", "Nothing above z 543 for y > −67 (Central Area roof)", "Elbow cover concentric with the roller (ball gap 51 ± 1 mm)", "S2 sensor window clear"],
 tests=[["Lift", "Balls lifted per minute, 3 rows", "No stalls with 15 stored"], ["Elbow", "Hand-off to basket at DC-25 200 RPM (0.42 m/s)", "10/10 into the basket"], ["Storage", "Balls held with tower stopped", "≈ 15"]],
 readme={
 "Purpose": "Lift balls from the intake and store them (≈ 15 when stopped), then pass them over the elbow into the basket in front of the tower.",
 "Competition Capabilities": "Ball transfer and storage. " + NOREQ,
 "Requirements": "3 balls wide (227 mm internal), top at z = 430 so nothing violates the Central Resource Area roof (z 543 at y > −67).",
 "Mechanical Interfaces": "Inlet from the [intake](../ball_intake/README.md); outlet into the [basket](../ball_storage/README.md); right plate on the elevator bulkhead ([gripper_elevation](../gripper_elevation/README.md)).",
 "Electrical Interfaces": "DC-37 (belts, 3:1 up) and DC-25 inside the elbow roller; S2 entry sensor (ranging sensor).",
 "Software Interfaces": "Runs with the intake; S2 counts balls in.",
 "Design": "Tilted 15°, length 352 mm, belts at 0.94 m/s. Elbow roller r20 at 51 mm from the cover axis, cover R86. R2 core passes through a D34 clearance in both plates (fixed in v20).",
 "Current Status": "v22 CAD; elbow and lift simulated in 2D.", "Testing": "See [prototypes](prototypes/README.md).",
 "Known Issues": "- The elbow motor could be removed with a transmission from the belts (frees a motor slot) but gears / belt clash with the launcher or the ball path; kept internal."})
I["ball_storage"] = dict(
 title="Ball Storage", cad_intro="Wide basket in front of the tower and the short feed roller that hands balls to the launcher (subsystem 8, `CN_`).",
 sims=[(O19 + "simulacion_lanzador_al_reves_v19.png", "Feed roller + inverted launcher: with the roller stopped the ball waits even with the wheel spinning; with the roller running it fires at ~44° / ~54°")],
 assembly="1. PC 1.2 floor sloped 10 % toward the launcher (and a V slope toward the lane), PC 1 walls.\n2. Feed roller TPU D30 on an 8 mm aluminium axle, bushing in the rear wall.\n3. DC-25 under the basket floor with 48T → 16T (3:1, 0.94 m/s at the roller) on the PETG support.",
 inspection=["Roller protrudes 12 mm above the floor", "Floor slot leaves the 16T and the support free", "Balls roll to the roller from both rows"],
 tests=[["Hold", "Ball waiting at the roller with the friction wheel at speed and roller stopped", "Does not move"], ["Feed", "Ball fired per roller activation at 0.94 m/s", "10/10, one ball at a time"], ["Capacity", "Balls in the basket", "6–8"]],
 readme={
 "Purpose": "Hold 6–8 balls next to the launcher and release them one at a time.",
 "Competition Capabilities": "Ball storage between collection and shooting. " + NOREQ,
 "Requirements": "Release only when the launcher is at speed (software interlock); no gate.",
 "Mechanical Interfaces": "Receives from the elbow of the [tower](../feeder/README.md); feeds the [shooter](../shooter/README.md) at the launcher mouth (`x −163`, `y 4`, `z 389`).",
 "Electrical Interfaces": "DC-25 feed motor (3:1).", "Software Interfaces": "Roller runs only with the brushless motors at speed.",
 "Design": "At 200 RPM direct (0.31 m/s) a waiting ball does not climb into the wheel (simulation), hence the 3:1 gear-up added in v20.",
 "Current Status": "v22 CAD; feed simulated in 2D.", "Testing": "See [prototypes](prototypes/README.md).",
 "Known Issues": "- Two balls entering together not simulated.\n- The 16T stands ~3 mm above the floor near the lane edge."})
I["shooter"] = dict(
 title="Shooter", cad_intro="Inverted launcher: friction wheel on top, hood below, ball fed horizontally from the basket (subsystem 7).",
 sims=[(O19 + "simulacion_lanzador_al_reves_v19.png", "Exit angle ~44° (fixed hood) / ~54–58° (servo flap); ball speed ≈ 0.47 × wheel speed"), (O19 + "simulacion_tiro_balistica_v19.png", "Wheel-speed window to land inside the Mobile Fortress top (640 mm, rim 646 mm) at 1–3 m, with air drag and an assumed 30 g ball")],
 assembly="1. CF 16×16 posts on the left rail and the CF3 base.\n2. Side plates CF3 with the D8 aluminium spacers.\n3. Two D45 friction wheels with rings on the two brushless motors and brackets; ESCs.\n4. Lower hood PC 2 mm R82.5 with TPU grip and ribs; flap on hinge driven by servo MS-12A; upper guard.",
 inspection=["Wheel–hood gap matches the CAD (ball squeeze)", "Flap travel 215° ↔ 198°", "Exit path clear of the robot in both hood positions", "Everything below z 543"],
 tests=[["Exit speed / angle", "High-speed video at 8 m/s wheel", "≈ 3.7 m/s, 44° / 54°"], ["Range table", "Wheel speed that lands in a 640 mm box at 1, 2, 3 m", "Window ±0.6–0.8 m/s; compare with the figure"], ["Repeatability", "Spread of 10 shots", "Inside 640 mm"]],
 readme={
 "Purpose": "Fire balls toward −x into the top of the opponent's Mobile Fortress.",
 "Competition Capabilities": "Ball scoring. " + NOREQ,
 "Requirements": "Fixed launcher (no turret), all parts below z 543 (Central Area roof), brushless 2/2, servos 1/6.",
 "Mechanical Interfaces": "Fed by the [basket](../ball_storage/README.md); base on the left rail posts; left of the [tower](../feeder/README.md).",
 "Electrical Interfaces": "2 brushless motors + 2 ESCs, 1 servo MS-12A.", "Software Interfaces": "Wheel-speed setpoint from a distance table; feed interlock.",
 "Design": "Wheel speed for a 30 g ball: 8.2–9.6 m/s at 1 m, 10.7–11.9 m/s at 2 m, 12.8–14.0 m/s at 3 m (44°).",
 "Current Status": "v22 CAD; simulated (2D contact + ballistics).", "Testing": "See [prototypes](prototypes/README.md).",
 "Known Issues": "- Ball mass not in the rules (30 g assumed); spin (Magnus) not modelled.\n- Brushless top speed on the D45 wheel unverified (needs ~14–15 m/s for 3 m)."})
I["gripper"] = dict(
 title="Gripper", cad_intro="Carriage and lead-screw jaw gripper; also carries the flag-mast receptor (subsystem 6).",
 sims=[],
 assembly="1. Carriage plate CF3 on the two linear-motion slide units; belt connector.\n2. Mounting block PETG, frame CF3, end blocks, D8 aluminium guide, T8×8 lead screw with DC-25 and coupling.\n3. Fixed and moving aluminium jaws with TPU V pads; distance sensor.\n4. Flag-mast receptor (6.17) glued/screwed on the front edge of the mounting block (`x 181.5`, `y −64`).",
 inspection=["Carriage travels 358 mm without binding", "Jaw opens/closes full stroke", "Receptor bore 8.3 mm aligned with the guide notch in the elevator lid"],
 tests=[["Pin grip", "Hold while driving and lifting", "No slip"], ["Cube / cone", "Grip and release", "TBD per element"]],
 readme={
 "Purpose": "Pick and place pins and other non-ball elements on the right side of the robot.",
 "Competition Capabilities": "Pins, Cones, Letter Cubes, Bonus Cubes are under study. " + NOREQ,
 "Requirements": "Inside the 500 mm footprint (jaw tip at x = +250).",
 "Mechanical Interfaces": "On the [gripper elevator](../gripper_elevation/README.md) carriage; holds the [flag mast](../flag_system/README.md) receptor.",
 "Electrical Interfaces": "DC-25 jaw motor, distance sensor.", "Software Interfaces": "Open / close commands; distance feedback.",
 "Design": "Single lead-screw jaw with V pads (v15 design, unchanged in v22).",
 "Current Status": "v22 CAD.", "Testing": "See [prototypes](prototypes/README.md).",
 "Known Issues": "- Universal vs dedicated tool trade study still open (see the original study table in git history)."})
I["gripper_elevation"] = dict(
 title="Gripper Elevation", cad_intro="Elevator tower (mast) for the gripper carriage, plus the structural ribs and spacers that tie it to the tower and intake (subsystem 5).",
 sims=[],
 assembly="1. Mast floor, rear/front plates, inner bulkhead and ribs (CF3).\n2. Linear rail (slide beam 496), 90T drive and idler pulleys, timing belt.\n3. DC-37 50 RPM with bracket.\n4. Lid with the AI camera tray; D10 notch for the flag mast at `x 181.5`, `y −64`.\n5. Tower–mast spacers (z 120 / 250 / 380) and intake–elevator frames.",
 inspection=["Carriage 28 → 386 mm (358 mm travel)", "Camera not crossed by the flag mast (3 mm clearance)", "Lid top z 612, robot height 642"],
 tests=[["Lift", "Time 0 → 358 mm with a pin", "TBD"], ["Holding", "Carriage drift with motor off", "None"]],
 readme={
 "Purpose": "Raise and lower the gripper carriage 358 mm; also raises the flag mast after the Modification Stage.",
 "Competition Capabilities": "Manipulator positioning; flag hanging height. " + NOREQ,
 "Requirements": "Initial height ≤ 700 mm (robot 642 mm).",
 "Mechanical Interfaces": "Carriage for the [gripper](../gripper/README.md); bulkhead shared with the [tower](../feeder/README.md); camera on the lid.",
 "Electrical Interfaces": "DC-37 50 RPM, AI camera 2.0.", "Software Interfaces": "Position presets; flag sequence (raise, lower, strafe).",
 "Design": "Belt drive with 90T pulleys; ribs at z 150 / 300 / 440.",
 "Current Status": "v22 CAD.", "Testing": "See [prototypes](prototypes/README.md).",
 "Known Issues": "- Elevator top support is 1 mm from the Central Area roof edge when the robot face is against the table; trim 10–15 mm suggested."})
I["flag_system"] = dict(
 title="Flag System", cad_intro="Removable flag mast, installed during the Modification Stage (subsystem 9). The receptor that stays on the robot is part 6.17 in [gripper](../../gripper/cad/README.md).",
 drawings_extra=[(O22 + "plano_mastil_bandera_v22.png", "Mast drawing: C-head section with dimensions and mast heights with the carriage down / up")],
 sims=[],
 assembly="Modification Stage (60 s): insert the CF 8×6 tube (9.2) through the lid notch into the receptor, fit the R clip (9.4), put the flag pole in the C head (9.1) and close it with the 2 rubber bands (9.3).",
 inspection=["Pole (< 10 × 10 mm) held by the bands against the spine", "Mast top 704 mm (carriage down) / 1062 mm (up)", "Robot + mast ≤ 10 kg (CAD 9.92 kg)"],
 tests=[["Retention", "Flag stays during driving and bumps", "No drop"], ["Hanging", "Raise, hook the loop on a real bar (950–965 mm), lower, strafe −x", "Flag stays on the bar, no contact with the robot"], ["Install time", "Mast installation", "< 30 s"]],
 readme={
 "Purpose": "Carry the team flag and hang it on the field flag bar in the Final Stage.",
 "Competition Capabilities": "Flag hanging, 50 points per flag. " + NOREQ,
 "Requirements": "- Flag ≥ 400 × 300 mm; optional rigid pole < 10 × 10 mm; suspension ≤ 400 × 10 × 10 (T17). Flag mass excluded, mast mass included (T02).\n- Field bar: horizontal aluminium bar 160 mm long at ≈ 950–965 mm.\n- No hook-shaped parts that can catch other robots (T08 (5)): the bands close the C.",
 "Mechanical Interfaces": "Receptor 6.17 on the gripper mounting block; guide notch in the elevator lid.",
 "Electrical Interfaces": "None (uses the gripper elevator).", "Software Interfaces": "Flag sequence: raise, hook, lower, strafe −x.",
 "Design": "Mast 31.6 g (tube 18.9 g, head 10.9 g, pin 1 g, bands 0.9 g).",
 "Current Status": "v22 CAD.", "Testing": "See [prototypes](prototypes/README.md).",
 "Known Issues": "- Bar direction relative to the pin table is not dimensioned in the rules; the head can be rotated 90° in the receptor.\n- Band stiffness must let the pole slide out without dragging the flag off the bar."})
I["common_parts"] = dict(
 title="Common Parts", cad_intro="Shared hardware (subsystem 10).",
 sims=[],
 assembly="Tighten all joints; blue thread locker on vibrating joints (motors, wheels, launcher).",
 inspection=["All modelled screws fitted (73 × M3 button head + chassis M4)", "≈ 80 additional joints defined by hand at assembly"],
 tests=[["Vibration", "Screws loose after 10 matches", "None"]],
 readme={
 "Purpose": "Hardware and parts shared by several subsystems.", "Competition Capabilities": "—",
 "Requirements": "Mass counts toward the 10 kg limit.", "Mechanical Interfaces": "All subsystems.", "Electrical Interfaces": "—", "Software Interfaces": "—",
 "Design": "Representative M3 button-head screws placed automatically at plate–plate and motor joints (73). Joints where the head clashed with neighbours are not modelled (≈ 80, ≈ 80 g).",
 "Current Status": "v22 CAD.", "Testing": "See [prototypes](prototypes/README.md).", "Known Issues": "- Real hole patterns come from the plate drawings, not from these screw positions."})
json.dump(I, open("/home/claude/docs_v22/info.json", "w"), indent=0, ensure_ascii=False)
