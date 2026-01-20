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
extern uint8_t robotCalibrated;
extern StepperMotor motors[];
extern char buffer_rx[40];
extern char buffer_tx[60];
extern char buffer_data[4][6];
extern uint8_t estadoGarra; // Definida en gripper_driver.c ahora, o si la dejaste en main.c
extern int homeStatus;      // La usabas en main.c, quizás debas definirla aquí o traerla con extern
// Tiempos para no saturar el puerto serie
uint32_t lastTelemetryCheck = 0;
uint32_t lastTelemetrySentTime = 0;

// Variables para recordar el estado anterior (static mantiene el valor entre llamadas)
static int prevX = -99999;
static int prevY = -99999;
static int prevZ = -99999;
static uint8_t prevSensors = 0xFF; // Valor imposible para forzar primer envío
static uint8_t prevCalib = 0xFF;
static uint8_t prevMoving = 0xFF;

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

      	  	  // 1. COMANDO HOMING (:-H)
      	  // Busca los sensores físicos para establecer el cero real de máquina.
		if (buffer_rx[2] == 'H'){
	          // 1. FORZAR LED DE "OCUPADO" (Wait)
	          HAL_GPIO_WritePin(Wait_led_GPIO_Port, Wait_led_Pin, GPIO_PIN_SET);

	          robotCalibrated = 0;

	          // Imprimimos mensaje inicial
	          USB_Print("STATUS|Homing...|M:1\r\n"); // M:1 fuerza al PC a saber que se mueve
	          Lcd_Clear();
	          Lcd_Set_Cursor(1,1); Lcd_Send_String("Homing...");

	          // 2. Ejecutar rutina (Bloqueante)
	          homeStatus_Local = HomingMotors(&homeMotor_X, &homeMotor_Y, &homeMotor_Z);

	          // 3. APAGAR LED DE "OCUPADO"
	          HAL_GPIO_WritePin(Wait_led_GPIO_Port, Wait_led_Pin, GPIO_PIN_RESET);

	          if (homeStatus_Local == 0){
	              robotCalibrated = 1;
	              // Al terminar, enviamos status final con Home OK (C:1) y Movimiento OFF (M:0)
	              // Esto actualizará la interfaz automáticamente
	              Robot_UpdateTelemetry();

	              sprintf(buffer_tx, "Homing OK\r\n"); USB_Print(buffer_tx);
	              Lcd_Set_Cursor(1,1); Lcd_Send_String("Home Status: OK");
	              HAL_GPIO_WritePin(Home_led_GPIO_Port, Home_led_Pin, GPIO_PIN_SET);
	          } else {
              sprintf(buffer_tx, "Homing Error: %d\r\n", homeStatus_Local); USB_Print(buffer_tx);
              Lcd_Set_Cursor(1,1); Lcd_Send_String("Home Error!");
          }

          HAL_GPIO_WritePin(Wait_led_GPIO_Port, Wait_led_Pin, GPIO_PIN_RESET);
          return 0;
      }

      // 2. COMANDO SET ZERO (:-Z)
      // Fuerza la posición actual como el nuevo (0,0,0) LÓGICO.
      else if (buffer_rx[2] == 'Z'){

          // Resetear variables de posición de todos los motores
          for(int i=0; i<NUM_MOTORS; i++){
              motors[i].currentPosition = 0;
              motors[i].newPosition = 0;
              // Opcional: Resetear acumuladores de pasos si tu driver los usa
              motors[i].stepCounter = 0;
          }

          robotCalibrated = 1; // Ahora sí sabemos dónde estamos (en el 0)

          sprintf(buffer_tx, "Set Zero OK. Posicion actual = 0,0,0\r\n");
          USB_Print(buffer_tx);
          return 0;
      }

      // 3. CONFIGURAR APERTURA GARRA (:-A120)
      else if (buffer_rx[2] == 'A'){
          int angulo = atoi(&buffer_rx[3]);
          Gripper_SetOpenAngle((uint16_t)angulo);

          sprintf(buffer_tx, "Config. Apertura: %d grados\r\n", angulo);
          USB_Print(buffer_tx);
          return 0;
      }

      // 4. CONFIGURAR CIERRE GARRA (:-P90)
      else if (buffer_rx[2] == 'P'){
          int angulo = atoi(&buffer_rx[3]);
          Gripper_SetClosedAngle((uint16_t)angulo);

          sprintf(buffer_tx, "Config. Cierre: %d grados\r\n", angulo);
          USB_Print(buffer_tx);
          return 0;
      }

      // 5. ENABLE/DISABLE MOTORES (:-E1 / :-E0)
      else if (buffer_rx[2] == 'E'){
          // Corregimos el índice del substring a (3, 4) para capturar el número
          CDC_FS_Substring(3, 4, buffer_rx, buffer_data[0]);
          int state = atoi(buffer_data[0]);

          ActivatedAll(state); // 1=Enable, 0=Disable

          sprintf(buffer_tx, "Motores Enable: %d\r\n", state);
          USB_Print(buffer_tx);
          return 0;
      }

      // 6. VELOCIDAD GLOBAL (:-V050)
      else if (buffer_rx[2] == 'V'){
          CDC_FS_Substring(3, 5, buffer_rx, buffer_data[0]); // Lee 2 dígitos (ej 50) o 3 (100)
          int velocidad = atoi(buffer_data[0]);

          if (velocidad > 0 && velocidad <= 100){
              // Aplicamos velocidad base a todos (para movimientos manuales futuros)
              for(int i=0; i<NUM_MOTORS; i++) {
                   // Nota: Esto cambia la velocidad actual.
                   // Si quieres solo cambiar la "por defecto", usa una variable global.
                   // Pero cambiar la actual está bien si están parados.
                   motors[i].velocity = velocidad;
              }
              sprintf(buffer_tx, "Velocidad Global: %d%%\r\n", velocidad); USB_Print(buffer_tx);
          }
          return 0;
      }

      // 7. STOP EMERGENCIA (:-S)
      else if (buffer_rx[2] == 'S'){
          ActivatedAll(-1); // Función que deshabilita o para todo
          sprintf(buffer_tx, "STOP CALIBRACION\r\n"); USB_Print(buffer_tx);
          return 0;
      }

      return 1; // Comando no reconocido en este modo
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
    }

    return 1;
}
uint8_t Robot_ModoEjecucion(void){
    // Formato: :#X200|Y200|C

    int x = BuscarValor('X', buffer_rx);
    int y = BuscarValor('Y', buffer_rx);
    int z = BuscarValor('Z', buffer_rx);

    // DEFINIR UNA VELOCIDAD POR DEFECTO PARA MOVIMIENTOS
    int velDefecto = 50; // 50% de velocidad (ajusta según necesites)

    // Validamos que al menos se haya enviado alguna coordenada
    if (x >= 0 || y >= 0 || z >= 0) {

        // Al llamar a moveMotors, pasamos &velDefecto en lugar de 0
        // Así aseguramos que el motor despierte del estado de reposo (vel=0)

        if (x >= 0) moveMotors(&motors[0], &x, &velDefecto);
        if (y >= 0) moveMotors(&motors[1], &y, &velDefecto);
        if (z >= 0) moveMotors(&motors[2], &z, &velDefecto);

        // Leemos estado actual real
		int curX = motors[0].currentPosition;
		int curY = motors[1].currentPosition;
		int curZ = motors[2].currentPosition;
		// Asumimos que tienes una variable global 'velocidadGlobal' o lees la de un motor
		int curVel = motors[0].velocity;
		// Variable global de estado garra (0 o 1) o un char
		char estadoGarra = (HAL_GPIO_ReadPin(Gripper_pin_GPIO_Port, Gripper_pin_Pin) == GPIO_PIN_SET) ? 'A' : 'C';

		sprintf(buffer_tx, "Ejecutando -> X:%d Y:%d Z:%d V:%d G:%c\r\n",
				curX, curY, curZ, curVel, estadoGarra);
		USB_Print(buffer_tx);
    }

    // Control de Garra
    if (strchr(buffer_rx, 'C') != NULL) {
        Gripper_Close();
        USB_Print("Garra: Cerrada\r\n");
    }
    else if (strchr(buffer_rx, 'A') != NULL) {
        Gripper_Open();
        USB_Print("Garra: Abierta\r\n");
    }

    return 0;
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
void Robot_UpdateTelemetry(void) {
    // Revisar cada 50ms (más rápido que antes, pero solo envía si hay cambios)
    if (HAL_GetTick() - lastTelemetryCheck < 50) return;
    lastTelemetryCheck = HAL_GetTick();

    // 1. LECTURA DE ESTADO ACTUAL
    // ---------------------------------------------------------
    int currX = motors[0].currentPosition;
    int currY = motors[1].currentPosition;
    int currZ = motors[2].currentPosition;

    // Leemos sensores (Lógica inversa: 1 si toca, 0 si no)
    uint8_t sX = (HAL_GPIO_ReadPin(StopM_X_GPIO_Port, StopM_X_Pin) == GPIO_PIN_RESET) ? 1 : 0;
    uint8_t sY = (HAL_GPIO_ReadPin(StopM_Y_GPIO_Port, StopM_Y_Pin) == GPIO_PIN_RESET) ? 1 : 0;
    uint8_t sZ = (HAL_GPIO_ReadPin(StopM_Z_GPIO_Port, StopM_Z_Pin) == GPIO_PIN_RESET) ? 1 : 0;

    // Empaquetamos sensores en un byte para fácil comparación (Bits: 0000 0ZYX)
    uint8_t currSensors = (sZ << 2) | (sY << 1) | (sX);

    // Estado de movimiento (Si alguno tiene velocidad > 0)
    uint8_t currMoving = (motors[0].velocity > 0 || motors[1].velocity > 0 || motors[2].velocity > 0);

    // Estado calibración
    uint8_t currCalib = robotCalibrated;

    // 2. GESTIÓN DE LEDS FÍSICOS (En la placa)
    // ---------------------------------------------------------
    HAL_GPIO_WritePin(Home_led_GPIO_Port, Home_led_Pin, currCalib ? GPIO_PIN_SET : GPIO_PIN_RESET);
    HAL_GPIO_WritePin(Wait_led_GPIO_Port, Wait_led_Pin, currMoving ? GPIO_PIN_SET : GPIO_PIN_RESET);
    // (Opcional) Finish Led podría ser parpadeo, aquí lo dejamos apagado por ahora
    // HAL_GPIO_WritePin(Finish_led_GPIO_Port, Finish_led_Pin, GPIO_PIN_RESET);


    // 3. DETECCIÓN DE CAMBIOS Y ENVÍO SERIAL
    // ---------------------------------------------------------
    uint8_t hasChanged = 0;

    if (currX != prevX) hasChanged = 1;
    if (currY != prevY) hasChanged = 1;
    if (currZ != prevZ) hasChanged = 1;
    if (currSensors != prevSensors) hasChanged = 1;
    if (currCalib != prevCalib) hasChanged = 1;
    if (currMoving != prevMoving) hasChanged = 1;

    // Condición de "Heartbeat": Si pasaron 2 segundos (2000ms) sin enviar, forzar envío
    uint8_t forceHeartbeat = (HAL_GetTick() - lastTelemetrySentTime > 2000);

    if (hasChanged || forceHeartbeat) {
        char msg[100];
        // AGREGAMOS MÁS DATOS A LA TRAMA:
        // C: Calibrado (0/1)
        // M: Moviendo (0/1)
        sprintf(msg, "STATUS|X:%d|Y:%d|Z:%d|S:%d%d%d|C:%d|M:%d\r\n",
                currX, currY, currZ,
                sX, sY, sZ,
                currCalib, currMoving);

        USB_Print(msg);

        // Actualizar estado previo
        prevX = currX; prevY = currY; prevZ = currZ;
        prevSensors = currSensors;
        prevCalib = currCalib;
        prevMoving = currMoving;

        lastTelemetrySentTime = HAL_GetTick();
    }
}
