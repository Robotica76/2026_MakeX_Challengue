## @file robot_control.py
#  @brief Control principal del robot con movimiento omnidireccional, griper, lanzador y visión QR.
#  @details Este módulo integra todos los subsistemas del robot:
#           - Tracción omnidireccional de 4 ruedas mediante motores encoder (M1–M4).
#           - Griper con movimiento vertical (DC1) y apertura/cierre de pinzas (SM1).
#           - Lanzador de pelotas con dos motores brushless (BL1, BL2).
#           - Visión artificial con cámara de IA para lectura y comparación de etiquetas QR.
#           - Control manual mediante gamepad con mapeo de teclas a acciones.
#           - Modo autónomo de 28 s que usa la cámara para seleccionar y alcanzar el cubo
#             de mayor valor detectado en campo.
#  @author  Equipo de robótica
#  @date    2024

import novapi
from mbuild.encoder_motor import encoder_motor_class
from mbuild.ai_camera import ai_camera_class
from mbuild.smartservo import smartservo_class
from mbuild import power_expand_board
from mbuild import gamepad
import time

## @name Variables globales
#  @{
## @var pot_lanzamiento  Potencia del lanzador (porcentaje) aplicada a BL1/BL2.
## @var aper_pot_griper  Potencia del motor de apertura/cierre de la garra (SM1).
## @var mov_pot_griper   Potencia del motor de movimiento de la garra (DC1).
## @var v1  Velocidad objetivo de la rueda M1 (la calcula Checar_Velocidades).
## @var v2  Velocidad objetivo de la rueda M2.
## @var v3  Velocidad objetivo de la rueda M3.
## @var v4  Velocidad objetivo de la rueda M4.
## @var Bandera  Bandera para salir de ciclos (1 = terminado).
## @var TECLAS Tupla de nombres de teclas del gamepad que están registradas en el sistema.
## @var acciones_gamepad  Diccionario que mapea cada tecla registrada a su función y argumentos.
#  @}

pot_lanzamiento = 0
aper_pot_griper = 0
mov_pot_griper = 0
ang_pot_brush = 0
bandera = 0

## @brief Aplica las velocidades globales v1..v4 a los motores (M2 y M4 van invertidos por el sentido de montaje).
encoder_motor_M1 = encoder_motor_class("M1", "INDEX1")
encoder_motor_M2 = encoder_motor_class("M2", "INDEX1")
encoder_motor_M3 = encoder_motor_class("M3", "INDEX1")
encoder_motor_M4 = encoder_motor_class("M4", "INDEX1")
## @brief Instancia de la cámara de IA para lectura de etiquetas QR.
ai_camera_p1 = ai_camera_class("PORT3", "INDEX1")
## @brief Instancias de los smartservos para el griper y el brush.
smartservo_1 = smartservo_class("M5", "INDEX1")
smartservo_2 = smartservo_class("M6", "INDEX1")


## @var TECLAS
#  @brief Tupla de nombres de teclas del gamepad que están registradas en el sistema.
#  @details Solo las teclas incluidas aquí son evaluadas por get_pressed_key().
#           Cualquier otra tecla del gamepad se ignora en el bucle principal.
TECLAS = ("N1", "N2", "N3", "Up", "Down", "L1", "R1", "Left", "Right")


# Cinemática

