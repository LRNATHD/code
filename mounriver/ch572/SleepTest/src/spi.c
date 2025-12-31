#include "spi.h"
#include "CH57x_common.h"

// Hardware SPI + DMA Driver for CH572
// Pins:
// CS:   PA4 (Controlled manually by GC9A01 driver)
// SCK:  PA5
// MOSI: PA7

void SPI_Init(uint8_t clockDiv) {
  // Configure Pins
  // PA4 (CS) - General Purpose Output (Manual CS)
  GPIOA_ModeCfg(GPIO_Pin_4, GPIO_ModeOut_PP_5mA);
  GPIOA_SetBits(GPIO_Pin_4); // High

  // PA5 (SCK) & PA7 (MOSI) - SPI Alternate Functions or just Outputs for SPI
  // engine The example configures them as Push-Pull Outputs.
  GPIOA_ModeCfg(GPIO_Pin_5 | GPIO_Pin_7, GPIO_ModeOut_PP_5mA);

  // Initialize SPI Master
  // Note: clockDiv argument is ignored here as SPI_MasterDefInit uses
  // predefined logic, typically max speed or defined by system clock division.
  // If we need specific speed, we might need to touch R8_SPI_CLOCK_DIV.
  SPI_MasterDefInit();

  if (clockDiv > 0) {
    R8_SPI_CLOCK_DIV = clockDiv;
  }
}

uint8_t SPI_Transfer(uint8_t data) {
  // Write byte
  SPI_MasterSendByte(data);
  // For read, we'd need to switch mode, but we are mostly writing to display.
  // Return dummy or 0.
  return 0;
}

void SPI_Send(uint8_t *data, uint16_t len) {
  // Use DMA for block transfer
  // CH572 DMA Length Register (R16_SPI_TOTAL_CNT) is 12-bit (Max 4095)
  // Split large transfers into chunks
  uint16_t sent = 0;
  while (sent < len) {
    uint16_t chunk = len - sent;
    if (chunk > 4094) {
      chunk = 4094;
    }
    SPI_MasterDMATrans(data + sent, chunk);
    sent += chunk;
  }
}

void SPI_Receive(uint8_t *buffer, uint16_t len) {
  SPI_MasterDMARecv(buffer, len);
}
