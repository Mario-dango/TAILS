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

// Variable Global de Estado
volatile uint8_t robotState = STATE_IDLE;

// Configuración por defecto de rampas (Ajustable)
#define DEFAULT_MIN_VEL  50   // 50 Hz de arranque (evita resonancia baja)
#define DEFAULT_ACCEL    5    // Aumentar 5 Hz por cada paso dado

// --- CONFIGURACIÓN DE HOMING ---
#define SPEED_STD       60  // Hz para Y y X (1.8°)
#define SPEED_FAST      30  // Hz para Z (3.75°)
#define TIMEOUT_SEC     10  // Tiempo máximo por eje

// --- Funciones Privadas ---
// --- PROTOTIPOS DE FUNCIONES PRIVADAS ---
void CalculateSpeed(StepperMotor *motor);
static int RunHomingSequence(int motorIndex, int velocity, int direction);
uint8_t IsSensorPressed(int motorIndex);

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

// Función auxiliar privada para mover un solo eje hasta el sensor
// Retorna: 0 si Éxito, -1 si Timeout
/* Core/Src/motor_driver.c */

static int RunHomingSequence(int motorIndex, int velocity, int direction) {

    // --- PASO 0: VERIFICACIÓN PREVIA (SMART HOMING) ---
    // ¿El sensor YA está presionado antes de empezar?
    if (IsSensorPressed(motorIndex)) {

        // ESTRATEGIA: Retroceder hasta liberar el sensor
        motors[motorIndex].velocity = velocity;
        motors[motorIndex].stepInterval = TIMER_FREQUENCY / velocity;

        // Invertimos la dirección para SALIR del sensor
        int dirSalida = (direction == DIR_TOWARDS_HOME) ? DIR_AWAY_HOME : DIR_TOWARDS_HOME;
        motors[motorIndex].direction = dirSalida;

        // Aplicar cambio físico de pin DIR
        GPIO_PinState pinState = (dirSalida == 0) ? GPIO_PIN_SET : GPIO_PIN_RESET;
        HAL_GPIO_WritePin(motors[motorIndex].dirPort, motors[motorIndex].dirPin, pinState);

        motors[motorIndex].stopFlag = 0; // Moverse

        // Esperar hasta que el sensor SE SUELTE (deje de estar presionado)
        contSeconds = 0;
        while (IsSensorPressed(motorIndex) && contSeconds < 5); // Timeout corto de seguridad

        // Unos pasitos extra para asegurar despeje
        HAL_Delay(500);
        motors[motorIndex].stopFlag = 1; // Frenar

        // Si después de intentar salir sigue presionado, hay error de hardware
        if (IsSensorPressed(motorIndex)) return -5;
    }

    // --- PASO 1: BÚSQUEDA NORMAL DE HOME ---
    // (Ahora seguro porque sabemos que no estamos tocando el sensor)

    motors[motorIndex].velocity = velocity;
    motors[motorIndex].stepInterval = TIMER_FREQUENCY / velocity;
    motors[motorIndex].direction = direction; // Dirección Hacia Home

    GPIO_PinState pinState = (direction == 0) ? GPIO_PIN_SET : GPIO_PIN_RESET;
    HAL_GPIO_WritePin(motors[motorIndex].dirPort, motors[motorIndex].dirPin, pinState);

    motors[motorIndex].stopFlag = 0; // START

    // Resetear flags de interrupción por si quedaron sucios
    if (motorIndex == 0) flagStopM_X = 0;
    else if (motorIndex == 1) flagStopM_Y = 0;
    else flagStopM_Z = 0;

    // Esperar a que el sensor se active (Flag ISR o lectura directa)
    contSeconds = 0;
    // Usamos lectura directa también por seguridad redundante
    while (!IsSensorPressed(motorIndex) && (contSeconds < TIMEOUT_SEC));

    motors[motorIndex].stopFlag = 1; // STOP

    if (!IsSensorPressed(motorIndex)) return -1; // Falló por Timeout
    return 0; // Éxito
}


