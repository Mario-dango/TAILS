/*
 * motor_driver.c
 *
 *  Created on: Jan 4, 2026
 *      Author: mprob
 */

/* Core/Src/motor_driver.c */
#include "motor_driver.h"
#include "tim.h"   // Necesario para acceder a htim3 (usado en homing)
#include <math.h>  // Para M_PI
#include "gripper_driver.h"

// Variables que antes tenías globales en main.c y son exclusivas de motores
volatile uint8_t flagStopM_X = 0;
volatile uint8_t flagStopM_Y = 0;
volatile uint8_t flagStopM_Z = 0;

// Configuración por defecto de rampas (Ajustable)
#define DEFAULT_MIN_VEL  50   // 50 Hz de arranque (evita resonancia baja)
#define DEFAULT_ACCEL    5    // Aumentar 5 Hz por cada paso dado

// --- Funciones Privadas ---
void CalculateSpeed(StepperMotor *motor);

// Inicializa valores por defecto para evitar basura en memoria
void Motor_Init(void) {
    for (int i = 0; i < NUM_MOTORS; i++) {
        motors[i].minVelocity = DEFAULT_MIN_VEL;
        motors[i].accelRate = DEFAULT_ACCEL;
        motors[i].velocity = 0;
        motors[i].targetVelocity = 0;
        motors[i].stopFlag = 1;
    }
}

// Implementación de ActivatedAll
void ActivatedAll(int habilitar){
    if (habilitar == -1){ // Parada de emergencia
        for (int i = 0; i < NUM_MOTORS; i++) {
            motors[i].targetVelocity = 0;
            motors[i].velocity = 0;
            motors[i].stepInterval = 0;
            motors[i].stopFlag = 1;
        }
    }
    else if (habilitar == 1){ // Habilitar driver
        HAL_GPIO_WritePin(EnableMotors_GPIO_Port, EnableMotors_Pin, RESET);
    }
    else if (habilitar == 0){ // Deshabilitar driver
        HAL_GPIO_WritePin(EnableMotors_GPIO_Port, EnableMotors_Pin, SET);
    }
}

// Lógica principal de configuración de movimiento
void moveMotors(StepperMotor *motor, int *newPosition, int *velocity) {

    // 1. Configurar Meta de Posición
    if (newPosition != 0) {
        motor->newPosition = *newPosition;
    }

    // 2. Configurar Meta de Velocidad (Target)
    if (velocity != 0) {
        motor->targetVelocity = *velocity;

        // Configuración de seguridad: Si la velocidad pedida es menor a la mínima,
        // usamos la mínima para evitar bloqueos, a menos que sea 0 (stop).
        if (*velocity > 0 && *velocity < motor->minVelocity) {
            motor->targetVelocity = motor->minVelocity;
        }
    }

    // 3. Lógica de Arranque
    if (motor->targetVelocity > 0) {
        // Calcular dirección
        if (motor->currentPosition < motor->newPosition){
            motor->direction = 0;
        } else if (motor->currentPosition > motor->newPosition){
            motor->direction = 1;
        }

        // Si hay distancia por recorrer
        if (motor->currentPosition != motor->newPosition){
            motor->stopFlag = 0;

            // Si el motor estaba parado, lo "despertamos" con la velocidad mínima
            if (motor->velocity == 0) {
                motor->velocity = motor->minVelocity;
            }

            // Calculamos el primer intervalo inmediatamente
            motor->stepInterval = TIMER_FREQUENCY / motor->velocity;

        } else {
             // Ya estamos en el lugar
             motor->velocity = 0;
             motor->stepInterval = 0;
             motor->stopFlag = 1;
        }
    } else {
        // Orden de parada (Velocidad 0)
        motor->velocity = 0;
        motor->stepInterval = 0;
        motor->stopFlag = 1;
    }
}

// Algoritmo de Rampa Trapezoidal
// Se llama CADA VEZ que el motor da un paso físico
void CalculateSpeed(StepperMotor *m) {
    long stepsRemaining = abs(m->newPosition - m->currentPosition);

    // Si ya llegamos (o nos pasamos por inercia)
    if (stepsRemaining == 0) {
        m->velocity = 0;
        m->stepInterval = 0;
        m->stopFlag = 1;
        return;
    }

    // Calculamos cuántos pasos necesitamos para frenar desde la velocidad actual
    // Formula simplificada: (Vel_Actual - Vel_Min) / Aceleracion
    long stepsToStop = (m->velocity - m->minVelocity) / m->accelRate;

    // --- FASE DE DESACELERACIÓN ---
    if (stepsRemaining <= stepsToStop) {
        if (m->velocity > m->minVelocity) {
            m->velocity -= m->accelRate;
        }
    }
    // --- FASE DE ACELERACIÓN ---
    else if (m->velocity < m->targetVelocity) {
        m->velocity += m->accelRate;

        // Cap (Techo) de seguridad
        if (m->velocity > m->targetVelocity)
            m->velocity = m->targetVelocity;
    }
    // --- FASE CRUCERO (Mantener) ---
    // (Implícita: si no entra en los if anteriores, mantiene velocidad)

    // Protección final matemática
    if (m->velocity < m->minVelocity) m->velocity = m->minVelocity;
    if (m->velocity == 0) m->stepInterval = 0;
    else m->stepInterval = TIMER_FREQUENCY / m->velocity;
}

