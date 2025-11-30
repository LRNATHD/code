#include "ch32fun.h"
#include <stdio.h>
#include "st7789_spi.h"

int main()
{
	SystemInit();
	funGpioInitAll(); 

	printf("Initializing ST7789...\r\n");
	st7789_init();
	printf("Done.\r\n");

	// Colors (RGB565)
	// Red: 0xF800, Green: 0x07E0, Blue: 0x001F
	
	while(1)
	{
		printf("Red\r\n");
		st7789_fill(0xF800);
		Delay_Ms(1000);
		
		printf("Green\r\n");
		st7789_fill(0x07E0);
		Delay_Ms(1000);
		
		printf("Blue\r\n");
		st7789_fill(0x001F);
		Delay_Ms(1000);
	}
}
