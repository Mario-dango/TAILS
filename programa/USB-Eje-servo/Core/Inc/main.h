/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2023 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

#include "lcd_i2c.h"
#include <math.h>
#include <usbd_cdc_if.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define LedPcb_Pin GPIO_PIN_13
#define LedPcb_GPIO_Port GPIOC
#define StepM_Z_Pin GPIO_PIN_0
#define StepM_Z_GPIO_Port GPIOA
#define StepM_Y_Pin GPIO_PIN_1
#define StepM_Y_GPIO_Port GPIOA
#define StepM_X_Pin GPIO_PIN_2
#define StepM_X_GPIO_Port GPIOA
#define DirM_Z_Pin GPIO_PIN_3
#define DirM_Z_GPIO_Port GPIOA
#define DirM_Y_Pin GPIO_PIN_4
#define DirM_Y_GPIO_Port GPIOA
#define DirM_X_Pin GPIO_PIN_5
#define DirM_X_GPIO_Port GPIOA
#define StopM_Z_Pin GPIO_PIN_12
#define StopM_Z_GPIO_Port GPIOB
#define StopM_Z_EXTI_IRQn EXTI15_10_IRQn
#define StopM_Y_Pin GPIO_PIN_13
#define StopM_Y_GPIO_Port GPIOB
#define StopM_Y_EXTI_IRQn EXTI15_10_IRQn
#define StopM_X_Pin GPIO_PIN_14
#define StopM_X_GPIO_Port GPIOB
#define StopM_X_EXTI_IRQn EXTI15_10_IRQn
#define STOP_btn_Pin GPIO_PIN_15
#define STOP_btn_GPIO_Port GPIOB
#define STOP_btn_EXTI_IRQn EXTI15_10_IRQn
#define Home_led_Pin GPIO_PIN_3
#define Home_led_GPIO_Port GPIOB
#define Finish_led_Pin GPIO_PIN_4
#define Finish_led_GPIO_Port GPIOB
#define Wait_led_Pin GPIO_PIN_5
#define Wait_led_GPIO_Port GPIOB
#define EnableMotors_Pin GPIO_PIN_8
#define EnableMotors_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

//	Valores para el gripper sg90
#define PULSE_MIN 550
#define PULSE_MAX 2450

// Definición de las frecuencias de temporización (en Hertz)
#define TIMER_FREQUENCY 1000 // Por ejemplo, 1000 Hz (1 ms de intervalo)

// Número de motores que estás utilizando
#define NUM_MOTORS 3

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
