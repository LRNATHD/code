#include "CH59x_common.h"
#include "oled_driver.h"

// --- Motor Pin Definitions ---
#define Left_Enable GPIO_Pin_12  // PA12 (PWM4)
#define Left_Phase GPIO_Pin_14   // PA14
#define Right_Enable GPIO_Pin_13 // PA13 (PWM5)
#define Right_Phase GPIO_Pin_15  // PA15

// --- Constants ---
#define PWM_MAX_PERIOD 60000 // Must be <= 65535 (16-bit PWM)

// === SET YOUR SPEED HERE (0.0 to 100.0) ===
#define MOTOR_SPEED_PERCENT 3.0f
// ==========================================

void Motor_Init(void) {
  // Motor Enable (PWM) and Phase pins as output
  GPIOA_ModeCfg(Left_Enable | Left_Phase | Right_Enable | Right_Phase,
                GPIO_ModeOut_PP_5mA);
  GPIOA_ResetBits(Left_Enable | Right_Enable); // Motors OFF

  // PWM Setup - MUST use 16bit version
  PWMX_CLKCfg(4);
  PWMX_16bit_CycleCfg(PWM_MAX_PERIOD);
  PWMX_16bit_ACTOUT(CH_PWM4, 0, High_Level, DISABLE);
  PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);

  // Forward direction
  GPIOA_SetBits(Left_Phase);
  GPIOA_SetBits(Right_Phase);
}

void SetBothMotors(float percent) {
  if (percent > 100.0f)
    percent = 100.0f;
  if (percent < 0.0f)
    percent = 0.0f;

  uint32_t pwm_val = (uint32_t)((PWM_MAX_PERIOD * percent) / 100.0f);

  if (percent > 0.0f) {
    PWMX_16bit_ACTOUT(CH_PWM4, pwm_val, High_Level, ENABLE); // Left
    PWMX_16bit_ACTOUT(CH_PWM5, pwm_val, High_Level, ENABLE); // Right
  } else {
    PWMX_16bit_ACTOUT(CH_PWM4, 0, High_Level, DISABLE);
    PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);
    GPIOA_ResetBits(Left_Enable | Right_Enable);
  }
}

int main(void) {
  SetSysClock(CLK_SOURCE_PLL_60MHz);

  OLED_Init();
  Motor_Init();

  OLED_Clear();
  OLED_ShowString(0, 0, "Motor Test");
  OLED_ShowString(0, 1, "Running...");

  // Run both motors at the configured speed
  SetBothMotors(MOTOR_SPEED_PERCENT);

  // Just keep running forever
  while (1) {
    DelayMs(1000);
  }
}
