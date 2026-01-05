/*
 * gripper_driver.h
 *
 *  Created on: Jan 4, 2026
 *      Author: mprob
 */
#ifndef GRIPPER_DRIVER_H
#define GRIPPER_DRIVER_H

#include "main.h" // Para uint16_t y definiciones de HAL

// Constantes del Servo SG90
#define PULSE_MIN 550
#define PULSE_MAX 2450

// Prototipos
void Gripper_Init(void);
void Gripper_SetAngle(uint16_t angle); // Equivalente a tu Servo_Write_angle
void Gripper_Open(void);
void Gripper_Close(void);

#endif /* GRIPPER_DRIVER_H */