## @brief Calcula las velocidades de los cuatro motores para un robot omnidireccional.
#  @details Aplica la ecuación de cinemática inversa holonómica para una configuración
#           de cuatro ruedas mecanum o similares. La velocidad angular se pondera con
#           el factor @p ri antes de sumarse o restarse a cada rueda:
#           @code
#           aux = W * ri
#           v1 = Vx - Vy - aux   (rueda M1)
#           v2 = Vx + Vy + aux   (rueda M2)
#           v3 = Vx + Vy - aux   (rueda M3)
#           v4 = Vx - Vy + aux   (rueda M4)
#           @endcode
#           Los signos permiten que el robot se traslade en cualquier dirección y
#           rote simultáneamente sin cambiar la orientación de las ruedas.
#  @param Vx  Componente de velocidad en el eje X del robot (avance/retroceso).
#             Valores positivos avanzan, negativos retroceden.
#  @param Vy  Componente de velocidad en el eje Y del robot (desplazamiento lateral).
#             Valores positivos desplazan a la derecha, negativos a la izquierda.
#  @param W   Velocidad angular de giro sobre el eje Z del robot.
#             Valores positivos giran en sentido horario, negativos en antihorario.
#  @param ri  Factor de escala (radio efectivo) que pondera la contribución angular.
#             Normalmente se pasa 1 para mantener las unidades consistentes.
#  @return    Tupla de cuatro flotantes (v1, v2, v3, v4) con las velocidades
#             calculadas para los motores M1, M2, M3 y M4 respectivamente.
def Checar_Velocidades(Vx, Vy, W, ri):
    aux_VelAngular = W * ri
    return (
        Vx - Vy - aux_VelAngular,   # v1 -> M1
        Vx + Vy + aux_VelAngular,   # v2 -> M2
        Vx + Vy - aux_VelAngular,   # v3 -> M3
        Vx - Vy + aux_VelAngular    # v4 -> M4
    )


## @brief Aplica las velocidades especificadas a los cuatro motores encoder del robot.
#  @details Los motores M2 y M4 reciben la velocidad multiplicada por -1 para compensar
#           su orientación física invertida respecto a M1 y M3. De este modo, una misma
#           velocidad lógica produce el movimiento correcto en todos los motores.
#           Esta función no realiza cálculos; solo envía los valores a los drivers.
#  @param v1 Velocidad deseada para el motor M1 (float, rango típico -100 a 100).
#  @param v2 Velocidad deseada para el motor M2 (float, rango típico -100 a 100).
#            Se aplicará con signo invertido al motor físico.
#  @param v3 Velocidad deseada para el motor M3 (float, rango típico -100 a 100).
#  @param v4 Velocidad deseada para el motor M4 (float, rango típico -100 a 100).
#            Se aplicará con signo invertido al motor físico.
#  @return   None
def Vel_Motores(v1, v2, v3, v4):
    encoder_motor_M1.set_speed(v1 *  1)
    encoder_motor_M2.set_speed(v2 * -1)
    encoder_motor_M3.set_speed(v3 *  1)
    encoder_motor_M4.set_speed(v4 * -1)


# Visión y autonomía

