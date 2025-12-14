#include "ch32fun.h"
#include "spi.h"
#include <stdio.h>


int main() {
  SystemInit();

  printf("Real Hardware SPI Test\n");

  // Initialize SPI with clock divider 60 (1MHz if SysClk is 60MHz)
  SPI_Init(60);

  while (1) {
    printf("Sending 0x55...\n");
    uint8_t rx = SPI_Transfer(0x55);
    printf("Received: 0x%02X\n", rx);
    Delay_Ms(1000);
  }
}
