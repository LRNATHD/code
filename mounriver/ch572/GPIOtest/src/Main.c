#include "CH57x_common.h"

int main() {
  SetSysClock(CLK_SOURCE_HSE_PLL_60MHz);

  /* Initialize GPIO for LED (Assuming PA8 for test, change as needed) */
  GPIOA_ModeCfg(GPIO_Pin_8, GPIO_ModeOut_PP_5mA);

  while (1) {
    GPIOA_SetBits(GPIO_Pin_8);
    DelayMs(500);
    GPIOA_ResetBits(GPIO_Pin_8);
    DelayMs(500);
  }
}
