# Reporte: partido 2 contra 2 con 4 robots y aprendizaje por refuerzo

ROBOTICA 76 · makeX 2026 Storm Breaker · simulación (5 de noviembre de 2026)

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
