#ifndef _GC9A01_H
#define _GC9A01_H

#include "CH57x_common.h"
#include "spi.h"

// Colors (RGB565)
#define WHITE 0xFFFF
#define BLACK 0x0000
#define BLUE 0x001F
#define RED 0xF800
#define MAGENTA 0xF81F
#define GREEN 0x07E0
#define CYAN 0x07FF
#define YELLOW 0xFFE0

void GC9A01_Init(void);
void GC9A01_SetWindow(uint16_t x, uint16_t y, uint16_t w, uint16_t h);
void GC9A01_DrawPixel(uint16_t x, uint16_t y, uint16_t color);
void GC9A01_FillRect(uint16_t x, uint16_t y, uint16_t w, uint16_t h,
                     uint16_t color);
void GC9A01_FillScreen(uint16_t color);
void GC9A01_DrawBitmap(uint16_t x, uint16_t y, uint16_t w, uint16_t h,
                       uint8_t *pData);

#endif
