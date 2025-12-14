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

C_SOURCES = \
src/Main.c \
src/spi.c \
src/gc9a01.c \
../../SRC/StdPeriphDriver/CH57x_clk.c \
../../SRC/StdPeriphDriver/CH57x_cmp.c \
../../SRC/StdPeriphDriver/CH57x_flash.c \
../../SRC/StdPeriphDriver/CH57x_gpio.c \
../../SRC/StdPeriphDriver/CH57x_i2c.c \
../../SRC/StdPeriphDriver/CH57x_keyscan.c \
../../SRC/StdPeriphDriver/CH57x_pwm.c \
../../SRC/StdPeriphDriver/CH57x_pwr.c \
../../SRC/StdPeriphDriver/CH57x_spi.c \
../../SRC/StdPeriphDriver/CH57x_sys.c \
../../SRC/StdPeriphDriver/CH57x_timer.c \
../../SRC/StdPeriphDriver/CH57x_uart.c \
../../SRC/StdPeriphDriver/CH57x_usbdev.c \
../../SRC/StdPeriphDriver/CH57x_usbhostBase.c \
../../SRC/StdPeriphDriver/CH57x_usbhostClass.c

# ASM sources
ASM_SOURCES =  \
../../SRC/Startup/startup_CH572.S

######################################
# Binaries
######################################
PREFIX = riscv-none-embed-
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
-I../../SRC/StdPeriphDriver/inc \
-I../../SRC/RVMSIS

# compile gcc flags
ASFLAGS = $(MCU) $(AS_DEFS) $(AS_INCLUDES) $(OPT) -Wall -fdata-sections -ffunction-sections

CFLAGS = $(MCU) $(C_DEFS) $(C_INCLUDES) $(OPT) -Wall -fdata-sections -ffunction-sections

# Generate dependency information
CFLAGS += -MMD -MP -MF"$(@:%.o=%.d)"

######################################
# LDFLAGS
######################################
# link script
LDSCRIPT = ../../SRC/Ld/Link.ld

# libraries
LIBS = -lc -lm -lnosys -lISP572
LIBDIR = -L../../SRC/StdPeriphDriver
LDFLAGS = $(MCU) -nostartfiles -T$(LDSCRIPT) $(LIBDIR) $(LIBS) -Wl,-Map=$(BUILD_DIR)/$(TARGET).map,--cref -Wl,--gc-sections

# default action: build all and flash
all: $(BUILD_DIR)/$(TARGET).elf $(BUILD_DIR)/$(TARGET).hex $(BUILD_DIR)/$(TARGET).bin
	minichlink -w $(BUILD_DIR)/$(TARGET).bin flash -b

# Flash (alias, for explicit use)
flash: all

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

$(BUILD_DIR)/%.o: ../../SRC/StdPeriphDriver/%.c Makefile | $(BUILD_DIR) 
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/$(notdir $(<:.c=.lst)) $< -o $@

$(BUILD_DIR)/%.o: %.S Makefile | $(BUILD_DIR)
	$(AS) -c $(CFLAGS) $< -o $@

$(BUILD_DIR)/%.o: ../../SRC/Startup/%.S Makefile | $(BUILD_DIR)
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


