/*
 * robot_logic.h
 *
 *  Created on: Jan 4, 2026
 *      Author: mprob
 */
#ifndef ROBOT_LOGIC_H
#define ROBOT_LOGIC_H

#include "main.h"

// Prototipos de las funciones de lógica
void Robot_Consignas(void);     // Imprime la ayuda
uint8_t Robot_ModoCalibracion(void);
uint8_t Robot_ModoAprendizaje(void);
uint8_t Robot_ModoEjecucion(void);

// Función maestra que decide qué hacer según el comando recibido
void Robot_ProcesarComando(char *cmd);

#endif /* ROBOT_LOGIC_H */