## @brief Lee las etiquetas QR de la cámara y decide el movimiento autónomo del robot.
#  @details Consulta los slots 2 y 3 de la cámara (cubos izquierdo y derecho) y
#           aplica la siguiente lógica de decisión:
#           - Si ambos slots devuelven 'Null' -> se asume presencia de 2 conos;
#              el robot avanza 55 unidades hacia la izquierda (tipo 1).
#           - Si las distancias de los slots 2 y 3 son iguales -> los cubos están
#              alineados en un solo bloque; se analiza el slot 1 individualmente:
#              - Si su valor es 2 (máximo posible), se imprime "Agarrar Cubo" y no
#                se realiza movimiento adicional.
#              - En caso contrario, se guarda el valor y la posición del primer cubo,
#                el robot avanza 44 u para posicionarse frente al segundo cubo,
#                se re-lee el QR y se llama a Comparacion_Valores() en modo 1.
#           - Si las distancias son distintas -> los cubos están en posiciones
#              diferentes; se llama directamente a Comparacion_Valores() en modo 0
#              con los datos de los slots 2 y 3.
#  @return None
def Comparacion_QR():
    B1  = 0    # Valor QR del cubo 1
    B2  = 0    # Valor QR del cubo 2
    PC1 = 0    # Posicion lateral del cubo 1 (0=derecha, 1=izquierda)
    PC2 = 0    # Posicion lateral del cubo 2 (0=derecha, 1=izquierda)
    BD1 = 0    # Distancia en pixeles del cubo 1

    cuboIzq = ai_camera_p1.ai_camera_tag_analysis_result_get(2, 1)
    cuboDer = ai_camera_p1.ai_camera_tag_analysis_result_get(3, 1)

    if cuboIzq == 'Null' and cuboDer == 'Null':
        print("2 Conos")
        Mov_Auto(1, 55)
    else:
        dist2 = ai_camera_p1.ai_camera_tag_spatial_attribute_get(2, 1, 1)
        dist3 = ai_camera_p1.ai_camera_tag_spatial_attribute_get(3, 1, 1)

        if dist2 == dist3:
            if ai_camera_p1.ai_camera_tag_analysis_result_get(1, 1) == 2:
                print("Agarrar Cubo")
            else:
                B1  = ai_camera_p1.ai_camera_tag_analysis_result_get(1, 1)
                BD1 = ai_camera_p1.ai_camera_tag_spatial_attribute_get(1, 1, 1)
                if BD1 < 320:
                    PC1 = 1
                Mov_Auto(1, 44)
                time.sleep(30)  # TODO: eliminar en version final
                B2      = ai_camera_p1.ai_camera_tag_analysis_result_get(1, 1)
                dist_b2 = ai_camera_p1.ai_camera_tag_spatial_attribute_get(1, 1, 1)
                if dist_b2 < 320:
                    PC2 = 1
                Comparacion_Valores(B1, BD1, PC1, B2, dist_b2, PC2, 1)
        else:
            Comparacion_Valores(
                ai_camera_p1.ai_camera_tag_analysis_result_get(2, 1),
                ai_camera_p1.ai_camera_tag_spatial_attribute_get(2, 1, 1), 0,
                ai_camera_p1.ai_camera_tag_analysis_result_get(3, 1),
                ai_camera_p1.ai_camera_tag_spatial_attribute_get(3, 1, 1), 0, 0
            )


## @brief Desplaza el robot de forma autónoma en la dirección indicada durante 20 segundos.
#  @details Calcula las velocidades mediante Checar_Velocidades(), reinicia el
#           temporizador interno de novapi y mantiene los motores activos hasta
#           que el temporizador supera los 20 segundos. El parámetro @p distancia
#           está reservado para una futura implementación que escale el tiempo
#           de movimiento; actualmente no afecta el comportamiento.
#           - Tipo 1: movimiento lateral izquierda  (Vy = +1).
#           - Tipo 2: movimiento lateral derecha    (Vy = -1).
#  @param tipo      Entero que indica la dirección de movimiento.
#                   1 = desplazamiento hacia la izquierda.
#                   2 = desplazamiento hacia la derecha.
#                   Cualquier otro valor no produce movimiento.
#  @param distancia Distancia objetivo en centímetros (parámetro reservado,
#                   no utilizado en el cálculo actual del tiempo de movimiento).
#  @return None
def Mov_Auto(tipo, distancia):
    if tipo == 1:
        v1, v2, v3, v4 = Checar_Velocidades(0,  1, 0, 1)
        novapi.reset_timer()
        while novapi.timer() < 20:
            time.sleep(0.001)
            Vel_Motores(v1, v2, v3, v4)
    elif tipo == 2:
        v1, v2, v3, v4 = Checar_Velocidades(0, -1, 0, 1)
        novapi.reset_timer()
        while novapi.timer() < 20:
            time.sleep(0.001)
            Vel_Motores(v1, v2, v3, v4)


## @brief Configura la cámara de IA para detectar y analizar etiquetas QR.
#  @details Realiza la secuencia de inicialización en tres pasos:
#           1. Activa el modo de reconocimiento de etiquetas (switch de función 4).
#           2. Espera 10 segundos para que el hardware de la cámara se estabilice.
#           3. Establece el modo de función de etiqueta en 3 (detección de QR/ArUco)
#              y define el tamaño físico real de las etiquetas en 10 cm, necesario
#              para que la cámara calcule distancias en unidades métricas.
#  @return None
def InicializarTag():
    ai_camera_p1.ai_camera_set_func_switch(4, 1)
    time.sleep(10)
    ai_camera_p1.ai_camera_tag_func_mode_set(3, 1)
    ai_camera_p1.ai_camera_tag_actual_size_set(10, 1)


