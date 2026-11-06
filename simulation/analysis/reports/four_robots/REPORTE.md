# Reporte: partido 2 contra 2 con 4 robots y aprendizaje por refuerzo

ROBOTICA 76 · makeX 2026 Storm Breaker · simulación

> **Actualización (6 de noviembre de 2026): leer primero.** Las secciones 1 y 3 son la versión inicial,
> con robots ideales. El Monte Carlo extenso de la sección 0 las reemplaza: el "450 – 360" fue un
> partido favorable con robots ideales, no un resultado típico.

## 0. Monte Carlo extenso (resultados vigentes)

80 partidos de 4 robots (5 enfrentamientos × 16 semillas): cada robot muestreado (motores, deslizamiento,
giroscopio, colocación), objetos a ±5 mm, retardo de piloto 0, 4, 6 u 8 cuadros
(`simulation/analysis/mc_four.py`, figura `../mc_four/mc_four.png`).

| Rojo vs azul | Margen rojo − azul (IC 95 %) | Gana rojo | Rojo | Azul |
| --- | --- | --- | --- | --- |
| 12 vs 12 | +31 ± 75 | 56 % | 329 | 299 |
| 13 vs 12 | +53 ± 65 | 50 % | 371 | 319 |
| **13, X 277.8 vs 12** | **+64 ± 71** | 56 % | 383 | 319 |
| 12 vs 13 | −33 ± 80 | 38 % | 318 | 350 |
| 13, X 277.8 vs 13 | +9 ± 63 | 44 % | 368 | 359 |

Comparaciones pareadas (misma semilla):

| Cambio | Efecto en el margen (IC 95 %) | ¿Se distingue de cero? |
| --- | --- | --- |
| ORDER 13 en vez de 12, azul con 12 (X 277.3) | +22 ± 41 | No |
| ORDER 13 y X 277.8 en vez de 12, azul con 12 | +33 ± 46 | No |
| ORDER 13 y X 277.8 en vez de 12, azul con 13 | +42 ± 37 | Sí, por poco |
| X 277.8 en vez de 277.3 | +11 ± 11 | Apenas |

Lectura: 13 sube la precisión (~213 contra ~131 puntos) y pierde un cono (20 contra 39). Con 16 semillas
el margen no separa las opciones con claridad; 13 con X 277.8 sigue siendo la mejor estimación. El azul
de la tabla usa siempre el mismo plan, y la alianza roja tiene ventaja por el X12 (el azul usa X6 con la
tarjeta de objetos simulada).

Lo que revelaron los robots muestreados:

- **La bandera de nuestro robot falla ~1 de cada 3 veces** (colgada 55 de 80; el gemelo azul 51 de 80):
  la rutina depende de la odometría. La del compañero, guiada por la pose real, cuelga 80 de 80.
- **Precisión muy por debajo de los robots ideales** (7–12 pelotas contra 13–15).
- 13 de 80 partidos tuvieron un robot fuera del campo: 10 del compañero azul a los 191 s, al iniciar la
  etapa final, y 3 de nuestro robot en la rutina de la bandera (x ≈ 277, y ≈ 1170).
- Las fortalezas aún terminan hasta 846 mm desplazadas: los robots con error de posición las empujan más.
- Una semilla no reproduce exactamente un partido (hilos no deterministas).

Fallas corregidas en este Monte Carlo: los retardos 0 y 2 eran el mismo experimento; los partidos
completos usaban robots ideales; el ruido de ±5 mm de los objetos nunca se aplicaba; los robots seguían
activos durante la etapa de modificación y salían del campo por deriva del giroscopio; la fortaleza podía
teletransportarse si un robot entraba a fondo en ella (ahora se mueve a 800 mm/s como máximo). Los
promedios anteriores (388, 410, 415, el bandido y la "confirmación") se obtuvieron sin estas correcciones.

Otros estudios de la tanda:

- **Rutas (65 órdenes × 12 robots, ±5 mm):** X12 válido en todas las que empiezan con él. Mejor en partido
  completo: 143 (447 puntos, robots ideales, 3 corridas), no probada aún con 4 robots. 12 es la más
  segura en el automático (182, peor robot 165); 13 baja a 172 (peor 110).
- **Aprendizaje por refuerzo, 5 semillas:** todas coinciden en bonus + mesa en el automático y dos barridos
  + cono; explotabilidad +14 a +21. No convergen la hora del X ni quién hace las letras.

Timelapse con robots muestreados: `partido_representativo_4_robots.gif`.

## Versión inicial (robots ideales)

