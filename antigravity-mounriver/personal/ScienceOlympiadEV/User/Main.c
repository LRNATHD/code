#include "CH59x_common.h"
#include "CH59x_timer.h"
#include "oled_driver.h"
#include <stdio.h>

// --- Motor Pin Definitions ---
#define Right_Enable GPIO_Pin_13 // PA13 (PWM5)
#define Right_Phase GPIO_Pin_15  // PA15
#define right_Correction 1       // easily switch motor direction

#define Left_Enable GPIO_Pin_12 // PA12 (PWM4)
#define Left_Phase GPIO_Pin_14  // PA14
#define left_Correction 1       // easily switch motor direction

// --- Encoder Pin Definitions ---
#define Left_Encoder_A GPIO_Pin_6  // PB6
#define Left_Encoder_B GPIO_Pin_0  // PB0
#define Right_Encoder_A GPIO_Pin_4 // PA4
#define Right_Encoder_B GPIO_Pin_5 // PA5

// Alias mappings for compatibility
#define La Left_Encoder_A
#define Lb Left_Encoder_B
#define Ra Right_Encoder_A
#define Rb Right_Encoder_B

// --- Constants ---
#define PWM_MAX_PERIOD 60000 // Must be <= 65535 (16-bit PWM)

// Physics Constants (N20 300RPM Motor 50:1)
#define ENCODER_PPR 7.0f    // Pulses per Motor Revolution (Hall Sensor)
#define GEAR_RATIO 50.0f    // Gear Ratio (1:50)
#define WHEEL_DIAM_M 0.090f // Wheel Diameter 90mm
#define PI 3.1415926f

// Ticks per meter = (Gear_Ratio * PPR) / (Wheel_Diameter * PI)
#define TICKS_PER_METER ((GEAR_RATIO * ENCODER_PPR) / (WHEEL_DIAM_M * PI))

// --- Calibration Configuration ---
#define NUM_CAL_POINTS 6
float duty_percents[NUM_CAL_POINTS] = {0.1f, 1.0f, 5.0f, 10.0f, 50.0f, 90.0f};

// Calibration results: [motor][speed_step] in m/s
// motor: 0=Left, 1=Right
float cal_results[2][NUM_CAL_POINTS];

// --- Global Variables ---
volatile int32_t count_left = 0;
volatile int32_t count_right = 0;
volatile uint32_t timer_ticks = 0;

// distances (meters)
volatile int32_t targetdistance = 0;
volatile int32_t currentdistance = 0;

// time (seconds)
volatile int32_t targettime = 0;
volatile int32_t currenttime = 0;

// calibrated max speeds (m/s)
static float leftmotormaxspeed = 0;
static float rightmotormaxspeed = 0;
static float combinedmaxspeed = 0;

// --- Interrupt Handlers ---

__INTERRUPT
__HIGH_CODE
void TMR0_IRQHandler(void) {
  if (TMR0_GetITFlag(TMR0_3_IT_CYC_END)) {
    TMR0_ClearITFlag(TMR0_3_IT_CYC_END);
    timer_ticks++;
  }
}

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

// --- Motor Control Functions ---

void Motor_Init(void) {
  // Motor Enable (PWM) and Phase pins as output
  GPIOA_ModeCfg(Left_Enable | Left_Phase | Right_Enable | Right_Phase,
                GPIO_ModeOut_PP_5mA);
  GPIOA_ResetBits(Left_Enable | Right_Enable); // Motors OFF

  // Left Encoder on Port B (PB6, PB0)
  GPIOB_ModeCfg(La | Lb, GPIO_ModeIN_PU);

  // Right Encoder on Port A (PA4, PA5)
  GPIOA_ModeCfg(Ra | Rb, GPIO_ModeIN_PU);

  // Encoder interrupts (start with falling edge)
  GPIOB_ITModeCfg(La, GPIO_ITMode_FallEdge);
  GPIOA_ITModeCfg(Ra, GPIO_ITMode_FallEdge);

  PFIC_EnableIRQ(GPIO_B_IRQn);
  PFIC_EnableIRQ(GPIO_A_IRQn);

  // PWM Setup - MUST use 16bit version for arbitrary cycle values
  PWMX_CLKCfg(4);
  PWMX_16bit_CycleCfg(PWM_MAX_PERIOD);
  PWMX_16bit_ACTOUT(CH_PWM4, 0, High_Level, DISABLE);
  PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);

  // Forward direction
  GPIOA_SetBits(Left_Phase);
  GPIOA_SetBits(Right_Phase);
}

