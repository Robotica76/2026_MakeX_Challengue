import novapi
from mbuild.encoder_motor import encoder_motor_class
from mbuild.ai_camera import ai_camera_class
from mbuild import power_expand_board
from mbuild import gamepad
import time

# Initialization of variables global
pot_lanzamiento = 0       # Variable para controlar la potencia del lanzamiento   
aper_pot_griper = 0       # Variable para apertura la potencia del griper  
mov_pot_griper = 0        # Variable para controlar la potencia del movimiento del griper  
bandera = 0               # Variable para controlar el bucle del lanzamiento

# Declaracion de los motores y camara
encoder_motor_M1 = encoder_motor_class("M1", "INDEX1")    # Motor 1, puerto M1, indice 1
encoder_motor_M2 = encoder_motor_class("M2", "INDEX1")    # Motor 2, puerto M2, indice 1
encoder_motor_M3 = encoder_motor_class("M3", "INDEX1")    # Motor 3, puerto M3, indice 1
encoder_motor_M4 = encoder_motor_class("M4", "INDEX1")    # Motor 4, puerto M4, indice 1
ai_camera_p1 = ai_camera_class("PORT3", "INDEX1")         # Camara, puerto PORT3, indice 1

# Teclas registradas del control que activan una acción
TECLAS = ("N1", "N2", "N3", "Up", "Down", "L1", "R1")

def Checar_Velocidades(Vx, Vy, W, ri):                    # Funcion (ecuacion) para calcular la velocidad de los motores
    aux_VelAngular = W * ri                               # Variable auxiliar para la velocidad angular
    return Vx - Vy - aux_VelAngular, Vx + Vy + aux_VelAngular, Vx + Vy - aux_VelAngular, Vx - Vy + aux_VelAngular   #Retorna el calculo de la velocidad de los motores M1, M2, M3 y M4

def Vel_Motores(v1, v2, v3, v4):                          # Funcion para asignar la velocidad a los motores
    encoder_motor_M1.set_speed(v1 * 1)                    # Asignar la velocidad al motor M1
    encoder_motor_M2.set_speed(v2 * -1)                   # Asignar la velocidad al motor M2
    encoder_motor_M3.set_speed(v3 * 1)                    # Asignar la velocidad al motor M3    
    encoder_motor_M4.set_speed(v4 * -1)                   # Asignar la velocidad al motor M4  