Archivos de esta carpeta:

| Archivo | Qué es |
| --- | --- |
| `partido_ganador_4_robots.gif` | Timelapse del partido ganador (280 s en 20 s, 1 cuadro por segundo) |
| `partido_ganador_4_robots.txt` | Registro completo de los 4 pilotos y puntaje final del mismo partido |
| `../rl_four/bandit.png` | Primera corrida del bandido UCB sobre partidos detallados de 4 robots |
| `../rl_strategy*/` | Aprendizaje por refuerzo en el juego 2 contra 2 (curva, márgenes, política) |
| `../summary/summary.png` | Resumen de todas las simulaciones |

## 1. Resultado

**Partido ganador: ROJO 450 – AZUL 360 (+90), sin penalizaciones ni contactos entre robots.**

Configuración ganadora de nuestra alianza (roja):

| Robot | Automático | Manual | Final |
| --- | --- | --- | --- |
| Nuestro (abajo, Red Start 1) | `ORDER 13`: X12 al área de intercambio y pelotas del nivel bajo de la mesa central, que dispara antes de estacionarse | 2 barridos del área de recursos 1 con tiro, colgar el cono b | Cubos K y E a los canales 3 y 4, bandera en el poste 2, 2 pelotas al X a los 277.8 s |
| Compañero (arriba, Red Start 2) | Se queda en su área (`ORDER 0`) | 3 barridos del área de recursos 2 con tiro | Bandera en el poste 1, 2 pelotas al X a los 277.8 s |

Desglose del partido ganador:

| Rubro | Rojo | Azul |
| --- | --- | --- |
| Precisión (pelotas en la fortaleza rival) | 270 (15 pelotas, 12 a 20 por el X12) | 130 (7 pelotas, 6 a 20 por el X6) |
| Cubo de bonus válido | X12 | X6 |
| Conos colgados | 20 | 40 |
| Cubos de letras | 60 | 60 |
| Banderas | 100 (las 2) | 100 (las 2) |
| X | 0 | 30 |
| Penalizaciones | 0 | 0 |
| **Total** | **450** | **360** |

## 2. Cómo se simuló el partido

Cuatro robots idénticos (v22 con el elevador propuesto de 430 mm) en el mismo simulador detallado
(física de pelotas, objetos, fortalezas móviles, X, reglas R06, R19, R26, colisiones):

| Robot | Programa | Piloto | Salida |
| --- | --- | --- | --- |
| Rojo abajo (nuestro) | `storm_breaker_2026.py` | `ai_driver.py` | Red Start 1 |
| Rojo arriba (compañero) | el mismo programa con `START_Y 2730`, `ORDER 0` | `partner_driver.py` | Red Start 2 |
| Azul arriba | nuestro robot girado 180° (la cancha es simétrica bajo ese giro, y el giro conserva el lado de la pinza) | `ai_driver.py` | Blue Start 2 |
| Azul abajo | el compañero girado 180° | `partner_driver.py` | Blue Start 1 |

Cada robot abajo se enfrenta al robot abajo de la otra alianza en el área de estrategia inferior y
en la mesa central. Comparten pelotas, objetos, el X y las dos fortalezas. El compañero no puede usar
nuestras rutinas reflejadas (la pinza quedaría del lado contrario), así que juega lo que no necesita
pinza: pelotas, bandera y X.

## 3. Aprendizaje por refuerzo

1. **Juego 2 contra 2 a nivel de misiones** (`strategy_game.py`, ~0.1 ms por partido), calibrado con
   las simulaciones detalladas. Incluye la carrera por los cubos de bonus (tarjeta de objetos al azar;
   más de 2 cubos de un lado anulan todos), la mesa central, conos, el X y las fortalezas móviles.
2. **Autojuego con gradiente de política** (`rl_strategy.py`): 192 000 partidos sobre ~28 millones de
   planes de alianza, contra versiones pasadas de la política y 6 estilos de rival. Política aprendida
   (puntería adaptativa): los dos robots con bonus y luego pelotas de la mesa, 2 barridos y cono, letras,
   bandera y X. Gana a los 6 estilos (+167 a +609, 85–100 % de victorias) y un rival entrenado contra
   ella gana solo +20.
3. **Bandido UCB sobre partidos detallados de 4 robots** (`rl_four.py`): prueba configuraciones de
   nuestra alianza propuestas por esa política contra el azul con el plan actual.

Confirmación final (después de las correcciones del punto 5), 3 partidos de 4 robots por opción:

