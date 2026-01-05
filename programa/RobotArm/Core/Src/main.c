/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "i2c.h"
#include "tim.h"
#include "usb_device.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "usbd_cdc_if.h"
#include "lcd_i2c.h"
#include <string.h>
#include <stdio.h>

// --- NUEVOS MODULOS ---
#include "robot_defines.h"
#include "motor_driver.h"
#include "gripper_driver.h"
#include "comm_manager.h"
#include "robot_logic.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
// (Vacío: La estructura StepperMotor ahora está en robot_defines.h)
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
// (Vacío: Los defines están en los headers correspondientes)
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */
/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */

// Array principal de motores (Variable Global compartida con extern)
StepperMotor motors[NUM_MOTORS];

// Buffers de Comunicación (Compartidos con comm_manager y robot_logic)
uint8_t flagUsb = 0;       // Se pone en 1 desde usbd_cdc_if.c
char buffer_rx[40];
char buffer_tx[80];
char buffer_data[4][6];

int contSeconds = 0;

// Variables para LCD (Estéticas del Main)
// Nota: estadoGarra se maneja internamente en gripper_driver,
// pero si necesitas mostrarla en LCD, puedes usar una variable local o getters.
extern uint8_t estadoGarra; // Traída del driver si la definiste global allá, o úsala local.

// 0: Muestra "???", 1: Muestra coordenadas "000"
uint8_t robotCalibrated = 0;
extern uint8_t estadoGarra; // Traída de gripper_driver.c

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
void Actualizar_LCD(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */
  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */
  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
//  MX_TIM2_Init();
  MX_USB_DEVICE_Init();
  MX_TIM4_Init();
  MX_TIM3_Init();
  MX_I2C1_Init();
  /* USER CODE BEGIN 2 */
  // Tus sensores están en PB12, PB13, PB14. Usan el vector EXTI15_10
    HAL_NVIC_SetPriority(EXTI15_10_IRQn, 0, 0); // Prioridad 0 (La más alta posible)
    HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);

    MX_TIM2_Init();

  // --- INICIALIZACIÓN DE PERIFÉRICOS ---

  // 1. LCD
  Lcd_Init();
  Lcd_Clear();
  Lcd_Set_Cursor(1,1); Lcd_Send_String("Iniciando...");
  HAL_Delay(1000);

  // 2. LEDS y ENABLE
  HAL_GPIO_WritePin(Wait_led_GPIO_Port, Wait_led_Pin, RESET);
  HAL_GPIO_WritePin(Finish_led_GPIO_Port, Finish_led_Pin, RESET);
  HAL_GPIO_WritePin(Home_led_GPIO_Port, Home_led_Pin, RESET);

  // Inicialmente deshabilitados o habilitados según tu lógica
  HAL_GPIO_WritePin(EnableMotors_GPIO_Port, EnableMotors_Pin, SET); // Deshabilitado (lógica negativa A4988?)

  // 3. GRIPPER
  Gripper_Init();

  // 4. MOTORES (Configuración inicial)
  // Nota: Asegúrate de que los defines StepM_X_GPIO_Port, etc., existen en main.h
  motors[0] = (StepperMotor){ StepM_X_GPIO_Port, StepM_X_Pin, DirM_X_GPIO_Port, DirM_X_Pin, 0, 0, 1, 0, 0, 0, 0, 1 };
  motors[1] = (StepperMotor){ StepM_Y_GPIO_Port, StepM_Y_Pin, DirM_Y_GPIO_Port, DirM_Y_Pin, 0, 0, 1, 0, 0, 0, 0, 1 };
  motors[2] = (StepperMotor){ StepM_Z_GPIO_Port, StepM_Z_Pin, DirM_Z_GPIO_Port, DirM_Z_Pin, 0, 0, 1, 0, 0, 0, 0, 1 };

  // 5. TIMERS
  HAL_TIM_Base_Start_IT(&htim2); // Timer de Pasos (Driver Motor)
  HAL_TIM_Base_Start_IT(&htim3); // Timer auxiliar segundos
  // TIM4 (PWM) ya se inició en Gripper_Init

  Lcd_Clear();
  Lcd_Set_Cursor(1,1); Lcd_Send_String("Robot Ready!");
  Lcd_Set_Cursor(2,1); Lcd_Send_String("Waiting USB...");

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
      // --- A. ATENCIÓN AL USB ---
	  if(flagUsb == 1){
//		  HAL_GPIO_TogglePin(LedPcb_GPIO_Port, LedPcb_Pin);

		  // Toda la lógica compleja se movió a robot_logic.c
		  Robot_ProcesarComando(buffer_rx);

		  flagUsb = 0; // Bajamos la bandera
	  }

	  // --- B. TAREAS DE FONDO (IDLE) ---
	  else {
		  // Actualización continua de motores (Polling para verificar llegada a destino)
		  // Esto es necesario si moveMotors maneja rampas o lógica de parada suave
		  for (int k = 0; k < NUM_MOTORS; ++k) {
			  moveMotors(&motors[k], 0, 0);
		  }

		  // --- ACTUALIZAR LCD ---
		  Actualizar_LCD(); // <--- LLAMADA AQUÍ

		  // Actualización de LCD (Opcional: hacer un contador para no refrescar tan rápido)
		  static uint32_t lcd_timer = 0;
		  if (HAL_GetTick() - lcd_timer > 500) {
		      // Aquí puedes poner tu código para mostrar X, Y, Z en el LCD
		      // Lcd_Set_Cursor(2,1); sprintf(...)
		      lcd_timer = HAL_GetTick();
		  }
	  }
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
    // (Tu configuración de reloj se mantiene igual, generada por CubeMX)
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_USB;
  PeriphClkInit.UsbClockSelection = RCC_USBCLKSOURCE_PLL_DIV1_5;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

