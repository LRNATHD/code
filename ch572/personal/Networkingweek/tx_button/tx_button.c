#include "ch32fun.h"
#include <stdio.h>

// Include iSLER from extralibs
// The makefile should include extralibs path?
// ble_beacon includes "iSLER.h".
// ch32fun.mk adds extralibs to include path usually?
// Let's assume yes.
#include "iSLER.h"

// Define Button Pin (e.g., PA4)
#define BTN_PIN PA1

void setup_button() { funPinMode(BTN_PIN, GPIO_CFGLR_IN_PUPD); }

int main() {
  SystemInit();

  // Power setup similar to ble_beacon for stability
  DCDCEnable();

  setup_button();

  // RF Init
  uint8_t txPower = LL_TX_POWER_0_DBM;
  RFCoreInit(txPower);

  uint8_t magic_packet[] = {0xCA, 0xFE, 0xBA, 0xBE}; // 4 bytes magic

  while (1) {
    // Check Button (High = Pressed)
    if (funDigitalRead(BTN_PIN) == 1) {

      // Send Packet
      // Frame_TX(data, len, channel, phy);
      // Channel 37 (BLE advertising channel)
      Frame_TX(magic_packet, sizeof(magic_packet), 37, PHY_1M);

      // Debounce / Wait
      Delay_Ms(200);

      // Wait for release? Or just repeat if held?
      // "on receiving that input". Simple repeat is fine for now.
    }
  }
}
