#include "CH59x_common.h"
#include "CH59x_timer.h"
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
#define ENCODER_PPR 7.0f        // pulses per revolution (on the ungeared motor)
#define GEAR_RATIO 51.43f       // gear ratio of the motor
#define COUNTS_PER_ROTATION 720 // pulses per revolution of the output shaft
#define WHEEL_DIAMETER_MM 63.5f // 2.5inches
#define PI 3.14159265f          // pi to a decent amount
#define WHEEL_CIRCUMFERENCE_MM (WHEEL_DIAMETER_MM * PI)
#define TICKS_PER_MM ((float)COUNTS_PER_ROTATION / WHEEL_CIRCUMFERENCE_MM)
#define TICKS_PER_METER (TICKS_PER_MM * 1000.0f)

volatile int32_t count_left = 0;
volatile int32_t count_right = 0;
volatile uint32_t timer_ticks = 0;

__INTERRUPT // timer, runs ever ms
    __HIGH_CODE void TMR0_IRQHandler(void) {
  if (TMR0_GetITFlag(TMR0_3_IT_CYC_END)) {
    TMR0_ClearITFlag(TMR0_3_IT_CYC_END);
    timer_ticks++;
  }
}

__INTERRUPT // encoder
    __HIGH_CODE void GPIOB_IRQHandler(void) {
  if (GPIOB_ReadITFlagBit(La)) {
    uint8_t a = (GPIOB_ReadPortPin(La) != 0);
    uint8_t b = (GPIOB_ReadPortPin(Lb) != 0);

    if (a == b)
      count_left++;
    else
      count_left--;

    if (a)
      GPIOB_ITModeCfg(La, GPIO_ITMode_FallEdge);
    else
      GPIOB_ITModeCfg(La, GPIO_ITMode_RiseEdge);

    GPIOB_ClearITFlagBit(La);
  }
}

__INTERRUPT // encoder
    __HIGH_CODE void GPIOA_IRQHandler(void) {
  if (GPIOA_ReadITFlagBit(Ra)) {
    uint8_t a = (GPIOA_ReadPortPin(Ra) != 0);
    uint8_t b = (GPIOA_ReadPortPin(Rb) != 0);

    if (a == b)
      count_right++;
    else
      count_right--;

    if (a)
      GPIOA_ITModeCfg(Ra, GPIO_ITMode_FallEdge);
    else
      GPIOA_ITModeCfg(Ra, GPIO_ITMode_RiseEdge);

    GPIOA_ClearITFlagBit(Ra);
  }
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

  PWMX_CLKCfg(4);
  PWMX_16bit_CycleCfg(PWM_MAX_PERIOD);
  PWMX_16bit_ACTOUT(CH_PWM4, 0, High_Level, DISABLE);
  PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);

  GPIOA_SetBits(Left_Phase);
  GPIOA_SetBits(Right_Phase);
}

enum UIState {
  PAGE_TIME,
  PAGE_DISTANCE,
  PAGE_PRIMED,
  PAGE_RUNNING,
  PAGE_FINISHED
};

