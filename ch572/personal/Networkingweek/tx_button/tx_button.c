#include "ch32fun.h"
#include "iSLER.h"
#include <stdio.h>


int main() {
  SystemInit();
  DCDCEnable();

  // Init RF with 0dBm power
  RFCoreInit(LL_TX_POWER_0_DBM);
  uint8_t magic_packet[] = {0xCA, 0xFE, 0xBA, 0xBE};

  while (1) {
    // Transmit heartbeat on ch37
    Frame_TX(magic_packet, sizeof(magic_packet), 37, PHY_1M);

    // ~150ms real-time delay (chip timing correction)
    Delay_Ms(75);
  }
}