// Set motor speed using float percent (0.0 to 100.0)
void SetMotorSpeed(int motor, float percent) {
  if (percent > 100.0f)
    percent = 100.0f;
  if (percent < 0.0f)
    percent = 0.0f;

  uint32_t pwm_val = (uint32_t)((PWM_MAX_PERIOD * percent) / 100.0f);

  if (motor == 0) {
    // --- Left Motor (PWM4 on PA12) ---
    // Turn off right motor first
    PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);
    GPIOA_ResetBits(Right_Enable);

    if (percent > 0.0f) {
      PWMX_16bit_ACTOUT(CH_PWM4, pwm_val, High_Level, ENABLE);
    } else {
      PWMX_16bit_ACTOUT(CH_PWM4, 0, High_Level, DISABLE);
      GPIOA_ResetBits(Left_Enable);
    }
  } else {
    // --- Right Motor (PWM5 on PA13) ---
    // Turn off left motor first
    PWMX_16bit_ACTOUT(CH_PWM4, 0, High_Level, DISABLE);
    GPIOA_ResetBits(Left_Enable);

    if (percent > 0.0f) {
      PWMX_16bit_ACTOUT(CH_PWM5, pwm_val, High_Level, ENABLE);
    } else {
      PWMX_16bit_ACTOUT(CH_PWM5, 0, High_Level, DISABLE);
      GPIOA_ResetBits(Right_Enable);
    }
  }
}

// --- Calibration ---

void CalibrateMotors(void) {
  char buf[24];
  OLED_Clear();
  OLED_ShowString(0, 0, "Calibrating...");

  for (int m = 0; m < 2; m++) { // Motor: 0=Left, 1=Right
    for (int s = 0; s < NUM_CAL_POINTS; s++) {
      // Display current test
      if (duty_percents[s] < 1.0f) {
        sprintf(buf, "%s 0.%d%%", (m == 0) ? "L" : "R",
                (int)(duty_percents[s] * 10));
      } else {
        sprintf(buf, "%s %d%%", (m == 0) ? "L" : "R", (int)duty_percents[s]);
      }
      OLED_ShowString(0, 1, buf);

      // 1. Run Motor at test speed
      SetMotorSpeed(m, duty_percents[s]);

      // 2. Settlement delay (500ms)
      DelayMs(500);

      // 3. Reset counters
      if (m == 0)
        count_left = 0;
      else
        count_right = 0;
      timer_ticks = 0;

      // 4. Measure for 1 second (100 ticks @ 10ms)
      while (timer_ticks < 100) {
        DelayMs(1);
      }

      // 5. Capture result
      int32_t counts = (m == 0) ? count_left : count_right;
      if (counts < 0)
        counts = -counts; // Absolute value

      // Calculate speed in m/s
      cal_results[m][s] = (float)counts / TICKS_PER_METER;

      // Stop Motor
      SetMotorSpeed(m, 0);
      DelayMs(200); // Cool down
    }
  }

  // Ensure both motors off
  SetMotorSpeed(0, 0);
  SetMotorSpeed(1, 0);

  // Record max speeds (from 90% test)
  leftmotormaxspeed = cal_results[0][NUM_CAL_POINTS - 1];
  rightmotormaxspeed = cal_results[1][NUM_CAL_POINTS - 1];
  combinedmaxspeed = (leftmotormaxspeed < rightmotormaxspeed)
                         ? leftmotormaxspeed
                         : rightmotormaxspeed;
}

