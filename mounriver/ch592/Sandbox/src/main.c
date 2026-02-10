/*
 * Sandbox.c
 * Spins both motors at 0% speed, then slowly ramps up to 30%.
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
#define Left_Phase GPIO_Pin_14
#define Right_Phase GPIO_Pin_15

// Encoder Pins
#define Left_Enc_A GPIO_Pin_6  // PB6
#define Left_Enc_B GPIO_Pin_0  // PB0
#define Right_Enc_A GPIO_Pin_4 // PA4
#define Right_Enc_B GPIO_Pin_5 // PB5

/* ---------- PWM parameters ---------- */
#define PWM_CYCLE 30000    // Fsys/4 = 15MHz, 15MHz/30000 = 500 Hz
#define RAMP_DELAY_MS 250  // delay between each step (ms)
#define RAMP_STEPS 30      // number of steps from 0% -> 30%
#define PWM_MIN_PERCENT 15 // Minimum duty cycle to overcome friction

// Speed Meas Constants
#define TICKS_PER_REV 350.0f // 7 poles * 50 gear ratio * 1 edge (Approx)
#define WHEEL_DIA_M 0.0885f  // 88.5 mm
#define PI 3.14159f

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
    buf[i++] = '0' + ones;
  buf[i] = '\0';
}

// Float to string (X.YY)
static void float_to_str(float val, char *buf) {
  int int_part = (int)val;
  int frac_part = (int)((val - int_part) * 100);

  int_to_str(int_part, buf);
  int len = 0;
  while (buf[len])
    len++;

  buf[len++] = '.';
  buf[len++] = (frac_part / 10) + '0';
  buf[len++] = (frac_part % 10) + '0';
  buf[len] = '\0';
}

// Globals for Interrupts
volatile uint32_t count_left = 0;

/* ---------- Interrupt Handlers ---------- */
__INTERRUPT
__HIGH_CODE
void GPIOB_IRQHandler(void) {
  if (GPIOB_GetITFlagBit(Left_Enc_A)) {
    uint8_t a = (GPIOB_ReadPortPin(Left_Enc_A) != 0);

    // Count every edge
    count_left++;

    // Toggle Edge Trigger
    if (a)
      GPIOB_ITModeCfg(Left_Enc_A, GPIO_ITMode_FallEdge);
    else
      GPIOB_ITModeCfg(Left_Enc_A, GPIO_ITMode_RiseEdge);

    GPIOB_ClearITFlagBit(Left_Enc_A);
  }
}

// Measure ticks on Left Encoder A for approx 1 second
// Blocking function. Returns ticks/sec.
static uint32_t Measure_Speed(void) {
  uint32_t start_t = count_left;
  DelayMs(1000);
  uint32_t end_t = count_left;
  return (end_t >= start_t) ? (end_t - start_t)
                            : (end_t + (0xFFFFFFFF - start_t) + 1);
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

  // Encoder GPIO setup
  // Left Enc A/B and Right Enc B are on Port B
  GPIOB_ModeCfg(Left_Enc_A | Left_Enc_B | Right_Enc_B, GPIO_ModeIN_PU);
  // Right Enc A is on Port A
  GPIOA_ModeCfg(Right_Enc_A, GPIO_ModeIN_PU);

  // Interrupt Configuration (Start low/falling?)
  // Actually, detect initial state or just force one?
  // Let's force RiseEdge initially to catch first transition if low.
  GPIOB_ITModeCfg(Left_Enc_A, GPIO_ITMode_FallEdge); // Trigger on falling edge
  PFIC_EnableIRQ(GPIO_B_IRQn);

  /* --- OLED setup --- */
  DelayMs(200);
  OLED_Init();
  OLED_Clear();
  OLED_ShowString(0, 0, "Motor Ramp Up  ");

  /* --- PWM setup --- */
  // Clock divider: PWM base = Fsys / 4 = 15 MHz
  PWMX_CLKCfg(4);
  // 16-bit cycle
  PWMX_16bit_CycleCfg(PWM_CYCLE);

  /* --- Speed Measurement Sequence --- */

  // 1. Min Speed (15%)
  uint32_t min_duty = (uint32_t)PWM_CYCLE * 15 / 100;
  PWMX_16bit_ACTOUT(CH_PWM4, (uint16_t)min_duty, High_Level, ENABLE);
  PWMX_16bit_ACTOUT(CH_PWM5, (uint16_t)min_duty, High_Level, ENABLE);

  DelayMs(500); // Spin up
  uint32_t ticks_15 = Measure_Speed();

// Calculate m/s (TICKS_PER_REV = 700 for dual edge)
// Use local constant for clarity
#define TICKS_PER_REV_DUAL 700.0f
  float speed_15 = (float)ticks_15 / TICKS_PER_REV_DUAL * (PI * WHEEL_DIA_M);

  // Display Ticks and Speed
  char buf_t[16], buf_s[16];
  int_to_str((int)ticks_15, buf_t);
  float_to_str(speed_15, buf_s);

  // Format: "15% T:150 S:0.12"
  OLED_ShowString(0, 1, "15% T:        ");
  OLED_ShowString(48, 1, buf_t);
  OLED_ShowString(80, 1, " S:");
  OLED_ShowString(100, 1, buf_s);

  // 2. Max Speed (100%)
  uint32_t max_duty = (uint32_t)PWM_CYCLE;
  PWMX_16bit_ACTOUT(CH_PWM4, (uint16_t)max_duty, High_Level, ENABLE);
  PWMX_16bit_ACTOUT(CH_PWM5, (uint16_t)max_duty, High_Level, ENABLE);

  DelayMs(500); // Spin up
  uint32_t ticks_100 = Measure_Speed();

  float speed_100 = (float)ticks_100 / TICKS_PER_REV_DUAL * (PI * WHEEL_DIA_M);

  int_to_str((int)ticks_100, buf_t);
  float_to_str(speed_100, buf_s);

  // Format: "100% T:163 S:0.15"
  OLED_ShowString(0, 2, "100% T:       ");
  OLED_ShowString(48, 2, buf_t);
  OLED_ShowString(80, 2, " S:");
  OLED_ShowString(100, 2, buf_s);

  // Stop
  PWMX_16bit_ACTOUT(CH_PWM4, 0, High_Level, DISABLE);
  PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);

  OLED_ShowString(0, 3, "Done.         ");

  while (1) {
    DelayMs(100);
  }
}