int main(void) {
  SetSysClock(CLK_SOURCE_PLL_60MHz);

  // Initialize timer for 1ms ticks
  TMR0_TimerInit(FREQ_SYS / 1000);
  TMR0_ITCfg(ENABLE, TMR0_3_IT_CYC_END);
  PFIC_EnableIRQ(TMR0_IRQn);

  OLED_Init();
  Motor_Init();

  // Initialize BOOT button
  GPIOB_ModeCfg(GPIO_Pin_22, GPIO_ModeIN_PU); // BOOT

  // Note: PB7 and PB4 are shared with I2C display.
  // Their mode will be dynamically swapped between In and Out depending on what
  // we are doing.

  float target_time_s = 10.0f;
  float target_distance_m = 7.0f;

  enum UIState state = PAGE_TIME;
  uint8_t screen_needs_update = 1;
  int final_time_ms = 0;

  while (1) {
    if (state == PAGE_TIME || state == PAGE_DISTANCE || state == PAGE_PRIMED) {
      uint8_t boot_pressed = (GPIOB_ReadPortPin(GPIO_Pin_22) == 0);
      uint8_t pb7_pressed = (GPIOB_ReadPortPin(GPIO_Pin_7) == 0);
      uint8_t pb4_pressed = (GPIOB_ReadPortPin(GPIO_Pin_4) == 0);

      if (!boot_pressed && !pb7_pressed && !pb4_pressed &&
          screen_needs_update) {
        GPIOB_ModeCfg(GPIO_Pin_7 | GPIO_Pin_4, GPIO_ModeOut_PP_5mA);
        GPIOB_SetBits(GPIO_Pin_7 | GPIO_Pin_4); // Idle High
        OLED_Clear();
        char buf[32];
        if (state == PAGE_TIME) {
          OLED_ShowString(0, 0, "--- 1. TIME ---");
          sprintf(buf, "Time: %d.%ds", (int)target_time_s,
                  ((int)(target_time_s * 10)) % 10);
          OLED_ShowString(0, 1, buf);
          OLED_ShowString(0, 2, "Boot: +/- 0.5s");
          OLED_ShowString(0, 3, "4/7+Boot: Next");
        } else if (state == PAGE_DISTANCE) {
          OLED_ShowString(0, 0, "--- 2. DISTANCE ---");
          sprintf(buf, "Dist: %d.%02dm", (int)target_distance_m,
                  ((int)(target_distance_m * 100)) % 100);
          OLED_ShowString(0, 1, buf);
          OLED_ShowString(0, 2, "Boot:1 PB7:.1 4:.01");
          OLED_ShowString(0, 3, "4/7+Boot: Prime");
        } else if (state == PAGE_PRIMED) {
          OLED_ShowString(0, 0, "--- 3. PRIMED ---");
          sprintf(buf, "%ds", (int)target_time_s);
          OLED_ShowString(0, 1, buf);
          sprintf(buf, "%d.%02dm", (int)target_distance_m,
                  ((int)(target_distance_m * 100)) % 100);
          OLED_ShowString(80, 1, buf);
          OLED_ShowString(0, 3, "BOOT to START");
        }
        screen_needs_update = 0;
      }

      GPIOB_ModeCfg(GPIO_Pin_7 | GPIO_Pin_4, GPIO_ModeIN_PU);

      if (boot_pressed || pb7_pressed || pb4_pressed) {
        uint32_t press_time = 0;
        uint8_t boot_was_pressed = 0;
        uint8_t pb7_was_pressed = 0;
        uint8_t pb4_was_pressed = 0;

        // Read continuously until all released
        while (1) {
          if (GPIOB_ReadPortPin(GPIO_Pin_22) == 0)
            boot_was_pressed = 1;
          if (GPIOB_ReadPortPin(GPIO_Pin_7) == 0)
            pb7_was_pressed = 1;
          if (GPIOB_ReadPortPin(GPIO_Pin_4) == 0)
            pb4_was_pressed = 1;

          if (GPIOB_ReadPortPin(GPIO_Pin_22) != 0 &&
              GPIOB_ReadPortPin(GPIO_Pin_7) != 0 &&
              GPIOB_ReadPortPin(GPIO_Pin_4) != 0) {
            break; // All released
          }
          DelayMs(10);
          press_time += 10;

          // Repeat subtract while held logic (turbo-fire every 200ms after
          // initial 400ms delay)
          if (press_time >= 400 && (press_time % 200 == 0)) {
            if (!pb7_was_pressed ||
                !pb4_was_pressed) { // Only repeat for single modifiers
              if (state == PAGE_TIME && boot_was_pressed) {
                target_time_s -= 0.5f;
                if (target_time_s < 2.0f)
                  target_time_s =
                      2.0f; // Allow dialing down to 2 seconds for testing
              } else if (state == PAGE_DISTANCE) {
                if (boot_was_pressed)
                  target_distance_m -= 1.0f;
                if (pb7_was_pressed)
                  target_distance_m -= 0.1f;
                if (pb4_was_pressed)
                  target_distance_m -= 0.01f;
                if (target_distance_m < 0.0f)
                  target_distance_m = 0.0f;
              }
              // Since we process during the hold, don't double process on
              // release. Setting press_time to something that won't trigger the
              // "add" will just mean the continuous logic takes over entirely.
            }
          }
        }

        uint8_t is_long_press = (press_time >= 400);

        // Handle commands based on state
        if ((pb7_was_pressed || pb4_was_pressed) && boot_was_pressed) {
          // Simultaneous navigation
          if (is_long_press) {
            // Go Back
            if (state == PAGE_PRIMED)
              state = PAGE_DISTANCE;
            else if (state == PAGE_DISTANCE)
              state = PAGE_TIME;
          } else {
            // Go Forward
            if (state == PAGE_TIME)
              state = PAGE_DISTANCE;
            else if (state == PAGE_DISTANCE)
              state = PAGE_PRIMED;
          }
        } else if (!is_long_press) {
          if (state == PAGE_TIME) {
            if (boot_was_pressed && !pb7_was_pressed && !pb4_was_pressed) {
              target_time_s += 0.5f;
              if (target_time_s > 20.0f)
                target_time_s = 20.0f;
            }
          } else if (state == PAGE_DISTANCE) {
            if (boot_was_pressed && !pb7_was_pressed && !pb4_was_pressed) {
              target_distance_m += 1.0f;
            } else if (pb7_was_pressed && !boot_was_pressed &&
                       !pb4_was_pressed) {
              target_distance_m += 0.1f;
            } else if (pb4_was_pressed && !boot_was_pressed &&
                       !pb7_was_pressed) {
              target_distance_m += 0.01f;
            }
          } else if (state == PAGE_PRIMED) {
            if (boot_was_pressed && !pb7_was_pressed && !pb4_was_pressed) {
              state = PAGE_RUNNING;
            }
          }
        }

        screen_needs_update = 1;
        DelayMs(50); // Debounce
      }
    } else if (state == PAGE_RUNNING) {
      // ==========================
      // RUNNING TRAJECTORY LOGIC
      // ==========================
      GPIOB_ModeCfg(GPIO_Pin_7 | GPIO_Pin_4, GPIO_ModeOut_PP_5mA);
      GPIOB_SetBits(GPIO_Pin_7 | GPIO_Pin_4); // Idle High
      OLED_Clear();
      OLED_ShowString(0, 0, "EVENT START");

      count_left = 0;
      count_right = 0;
      timer_ticks = 0;

      int target_ticks = (int)(target_distance_m * TICKS_PER_METER);
      int target_ms = (int)(target_time_s * 1000.0f);

      float MIN_SPEED = 10.0f;
      float Kp = 1.0f;  // Gain for overall positioning error
      float Ki = 0.05f; // Integral gain to eliminate steady-state time lag
      float Kp_balance = 0.3f; // Gain for side-to-side drift synchronization

      uint8_t left_braking = 0;
      uint8_t right_braking = 0;
      int last_left = 0;
      int last_right = 0;

      float integral_error_left = 0.0f;
      float integral_error_right = 0.0f;

      int last_time_ms = 0;
      final_time_ms = 0; // reset for a new run

      float last_pct_left = 0.0f;
      float last_pct_right = 0.0f;

      while (1) {
        int current_time_ms = timer_ticks;

        // Wait until exactly 10ms have passed since the last loop
        while (current_time_ms - last_time_ms < 10) {
          current_time_ms = timer_ticks;
        }
        last_time_ms = current_time_ms;

        int current_left = count_left;
        if (current_left < 0)
          current_left = -current_left;
        int current_right = count_right;
        if (current_right < 0)
          current_right = -current_right;

        float t = (float)current_time_ms / (float)target_ms;
        if (t > 1.0f)
          t = 1.0f;
        float t2 = t * t;
        float t3 = t2 * t;

        // Smooth Cubic Trajectory:
        // position(t) = D * (-1.9 t^3 + 2.9 t^2)
        // velocity(t) = (D/T) * (-5.7 t^2 + 5.8 t)
        // This ensures reaching exactly D at exactly T, starting from 0 speed,
        // peaking at ~1.5x average speed, and ending exactly at a slow 10%
        // crawl speed at T.

        float expected_position_f =
            (float)target_ticks * (-1.9f * t3 + 2.9f * t2);
        int expected_position = (int)expected_position_f;
        if (expected_position > target_ticks)
          expected_position = target_ticks;

        float expected_velocity_ticks_per_ms =
            ((float)target_ticks / (float)target_ms) * (-5.7f * t2 + 5.8f * t);

        // Calculate expected velocity for feed-forward power
        // 1% Pwm gives ~ 0.036 ticks/ms. Power = Velocity_Ticks_Per_Ms / 0.036
        // = Velocity * 27.7f
        float base_power = expected_velocity_ticks_per_ms * 27.7f;
        if (base_power > 100.0f)
          base_power = 100.0f;
        if (base_power < 0.0f)
          base_power = 0.0f;

        float pct_left = 0.0f;
        float pct_right = 0.0f;

        // Control Loop Left
        if (left_braking) {
          if (current_left <= last_left) {
            pct_left = 0.0f;
            left_braking = 2; // complete
          } else {
            pct_left = -15.0f;
          }
        } else {
          if (current_left >= target_ticks) {
            left_braking = 1;
            pct_left = -15.0f;
            if (final_time_ms == 0)
              final_time_ms = current_time_ms;
          } else {
            float error = expected_position - current_left;
            integral_error_left += error;

            // Anti-windup cap for integral
            if (integral_error_left > 1000.0f)
              integral_error_left = 1000.0f;
            if (integral_error_left < -1000.0f)
              integral_error_left = -1000.0f;

            float sync_error = current_right - current_left;
            pct_left = base_power + (error * Kp) + (integral_error_left * Ki) +
                       (sync_error * Kp_balance);

            if (pct_left < 0.0f) {
              pct_left =
                  0.0f; // Allow coasting if overshooting (negative PI output)
            } else if (pct_left > 0.0f && pct_left < MIN_SPEED &&
                       expected_position < target_ticks) {
              pct_left = MIN_SPEED; // Enforce minimum torque if we need to
                                    // track forward
            }
            if (pct_left > 100.0f)
              pct_left = 100.0f;

            // Slew rate limits to prevent breaking traction
            // 2.5% per 10ms = 250% per second
            if (pct_left > last_pct_left + 2.5f) {
              pct_left = last_pct_left + 2.5f;
            } else if (pct_left < last_pct_left - 2.5f) {
              pct_left = last_pct_left - 2.5f;
            }
          }
        }

        // Control Loop Right
        if (right_braking) {
          if (current_right <= last_right) {
            pct_right = 0.0f;
            right_braking = 2; // complete
          } else {
            pct_right = -15.0f;
          }
        } else {
          if (current_right >= target_ticks) {
            right_braking = 1;
            pct_right = -15.0f;
            if (final_time_ms == 0)
              final_time_ms = current_time_ms;
          } else {
            float error = expected_position - current_right;
            integral_error_right += error;

            // Anti-windup cap for integral
            if (integral_error_right > 1000.0f)
              integral_error_right = 1000.0f;
            if (integral_error_right < -1000.0f)
              integral_error_right = -1000.0f;

            float sync_error = current_left - current_right;
            pct_right = base_power + (error * Kp) +
                        (integral_error_right * Ki) + (sync_error * Kp_balance);

            if (pct_right < 0.0f) {
              pct_right =
                  0.0f; // Allow coasting if overshooting (negative PI output)
            } else if (pct_right > 0.0f && pct_right < MIN_SPEED &&
                       expected_position < target_ticks) {
              pct_right = MIN_SPEED; // Enforce minimum torque if we need to
                                     // track forward
            }
            if (pct_right > 100.0f)
              pct_right = 100.0f;

            // Slew rate limits to prevent breaking traction
            // 2.5% per 10ms = 250% per second
            if (pct_right > last_pct_right + 2.5f) {
              pct_right = last_pct_right + 2.5f;
            } else if (pct_right < last_pct_right - 2.5f) {
              pct_right = last_pct_right - 2.5f;
            }
          }
        }

        last_pct_left = pct_left;
        last_pct_right = pct_right;

        SetLeftMotor(pct_left);
        SetRightMotor(pct_right);

        if (left_braking == 2 && right_braking == 2) {
          state = PAGE_FINISHED;
          screen_needs_update = 1;
          break;
        }

        last_left = current_left;
        last_right = current_right;
      }
    } else if (state == PAGE_FINISHED) {
      SetLeftMotor(0.0f);
      SetRightMotor(0.0f);

      if (screen_needs_update) {
        GPIOB_ModeCfg(GPIO_Pin_7 | GPIO_Pin_4, GPIO_ModeOut_PP_5mA);
        GPIOB_SetBits(GPIO_Pin_7 | GPIO_Pin_4); // Idle High
        OLED_Clear();
        char buf[32];
        OLED_ShowString(0, 0, "FINISHED!");

        // Calculate average mm traveled (using left motor as reference, or
        // average of both)
        int avg_counts = (count_left + count_right) / 2;
        int distance_mm = (int)((float)avg_counts / TICKS_PER_MM);

        sprintf(buf, "Time: %ld ms", (long int)final_time_ms);
        OLED_ShowString(0, 1, buf);

        sprintf(buf, "Dist: %d mm", distance_mm);
        OLED_ShowString(0, 2, buf);

        OLED_ShowString(0, 3, "4/7+Boot: Reset");
        screen_needs_update = 0;
      }

      GPIOB_ModeCfg(GPIO_Pin_7 | GPIO_Pin_4, GPIO_ModeIN_PU);

      uint8_t boot_pressed = (GPIOB_ReadPortPin(GPIO_Pin_22) == 0);
      uint8_t pb7_pressed = (GPIOB_ReadPortPin(GPIO_Pin_7) == 0);
      uint8_t pb4_pressed = (GPIOB_ReadPortPin(GPIO_Pin_4) == 0);

      if (boot_pressed && (pb7_pressed || pb4_pressed)) {
        while (GPIOB_ReadPortPin(GPIO_Pin_22) == 0 ||
               GPIOB_ReadPortPin(GPIO_Pin_7) == 0 ||
               GPIOB_ReadPortPin(GPIO_Pin_4) == 0) {
          DelayMs(10);
        }
        state = PAGE_TIME;
        screen_needs_update = 1;
        DelayMs(50);
      }
    }
  }
}
