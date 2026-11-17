import novapi
from mbuild.encoder_motor import encoder_motor_class
from mbuild.ai_camera import ai_camera_class
from mbuild import power_expand_board
from mbuild import gamepad
import time

# Initialization of variables global
pot_lanzamiento = 0
aper_pot_griper = 0
mov_pot_griper = 0
v1 = 0
v2 = 0
v3 = 0
v4 = 0
Bandera = 0

# new class
encoder_motor_M1 = encoder_motor_class("M1", "INDEX1")
encoder_motor_M2 = encoder_motor_class("M2", "INDEX1")
encoder_motor_M3 = encoder_motor_class("M3", "INDEX1")
encoder_motor_M4 = encoder_motor_class("M4", "INDEX1")
ai_camera_p1 = ai_camera_class("PORT3", "INDEX1")

def Checar_Velocidades(Vx, Vy, W, ri):
    global v1, v2, v3, v4
    aux_VelAngular = W * ri
    v1 = Vx - Vy - aux_VelAngular
    v2 = Vx + Vy + aux_VelAngular
    v3 = Vx + Vy - aux_VelAngular
    v4 = Vx - Vy + aux_VelAngular

def Vel_Motores():
    global v1, v2, v3, v4
    encoder_motor_M1.set_speed(v1 * 1)
    encoder_motor_M2.set_speed(v2 * -1)
    encoder_motor_M3.set_speed(v3 * 1)
    encoder_motor_M4.set_speed(v4 * -1)

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

def InicializarTag():
    ai_camera_p1.ai_camera_set_func_switch(4, 1)
    time.sleep(10)
    ai_camera_p1.ai_camera_tag_func_mode_set(3, 1)
    ai_camera_p1.ai_camera_tag_actual_size_set(10, 1)

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

def Mov_Griper_N(modo):
    global mov_pot_griper
    mov_pot_griper = 50
    if modo == 1:
      power_expand_board.set_power("DC1", mov_pot_griper)
    else:
      power_expand_board.set_power("DC1", mov_pot_griper * -1)

def Reset_Motores():
    encoder_motor_M2.set_speed(0)
    encoder_motor_M3.set_speed(0)
    encoder_motor_M4.set_speed(0)

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

def Apertura_Griper_N(modo): 
    global aper_pot_griper
    aper_pot_griper = 50
    if modo == 1:
      power_expand_board.set_power("DC2", aper_pot_griper)
    else:
      power_expand_board.set_power("DC2", aper_pot_griper * -1)

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

time.sleep(30)
InicializarTag()
main()