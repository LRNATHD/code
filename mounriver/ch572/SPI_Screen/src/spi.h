#ifndef _SPI_H
#define _SPI_H

#include "CH57x_common.h"

void SPI_Init(uint8_t clockDiv);
uint8_t SPI_Transfer(uint8_t data);
void SPI_Send(uint8_t *data, uint16_t len);
void SPI_Receive(uint8_t *buffer, uint16_t len);

#endif
