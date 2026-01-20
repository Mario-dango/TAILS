# 🤖 Firmware Brazo Robótico 4-DOF (STM32 BluePill)

Este documento detalla la arquitectura, lógica y configuración del firmware para el controlador del brazo robótico de 4 grados de libertad (3 ejes cartesianos + 1 Gripper). El sistema corre sobre un **STM32F103C8T6 (BluePill)** utilizando **STM32CubeIDE** y la librería **HAL**.

---

## 📂 Arquitectura de Archivos

El proyecto sigue una estructura modular donde se separa la lógica de negocio, el control de hardware y la comunicación.

### 📁 Core/Src & Core/Inc

| Archivo | Propósito / Alcance |
| :--- | :--- |
| **`main.c` / `.h`** | **Punto de Entrada.** Configuración inicial de periféricos (HAL_Init), bucle infinito (`while(1)`), instanciación de variables globales y orquestación entre USB y Motores. |
| **`robot_logic.c` / `.h`** | **Cerebro del Robot.** Interpreta los comandos ASCII recibidos, gestiona la máquina de estados (Calibración, Aprendizaje, Ejecución) y controla la telemetría automática. |
| **`motor_driver.c` / `.h`** | **Control de Movimiento (Paso a Paso).** Contiene la lógica matemática para generar pulsos, rampas (si aplica), rutinas de *Homing* y gestión de interrupciones de temporizadores para los pasos. |
| **`gripper_driver.c` / `.h`** | **Control del Efector Final.** Maneja el servo mediante PWM. Abstrae los ángulos físicos a comandos lógicos (`Open`/`Close`). |
| **`comm_manager.c` / `.h`** | **Gestor de Comunicación.** Wrapper para la transmisión USB (CDC) segura y funciones de utilidad para parseo de cadenas (substrings, atoi). |
| **`stm32f1xx_it.c` / `.h`** | **Interrupciones.** Manejadores de interrupciones de hardware (IRQ Handlers) para Timers y Pines EXTI (Fines de carrera/Emergencia). |
| **`lcd_i2c.c` / `.h`** | **Driver de Pantalla.** Librería de bajo nivel para controlar el LCD 16x2/20x4 mediante el bus I2C. |
| **`robot_defines.h`** | **Definiciones Globales.** Contiene las estructuras de datos principales (`StepperMotor`) y constantes del sistema. |

---

## ⚙️ Métodos y Funciones Clave

A continuación se detallan las funciones críticas que dan vida al robot:

### 🧠 Lógica (`robot_logic.c`)
* `void Robot_ProcesarComando(char *cmd)`: Recibe la trama cruda del USB (ej. `:#X100|Y200`). Usa un `switch` para derivar al modo correcto:
    * `:-` -> **Modo Calibración** (Homing, Set Zero, Config Velocidad).
    * `:#` -> **Modo Ejecución** (Movimiento coordinado).
* `uint8_t Robot_ModoEjecucion(void)`: Parsea coordenadas X, Y, Z y actualiza el *setpoint* de los motores. Aplica la velocidad global configurada.
* `void Robot_UpdateTelemetry(void)`: Se ejecuta cada 50ms. Verifica si hubo cambios en posición o sensores y envía el estado al PC: `STATUS|X:100|Y:100|...`.

### 💪 Motores (`motor_driver.c`)
* `void moveMotors(StepperMotor *motor, ...)`: No mueve el motor directamente. Calcula el **intervalo de tiempo** necesario entre pasos basándose en la velocidad deseada y la resolución del timer.
* `void Motor_Timer_Callback(void)`: Llamada desde la interrupción del Timer. Si el contador llega al intervalo calculado, genera un pulso físico en el pin `STEP`.
* `int HomingMotors(...)`: Rutina **bloqueante**. Mueve los ejes secuencialmente hacia el sensor, espera la interrupción y establece el cero lógico.

### ✋ Seguridad e Interrupciones (`stm32f1xx_it.c`)
* `EXTI15_10_IRQHandler`: Se dispara al tocar cualquier fin de carrera o el botón de emergencia. Llama inmediatamente a `Motor_Sensor_Triggered` para detener los pulsos.

---

## 🔌 Configuración de Hardware (Pinout)

### ⚡ Motores Paso a Paso (Drivers A4988)
| Eje | Pin STEP | Pin DIR | Notas |
| :--- | :--- | :--- | :--- |
| **X** | `PA0` | `PA3` | |
| **Y** | `PA1` | `PA4` | |
| **Z** | `PA2` | `PA5` | |
| **Enable**| `PB8` | - | Activo en BAJO (Lógica negativa) |

### 🛑 Sensores y Seguridad (Input Pull-Up)
| Función | Pin | Interrupción |
| :--- | :--- | :--- |
| **Fin X** | `PB12` | EXTI Line 12 |
| **Fin Y** | `PB13` | EXTI Line 13 |
| **Fin Z** | `PB14` | EXTI Line 14 |
| **E-STOP**| `PB15` | EXTI Line 15 (Prioridad Máxima) |

### 📟 Periféricos Adicionales
* **Servo (Gripper):** `PB9` (PWM TIM4 CH4).
* **LCD I2C:** `PB6` (SCL), `PB7` (SDA).
* **LEDs Estado:** `PB3` (Home), `PB4` (Finish), `PB5` (Wait).
* **USB:** `PA11` (DM), `PA12` (DP).

---

## ⏱️ Configuración de Timers y Velocidad

El sistema utiliza interrupciones de temporizador para generar los pasos con precisión.

### Asignación de Timers
* **TIM2:** **Generación de Pasos.** Configurado a **20 kHz**. Es el "metrónomo" del sistema.
* **TIM3:** **Base de Tiempo (Segundos).** Usado para *timeouts* en rutinas de homing (Watchdog por software).
* **TIM4:** **PWM Servo.** Frecuencia 50Hz (Periodo 20ms) para control estándar de servos.

### 📐 Cálculo de Velocidad
Considerando el siguiente hardware estándar:
* **Motor:** NEMA 17 (1.8° por paso = 200 pasos/vuelta).
* **Driver:** A4988 en modo **Full Step** (Microstepping desactivado o MS1/MS2/MS3 a GND).
* **Timer Frequency (`TIMER_FREQUENCY`):** 20,000 Hz.

#### Fórmula de Frecuencia de Pasos
El firmware recibe un valor de velocidad (V) que se interpreta directamente como frecuencia en Hz (Pasos por segundo).

$$IntervaloTimer = \frac{TIMER\_FREQUENCY}{VelocidadObj}$$

#### Conversión a RPM
Para saber la velocidad rotacional real del eje:

$$RPM = \frac{VelocidadObj \text{ (Hz)} \times 60}{200}$$

**Ejemplos Prácticos:**

| Comando USB | Velocidad (Hz) | RPM (Eje Motor) | Descripción |
| :--- | :--- | :--- | :--- |
| `:-V010` | 100 Hz | **30 RPM** | Velocidad muy lenta (precisión). |
| `:-V050` | 500 Hz | **150 RPM** | Velocidad media. |
| `:-V100` | 1000 Hz | **300 RPM** | Velocidad rápida (Límite típico sin rampa). |

> **Nota:** La variable `velocidadGlobal` en el código se escala multiplicando el input por 10 (Input 10-100 -> Output 100-1000 Hz).
