## @file Robot.py
#  @brief Autonomous and manual control program for the Robotica76 robot, MakeX 2026 "StormBreaker" challenge.
#  @details Runs on the mBuild NovaPi controller with a 4-wheel mecanum/omni drive (encoder motors M1-M4),
#  an AI camera used to read QR/tag codes, a gripper (DC1 moves, DC2 opens/closes) and a
#  two-motor brushless launcher (BL1/BL2).
#
#  Operation:
#  - On boot the script waits 30 s, initializes the camera tag recognition and enters main().
#  - main() is a gamepad loop: the joysticks always drive the chassis, and buttons trigger actions:
#    N1 = 28 s autonomous routine (reads tags and moves accordingly), N2 = stop motors,
#    Up/Down = gripper move, L1/R1 = gripper open/close, N3 = launcher (R2/L2 adjust power, N3 stops).
#
#  @note Spanish identifiers are kept from the original mBlock project.

import novapi
from mbuild.encoder_motor import encoder_motor_class
from mbuild.ai_camera import ai_camera_class
from mbuild import power_expand_board
from mbuild import gamepad
import time

## @name Global state
#  @{
## @var pot_lanzamiento  Launcher power (percent) applied to BL1/BL2.
## @var aper_pot_griper  Power of the gripper open/close motor (DC2).
## @var mov_pot_griper   Power of the gripper movement motor (DC1).
## @var v1  Target speed of wheel M1 (set by Checar_Velocidades).
## @var v2  Target speed of wheel M2.
## @var v3  Target speed of wheel M3.
## @var v4  Target speed of wheel M4.
## @var Bandera  Flag used to exit loops (1 = finished).
#  @}
# Initialization of variables global
pot_lanzamiento = 0
aper_pot_griper = 0
mov_pot_griper = 0
v1 = 0
v2 = 0
v3 = 0
v4 = 0
Bandera = 0

## @name Hardware objects
#  @{
## @var encoder_motor_M1 Chassis encoder motor on M1.
## @var encoder_motor_M2 Chassis encoder motor on M2.
## @var encoder_motor_M3 Chassis encoder motor on M3.
## @var encoder_motor_M4 Chassis encoder motor on M4.
## @var ai_camera_p1 AI camera on PORT3 used for tag/QR detection.
#  @}
# new class
encoder_motor_M1 = encoder_motor_class("M1", "INDEX1")
encoder_motor_M2 = encoder_motor_class("M2", "INDEX1")
encoder_motor_M3 = encoder_motor_class("M3", "INDEX1")
encoder_motor_M4 = encoder_motor_class("M4", "INDEX1")
ai_camera_p1 = ai_camera_class("PORT3", "INDEX1")

## @brief Computes the four wheel speeds from a desired chassis velocity (mecanum kinematics).
#  @param Vx Forward/backward component.
#  @param Vy Lateral (strafe) component.
#  @param W  Rotation component.
#  @param ri Rotation gain (distance factor applied to W).
#  @post Global v1..v4 are updated; call Vel_Motores() to apply them.
def Checar_Velocidades(Vx, Vy, W, ri):
    global v1, v2, v3, v4
    aux_VelAngular = W * ri
    v1 = Vx - Vy - aux_VelAngular
    v2 = Vx + Vy + aux_VelAngular
    v3 = Vx + Vy - aux_VelAngular
    v4 = Vx - Vy + aux_VelAngular

## @brief Applies the global wheel speeds v1..v4 to the motors (M2 and M4 are inverted for mounting direction).
def Vel_Motores():
    global v1, v2, v3, v4
    encoder_motor_M1.set_speed(v1 * 1)
    encoder_motor_M2.set_speed(v2 * -1)
    encoder_motor_M3.set_speed(v3 * 1)
    encoder_motor_M4.set_speed(v4 * -1)

