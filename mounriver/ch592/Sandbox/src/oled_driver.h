#ifndef __OLED_DRIVER_H
#define __OLED_DRIVER_H

#include <stdint.h>
#include "CH59x_common.h"
// -- Hardcoded Pin Definitions --
// Uses GPIOB, Pin 4 (SDA) and Pin 7 (SCL)
#define I2C_SDA_PIN  GPIO_Pin_4
#define I2C_SCL_PIN  GPIO_Pin_7

void OLED_Init(void);
void OLED_Clear(void);
void OLED_ShowChar(uint8_t x, uint8_t y, char chr);
void OLED_ShowString(uint8_t x, uint8_t y, char *str);

#endif