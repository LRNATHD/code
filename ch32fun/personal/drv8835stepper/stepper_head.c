#include "ch32fun.h"
#include "iSLER.h"
#include <stdint.h>
#include <stdio.h>

// Standard Pins for DRV8835 on these boards
#define AIN1 PA6
#define AIN2 PA7
#define BIN1 PA10
#define BIN2 PA11

// Head position limits (±45 degrees)
// Adjust POSITION_LIMIT based on your stepper's steps-per-degree
#define POSITION_LIMIT 75 // ±75 steps = ±45 degrees

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

// Head position tracking (0 = center, positive = down, negative = up)
static int16_t head_position = 0;

void set_stepper_pins(Stepper *s, int a1, int a2, int b1, int b2) {
  funDigitalWrite(s->pin_a1, a1);
  funDigitalWrite(s->pin_a2, a2);
  funDigitalWrite(s->pin_b1, b1);
  funDigitalWrite(s->pin_b2, b2);
}

void step_sequence(Stepper *s) {
  // Update position based on direction BEFORE stepping
  if (s->dir == 0) {
    head_position--; // Up
    s->step_phase++;
    if (s->step_phase > 3)
      s->step_phase = 0;
  } else {
    head_position++; // Down
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
  // When disabled or at limits, just don't advance - but keep coils energized
  // for holding torque
  if (!s->enable) {
    return; // Keep current step energized for holding torque
  }

  // Check position limits
  // dir=0 is up (negative position), dir=1 is down (positive position)
  if (s->dir == 0 && head_position <= -POSITION_LIMIT) {
    // At upper limit, can't go up anymore
    return; // Keep current step energized
  }
  if (s->dir == 1 && head_position >= POSITION_LIMIT) {
    // At lower limit, can't go down anymore
    return; // Keep current step energized
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

  // Head position starts at center (gravity returns it naturally)
  // head_position is already initialized to 0

  // Energize coils in initial position for holding torque
  set_stepper_pins(&motor, 1, 0, 1, 0); // Phase 0

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
      // pBuf[4] = S1, pBuf[5] = D1, pBuf[6] = E1 (for base)
      // pBuf[7] = S2 (speed for head)
      // pBuf[8] = D2 (direction for head)
      // pBuf[9] = E2 (enable for head)

      if (pBuf[2] == 0xCA && pBuf[3] == 0xFE) {
        motor.speed = pBuf[7];
        motor.dir = pBuf[8];
        motor.enable = pBuf[9];
      }

      Frame_RX(ACCESS_ADDRESS, 37, PHY_1M);
    }

    run_stepper(&motor);
    Delay_Us(100);
  }
}
