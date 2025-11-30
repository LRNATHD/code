#ifndef ST7789_SPI_H
#define ST7789_SPI_H

#include "ch32fun.h"
#include <stdio.h>

// ===================================================================================
// Pin Definitions (User Config)
// ===================================================================================
#define TFT_SCL PA4
#define TFT_SDA PA5
#define TFT_RST PA6
#define TFT_DC  PA7
#define TFT_CS  PA2
#define TFT_BL  PA3

// ===================================================================================
// Bit-Bang SPI Driver
// ===================================================================================

static void tft_gpio_init(void) {
    // Configure all pins as Push-Pull Output
    funPinMode(TFT_SCL, GPIO_CFGLR_OUT_10Mhz_PP);
    funPinMode(TFT_SDA, GPIO_CFGLR_OUT_10Mhz_PP);
    funPinMode(TFT_RST, GPIO_CFGLR_OUT_10Mhz_PP);
    funPinMode(TFT_DC,  GPIO_CFGLR_OUT_10Mhz_PP);
    funPinMode(TFT_CS,  GPIO_CFGLR_OUT_10Mhz_PP);
    funPinMode(TFT_BL,  GPIO_CFGLR_OUT_10Mhz_PP);

    // Default States
    funDigitalWrite(TFT_CS, 1);  // Deselect
    funDigitalWrite(TFT_SCL, 0); // Idle Low
    funDigitalWrite(TFT_RST, 1); // Reset High (Inactive)
    funDigitalWrite(TFT_BL, 0);  // Backlight On (Active-Low!)
}

static void tft_spi_write(uint8_t data) {
    for (uint8_t i = 0; i < 8; i++) {
        // Set data line (MSB First)
        if (data & 0x80) funDigitalWrite(TFT_SDA, 1);
        else             funDigitalWrite(TFT_SDA, 0);
        
        data <<= 1;
        
        // Clock High (data is sampled on rising edge)
        funDigitalWrite(TFT_SCL, 1);
        __asm__("nop"); // Small delay
        
        // Clock Low
        funDigitalWrite(TFT_SCL, 0);
    }
}

static void tft_cmd(uint8_t cmd) {
    funDigitalWrite(TFT_DC, 0); // Command Mode
    funDigitalWrite(TFT_CS, 0); // Select
    tft_spi_write(cmd);
    funDigitalWrite(TFT_CS, 1); // Deselect
}

static void tft_data(uint8_t data) {
    funDigitalWrite(TFT_DC, 1); // Data Mode
    funDigitalWrite(TFT_CS, 0); // Select
    tft_spi_write(data);
    funDigitalWrite(TFT_CS, 1); // Deselect
}

static void tft_data16(uint16_t data) {
    funDigitalWrite(TFT_DC, 1);
    funDigitalWrite(TFT_CS, 0);
    tft_spi_write(data >> 8);
    tft_spi_write(data & 0xFF);
    funDigitalWrite(TFT_CS, 1);
}

// ===================================================================================
// ST7789 Driver
// ===================================================================================

#define ST7789_WIDTH  240
#define ST7789_HEIGHT 284 // As requested, though usually 240 or 320

static void st7789_reset(void) {
    funDigitalWrite(TFT_RST, 0);
    Delay_Ms(50);
    funDigitalWrite(TFT_RST, 1);
    Delay_Ms(150);
}

static void st7789_init(void) {
    tft_gpio_init();
    st7789_reset();

    tft_cmd(0x11); // Sleep Out
    Delay_Ms(120);

    tft_cmd(0x36); // MADCTL (Memory Access Control)
    tft_data(0x00); // Row/Column order

    tft_cmd(0x3A); // COLMOD (Pixel Format)
    tft_data(0x55); // 16-bit color (RGB565)

    tft_cmd(0xB2); // Porch Setting
    tft_data(0x0C);
    tft_data(0x0C);
    tft_data(0x00);
    tft_data(0x33);
    tft_data(0x33);

    tft_cmd(0xB7); // Gate Control
    tft_data(0x35);

    tft_cmd(0xBB); // VCOMS Setting
    tft_data(0x1F);

    tft_cmd(0xC0); // LCM Control
    tft_data(0x2C);

    tft_cmd(0xC2); // VDV and VRH Command Enable
    tft_data(0x01);

    tft_cmd(0xC3); // VRH Set
    tft_data(0x12);

    tft_cmd(0xC4); // VDV Set
    tft_data(0x20);

    tft_cmd(0xC6); // Frame Rate Control
    tft_data(0x0F);

    tft_cmd(0xD0); // Power Control 1
    tft_data(0xA4);
    tft_data(0xA1);

    tft_cmd(0xE0); // Positive Voltage Gamma Control
    tft_data(0xD0);
    tft_data(0x08);
    tft_data(0x11);
    tft_data(0x08);
    tft_data(0x0C);
    tft_data(0x15);
    tft_data(0x39);
    tft_data(0x33);
    tft_data(0x50);
    tft_data(0x36);
    tft_data(0x13);
    tft_data(0x14);
    tft_data(0x29);
    tft_data(0x2D);

    tft_cmd(0xE1); // Negative Voltage Gamma Control
    tft_data(0xD0);
    tft_data(0x08);
    tft_data(0x10);
    tft_data(0x08);
    tft_data(0x06);
    tft_data(0x06);
    tft_data(0x39);
    tft_data(0x44);
    tft_data(0x51);
    tft_data(0x0B);
    tft_data(0x16);
    tft_data(0x14);
    tft_data(0x2F);
    tft_data(0x31);

    tft_cmd(0x21); // Inversion On
    
    tft_cmd(0x13); // Normal Display Mode On
    Delay_Ms(10);

    tft_cmd(0x29); // Display On
    Delay_Ms(100);
}

static void st7789_set_window(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2) {
    tft_cmd(0x2A); // Column Address Set
    tft_data(x1 >> 8);
    tft_data(x1 & 0xFF);
    tft_data(x2 >> 8);
    tft_data(x2 & 0xFF);

    tft_cmd(0x2B); // Row Address Set
    tft_data(y1 >> 8);
    tft_data(y1 & 0xFF);
    tft_data(y2 >> 8);
    tft_data(y2 & 0xFF);

    tft_cmd(0x2C); // RAM Write
}

static void st7789_fill(uint16_t color) {
    st7789_set_window(0, 0, ST7789_WIDTH - 1, ST7789_HEIGHT - 1);
    
    funDigitalWrite(TFT_DC, 1);
    funDigitalWrite(TFT_CS, 0);
    
    // Optimization: Unroll loop slightly or just blast bytes
    // Since we are bit-banging, function call overhead is negligible compared to GPIO toggle
    for(uint32_t i = 0; i < (uint32_t)ST7789_WIDTH * ST7789_HEIGHT; i++) {
        tft_spi_write(color >> 8);
        tft_spi_write(color & 0xFF);
    }
    
    funDigitalWrite(TFT_CS, 1);
}

#endif
