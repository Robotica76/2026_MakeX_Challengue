## @file Robot.py
#  @brief Programa autónomo y de control manual del robot de Robotica76 para el reto MakeX 2026 "StormBreaker".
#  @details Se ejecuta en el controlador NovaPi de mBuild con chasis de 4 ruedas mecanum (motores con encoder M1-M4),
#  una cámara AI para leer códigos QR/tags, una garra (DC1 la mueve, DC2 la abre/cierra) y un
#  lanzador con dos motores brushless (BL1/BL2).
#
#  Funcionamiento:
#  - Al iniciar espera 30 s, inicializa el reconocimiento de tags de la cámara y entra a main().
#  - main() es un ciclo de control con el gamepad: los joysticks siempre mueven el chasis y los botones
#    activan acciones: N1 = rutina autónoma de 28 s (lee tags y se mueve según el resultado), N2 = detener motores,
#    Up/Down = mover garra, L1/R1 = abrir/cerrar garra, N3 = lanzador (R2/L2 ajustan la potencia, N3 lo detiene).
#
#  @note Los nombres en español se conservan del proyecto original de mBlock.

import novapi
from mbuild.encoder_motor import encoder_motor_class
from mbuild.ai_camera import ai_camera_class
from mbuild import power_expand_board
from mbuild import gamepad
import time

## @name Variables globales
#  @{
## @var pot_lanzamiento  Potencia del lanzador (porcentaje) aplicada a BL1/BL2.
## @var aper_pot_griper  Potencia del motor de apertura/cierre de la garra (DC2).
## @var mov_pot_griper   Potencia del motor de movimiento de la garra (DC1).
## @var v1  Velocidad objetivo de la rueda M1 (la calcula Checar_Velocidades).
## @var v2  Velocidad objetivo de la rueda M2.
## @var v3  Velocidad objetivo de la rueda M3.
## @var v4  Velocidad objetivo de la rueda M4.
## @var Bandera  Bandera para salir de ciclos (1 = terminado).
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

## @name Objetos de hardware
#  @{
## @var encoder_motor_M1 Motor con encoder del chasis en M1.
## @var encoder_motor_M2 Motor con encoder del chasis en M2.
## @var encoder_motor_M3 Motor con encoder del chasis en M3.
## @var encoder_motor_M4 Motor con encoder del chasis en M4.
## @var ai_camera_p1 Cámara AI en PORT3 usada para detectar tags/QR.
#  @}
# new class
encoder_motor_M1 = encoder_motor_class("M1", "INDEX1")
encoder_motor_M2 = encoder_motor_class("M2", "INDEX1")
encoder_motor_M3 = encoder_motor_class("M3", "INDEX1")
encoder_motor_M4 = encoder_motor_class("M4", "INDEX1")
ai_camera_p1 = ai_camera_class("PORT3", "INDEX1")

## @brief Calcula las velocidades de las cuatro ruedas a partir de la velocidad deseada del chasis (cinemática mecanum).
#  @param Vx Componente hacia adelante/atrás.
#  @param Vy Componente lateral.
#  @param W  Componente de rotación.
#  @param ri Ganancia de rotación (factor aplicado a W).
#  @post Se actualizan las globales v1..v4; llamar a Vel_Motores() para aplicarlas.
def Checar_Velocidades(Vx, Vy, W, ri):
    global v1, v2, v3, v4
    aux_VelAngular = W * ri
    v1 = Vx - Vy - aux_VelAngular
    v2 = Vx + Vy + aux_VelAngular
    v3 = Vx + Vy - aux_VelAngular
    v4 = Vx - Vy + aux_VelAngular

## @brief Aplica las velocidades globales v1..v4 a los motores (M2 y M4 van invertidos por el sentido de montaje).
def Vel_Motores():
    global v1, v2, v3, v4
    encoder_motor_M1.set_speed(v1 * 1)
    encoder_motor_M2.set_speed(v2 * -1)
    encoder_motor_M3.set_speed(v3 * 1)
    encoder_motor_M4.set_speed(v4 * -1)