// --- RUTINA PRINCIPAL DE HOMING (Y -> Z -> X) ---
int HomingMotors(uint8_t* hmX, uint8_t* hmY, uint8_t* hmZ) {
    ActivatedAll(1); // Enable Drivers
    Gripper_Open();
    HAL_Delay(500);

    // Reset Flags
    flagStopM_X = 0; flagStopM_Y = 0; flagStopM_Z = 0;
    *hmX = 0; *hmY = 0; *hmZ = 0;

    // 1. HOMING Y (Hombro/Verde) - Levantar primero
    if (RunHomingSequence(1, SPEED_STD, DIR_TOWARDS_HOME) != 0) return -2;
    *hmY = 1;
    HAL_Delay(200);

    // 2. HOMING Z (Codo/Lila) - Recoger brazo
    if (RunHomingSequence(2, SPEED_FAST, DIR_TOWARDS_HOME) != 0) return -3;
    *hmZ = 1;
    HAL_Delay(200);

    // 3. HOMING X (Base/Rojo) - Centrar giro
    if (RunHomingSequence(0, SPEED_STD, DIR_TOWARDS_HOME) != 0) return -1;
    *hmX = 1;
    HAL_Delay(200);

    // 4. RETROCESO DE SEGURIDAD (BACK-OFF) SIMULTÁNEO
    // Configuramos los 3 para moverse hacia afuera
    int backoff_steps = HOMING_BACKOFF_STEPS;

    for (int i = 0; i < NUM_MOTORS; i++) {
        motors[i].direction = DIR_AWAY_HOME;
        motors[i].currentPosition = 0;
        motors[i].stopFlag = 0; // START

        // Ajuste especial para Z (3.75°) -> Mitad de pasos
        if (i == 2) {
            motors[i].newPosition = backoff_steps / 2;
            motors[i].velocity = SPEED_FAST;
        } else {
            motors[i].newPosition = backoff_steps;
            motors[i].velocity = SPEED_STD;
        }
        motors[i].stepInterval = TIMER_FREQUENCY / motors[i].velocity;
    }

    // Esperar a que todos terminen el retroceso
    while(motors[0].currentPosition < motors[0].newPosition ||
          motors[1].currentPosition < motors[1].newPosition ||
          motors[2].currentPosition < motors[2].newPosition);

    // 5. RESTAURACIÓN FINAL Y RESET DE HARDWARE
    flagStopM_X = 0; flagStopM_Y = 0; flagStopM_Z = 0;

    for (int i = 0; i < NUM_MOTORS; i++) {
        // Dirección segura (Hacia afuera)
        motors[i].direction = DIR_AWAY_HOME;

        // Sincronismo físico del pin DIR
        GPIO_PinState pinState = (motors[i].direction == 0) ? GPIO_PIN_SET : GPIO_PIN_RESET;
        HAL_GPIO_WritePin(motors[i].dirPort, motors[i].dirPin, pinState);

        // Reset Variables Lógicas
        motors[i].velocity = 0;
        motors[i].stepInterval = 0;
        motors[i].currentPosition = 0; // CERO REAL
        motors[i].newPosition = 0;
        motors[i].stopFlag = 1;        // STOP

        // Restaurar aceleración normal
        motors[i].accelRate = DEFAULT_ACCEL;
        motors[i].minVelocity = DEFAULT_MIN_VEL;
    }

    return 0; // Homing Exitoso
}

// --- INTERRUPCIÓN DEL TIMER (Generación de Pulsos) ---
void Motor_Timer_Callback(void) {

    // [PRIORIDAD MÁXIMA] E-STOP CHECK
    // Si estamos en emergencia, abortamos INSTANTÁNEAMENTE.
    // No hay "ifs", no hay "peros", no hay rampas de frenado. Se corta la señal.
    if (robotState == STATE_ESTOP) {
        return;
    }

    for (int i = 0; i < NUM_MOTORS; i++) {
        StepperMotor *motor = &motors[i];

        // [PRIORIDAD ALTA] HARD LIMITS (Fines de Carrera en Tiempo Real)
        // Verificamos si estamos pisando el sensor Y queriendo avanzar contra él.
        if (IsSensorPressed(i) && motor->direction == DIR_TOWARDS_HOME) {
             // Forzamos apagado de este motor específico
             motor->stepInterval = 0;
             motor->velocity = 0;
             motor->stopFlag = 1;
             continue; // Saltamos al siguiente motor, este no se mueve.
        }

        // --- GENERACIÓN NORMAL DE PASOS ---
        if (motor->stopFlag == 0 && motor->stepInterval > 0) {
            motor->stepCounter++;

            // Generar Flanco de Subida (STEP HIGH)
            if (motor->stepCounter >= motor->stepInterval) {
                HAL_GPIO_WritePin(motor->dirPort, motor->dirPin, (motor->direction == 0) ? GPIO_PIN_SET : GPIO_PIN_RESET);
                HAL_GPIO_WritePin(motor->stepPort, motor->stepPin, GPIO_PIN_SET);
            }

            // Generar Flanco de Bajada (STEP LOW)
            if (motor->stepCounter >= (motor->stepInterval + 1)) {
                HAL_GPIO_WritePin(motor->stepPort, motor->stepPin, GPIO_PIN_RESET);
                motor->stepCounter = 0;

                // Actualizar Posición Lógica
                if (motor->direction == 0) motor->currentPosition++;
                else motor->currentPosition--;

                CalculateSpeed(motor); // Recalcular rampa
            }
        }
    }
}

