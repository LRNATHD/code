#include "ch32fun.h"
#include "iSLER.h"
#include <stdint.h>
#include <stdio.h>

// Motor 1 Pins (Base)
#define M1_AIN1 PA6
#define M1_AIN2 PA7
#define M1_BIN1 PA10
#define M1_BIN2 PA11

// Motor 2 Pins (Head) - PA12/13 Used for HSE
#define M2_AIN1 PA2
#define M2_AIN2 PA3
#define M2_BIN1 PA4
#define M2_BIN2 PA5

typedef struct {
  uint32_t pin_a1;
  uint32_t pin_a2;
  uint32_t pin_b1;
  uint32_t pin_b2;

  int step_phase;
  uint8_t speed;  // 0-255
  uint8_t dir;    // 0 or 1
  uint8_t enable; // 0 or 1

  uint32_t tick_counter;
  uint32_t current_interval_ticks; // Derived from speed
} Stepper;

Stepper motor1 = {M1_AIN1, M1_AIN2, M1_BIN1, M1_BIN2, 0, 0, 0, 0, 0, 0};
Stepper motor2 = {M2_AIN1, M2_AIN2, M2_BIN1, M2_BIN2, 0, 0, 0, 0, 0, 0};

void set_stepper_pins(Stepper *s, int a1, int a2, int b1, int b2) {
  funDigitalWrite(s->pin_a1, a1);
  funDigitalWrite(s->pin_a2, a2);
  funDigitalWrite(s->pin_b1, b1);
  funDigitalWrite(s->pin_b2, b2);
}

void step_sequence(Stepper *s) {
  if (s->dir == 0) {
    s->step_phase++;
    if (s->step_phase > 3)
      s->step_phase = 0;
  } else {
    s->step_phase--;
    if (s->step_phase < 0)
      s->step_phase = 3;
  }

  // Double coil excitation for more torque? Or single? Keeping original
  // single/mixed logic Original Sequence: 0: 1010 1: 0110 2: 0101 3: 1001
  switch (s->step_phase) {
  case 0:
    set_stepper_pins(s, 1, 0, 1, 0);
    break;
  case 1:
    set_stepper_pins(s, 0, 1, 1, 0);
    break;
  case 2:
    set_stepper_pins(s, 0, 1, 0, 1);
    break;
  case 3:
    set_stepper_pins(s, 1, 0, 0, 1);
    break;
  }
}

void run_stepper(Stepper *s) {
  if (!s->enable) {
    set_stepper_pins(s, 0, 0, 0, 0);
    return;
  }

  // Calculate interval. Speed 0-255.
  // Slowest: Speed 1 -> ~20ms. Fastest: Speed 255 -> ~2ms.
  // Ticks are 100us (0.1ms).
  // 20ms = 200 ticks. 2ms = 20 ticks.
  // Formula: 200 - (speed * 180 / 255)
  // Safety clamp

  uint32_t target = 200;
  if (s->speed > 0) {
    target = 200 - ((s->speed * 180) / 255);
  }
  if (target < 20)
    target = 20; // Max speed cap (2ms)

  s->tick_counter++;
  if (s->tick_counter >= target) {
    s->tick_counter = 0;
    step_sequence(s);
  }
}

void setup() {
  SystemInit();
  DCDCEnable();

  // Configure pins
  funPinMode(M1_AIN1, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(M1_AIN2, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(M1_BIN1, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(M1_BIN2, GPIO_CFGLR_OUT_10Mhz_PP);

  funPinMode(M2_AIN1, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(M2_AIN2, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(M2_BIN1, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(M2_BIN2, GPIO_CFGLR_OUT_10Mhz_PP);

  set_stepper_pins(&motor1, 0, 0, 0, 0);
  set_stepper_pins(&motor2, 0, 0, 0, 0);

  RFCoreInit(LL_TX_POWER_0_DBM);
}

#define ACCESS_ADDRESS 0x12345678

int main() {
  setup();

  // Test Wiggle
  motor1.enable = 1;
  motor1.speed = 100;
  motor2.enable = 1;
  motor2.speed = 100;
  for (int i = 0; i < 500; i++) { // Run for a bit
    run_stepper(&motor1);
    run_stepper(&motor2);
    Delay_Us(100);
  }
  motor1.enable = 0;
  motor2.enable = 0;
  set_stepper_pins(&motor1, 0, 0, 0, 0);
  set_stepper_pins(&motor2, 0, 0, 0, 0);

  // Disable Whitening
  BB->CTRL_CFG |= (1 << 6);

  // Start Listening
  Frame_RX(ACCESS_ADDRESS, 37, PHY_1M);

  while (1) {
    // 1. Check Radio
    if (rx_ready) {
      rx_ready = 0;
      volatile uint8_t *pBuf = (volatile uint8_t *)LLE_BUF;

      // Locate Packet
      int found_idx = -1;
      for (int k = 0; k < 32; k++) {
        if (pBuf[k] == 0xCA && pBuf[k + 1] == 0xFE) {
          found_idx = k;
          break;
        }
      }

      if (found_idx != -1) {
        // [S1, D1, E1, S2, D2, E2] at offset +2
        motor1.speed = pBuf[found_idx + 2];
        motor1.dir = pBuf[found_idx + 3];
        motor1.enable = pBuf[found_idx + 4];

        motor2.speed = pBuf[found_idx + 5];
        motor2.dir = pBuf[found_idx + 6];
        motor2.enable = pBuf[found_idx + 7];
      }

      // Re-arm RX
      Frame_RX(ACCESS_ADDRESS, 37, PHY_1M);
    }

    // 2. Run Motors
    run_stepper(&motor1);
    run_stepper(&motor2);

    // 3. Tick Delay
    Delay_Us(100); // 0.1ms tick
  }
}
