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
extern char buffer_tx[80];
extern char buffer_data[4][6];
extern uint8_t estadoGarra; // Definida en gripper_driver.c ahora, o si la dejaste en main.c
extern int homeStatus;      // La usabas en main.c, quizás debas definirla aquí o traerla con extern
// Tiempos para no saturar el puerto serie
uint32_t lastTelemetryCheck = 0;
uint32_t lastTelemetrySentTime = 0;

// Asegúrate de tener acceso a la variable de estado
extern volatile uint8_t robotState;

// Ventana temporal del aviso de comunicación USB en el LCD (definida en main.c)
extern volatile uint32_t usbGreetingUntil;

// Variables para recordar el estado anterior (static mantiene el valor entre llamadas)
static int prevX = -99999;
static int prevY = -99999;
static int prevZ = -99999;
static uint8_t prevSensors = 0xFF; // Valor imposible para forzar primer envío
static uint8_t prevCalib = 0xFF;
static uint8_t prevMoving = 0xFF;
static uint8_t prevEstop = 0xFF;

// Variables locales de ayuda
uint8_t homeMotor_X = 0;
uint8_t homeMotor_Y = 0;
uint8_t homeMotor_Z = 0;
int homeStatus_Local = 0; // Para guardar resultado de homing
int velocidadGlobal = DEFAULT_GLOBAL_VELOCITY; // Default para que el primer jog mueva sin :-V previo


// Bandera de fallo de homing: cuando != 0, el bucle principal hace parpadear el
// LED de Home físico y la interfaz resalta el error. Se limpia al reintentar
// homing o al calibrar por :-Z. (Definida aquí, usada también en main.c).
volatile uint8_t homingFailed = 0;

// Latido de las esperas bloqueantes del homing (declarado en motor_driver.h).
// HomingMotors() no devuelve el control al bucle principal hasta terminar, así que
// sin esto la interfaz pasa toda la calibración a ciegas: no recibe ninguna trama
// STATUS y los LEDs de finales de carrera nunca se encienden (el back-off ya los
// liberó cuando por fin llega la primera). Reusa el throttle de 50 ms de
// Robot_UpdateTelemetry(), así que no satura el CDC por más seguido que se llame.
void Motor_HomingTick(void) {
    Robot_UpdateTelemetry();
    Robot_ReportInterrupts();
}

// Recorta un destino al recorrido real del eje (0 .. motorMaxPos[idx]) y avisa por
// consola cuando hubo que hacerlo. El fin de carrera sólo protege el lado de HOME:
// del otro lado, hasta ahora, se aceptaba cualquier número que mandara el PC.
// Devuelve el valor ya acotado.
static int Robot_LimitarDestino(int idx, int destino) {
    const char eje = (idx == 0) ? 'X' : (idx == 1) ? 'Y' : 'Z';
    int limitado = destino;

    if (limitado > motorMaxPos[idx]) limitado = motorMaxPos[idx];
    if (limitado < 0)                limitado = 0;

    if (limitado != destino) {
        sprintf(buffer_tx, "AVISO|Limite de eje %c: pedido %d, recortado a %d\r\n",
                eje, destino, limitado);
        USB_Print(buffer_tx);
    }
    return limitado;
}

// Devuelve una descripción legible del código de error de homing (no solo el número).
const char* Robot_HomingErrorStr(int code){
    switch (code) {
        case  -1: return "eje X no encontro su fin de carrera (timeout)";
        case  -2: return "eje Y no encontro su fin de carrera (timeout)";
        case  -3: return "eje Z no encontro su fin de carrera (timeout)";
        case -11: return "eje X: el fin de carrera no se libera (revisar sensor/mecanica)";
        case -12: return "eje Y: el fin de carrera no se libera (revisar sensor/mecanica)";
        case -13: return "eje Z: el fin de carrera no se libera (revisar sensor/mecanica)";
        case  -9: return "ABORTADO por PARO DE EMERGENCIA";
        default : return "error de homing desconocido";
    }
}

// --- Implementación ---