## @brief Compara los valores QR de dos cubos y mueve el robot hacia el de mayor valor.
#  @details Convierte primero las distancias de píxeles a centímetros dividiendo
#           entre el factor de calibración 16.84 px/cm. Luego, dependiendo del @p modo,
#           aplica una de dos estrategias:
#
#           Modo 1 — Cubos en bloques distintos:
#           - Si Val1 > Val2 -> el cubo 1 es el objetivo. Si está a la izquierda
#             (Pos1 == 1) se invierte Dist1 para moverse en esa dirección.
#             El robot se desplaza (-44 + Dist1) unidades desde el punto de referencia.
#           - Si Val2 >= Val1 -> el cubo 2 es el objetivo. Si está a la izquierda
#             (Pos2 == 1) se invierte Dist2. El robot se desplaza Dist2 unidades.
#
#           Modo 0 — Cubos en el mismo bloque:
#           - Si Val1 > Val2 -> el cubo 1 (izquierda) es el objetivo; Dist1 se
#             invierte y el robot se desplaza esa distancia hacia la izquierda.
#           - Si Val2 >= Val1 -> el cubo 2 (derecha) es el objetivo; el robot se
#             desplaza Dist2 unidades hacia la derecha.
#
#  @param Val1  Valor numérico leído del QR del cubo 1 (entero, mayor = mejor).
#  @param Dist1 Distancia en píxeles desde el punto de referencia de la cámara
#               hasta el QR del cubo 1. Se convierte internamente a centímetros.
#  @param Pos1  Posición lateral del cubo 1 respecto al centro de la imagen.
#               1 = cubo a la izquierda (coordenada X < 320 px).
#               0 = cubo a la derecha  (coordenada X >= 320 px).
#  @param Val2  Valor numérico leído del QR del cubo 2 (entero, mayor = mejor).
#  @param Dist2 Distancia en píxeles desde el punto de referencia de la cámara
#               hasta el QR del cubo 2. Se convierte internamente a centímetros.
#  @param Pos2  Posición lateral del cubo 2 respecto al centro de la imagen.
#               1 = cubo a la izquierda (coordenada X < 320 px).
#               0 = cubo a la derecha  (coordenada X >= 320 px).
#  @param modo  Estrategia de comparación a aplicar.
#               1 = los cubos están en bloques distintos (se usa offset de 44 u).
#               0 = los cubos están en el mismo bloque (desplazamiento directo).
#  @return None
def Comparacion_Valores(Val1, Dist1, Pos1, Val2, Dist2, Pos2, modo):
    Dist1 = Dist1 / 16.84
    Dist2 = Dist2 / 16.84

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


# Griper

## @brief Controla el movimiento vertical del griper (ascenso o descenso).
#  @details Establece la potencia de mov_pot_griper en 50 % y la aplica al
#           canal DC1 de la placa de expansión de potencia. El signo positivo
#           hace ascender el griper y el negativo lo hace descender.
#           La variable global mov_pot_griper se actualiza en cada llamada.
#  @param modo Entero que indica la dirección de movimiento vertical.
#              1              = ascender el griper (potencia positiva en DC1).
#              Cualquier otro = descender el griper (potencia negativa en DC1).
#  @return None
def Mov_Griper(modo):
    global mov_pot_griper
    mov_pot_griper = 50
    if modo == 1:
        while gamepad.is_key_pressed("Up"):
            power_expand_board.set_power("DC1",  mov_pot_griper)
    else:
        while gamepad.is_key_pressed("Down"):
            power_expand_board.set_power("DC1", -mov_pot_griper)
    power_expand_board.set_power("DC1", 0)


