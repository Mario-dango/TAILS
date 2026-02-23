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
| `TC-04` | Jogging | Restricción de límites | 1. Hacer Home.<br>2. Clic en "X-" | El comando no se envía o se limita a 0 (si la lógica prohíbe valores negativos). El LCD X no baja de 0. |
| `TC-05` | Ejecución | Parada de Emergencia | 1. Cargar rutina y dar Play.<br>2. Clic en "STOP EMERGENCIA". | El robot se detiene instantáneamente (`:-S`). La barra de progreso se reinicia a 0. La rutina no continúa. |

## 3. Matriz de Entornos
* **OS soportados para pruebas:** Windows 10, Windows 11.
* **Firmware:** STM32 Tails_Firmware_v1.0 (o superior).