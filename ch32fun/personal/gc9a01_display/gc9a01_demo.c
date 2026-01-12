#include "ch32fun.h"
#include "gc9a01.h"
#include "spi.h"
#include <stdio.h>

int main() {
  SystemInit();

  printf("GC9A01 SPI Demo\n");
  // set sysclock to 100mhz
  // Initialize SPI with clock divider 4 (15MHz if SysClk is 60MHz) -> fast
  // enough for display
  SPI_Init(4);

  // Initialize Display
  GC9A01_Init();

  printf("Display Initialized\n");

  while (1) {
    printf("Red\n");
    GC9A01_FillScreen(RED);
    Delay_Ms(1000);

    printf("Green\n");
    GC9A01_FillScreen(GREEN);
    Delay_Ms(1000);

    printf("Blue\n");
    GC9A01_FillScreen(BLUE);
    Delay_Ms(1000);

    // Draw some patterns
    printf("Pattern\n");
    GC9A01_FillScreen(BLACK);
    GC9A01_FillRect(60, 60, 120, 120, WHITE);
    GC9A01_FillRect(90, 90, 60, 60, RED);

    Delay_Ms(2000);
  }
}