// --- CALLBACKS DE INTERRUPCIONES LIMPIOS ---

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
	// Timer de generación de pasos (Alta frecuencia)
	if (htim->Instance == TIM2) {
	     Motor_Timer_Callback(); // Delegamos al driver
	}
	// Timer de conteo de segundos (Baja frecuencia)
	if (htim->Instance == TIM3){
		extern int contSeconds; // Variable definida en motor_driver.c u otro
		contSeconds++;
	}
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin){
    // Delegamos la lógica de sensores al driver
	Motor_Sensor_Triggered(GPIO_Pin);
}

// NOTA: Todas las funciones viejas (modoCalibracion, HomingMotors, etc.)
// han sido eliminadas de aquí porque ahora viven en:
// - comm_manager.c
// - motor_driver.c
// - robot_logic.c
// - gripper_driver.c

void Actualizar_LCD(void) {
    static uint32_t lcd_timer = 0;

    // Refrescamos el LCD cada 300ms para no saturar el I2C ni parpadear
    if (HAL_GetTick() - lcd_timer > 300) {
        lcd_timer = HAL_GetTick();
        Lcd_Clear();
        // Renglón 1: Fijo
        Lcd_Set_Cursor(1,1);
        Lcd_Send_String("Estado Global");

        // Renglón 2: Dinámico
        Lcd_Set_Cursor(2,1);

        char buffer_lcd[17]; // Buffer temporal para formatear texto
        char charGarra = (estadoGarra == 1) ? 'A' : 'C'; // A=Abierta, C=Cerrada

        if (robotCalibrated == 0) {
            // ESTADO DESCONOCIDO
            // Muestra: X???|Y???|Z???|?
            // Si la garra ya se movió alguna vez, mostramos su estado, si no '?'
            sprintf(buffer_lcd, "X???|Y???|Z???|%c", charGarra);
        }
        else {
            // ESTADO CONOCIDO (CALIBRADO)
            // %03d fuerza a que el número tenga 3 dígitos (ej: 5 -> 005)
            sprintf(buffer_lcd, "X%03d|Y%03d|Z%03d|%c",
                    motors[0].currentPosition,
                    motors[1].currentPosition,
                    motors[2].currentPosition,
                    charGarra);
        }

        Lcd_Send_String(buffer_lcd);
    }
}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
}
#endif /* USE_FULL_ASSERT */
