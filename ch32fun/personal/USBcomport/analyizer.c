#include "ch32fun.h"
#include "fsusb.h"
#include "oled_i2c.h"
#include "usb_config.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

// ===================================================================================
// Console Implementation
// ===================================================================================

#define CONSOLE_ROWS 4
#define CONSOLE_COLS 21 // 128 / 6 px = 21.3
char console_buffer[CONSOLE_ROWS][CONSOLE_COLS + 1];
int cursor_row = 0;
int cursor_col = 0;

void console_draw() {
  for (int i = 0; i < CONSOLE_ROWS; i++) {
    ssd1306_set_cursor(i, 0);
    ssd1306_print(console_buffer[i]);
  }
}

void console_init() {
  for (int i = 0; i < CONSOLE_ROWS; i++) {
    memset(console_buffer[i], ' ', CONSOLE_COLS);
    console_buffer[i][CONSOLE_COLS] = 0;
  }
  cursor_row = 0;
  cursor_col = 0;
  ssd1306_clear();
  console_draw();
}

void console_scroll() {
  // Shift lines up
  for (int i = 0; i < CONSOLE_ROWS - 1; i++) {
    strcpy(console_buffer[i], console_buffer[i + 1]);
  }
  // Clear last line
  memset(console_buffer[CONSOLE_ROWS - 1], ' ', CONSOLE_COLS);
  console_buffer[CONSOLE_ROWS - 1][CONSOLE_COLS] = 0;
  cursor_row = CONSOLE_ROWS - 1;
  cursor_col = 0;
}

void console_putc(char c) {
  if (c == '\r')
    return; // Ignore CR, treat LF as newline

  if (c == '\n') {
    if (cursor_row < CONSOLE_ROWS - 1) {
      cursor_row++;
      cursor_col = 0;
    } else {
      console_scroll();
    }
    console_draw(); // Update immediately for responsiveness
    return;
  }

  // Auto-wrap if at end of line
  if (cursor_col >= CONSOLE_COLS) {
    if (cursor_row < CONSOLE_ROWS - 1) {
      cursor_row++;
      cursor_col = 0;
    } else {
      console_scroll();
    }
  }

  console_buffer[cursor_row][cursor_col] = c;
  cursor_col++;

  // Note: optimization, only redraw current line?
  // For now, redraw all to be safe.
  console_draw();
}

void console_puts(const char *s) {
  while (*s)
    console_putc(*s++);
}

// ===================================================================================
// Main
// ===================================================================================

// ===================================================================================
// Ring Buffer for RX
// ===================================================================================

#define RB_SIZE 256
volatile char rb_data[RB_SIZE];
volatile int rb_head = 0;
volatile int rb_tail = 0;

void rb_push(char c) {
  int next = (rb_head + 1) % RB_SIZE;
  if (next != rb_tail) {
    rb_data[rb_head] = c;
    rb_head = next;
  }
}

int rb_pop() {
  if (rb_head == rb_tail)
    return -1;
  char c = rb_data[rb_tail];
  rb_tail = (rb_tail + 1) % RB_SIZE;
  return c;
}

// ===================================================================================
// USB Handlers
// ===================================================================================

// Required because FUSB_USER_HANDLERS = 1 in usb_config.h
void HandleDataOut(struct _USBState *ctx, int endp, uint8_t *data, int len) {
  if (endp == 2) {
    for (int i = 0; i < len; i++) {
      rb_push((char)data[i]);
    }
  }
}

int HandleInRequest(struct _USBState *ctx, int endp, uint8_t *data, int len) {
  return 0; // Pass to default handler
}

int HandleSetupCustom(struct _USBState *ctx, int setup_code) {
  return 0; // Pass to default handler
}

// ===================================================================================
// Main
// ===================================================================================

int main() {
  SystemInit();
  funGpioInitAll();

  // Init OLED
  i2c_init();
  ssd1306_init();
  console_init();

  console_puts("Analyze Ready\n");
  console_puts("Waiting USB...");

  USBFSSetup();

  // Wait for generic USB init
  Delay_Ms(500);
  console_puts("Started.\n");

  while (1) {
    // Poll Ring Buffer
    int c = rb_pop();
    if (c != -1) {
      console_putc((char)c);
    }

    // Optional: Blink to show activity?
    // Can interfere with OLED I2C if not careful (blocking), but simple blink
    // is fine. For now, keep it simple.
  }
}
