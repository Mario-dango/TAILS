/* Core/Inc/robot_defines.h */
#ifndef ROBOT_DEFINES_H
#define ROBOT_DEFINES_H

#include "main.h" // Importante: para reconocer GPIO_TypeDef, uint16_t, etc.

// Constantes Globales
#define NUM_MOTORS 3
#define TIMER_FREQUENCY 20000 // Ajustado a 20kHz según nuestra corrección anterior

// Estructura del Motor
typedef struct {
    GPIO_TypeDef *stepPort;     // Puerto GPIO para el pin de paso (step)
    uint16_t stepPin;           // Número del pin de paso (step)
    GPIO_TypeDef *dirPort;      // Puerto GPIO para el pin de dirección (dir)
    uint16_t dirPin;            // Número del pin de dirección (dir)
    int direction;              // Dirección (0 o 1)
    int velocity;               // 0-100%
    int microStepping;          // Factor de división
    volatile int currentPosition;        // Pasos actuales
    volatile int newPosition;            // Meta
    int stepCounter;            // Contador interno para el Timer
    int stepInterval;           // Ticks del timer entre pasos
    volatile int stopFlag;      // 1 = Detenido, 0 = Moviéndose
} StepperMotor;

#endif /* ROBOT_DEFINES_H */