void ShowCalibrationResults(void) {
  char buf[24];

  // Show Left Motor results (first 3)
  OLED_Clear();
  OLED_ShowString(0, 0, "Left Motor:");
  for (int i = 0; i < 3 && i < NUM_CAL_POINTS; i++) {
    if (duty_percents[i] < 1.0f) {
      sprintf(buf, "0.%d%%: %.3fm/s", (int)(duty_percents[i] * 10),
              cal_results[0][i]);
    } else {
      sprintf(buf, "%d%%: %.3fm/s", (int)duty_percents[i], cal_results[0][i]);
    }
    OLED_ShowString(0, i + 1, buf);
  }
  DelayMs(3000);

  // Show Left Motor results (next 3)
  OLED_Clear();
  OLED_ShowString(0, 0, "Left (cont):");
  for (int i = 3; i < NUM_CAL_POINTS; i++) {
    sprintf(buf, "%d%%: %.3fm/s", (int)duty_percents[i], cal_results[0][i]);
    OLED_ShowString(0, i - 2, buf);
  }
  DelayMs(3000);

  // Show Right Motor results (first 3)
  OLED_Clear();
  OLED_ShowString(0, 0, "Right Motor:");
  for (int i = 0; i < 3 && i < NUM_CAL_POINTS; i++) {
    if (duty_percents[i] < 1.0f) {
      sprintf(buf, "0.%d%%: %.3fm/s", (int)(duty_percents[i] * 10),
              cal_results[1][i]);
    } else {
      sprintf(buf, "%d%%: %.3fm/s", (int)duty_percents[i], cal_results[1][i]);
    }
    OLED_ShowString(0, i + 1, buf);
  }
  DelayMs(3000);

  // Show Right Motor results (next 3)
  OLED_Clear();
  OLED_ShowString(0, 0, "Right (cont):");
  for (int i = 3; i < NUM_CAL_POINTS; i++) {
    sprintf(buf, "%d%%: %.3fm/s", (int)duty_percents[i], cal_results[1][i]);
    OLED_ShowString(0, i - 2, buf);
  }
  DelayMs(3000);
}

// --- Run Functions ---

// Set BOTH motors to the same speed (for straight-line driving)
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

// Convert target speed (m/s) to PWM percent using calibration data
// Uses linear interpolation between calibration points
// Uses the SLOWER motor's calibration to ensure both can achieve the speed
float SpeedToPercent(float target_speed_ms) {
  // Clamp to achievable range
  if (target_speed_ms <= 0.0f)
    return 0.0f;
  if (target_speed_ms >= combinedmaxspeed)
    return 90.0f;

  // Find which motor is slower and use that calibration
  // (ensures both motors can achieve the requested speed)
  int motor = (leftmotormaxspeed <= rightmotormaxspeed) ? 0 : 1;

  // Find the two calibration points that bracket the target speed
  for (int i = 0; i < NUM_CAL_POINTS - 1; i++) {
    float speed_low = cal_results[motor][i];
    float speed_high = cal_results[motor][i + 1];

    if (target_speed_ms >= speed_low && target_speed_ms <= speed_high) {
      // Linear interpolation
      float pct_low = duty_percents[i];
      float pct_high = duty_percents[i + 1];
      float ratio = (target_speed_ms - speed_low) / (speed_high - speed_low);
      return pct_low + ratio * (pct_high - pct_low);
    }
  }

  // If below minimum calibrated speed, use lowest percent
  if (target_speed_ms < cal_results[motor][0]) {
    return duty_percents[0] * (target_speed_ms / cal_results[motor][0]);
  }

  // Fallback: use max
  return 90.0f;
}

// Get current distance traveled (average of both encoders) in meters
float GetCurrentDistance(void) {
  int32_t avg_counts = (count_left + count_right) / 2;
  if (avg_counts < 0)
    avg_counts = -avg_counts;
  return (float)avg_counts / TICKS_PER_METER;
}

