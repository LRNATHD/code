#include "CH57x_common.h"
#include "gc9a01.h"
#include "spi.h"
#include <stdio.h>

void DebugInit(void) {
  GPIOA_SetBits(GPIO_Pin_9);
  GPIOA_ModeCfg(GPIO_Pin_8, GPIO_ModeIN_PU);
  GPIOA_ModeCfg(GPIO_Pin_9, GPIO_ModeOut_PP_5mA);
  UART_DefInit();
}

int main() {
  // Initialize System Clock
  SetSysClock(CLK_SOURCE_HSE_PLL_60MHz);

  // Initialize SPI with clock divider 4 (15MHz)
  SPI_Init(4);

  // Initialize Display
  GC9A01_Init();
  GC9A01_FillScreen(BLACK);

  // Draw Stats (Centered for 240x240 Circular Display)
  // Font size 2: 10px wide, 14px high (approx with spacing)
  // "Sleep Power Test" -> 16 chars * 12px = 192px width. Start X ~ 24.
  GC9A01_DrawString(24, 60, "Sleep Power Test", WHITE, BLACK, 2);

  // Font size 1: 6px wide, 8px high
  // "Mode: Shutdown(0)" -> 17 chars * 6 = 102px. Start X ~ 69.
  GC9A01_DrawString(69, 100, "Mode: Shutdown(0)", GREEN, BLACK, 1);

  // "RAM Retained: No" -> 16 chars * 6 = 96px. Start X ~ 72.
  GC9A01_DrawString(72, 115, "RAM Retained: No", RED, BLACK, 1);

  // "Active Time: 2s" -> 15 chars * 6 = 90px. Start X ~ 75.
  GC9A01_DrawString(75, 130, "Active Time: 2s", WHITE, BLACK, 1);

  // "Sleeping in 5s..." -> 17 chars * 6 = 102px. Start X ~ 69.
  GC9A01_DrawString(69, 160, "Sleeping in 5s...", CYAN, BLACK, 1);

  // Initialize UART for debug
  DebugInit();
  printf("Sleep Power Test. Sleeping in 5s...\n");

  // Delay to let user read screen
  DelayMs(5000);

  // Turn off Display to save power
  // "Display OFF..." -> 14 chars * 6 = 84px. Start X ~ 78.
  GC9A01_DrawString(78, 180, "Display OFF...", BLUE, BLACK, 1);
  DelayMs(100);
  GC9A01_Sleep();

  // Set all GPIO to Input Pull-Up to minimize leakage
  GPIOA_ModeCfg(GPIO_Pin_All, GPIO_ModeIN_PU);

  // Configure RTC Wakeup
  // Enable RTC Wakeup Event
  PWR_PeriphWakeUpCfg(ENABLE, RB_SLP_RTC_WAKE, 0);
  // Set Trigger for 5 seconds later
  // LSI is approx 32000Hz.
  // We use RTC_TRIGFunCfg which takes cycles.
  // 5 seconds * 32000 = 160000 cycles.
  RTC_TRIGFunCfg(160000);

  // Enter Shutdown Mode
  // 0 = RAM retention off (lowest power)
  LowPower_Shutdown(0);

  while (1)
    ;
}