def Comparacion_QR():                                     # Funcion para comparar los valores de los QR y tomar decisiones
    B1 = 0                                                # Variable para almacenar el valor del QR del bloque 1
    B2 = 0                                                # Variable para almacenar el valor del QR del bloque 2                  
    PC1 = 0                                               # Variable para almacenar la posicion del QR del bloque 1
    PC2 = 0                                               # Variable para almacenar la posicion del QR del bloque 2            
    BD1 = 0                                               # Variable para almacenar la distancia del QR del bloque 1 (Del punto de referencia al QR)
    cuboIzq = ai_camera_p1.ai_camera_tag_analysis_result_get(2, 1)  # Variable para almacenar el valor del QR del bloque izquierdo
    cuboDer = ai_camera_p1.ai_camera_tag_analysis_result_get(3, 1)  # Variable para almacenar el valor del QR del bloque derecho
    if cuboIzq == 'Null' and cuboDer == 'Null':           # Si no hay QR detectados, se asume que hay 2 conos
      print("2 Conos")
      Mov_Auto(1, 55)                                     # Mover el robot hacia el ultimo cubo, con más probabilidad de obtener el cubo con mayor valor
    else:
      if ai_camera_p1.ai_camera_tag_spatial_attribute_get(2, 1, 1) == ai_camera_p1.ai_camera_tag_spatial_attribute_get(3, 1, 1):  # Si los QR detectados están a la misma distancia, se asume que hay 1 cubo
        if ai_camera_p1.ai_camera_tag_analysis_result_get(1, 1) == 2:         # Si el valor del QR detectado es 12, loa agrra ya que es del de mayor valor
          print("Agarrar Cubo")
        else:
          B1 = ai_camera_p1.ai_camera_tag_analysis_result_get(1, 1)           # Variable para almacenar el valor del QR del bloque 1
          BD1 = ai_camera_p1.ai_camera_tag_spatial_attribute_get(1, 1, 1)     # Variable para almacenar la distancia del QR del bloque 1 (Del punto de referencia al QR)
          if ai_camera_p1.ai_camera_tag_spatial_attribute_get(1, 1, 1) < 320: # Si la distancia del QR del bloque 1 es menor a 320, se asume que está a la izquierda
            PC1 = 1                                                           # Variable para almacenar la posicion del QR del bloque 1
          Mov_Auto(1, 44)                                                     # Se mueve el robot hasta el bloque 2, para seguir con la comparacion
          time.sleep(30) # QUITAR
          B2 = ai_camera_p1.ai_camera_tag_analysis_result_get(1, 1)           # Variable para almacenar el valor del QR del bloque 2
          if ai_camera_p1.ai_camera_tag_spatial_attribute_get(1, 1, 1) < 320: # Si la distancia del QR del bloque 2 es menor a 320, se asume que está a la izquierda
            PC2 = 1                                                           # Variable para almacenar la posicion del QR del bloque 2
          Comparacion_Valores(B1, BD1, PC1, B2, ai_camera_p1.ai_camera_tag_spatial_attribute_get(1, 1, 1), PC2, 1)  # Se llama a la funcion Comparacion_Valores para comparar los valores de los QR y tomar decisiones
      else:
        Comparacion_Valores(ai_camera_p1.ai_camera_tag_analysis_result_get(2, 1), ai_camera_p1.ai_camera_tag_spatial_attribute_get(2, 1, 1), 0, ai_camera_p1.ai_camera_tag_analysis_result_get(3, 1), ai_camera_p1.ai_camera_tag_spatial_attribute_get(3, 1, 1), 0, 0) # Se llama a la funcion Comparacion_Valores para comparar los valores de los QR y tomar decisiones (Se ausme que esyan en el mismo bloque)

def Mov_Auto(tipo, distancia):                            # Funcion para mover el robot de manera automatica, dependiendo del tipo de movimiento y la distancia a recorrer
    # Con la DISTANCIA obtener la velocidad de los motores y el tiempo que se debe de mover
    if tipo == 1:                                         # Si el tipo de movimiento es 1, se asume que es un movimiento hacia izquierda
      v1, v2, v3, v4 = Checar_Velocidades(0, 1, 0, 1)     # Se obtiene la velocidad de los motores para el movimiento hacia izquierda
      novapi.reset_timer()                                # Se reinicia el timer para medir el tiempo que se debe de mover
      while novapi.timer() < 20:                          # Se mide el tiempo que se debe de mover, en este caso 20 segundos
          time.sleep(0.001)                               # Se espera 1 milisegundo para evitar que el programa se congele
          Vel_Motores(v1, v2, v3, v4)                     # Se asigna la velocidad a los motores para el movimiento hacia izquierda
    elif tipo == 2:                                       # Si el tipo de movimiento es 2, se asume que es un movimiento hacia derecha             
      v1, v2, v3, v4 = Checar_Velocidades(0, -1, 0, 1)    # Se obtiene la velocidad de los motores para el movimiento hacia derecha
      novapi.reset_timer()                                # Se reinicia el timer para medir el tiempo que se debe de mover        
      while  novapi.timer() < 20:                         # Se mide el tiempo que se debe de mover, en este caso 20 segundos
          time.sleep(0.001)                               # Se espera 1 milisegundo para evitar que el programa se congele       
          Vel_Motores(v1, v2, v3, v4)                     # Se asigna la velocidad a los motores para el movimiento hacia derecha

