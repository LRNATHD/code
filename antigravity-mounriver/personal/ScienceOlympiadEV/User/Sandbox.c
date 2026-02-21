#include "CH59x_common.h"
#include "oled_driver.h"
#include <stdio.h>

// --- Motor Pin Definitions ---
#define Left_Enable GPIO_Pin_12  // PA12 (PWM4)
#define Left_Phase GPIO_Pin_14   // PA14
#define Right_Enable GPIO_Pin_13 // PA13 (PWM5)
#define Right_Phase GPIO_Pin_15  // PA15

// --- Encoder Pin Definitions ---
#define Left_Encoder_A GPIO_Pin_6  // PB6
#define Left_Encoder_B GPIO_Pin_0  // PB0
#define Right_Encoder_A GPIO_Pin_4 // PA4
#define Right_Encoder_B GPIO_Pin_5 // PA5

#define La Left_Encoder_A
#define Lb Left_Encoder_B
#define Ra Right_Encoder_A
#define Rb Right_Encoder_B

#define PWM_MAX_PERIOD 60000 // Must be <= 65535 (16-bit PWM)

// Physics Constants
#define ENCODER_PPR 7.0f // Pulses per Motor Revolution
#define GEAR_RATIO 50.0f // Gear Ratio (1:50)

// Counting BOTH rising and falling edges of channel A = 2 counts per pulse.
// Total counts per wheel rotation = 7 * 2 * 50 = 700
#define COUNTS_PER_ROTATION 700

volatile int32_t count_left = 0;
volatile int32_t count_right = 0;

__INTERRUPT
__HIGH_CODE
void GPIOB_IRQHandler(void) {
  // Left Encoder A (PB6)
  if (GPIOB_ReadITFlagBit(La)) {
    uint8_t a = (GPIOB_ReadPortPin(La) != 0);
    uint8_t b = (GPIOB_ReadPortPin(Lb) != 0);

    if (a == b)
      count_left++;
    else
      count_left--;

    // Toggle edge detection for double resolution
    if (a)
      GPIOB_ITModeCfg(La, GPIO_ITMode_FallEdge);
    else
      GPIOB_ITModeCfg(La, GPIO_ITMode_RiseEdge);

    GPIOB_ClearITFlagBit(La);
  }
}

__INTERRUPT
__HIGH_CODE
void GPIOA_IRQHandler(void) {
  // Right Encoder A (PA4)
  if (GPIOA_ReadITFlagBit(Ra)) {
    uint8_t a = (GPIOA_ReadPortPin(Ra) != 0);
    uint8_t b = (GPIOA_ReadPortPin(Rb) != 0);

    if (a == b)
      count_right++;
    else
      count_right--;

    // Toggle edge detection for double resolution
    if (a)
      GPIOA_ITModeCfg(Ra, GPIO_ITMode_FallEdge);
    else
      GPIOA_ITModeCfg(Ra, GPIO_ITMode_RiseEdge);

    GPIOA_ClearITFlagBit(Ra);
  }
}

void Motor_Init(void) {
  // Motor Pins
  GPIOA_ModeCfg(Left_Enable | Left_Phase | Right_Enable | Right_Phase,
                GPIO_ModeOut_PP_5mA);
  GPIOA_ResetBits(Left_Enable | Right_Enable); // Motors OFF

  // Encoders
  GPIOB_ModeCfg(La | Lb, GPIO_ModeIN_PU);
  GPIOA_ModeCfg(Ra | Rb, GPIO_ModeIN_PU);

  GPIOB_ITModeCfg(La, GPIO_ITMode_FallEdge);
  GPIOA_ITModeCfg(Ra, GPIO_ITMode_FallEdge);

  PFIC_EnableIRQ(GPIO_B_IRQn);
  PFIC_EnableIRQ(GPIO_A_IRQn);

  // PWM Setup
  PWMX_CLKCfg(4);
  PWMX_16bit_CycleCfg(PWM_MAX_PERIOD);
  PWMX_16bit_ACTOUT(CH_PWM4, 0, High_Level, DISABLE);
  PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);

  // Set forward direction
  GPIOA_SetBits(Left_Phase);
  GPIOA_SetBits(Right_Phase);
}

