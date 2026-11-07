# codes make you happy
import novapi
from mbuild.ranging_sensor import ranging_sensor_class
from mbuild import gamepad
from mbuild import power_expand_board
from mbuild.encoder_motor import encoder_motor_class
from mbuild.smartservo import smartservo_class
import time

# initialize variables
Diametro = 0
pi = 0
distancia_cm = 0
motor_sensibilidad = 0
potencia = 0
auxiliar_modo_pinza_lanzador = 0
tiempo_subida_pinza = 0
medida_pinza_alzada = 0
diferencia_cm_piso_pinza = 0

# new class
distance_sensor_1 = ranging_sensor_class("PORT5", "INDEX1")
encoder_motor_M1 = encoder_motor_class("M1", "INDEX1")
encoder_motor_M2 = encoder_motor_class("M2", "INDEX1")
encoder_motor_M3 = encoder_motor_class("M3", "INDEX1")
encoder_motor_M4 = encoder_motor_class("M4", "INDEX1")
smartservo_2 = smartservo_class("M6", "INDEX1")
smartservo_1 = smartservo_class("M5", "INDEX1")

def abrir_pinza_auto_N(angulo_abertura_pinza_auto):
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    smartservo_2.move_to(angulo_abertura_pinza_auto, 5)

def cerrar_pinza_auto_N(angulo_cerradura_pinza_auto):
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    smartservo_2.move_to(angulo_cerradura_pinza_auto, 5)

def inicio_derecho():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    time.sleep(3)

def inicio_izquierdo():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    while not (distance_sensor_1.get_distance() < 10):
        time.sleep(0.001)
        subir_pinza()

def Automatico():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    abrir_pinza_manual()
    Diametro = 6
    pi = 3.14159
    tiempo_subida_pinza = 8.81
    medida_pinza_alzada = 82.5
    diferencia_cm_piso_pinza = 7.5
    while not (gamepad.is_key_pressed("N2") or gamepad.is_key_pressed("N3")):
      # DO SOMETHING
      pass

    if gamepad.is_key_pressed("N2"):
      inicio_derecho()

    if gamepad.is_key_pressed("N3"):
      inicio_izquierdo()

def t_subida_pinza_N(cm_subir_t_pinza):
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    power_expand_board.set_power("DC5", ((((cm_subir_t_pinza - diferencia_cm_piso_pinza)) * medida_pinza_alzada) / tiempo_subida_pinza) * -100)
    power_expand_board.set_power("DC6", ((((cm_subir_t_pinza - diferencia_cm_piso_pinza)) * medida_pinza_alzada) / tiempo_subida_pinza) * 100)

def t_bajada_pinza_N(cm_bajada_T_pinza):
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    power_expand_board.set_power("DC5", ((((cm_bajada_T_pinza - diferencia_cm_piso_pinza)) * medida_pinza_alzada) / tiempo_subida_pinza) * 100)
    power_expand_board.set_power("DC6", ((((cm_bajada_T_pinza - diferencia_cm_piso_pinza)) * medida_pinza_alzada) / tiempo_subida_pinza) * -100)

def parar_subida_disco():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    power_expand_board.stop("DC1")
    power_expand_board.stop("DC2")
    power_expand_board.stop("DC3")
    power_expand_board.stop("DC4")
    power_expand_board.stop("DC7")

def abrir_pinza_manual():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    # maxima abertura 50 grados
    smartservo_2.move_to(40, 5)

def subir_pinza():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    power_expand_board.set_power("DC5", -100)
    power_expand_board.set_power("DC6", 100)

def cerrar_pinza_manual():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    # maxima cerradura -65,
    # dejar a -60 por seguridad
    smartservo_2.move_to(-60, 5)

def subir_lanzador():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    # el maximo para la elevacion es -150
    smartservo_1.move_to(-145, 5)

def bajar_pinza():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    power_expand_board.set_power("DC5", 100)
    power_expand_board.set_power("DC6", -100)

def subir_disco_N(potencia_subir_disco):
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    power_expand_board.set_power("DC1", 1 * potencia_subir_disco)
    power_expand_board.set_power("DC2", -1 * potencia_subir_disco)
    power_expand_board.set_power("DC3", -1 * potencia_subir_disco)
    power_expand_board.set_power("DC4", -1 * potencia_subir_disco)
    power_expand_board.set_power("DC7", 1 * potencia_subir_disco)

def bajar_lanzador():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    smartservo_1.move_to(-40, 5)

def pinza_parar_abertura():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    smartservo_2.move(0, 0)

def detener_pinza():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    power_expand_board.stop("DC5")
    power_expand_board.stop("DC6")