## @brief Autonomous decision routine based on the tags seen by the AI camera.
#  @details Reads the left (id 2) and right (id 3) tags. If neither is found it assumes
#  two cones and moves forward. If both tags are at the same position it either grabs the cube
#  (tag value 2) or moves, re-reads the tag and compares both readings. Otherwise it compares the
#  two tags directly. Results are delegated to Comparacion_Valores() and Mov_Auto().
#  @note Contains a temporary 30 s sleep marked "QUITAR" (remove) for testing.
def Comparacion_QR():
    B1 = 0
    B2 = 0
    PC1 = 0
    PC2 = 0
    BD1 = 0
    cuboIzq = ai_camera_p1.ai_camera_tag_analysis_result_get(2, 1)
    cuboDer = ai_camera_p1.ai_camera_tag_analysis_result_get(3, 1)
    if cuboIzq == 'Null' and cuboDer == 'Null':
      print("2 Conos")
      Mov_Auto(1, 55)
    else:
      if ai_camera_p1.ai_camera_tag_spatial_attribute_get(2, 1, 1) == ai_camera_p1.ai_camera_tag_spatial_attribute_get(3, 1, 1):
        if ai_camera_p1.ai_camera_tag_analysis_result_get(1, 1) == 2:
          print("Agarrar Cubo")
        else:
          B1 = ai_camera_p1.ai_camera_tag_analysis_result_get(1, 1)
          BD1 = ai_camera_p1.ai_camera_tag_spatial_attribute_get(1, 1, 1)
          if ai_camera_p1.ai_camera_tag_spatial_attribute_get(1, 1, 1) < 320:
            PC1 = 1
          Mov_Auto(1, 44)
          time.sleep(30) # QUITAR
          B2 = ai_camera_p1.ai_camera_tag_analysis_result_get(1, 1)
          if ai_camera_p1.ai_camera_tag_spatial_attribute_get(1, 1, 1) < 320:
            PC2 = 1
          Comparacion_Valores(B1, BD1, PC1, B2, ai_camera_p1.ai_camera_tag_spatial_attribute_get(3, 1, 1), PC2, 1)
      else:
        Comparacion_Valores(ai_camera_p1.ai_camera_tag_analysis_result_get(2, 1), ai_camera_p1.ai_camera_tag_spatial_attribute_get(2, 1, 1), 0, ai_camera_p1.ai_camera_tag_analysis_result_get(3, 1), ai_camera_p1.ai_camera_tag_spatial_attribute_get(3, 1, 1), 0, 0)

## @brief Moves the robot autonomously for a fixed time.
#  @param tipo Movement type: 1 = lateral movement then forward; otherwise forward only.
#  @param distancia Target distance in cm (currently unused; movement is time based, see the TODO inside).
#  @note Each phase runs until novapi.timer() equals 20.
def Mov_Auto(tipo, distancia):
    # Con la DISTANCIA obtener la velocidad de los motores y el tiempo que se debe de mover
    if tipo == 1:
      Checar_Velocidades(0, 1, 0, 1)
      novapi.reset_timer()
      while not (novapi.timer() == 20):
          time.sleep(0.001)
          Vel_Motores()

    Checar_Velocidades(1, 0, 0, 1)
    novapi.reset_timer()
    while not (novapi.timer() == 20):
        time.sleep(0.001)
        Vel_Motores()

## @brief Initializes the AI camera tag recognition.
#  @details Enables the tag function, waits 10 s for the camera to start, then sets the tag
#  mode and the real tag size (10).
def InicializarTag():
    ai_camera_p1.ai_camera_set_func_switch(4, 1)
    time.sleep(10)
    ai_camera_p1.ai_camera_tag_func_mode_set(3, 1)
    ai_camera_p1.ai_camera_tag_actual_size_set(10, 1)

