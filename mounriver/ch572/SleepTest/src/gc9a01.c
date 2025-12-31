#include "gc9a01.h"
#include "CH57x_common.h"
#include "font.h"

// Private Helper Functions
static void GC9A01_WriteCmd(uint8_t cmd) {
  GPIOA_ResetBits(GPIO_Pin_11); // DC Low
  GPIOA_ResetBits(GPIO_Pin_4);  // CS Low
  SPI_Transfer(cmd);
  // R32_PA_OUT |= (1<<4); // CS High - Optimized
  GPIOA_SetBits(GPIO_Pin_4);
}

static void GC9A01_WriteData(uint8_t data) {
  GPIOA_SetBits(GPIO_Pin_11);  // DC High
  GPIOA_ResetBits(GPIO_Pin_4); // CS Low
  SPI_Transfer(data);
  GPIOA_SetBits(GPIO_Pin_4); // CS High
}

static void GC9A01_WriteDataArray(uint8_t *data, uint16_t len) {
  GPIOA_SetBits(GPIO_Pin_11);  // DC High
  GPIOA_ResetBits(GPIO_Pin_4); // CS Low
  SPI_Send(data, len);
  GPIOA_SetBits(GPIO_Pin_4); // CS High
}

void GC9A01_Init(void) {
  // Initialize Pins
  // CS: PA4, DC: PA11, RST: PA10
  GPIOA_ModeCfg(GPIO_Pin_4, GPIO_ModeOut_PP_20mA);
  GPIOA_ModeCfg(GPIO_Pin_11, GPIO_ModeOut_PP_20mA);
  GPIOA_ModeCfg(GPIO_Pin_10, GPIO_ModeOut_PP_20mA);

  GPIOA_SetBits(GPIO_Pin_4);
  GPIOA_SetBits(GPIO_Pin_11);

  // Reset Sequence
  GPIOA_SetBits(GPIO_Pin_10);
  DelayMs(100);
  GPIOA_ResetBits(GPIO_Pin_10);
  DelayMs(100);
  GPIOA_SetBits(GPIO_Pin_10);
  DelayMs(200);

  // Initialization Commands
  GC9A01_WriteCmd(0xEF);

  GC9A01_WriteCmd(0xEB);
  GC9A01_WriteData(0x14);

  GC9A01_WriteCmd(0xFE);
  GC9A01_WriteCmd(0xEF);

  GC9A01_WriteCmd(0xEB);
  GC9A01_WriteData(0x14);

  GC9A01_WriteCmd(0x84);
  GC9A01_WriteData(0x40);

  GC9A01_WriteCmd(0x85);
  GC9A01_WriteData(0xFF);

  GC9A01_WriteCmd(0x86);
  GC9A01_WriteData(0xFF);

  GC9A01_WriteCmd(0x87);
  GC9A01_WriteData(0xFF);

  GC9A01_WriteCmd(0x88);
  GC9A01_WriteData(0x0A);

  GC9A01_WriteCmd(0x89);
  GC9A01_WriteData(0x21);

  GC9A01_WriteCmd(0x8A);
  GC9A01_WriteData(0x00);

  GC9A01_WriteCmd(0x8B);
  GC9A01_WriteData(0x80);

  GC9A01_WriteCmd(0x8C);
  GC9A01_WriteData(0x01);

  GC9A01_WriteCmd(0x8D);
  GC9A01_WriteData(0x01);

  GC9A01_WriteCmd(0x8E);
  GC9A01_WriteData(0xFF);

  GC9A01_WriteCmd(0x8F);
  GC9A01_WriteData(0xFF);

  GC9A01_WriteCmd(0xB6);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0x20);

  GC9A01_WriteCmd(0x36);
  GC9A01_WriteData(0x08); // Orientation

  GC9A01_WriteCmd(0x3A);
  GC9A01_WriteData(0x05); // 16-bit color

  GC9A01_WriteCmd(0x90);
  GC9A01_WriteData(0x08);
  GC9A01_WriteData(0x08);
  GC9A01_WriteData(0x08);
  GC9A01_WriteData(0x08);

  GC9A01_WriteCmd(0xBD);
  GC9A01_WriteData(0x06);

  GC9A01_WriteCmd(0xBC);
  GC9A01_WriteData(0x00);

  GC9A01_WriteCmd(0xFF);
  GC9A01_WriteData(0x60);
  GC9A01_WriteData(0x01);
  GC9A01_WriteData(0x04);

  GC9A01_WriteCmd(0xC3);
  GC9A01_WriteData(0x13);

  GC9A01_WriteCmd(0xC4);
  GC9A01_WriteData(0x13);

  GC9A01_WriteCmd(0xC9);
  GC9A01_WriteData(0x22);

  GC9A01_WriteCmd(0xBE);
  GC9A01_WriteData(0x11);

  GC9A01_WriteCmd(0xE1);
  GC9A01_WriteData(0x10);
  GC9A01_WriteData(0x0E);

  GC9A01_WriteCmd(0xDF);
  GC9A01_WriteData(0x21);
  GC9A01_WriteData(0x0c);
  GC9A01_WriteData(0x02);

  GC9A01_WriteCmd(0xF0);
  GC9A01_WriteData(0x45);
  GC9A01_WriteData(0x09);
  GC9A01_WriteData(0x08);
  GC9A01_WriteData(0x08);
  GC9A01_WriteData(0x26);
  GC9A01_WriteData(0x2A);

  GC9A01_WriteCmd(0xF1);
  GC9A01_WriteData(0x43);
  GC9A01_WriteData(0x70);
  GC9A01_WriteData(0x72);
  GC9A01_WriteData(0x36);
  GC9A01_WriteData(0x37);
  GC9A01_WriteData(0x6F);

  GC9A01_WriteCmd(0xF2);
  GC9A01_WriteData(0x45);
  GC9A01_WriteData(0x09);
  GC9A01_WriteData(0x08);
  GC9A01_WriteData(0x08);
  GC9A01_WriteData(0x26);
  GC9A01_WriteData(0x2A);

  GC9A01_WriteCmd(0xF3);
  GC9A01_WriteData(0x43);
  GC9A01_WriteData(0x70);
  GC9A01_WriteData(0x72);
  GC9A01_WriteData(0x36);
  GC9A01_WriteData(0x37);
  GC9A01_WriteData(0x6F);

  GC9A01_WriteCmd(0xED);
  GC9A01_WriteData(0x1B);
  GC9A01_WriteData(0x0B);

  GC9A01_WriteCmd(0xAE);
  GC9A01_WriteData(0x77);

  GC9A01_WriteCmd(0xCD);
  GC9A01_WriteData(0x63);

  GC9A01_WriteCmd(0x70);
  GC9A01_WriteData(0x07);
  GC9A01_WriteData(0x07);
  GC9A01_WriteData(0x04);
  GC9A01_WriteData(0x0E);
  GC9A01_WriteData(0x0F);
  GC9A01_WriteData(0x09);
  GC9A01_WriteData(0x07);
  GC9A01_WriteData(0x08);
  GC9A01_WriteData(0x03);

  GC9A01_WriteCmd(0xE8);
  GC9A01_WriteData(0x34);

  GC9A01_WriteCmd(0x62);
  GC9A01_WriteData(0x18);
  GC9A01_WriteData(0x0D);
  GC9A01_WriteData(0x71);
  GC9A01_WriteData(0xED);
  GC9A01_WriteData(0x70);
  GC9A01_WriteData(0x70);
  GC9A01_WriteData(0x18);
  GC9A01_WriteData(0x0F);
  GC9A01_WriteData(0x71);
  GC9A01_WriteData(0xEF);
  GC9A01_WriteData(0x70);
  GC9A01_WriteData(0x70);

  GC9A01_WriteCmd(0x63);
  GC9A01_WriteData(0x18);
  GC9A01_WriteData(0x11);
  GC9A01_WriteData(0x71);
  GC9A01_WriteData(0xF1);
  GC9A01_WriteData(0x70);
  GC9A01_WriteData(0x70);
  GC9A01_WriteData(0x18);
  GC9A01_WriteData(0x13);
  GC9A01_WriteData(0x71);
  GC9A01_WriteData(0xF3);
  GC9A01_WriteData(0x70);
  GC9A01_WriteData(0x70);

  GC9A01_WriteCmd(0x64);
  GC9A01_WriteData(0x28);
  GC9A01_WriteData(0x29);
  GC9A01_WriteData(0xF1);
  GC9A01_WriteData(0x01);
  GC9A01_WriteData(0xF1);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0x07);

  GC9A01_WriteCmd(0x66);
  GC9A01_WriteData(0x3C);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0xCD);
  GC9A01_WriteData(0x67);
  GC9A01_WriteData(0x45);
  GC9A01_WriteData(0x45);
  GC9A01_WriteData(0x10);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0x00);

  GC9A01_WriteCmd(0x67);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0x3C);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0x01);
  GC9A01_WriteData(0x54);
  GC9A01_WriteData(0x10);
  GC9A01_WriteData(0x32);
  GC9A01_WriteData(0x98);

  GC9A01_WriteCmd(0x74);
  GC9A01_WriteData(0x10);
  GC9A01_WriteData(0x85);
  GC9A01_WriteData(0x80);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0x00);
  GC9A01_WriteData(0x4E);
  GC9A01_WriteData(0x00);

  GC9A01_WriteCmd(0x98);
  GC9A01_WriteData(0x3e);
  GC9A01_WriteData(0x07);

  GC9A01_WriteCmd(0x35);
  GC9A01_WriteCmd(0x21); // Inversion invert

  GC9A01_WriteCmd(0x11);
  DelayMs(120);
  GC9A01_WriteCmd(0x29);
  DelayMs(20);
}