def InicializarTag():                                     # Funcion para inicializar la camara
    ai_camera_p1.ai_camera_set_func_switch(4, 1)          # Se activa la funcion de reconocimiento de etiquetas
    time.sleep(10)                                        # Se espera 10 segundos para que la camara se inicialice
    ai_camera_p1.ai_camera_tag_func_mode_set(3, 1)        # Se activa la funcion de deteccion de QR
    ai_camera_p1.ai_camera_tag_actual_size_set(10, 1)     # Se establece el tamaño actual de los QR a 10 cm

def Comparacion_Valores(Val1, Dist1, Pos1, Val2, Dist2, Pos2, modo):    # Funcion para comparar los valores de los QR y tomar decisiones dependiendo del modo de comparacion
    Dist1 = Dist1 / 16.84   # Dist1 esta en pixeles y se divide entre 16.84 para obtener la distancia en cm
    Dist2 = Dist2 / 16.84   # Dist2 esta en pixeles y se divide entre 16.84 para obtener la distancia en cm
    if modo == 1:                                         # Si el modo de comparacion es 1, se asume que hay 2 bloques de QR y se comparan los valores de los QR de cada bloque
      if Val1 > Val2:                                     # Si el valor del QR del bloque 1 es mayor que el valor del QR del bloque 2, se asume que el bloque 1 es el de mayor valor
        if Pos1 == 1:                                     # Si la posicion del QR del bloque 1 es a la izquierda
          Dist1 = Dist1 * -1                              # Se multiplica la distancia por -1 para que el robot se mueva hacia la izquierda
        print("2 CUBO IZQ")
        Mov_Auto(1, (-44 + Dist1))                        # Se mueve el robot hacia el bloque 1, con la distancia calculada (del punto de referencia al otro de referencia con la ditancia de se punto al QR)
      else:                                               # Si el valor del QR del bloque 2 es mayor que el valor del QR del bloque 1, se asume que el bloque 2 es el de mayor valor
        if Pos2 == 1:                                     # Si la posicion del QR del bloque 2 es a la izquierda    
            Dist2 = Dist2 * -1                            # Se multiplica la distancia por -1 para que el robot se mueva hacia la izquierda          
        print("2 CUBO DER")
        Mov_Auto(1, Dist2)                                # Se mueve el robot con la distancia calculada (del punto de referencia a la distancia del QR)
    else:                                                 # Si el modo de comparacion es 0, se asume que hay 2 cubos en el mismo bloque y se comparan los valores de los QR de cada cubo
      if Val1 > Val2:                                     # Si el valor del QR del cubo 1 es mayor que el valor del QR del cubo 2, se asume que el cubo 1 es el de mayor valor  
        Dist1 = Dist1 * -1                                # Se multiplica la distancia por -1 para que el robot se mueva hacia la izquierda (ya que el mayor es el cubo de la izquierda)
        print("3 IZQ")
        Mov_Auto(1, Dist1)                                # Se mueve el robot con la distancia calculada (del punto de referencia a la distancia del cubo)
      else:                                               # Si el valor del QR del cubo 2 es mayor que el valor del QR del cubo 1, se asume que el cubo 2 es el de mayor valor
        print("3 DER")
        Mov_Auto(1, Dist2)                                # Se mueve el robot con la distancia calculada (del punto de referencia a la distancia del cubo (derecha))                

def Mov_Griper(modo):                                     # Funcion que asciende y desciende el griper
    global mov_pot_griper
    mov_pot_griper = 50                                   # Se inicializa la potencia del griper al 50%
    if modo == 1:                                         # Si modo es igual a 1, el griper ascendera, en caso contrario, descendera  
      power_expand_board.set_power("DC1", mov_pot_griper)
    else:
      power_expand_board.set_power("DC1", mov_pot_griper * -1)

def Reset_Motores():        #funcion que restaura la velocidad de todos los motores en 0
    encoder_motor_M1.set_speed(0)
    encoder_motor_M2.set_speed(0)
    encoder_motor_M3.set_speed(0)
    encoder_motor_M4.set_speed(0)

