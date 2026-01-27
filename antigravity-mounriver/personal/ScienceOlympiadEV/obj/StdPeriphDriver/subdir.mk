################################################################################
# MRS Version: 2.3.0
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../StdPeriphDriver/CH59x_adc.c \
../StdPeriphDriver/CH59x_clk.c \
../StdPeriphDriver/CH59x_flash.c \
../StdPeriphDriver/CH59x_gpio.c \
../StdPeriphDriver/CH59x_i2c.c \
../StdPeriphDriver/CH59x_lcd.c \
../StdPeriphDriver/CH59x_pwm.c \
../StdPeriphDriver/CH59x_pwr.c \
../StdPeriphDriver/CH59x_spi0.c \
../StdPeriphDriver/CH59x_sys.c \
../StdPeriphDriver/CH59x_timer0.c \
../StdPeriphDriver/CH59x_timer1.c \
../StdPeriphDriver/CH59x_timer2.c \
../StdPeriphDriver/CH59x_timer3.c \
../StdPeriphDriver/CH59x_uart0.c \
../StdPeriphDriver/CH59x_uart1.c \
../StdPeriphDriver/CH59x_uart2.c \
../StdPeriphDriver/CH59x_uart3.c \
../StdPeriphDriver/CH59x_usbdev.c \
../StdPeriphDriver/CH59x_usbhostBase.c \
../StdPeriphDriver/CH59x_usbhostClass.c 

C_DEPS += \
./StdPeriphDriver/CH59x_adc.d \
./StdPeriphDriver/CH59x_clk.d \
./StdPeriphDriver/CH59x_flash.d \
./StdPeriphDriver/CH59x_gpio.d \
./StdPeriphDriver/CH59x_i2c.d \
./StdPeriphDriver/CH59x_lcd.d \
./StdPeriphDriver/CH59x_pwm.d \
./StdPeriphDriver/CH59x_pwr.d \
./StdPeriphDriver/CH59x_spi0.d \
./StdPeriphDriver/CH59x_sys.d \
./StdPeriphDriver/CH59x_timer0.d \
./StdPeriphDriver/CH59x_timer1.d \
./StdPeriphDriver/CH59x_timer2.d \
./StdPeriphDriver/CH59x_timer3.d \
./StdPeriphDriver/CH59x_uart0.d \
./StdPeriphDriver/CH59x_uart1.d \
./StdPeriphDriver/CH59x_uart2.d \
./StdPeriphDriver/CH59x_uart3.d \
./StdPeriphDriver/CH59x_usbdev.d \
./StdPeriphDriver/CH59x_usbhostBase.d \
./StdPeriphDriver/CH59x_usbhostClass.d 

OBJS += \
./StdPeriphDriver/CH59x_adc.o \
./StdPeriphDriver/CH59x_clk.o \
./StdPeriphDriver/CH59x_flash.o \
./StdPeriphDriver/CH59x_gpio.o \
./StdPeriphDriver/CH59x_i2c.o \
./StdPeriphDriver/CH59x_lcd.o \
./StdPeriphDriver/CH59x_pwm.o \
./StdPeriphDriver/CH59x_pwr.o \
./StdPeriphDriver/CH59x_spi0.o \
./StdPeriphDriver/CH59x_sys.o \
./StdPeriphDriver/CH59x_timer0.o \
./StdPeriphDriver/CH59x_timer1.o \
./StdPeriphDriver/CH59x_timer2.o \
./StdPeriphDriver/CH59x_timer3.o \
./StdPeriphDriver/CH59x_uart0.o \
./StdPeriphDriver/CH59x_uart1.o \
./StdPeriphDriver/CH59x_uart2.o \
./StdPeriphDriver/CH59x_uart3.o \
./StdPeriphDriver/CH59x_usbdev.o \
./StdPeriphDriver/CH59x_usbhostBase.o \
./StdPeriphDriver/CH59x_usbhostClass.o 

DIR_OBJS += \
./StdPeriphDriver/*.o \

DIR_DEPS += \
./StdPeriphDriver/*.d \

DIR_EXPANDS += \
./StdPeriphDriver/*.253r.expand \


# Each subdirectory must supply rules for building sources it contributes
StdPeriphDriver/%.o: ../StdPeriphDriver/%.c
	@	riscv-wch-elf-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -Wunused -Wuninitialized -g -DDEBUG=1 -I"c:/Users/LRNA/Desktop/code/mounriver/ch592/ScienceOlympiadEV/StdPeriphDriver/inc" -I"c:/Users/LRNA/Desktop/code/mounriver/ch592/ScienceOlympiadEV/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"

