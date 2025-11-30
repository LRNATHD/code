#include "ch32fun.h"
#include <stdio.h>

// Pin definitions
#define TFT_SCL PA4
#define TFT_SDA PA5
#define TFT_RST PA6
#define TFT_DC  PA7
#define TFT_CS  PA2
#define TFT_BL  PA3

void spi_write(uint8_t data) {
    for (uint8_t i = 0; i < 8; i++) {
        if (data & 0x80) funDigitalWrite(TFT_SDA, 1);
        else             funDigitalWrite(TFT_SDA, 0);
        data <<= 1;
        funDigitalWrite(TFT_SCL, 1);
        funDigitalWrite(TFT_SCL, 0);
    }
}

int main()
{
	SystemInit();
	funGpioInitAll(); 

	// Setup GPIO
	funPinMode(TFT_SCL, GPIO_CFGLR_OUT_10Mhz_PP);
	funPinMode(TFT_SDA, GPIO_CFGLR_OUT_10Mhz_PP);
	funPinMode(TFT_DC,  GPIO_CFGLR_OUT_10Mhz_PP);
	funPinMode(TFT_CS,  GPIO_CFGLR_OUT_10Mhz_PP);
	funPinMode(TFT_BL,  GPIO_CFGLR_OUT_10Mhz_PP);
	
	funDigitalWrite(TFT_CS, 1);
	funDigitalWrite(TFT_SCL, 0);
	funDigitalWrite(TFT_BL, 0); // Backlight ON (active-low)
	
	printf("Drawing...\r\n");
	
	// Just draw some pixels without init
	funDigitalWrite(TFT_DC, 1); // Data mode
	funDigitalWrite(TFT_CS, 0); // Select
	
	for(int i = 0; i < 100; i++) {
		spi_write(0xF8); // Red
		spi_write(0x00);
	}
	
	funDigitalWrite(TFT_CS, 1); // Deselect
	printf("Done.\r\n");
	
	while(1) {
		Delay_Ms(1000);
	}
}
