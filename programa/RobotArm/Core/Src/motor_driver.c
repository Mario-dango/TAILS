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

// Implementación de ActivatedAll
void ActivatedAll(int habilitar){
    if (habilitar == -1){ // Parada de emergencia
        for (int i = 0; i < NUM_MOTORS; i++) {
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

// Implementación de moveMotors (Lógica de control de velocidad)
void moveMotors(StepperMotor *motor, int *newPosition, int *velocity) {
    if (velocity != 0) motor->velocity = *velocity;
    if (newPosition != 0) motor->newPosition = *newPosition;

    if (motor->velocity != 0){
        // Calcular dirección
        if (motor->currentPosition < motor->newPosition){
            motor->direction = 0;
        } else if (motor->currentPosition > motor->newPosition){
            motor->direction = 1;
        }

        // Calcular si debe moverse
        if (motor->currentPosition != motor->newPosition){
            motor->stopFlag = 0;
            // Evitar división por cero
            if (motor->velocity > 0)
                motor->stepInterval = TIMER_FREQUENCY / (motor->velocity * motor->microStepping);
        } else {
             // Ya llegó
             motor->stepInterval = 0;
        }
    } else {
        motor->stepInterval = 0;
        motor->stopFlag = 1;
    }
}

// Implementación de Homing
int HomingMotors(uint8_t* hmX, uint8_t* hmY, uint8_t* hmZ) {
    ActivatedAll(1); // Habilitar drivers

    Gripper_Open();
    HAL_Delay(500); // Dar tiempo al servo para abrirse

    // 0. Resetear banderas globales de sensores por seguridad
    flagStopM_X = 0;
    flagStopM_Y = 0;
    flagStopM_Z = 0;

    // Inicializar valores de retorno
    *hmX = 0; *hmY = 0; *hmZ = 0;

    // 1. Configurar movimiento lento hacia los sensores
    for (int i = 0; i < NUM_MOTORS; i++) {
        motors[i].velocity = 20;
        motors[i].stepInterval = TIMER_FREQUENCY / (motors[i].velocity * motors[i].microStepping);
        motors[i].direction = 1; // Asegúrate que 1 sea la dirección HACIA el sensor
        motors[i].stopFlag = 1;  // Empezar parados
    }

    // --- SECUENCIA EJE X ---
    motors[0].stopFlag = 0; // Mover X
    contSeconds = 0; // Reiniciar contador de tiempo (asegúrate de resetearlo en main o aquí si es extern)

    // CORRECCIÓN AQUÍ: Verificamos la bandera global dentro del while
    while ((*hmX == 0) && (contSeconds < 15)) {
        if (flagStopM_X == 1) {
            *hmX = 1;            // Avisamos al bucle que ya llegamos
            motors[0].stopFlag = 1; // Aseguramos que el motor pare
        }
    }
    motors[0].stopFlag = 1; // Detener X forzosamente al salir

    // --- SECUENCIA EJE Y ---
    motors[1].stopFlag = 0;
    contSeconds = 0;
    while ((*hmY == 0) && (contSeconds < 15)) {
        if (flagStopM_Y == 1) {
            *hmY = 1;
            motors[1].stopFlag = 1;
        }
    }
    motors[1].stopFlag = 1;

    // --- SECUENCIA EJE Z ---
    motors[2].stopFlag = 0;
    contSeconds = 0;
    while ((*hmZ == 0) && (contSeconds < 15)) {
        if (flagStopM_Z == 1) {
            *hmZ = 1;
            motors[2].stopFlag = 1;
        }
    }
    motors[2].stopFlag = 1;

    // Limpieza final
    for (int i = 0; i < NUM_MOTORS; i++) {
        motors[i].velocity = 0;
        motors[i].stepInterval = 0;
        motors[i].currentPosition = 0;
        motors[i].stopFlag = 0; // Dejarlos listos para recibir comandos
    }

    // Retorno de estado
    if ((*hmX == 1 )&&(*hmY == 1 )&&(*hmZ == 1 )){
        return 0; // Éxito total
    }
    if (*hmX == 0) return -1; // Falló X
    if (*hmY == 0) return -2; // Falló Y
    if (*hmZ == 0) return -3; // Falló Z

    return 1;
}

// Lógica del Timer (Lo que antes estaba en TIM2_PeriodElapsedCallback)
void Motor_Timer_Callback(void) {
    for (int i = 0; i < NUM_MOTORS; i++) {
        StepperMotor *motor = &motors[i];

        if (motor->stopFlag == 0 && motor->stepInterval > 0) {
            motor->stepCounter++;

            // Generación de pulso con ancho controlado
            if (motor->stepCounter >= motor->stepInterval) {
                // Setear dirección física
                HAL_GPIO_WritePin(motor->dirPort, motor->dirPin, (motor->direction == 0) ? GPIO_PIN_SET : GPIO_PIN_RESET);
                // Flanco ascendente (STEP HIGH)
                HAL_GPIO_WritePin(motor->stepPort, motor->stepPin, GPIO_PIN_SET);
            }

            // Flanco descendente (STEP LOW) - 1 tick después
            if (motor->stepCounter >= (motor->stepInterval + 1)) {
                HAL_GPIO_WritePin(motor->stepPort, motor->stepPin, GPIO_PIN_RESET);
                motor->stepCounter = 0;

                // Actualizar posición lógica
                if (motor->direction == 0) motor->currentPosition++;
                else motor->currentPosition--;
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
        flagStopM_X = 1; // Usado por la lógica de Homing
    }
    else if (GPIO_Pin == StopM_Y_Pin) {
        motors[1].stopFlag = 1;
        flagStopM_Y = 1;
    }
    else if (GPIO_Pin == StopM_Z_Pin) {
        motors[2].stopFlag = 1;
        flagStopM_Z = 1;
    }
}

// Auxiliares
int targetComplete(StepperMotor *motor){
    int target = 0;
    for(int i = 0; i < NUM_MOTORS; i++){
        if (motor[i].currentPosition == motor[i].newPosition) target++;
    }
    return (target == NUM_MOTORS) ? 1 : 0;
}

float deg2rad(float degrees) {
    return degrees * (M_PI / 180.0);
}
