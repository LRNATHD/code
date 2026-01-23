################################################################################
# MRS Version: 2.3.0
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../User/Sandbox.c \
../User/oled_driver.c 

C_DEPS += \
./User/Sandbox.d \
./User/oled_driver.d 

OBJS += \
./User/Sandbox.o \
./User/oled_driver.o 

DIR_OBJS += \
./User/*.o \

DIR_DEPS += \
./User/*.d \

DIR_EXPANDS += \
./User/*.253r.expand \


# Each subdirectory must supply rules for building sources it contributes
User/%.o: ../User/%.c
	@	riscv-wch-elf-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -Wunused -Wuninitialized -g -DDEBUG=1 -I"c:/Users/Noahs/Desktop/code/mounriver/ch592/ScienceOlympiadEV/StdPeriphDriver/inc" -I"c:/Users/Noahs/Desktop/code/mounriver/ch592/ScienceOlympiadEV/RVMSIS" -std=gnu99 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -c -o "$@" "$<"

