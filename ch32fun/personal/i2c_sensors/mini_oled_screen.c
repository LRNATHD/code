#include "ch32fun.h"
#include "oled_i2c.h"
#include <stdio.h>

int main() {
  SystemInit();
  funGpioInitAll();

  int count = 0;
  char buffer[32];

  // State tracking
  int sda_pressed = 0;
  int scl_pressed = 0;
  int pa4_pressed = 0;
  int needs_update = 1; // Update once at start

  // Initialize PA4 as Input
  funPinMode(PA4, GPIO_CFGLR_IN_PUPD);

  // Initial Init & Clear
  i2c_init();
  ssd1306_init();
  ssd1306_clear();

  // Prepare for loop: Stop I2C and Switch to Input
  i2c_stop();
  funPinMode(PA5, GPIO_CFGLR_IN_PUPD); // SCL
  funPinMode(PA6, GPIO_CFGLR_IN_PUPD); // SDA

  while (1) {
    // Poll Inputs (Normalize to 0 or 1)
    int sda = funDigitalRead(PA6) ? 1 : 0;
    int scl = funDigitalRead(PA5) ? 1 : 0;
    int pa4 = funDigitalRead(PA4) ? 1 : 0;

    // PA6 (SDA) -> +1
    if (sda == 0) {
      sda_pressed = 1;
    } else if (sda == 1 && sda_pressed) {
      Delay_Ms(20); // Debounce
      if (funDigitalRead(PA6)) {
        count += 1;
        sda_pressed = 0;
        needs_update = 1;
      }
    }

    // PA5 (SCL) -> +10
    if (scl == 0) {
      scl_pressed = 1;
    } else if (scl == 1 && scl_pressed) {
      Delay_Ms(20); // Debounce
      if (funDigitalRead(PA5)) {
        count += 10;
        scl_pressed = 0;
        needs_update = 1;
      }
    }

    // PA4 -> +100
    if (pa4 == 0) {
      pa4_pressed = 1;
    } else if (pa4 == 1 && pa4_pressed) {
      Delay_Ms(20); // Debounce
      if (funDigitalRead(PA4)) {
        count += 100;
        pa4_pressed = 0;
        needs_update = 1;
      }
    }

    if (needs_update) {
      // Safety: Ensure I2C bus is free (High) before taking control
      // If a button is held down, we skip the update until it's released
      if ((funDigitalRead(PA5) ? 1 : 0) == 1 &&
          (funDigitalRead(PA6) ? 1 : 0) == 1) {
        // Switch to I2C Output Mode
        i2c_init();

        ssd1306_set_cursor(0, 0);
        sprintf(buffer, "Cnt: %d      ", count);
        ssd1306_print(buffer);

        // Clear second line (remove old debug info)
        ssd1306_set_cursor(1, 0);
        ssd1306_print("                ");

        i2c_stop();

        // Switch back to Input Mode
        funPinMode(PA5, GPIO_CFGLR_IN_PUPD);
        funPinMode(PA6, GPIO_CFGLR_IN_PUPD);

        needs_update = 0;
      }
    }

    Delay_Ms(10);
  }
}
