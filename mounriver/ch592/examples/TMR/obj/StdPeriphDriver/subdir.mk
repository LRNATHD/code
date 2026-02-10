################################################################################
# MRS Version: 2.3.0
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_clk.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_flash.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_gpio.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_i2c.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_lcd.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_pwr.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_sys.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_timer0.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_timer1.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_timer2.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_timer3.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_uart0.c \
c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_uart1.c 

C_DEPS += \
./StdPeriphDriver/CH59x_clk.d \
./StdPeriphDriver/CH59x_flash.d \
./StdPeriphDriver/CH59x_gpio.d \
./StdPeriphDriver/CH59x_i2c.d \
./StdPeriphDriver/CH59x_lcd.d \
./StdPeriphDriver/CH59x_pwr.d \
./StdPeriphDriver/CH59x_sys.d \
./StdPeriphDriver/CH59x_timer0.d \
./StdPeriphDriver/CH59x_timer1.d \
./StdPeriphDriver/CH59x_timer2.d \
./StdPeriphDriver/CH59x_timer3.d \
./StdPeriphDriver/CH59x_uart0.d \
./StdPeriphDriver/CH59x_uart1.d 

OBJS += \
./StdPeriphDriver/CH59x_clk.o \
./StdPeriphDriver/CH59x_flash.o \
./StdPeriphDriver/CH59x_gpio.o \
./StdPeriphDriver/CH59x_i2c.o \
./StdPeriphDriver/CH59x_lcd.o \
./StdPeriphDriver/CH59x_pwr.o \
./StdPeriphDriver/CH59x_sys.o \
./StdPeriphDriver/CH59x_timer0.o \
./StdPeriphDriver/CH59x_timer1.o \
./StdPeriphDriver/CH59x_timer2.o \
./StdPeriphDriver/CH59x_timer3.o \
./StdPeriphDriver/CH59x_uart0.o \
./StdPeriphDriver/CH59x_uart1.o 

DIR_OBJS += \
./StdPeriphDriver/*.o \

DIR_DEPS += \
./StdPeriphDriver/*.d \

DIR_EXPANDS += \
./StdPeriphDriver/*.234r.expand \


# Each subdirectory must supply rules for building sources it contributes
StdPeriphDriver/CH59x_clk.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_clk.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_flash.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_flash.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_gpio.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_gpio.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_i2c.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_i2c.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_lcd.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_lcd.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_pwr.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_pwr.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_sys.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_sys.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_timer0.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_timer0.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_timer1.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_timer1.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_timer2.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_timer2.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_timer3.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_timer3.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_uart0.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_uart0.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"
StdPeriphDriver/CH59x_uart1.o: c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/CH59x_uart1.c
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -DDEBUG=1 -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver/inc" -I"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"

