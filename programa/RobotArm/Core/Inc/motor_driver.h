/* Core/Inc/motor_driver.h */
#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

#include "robot_defines.h"

// --- Variables Externas ---
// Prometemos que existen en main.c o motor_driver.c
extern StepperMotor motors[NUM_MOTORS];
extern int contSeconds; // Variable para el timeout del homing

// --- Prototipos de Funciones ---

// Inicializa o configura valores por defecto si es necesario
void Motor_Init(void);

// Habilita (1), Deshabilita (0) o Frena (-1) todos los motores
void ActivatedAll(int habilitar);

// Calcula el intervalo de pasos según la velocidad (llamada en el bucle principal)
void moveMotors(StepperMotor *motor, int *newPosition, int *velocity);

// Verifica si todos los motores llegaron a destino
int targetComplete(StepperMotor *motor);

// Rutina de Homing (Devuelve 0 si OK, o código de error)
// Pasamos punteros para actualizar las banderas de éxito de cada eje
int HomingMotors(uint8_t* hmX, uint8_t* hmY, uint8_t* hmZ);

// Conversión auxiliar
float deg2rad(float degrees);

// --- Funciones para Interrupciones (Callbacks) ---
// Llama a esto dentro de HAL_TIM_PeriodElapsedCallback (TIM2)
void Motor_Timer_Callback(void);

// Llama a esto dentro de HAL_GPIO_EXTI_Callback
void Motor_Sensor_Triggered(uint16_t GPIO_Pin);

#endif /* MOTOR_DRIVER_H */
