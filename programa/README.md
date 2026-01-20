# 🤖 Firmware Brazo Robótico 4-DOF (STM32 BluePill)

Este proyecto implementa el firmware de control para un brazo robótico de 4 grados de libertad (3 ejes cartesianos + 1 Gripper). El sistema corre sobre un **STM32F103C8T6 (BluePill)**, utilizando una arquitectura modular por capas sobre HAL.

El sistema destaca por incluir generación de pasos por interrupción (20kHz), control de velocidad con **rampas de aceleración trapezoidal** en tiempo real y comunicación USB-CDC robusta.

---

## 📂 Arquitectura del Proyecto

El código se organiza separando la lógica de negocio (Robot), el control de hardware (Drivers) y la comunicación.

| Módulo (`.c/.h`) | Descripción Técnica |
| :--- | :--- |
| **`main`** | Inicialización de HAL, bucle infinito `while(1)` y orquestación de tareas de fondo (LCD, Polling). |
| **`robot_logic`** | **Cerebro.** Máquina de estados que interpreta comandos ASCII (`:#`, `:-`), gestiona modos (Calibración/Ejecución) y telemetría. |
| **`motor_driver`** | **Cinemática.** Gestión de motores paso a paso. Incluye la lógica de **Rampas Trapezoidales** (`CalculateSpeed`), generación de pulsos en interrupción y Homing. |
| **`gripper_driver`** | **Efector Final.** Abstracción para el control del servo SG90 mediante PWM (TIM4). |
| **`comm_manager`** | **Comunicaciones.** Wrapper para transmisión USB segura y utilidades de parseo de texto (`atoi`, `substring`). |
| **`stm32f1xx_it`** | **Interrupciones.** Manejo de IRQs de Timers y EXTI (Sensores y E-STOP). |

---

## 🔌 Configuración de Hardware (Pinout)

### ⚡ Motores Paso a Paso (Drivers A4988)
Configurados en modo **Full Step** (sin microstepping).

| Eje | Pin STEP | Pin DIR | Timer / Frecuencia |
| :--- | :--- | :--- | :--- |
| **X** | `PA0` | `PA3` | TIM2 (20 kHz) |
| **Y** | `PA1` | `PA4` | TIM2 (20 kHz) |
| **Z** | `PA2` | `PA5` | TIM2 (20 kHz) |
| **Enable**| `PB8` | - | Activo en BAJO (Lógica negativa) |

### 🛑 Sensores y Seguridad (Input Pull-Up)
Todos los sensores funcionan por interrupción externa (`EXTI`) para respuesta inmediata.

| Función | Pin | Interrupción |
| :--- | :--- | :--- |
| **Fin de Carrera X** | `PB12` | EXTI Line 12 |
| **Fin de Carrera Y** | `PB13` | EXTI Line 13 |
| **Fin de Carrera Z** | `PB14` | EXTI Line 14 |
| **E-STOP (Emergencia)**| `PB15` | EXTI Line 15 (Prioridad Máxima) |

### 📟 Periféricos Adicionales
* **Servo (Gripper):** `PB9` (TIM4 CH4 - PWM 50Hz).
* **LCD I2C:** `PB6` (SCL), `PB7` (SDA) - Dirección `0x4E` (o `0x27`).
* **LEDs Estado:** `PB3` (Home), `PB4` (Finish), `PB5` (Wait).
* **USB:** `PA11` (DM), `PA12` (DP) - Virtual COM Port.

---

## ⏱️ Configuración de Timers y Física

### TIM2: Generador de Pasos (Step Engine)
* **Prescaler:** 71, **Period:** 49 -> **20,000 Hz**.
* Es el "metrónomo" del sistema. Cada 50µs verifica si un motor debe dar un paso.
* **Control de Velocidad:** No se cambia la frecuencia del timer. Se calcula dinámicamente cuántos "ticks" de 50µs deben pasar entre paso y paso (`stepInterval`).

### TIM3: Watchdog de Software
* **Frecuencia:** 1 Hz (1 segundo).
* Se usa durante el **Homing** para abortar la operación si un sensor no se activa en 15 segundos.

### TIM4: PWM Servo
* **Frecuencia:** 50 Hz (Periodo 20ms).
* Controla el ancho de pulso del servo (550µs a 2450µs).

---

## 📡 Protocolo de Comunicación USB

El robot se conecta como un puerto serie virtual (COMx). Velocidad indiferente (CDC).
Los comandos deben terminar con `\r\n` o `\n`.

### 1. Comandos de Configuración (`:-`)

| Comando | Acción | Descripción |
| :--- | :--- | :--- |
| `:-H` | **Homing** | Inicia secuencia de calibración (X -> Y -> Z). Bloqueante. |
| `:-Z` | **Set Zero** | Establece la posición actual como el origen (0,0,0). |
| `:-V[val]` | **Set Speed** | Define velocidad máxima global en % (10-100). Ej: `:-V050`. |
| `:-E[1/0]` | **Enable** | `1` Energiza motores, `0` libera el eje. Ej: `:-E1`. |
| `:-A[ang]` | **Config Open** | Define ángulo de apertura de garra. Ej: `:-A120`. |
| `:-P[ang]` | **Config Close**| Define ángulo de cierre de garra. Ej: `:-P090`. |
| `:-S` | **STOP** | Parada de emergencia por software. |

### 2. Comandos de Movimiento (`:#`)

Formato: `:#X[pasos]Y[pasos]Z[pasos][C/A]`
* Se pueden enviar ejes individuales o combinados.
* `C`: Cierra la garra al finalizar.
* `A`: Abre la garra al finalizar.

**Ejemplos:**
* `:#X200` -> Mueve X a la posición absoluta 200.
* `:#X100Y100Z50C` -> Mueve los 3 ejes y cierra la garra.

### 3. Telemetría (Respuesta Automática)

El robot envía su estado cada 50ms (solo si hubo cambios).
Formato: `STATUS|X:000|Y:000|Z:000|S:000|C:1|M:0`

* **X, Y, Z:** Posición actual en pasos.
* **S:** Estado Sensores (Binario `0ZYX`, 1=Activado).
* **C:** Calibrado (1=Sí, 0=No).
* **M:** En Movimiento (1=Sí, 0=No).

---

## 🚀 Características de Control de Movimiento

El firmware implementa un perfil de velocidad **Trapezoidal** en tiempo real:

1.  **Fase de Aceleración:** La velocidad aumenta linealmente (`accelRate`) desde `minVelocity` hasta `targetVelocity`.
2.  **Fase de Crucero:** Mantiene la velocidad objetivo.
3.  **Fase de Desaceleración:** Calcula la distancia de frenado y reduce la velocidad para llegar al destino exactamente a `minVelocity`.

Esto previene la pérdida de pasos y vibraciones mecánicas al iniciar movimientos rápidos.
