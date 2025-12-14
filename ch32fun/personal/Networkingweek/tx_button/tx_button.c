#include "ch32fun.h"
#include "iSLER.h"
#include <stdint.h>
#include <stdio.h>

int main() {
  SystemInit();
  DCDCEnable();

  // turn on rf
  RFCoreInit(LL_TX_POWER_0_DBM);
  uint8_t magic_packet[] = {0xCA, 0xFE, 0xBA,
                              0xBE}; // 4 randomly selected, low chance of copied

  while (1) {
    // Transmit heartbeat on channel 37 only to decrease latency
    Frame_TX(magic_packet, sizeof(magic_packet), 37, PHY_1M);

    // ~150ms real-time delay (chip timing is geeked)
    Delay_Ms(75);
  }
}
