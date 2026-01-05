/*
 * comm_manager.c
 *
 *  Created on: Jan 4, 2026
 *      Author: mprob
 */

#include "comm_manager.h"
#include "usbd_cdc_if.h" // Necesario para CDC_Transmit_FS

// Función segura que espera si el USB está ocupado
void USB_Print(char *str) {
    uint8_t result = USBD_OK;
    uint32_t timeout = HAL_GetTick();

    // Intentar enviar hasta que esté libre o pase el tiempo
    do {
        result = CDC_Transmit_FS((uint8_t*)str, strlen(str));

        // Timeout de seguridad de 10ms para no colgar el micro si no hay USB
        if (HAL_GetTick() - timeout > 10) break;

    } while(result == USBD_BUSY);
}

// Tu función original de Substring, movida aquí
void CDC_FS_Substring(uint8_t inicioCadena, uint8_t finCadena, char* cadenaOriginal, char* cadenaCortada) {
    uint8_t pt = 0;
    for (uint16_t lt = inicioCadena; lt < finCadena; lt++) {
        cadenaCortada[pt] = cadenaOriginal[lt];
        pt++;
    }
    cadenaCortada[pt] = '\0';
}
