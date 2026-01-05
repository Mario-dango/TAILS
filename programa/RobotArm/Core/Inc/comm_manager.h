/*
 * comm_manager.h
 *
 *  Created on: Jan 4, 2026
 *      Author: mprob
 */
#ifndef COMM_MANAGER_H
#define COMM_MANAGER_H

#include "main.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h> // Para atoi

// Prototipo de la función de impresión segura (bloqueante)
void USB_Print(char *str);

// Utilidad para cortar cadenas
void CDC_FS_Substring(uint8_t inicioCadena, uint8_t finCadena, char* str, char* dst);

#endif /* COMM_MANAGER_H */
