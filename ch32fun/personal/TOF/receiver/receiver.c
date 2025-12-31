#include "../common/radio.h"
#include "ch32fun.h"
#include <stdio.h>
#include <string.h>

#define RX_PAYLOAD_LEN 32
#define RF_CHANNEL 5
#define PROTOCOL_ID 0xAA

uint8_t rx_data[RX_PAYLOAD_LEN];
uint8_t tx_data[RX_PAYLOAD_LEN];

int main() {
  SystemInit();
  printf("TOF Receiver Start\n");

  Radio_Init(0x10);

  while (1) {
    // Shorter timeout to loop more frequently
    int len = Radio_RX(rx_data, RX_PAYLOAD_LEN, RF_CHANNEL, 100);

    if (len > 0) {
      // Check if it's a PING packet with correct ID
      if (rx_data[0] == PROTOCOL_ID &&
          strncmp((char *)&rx_data[1], "PING", 4) == 0) {
        //

        // Reply
        tx_data[0] = PROTOCOL_ID;
        sprintf((char *)&tx_data[1], "PONG");
        Radio_TX(tx_data, 5, RF_CHANNEL);
      }
    }
  }
}
