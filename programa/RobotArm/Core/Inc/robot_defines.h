/* Core/Inc/robot_defines.h */
#ifndef ROBOT_DEFINES_H
#define ROBOT_DEFINES_H

#include "main.h" // Importante: para reconocer GPIO_TypeDef, uint16_t, etc.
#include <stdlib.h> // <--- AGREGADO: Soluciona el error de "implicit declaration of abs"

// Constantes Globales
#define NUM_MOTORS 3
#define TIMER_FREQUENCY 20000

// --- CONFIGURACIÓN DE DIRECCIÓN FÍSICA (AGREGADO) ---
// Define la lógica de tus drivers (ajusta 1 o 0 según si tu robot va al revés)
#define DIR_TOWARDS_HOME  1  // Dirección lógica para ir HACIA el sensor
#define DIR_AWAY_HOME     0  // Dirección lógica para ALEJARSE del sensor

// --- PARÁMETROS DE SEGURIDAD (AGREGADO) ---
#define HOMING_BACKOFF_STEPS 5 // Pasos que retrocede para liberar el sensor

// ESTADOS DEL ROBOT
#define STATE_IDLE      0  // Normal, esperando comandos
#define STATE_HOMING    1  // En proceso de calibración
#define STATE_MOVING    2  // Ejecutando movimiento
#define STATE_ESTOP     99 // ¡PARADA DE EMERGENCIA ACTIVA! (Bloqueo)

// Agrega esta variable externa para que todos la vean
extern volatile uint8_t robotState;

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
    int stepInterval;           // Ticks del timer entre pasos
    volatile int stopFlag;      // 1 = Detenido, 0 = Moviéndose

    // --- CAMPOS PARA RAMPAS ---
    int targetVelocity;  // Velocidad Objetivo
    int minVelocity;     // Velocidad de Arranque
    int accelRate;       // Tasa de aceleración
    int stepsToDecel;    // Cálculo interno
} StepperMotor;

#endif /* ROBOT_DEFINES_H */