// CAPA 1 de la ayuda: lista TODOS los comandos que interpreta el STM32.
// Para un ejemplo puntual, pedir la CAPA 2 con :-?<Letra> (ej: :-?V).
void Robot_Consignas(void){
    USB_Print("=== COMANDOS T.A.I.L.S. (STM32) ===\r\n");
    USB_Print("Todo comando empieza con ':' y termina en Enter.\r\n");
    USB_Print("-- Calibracion / Config (:-) --\r\n");
    USB_Print("  :-H         Homing (busca los 3 fines de carrera)\r\n");
    USB_Print("  :-Z         Set Zero: fija (0,0,0) en la posicion actual\r\n");
    USB_Print("  :-A<grados> Angulo de apertura de garra (ej :-A120)\r\n");
    USB_Print("  :-P<grados> Angulo de cierre de garra (ej :-P030)\r\n");
    USB_Print("  :-E<0|1>    Enable motores (1=torque ON, 0=OFF)\r\n");
    USB_Print("  :-V<nnn>    Velocidad global % 010..100 (ej :-V050)\r\n");
    USB_Print("  :-S         PARO de emergencia (se libera con :-R)\r\n");
    USB_Print("  :-R         Rearmar tras E-STOP (pide recalibrar)\r\n");
    USB_Print("  :-I         Handshake (responde TAILS USB OK)\r\n");
    USB_Print("-- Movimiento (:#) --\r\n");
    USB_Print("  :#X..Y..Z..[V..][|A|C]  Mover a posicion absoluta (pasos)\r\n");
    USB_Print("-- Test / Diagnostico (:*) --\r\n");
    USB_Print("  :*L<H|W|F|P><0|1>  Prender/apagar un LED\r\n");
    USB_Print("  :*M<X|Y|Z><+|-><nnn>  Mover un motor (pasos relativos)\r\n");
    USB_Print("  :*G<A|C>           Garra: Abrir / Cerrar\r\n");
    USB_Print("-- Ayuda --\r\n");
    USB_Print("  :-?         Esta lista | :-?<Letra> ejemplo (ej :-?V)\r\n");
}

// CAPA 2 de la ayuda: ejemplo concreto de un comando puntual.
void Robot_ComandoEjemplo(char c){
    switch (c) {
        case 'H': USB_Print("Ej :-H   -> Homing: referencia los 3 ejes\r\n"); break;
        case 'Z': USB_Print("Ej :-Z   -> fija la posicion actual como (0,0,0)\r\n"); break;
        case 'A': USB_Print("Ej :-A120 -> apertura de garra = 120 grados\r\n"); break;
        case 'P': USB_Print("Ej :-P030 -> cierre de garra = 30 grados\r\n"); break;
        case 'E': USB_Print("Ej :-E1 (torque ON) / :-E0 (torque OFF)\r\n"); break;
        case 'V': USB_Print("Ej :-V050 -> velocidad global 50% (rango 010..100)\r\n"); break;
        case 'S': USB_Print("Ej :-S   -> PARO de emergencia (liberar con :-R)\r\n"); break;
        case 'R': USB_Print("Ej :-R   -> rearma tras un E-STOP\r\n"); break;
        case 'I': USB_Print("Ej :-I   -> handshake, responde TAILS USB OK\r\n"); break;
        case '#': USB_Print("Ej :#X200Y150Z050V050|C -> mover XYZ, vel 50%, cerrar garra\r\n"); break;
        case 'M': USB_Print("Ej :*MX+100 -> (TEST) mueve X +100 pasos | :*MZ-050\r\n"); break;
        case 'L': USB_Print("Ej :*LH1 -> (TEST) LED Home ON | :*LW0 -> LED Wait OFF\r\n"); break;
        case 'G': USB_Print("Ej :*GA -> (TEST) abrir garra | :*GC -> cerrar garra\r\n"); break;
        default : USB_Print("Sin ejemplo para ese comando. Envie :-? para la lista.\r\n"); break;
    }
}

