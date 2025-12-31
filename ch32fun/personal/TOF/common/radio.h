#ifndef _RADIO_H
#define _RADIO_H

#include "ch32fun.h"

// Wrappers for simplified usage
void Radio_Init(uint8_t txPower);
void Radio_TX(uint8_t *data, uint8_t len, uint8_t channel);
int Radio_RX(uint8_t *data, uint8_t max_len, uint8_t channel,
             uint32_t timeout_ms);

#endif
