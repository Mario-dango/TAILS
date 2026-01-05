/*
 * robot_logic.c
 *
 *  Created on: Jan 4, 2026
 *      Author: mprob
 */


#include "robot_logic.h"
#include "motor_driver.h"
#include "gripper_driver.h"
#include "comm_manager.h"
#include "lcd_i2c.h" // Asumiendo que tienes este archivo en Inc

// --- Variables Externas (Viven en main.c) ---
extern char buffer_rx[40];
extern char buffer_tx[60];
extern char buffer_data[4][6];
extern uint8_t estadoGarra; // Definida en gripper_driver.c ahora, o si la dejaste en main.c
extern int homeStatus;      // La usabas en main.c, quizás debas definirla aquí o traerla con extern
// Variable externa que vive en main.c
extern uint8_t robotCalibrated;

// Variables locales de ayuda
uint8_t homeMotor_X = 0;
uint8_t homeMotor_Y = 0;
uint8_t homeMotor_Z = 0;
int homeStatus_Local = 0; // Para guardar resultado de homing

// --- Implementación ---

void Robot_Consignas(void){
    // Usamos la función segura USB_Print
    sprintf(buffer_tx, "Existen 3 modos de comportamiento para el robot\r\n"); USB_Print(buffer_tx);
    sprintf(buffer_tx, "CALIBRACION (-), APRENDIZAJE (+) y EJECUCION (#)\r\n"); USB_Print(buffer_tx);
    sprintf(buffer_tx, "Comandos: :-H (Home), :-V045 (Vel Global), :-E1 (Enable)\r\n"); USB_Print(buffer_tx);
    sprintf(buffer_tx, "          :-vX023Y100Z078 (Vel individual), :-S (Stop)\r\n"); USB_Print(buffer_tx);
}

uint8_t Robot_ModoCalibracion(void){
      // CASO DE HOMING
      if (buffer_rx[2] == 'H'){
          HAL_GPIO_WritePin(Wait_led_GPIO_Port, Wait_led_Pin, SET);
          HAL_GPIO_WritePin(Finish_led_GPIO_Port, Finish_led_Pin, RESET);

          Lcd_Clear();
          Lcd_Set_Cursor(1,1); Lcd_Send_String("Start Homing");

          Gripper_Close(); // Usando el nuevo driver
          robotCalibrated = 0; // Mientras se mueve, es desconocido

          // Llamada al driver de homing
          homeStatus_Local = HomingMotors(&homeMotor_X, &homeMotor_Y, &homeMotor_Z);

          Lcd_Clear();
          if (homeStatus_Local == 0){
        	  robotCalibrated = 1; // <--- ¡ÉXITO!
              sprintf(buffer_tx, "Home exitoso!\r\n"); USB_Print(buffer_tx);
              Lcd_Set_Cursor(1,1); Lcd_Send_String("Home Status: OK");
              HAL_GPIO_WritePin(Home_led_GPIO_Port, Home_led_Pin, SET);
          } else {
              sprintf(buffer_tx, "Falla Home Error: %d\r\n", homeStatus_Local); USB_Print(buffer_tx);
              Lcd_Set_Cursor(1,1); Lcd_Send_String("Home Error!");
          }
          return 0;
      }

      // CASO VELOCIDAD GLOBAL (:-V058)
      else if (buffer_rx[2] == 'V'){
          CDC_FS_Substring(3, 5, buffer_rx, buffer_data[0]);
          uint8_t velocidad = (uint8_t)atoi(buffer_data[0]);
          if (velocidad <= 100){
              int vel = velocidad;
              // Actualizamos todos los motores
              for(int i=0; i<NUM_MOTORS; i++) moveMotors(&motors[i], 0, &vel);

              sprintf(buffer_tx, "Velocidad global: %d%%\r\n", velocidad); USB_Print(buffer_tx);
          }
          return 0;
      }

      // CASO VELOCIDAD INDIVIDUAL (:-vX...)
      else if (buffer_rx[2] == 'v'){
           // (Aquí va tu lógica de parsing de velocidades individuales usando CDC_FS_Substring)
           // ... recuerda usar moveMotors(&motors[i], 0, &vel_individual);
           sprintf(buffer_tx, "Velocidades individuales seteadas.\r\n"); USB_Print(buffer_tx);
           return 0;
      }

      // CASO ENABLE/DISABLE (:-E1 / :-E0)
      else if (buffer_rx[2] == 'E'){
          CDC_FS_Substring(3, 3, buffer_rx, buffer_data[0]);
          int state = atoi(buffer_data[0]);
          ActivatedAll(state);
          sprintf(buffer_tx, "Motores estado: %d\r\n", state); USB_Print(buffer_tx);
          return 0;
      }

      // CASO STOP (:-S)
      else if (buffer_rx[2] == 'S'){
          ActivatedAll(-1); // Parada emergencia
          sprintf(buffer_tx, "STOP EMERGENCIA\r\n"); USB_Print(buffer_tx);
          return 0;
      }

      return 1;
}

uint8_t Robot_ModoAprendizaje(void){
    // CASO MOVER A POSICION ('D')
    if (buffer_rx[0] == 'D'){ // Ojo: Ajusta según tu protocolo exacto (en tu main original usabas buffer_data[0][0])
         char posStr[5];
         // Ejemplo parsing X
         CDC_FS_Substring(2, 4, buffer_rx, posStr);
         int posX = atoi(posStr);

         // Actualizar newPosition en motores
         int pX = posX; // Casting si es necesario
         moveMotors(&motors[0], &pX, 0);

         // ... Repetir para Y y Z ...
    }
    // CASO GRIPPER ('P')
    else if (buffer_rx[0] == 'P'){
         CDC_FS_Substring(2, 4, buffer_rx, buffer_data[2]);
         int angulo = atoi(buffer_data[2]);
         Gripper_SetAngle(angulo);
         sprintf(buffer_tx, "Gripper a %d grados\r\n", angulo); USB_Print(buffer_tx);
    }
    return 1;
}

// Nota: Modo Ejecución suele ser igual a Aprendizaje pero quizás sin guardar datos
uint8_t Robot_ModoEjecucion(void){
    return Robot_ModoAprendizaje(); // Reutilizamos lógica si es idéntica
}

void Robot_ProcesarComando(char *cmd){
    // Este switch gigante estaba en tu main.c
    if (cmd[0] == ':'){
        switch (cmd[1]){
            case '-':
                sprintf(buffer_tx, "Modo Calibracion\r\n"); USB_Print(buffer_tx);
                Robot_ModoCalibracion();
                break;
            case '+':
                sprintf(buffer_tx, "Modo Aprendizaje\r\n"); USB_Print(buffer_tx);
                Robot_ModoAprendizaje();
                break;
            case '#':
                sprintf(buffer_tx, "Modo Ejecucion\r\n"); USB_Print(buffer_tx);
                Robot_ModoEjecucion();
                break;
            case '?':
                Robot_Consignas();
                break;
            default:
                sprintf(buffer_tx, "Comando desconocido\r\n"); USB_Print(buffer_tx);
                break;
        }
    } else if (cmd[0] == '?'){
        Robot_Consignas();
    }
}