## @brief Rutina autónoma de decisión basada en los tags vistos por la cámara AI.
#  @details Lee el tag izquierdo (id 2) y el derecho (id 3). Si no encuentra ninguno asume
#  dos conos y avanza. Si ambos tags están en la misma posición, agarra el cubo (valor de tag 2)
#  o se mueve, vuelve a leer el tag y compara ambas lecturas. En otro caso compara los dos tags
#  directamente. El resultado se delega a Comparacion_Valores() y Mov_Auto().
#  @note Contiene un time.sleep(30) temporal marcado "QUITAR" para pruebas.
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

## @brief Mueve el robot de forma autónoma durante un tiempo fijo.
#  @param tipo Tipo de movimiento: 1 = primero lateral y luego hacia adelante; otro valor = solo hacia adelante.
#  @param distancia Distancia objetivo en cm (aún no se usa; el movimiento es por tiempo, ver el comentario interno).
#  @note Cada fase corre hasta que novapi.timer() es igual a 20.
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

## @brief Inicializa el reconocimiento de tags de la cámara AI.
#  @details Activa la función de tags, espera 10 s a que la cámara arranque y luego configura
#  el modo de tag y el tamaño real del tag (10).
def InicializarTag():
    ai_camera_p1.ai_camera_set_func_switch(4, 1)
    time.sleep(10)
    ai_camera_p1.ai_camera_tag_func_mode_set(3, 1)
    ai_camera_p1.ai_camera_tag_actual_size_set(10, 1)

## @brief Compara dos lecturas de tags y se mueve hacia el objetivo elegido.
#  @param Val1 Valor del primer tag.
#  @param Dist1 Distancia del primer tag en píxeles (se convierte a cm con 16.84 px/cm).
#  @param Pos1 1 si el primer tag está al lado izquierdo de la imagen (se niega la distancia).
#  @param Val2 Valor del segundo tag.
#  @param Dist2 Distancia del segundo tag en píxeles (se convierte a cm).
#  @param Pos2 1 si el segundo tag está al lado izquierdo de la imagen.
#  @param modo 1 = caso de dos cubos; otro valor = caso de tres posiciones.
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

## @brief Mueve la garra con el motor DC1 al 50% de potencia.
#  @param modo 1 = un sentido; otro valor = sentido contrario.
def Mov_Griper_N(modo):
    global mov_pot_griper
    mov_pot_griper = 50
    if modo == 1:
      power_expand_board.set_power("DC1", mov_pot_griper)
    else:
      power_expand_board.set_power("DC1", mov_pot_griper * -1)

## @brief Detiene los motores del chasis M2, M3 y M4.
def Reset_Motores():
    encoder_motor_M2.set_speed(0)
    encoder_motor_M3.set_speed(0)
    encoder_motor_M4.set_speed(0)

## @brief Ciclo principal del gamepad (nunca termina).
#  @details Atiende el inicio autónomo (N1, 28 s), paro de motores (N2), garra (Up/Down, L1/R1) y
#  lanzador (N3), y mueve continuamente el chasis con los joysticks.
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

## @brief Abre o cierra la garra con el motor DC2 al 50% de potencia.
#  @param modo 1 = un sentido; otro valor = sentido contrario.
def Apertura_Griper_N(modo): 
    global aper_pot_griper
    aper_pot_griper = 50
    if modo == 1:
      power_expand_board.set_power("DC2", aper_pot_griper)
    else:
      power_expand_board.set_power("DC2", aper_pot_griper * -1)

## @brief Ciclo de control del lanzador.
#  @details Mantiene los motores brushless BL1/BL2 a pot_lanzamiento; R2 aumenta y L2 disminuye
#  la potencia en 5. Al presionar N3 detiene ambos motores y sale del ciclo.
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

# Punto de entrada del programa
time.sleep(30)
InicializarTag()
main()