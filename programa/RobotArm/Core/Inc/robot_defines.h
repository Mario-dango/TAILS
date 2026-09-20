/* Core/Inc/robot_defines.h */
#ifndef ROBOT_DEFINES_H
#define ROBOT_DEFINES_H

#include "main.h" // Importante: para reconocer GPIO_TypeDef, uint16_t, etc.
#include <stdlib.h> // <--- AGREGADO: Soluciona el error de "implicit declaration of abs"

// Constantes Globales
#define NUM_MOTORS 3
#define TIMER_FREQUENCY 20000

// Velocidad global por defecto (pps). Se usa hasta que el usuario ajuste
// el slider (:-V). Debe ser > minVelocity para que el primer movimiento
// arranque sin depender de que la interfaz mande velocidad antes.
#define DEFAULT_GLOBAL_VELOCITY 300

// --- CONFIGURACIÓN DE DIRECCIÓN FÍSICA (AGREGADO) ---
// Define la lógica de tus drivers (ajusta 1 o 0 según si tu robot va al revés)
#define DIR_TOWARDS_HOME  1  // Dirección lógica para ir HACIA el sensor
#define DIR_AWAY_HOME     0  // Dirección lógica para ALEJARSE del sensor

// --- PARÁMETROS DE SEGURIDAD (AGREGADO) ---
#define HOMING_BACKOFF_STEPS 5 // Pasos que retrocede para liberar el sensor

// Objetivo "lejano" para el homing: el motor debe correr a velocidad constante
// hasta que lo detenga el SENSOR, no la posición. Fijamos newPosition a esta
// distancia para que CalculateSpeed no frene el motor antes de llegar al sensor.
#define HOMING_FAR_STEPS 1000000L

// --- LIMITES ARTICULARES (TOPE LEJANO DE CADA EJE, EN PASOS) ---
// El fin de carrera protege el extremo de HOME; del otro lado no habia nada que
// frenara al brazo: se aceptaba cualquier destino que mandara la interfaz. Estos
// son los topes mecanicos medidos, y deben coincidir con RANGO_X/Y/Z de
// interfaz/view/ui_widgets.py (la interfaz recorta igual, esto es la red final).
#define MAX_POS_X 580   // giro de la base
#define MAX_POS_Y 130   // extension del brazo
#define MAX_POS_Z 60    // altura

// ESTADOS DEL ROBOT
#define STATE_IDLE      0  // Normal, esperando comandos
#define STATE_HOMING    1  // En proceso de calibración
#define STATE_MOVING    2  // Ejecutando movimiento
#define STATE_ESTOP     99 // ¡PARADA DE EMERGENCIA ACTIVA! (Bloqueo)

// Agrega esta variable externa para que todos la vean
extern volatile uint8_t robotState;

// --- FUENTES DE INTERRUPCIÓN / EVENTO (para diferenciar en el log) ---
// Se setean en la ISR (o en la recepción USB para el E-STOP por software) y las
// imprime el bucle principal vía Robot_ReportInterrupts(). Así se puede saber por
// dónde entró la parada: botón físico, comando :-S, o qué fin de carrera tocó.
#define IRQ_SRC_NONE       0
#define IRQ_SRC_ESTOP_BTN  1  // Botón físico de PARO (EXTI PB15)
#define IRQ_SRC_ESTOP_SW   2  // Comando :-S desde la interfaz (E-STOP por software)
#define IRQ_SRC_LIMIT_X    3  // Fin de carrera X (EXTI PB12)
#define IRQ_SRC_LIMIT_Y    4  // Fin de carrera Y (EXTI PB13)
#define IRQ_SRC_LIMIT_Z    5  // Fin de carrera Z (EXTI PB14)

// Último evento de interrupción pendiente de reportar (definida en motor_driver.c).
extern volatile uint8_t lastIrqSource;

// Estructura del Motor
typedef struct {
    GPIO_TypeDef *stepPort;     // Puerto GPIO para el pin de paso (step)
    uint16_t stepPin;           // Número del pin de paso (step)
    GPIO_TypeDef *dirPort;      // Puerto GPIO para el pin de dirección (dir)
    uint16_t dirPin;            // Número del pin de dirección (dir)
    int direction;              // Dirección (0 o 1)
    volatile int velocity;      // Velocidad instantánea
    int microStepping;          // Factor de división
    volatile int currentPosition;        // Pasos actuales
    volatile int newPosition;            // Meta
    int stepCounter;            // Contador interno para el Timer
    volatile int stepInterval;  // Ticks del timer entre pasos (compartido con ISR TIM2)
    volatile int stopFlag;      // 1 = Detenido, 0 = Moviéndose

    // --- CAMPOS PARA RAMPAS ---
    volatile int targetVelocity;  // Velocidad Objetivo (compartido con ISR TIM2)
    int minVelocity;     // Velocidad de Arranque
    int accelRate;       // Tasa de aceleración
    int stepsToDecel;    // Cálculo interno
} StepperMotor;

#endif /* ROBOT_DEFINES_H */
