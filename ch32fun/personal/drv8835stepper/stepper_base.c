#include "ch32fun.h"
#include "iSLER.h"
#include <stdint.h>
#include <stdio.h>

// Standard Pins for DRV8835 on these boards
#define AIN1 PA6
#define AIN2 PA7
#define BIN1 PA10
#define BIN2 PA11

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
} Stepper;

Stepper motor = {AIN1, AIN2, BIN1, BIN2, 0, 0, 0, 0, 0};

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

  // Speed Range: 30ms (300 ticks) to 2ms (20 ticks)
  // Tick = 100us
  uint32_t target = 300;
  if (s->speed > 0) {
    target = 300 - ((s->speed * 280) / 255);
  }
  if (target < 20)
    target = 20;

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
  funPinMode(AIN1, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(AIN2, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(BIN1, GPIO_CFGLR_OUT_10Mhz_PP);
  funPinMode(BIN2, GPIO_CFGLR_OUT_10Mhz_PP);

  set_stepper_pins(&motor, 0, 0, 0, 0);

  RFCoreInit(LL_TX_POWER_0_DBM);
}

#define ACCESS_ADDRESS 0x12345678

int main() {
  setup();

  // Disable Whitening
  BB->CTRL_CFG |= (1 << 6);

  // Start Listening
  Frame_RX(ACCESS_ADDRESS, 37, PHY_1M);

  while (1) {
    if (rx_ready) {
      rx_ready = 0;
      volatile uint8_t *pBuf = (volatile uint8_t *)LLE_BUF;

      // Packet structure in LLE_BUF:
      // pBuf[0] = Header (BLE-like)
      // pBuf[1] = Length
      // pBuf[2] = Magic1 (0xCA) - start of our payload
      // pBuf[3] = Magic2 (0xFE)
      // pBuf[4] = S1 (speed for base)
      // pBuf[5] = D1 (direction for base)
      // pBuf[6] = E1 (enable for base)
      // pBuf[7] = S2, pBuf[8] = D2, pBuf[9] = E2 (for head)

      if (pBuf[2] == 0xCA && pBuf[3] == 0xFE) {
        motor.speed = pBuf[4];
        motor.dir = pBuf[5];
        motor.enable = pBuf[6];
      }

      Frame_RX(ACCESS_ADDRESS, 37, PHY_1M);
    }

    run_stepper(&motor);
    Delay_Us(100);
  }
}
