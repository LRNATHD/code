#include "../common/gc9a01.h"
#include "../common/radio.h"
#include "../common/spi.h"
#include "ch32fun.h"
#include <stdio.h>
#include <string.h>

#define TX_PAYLOAD_LEN 32
#define RF_CHANNEL 5
#define PROTOCOL_ID 0xAA

uint8_t tx_data[TX_PAYLOAD_LEN];
uint8_t rx_data[TX_PAYLOAD_LEN];

// Helper to draw centered text
void DrawCentered(const char *msg, uint16_t y, uint16_t color, uint8_t size) {
  size_t len = strlen(msg);
  uint16_t width = len * 6 * size;
  uint16_t x = (240 - width) / 2;
  // Clear the line area (assuming max width for safety in clearing)
  // For a cleaner look, we might simply overwrite background if the font
  // function supported transparent bg, but here we just fill rect.
  GC9A01_FillRect(0, y, 240, 8 * size, BLACK);
  GC9A01_DrawString(x, y, (char *)msg, color, BLACK, size);
}

int main() {
  SystemInit();

  // Init Radio
  Radio_Init(0x10);

  // Init SPI and Screen
  SPI_Init(4);
  GC9A01_Init();
  GC9A01_FillScreen(BLACK);

  DrawCentered("TOF Sender", 40, YELLOW, 2);

  int count = 0;
  char buffer[32];
  uint8_t last_state = 2; // 0=Timeout, 1=Connected, 2=Init

  while (1) {
    // Prepare Packet
    tx_data[0] = PROTOCOL_ID;
    sprintf((char *)&tx_data[1], "PING %d", count++);

    uint32_t t_start = (uint32_t)(SysTick->CNT);

    Radio_TX(tx_data, TX_PAYLOAD_LEN, RF_CHANNEL);

    // Wait for Reply
    int len = Radio_RX(rx_data, TX_PAYLOAD_LEN, RF_CHANNEL, 200);
    uint32_t t_end = (uint32_t)(SysTick->CNT);

    int valid_pkt = 0;
    static uint8_t act_toggle = 0;

    if (len > 0) {
      // Activity Indicator: Toggle a pixel at top to show radio is hearing
      // SOMETHING
      GC9A01_FillRect(118, 20, 4, 4, act_toggle ? CYAN : BLUE);
      act_toggle = !act_toggle;

      if (rx_data[0] == PROTOCOL_ID &&
          strncmp((char *)&rx_data[1], "PONG", 4) == 0) {
        valid_pkt = 1;

        uint32_t diff = t_end - t_start;

        sprintf(buffer, "RTT: %lu", diff);
        DrawCentered(buffer, 100, WHITE, 2);

        sprintf(buffer, "RX: %s", &rx_data[1]);
        DrawCentered(buffer, 130, WHITE, 2);

        // Status Dot Centered Bottom
        GC9A01_FillRect(110, 160, 20, 20, GREEN);

        last_state = 1;
      }
    }

    if (!valid_pkt) {
      if (len > 0) {
        // We received something, but it failed verification. Show it!
        sprintf(buffer, "Bad: %02X %02X %02X", rx_data[0], rx_data[1],
                rx_data[2]);
        DrawCentered(buffer, 100, RED, 2);

        sprintf(buffer, "L:%d ch:%d", len,
                rx_data[0]); // debug length and first byte
        DrawCentered(buffer, 130, RED, 2);

        GC9A01_FillRect(110, 160, 20, 20, RED);
        last_state = 0; // Force update next time
      } else if (last_state != 0) {
        DrawCentered("Timeout", 100, RED, 2);
        // Clear RX line
        GC9A01_FillRect(0, 130, 240, 16, BLACK);

        GC9A01_FillRect(110, 160, 20, 20, RED);
        last_state = 0;
      }
    }

    Delay_Ms(100);
  }
}
