# 📋 Plan de Pruebas (Test Plan) - T.A.I.L.S.

Este documento outlinea la estrategia de QA (Aseguramiento de Calidad) para la interfaz T.A.I.L.S., combinando pruebas automatizadas de backend y pruebas exploratorias/manuales de hardware.

## 1. Alcance (Scope)
* **En alcance:** Lógica de guardado/carga JSON, parseo de telemetría serial, validación de la UI, comunicación USB bidireccional, cinemática básica.
* **Fuera de alcance:** Calentamiento de motores físicos, desgaste de engranajes impresos en 3D, consumo de corriente del STM32.

## 2. Casos de Prueba Manuales (Smoke Test)
Ejecutar esta suite antes de fusionar código a la rama `master`.

| ID | Módulo | Caso de Prueba | Pasos de Ejecución | Resultado Esperado (Criterio de Aceptación) |
|---|---|---|---|---|
| `TC-01` | Conexión | Conexión exitosa a STM32 | 1. Conectar cable USB.<br>2. Clic en "Refrescar".<br>3. Seleccionar COM.<br>4. Clic "Conectar". | El botón cambia a "Desconectar", la interfaz se desbloquea, la consola muestra `[INFO] Conectado a COMx`. |
| `TC-02` | UI/Seguridad | Desconexión por cable | 1. Conectar el robot.<br>2. Desconectar el cable USB físicamente. | El software no crashea. Se captura la excepción y se bloquean los botones de la interfaz automáticamente. |
| `TC-03` | Calibración | Secuencia Homing | 1. Clic en "HOME ALL". | Se envía `:-H`. El botón de sistema parpadea en "WAIT". Al terminar, se pone verde y dice "HOME OK". Los LCDs marcan 0,0,0. |
| `TC-04` | Jogging | Restricción de límites | 1. Hacer Home.<br>2. Clic en "X-".<br>3. Llevar cada eje hasta su tope con incremento de 50 pasos. | El LCD X no baja de 0 ni pasa de 580 (Y de 130, Z de 60). Al llegar al tope no se reenvía el comando y la consola avisa `Eje X ya está en su tope`. |
| `TC-14` | Seguridad | Tope articular por firmware | 1. Hacer Home.<br>2. Escribir a mano `:#X999` en la terminal. | El firmware responde `AVISO\|Limite de eje X: pedido 999, recortado a 580` y el brazo frena en 580. Repetir con `:#Y999` y `:#Z999`. |
| `TC-15` | Calibración | LEDs de fin de carrera | 1. Clic en "HOME ALL".<br>2. Mirar los LEDs `X` `Y` `Z` del panel *Finales* durante la secuencia. | Cada LED se enciende en rojo **a medida que su eje toca el final**, no recién al terminar, y queda visible al menos medio segundo. |
| `TC-16` | UI | Destello de WAIT / FINISH | 1. Dar un jog cualquiera en Aprendizaje. | `WAIT / BUSY` **late** mientras el brazo se mueve y, al detenerse, `FINISH` destella y queda encendido. |
| `TC-17` | Ejecución | Nombre del paso en el log | 1. Capturar puntos poniéndoles nombre en la columna `NOMBRE`.<br>2. Guardar, cargar y ejecutar la rutina. | Cada línea del log de ejecución y el rótulo de progreso identifican el paso por su nombre (`Paso 3 · «Tomar pieza» — …`). |
| `TC-18` | UI | Terminal acoplable | 1. Ocultar/mostrar con el botón del app bar.<br>2. Arrastrar la terminal fuera de la ventana y volver a acoplarla.<br>3. Cerrar y reabrir la aplicación. | El botón y la terminal nunca quedan desfasados, la terminal se puede dejar flotando y redimensionar, y al reabrir la app conserva la posición y el tamaño en que se la dejó. |
| `TC-19` | Diagnóstico | Panel de Test en pantalla chica | 1. Abrir **Herramientas → Panel de Test** en un monitor de 1366×768 o con escalado al 125 %. | La ventana entra completa (con barra de desplazamiento si hace falta) y **no** tiene el botón `?` en la barra de título. |
| `TC-05` | Ejecución | Parada de emergencia por software | 1. Cargar rutina y dar Play.<br>2. Clic en "STOP EMERGENCIA". | El robot se detiene al instante (`:-S`) y **engancha el bloqueo**. Aparece la franja roja de alarma bajo el app bar, la barra de progreso vuelve a 0 y el badge de sistema pasa a `E-STOP`. La rutina no continúa ni se puede reanudar con Play. |
| `TC-06` | Seguridad | Paro por botón físico | 1. Cargar rutina y dar Play.<br>2. Pulsar el botón físico de PARO (PB15). | La interfaz lo detecta **por telemetría** (campo `E:1`), sin depender de mensajes de texto: frena su secuencia sola, muestra el banner de alarma y resalta *Rearmar*. |
| `TC-07` | Seguridad | Rearme | 1. Estando en E-STOP, clic en **Rearmar (:-R)** (el del banner o el del panel izquierdo). | Se envía `:-R`, el banner desaparece, el badge vuelve a `WAIT / BUSY` y la consola recuerda recalibrar. El indicador `HOME` queda parpadeando en `REQ. HOMING`. |
| `TC-08` | Calibración | Fallo de homing | 1. Obstruir un eje o desconectar un fin de carrera.<br>2. Clic en "HOME ALL". | La consola detalla el motivo (qué eje y por qué), el indicador `HOME` parpadea mostrando `HOME FALLÓ` y el LED de Home del robot parpadea. |
| `TC-09` | Diagnóstico | Panel de Test | 1. Menú **Herramientas → Panel de Test / Diagnóstico**.<br>2. Prender cada LED y mover cada eje. | Cada LED responde individualmente (`:*L…`) y cada eje se mueve de forma relativa (`:*M…`) sin requerir calibración previa. Durante un E-STOP los comandos `:*` se rechazan. |
| `TC-10` | Ayuda | Comandos del firmware | 1. Menú **Ayuda → Comandos del STM32**.<br>2. Menú **Ayuda → Ejemplo de un comando…** y elegir `V`. | El firmware imprime en la consola la lista completa (`:-?`) y luego el ejemplo puntual (`:-?V`). |
| `TC-11` | Aprendizaje | Integridad de la rutina guardada | 1. Capturar 3 puntos con coordenadas distintas y velocidades distintas.<br>2. Guardar el JSON y abrirlo en un editor. | Cada objeto tiene `x/y/z/g/v` (y `t` si se cargó una espera) con **los valores capturados, sin corrimientos entre campos**. La columna `#` de la tabla numera 1, 2, 3 sin huecos tras borrar una fila. |
| `TC-12` | UI | Atajos de teclado | 1. Con foco en la ventana, pulsar `←` `→` `↑` `↓` `W` `S`.<br>2. Pulsar `Esc`. | Cada tecla produce el mismo movimiento que su botón de jogging. `Esc` dispara la parada de emergencia. |
| `TC-20` | Ejecución | Espera por paso | 1. Capturar 3 puntos y poner `4.0` en la columna `ESPERA s` del segundo.<br>2. Guardar, cargar y ejecutar la rutina con un cronómetro. | Entre el paso 2 y el 3 pasan ~5,5 s (1,5 s de intervalo base + 4 s de espera) contra ~1,5 s entre el 1 y el 2. El log escribe `espera 4 s…` y el panel *Secuencia* muestra `+4s` en ese paso. |
| `TC-21` | Aprendizaje | Espera fuera de rango | 1. Escribir `abc` en una celda `ESPERA s`.<br>2. Escribir `90`. | En los dos casos aparece el aviso *Valor fuera de rango*, la celda vuelve al último valor bueno y la rutina no se corrompe (la espera admite 0 a 60 s). |
| `TC-22` | UI | Rail izquierdo sin terminal | 1. Ocultar la terminal con el botón del app bar.<br>2. Volver a mostrarla.<br>3. Repetir con la ventana en su tamaño mínimo. | Los visores (vista superior y gauge de Z) mantienen su proporción, no queda un bloque de fondo vacío en el rail, el texto de coordenadas se lee completo y **nunca** aparece barra de desplazamiento con la terminal abierta. |
| `TC-13` | UI | Modo Kawaii | 1. Togglear desde el botón del app bar.<br>2. Togglear desde **Ayuda → Modo Kawaii**. | Los iconos aparecen/desaparecen y **ambos controles quedan siempre en el mismo estado** (no se desfasan). |

## 3. Matriz de Entornos
* **OS soportados para pruebas:** Windows 10, Windows 11.
* **Firmware:** STM32 Tails_Firmware_v1.0 (o superior, con telemetría de campo `E:` y comandos `:*` / `:-?`).
* **Interfaz:** v2 "Instrument Dark".

## 4. Nota sobre unidades
Toda la interfaz muestra y envía **pasos**, no grados (salvo los ángulos de la garra).
Al validar posiciones, comparar contra los pasos que reporta la telemetría del firmware.