def Retroceder_N(cm):
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    encoder_motor_M1.move((cm / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M2.move((cm / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M3.move((cm / ((Diametro * pi) / 360)) * -1, 80)
    encoder_motor_M4.move((cm / ((Diametro * pi) / 360)) * -1, 80)

def detener_lanzador():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    smartservo_1.move(0, 0)

def manual():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    while True:
        time.sleep(0.001)
        if gamepad.is_key_pressed("≡"):
          auxiliar_modo_pinza_lanzador = 0

        if gamepad.is_key_pressed("+"):
          auxiliar_modo_pinza_lanzador = 1

        if auxiliar_modo_pinza_lanzador == 0:
          modo_lanzamiento()

        if auxiliar_modo_pinza_lanzador == 1:
          modo_pinza()

def modo_pinza():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    movimiento_joystick_pinza()
    if gamepad.is_key_pressed("Up"):
      subir_pinza()

    else:
      if gamepad.is_key_pressed("Down"):
        bajar_pinza()

      else:
        detener_pinza()

    # el maximo que se puede abrir la pinza es 50
    if gamepad.is_key_pressed("Left"):
      abrir_pinza_manual()

    else:
      if gamepad.is_key_pressed("Right"):
        cerrar_pinza_manual()

      else:
        pinza_parar_abertura()

def modo_lanzamiento():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    movimiento_joystick_lanzador()
    if gamepad.is_key_pressed("Up"):
      subir_lanzador()

    else:
      if gamepad.is_key_pressed("Down"):
        bajar_lanzador()

      else:
        detener_lanzador()

    if gamepad.is_key_pressed("L1"):
      subir_disco_N(70)

    else:
      parar_subida_disco()

def Avanzar_N(cm):
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    encoder_motor_M1.move((cm / ((Diametro * pi) / 360)) * -1, 80)
    encoder_motor_M2.move((cm / ((Diametro * pi) / 360)) * -1, 80)
    encoder_motor_M3.move((cm / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M4.move((cm / ((Diametro * pi) / 360)) * 1, 80)

def avance_izquierda_N(cm):
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    encoder_motor_M1.move((cm / ((Diametro * pi) / 360)) * 1, 85)
    encoder_motor_M2.move((cm / ((Diametro * pi) / 360)) * -1, 85)
    encoder_motor_M3.move((cm / ((Diametro * pi) / 360)) * -1, 85)
    encoder_motor_M4.move((cm / ((Diametro * pi) / 360)) * 1, 85)

def movimiento_joystick_pinza():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    encoder_motor_M1.set_speed((-1 * gamepad.get_joystick("Ly") + ((1 * gamepad.get_joystick("Lx") + -1 * gamepad.get_joystick("Rx")))))
    encoder_motor_M2.set_speed((-1 * gamepad.get_joystick("Ly") + ((-1 * gamepad.get_joystick("Lx") + -1 * gamepad.get_joystick("Rx")))))
    encoder_motor_M3.set_speed((1 * gamepad.get_joystick("Ly") + ((-1 * gamepad.get_joystick("Lx") + -1 * gamepad.get_joystick("Rx")))))
    encoder_motor_M4.set_speed((1 * gamepad.get_joystick("Ly") + ((1 * gamepad.get_joystick("Lx") + -1 * gamepad.get_joystick("Rx")))))

def avance_derecha_N(cm):
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    encoder_motor_M1.move((((cm + 5)) / ((Diametro * pi) / 360)) * -1, 80)
    encoder_motor_M2.move((((cm + 5)) / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M3.move((((cm + 5)) / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M4.move((((cm + 5)) / ((Diametro * pi) / 360)) * -1, 80)

def movimiento_joystick_lanzador():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    encoder_motor_M1.set_speed((1 * gamepad.get_joystick("Ly") + ((-1 * gamepad.get_joystick("Lx") + -1 * gamepad.get_joystick("Rx")))))
    encoder_motor_M2.set_speed((1 * gamepad.get_joystick("Ly") + ((1 * gamepad.get_joystick("Lx") + -1 * gamepad.get_joystick("Rx")))))
    encoder_motor_M3.set_speed((-1 * gamepad.get_joystick("Ly") + ((1 * gamepad.get_joystick("Lx") + -1 * gamepad.get_joystick("Rx")))))
    encoder_motor_M4.set_speed((-1 * gamepad.get_joystick("Ly") + ((-1 * gamepad.get_joystick("Lx") + -1 * gamepad.get_joystick("Rx")))))

def girar_izquierda_90_C2_B0():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    encoder_motor_M1.move((47 / ((Diametro * pi) / 360)) * -1, 80)
    encoder_motor_M2.move((47 / ((Diametro * pi) / 360)) * -1, 80)
    encoder_motor_M3.move((47 / ((Diametro * pi) / 360)) * -1, 80)
    encoder_motor_M4.move((47 / ((Diametro * pi) / 360)) * -1, 80)

def girar_izquierda_180_C2_B0():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    encoder_motor_M1.move((92 / ((Diametro * pi) / 360)) * -1, 80)
    encoder_motor_M2.move((92 / ((Diametro * pi) / 360)) * -1, 80)
    encoder_motor_M3.move((92 / ((Diametro * pi) / 360)) * -1, 80)
    encoder_motor_M4.move((92 / ((Diametro * pi) / 360)) * -1, 80)

def girar_derecha_90_C2_B0():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    encoder_motor_M1.move((47 / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M2.move((47 / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M3.move((47 / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M4.move((47 / ((Diametro * pi) / 360)) * 1, 80)

def girar_derecha_180_C2_B0():
    global Diametro, pi, distancia_cm, motor_sensibilidad, potencia, auxiliar_modo_pinza_lanzador, tiempo_subida_pinza, medida_pinza_alzada, diferencia_cm_piso_pinza
    encoder_motor_M1.move((92 / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M2.move((92 / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M3.move((92 / ((Diametro * pi) / 360)) * 1, 80)
    encoder_motor_M4.move((92 / ((Diametro * pi) / 360)) * 1, 80)

smartservo_2.move_to(30, 5)
while not gamepad.is_key_pressed("N1"):
  # DO SOMETHING
  pass

Automatico()
manual()