void GC9A01_SetWindow(uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
  GC9A01_WriteCmd(0x2A); // Column Address Set
  GC9A01_WriteData(x >> 8);
  GC9A01_WriteData(x & 0xFF);
  GC9A01_WriteData((x + w - 1) >> 8);
  GC9A01_WriteData((x + w - 1) & 0xFF);

  GC9A01_WriteCmd(0x2B); // Row Address Set
  GC9A01_WriteData(y >> 8);
  GC9A01_WriteData(y & 0xFF);
  GC9A01_WriteData((y + h - 1) >> 8);
  GC9A01_WriteData((y + h - 1) & 0xFF);

  GC9A01_WriteCmd(0x2C); // Memory Write
}

void GC9A01_DrawPixel(uint16_t x, uint16_t y, uint16_t color) {
  if (x >= 240 || y >= 240)
    return;
  GC9A01_SetWindow(x, y, 1, 1);

  uint8_t data[2] = {color >> 8, color & 0xFF};
  GC9A01_WriteDataArray(data, 2);
}

void GC9A01_FillRect(uint16_t x, uint16_t y, uint16_t w, uint16_t h,
                     uint16_t color) {
  if ((x >= 240) || (y >= 240))
    return;
  if ((x + w - 1) >= 240)
    w = 240 - x;
  if ((y + h - 1) >= 240)
    h = 240 - y;

  GC9A01_SetWindow(x, y, w, h);

  uint8_t hi = color >> 8;
  uint8_t lo = color & 0xFF;

  GPIOA_SetBits(GPIO_Pin_11);  // DC High
  GPIOA_ResetBits(GPIO_Pin_4); // CS Low

// Optimization: Larger buffer for DMA bursts
#define BUF_SIZE 512
  static uint8_t buffer[BUF_SIZE * 2];

  // Pre-fill buffer once (optimization for solid color fill)
  // This assumes the buffer content is meant to be repeated.
  // Actually, we need to fill it every time because we might change color
  // between calls. But inside the loop, we fill it once if we are filling a
  // large area? Ah, the original code filled it inside the loop? No, it filled
  // it ONCE before the while loop. "for (int k = 0; k < BUF_SIZE; k++) {
  // buffer... }" The logic was roughly: fill buffer with color while count > 0:
  // send chunk.

  // So increasing buf size helps.

  for (int k = 0; k < BUF_SIZE; k++) {
    buffer[k * 2] = hi;
    buffer[k * 2 + 1] = lo;
  }

  uint32_t count = w * h;
  while (count > 0) {
    uint32_t chunk = (count > BUF_SIZE) ? BUF_SIZE : count;
    SPI_Send(buffer, chunk * 2);
    count -= chunk;
  }

  GPIOA_SetBits(GPIO_Pin_4); // CS High
}

