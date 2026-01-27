######################################
# Target
######################################
# Change this to your desired output filename
TARGET = firmware

######################################
# Building variables
######################################
# optimization
OPT = -Os

# Build path
BUILD_DIR = obj

######################################
# Source
######################################
# CPP sources
CPP_SOURCES = 

# C sources
C_SOURCES = \
src/Main.c \
../../sdk/ch592/StdPeriphDriver/CH59x_adc.c \
../../sdk/ch592/StdPeriphDriver/CH59x_clk.c \
../../sdk/ch592/StdPeriphDriver/CH59x_flash.c \
../../sdk/ch592/StdPeriphDriver/CH59x_gpio.c \
../../sdk/ch592/StdPeriphDriver/CH59x_i2c.c \
../../sdk/ch592/StdPeriphDriver/CH59x_lcd.c \
../../sdk/ch592/StdPeriphDriver/CH59x_pwm.c \
../../sdk/ch592/StdPeriphDriver/CH59x_pwr.c \
../../sdk/ch592/StdPeriphDriver/CH59x_spi0.c \
../../sdk/ch592/StdPeriphDriver/CH59x_sys.c \
../../sdk/ch592/StdPeriphDriver/CH59x_timer0.c \
../../sdk/ch592/StdPeriphDriver/CH59x_timer1.c \
../../sdk/ch592/StdPeriphDriver/CH59x_timer2.c \
../../sdk/ch592/StdPeriphDriver/CH59x_timer3.c \
../../sdk/ch592/StdPeriphDriver/CH59x_uart0.c \
../../sdk/ch592/StdPeriphDriver/CH59x_uart1.c \
../../sdk/ch592/StdPeriphDriver/CH59x_uart2.c \
../../sdk/ch592/StdPeriphDriver/CH59x_uart3.c \
../../sdk/ch592/StdPeriphDriver/CH59x_usbdev.c \
../../sdk/ch592/StdPeriphDriver/CH59x_usbhostBase.c \
../../sdk/ch592/StdPeriphDriver/CH59x_usbhostClass.c

# ASM sources
ASM_SOURCES =  \
../../sdk/ch592/Startup/startup_CH592.S

######################################
# Binaries
######################################
# GCC Path with spaces escaped or handled
GCC_PATH = "c:/MounRiver/MounRiver_Studio2/resources/app/resources/win32/components/WCH/Toolchain/RISC-V Embedded GCC/bin/"
PREFIX = $(GCC_PATH)riscv-none-embed-
CC = $(PREFIX)gcc
AS = $(PREFIX)gcc -x assembler-with-cpp
CP = $(PREFIX)objcopy
SZ = $(PREFIX)size
HEX = $(CP) -O ihex
BIN = $(CP) -O binary -S

######################################
# CFLAGS
######################################
# cpu
CPU = -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 

# fpu
# NONE for Cortex-M0/M0+/M3

# float-abi

# mcu
MCU = $(CPU) $(FPU) $(FLOAT-ABI)

# macros for gcc
# AS defines
AS_DEFS = 

# C defines
C_DEFS =  \


# AS includes
AS_INCLUDES = 

# C includes
C_INCLUDES =  \
-Isrc \
-I../../sdk/ch592/StdPeriphDriver/inc \
-I../../sdk/ch592/RVMSIS

# compile gcc flags
ASFLAGS = $(MCU) $(AS_DEFS) $(AS_INCLUDES) $(OPT) -Wall -fdata-sections -ffunction-sections

CFLAGS = $(MCU) $(C_DEFS) $(C_INCLUDES) $(OPT) -Wall -fdata-sections -ffunction-sections

# Generate dependency information
CFLAGS += -MMD -MP -MF"$(@:%.o=%.d)"

######################################
# LDFLAGS
######################################
# link script
LDSCRIPT = ../../sdk/ch592/Ld/Link.ld

# libraries
LIBS = -lc -lm -lnosys -lISP592
LIBDIR = -L../../sdk/ch592/StdPeriphDriver
LDFLAGS = $(MCU) -nostartfiles -T$(LDSCRIPT) $(LIBDIR) $(LIBS) -Wl,-Map=$(BUILD_DIR)/$(TARGET).map,--cref -Wl,--gc-sections

# default action: build all and flash
all: $(BUILD_DIR)/$(TARGET).elf $(BUILD_DIR)/$(TARGET).hex $(BUILD_DIR)/$(TARGET).bin flash

# Flash (alias, for explicit use)
flash: $(BUILD_DIR)/$(TARGET).bin
	flash.bat $(BUILD_DIR)/$(TARGET).bin

# Open WCHISPTool GUI (if minichlink fails due to drivers)
WCHISPTOOL = "c:/MounRiver/MounRiver_Studio2/resources/app/resources/win32/components/WCH/Others/WCHISPTool/default/WCHISPTool_CH57x-59x/WCHISPTool_CH57x-59x.exe"
openisp:
	$(WCHISPTOOL)


######################################
# build the application
######################################
# list of objects
OBJECTS = $(addprefix $(BUILD_DIR)/,$(notdir $(C_SOURCES:.c=.o)))
vpath %.c $(sort $(dir $(C_SOURCES)))
# list of ASM program objects
OBJECTS += $(addprefix $(BUILD_DIR)/,$(notdir $(ASM_SOURCES:.S=.o)))
vpath %.S $(sort $(dir $(ASM_SOURCES)))

$(BUILD_DIR)/%.o: %.c Makefile | $(BUILD_DIR) 
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/$(notdir $(<:.c=.lst)) $< -o $@

$(BUILD_DIR)/%.o: src/%.c Makefile | $(BUILD_DIR) 
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/$(notdir $(<:.c=.lst)) $< -o $@

$(BUILD_DIR)/%.o: ../../sdk/ch592/StdPeriphDriver/%.c Makefile | $(BUILD_DIR) 
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/$(notdir $(<:.c=.lst)) $< -o $@

$(BUILD_DIR)/%.o: %.S Makefile | $(BUILD_DIR)
	$(AS) -c $(CFLAGS) $< -o $@

$(BUILD_DIR)/%.o: ../../sdk/ch592/Startup/%.S Makefile | $(BUILD_DIR)
	$(AS) -c $(CFLAGS) $< -o $@

$(BUILD_DIR)/$(TARGET).elf: $(OBJECTS) Makefile
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@
	$(SZ) $@

$(BUILD_DIR)/%.hex: $(BUILD_DIR)/%.elf | $(BUILD_DIR)
	$(HEX) $< $@
	
$(BUILD_DIR)/%.bin: $(BUILD_DIR)/%.elf | $(BUILD_DIR)
	$(BIN) $< $@	
	
$(BUILD_DIR):
	mkdir $@

######################################
# erase
######################################
clean:
	-rm -fR $(BUILD_DIR)
  
######################################
# dependencies
######################################
-include $(wildcard $(BUILD_DIR)/*.d)
