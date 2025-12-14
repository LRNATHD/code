#include "spi.h"

void SPI_Init(uint8_t clockDiv) {
  // Configure SPI0 Pins
  // PA13: SCK
  // PA14: MOSI
  // PA15: MISO
  funPinMode(PA13, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(PA14, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(PA15, GPIO_CFGLR_IN_PU);

  // Reset SPI
  R8_SPI0_CTRL_MOD = RB_SPI_ALL_CLEAR;
  R8_SPI0_CTRL_MOD = RB_SPI_MOSI_OE | RB_SPI_SCK_OE; // Master mode, Mode 0

  // Set Clock Divider
  R8_SPI0_CLOCK_DIV = clockDiv;

  // Configure SPI
  // Enable Auto Flag Clear on FIFO access
  R8_SPI0_CTRL_CFG = RB_SPI_AUTO_IF;
}

uint8_t SPI_Transfer(uint8_t data) {
  // 1. Set FIFO Direction to Output (Write)
  R8_SPI0_CTRL_MOD &= ~RB_SPI_FIFO_DIR;

  // 2. Write data to FIFO
  R8_SPI0_FIFO = data;

  // 3. Wait for transmission to complete (SPI Free)
  while (!(R8_SPI0_INT_FLAG & RB_SPI_FREE))
    ;

  // 4. Set FIFO Direction to Input (Read)
  R8_SPI0_CTRL_MOD |= RB_SPI_FIFO_DIR;

  // 5. Read received data
  uint8_t ret = R8_SPI0_FIFO;

  return ret;
}

void SPI_Send(uint8_t *data, uint16_t len) {
  for (uint16_t i = 0; i < len; i++) {
    SPI_Transfer(data[i]);
  }
}

void SPI_Receive(uint8_t *buffer, uint16_t len) {
  for (uint16_t i = 0; i < len; i++) {
    buffer[i] = SPI_Transfer(0xFF);
  }
}
