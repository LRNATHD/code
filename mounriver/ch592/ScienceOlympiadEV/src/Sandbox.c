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
#define ENCODER_PPR 7.0f  // Pulses per Motor Revolution
#define GEAR_RATIO 51.43f // Gear Ratio (~1:51.45)

// Counting BOTH rising and falling edges of channel A = 2 counts per pulse.
// Based on exact N20 1:51.45 Micro Metal Gearmotor specs:
#define COUNTS_PER_ROTATION 720

#define WHEEL_DIAMETER_MM 63.5f // 2.5 inches exactly
#define PI 3.14159265f
#define WHEEL_CIRCUMFERENCE_MM (WHEEL_DIAMETER_MM * PI)

// Ticks per mm = (Counts per rotation) / (Wheel circumference in mm)
#define TICKS_PER_MM ((float)COUNTS_PER_ROTATION / WHEEL_CIRCUMFERENCE_MM)

float CalculateSpeedProfile(int current_counts, int target_counts);

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
  if (percent < -100.0f)
    percent = -100.0f;

  if (percent < 0.0f) {
    GPIOA_ResetBits(Left_Phase); // Reverse
    percent = -percent;
  } else {
    GPIOA_SetBits(Left_Phase); // Forward
  }

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
  if (percent < -100.0f)
    percent = -100.0f;

  if (percent < 0.0f) {
    GPIOA_ResetBits(Right_Phase); // Reverse
    percent = -percent;
  } else {
    GPIOA_SetBits(Right_Phase); // Forward
  }

  uint32_t pwm_val = (uint32_t)((PWM_MAX_PERIOD * percent) / 100.0f);
  if (percent > 0.0f) {
    PWMX_16bit_ACTOUT(CH_PWM5, pwm_val, High_Level, ENABLE);
  } else {
    PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);
    GPIOA_ResetBits(Right_Enable);
  }
}

float CalculateSpeedProfile(int current_counts, int target_counts) {
  // Distance-based Trapezoidal Speed Profile (Ramp Up -> Coast -> Ramp Down)

  // Limits
  const float MAX_SPEED = 25.0f; // Max coasting speed
  const float MIN_SPEED = 10.0f; // Minimum to overcome friction

  // Ramp settings (in encoder counts)
  // 100 counts translates to roughly 14mm of ramping distance.
  const int RAMP_UP_COUNTS = 100;
  const int RAMP_DOWN_COUNTS = 150;

  int remaining_counts = target_counts - current_counts;

  // 1. If we've hit or passed the target, stop immediately.
  if (remaining_counts <= 0) {
    return 0.0f;
  }

  float target_speed = MAX_SPEED;

  // 2. Ramp Down Phase (Prioritized if distance is short)
  if (remaining_counts < RAMP_DOWN_COUNTS) {
    // Linearly scale from MAX_SPEED down to MIN_SPEED based on remaining
    // distance
    float progress = (float)remaining_counts / (float)RAMP_DOWN_COUNTS;
    target_speed = MIN_SPEED + (progress * (MAX_SPEED - MIN_SPEED));
  }
  // 3. Ramp Up Phase
  else if (current_counts < RAMP_UP_COUNTS) {
    // Linearly scale from MIN_SPEED up to MAX_SPEED based on distance traveled
    float progress = (float)current_counts / (float)RAMP_UP_COUNTS;
    target_speed = MIN_SPEED + (progress * (MAX_SPEED - MIN_SPEED));
  }

  if (target_speed < MIN_SPEED) {
    target_speed = MIN_SPEED;
  }

  return target_speed;
}

int main(void) {
  SetSysClock(CLK_SOURCE_PLL_60MHz);

  OLED_Init();
  Motor_Init();

  // Initialize BOOT button (PB22) as input with pull-up
  GPIOB_ModeCfg(GPIO_Pin_22, GPIO_ModeIN_PU);

  // --- TARGET SETTING ---
  float target_distance_mm = 100.0f;
  int target_counts = (int)(target_distance_mm * TICKS_PER_MM);

  while (1) {
    OLED_Clear();
    OLED_ShowString(0, 0, "Ready!");

    char trgt_buf[32];
    sprintf(trgt_buf, "Target: %dmm", (int)target_distance_mm);
    OLED_ShowString(0, 1, trgt_buf);

    OLED_ShowString(0, 3, "Press BOOT btn");

    // Wait for button press (active low)
    while (GPIOB_ReadPortPin(GPIO_Pin_22) != 0) {
      DelayMs(10);
    }

    count_left = 0;
    count_right = 0;

    OLED_Clear();
    OLED_ShowString(0, 0, "Driving ~100mm");

    uint8_t left_braking = 0;
    uint8_t right_braking = 0;

    // Track counts to detect backward movement during braking
    int brake_start_left = 0;
    int brake_start_right = 0;

    int last_left = 0;
    int last_right = 0;

    while (1) {
      int current_left = count_left;
      if (current_left < 0)
        current_left = -current_left;

      int current_right = count_right;
      if (current_right < 0)
        current_right = -current_right;

      float pct_left = 0.0f;
      float pct_right = 0.0f;

      // LEFT MOTOR LOGIC
      if (left_braking) {
        // If we are actively braking, apply 15% reverse power
        // Until the encoder count actually drops
        if (current_left <= last_left) {
          pct_left = 0.0f;  // Braked enough
          left_braking = 2; // Move to 'done' state
        } else {
          pct_left = -15.0f;
        }
      } else if (left_braking == 0) {
        pct_left = CalculateSpeedProfile(current_left, target_counts);
        // If profile says 0, trigger braking phase
        if (pct_left == 0.0f) {
          left_braking = 1;
          brake_start_left = current_left;
          pct_left = -15.0f;
        }
      }

      // RIGHT MOTOR LOGIC
      if (right_braking) {
        // If we are actively braking, apply 15% reverse power
        // Until the encoder count actually drops
        if (current_right <= last_right) {
          pct_right = 0.0f;  // Braked enough
          right_braking = 2; // Move to 'done' state
        } else {
          pct_right = -15.0f;
        }
      } else if (right_braking == 0) {
        pct_right = CalculateSpeedProfile(current_right, target_counts);
        // If profile says 0, trigger braking phase
        if (pct_right == 0.0f) {
          right_braking = 1;
          brake_start_right = current_right;
          pct_right = -15.0f;
        }
      }

      SetLeftMotor(pct_left);
      SetRightMotor(pct_right);

      // If both are done braking, exit the loop
      if (left_braking == 2 && right_braking == 2) {
        break;
      }

      last_left = current_left;
      last_right = current_right;

      DelayMs(10);
    } // End of driving loop

    // Ensure motors are stopped completely after completing the sequence
    SetLeftMotor(0.0f);
    SetRightMotor(0.0f);

    OLED_Clear();
    OLED_ShowString(0, 0, "Finished!");

    char buf[32];
    sprintf(buf, "L: %d", (int)count_left);
    OLED_ShowString(0, 1, buf);
    sprintf(buf, "R: %d", (int)count_right);
    OLED_ShowString(0, 2, buf);

    sprintf(buf, "Target: %d", target_counts);
    OLED_ShowString(0, 3, buf);

    // Wait for button release
    while (GPIOB_ReadPortPin(GPIO_Pin_22) == 0) {
      DelayMs(10);
    }

    // Short delay before allowing the next run
    DelayMs(1000);
  }
}
