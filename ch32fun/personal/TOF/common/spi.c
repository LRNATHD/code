#include "spi.h"

// Optimized Software SPI (Bit-Bang) for CH572
// Pins:
// SCK:  PA5
// MOSI: PA7
// MISO: PA6 (Optional/Not Used)

// Direct register access masks
#define PIN_SCK_MASK (1 << 5)
#define PIN_MOSI_MASK (1 << 7)

void SPI_Init(uint8_t clockDiv) {
  // Configure Pins as Output Push-Pull 10MHz
  funPinMode(PA5, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(PA7, GPIO_CFGLR_OUT_10Mhz_PP);
  // funPinMode( PA6, GPIO_CFGLR_IN_PU );

  // Initial Idle State (Clock Low)
  R32_PA_CLR = PIN_SCK_MASK;
  R32_PA_CLR = PIN_MOSI_MASK;
}

uint8_t SPI_Transfer(uint8_t data) {
  // Unrolled SPI Mode 0 (CPOL=0, CPHA=0)
  // Write Data (Setup) -> Clock High -> Clock Low

  // Bit 7
  if (data & 0x80)
    R32_PA_SET = PIN_MOSI_MASK;
  else
    R32_PA_CLR = PIN_MOSI_MASK;
  R32_PA_SET = PIN_SCK_MASK;
  R32_PA_CLR = PIN_SCK_MASK;

  // Bit 6
  if (data & 0x40)
    R32_PA_SET = PIN_MOSI_MASK;
  else
    R32_PA_CLR = PIN_MOSI_MASK;
  R32_PA_SET = PIN_SCK_MASK;
  R32_PA_CLR = PIN_SCK_MASK;

  // Bit 5
  if (data & 0x20)
    R32_PA_SET = PIN_MOSI_MASK;
  else
    R32_PA_CLR = PIN_MOSI_MASK;
  R32_PA_SET = PIN_SCK_MASK;
  R32_PA_CLR = PIN_SCK_MASK;

  // Bit 4
  if (data & 0x10)
    R32_PA_SET = PIN_MOSI_MASK;
  else
    R32_PA_CLR = PIN_MOSI_MASK;
  R32_PA_SET = PIN_SCK_MASK;
  R32_PA_CLR = PIN_SCK_MASK;

  // Bit 3
  if (data & 0x08)
    R32_PA_SET = PIN_MOSI_MASK;
  else
    R32_PA_CLR = PIN_MOSI_MASK;
  R32_PA_SET = PIN_SCK_MASK;
  R32_PA_CLR = PIN_SCK_MASK;

  // Bit 2
  if (data & 0x04)
    R32_PA_SET = PIN_MOSI_MASK;
  else
    R32_PA_CLR = PIN_MOSI_MASK;
  R32_PA_SET = PIN_SCK_MASK;
  R32_PA_CLR = PIN_SCK_MASK;

  // Bit 1
  if (data & 0x02)
    R32_PA_SET = PIN_MOSI_MASK;
  else
    R32_PA_CLR = PIN_MOSI_MASK;
  R32_PA_SET = PIN_SCK_MASK;
  R32_PA_CLR = PIN_SCK_MASK;

  // Bit 0
  if (data & 0x01)
    R32_PA_SET = PIN_MOSI_MASK;
  else
    R32_PA_CLR = PIN_MOSI_MASK;
  R32_PA_SET = PIN_SCK_MASK;
  R32_PA_CLR = PIN_SCK_MASK;

  return 0;
}

void SPI_Send(uint8_t *data, uint16_t len) {
  // Fast loop with local pointers to registers
  volatile uint32_t *pa_set = &R32_PA_SET;
  volatile uint32_t *pa_clr = &R32_PA_CLR;

  for (uint16_t i = 0; i < len; i++) {
    uint8_t b = data[i];

    // Unrolled bit banging
    if (b & 0x80)
      *pa_set = PIN_MOSI_MASK;
    else
      *pa_clr = PIN_MOSI_MASK;
    *pa_set = PIN_SCK_MASK;
    *pa_clr = PIN_SCK_MASK; // Pulse SCK High then Low

    if (b & 0x40)
      *pa_set = PIN_MOSI_MASK;
    else
      *pa_clr = PIN_MOSI_MASK;
    *pa_set = PIN_SCK_MASK;
    *pa_clr = PIN_SCK_MASK;

    if (b & 0x20)
      *pa_set = PIN_MOSI_MASK;
    else
      *pa_clr = PIN_MOSI_MASK;
    *pa_set = PIN_SCK_MASK;
    *pa_clr = PIN_SCK_MASK;

    if (b & 0x10)
      *pa_set = PIN_MOSI_MASK;
    else
      *pa_clr = PIN_MOSI_MASK;
    *pa_set = PIN_SCK_MASK;
    *pa_clr = PIN_SCK_MASK;

    if (b & 0x08)
      *pa_set = PIN_MOSI_MASK;
    else
      *pa_clr = PIN_MOSI_MASK;
    *pa_set = PIN_SCK_MASK;
    *pa_clr = PIN_SCK_MASK;

    if (b & 0x04)
      *pa_set = PIN_MOSI_MASK;
    else
      *pa_clr = PIN_MOSI_MASK;
    *pa_set = PIN_SCK_MASK;
    *pa_clr = PIN_SCK_MASK;

    if (b & 0x02)
      *pa_set = PIN_MOSI_MASK;
    else
      *pa_clr = PIN_MOSI_MASK;
    *pa_set = PIN_SCK_MASK;
    *pa_clr = PIN_SCK_MASK;

    if (b & 0x01)
      *pa_set = PIN_MOSI_MASK;
    else
      *pa_clr = PIN_MOSI_MASK;
    *pa_set = PIN_SCK_MASK;
    *pa_clr = PIN_SCK_MASK;
  }
}

void SPI_Receive(uint8_t *buffer, uint16_t len) {
  // Not implemented in this bit-bang version (tx only for display)
}
