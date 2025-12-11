#include "ch32fun.h"
#include "iSLER.h"
#include "oled_i2c.h"

int device_state = -1;

// Helper: Print integer to OLED
void ssd1306_print_int(int val) {
  char buf[16];
  if (val == 0) {
    buf[0] = '0';
    buf[1] = 0;
  } else {
    int i = 0;
    int k = val;
    while (k > 0) {
      k /= 10;
      i++;
    }
    buf[i] = 0;
    while (val > 0) {
      buf[--i] = (val % 10) + '0';
      val /= 10;
    }
  }
  ssd1306_print(buf);
}

// Update time display on OLED
void update_time_display(int ms) {
  ssd1306_set_cursor(1, 0);
  ssd1306_print("Time: ");
  ssd1306_print_int(ms);
  ssd1306_print(" ms    ");
}

// State management
void set_device_on() {
  if (device_state == 1)
    return;
  device_state = 1;
  ssd1306_set_cursor(0, 0);
  ssd1306_print("Device: ON      ");
}

void set_device_off() {
  if (device_state == 0)
    return;
  device_state = 0;
  ssd1306_set_cursor(0, 0);
  ssd1306_print("Device: OFF     ");
}

int main() {
  SystemInit();
  DCDCEnable();

  // Init OLED
  i2c_init();
  ssd1306_init();
  ssd1306_clear();

  // Initial state
  set_device_off();
  update_time_display(0);

  // Init RF
  RFCoreInit(LL_TX_POWER_0_DBM);

  int heartbeat_timer_ticks = 100; // ~525ms real-time timeout
  int ticks_since = 0;

  while (1) {
    // Listen on ch37
    Frame_RX(NULL, 37, PHY_1M);

    // Wait for packet
    while (!rx_ready) {
      Delay_Ms(1);
      ticks_since++;

      // Timeout logic
      if (heartbeat_timer_ticks > 0) {
        heartbeat_timer_ticks--;
      } else {
        set_device_off();
      }

      // Update UI every ~50ms real-time (correction applied)
      if (ticks_since % 33 == 0) {
        update_time_display((ticks_since * 3) / 2);
      }
    }

    // Packet received
    if (rx_ready) {
      uint8_t *pBuf = (uint8_t *)LLE_BUF;
      // Check magic bytes
      if (pBuf[2] == 0xCA && pBuf[3] == 0xFE && pBuf[4] == 0xBA &&
          pBuf[5] == 0xBE) {
        heartbeat_timer_ticks = 100;
        ticks_since = 0;
        update_time_display(0);
        set_device_on();
      }
    }
  }
}
