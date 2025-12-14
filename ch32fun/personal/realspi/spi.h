#ifndef _SPI_H
#define _SPI_H

#include "ch32fun.h"

// SPI0 Initialization
// clockDiv: Clock divider (e.g., 60 for 1MHz at 60MHz Fsys)
void SPI_Init(uint8_t clockDiv);

// Transfer a single byte (read/write)
uint8_t SPI_Transfer(uint8_t data);

// Send data buffer
void SPI_Send(uint8_t *data, uint16_t len);

// Receive data buffer
void SPI_Receive(uint8_t *buffer, uint16_t len);

#endif
