/*
 * Template main.c for CH592
 * Bare skeleton: clock init + idle loop.
 * Add your code below.
 */

#include "CH59x_common.h"

int main(void) {
  SetSysClock(CLK_SOURCE_PLL_60MHz);

  // --- Your init code here ---

  while (1) {
    DelayMs(100);
  }
}
