#include "ch32fun.h"
#include <stdio.h>
#include "oled_i2c.h"

int main()
{
	SystemInit();
	funGpioInitAll(); 

	// Initialize Soft I2C
	i2c_init();
	printf("I2C Initialized\r\n");

	// Initialize OLED
	ssd1306_init();
	ssd1306_clear();
	
	ssd1306_set_cursor(0, 0);
	ssd1306_print("OLED TEST");

	// Random Character Generator
	uint32_t seed = 12345;
	
	while(1)
	{
		// Simple LCG Random Number Generator
		seed = seed * 1103515245 + 12345;
		char c = (seed % (126 - 32)) + 32; // Printable ASCII range
		
		ssd1306_write_char(c);
		
		// Optional: Small delay to make it readable, remove for max speed
		Delay_Ms(5); 
	}
}