void GC9A01_FillScreen(uint16_t color) {
  GC9A01_FillRect(0, 0, 240, 240, color);
}

void GC9A01_DrawBitmap(uint16_t x, uint16_t y, uint16_t w, uint16_t h,
                       uint8_t *pData) {
  // Set Window
  GC9A01_SetWindow(x, y, w, h);

  // Write Data
  GPIOA_SetBits(GPIO_Pin_11);  // DC High
  GPIOA_ResetBits(GPIO_Pin_4); // CS Low

  // Send the entire buffer via DMA
  // Size in bytes = w * h * 2
  // Note: SPI_Send takes length in bytes.
  SPI_Send(pData, w * h * 2);

  // Wait for SPI to be free (Tx/Rx FIFO empty and engine idle)
  // RB_SPI_FREE is 0x40. If it is 0, SPI is busy.
  while ((R8_SPI_INT_FLAG & RB_SPI_FREE) == 0)
    ;

  GPIOA_SetBits(GPIO_Pin_4); // CS High
}

void GC9A01_DrawChar(uint16_t x, uint16_t y, char c, uint16_t color,
                     uint16_t bg, uint8_t size) {
  if ((x >= 240) || (y >= 240))
    return;
  if (c < 32 || c > 126)
    c = 32; // Limit to ASCII

  // Get index in flat font array
  // Each char is 5 bytes
  int idx = (c - 32) * 5;

  // Draw 5x7
  for (int col = 0; col < 5; col++) {
    uint8_t line = Font5x7[idx + col];
    for (int row = 0; row < 7; row++) {
      uint16_t pixelColor = (line & 0x01) ? color : bg;
      line >>= 1;

      if (size == 1) {
        GC9A01_DrawPixel(x + col, y + row, pixelColor);
      } else {
        GC9A01_FillRect(x + col * size, y + row * size, size, size, pixelColor);
      }
    }
  }
}

void GC9A01_DrawString(uint16_t x, uint16_t y, const char *str, uint16_t color,
                       uint16_t bg, uint8_t size) {
  while (*str) {
    if (x + 5 * size >= 240) { // Wrap
      x = 0;
      y += 8 * size;
    }
    GC9A01_DrawChar(x, y, *str, color, bg, size);
    x += 6 * size;
    str++;
  }
}

void GC9A01_Sleep(void) {
  GC9A01_WriteCmd(0x28); // Display OFF
  GC9A01_WriteCmd(0x10); // Sleep In
  DelayMs(120);
}