void SetLeftMotor(float percent) {
  if (percent > 100.0f)
    percent = 100.0f;
  if (percent < 0.0f)
    percent = 0.0f;
  uint32_t pwm_val = (uint32_t)((PWM_MAX_PERIOD * percent) / 100.0f);
  if (percent > 0.0f) {
    PWMX_16bit_ACTOUT(CH_PWM4, pwm_val, High_Level, ENABLE);
  } else {
    PWMX_16bit_ACTOUT(CH_PWM4, 0, High_Level, DISABLE);
    GPIOA_ResetBits(Left_Enable);
  }
}

void SetRightMotor(float percent) {
  if (percent > 100.0f)
    percent = 100.0f;
  if (percent < 0.0f)
    percent = 0.0f;
  uint32_t pwm_val = (uint32_t)((PWM_MAX_PERIOD * percent) / 100.0f);
  if (percent > 0.0f) {
    PWMX_16bit_ACTOUT(CH_PWM5, pwm_val, High_Level, ENABLE);
  } else {
    PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);
    GPIOA_ResetBits(Right_Enable);
  }
}

int main(void) {
  SetSysClock(CLK_SOURCE_PLL_60MHz);

  OLED_Init();
  Motor_Init();

  count_left = 0;
  count_right = 0;

  OLED_Clear();
  OLED_ShowString(0, 0, "Spinning 1 Rot");

  int target_counts = COUNTS_PER_ROTATION;

  while (1) {
    int current_left = count_left;
    if (current_left < 0)
      current_left = -current_left;

    int current_right = count_right;
    if (current_right < 0)
      current_right = -current_right;

    int remaining_left = target_counts - current_left;
    int remaining_right = target_counts - current_right;

    // Proportional control to "edge off" speed as we approach the target
    float pct_left = 0.0f;
    if (remaining_left > 0) {
      // 100 counts left -> 50% speed. Over 200 counts -> 100% speed.
      pct_left = (float)remaining_left * 0.5f;
      if (pct_left > 100.0f)
        pct_left = 100.0f;
      // Minimum power to keep the motor moving to avoid stopping from friction
      if (pct_left < 15.0f)
        pct_left = 15.0f;
    }

    float pct_right = 0.0f;
    if (remaining_right > 0) {
      pct_right = (float)remaining_right * 0.5f;
      if (pct_right > 100.0f)
        pct_right = 100.0f;
      if (pct_right < 15.0f)
        pct_right = 15.0f;
    }

    // Stop if reached or exceeded
    if (remaining_left <= 0)
      pct_left = 0.0f;
    if (remaining_right <= 0)
      pct_right = 0.0f;

    SetLeftMotor(pct_left);
    SetRightMotor(pct_right);

    // Update Display during travel
    char buf[32];
    sprintf(buf, "L: %d/%d", current_left, target_counts);
    OLED_ShowString(0, 1, buf);
    sprintf(buf, "R: %d/%d", current_right, target_counts);
    OLED_ShowString(0, 2, buf);
    sprintf(buf, "Spd: %d%% %d%%", (int)pct_left, (int)pct_right);
    OLED_ShowString(0, 3, buf);

    // If both are done, exit the loop
    if (remaining_left <= 0 && remaining_right <= 0) {
      break;
    }

    DelayMs(10);
  }

  // Ensure motors are stopped completely after completing the rotation
  SetLeftMotor(0.0f);
  SetRightMotor(0.0f);

  OLED_Clear();
  OLED_ShowString(0, 0, "Finished!");

  while (1) {
    char buf[32];
    // Final check inside infinite loop to display what was recorded
    sprintf(buf, "L: %d", (int)count_left);
    OLED_ShowString(0, 1, buf);
    sprintf(buf, "R: %d", (int)count_right);
    OLED_ShowString(0, 2, buf);
    OLED_ShowString(0, 3, "Exactly 1 Rot.");
    DelayMs(100);
  }
}