## @brief Verifica el estado del smartservo 1 y lo detiene si detecta sobrecarga o bloqueo.
#  @details Espera 300 ms tras el inicio del movimiento para que el servo alcance
#           velocidad estable, luego lee la corriente y la velocidad del smartservo_1.
#           Dependiendo del @p modo, aplica uno de dos criterios de parada:
#           - Modo 1 (apertura): detiene el servo si la corriente supera 900 mA
#             o la velocidad cae por debajo de 2 rpm, lo que indica que las pinzas
#             llegaron al tope mecánico o encontraron resistencia excesiva.
#           - Modo 0 (cierre): detiene el servo si la corriente supera 900 mA
#             o la velocidad sube por encima de -2 rpm (el signo negativo refleja
#             la dirección inversa del cierre), indicando bloqueo o tope mecánico.
#           Al detectar la condición de parada, envía velocidad 0 al servo y espera
#           500 ms para que el mecanismo se estabilice antes de regresar el control.
#  @param modo Entero que indica la dirección de movimiento que se está supervisando.
#              1              = supervisión de apertura de pinzas.
#              Cualquier otro = supervisión de cierre de pinzas.
#  @return None
def ChecarServo(modo):
    time.sleep(0.3)
    Corriente = 0
    Velocidad = 0
    Corriente = smartservo_1.get_value("current")
    Velocidad = smartservo_1.get_value("speed")
    if modo == 1:
        if Corriente > 900 or Velocidad < 2:
            smartservo_1.move(0, 0)
            time.sleep(0.5)
    else:
        if Corriente > 900 or Velocidad > -2:
            smartservo_1.move(0, 0)
            time.sleep(0.5)


## @brief Controla la apertura o el cierre de las pinzas del griper.
#  @details Establece la potencia de aper_pot_griper en 50 % y la aplica al
#           canal DC2 de la placa de expansión de potencia. El signo positivo
#           abre las pinzas y el negativo las cierra.
#           La variable global aper_pot_griper se actualiza en cada llamada.
#  @param modo Entero que indica la acción a realizar sobre las pinzas.
#              1              = abrir las pinzas (potencia positiva en DC2).
#              Cualquier otro = cerrar las pinzas (potencia negativa en DC2).
#  @return None
def Apertura_Griper(modo):
    aper_pot_griper = 80
    if modo == 1:
        while gamepad.is_key_pressed("L1"):
            smartservo_1.set_power(aper_pot_griper)
            ChecarServo(1)
    else:
        while gamepad.is_key_pressed("R1"):
            smartservo_1.set_power(aper_pot_griper * -1)
            ChecarServo(0)
    smartservo_1.set_power(0)


## @brief Ajusta el ángulo del smartservo 2 (brush) mediante el gamepad.
#  @details Incrementa o decrementa la variable global @p ang_pot_brush en pasos
#           de 5 grados mientras la tecla correspondiente permanezca presionada,
#           respetando los límites físicos del mecanismo:
#           - Límite superior: 176 grados (modo 1, tecla "Left").
#           - Límite inferior: 4 grados   (modo 0, tecla "Right").
#           Tras cada paso aplica el nuevo ángulo al servo con una velocidad de
#           movimiento de 20 unidades y espera 300 ms para que el servo alcance
#           la posición antes de leer de nuevo el gamepad, evitando saltos bruscos.
#           La variable global @p ang_pot_brush conserva el ángulo entre llamadas,
#           de modo que el brush retiene su posición al soltar la tecla.
#  @param modo Entero que indica la dirección de ajuste del ángulo.
#              1              = incrementar el ángulo (mover hacia 176°, tecla "Left").
#              Cualquier otro = decrementar el ángulo (mover hacia 4°, tecla "Right").
#  @return None
def Angulo_Brush(modo):
    global ang_pot_brush
    if modo == 1:
      while gamepad.is_key_pressed("Left"):
        if ang_pot_brush < 176:
          ang_pot_brush = (ang_pot_brush + 5)
          smartservo_2.move_to(ang_pot_brush, 20)
          time.sleep(0.3)
    else:
      while gamepad.is_key_pressed("Right"):
        if ang_pot_brush > 4:
          ang_pot_brush = (ang_pot_brush + -5)
          smartservo_2.move_to(ang_pot_brush, 20)
          time.sleep(0.3)


