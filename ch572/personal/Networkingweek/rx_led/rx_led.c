#include "ch32fun.h"
#include "iSLER.h"
#include "oled_i2c.h"

// Define LED Pin (e.g., PA9 for CH572)
#define LED_PIN PA9

void on_receive_magic_packet() {
  // Turn LED on
  funDigitalWrite(LED_PIN, FUN_LOW);

  // Update OLED to show Pressed
  ssd1306_set_cursor(0, 0);
  ssd1306_print("Button: PRESSED ");

  Delay_Ms(100);

  funDigitalWrite(LED_PIN, FUN_HIGH);

  // Reset OLED to Released
  ssd1306_set_cursor(0, 0);
  ssd1306_print("Button: RELEASED");
}

int main() {
  SystemInit();
  DCDCEnable();

  // Init LED and GPIOs
  funGpioInitAll();
  funPinMode(LED_PIN, GPIO_CFGLR_OUT_2Mhz_PP);
  funDigitalWrite(LED_PIN, FUN_HIGH); // Ensure Off

  // Init OLED
  // oled_i2c.h uses PA5 (SCL) and PA6 (SDA) by default
  i2c_init();
  ssd1306_init();
  ssd1306_clear();

  // Show initial status
  ssd1306_set_cursor(0, 0);
  ssd1306_print("Button: RELEASED");

  // Init RF
  RFCoreInit(LL_TX_POWER_0_DBM);

  while (1) {
    // Start RX
    // Frame_RX sets rx_ready = 0 and enables RX mode
    Frame_RX(NULL, 37, PHY_1M);

    // Wait for packet reception
    while (!rx_ready)
      ;

    // Check for Magic Packet
    // LLE_BUF is the DMA buffer for RF
    uint8_t *pBuf = (uint8_t *)LLE_BUF;

    // pBuf[0] is Header
    // pBuf[1] is Length
    // pBuf[2...] is Payload

    // We look for 0xCA 0xFE 0xBA 0xBE at the start of payload
    if (pBuf[2] == 0xCA && pBuf[3] == 0xFE && pBuf[4] == 0xBA &&
        pBuf[5] == 0xBE) {
      on_receive_magic_packet();
    }

    // Next loop iteration will re-arm RX
  }
}