| Opción de nuestra alianza | Margen promedio | Peor partido |
| --- | --- | --- |
| **ORDER 13, X a los 277.8 s** | **+76.7** | **+50** |
| ORDER 13, X a los 277.3 s | +73.3 | +40 |
| Plan anterior: ORDER 12, X a los 277.3 s | +73.3 | +20 |

La ventaja de ORDER 13 en partido detallado es pequeña (+3, y un peor caso mejor): la simulación de un
partido varía ±50 puntos según cómo rebotan las pelotas en la fortaleza.

## 4. Reglas que limitan las estrategias

- **Bloquear no se permite.** R27: "Robots may not obstruct or restrict the movement of opposing
  alliance robots or prevent them from interacting with field elements" (−20, luego −120). R06 mantiene
  a cada robot en su campo. No se modeló.
- **Negar recursos sí:** traer a nuestro lado objetos y pelotas centrales (R23 solo prohíbe mandarlos al
  campo contrario).
- **Mover nuestra fortaleza sí** (pág. 25), sin inclinarla (R02) ni sacar pelotas anotadas (R25). Un
  árbitro podría verlo como R27: consultar antes de usarlo.
- **X:** sin tocarlo (R24); cuenta el último golpe antes del final.

## 5. Problemas que encontró la simulación y se corrigieron

| Problema | Corrección |
| --- | --- |
| ORDER 13 recibía −20 por R19: la cabeza seguía subiendo a los 30 s (el estacionamiento esperaba sin límite) | El automático corta los mecanismos a los 29.5 s y `park()` espera la cabeza solo hasta los 28.5 s |
| Con ORDER 13 el piloto empujaba el cono b fuera del alcance de la pinza al salir del estacionamiento | Sale primero hacia el oeste |
| La pasada a la mesa podía arrastrar el cono b | Rodea por (1450, 1200) |
| El compañero tocaba el poste de conos 1 al colgar la bandera | Llega a x 336 (traslape de 32 mm sobre el poste, se necesitan 30) |
| El compañero rozaba una pata del área de recursos 2 | Punto de paso (900, 2300) |
| El compañero terminaba el manual a los 57 s | Tercer barrido |

## 6. Hallazgos para el equipo

1. **Puntería adaptativa** (botones de corrección o cámara). Es la mejora más valiosa: nuestro programa
   apunta a coordenadas fijas, y una fortaleza movida 150 mm deja nuestros tiros en 0 (simulación
   detallada: 10 de 13 sin mover, 0 de 13 a 150 mm al norte o al este). Con dos robots, cuando el azul
   movió su fortaleza nuestra precisión bajó de 240 a 140.
2. **Automático `ORDER 13`** (X12 y luego pelotas de la mesa): también fue la mejor ruta en el Monte
   Carlo detallado de un robot (443 puntos).
3. **Que el compañero también tome un cubo de bonus** de su mitad (máximo 2 de nuestro lado). En este
   partido el compañero no tiene rutina de automático, así que no se probó.
4. **El X lo gana el azul en todas las corridas de 4 robots**, aunque disparemos a los 277.8 s: con los 4
   robots disparando, la última pelota que llega es azul por la geometría de sus puntos de tiro. Opciones:
   disparar desde más cerca o más tarde (riesgo: que la pelota no llegue antes de los 280 s).
5. **Mover nuestra fortaleza solo funciona hacia el sur** (lo puede hacer el compañero desde su mitad):
   hacia el norte no saca los tiros azules de la zona y nos deja sin las letras K y E.

## 7. Límites de esta simulación

- Los 4 robots son idénticos al v22: nadie alcanza los pines ni completa MAKE. El compañero no tiene
  automático ni rutinas de pinza.
- El rival azul usa nuestro mismo plan girado; un rival real tendrá otro robot y otro piloto.
- El juego 2 contra 2 es un modelo calibrado, no física; la validación detallada se hizo con el bandido
  y los partidos de 4 robots (12 partidos de confirmación en total).
- El ganador sigue rozando el área de pines al colgar la bandera (267 s, rutina del programa, x 322).

## 8. Cómo repetirlo

```bash
.venv/bin/python simulation/analysis/four_robots.py --red 13 --blue 12
.venv/bin/python simulation/analysis/rl_strategy.py --opp-aim adaptive --our-aim adaptive --tag robust
.venv/bin/python simulation/analysis/rl_four.py --rounds 4
cd simulation/field3d && ../../.venv/bin/python timelapse4.py --red 13 --red-options '{"main": {"x_fire_at": 277.8}, "partner": {"x_fire_at": 277.8}}' --out ganador.gif
```