## @brief Compares two tag readings and moves toward the selected target.
#  @param Val1 Value of the first tag.
#  @param Dist1 Distance of the first tag in pixels (converted to cm using 16.84 px/cm).
#  @param Pos1 1 if the first tag is on the left side of the image (distance is negated).
#  @param Val2 Value of the second tag.
#  @param Dist2 Distance of the second tag in pixels (converted to cm).
#  @param Pos2 1 if the second tag is on the left side of the image.
#  @param modo 1 = two-cube case, any other value = three-position case.
def Comparacion_Valores(Val1, Dist1, Pos1, Val2, Dist2, Pos2, modo):
    Dist1 = Dist1 / 16.84   # Dist1 esta en pixeles y se divide entre 16.84 para obtener la distancia en cm
    Dist2 = Dist2 / 16.84   # Dist2 esta en pixeles y se divide entre 16.84 para obtener la distancia en cm
    if modo == 1:
      if Val1 > Val2:
        if Pos1 == 1:
          Dist1 = Dist1 * -1
        print("2 CUBO IZQ")
        Mov_Auto(1, (-44 + Dist1))
      else:
        if Pos2 == 1:
            Dist2 = Dist2 * -1    
        print("2 CUBO DER")
        Mov_Auto(1, Dist2)
    else:
      if Val1 > Val2:
        Dist1 = Dist1 * -1
        print("3 IZQ")
        Mov_Auto(1, Dist1)
      else:
        print("3 DER")
        Mov_Auto(1, Dist2)

## @brief Moves the gripper with motor DC1 at 50% power.
#  @param modo 1 = one direction, any other value = opposite direction.
def Mov_Griper_N(modo):
    global mov_pot_griper
    mov_pot_griper = 50
    if modo == 1:
      power_expand_board.set_power("DC1", mov_pot_griper)
    else:
      power_expand_board.set_power("DC1", mov_pot_griper * -1)

## @brief Stops chassis motors M2, M3 and M4.
def Reset_Motores():
    encoder_motor_M2.set_speed(0)
    encoder_motor_M3.set_speed(0)
    encoder_motor_M4.set_speed(0)

## @brief Main gamepad loop (never returns).
#  @details Handles autonomous start (N1, 28 s), motor stop (N2), gripper (Up/Down, L1/R1) and
#  launcher (N3), and continuously drives the chassis with the joysticks.
def main():
    global pot_lanzamiento
    while True:
        time.sleep(0.001)
        if gamepad.is_key_pressed("N1"):
          novapi.reset_timer()
          while novapi.timer() < 28: # 28
            Comparacion_QR()
        elif gamepad.is_key_pressed("N2"):
          Reset_Motores()
        elif gamepad.is_key_pressed("Up"):
          Mov_Griper_N(1)
        elif gamepad.is_key_pressed("Down"):
          Mov_Griper_N(0)
        elif gamepad.is_key_pressed("L1"):
          Apertura_Griper_N(1)
        elif gamepad.is_key_pressed("R1"):
          Apertura_Griper_N(0)
        elif gamepad.is_key_pressed("N3"):
          pot_lanzamiento = 20
          Lanzador()
        Checar_Velocidades(gamepad.get_joystick("Ly"), gamepad.get_joystick("Lx"), gamepad.get_joystick("Rx"), 1)
        Vel_Motores()

## @brief Opens or closes the gripper with motor DC2 at 50% power.
#  @param modo 1 = one direction, any other value = opposite direction.
def Apertura_Griper_N(modo): 
    global aper_pot_griper
    aper_pot_griper = 50
    if modo == 1:
      power_expand_board.set_power("DC2", aper_pot_griper)
    else:
      power_expand_board.set_power("DC2", aper_pot_griper * -1)

## @brief Launcher control loop.
#  @details Runs the brushless motors BL1/BL2 at pot_lanzamiento; R2 increases and L2 decreases
#  the power by 5. Pressing N3 stops both motors and exits the loop.
def Lanzador():
    global pot_lanzamiento
    Bandera = 0
    while not (Bandera == 1):
        time.sleep(0.001)
        if gamepad.is_key_pressed("R2"):
          pot_lanzamiento = (pot_lanzamiento + 5)

        if gamepad.is_key_pressed("L2"):
          pot_lanzamiento = (pot_lanzamiento - 5)

        power_expand_board.set_power("BL1", pot_lanzamiento)
        power_expand_board.set_power("BL2", pot_lanzamiento)
        if gamepad.is_key_pressed("N3"):
          power_expand_board.set_power("BL1", 0)
          power_expand_board.set_power("BL2", 0)
          Bandera = 1

# Program entry point
time.sleep(30)
InicializarTag()
main()