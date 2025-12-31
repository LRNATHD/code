#define CH570_CH572
#include "radio.h"
#include "../../../extralibs/iSLER.h"
#include <stdio.h>
#include <string.h>

#ifndef FUNCONF_SYSTEM_CORE_CLOCK
#define FUNCONF_SYSTEM_CORE_CLOCK 60000000
#endif

// Globals used by iSLER
// rx_ready is defined in iSLER.h
// LLE_BUF is defined in iSLER.h

void Radio_Init(uint8_t TxPower) { RFCoreInit(TxPower); }

void Radio_TX(uint8_t *data, uint8_t len, uint8_t channel) {
  Frame_TX(data, len, channel, PHY_1M);
}

int Radio_RX(uint8_t *data, uint8_t max_len, uint8_t channel,
             uint32_t timeout_ms) {
  // Mimic the example's frame_info (even if comment says maybe not needed)
  uint8_t frame_info[] = {0xff, 0x10};

  // Start RX
  Frame_RX(frame_info, channel, PHY_1M);

  // Check for packet with timeout
  while (timeout_ms--) {
    if (rx_ready)
      break;
    Delay_Ms(1);
  }

  if (!rx_ready)
    return 0; // Timeout

  // Got a packet!
  rx_ready = 0;

  uint8_t *frame = (uint8_t *)LLE_BUF;

  // frame[0] = RSSI
  // frame[1] = Total PDU Length
  // frame[2] = Header (0x02 added by Frame_TX)
  // frame[3] = Length (added by Frame_TX)
  // frame[4] = Actual Payload (0xAA...)

  int total_len = frame[1];

  // Strip the 2-byte custom header that Frame_TX adds ([0x02] [Len])
  if (total_len > 2) {
    int payload_len = total_len - 2;
    if (payload_len > max_len)
      payload_len = max_len;

    memcpy(data, &frame[4], payload_len);
    data[payload_len] = 0; // Null terminate
    return payload_len;
  }

  return 0;
}