# Lanzador

## @brief Bucle interactivo de control de los motores brushless del lanzador.
#  @details Permite al operador ajustar la potencia de lanzamiento en tiempo real
#           mediante el gamepad mientras el robot está en movimiento. El bucle
#           se ejecuta hasta que el operador presiona N3:
#           - R2 incrementa pot_lanzamiento en 5 unidades (máximo 100).
#           - L2 decrementa pot_lanzamiento en 5 unidades (mínimo -100).
#           - La potencia actualizada se aplica simultáneamente a BL1 y BL2.
#           - N3 establece ambos motores a 0 y sale del bucle.
#           La variable global pot_lanzamiento conserva el último valor entre llamadas,
#           por lo que la función lanzamiento() la pre-inicializa antes de llamar aquí.
#  @return None
def Lanzador():
    global pot_lanzamiento
    bandera = 0
    while not (bandera == 1):
        time.sleep(0.001)
        if gamepad.is_key_pressed("R2"):
            pot_lanzamiento = min(100, pot_lanzamiento + 5)
        if gamepad.is_key_pressed("L2"):
            pot_lanzamiento = max(-100, pot_lanzamiento - 5)

        power_expand_board.set_power("BL1", pot_lanzamiento)
        power_expand_board.set_power("BL2", pot_lanzamiento)

        if gamepad.is_key_pressed("N3"):
            power_expand_board.set_power("BL1", 0)
            power_expand_board.set_power("BL2", 0)
            bandera = 1


# Modos de operación

## @brief Activa el modo autónomo del robot durante un período de 28 segundos.
#  @details Reinicia el temporizador interno de novapi y ejecuta Comparacion_QR()
#           en un bucle continuo mientras el tiempo transcurrido sea menor a 28 s.
#           Al expirar el tiempo, el bucle termina y el control regresa al llamador
#           (normalmente el bucle principal de main()).
#  @return None
def modo_automatico():
    novapi.reset_timer()
    while novapi.timer() < 28:
        Comparacion_QR()


## @brief Prepara e inicia el lanzador de pelotas con una potencia inicial del 20 %.
#  @details Asigna 20 a la variable global pot_lanzamiento como punto de partida
#           seguro (suficiente para girar los motores sin un arranque brusco) y
#           delega el control al bucle interactivo Lanzador().
#  @return None
def lanzamiento():
    global pot_lanzamiento
    pot_lanzamiento = 20
    Lanzador()


# Control del gamepad

## @brief Detiene por completo los motores de tracción del robot.
#  @details Envía velocidad 0 a los cuatro motores encoder (M1–M4), deteniendo
#           cualquier movimiento en curso. No afecta al griper ni al lanzador.
#           Útil como parada de emergencia o al finalizar una secuencia autónoma.
#  @return None
def Reset_Motores():
    encoder_motor_M1.set_speed(0)
    encoder_motor_M2.set_speed(0)
    encoder_motor_M3.set_speed(0)
    encoder_motor_M4.set_speed(0)


## @brief Detecta y devuelve la primera tecla registrada que esté presionada.
#  @details Itera sobre la tupla TECLAS en orden de declaración y consulta
#           el estado de cada tecla al gamepad. Retorna en cuanto encuentra
#           una tecla activa, garantizando un costo O(n) en el peor caso pero
#           O(1) en promedio para la tecla más común. Si ninguna tecla está
#           activa, retorna None para que el llamador no ejecute ninguna acción.
#  @return str  Nombre de la primera tecla presionada (p. ej. "N1", "Up", "L1").
#  @return None Si ninguna de las teclas registradas está presionada en ese instante.
def get_pressed_key():
    for tecla in TECLAS:
        if gamepad.is_key_pressed(tecla):
            return tecla
    return None