def Apertura_Griper(modo):  #funcion que apertura o cierra el griper
    global aper_pot_griper
    aper_pot_griper = 50    #Se inicializa la potencia del griper al 50%
    if modo == 1:           #Si modo es igual a 1, el griper se abrira, en caso contrario, se cerrara
      power_expand_board.set_power("DC2", aper_pot_griper)
    else:
      power_expand_board.set_power("DC2", aper_pot_griper * -1)

def Lanzador():      #funcion que activa los motores brushles para el lanzamiento de pelotas
                     #R2 aumenta la potencia, L2 disminuye la potencia y N3 detiene los motores y sale del ciclo  
    global pot_lanzamiento
    bandera = 0          
    while not (bandera == 1):
        time.sleep(0.001)                     # Evitar el rebote de los botones
        if gamepad.is_key_pressed("R2"):
          pot_lanzamiento = min(100, pot_lanzamiento + 5)  #sube la potencia del motor en 5, con un maximo de 100

        if gamepad.is_key_pressed("L2"):
          pot_lanzamiento = max(-100, pot_lanzamiento - 5) #baja la potencia del motor en 5, con un minimo de -100

        power_expand_board.set_power("BL1", pot_lanzamiento) #aplica la potencia al motor 1
        power_expand_board.set_power("BL2", pot_lanzamiento) #aplica la potencia al motor 2

        if gamepad.is_key_pressed("N3"):              #apaga los motores del lanzador y terminar el ciclo
          power_expand_board.set_power("BL1", 0)
          power_expand_board.set_power("BL2", 0)
          bandera = 1 

def modo_automatico():   # funcion del modo autónomo:durante 28 segundos busca y compara los tags QR con la camara
   novapi.reset_timer()   #reinicia el temporizador 
   while novapi.timer() < 28: #todo se repite durante 28 segundos
     Comparacion_QR()    #activa a comparacion de los tags de la camara

def lanzamiento():      #prepara el motor brushles con potencia inicial de 20
   global pot_lanzamiento
   pot_lanzamiento = 20
   Lanzador()           #manda los datos a la funcion lanzador
   
def get_pressed_key():    #funcion que obtiene el boton presionado
    for tecla in TECLAS:  #recorre cada tecla registrada
        if gamepad.is_key_pressed(tecla):
            return tecla  #regresa la tecla que esta presionada 
    return None           #En caso de que ninguna tecla este presionada 

# Diccionario que guarda cada funcion a ejecutar 
acciones_gamepad = {
    "N1": (modo_automatico,   ()),      #N1: modo autonomo
    "N2": (Reset_Motores,     ()),      #N2: Resetea los motores de la llanta
    "N3": (lanzamiento,       ()),      #N3: Activa el lanzador
    "Up":   (Mov_Griper,      (1,)),    #Cruceta arriba: Asciende el griper
    "Down": (Mov_Griper,      (0,)),    #Cruceta abajo: Desciende el griper 
    "L1":   (Apertura_Griper, (1,)),    #L1: abre el griper
    "R1":   (Apertura_Griper, (0,)),    #R1: cierra el griper
}

def main():
    #ciclo principal que controla el movimiento del robot y lee el control
    while True:
        time.sleep(0.001)                   #Evita el rebote de la señal del control

        tecla = get_pressed_key()          # O(n) aquí, una sola vez, busca la tecla que esta presionada 
        if tecla in acciones_gamepad:      # O(1) real
            funcion, args = acciones_gamepad[tecla]
            funcion(*args)                 #ejecuta la funcion correspondiente a la tecla asignada junto con sus argumentos

        v1, v2, v3, v4 = Checar_Velocidades(  #se obtiene le movimiento a partir del joystick
            gamepad.get_joystick("Ly"), #moviento de avance/retroceso
            gamepad.get_joystick("Lx"), #movimiento lateral(izquierda/derecha)
            gamepad.get_joystick("Rx"), #giro
            1
        )
        Vel_Motores(v1,v2,v3,v4)

time.sleep(30)  #Inicializacion de la camara
InicializarTag() #configura la camara para poder leer los tags
main()   #inicializa el ciclo principal