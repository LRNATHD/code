/*
 * Sandbox.c
 * Spins both motors at full speed (100%), then slowly ramps down to 0%.
 * Displays current PWM duty-cycle percentage on the OLED.
 *
 * PWM channel mapping (CH592):
 *   PWM4 -> PA12 (Left  motor enable)
 *   PWM5 -> PA13 (Right motor enable)
 * Phase pins set HIGH for forward direction.
 */

#include "CH59x_common.h"
#include "oled_driver.h"

/* ---------- Pin definitions ---------- */
#define Left_Enable GPIO_Pin_12  // PA12 = PWM4
#define Right_Enable GPIO_Pin_13 // PA13 = PWM5
#define Left_Phase GPIO_Pin_14
#define Right_Phase GPIO_Pin_15

/* ---------- PWM parameters ---------- */
#define PWM_CYCLE 30000  // Fsys/4 = 15MHz, 15MHz/30000 = 500 Hz
#define RAMP_DELAY_MS 50 // delay between each step (ms)
#define RAMP_STEPS 100   // number of steps from 100% -> 0%

/* ---------- Helpers ---------- */

// Integer to string (0-100). Writes into caller-supplied buffer.
static void int_to_str(int val, char *buf) {
  if (val >= 100) {
    buf[0] = '1';
    buf[1] = '0';
    buf[2] = '0';
    buf[3] = '\0';
    return;
  }
  if (val < 0) {
    buf[0] = '0';
    buf[1] = '\0';
    return;
  }

  int tens = val / 10;
  int ones = val % 10;
  int i = 0;
  if (tens > 0)
    buf[i++] = '0' + tens;
  buf[i++] = '0' + ones;
  buf[i] = '\0';
}

/* ---------- Main ---------- */
int main(void) {
  SetSysClock(CLK_SOURCE_PLL_60MHz);

  /* --- GPIO setup --- */
  // Enable + Phase pins as push-pull output
  GPIOA_ModeCfg(Left_Enable | Right_Enable | Left_Phase | Right_Phase,
                GPIO_ModeOut_PP_5mA);

  // Set phase HIGH (forward direction for both motors)
  GPIOA_SetBits(Left_Phase | Right_Phase);

  /* --- OLED setup --- */
  DelayMs(200);
  OLED_Init();
  OLED_Clear();
  OLED_ShowString(0, 0, "Motor Ramp Down");

  /* --- PWM setup --- */
  // Clock divider: PWM base = Fsys / 4 = 15 MHz
  PWMX_CLKCfg(4);
  // 16-bit cycle
  PWMX_16bit_CycleCfg(PWM_CYCLE);

  // Start both channels at 100% duty
  PWMX_16bit_ACTOUT(CH_PWM4, PWM_CYCLE, High_Level, ENABLE);
  PWMX_16bit_ACTOUT(CH_PWM5, PWM_CYCLE, High_Level, ENABLE);

  /* --- Ramp-down loop --- */
  int pct;
  char buf[8];

  for (pct = 100; pct >= 0; pct--) {
    // Compute duty value proportional to percentage
    uint16_t duty = (uint16_t)(((uint32_t)PWM_CYCLE * pct) / 100);

    // Update PWM duty on both channels
    PWMX_16bit_ACTOUT(CH_PWM4, duty, High_Level, ENABLE);
    PWMX_16bit_ACTOUT(CH_PWM5, duty, High_Level, ENABLE);

    // Format "PWM: xxx%"
    OLED_ShowString(0, 2, "PWM:     "); // clear previous value
    int_to_str(pct, buf);

    // Build display: "PWM: <pct>%"
    char line[16];
    int i = 0;
    line[i++] = 'P';
    line[i++] = 'W';
    line[i++] = 'M';
    line[i++] = ':';
    line[i++] = ' ';
    int j = 0;
    while (buf[j])
      line[i++] = buf[j++];
    line[i++] = '%';
    line[i] = '\0';

    OLED_ShowString(0, 2, line);

    DelayMs(RAMP_DELAY_MS);
  }

  // Motors fully stopped – disable PWM outputs
  PWMX_16bit_ACTOUT(CH_PWM4, 0, High_Level, DISABLE);
  PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);

  OLED_ShowString(0, 2, "PWM: 0%  ");
  OLED_ShowString(0, 3, "Done.");

  // Idle
  while (1) {
    DelayMs(100);
  }
}
