######################################
# Target
######################################
TARGET = firmware

######################################
# Building variables
######################################
OPT = -Os

# Build path
BUILD_DIR = ../obj/Template

######################################
# Source
######################################
# C sources
C_SOURCES = \
src/main.c \
../SRC/StdPeriphDriver/CH59x_clk.c \
../SRC/StdPeriphDriver/CH59x_flash.c \
../SRC/StdPeriphDriver/CH59x_gpio.c \
../SRC/StdPeriphDriver/CH59x_i2c.c \
../SRC/StdPeriphDriver/CH59x_pwm.c \
../SRC/StdPeriphDriver/CH59x_pwr.c \
../SRC/StdPeriphDriver/CH59x_sys.c \
../SRC/StdPeriphDriver/CH59x_timer0.c \
../SRC/StdPeriphDriver/CH59x_timer1.c \
../SRC/StdPeriphDriver/CH59x_timer2.c \
../SRC/StdPeriphDriver/CH59x_timer3.c \
../SRC/StdPeriphDriver/CH59x_adc.c \
../SRC/StdPeriphDriver/CH59x_spi0.c \
../SRC/StdPeriphDriver/CH59x_uart0.c \
../SRC/StdPeriphDriver/CH59x_uart1.c \
../SRC/StdPeriphDriver/CH59x_uart2.c \
../SRC/StdPeriphDriver/CH59x_uart3.c \
../SRC/StdPeriphDriver/CH59x_usbdev.c \
../SRC/StdPeriphDriver/CH59x_usbhostBase.c \
../SRC/StdPeriphDriver/CH59x_usbhostClass.c \
../SRC/StdPeriphDriver/CH59x_lcd.c

# ASM sources
ASM_SOURCES = \
../SRC/Startup/startup_CH592.S

######################################
# Binaries
######################################
PREFIX = riscv-wch-elf-
CC = $(PREFIX)gcc
AS = $(PREFIX)gcc -x assembler-with-cpp
CP = $(PREFIX)objcopy
SZ = $(PREFIX)size
HEX = $(CP) -O ihex
BIN = $(CP) -O binary -S

######################################
# CFLAGS
######################################
CPU = -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8

MCU = $(CPU)

AS_DEFS =

C_DEFS = \
-DDEBUG=1

AS_INCLUDES =

C_INCLUDES = \
-Isrc \
-I../SRC/StdPeriphDriver/inc \
-I../SRC/RVMSIS

ASFLAGS = $(MCU) $(AS_DEFS) $(AS_INCLUDES) $(OPT) -Wall -fdata-sections -ffunction-sections
CFLAGS = $(MCU) $(C_DEFS) $(C_INCLUDES) $(OPT) -Wall -fdata-sections -ffunction-sections -fno-common -fsigned-char -std=gnu99
CFLAGS += -MMD -MP -MF"$(@:%.o=%.d)"

######################################
# LDFLAGS
######################################
LDSCRIPT = ../SRC/Ld/Link.ld

LIBS = -lc -lm -lnosys -lISP592
LIBDIR = -L../SRC/StdPeriphDriver
LDFLAGS = $(MCU) -mno-save-restore -fmax-errors=20 -nostartfiles -T$(LDSCRIPT) $(LIBDIR) $(LIBS) -Wl,-Map=$(BUILD_DIR)/$(TARGET).map,--cref -Wl,--gc-sections -Wl,--print-memory-usage --specs=nano.specs --specs=nosys.specs

######################################
# Build
######################################
all: $(BUILD_DIR)/$(TARGET).elf $(BUILD_DIR)/$(TARGET).hex $(BUILD_DIR)/$(TARGET).bin
	@copy "$(subst /,\,$(BUILD_DIR)/$(TARGET).bin)" "$(TARGET).bin" >nul 2>&1
	@echo "Build complete. $(TARGET).bin copied to project root."

# list of objects
OBJECTS = $(addprefix $(BUILD_DIR)/,$(notdir $(C_SOURCES:.c=.o)))
vpath %.c $(sort $(dir $(C_SOURCES)))
OBJECTS += $(addprefix $(BUILD_DIR)/,$(notdir $(ASM_SOURCES:.S=.o)))
vpath %.S $(sort $(dir $(ASM_SOURCES)))

$(BUILD_DIR)/%.o: %.c Makefile | $(BUILD_DIR)
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/$(notdir $(<:.c=.lst)) $< -o $@

$(BUILD_DIR)/%.o: src/%.c Makefile | $(BUILD_DIR)
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/$(notdir $(<:.c=.lst)) $< -o $@

$(BUILD_DIR)/%.o: ../SRC/StdPeriphDriver/%.c Makefile | $(BUILD_DIR)
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-alms=$(BUILD_DIR)/$(notdir $(<:.c=.lst)) $< -o $@

$(BUILD_DIR)/%.o: %.S Makefile | $(BUILD_DIR)
	$(AS) -c $(CFLAGS) $< -o $@

$(BUILD_DIR)/%.o: ../SRC/Startup/%.S Makefile | $(BUILD_DIR)
	$(AS) -c $(CFLAGS) $< -o $@


$(BUILD_DIR)/$(TARGET).elf: $(OBJECTS) Makefile
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@
	$(SZ) $@

$(BUILD_DIR)/%.hex: $(BUILD_DIR)/%.elf | $(BUILD_DIR)
	$(HEX) $< $@

$(BUILD_DIR)/%.bin: $(BUILD_DIR)/%.elf | $(BUILD_DIR)
	$(BIN) $< $@

$(BUILD_DIR):
	@if not exist "$(subst /,\,$@)" cmd /c "mkdir $(subst /,\,$@)"

######################################
# Flash tool
######################################
MINICHLINK = ../../tools/minichlink

######################################
# Clean
######################################
clean:
	-rm -fR $(BUILD_DIR)
	-del /Q $(TARGET).bin 2>nul

######################################
# Flash
######################################
flash: all
	$(MINICHLINK) -w $(TARGET).bin flash -b

unbrick:
	@echo "Hold BOOT button while plugging in USB, then run this."
	$(MINICHLINK) -E

enable_swd:
	@echo "Hold BOOT button while plugging in USB, then run this."
	$(MINICHLINK) -N

-include $(wildcard $(BUILD_DIR)/*.d)
