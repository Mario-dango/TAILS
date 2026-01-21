/*
 * gripper_driver.c
 *
 *  Created on: Jan 4, 2026
 *      Author: mprob
 */

#include "gripper_driver.h"
#include "tim.h" // Necesitamos acceder a htim4

// Variable interna para guardar el estado (opcional, si la necesitas en lógica)
uint8_t estadoGarra = 0; // 0: Cerrada, 1: Abierta

// Variable privada para guardar el ángulo de cierre (Default 0)
static uint16_t anguloCierre = 0;   // Default 0
static uint16_t anguloApertura = 90; // Default 90

// Agrega este prototipo
void Gripper_SetClosedAngle(uint16_t angle);
void Gripper_SetOpenAngle(uint16_t angle);

void Gripper_Init(void) {
    // Inicia el PWM del servo
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_4);
}

void Gripper_SetAngle(uint16_t theta) {
    uint16_t pwm_servo;
    // Protección para no exceder límites físicos (0 a 180 grados)
    if (theta > 180) theta = 180;

    // Mapeo de grados a ancho de pulso
    pwm_servo = (uint16_t)((theta - 0) * (PULSE_MAX - PULSE_MIN) / (180 - 0) + PULSE_MIN);
    __HAL_TIM_SetCompare(&htim4, TIM_CHANNEL_4, pwm_servo);
}

void Gripper_SetOpenAngle(uint16_t angle) {
    if (angle > 180) angle = 180;
    anguloApertura = angle;
}

// Modificar Gripper_Open para usar la variable
void Gripper_Open(void) {
    Gripper_SetAngle(anguloApertura); // <--- USAR LA VARIABLE, NO 90 FIJO
    estadoGarra = 1; // 1: Abierta
}

void Gripper_SetClosedAngle(uint16_t angle) {
    if (angle > 180) angle = 180;
    anguloCierre = angle;
}

// Modificamos Gripper_Close para usar la variable
void Gripper_Close(void) {
    Gripper_SetAngle(anguloCierre); // Usamos el valor configurado
    estadoGarra = 0; // 0 = Cerrada
}