// Run to target distance, aiming to arrive at target time
// Distance is priority #1, time is priority #2
// "Eases up" to the target by reducing speed as we approach
void RunToTarget(float target_dist_m, float target_time_s) {
  char buf[24];

  // Reset encoders and timer
  count_left = 0;
  count_right = 0;
  timer_ticks = 0;

  // Calculate initial target speed
  float required_speed = target_dist_m / target_time_s;

  // Clamp to achievable speed
  if (required_speed > combinedmaxspeed) {
    required_speed = combinedmaxspeed;
  }

  // Easing parameters - start easing very late for better time accuracy
  float ease_start_dist =
      target_dist_m * 0.95f;           // Start slowing at 95% distance
  float min_speed = cal_results[0][0]; // Minimum speed (from 0.1% cal)

  OLED_Clear();
  OLED_ShowString(0, 0, "Running...");

  while (1) {
    float current_dist = GetCurrentDistance();
    float elapsed_time =
        (float)timer_ticks / 100.0f; // timer_ticks is 10ms each
    float remaining_dist = target_dist_m - current_dist;
    float remaining_time = target_time_s - elapsed_time;

    // Stop if we've reached the target
    if (remaining_dist <= 0.001f) { // Within 1mm
      SetBothMotors(0);
      break;
    }

    // Calculate current target speed
    float current_speed;

    if (current_dist < ease_start_dist) {
      // Full speed phase - continuously adjust based on remaining distance/time
      if (remaining_time > 0.1f) {
        current_speed = remaining_dist / remaining_time;
        // Cap at max achievable, but allow going faster than original
        // required_speed if we're behind schedule
        if (current_speed > combinedmaxspeed) {
          current_speed = combinedmaxspeed;
        }
      } else {
        // Almost out of time, go max speed
        current_speed = combinedmaxspeed;
      }
    } else {
      // Easing phase - reduce speed proportionally to remaining distance
      float ease_progress =
          (current_dist - ease_start_dist) / (target_dist_m - ease_start_dist);
      // Map 0..1 progress to current_speed..min_speed
      // Base the easing off what speed we SHOULD be at, not just required_speed
      float target_end_speed = min_speed;
      current_speed = required_speed * (1.0f - ease_progress) +
                      target_end_speed * ease_progress;
      if (current_speed < min_speed)
        current_speed = min_speed;
    }

    // Convert speed to PWM percent and set motors
    float percent = SpeedToPercent(current_speed);
    SetBothMotors(percent);

    // Update display occasionally (every 500ms)
    if ((timer_ticks % 50) == 0) {
      sprintf(buf, "D:%.2fm T:%.1fs", current_dist, elapsed_time);
      OLED_ShowString(0, 1, buf);
      sprintf(buf, "Spd:%.2f%%", percent);
      OLED_ShowString(0, 2, buf);
    }

    DelayMs(10);
  }

  // Final result
  float final_dist = GetCurrentDistance();
  float final_time = (float)timer_ticks / 100.0f;

  OLED_Clear();
  OLED_ShowString(0, 0, "FINISHED!");
  sprintf(buf, "Dist: %.3fm", final_dist);
  OLED_ShowString(0, 1, buf);
  sprintf(buf, "Time: %.2fs", final_time);
  OLED_ShowString(0, 2, buf);
  sprintf(buf, "Err: %.1fmm", (final_dist - target_dist_m) * 1000.0f);
  OLED_ShowString(0, 3, buf);
}

// --- Main ---

int main(void) {
  SetSysClock(CLK_SOURCE_PLL_60MHz);

  // 10ms Timer for timing
  TMR0_TimerInit(FREQ_SYS / 100);
  TMR0_ClearITFlag(TMR0_3_IT_CYC_END);
  TMR0_ITCfg(ENABLE, TMR0_3_IT_CYC_END);
  PFIC_EnableIRQ(TMR0_IRQn);

  OLED_Init();
  Motor_Init();

  // Run calibration
  CalibrateMotors();

  // Show calibration completed
  OLED_Clear();
  OLED_ShowString(0, 0, "Cal Complete!");
  OLED_ShowString(0, 1, "Starting run...");
  DelayMs(2000);

  // Reset timer for run
  timer_ticks = 0;

  // === SET YOUR TARGET HERE ===
  targetdistance = 5; // meters (integer, will be converted to float)
  targettime = 10;    // seconds (integer, will be converted to float)
  // ============================

  // Run to target
  RunToTarget((float)targetdistance, (float)targettime);

  // Done - stay here showing results
  while (1) {
    DelayMs(1000);
  }
}