// Rutina de Homing (Modificada para usar velocidad constante y segura)
int HomingMotors(uint8_t* hmX, uint8_t* hmY, uint8_t* hmZ) {
    ActivatedAll(1);
    Gripper_Open();
    HAL_Delay(500);

    flagStopM_X = 0; flagStopM_Y = 0; flagStopM_Z = 0;
    *hmX = 0; *hmY = 0; *hmZ = 0;

    // Configuración para Homing: Sin rampas, velocidad fija y baja
    int homingSpeed = 50; // Hz

    for (int i = 0; i < NUM_MOTORS; i++) {
        motors[i].minVelocity = homingSpeed;
        motors[i].targetVelocity = homingSpeed; // Target = Min para que no acelere
        motors[i].velocity = homingSpeed;
        motors[i].accelRate = 0; // Desactivar aceleración para homing

        motors[i].stepInterval = TIMER_FREQUENCY / homingSpeed;
        motors[i].direction = 1;
        motors[i].stopFlag = 1;
    }

    // --- SECUENCIA EJE X ---
    motors[0].stopFlag = 0;
    contSeconds = 0;
    while ((*hmX == 0) && (contSeconds < 15)) {
        if (flagStopM_X == 1) {
            *hmX = 1; motors[0].stopFlag = 1;
        }
    }
    motors[0].stopFlag = 1;

    // --- SECUENCIA EJE Y ---
    motors[1].stopFlag = 0;
    contSeconds = 0;
    while ((*hmY == 0) && (contSeconds < 15)) {
        if (flagStopM_Y == 1) {
            *hmY = 1; motors[1].stopFlag = 1;
        }
    }
    motors[1].stopFlag = 1;

    // --- SECUENCIA EJE Z ---
    motors[2].stopFlag = 0;
    contSeconds = 0;
    while ((*hmZ == 0) && (contSeconds < 15)) {
        if (flagStopM_Z == 1) {
            *hmZ = 1; motors[2].stopFlag = 1;
        }
    }
    motors[2].stopFlag = 1;

    // Restaurar valores normales post-homing
    for (int i = 0; i < NUM_MOTORS; i++) {
        motors[i].velocity = 0;
        motors[i].stepInterval = 0;
        motors[i].currentPosition = 0;
        motors[i].stopFlag = 0;
        motors[i].accelRate = DEFAULT_ACCEL; // Restaurar aceleración
        motors[i].minVelocity = DEFAULT_MIN_VEL;
    }

    if ((*hmX == 1 )&&(*hmY == 1 )&&(*hmZ == 1 )) return 0;
    if (*hmX == 0) return -1;
    if (*hmY == 0) return -2;
    if (*hmZ == 0) return -3;

    return 1;
}

// --- INTERRUPCIÓN DEL TIMER (Generación de Pulsos) ---
void Motor_Timer_Callback(void) {
    for (int i = 0; i < NUM_MOTORS; i++) {
        StepperMotor *motor = &motors[i];

        if (motor->stopFlag == 0 && motor->stepInterval > 0) {
            motor->stepCounter++;

            // Generar Pulso STEP (High)
            if (motor->stepCounter >= motor->stepInterval) {
                HAL_GPIO_WritePin(motor->dirPort, motor->dirPin, (motor->direction == 0) ? GPIO_PIN_SET : GPIO_PIN_RESET);
                HAL_GPIO_WritePin(motor->stepPort, motor->stepPin, GPIO_PIN_SET);
            }

            // Terminar Pulso STEP (Low) y Contabilizar Paso
            if (motor->stepCounter >= (motor->stepInterval + 1)) {
                HAL_GPIO_WritePin(motor->stepPort, motor->stepPin, GPIO_PIN_RESET);
                motor->stepCounter = 0;

                // Actualizar Posición
                if (motor->direction == 0) motor->currentPosition++;
                else motor->currentPosition--;

                // --- AQUÍ OCURRE LA MAGIA DE LA RAMPA ---
                // Recalculamos la velocidad para el SIGUIENTE paso
                CalculateSpeed(motor);
            }
        }
    }
}

// Lógica de sensores (Lo que antes estaba en HAL_GPIO_EXTI_Callback)
void Motor_Sensor_Triggered(uint16_t GPIO_Pin) {
    if (GPIO_Pin == STOP_btn_Pin){
        ActivatedAll(-1); // Parada emergencia
    }
    // Finales de carrera: Detener motor y marcar bandera
    // Nota: Aquí podrías actualizar directamente los punteros hmX/Y/Z si los tuvieras globales,
    // o usar las variables estáticas flagStopM_X.
    else if (GPIO_Pin == StopM_X_Pin) {
        motors[0].stopFlag = 1;
        motors[0].velocity = 0; // Parada seca al tocar sensor
        flagStopM_X = 1; // Usado por la lógica de Homing
    }
    else if (GPIO_Pin == StopM_Y_Pin) {
        motors[1].stopFlag = 1;
        motors[1].velocity = 0; // Parada seca al tocar sensor
        flagStopM_Y = 1;
    }
    else if (GPIO_Pin == StopM_Z_Pin) {
        motors[2].stopFlag = 1;
        motors[2].velocity = 0; // Parada seca al tocar sensor
        flagStopM_Z = 1;
    }
}

// Auxiliares
int targetComplete(StepperMotor *motor){
    int target = 0;
    for(int i = 0; i < NUM_MOTORS; i++){
    	// Consideramos completado si está parado y velocity es 0
        if (motor[i].velocity == 0 && motor[i].stopFlag == 1) target++;
    }
    return (target == NUM_MOTORS) ? 1 : 0;
}


float deg2rad(float degrees) {
    return degrees * (M_PI / 180.0);
}