// Esta función es llamada DIRECTAMENTE desde la interrupción EXTI (Prioridad 0)
void Motor_Sensor_Triggered(uint16_t GPIO_Pin) {

    // ============================================================
    // CASO 1: PARADA DE EMERGENCIA (¡PRIORIDAD ABSOLUTA!)
    // ============================================================
    if (GPIO_Pin == STOP_btn_Pin) {

        // 1. DESHABILITAR DRIVERS FÍSICAMENTE (OPCIONAL)
        // Si pones el pin ENABLE en alto, el motor pierde torque inmediatamente.
        // Útil si quieres que el robot "se suelte".
        // Si prefieres que frene y mantenga posición, comenta esta línea.
        // HAL_GPIO_WritePin(EnableMotors_GPIO_Port, EnableMotors_Pin, GPIO_PIN_SET);

        // 2. MATAR LA GENERACIÓN DE PASOS (CRÍTICO)
        // Recorremos todos los motores y ponemos sus intervalos a 0.
        // Esto asegura que la próxima interrupción del TIM2 (50us después) NO haga nada.
        for (int i = 0; i < NUM_MOTORS; i++) {
            motors[i].velocity = 0;
            motors[i].targetVelocity = 0;
            motors[i].stepInterval = 0; // <--- ESTO ES EL FRENO DE MANO
            motors[i].stopFlag = 1;
        }

        // 3. CAMBIAR ESTADO GLOBAL
        // Para que el main loop y el USB sepan que pasó algo grave.
        robotState = STATE_ESTOP;

        // 4. FEEDBACK VISUAL INMEDIATO (Debugging)
        // Encendemos un LED directamente aquí para saber que la ISR entró.
        // HAL_GPIO_WritePin(Wait_led_GPIO_Port, Wait_led_Pin, GPIO_PIN_SET);
    }

    // ============================================================
    // CASO 2: FINAL DE CARRERA (X, Y, Z)
    // ============================================================
    // Solo detenemos el motor específico que tocó su sensor.
    else {
        StepperMotor *motorAfectado = NULL;
        volatile uint8_t *flagGlobal = NULL;

        if (GPIO_Pin == StopM_X_Pin) {
            motorAfectado = &motors[0];
            flagGlobal = &flagStopM_X;
        }
        else if (GPIO_Pin == StopM_Y_Pin) {
            motorAfectado = &motors[1];
            flagGlobal = &flagStopM_Y;
        }
        else if (GPIO_Pin == StopM_Z_Pin) {
            motorAfectado = &motors[2];
            flagGlobal = &flagStopM_Z;
        }

        if (motorAfectado != NULL) {
            // A. Detener motor INMEDIATAMENTE dentro de la interrupción
            motorAfectado->velocity = 0;
            motorAfectado->targetVelocity = 0;
            motorAfectado->stepInterval = 0; // <--- Freno instantáneo
            motorAfectado->stopFlag = 1;

            // B. Marcar bandera para lógica de Homing
            if (flagGlobal != NULL) *flagGlobal = 1;
        }
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

// Asume que tus sensores dan 0 (RESET) cuando están presionados (Pull-Up)
// Si es al revés, cambia GPIO_PIN_RESET por GPIO_PIN_SET
uint8_t IsSensorPressed(int motorIndex) {
    if (motorIndex == 0) return (HAL_GPIO_ReadPin(StopM_X_GPIO_Port, StopM_X_Pin) == GPIO_PIN_RESET);
    if (motorIndex == 1) return (HAL_GPIO_ReadPin(StopM_Y_GPIO_Port, StopM_Y_Pin) == GPIO_PIN_RESET);
    if (motorIndex == 2) return (HAL_GPIO_ReadPin(StopM_Z_GPIO_Port, StopM_Z_Pin) == GPIO_PIN_RESET);
    return 0;
}

float deg2rad(float degrees) {
    return degrees * (M_PI / 180.0);
}
