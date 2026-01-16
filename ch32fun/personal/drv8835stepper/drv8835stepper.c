#include "ch32fun.h"
#include "iSLER.h"
#include <stdint.h>
#include <stdio.h>

#define AIN1 PA6
#define AIN2 PA7
#define BIN1 PA10
#define BIN2 PA11

volatile uint8_t motor_enable = 0;
volatile uint8_t motor_dir = 0;
volatile uint8_t motor_speed = 0; // 0-255
volatile int stepperdelay = 20;

void set_stepper_pins(int a1, int a2, int b1, int b2) {
  if (!motor_enable) {
    funDigitalWrite(AIN1, 0);
    funDigitalWrite(AIN2, 0);
    funDigitalWrite(BIN1, 0);
    funDigitalWrite(BIN2, 0);
    return;
  }
  funDigitalWrite(AIN1, a1);
  funDigitalWrite(AIN2, a2);
  funDigitalWrite(BIN1, b1);
  funDigitalWrite(BIN2, b2);
}

// Global Step Index
int step_phase = 0;

void step_sequence(int direction) {
  if (direction == 0) {
    step_phase++;
    if (step_phase > 3)
      step_phase = 0;
  } else {
    step_phase--;
    if (step_phase < 0)
      step_phase = 3;
  }

  switch (step_phase) {
  case 0:
    set_stepper_pins(1, 0, 1, 0);
    break;
  case 1:
    set_stepper_pins(0, 1, 1, 0);
    break;
  case 2:
    set_stepper_pins(0, 1, 0, 1);
    break;
  case 3:
    set_stepper_pins(1, 0, 0, 1);
    break;
  }
}

void setup() {
  SystemInit();
  DCDCEnable();

  // Configure pins as Push-Pull Outputs
  funPinMode(AIN1, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(AIN2, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(BIN1, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(BIN2, GPIO_CFGLR_OUT_10Mhz_PP);

  // Disable initially
  set_stepper_pins(0, 0, 0, 0);

  // Init Radio
  RFCoreInit(LL_TX_POWER_0_DBM);
}

#define ACCESS_ADDRESS 0x12345678

int main() {
  setup();

  // Test Spin on Startup
  Delay_Ms(1000);
  motor_enable = 1;
  for (int i = 0; i < 20; i++) {
    step_sequence(0);
    Delay_Ms(20);
  }
  motor_enable = 0;
  set_stepper_pins(0, 0, 0, 0);

  // Disable Whitening
  BB->CTRL_CFG |= (1 << 6);

  // Start Listening
  Frame_RX(ACCESS_ADDRESS, 37, PHY_1M);

  int state = 0;

  while (1) {
    // 1. Check Radio
    if (rx_ready) {
      rx_ready = 0; // ACK/Clear the flag manually
      volatile uint8_t *pBuf = (volatile uint8_t *)LLE_BUF;

      // Search for Magic Sequence [0xCA, 0xFE] in the first 32 bytes
      int found_idx = -1;
      for (int k = 0; k < 32; k++) {
        if (pBuf[k] == 0xCA && pBuf[k + 1] == 0xFE) {
          found_idx = k;
          break;
        }
      }

      if (found_idx != -1) {
        // Packet found at found_idx
        // Payload: [Magic1(CA), Magic2(FE), Speed, Dir, Enable]
        motor_speed = pBuf[found_idx + 2];
        motor_dir = pBuf[found_idx + 3];
        motor_enable = pBuf[found_idx + 4];

        // Map Speed (0-255) to Delay (20ms - 2ms)
        if (motor_speed == 0)
          stepperdelay = 20;
        else
          stepperdelay = 20 - ((motor_speed * 18) / 255);
        if (stepperdelay < 2)
          stepperdelay = 2;

      } else {
        // Magic not found
      }

      if (!motor_enable) {
        set_stepper_pins(0, 0, 0, 0);
      }

      // Re-arm RX
      Frame_RX(ACCESS_ADDRESS, 37, PHY_1M);
    }

    // Continuous run based on state
    if (motor_enable) {
      step_sequence(motor_dir);
      Delay_Ms(stepperdelay);
    }
  }
}