uint8_t Robot_ModoCalibracion(void){

      	  	  // 1. COMANDO HOMING (:-H)
      	  // Busca los sensores físicos para establecer el cero real de máquina.
		if (buffer_rx[2] == 'H'){
	          // 1. FORZAR LED DE "OCUPADO" (Wait) y apagar el de tarea terminada:
	          //    arranca una tarea nueva, lo anterior ya no está "finalizado".
	          HAL_GPIO_WritePin(Wait_led_GPIO_Port, Wait_led_Pin, GPIO_PIN_SET);
	          HAL_GPIO_WritePin(Finish_led_GPIO_Port, Finish_led_Pin, GPIO_PIN_RESET);

	          robotCalibrated = 0;
	          homingFailed = 0; // Reintento: limpiamos cualquier fallo previo (apaga parpadeo)

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
	              homingFailed = 0; // Éxito: sin parpadeo de error
	              // Al terminar, enviamos status final con Home OK (C:1) y Movimiento OFF (M:0)
	              // Esto actualizará la interfaz automáticamente
	              Robot_UpdateTelemetry();

	              sprintf(buffer_tx, "Homing OK\r\n"); USB_Print(buffer_tx);
	              Lcd_Set_Cursor(1,1); Lcd_Send_String("Home Status: OK");
	              HAL_GPIO_WritePin(Home_led_GPIO_Port, Home_led_Pin, GPIO_PIN_SET);

	              // FINISH: el homing es bloqueante, así que la telemetría no corre
	              // mientras dura y el flanco de "dejó de moverse" se pierde. Lo
	              // encendemos acá para que el fin de calibración también lo marque.
	              HAL_GPIO_WritePin(Finish_led_GPIO_Port, Finish_led_Pin, GPIO_PIN_SET);
	          } else {
              // Marcamos el fallo (el LED de Home parpadea desde el bucle principal) e
              // imprimimos DESCRIPCIÓN + código, no solo el número.
              homingFailed = 1;
              sprintf(buffer_tx, "Homing Error %d: %s\r\n",
                      homeStatus_Local, Robot_HomingErrorStr(homeStatus_Local));
              USB_Print(buffer_tx);
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
          homingFailed = 0;    // Calibrado manual: apaga el parpadeo de error

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

		// 6. VELOCIDAD GLOBAL (:-V100)
	  else if (buffer_rx[2] == 'V'){
		  // CORRECCIÓN 1: Leer 3 dígitos (índices 3, 4, 5). El fin es 6.
		  CDC_FS_Substring(3, 6, buffer_rx, buffer_data[0]);

		  int porcentaje = atoi(buffer_data[0]); // Esto nos da 10 a 100

		  if (porcentaje >= 10 && porcentaje <= 100){

			  // CORRECCIÓN 2: Escalado.
			  // Si porcentaje es 100, velocidad = 1000.
			  // Si porcentaje es 10, velocidad = 100.
			  int nuevaVelocidad = porcentaje * 10;

			  // (Opcional) Si quieres forzar que el mínimo sea idéntico al homing (20):
			  if (porcentaje <= 10) nuevaVelocidad = 20;

			  // Guardamos en la variable global para futuros movimientos (:#...)
			  velocidadGlobal = nuevaVelocidad;

			  // Aplicamos inmediatamente por si queremos movernos ahora mismo
			  for(int i=0; i<NUM_MOTORS; i++) {
				   motors[i].velocity = velocidadGlobal;
			  }

			  sprintf(buffer_tx, "Velocidad Set: %d%% (%d pps)\r\n", porcentaje, nuevaVelocidad);
			  USB_Print(buffer_tx);
		  }
		  return 0;
	  }

      // 7. STOP EMERGENCIA (:-S)
      // Misma respuesta que el botón físico: frena y engancha el bloqueo E-STOP.
      else if (buffer_rx[2] == 'S'){
          Motor_EmergencyStop();
          sprintf(buffer_tx, "E-STOP (SW). Envie :-R para reiniciar.\r\n"); USB_Print(buffer_tx);
          return 0;
      }

      // 8. AYUDA DE COMANDOS EN 2 CAPAS (:-? lista, :-?<Letra> ejemplo)
      else if (buffer_rx[2] == '?'){
          char sel = buffer_rx[3];
          if (sel == '\0' || sel == '\r' || sel == '\n') {
              Robot_Consignas();          // CAPA 1: lista completa
          } else {
              Robot_ComandoEjemplo(sel);  // CAPA 2: ejemplo puntual
          }
          return 0;
      }

      // 9. HANDSHAKE / IDENTIFICACIÓN (:-I)
      // Lo envía la interfaz al conectar. Respondemos identificación y mostramos
      // un aviso temporal en el LCD de que se estableció la comunicación USB.
      else if (buffer_rx[2] == 'I'){
          usbGreetingUntil = HAL_GetTick() + 2500; // Aviso en LCD por ~2.5 s (no bloqueante)
          USB_Print("TAILS USB OK\r\n");
          // Diagnóstico del LCD: informamos si se detectó y en qué dirección I2C.
          // Ayuda a saber si "el LCD no responde" es dirección equivocada o cableado.
          if (Lcd_IsPresent()) {
              sprintf(buffer_tx, "LCD OK (I2C 0x%02X)\r\n", Lcd_GetAddress());
          } else {
              sprintf(buffer_tx, "LCD NO DETECTADO (revisar cableado/contraste)\r\n");
          }
          USB_Print(buffer_tx);
          return 0;
      }

      return 1; // Comando no reconocido en este modo
}

uint8_t Robot_ModoAprendizaje(void){
    // El aprendizaje se gestiona por PC: la interfaz mueve cada eje con jog (:#X/Y/Z),
    // guarda el punto (x,y,z + estado de garra) y arma la trayectoria en JSON.
    // El firmware NO debe generar movimiento propio en el modo '+': solo responde.
    USB_Print("Aprendizaje se gestiona por PC (jog :#). '+' sin accion.\r\n");
    return 1;
}
uint8_t Robot_ModoEjecucion(void){
    // Formato: :#X200Y200Z050V050|C  (V = velocidad del segmento en %, opcional)

    int x = BuscarValor('X', buffer_rx);
    int y = BuscarValor('Y', buffer_rx);
    int z = BuscarValor('Z', buffer_rx);

    // Velocidad del segmento embebida (opcional). Si viene V entre 10 y 100,
    // fija la velocidad global de este movimiento (misma escala que :-V => %*10).
    int vpct = BuscarValor('V', buffer_rx);
    if (vpct >= 10 && vpct <= 100) {
        velocidadGlobal = vpct * 10;
    }

    // Validamos que al menos se haya enviado alguna coordenada
    if (x >= 0 || y >= 0 || z >= 0) {

        // LÍMITES ARTICULARES: recortamos el destino ANTES de mandarlo al driver.
        // Se recorta acá y no dentro de moveMotors() porque esa función recibe un
        // StepperMotor* suelto y no sabe qué eje es. Sólo con el robot calibrado:
        // sin homing los pasos no tienen referencia física contra la que comparar.
        if (robotCalibrated) {
            if (x >= 0) x = Robot_LimitarDestino(0, x);
            if (y >= 0) y = Robot_LimitarDestino(1, y);
            if (z >= 0) z = Robot_LimitarDestino(2, z);
        }

        // Al llamar a moveMotors, pasamos &velDefecto en lugar de 0
        // Así aseguramos que el motor despierte del estado de reposo (vel=0)
    	if (x >= 0) moveMotors(&motors[0], &x, &velocidadGlobal);
		if (y >= 0) moveMotors(&motors[1], &y, &velocidadGlobal);
		if (z >= 0) moveMotors(&motors[2], &z, &velocidadGlobal);

        // Leemos estado actual real
		int curX = motors[0].currentPosition;
		int curY = motors[1].currentPosition;
		int curZ = motors[2].currentPosition;
		// Asumimos que tienes una variable global 'velocidadGlobal' o lees la de un motor
		int curVel = motors[0].velocity;
		// Estado real de la garra desde la variable global del driver (1=Abierta, 0=Cerrada).
		// No se lee el pin: es salida PWM (TIM4_CH4) y su IDR no es fiable.
		char garra = (estadoGarra == 1) ? 'A' : 'C';

		sprintf(buffer_tx, "Ejecutando -> X:%d Y:%d Z:%d V:%d G:%c\r\n",
				curX, curY, curZ, curVel, garra);
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

// ============================================================
// MODO TEST / DIAGNÓSTICO (prefijo :*)
// Pensado para el panel de pruebas de la interfaz: permite ejercitar el hardware
// de a una parte por vez (cada LED, cada motor, la garra) sin depender de una
// rutina ni de la calibración. Útil para verificar conexiones y cableado.
// ============================================================
uint8_t Robot_ModoTest(void){

    // --- :*L<C><S>  Prender/apagar un LED ---
    if (buffer_rx[2] == 'L') {
        char c = buffer_rx[3];               // H=Home, W=Wait, F=Finish, P=LED de placa
        GPIO_PinState st = (buffer_rx[4] == '1') ? GPIO_PIN_SET : GPIO_PIN_RESET;
        const char* nombre = "?";

        switch (c) {
            case 'H': HAL_GPIO_WritePin(Home_led_GPIO_Port,   Home_led_Pin,   st); nombre = "Home";   break;
            case 'W': HAL_GPIO_WritePin(Wait_led_GPIO_Port,   Wait_led_Pin,   st); nombre = "Wait";   break;
            case 'F': HAL_GPIO_WritePin(Finish_led_GPIO_Port, Finish_led_Pin, st); nombre = "Finish"; break;
            case 'P': HAL_GPIO_WritePin(LedPcb_GPIO_Port,     LedPcb_Pin,     st); nombre = "Placa";  break;
            default:
                USB_Print("TEST: LED invalido (use H/W/F/P)\r\n");
                return 0;
        }
        sprintf(buffer_tx, "TEST: LED %s -> %s\r\n", nombre, (buffer_rx[4]=='1') ? "ON" : "OFF");
        USB_Print(buffer_tx);
        return 0;
    }

    // --- :*M<A><+|-><nnn>  Mover un motor de forma relativa (jog de prueba) ---
    else if (buffer_rx[2] == 'M') {
        char axis = buffer_rx[3];            // X / Y / Z
        char sign = buffer_rx[4];            // + / -
        int steps = atoi(&buffer_rx[5]);     // cantidad de pasos
        int idx = (axis == 'X') ? 0 : (axis == 'Y') ? 1 : (axis == 'Z') ? 2 : -1;

        if (idx < 0) { USB_Print("TEST: eje invalido (use X/Y/Z)\r\n"); return 0; }
        if (steps <= 0) { USB_Print("TEST: pasos invalidos (>0)\r\n"); return 0; }

        int delta  = (sign == '-') ? -steps : steps;
        int target = motors[idx].currentPosition + delta;
        // El jog de test también respeta el tope articular (si hay referencia).
        if (robotCalibrated) target = Robot_LimitarDestino(idx, target);
        moveMotors(&motors[idx], &target, &velocidadGlobal);

        sprintf(buffer_tx, "TEST: motor %c %c%d pasos (destino %d)\r\n",
                axis, (sign == '-') ? '-' : '+', steps, target);
        USB_Print(buffer_tx);
        return 0;
    }

    // --- :*G<A|C>  Garra abrir/cerrar ---
    else if (buffer_rx[2] == 'G') {
        if (buffer_rx[3] == 'A')      { Gripper_Open();  USB_Print("TEST: garra ABIERTA\r\n"); }
        else if (buffer_rx[3] == 'C') { Gripper_Close(); USB_Print("TEST: garra CERRADA\r\n"); }
        else                          { USB_Print("TEST: garra invalida (use A/C)\r\n"); }
        return 0;
    }

    USB_Print("TEST: comando :* no reconocido (L/M/G)\r\n");
    return 1;
}

void Robot_ProcesarComando(char *cmd){

    // ============================================================
    // 1. ZONA DE SEGURIDAD (BLOQUEO POR E-STOP)
    // ============================================================
    if (robotState == STATE_ESTOP) {
        // En este estado, el robot es un ladrillo. Solo escucha un comando.

        // Verificamos si es el comando de REINICIO (:-R)
        if (cmd[0] == ':' && cmd[1] == '-' && cmd[2] == 'R') {

            // --- PROCEDIMIENTO DE DESBLOQUEO ---
            robotState = STATE_IDLE; // 1. Volvemos al estado normal

            // 2. Reactivamos los drivers (torque)
            ActivatedAll(1);

            // 3. Feedback al usuario
            sprintf(buffer_tx, "SISTEMA DESBLOQUEADO. RECALIBRAR.\r\n");
            USB_Print(buffer_tx);

            // 4. Limpiamos el LCD inmediatamente (opcional, o dejamos que main lo haga)
            Lcd_Clear();
            Lcd_Set_Cursor(1,1); Lcd_Send_String("System Unlocked");
        }
        // El propio :-S que disparó la parada llega hasta acá (ya lo enganchó la
        // ISR de USB). No es un error: confirmamos el E-STOP por software.
        else if (cmd[0] == ':' && cmd[1] == '-' && cmd[2] == 'S') {
            sprintf(buffer_tx, "E-STOP (SW) enganchado. Envie :-R para reiniciar.\r\n");
            USB_Print(buffer_tx);
        }
        else {
            // CUALQUIER OTRO COMANDO SE RECHAZA
            sprintf(buffer_tx, "ERROR: E-STOP ACTIVO. ENVIE ':-R' PARA REINICIAR.\r\n");
            USB_Print(buffer_tx);
        }
        return; // ¡IMPORTANTE! Salimos aquí para no ejecutar nada más.
    }

    // ============================================================
    // 2. PROCESAMIENTO NORMAL (Si no hay emergencia)
    // ============================================================
    if (cmd[0] == ':'){
        switch (cmd[1]){
            case '-':
                // Comandos de Configuración
                if (cmd[2] == 'H') {
                     // Guarda de reentrada: HomingMotors() es BLOQUEANTE. Si el
                     // operador aprieta HOME varias veces seguidas, cada :-H que
                     // entra por USB encolaba otra rutina completa y el robot
                     // parecía quedarse trabado en "Homing". Rechazamos el pedido
                     // mientras haya uno en curso.
                     if (robotState == STATE_HOMING) {
                         USB_Print("AVISO|Homing ya en curso: se ignora el :-H repetido\r\n");
                         break;
                     }
                     // Homing cambia el estado a HOMING
                     robotState = STATE_HOMING;
                     Robot_ModoCalibracion();
                     // Al volver, si fue exitoso, regresamos a IDLE
                     if (robotState != STATE_ESTOP) robotState = STATE_IDLE;
                }
                else {
                     Robot_ModoCalibracion();
                }
                break;

            case '#':
                // Comandos de Movimiento
                robotState = STATE_MOVING;
                Robot_ModoEjecucion();
                if (robotState != STATE_ESTOP) robotState = STATE_IDLE;
                break;

            case '+':
                Robot_ModoAprendizaje();
                break;

            case '*':
                // Comandos de test/diagnóstico (no cambian el estado del robot).
                Robot_ModoTest();
                break;

            default:
                USB_Print("Comando desconocido\r\n");
                break;
        }
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

    // El HOMING cuenta como UNA tarea, de punta a punta. Ahora que la telemetría
    // también corre durante la calibración (Motor_HomingTick), entre eje y eje
    // los motores quedan un instante quietos: sin esto se verían tres pulsos de
    // "tarea terminada" —LED de Finish en la placa y badge FINISH en la
    // interfaz— en mitad del homing, uno por eje.
    if (robotState == STATE_HOMING) currMoving = 1;

    // Estado calibración
    uint8_t currCalib = robotCalibrated;

    // Estado de PARO DE EMERGENCIA (para que la interfaz frene su secuencia sola,
    // sin depender de mensajes de texto: la dispara el botón físico o el :-S).
    uint8_t currEstop = (robotState == STATE_ESTOP) ? 1 : 0;

    // 2. GESTIÓN DE LEDS FÍSICOS (En la placa)
    // ---------------------------------------------------------
    // Si hubo fallo de homing NO forzamos el LED de Home acá: lo hace parpadear el
    // bucle principal (Actualizar_LCD). Así el usuario ve el error también en la placa.
    if (!homingFailed)
        HAL_GPIO_WritePin(Home_led_GPIO_Port, Home_led_Pin, currCalib ? GPIO_PIN_SET : GPIO_PIN_RESET);
    HAL_GPIO_WritePin(Wait_led_GPIO_Port, Wait_led_Pin, currMoving ? GPIO_PIN_SET : GPIO_PIN_RESET);

    // LED de FINISH: marca "tarea terminada". Se maneja por FLANCO del estado de
    // movimiento, así cubre los tres casos de una sola vez —fin de homing, fin de
    // un jog y fin de cada paso de rutina— sin que cada rutina tenga que acordarse
    // de encenderlo. Antes esta línea estaba comentada y el LED no prendía nunca.
    if (currMoving && !prevMoving) {
        // Arrancó un movimiento: la tarea anterior deja de estar "terminada"
        HAL_GPIO_WritePin(Finish_led_GPIO_Port, Finish_led_Pin, GPIO_PIN_RESET);
    } else if (!currMoving && prevMoving) {
        // Se detuvo: tarea completada
        HAL_GPIO_WritePin(Finish_led_GPIO_Port, Finish_led_Pin, GPIO_PIN_SET);
    }


    // 3. DETECCIÓN DE CAMBIOS Y ENVÍO SERIAL
    // ---------------------------------------------------------
    uint8_t hasChanged = 0;

    if (currX != prevX) hasChanged = 1;
    if (currY != prevY) hasChanged = 1;
    if (currZ != prevZ) hasChanged = 1;
    if (currSensors != prevSensors) hasChanged = 1;
    if (currCalib != prevCalib) hasChanged = 1;
    if (currMoving != prevMoving) hasChanged = 1;
    if (currEstop != prevEstop) hasChanged = 1;

    // Condición de "Heartbeat": Si pasaron 2 segundos (2000ms) sin enviar, forzar envío
    uint8_t forceHeartbeat = (HAL_GetTick() - lastTelemetrySentTime > 2000);

    if (hasChanged || forceHeartbeat) {
        char msg[110];
        // AGREGAMOS MÁS DATOS A LA TRAMA:
        // C: Calibrado (0/1)
        // M: Moviendo (0/1)
        // E: Paro de emergencia activo (0/1) -> la interfaz frena su secuencia sola
        sprintf(msg, "STATUS|X:%d|Y:%d|Z:%d|S:%d%d%d|C:%d|M:%d|E:%d\r\n",
                currX, currY, currZ,
                sX, sY, sZ,
                currCalib, currMoving, currEstop);

        USB_Print(msg);

        // Actualizar estado previo
        prevX = currX; prevY = currY; prevZ = currZ;
        prevSensors = currSensors;
        prevCalib = currCalib;
        prevMoving = currMoving;
        prevEstop = currEstop;

        lastTelemetrySentTime = HAL_GetTick();
    }
}

// Reporta por USB el último evento de interrupción, diferenciando su ORIGEN.
// Se llama desde el bucle principal (NO desde la ISR) para no bloquear dentro de
// una interrupción. Deja el log claro de por dónde entró la parada o el tope:
//   - Botón físico de PARO (EXTI PB15)
//   - Comando :-S por software (E-STOP desde la interfaz)
//   - Fin de carrera X / Y / Z (indicando qué eje tocó su sensor)
void Robot_ReportInterrupts(void) {
    uint8_t src = lastIrqSource;      // Copia local (la ISR podría reescribirla)
    if (src == IRQ_SRC_NONE) return;
    lastIrqSource = IRQ_SRC_NONE;     // Consumimos el evento

    switch (src) {
        case IRQ_SRC_ESTOP_BTN:
            USB_Print("IRQ|E-STOP: boton fisico (PB15)\r\n");
            break;
        case IRQ_SRC_ESTOP_SW:
            USB_Print("IRQ|E-STOP: comando :-S (software)\r\n");
            break;
        // En los fines de carrera avisamos además que el movimiento pendiente se
        // canceló (lo hace Motor_Sensor_Triggered igualando newPosition a la
        // posición real). Es un aviso NO BLOQUEANTE: el robot sigue aceptando
        // comandos, sólo se descartó el tramo que excedía el recorrido.
        //
        // Durante el homing NO se avisa: ahí tocar los tres finales es el
        // procedimiento normal y el aviso sólo ensuciaría la consola.
        case IRQ_SRC_LIMIT_X:
            USB_Print("IRQ|Fin de carrera: eje X (PB12)\r\n");
            if (robotState != STATE_HOMING)
                USB_Print("AVISO|Movimiento cancelado: eje X en fin de carrera\r\n");
            break;
        case IRQ_SRC_LIMIT_Y:
            USB_Print("IRQ|Fin de carrera: eje Y (PB13)\r\n");
            if (robotState != STATE_HOMING)
                USB_Print("AVISO|Movimiento cancelado: eje Y en fin de carrera\r\n");
            break;
        case IRQ_SRC_LIMIT_Z:
            USB_Print("IRQ|Fin de carrera: eje Z (PB14)\r\n");
            if (robotState != STATE_HOMING)
                USB_Print("AVISO|Movimiento cancelado: eje Z en fin de carrera\r\n");
            break;
        default:
            break;
    }
}