## @var acciones_gamepad
#  @brief Diccionario que mapea cada tecla registrada a su función y argumentos.
#  @details Estructura: { "TECLA": (funcion, (arg1, arg2, ...)) }
#           Permite ejecutar cualquier acción en O(1) sin bloques if/elif anidados.
#
#  | Tecla | Función          | Argumento | Efecto                              |
#  |-------|------------------|-----------|-------------------------------------|
#  | N1    | modo_automatico  | —         | Inicia el modo autónomo (28 s)      |
#  | N2    | Reset_Motores    | —         | Detiene los 4 motores de tracción   |
#  | N3    | lanzamiento      | —         | Inicia el lanzador (pot. inicial 20)|
#  | Up    | Mov_Griper       | 1         | Asciende el griper                  |
#  | Down  | Mov_Griper       | 0         | Desciende el griper                 |
#  | L1    | Apertura_Griper  | 1         | Abre las pinzas del griper          |
#  | R1    | Apertura_Griper  | 0         | Cierra las pinzas del griper        |
#  | Left  | Angulo_Brush     | 1         | Ajusta el ángulo del brush          |
#  | Right | Angulo_Brush     | 0         | Ajusta el ángulo del brush          |

acciones_gamepad = {
    "N1":   (modo_automatico,   ()),
    "N2":   (Reset_Motores,     ()),
    "N3":   (lanzamiento,       ()),        ##MODIFICAR
    "Up":   (Mov_Griper,        (1,)),
    "Down": (Mov_Griper,        (0,)),
    "L1":   (Apertura_Griper,   (1,)),
    "R1":   (Apertura_Griper,   (0,)),
    "Left": (Angulo_Brush,      (1,)),
    "Right": (Angulo_Brush,     (0,)),
}


# Bucle principal

## @brief Ciclo principal del control del robot.
#  @details Ejecuta indefinidamente las siguientes operaciones en cada iteración:
#           1. Pausa de 1 ms (time.sleep(0.001)) para evitar rebotes de señal
#              y reducir la carga de CPU al mínimo necesario.
#           2. Consulta get_pressed_key() para detectar teclas activas del gamepad.
#              Si se detecta una tecla registrada en acciones_gamepad, se ejecuta
#              su función asociada con los argumentos definidos.
#           3. Lee los tres ejes del gamepad (Ly, Lx, Rx) para calcular las
#              velocidades omnidireccionales mediante Checar_Velocidades() y las
#              aplica a los motores con Vel_Motores().
#           El control manual de joystick es continuo: opera en paralelo con las
#           acciones de tecla, salvo cuando una acción bloquea el hilo (p. ej.
#           modo_automatico() o Lanzador() tienen sus propios bucles internos).
#  @return None  (bucle infinito; solo termina por interrupción externa)
def main():
    while True:
        time.sleep(0.001)

        tecla = get_pressed_key()
        if tecla in acciones_gamepad:
            funcion, args = acciones_gamepad[tecla]
            funcion(*args)

        v1, v2, v3, v4 = Checar_Velocidades(
            gamepad.get_joystick("Ly"),   # Eje de avance / retroceso
            gamepad.get_joystick("Lx"),   # Eje de desplazamiento lateral
            gamepad.get_joystick("Rx"),   # Eje de giro (rotacion)
            1                             # Factor ri (escala angular)
        )
        Vel_Motores(v1, v2, v3, v4)


# Punto de entrada

time.sleep(30)      # Espera 30 s para que el hardware de la camara se estabilice
InicializarTag()    # Configura la camara para lectura de etiquetas QR
main()              # Inicia el bucle principal de control (bloquea indefinidamente)