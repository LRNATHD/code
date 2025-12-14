#ifndef LIB_I2C_CH5XX_H
#define LIB_I2C_CH5XX_H

#include "ch32fun.h"
#include <stdio.h>

// User defined pins for Soft I2C
// Hardware I2C on CH572 is typically PB12/13 or PA6/7.
// PA5/PA6 requires bit-banging.
#define I2C_SDA PA6
#define I2C_SCL PA5

// Simple delay for bit-banging
void i2c_delay(void) {
    for(volatile int i = 0; i < 20; i++) { __asm__("nop"); }
}

void i2c_sda_high(void) {
    // Set as Input with Pull-up (External pull-up relied upon usually, but internal helps)
    funPinMode(I2C_SDA, GPIO_CFGLR_IN_PUPD); 
    funDigitalWrite(I2C_SDA, 1); // Ensure pull-up is active if applicable
}

void i2c_sda_low(void) {
    // Set as Output Low
    funPinMode(I2C_SDA, GPIO_CFGLR_OUT_10Mhz_PP);
    funDigitalWrite(I2C_SDA, 0);
}

void i2c_scl_high(void) {
    funDigitalWrite(I2C_SCL, 1);
}

void i2c_scl_low(void) {
    funDigitalWrite(I2C_SCL, 0);
}

u8 i2c_init(u16 i2c_speed_khz) {
    // SCL Output Push-Pull
    funPinMode(I2C_SCL, GPIO_CFGLR_OUT_10Mhz_PP);
    i2c_scl_high();
    
    // SDA Init as High (Input)
    i2c_sda_high();
    
    printf("Soft I2C Init: SDA=PA6, SCL=PA5\r\n");
    return 0;
}

void i2c_start(void) {
    i2c_sda_high();
    i2c_scl_high();
    i2c_delay();
    i2c_sda_low();
    i2c_delay();
    i2c_scl_low();
}

void i2c_stop(void) {
    i2c_sda_low();
    i2c_delay();
    i2c_scl_high();
    i2c_delay();
    i2c_sda_high();
    i2c_delay();
}

u8 i2c_write_byte(u8 byte) {
    for(int i = 0; i < 8; i++) {
        if(byte & 0x80) i2c_sda_high();
        else i2c_sda_low();
        byte <<= 1;
        i2c_delay();
        i2c_scl_high();
        i2c_delay();
        i2c_scl_low();
    }
    
    // ACK Pulse
    i2c_sda_high(); // Release SDA
    i2c_delay();
    i2c_scl_high();
    i2c_delay();
    
    // Sample SDA
    u8 ack = funDigitalRead(I2C_SDA);
    
    i2c_scl_low();
    return ack;
}

u8 i2c_writeData(u8 address, u8 *data, u8 len) {
    i2c_start();
    
    // Send Address + Write(0)
    if(i2c_write_byte(address << 1)) {
        i2c_stop();
        return 1; // NACK
    }
    
    for(u8 i = 0; i < len; i++) {
        if(i2c_write_byte(data[i])) {
            i2c_stop();
            return 2; // NACK
        }
    }
    
    i2c_stop();
    return 0; // Success
}

// Dummy read for now as we only need write for OLED
u8 i2c_readData(u8 address, u8 *data, u8 len) {
    return 0; 
}

#endif