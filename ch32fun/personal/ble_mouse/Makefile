################################################################################
# Makefile for CH572 BLE HID Mouse (WCH Standard Library)
################################################################################

# Toolchain
CC = riscv64-unknown-elf-gcc
OBJCOPY = riscv64-unknown-elf-objcopy
SIZE = riscv64-unknown-elf-size

# Project Name
TARGET = ble_mouse

# Directories
APP_DIR = APP
PROFILE_DIR = Profile
HAL_DIR = HAL
STD_PERIPH_DIR = StdPeriphDriver
STARTUP_DIR = Startup
LD_DIR = Ld
LIB_DIR = LIB

# Source Files
C_SOURCES += $(wildcard $(APP_DIR)/*.c)
C_SOURCES += $(wildcard $(PROFILE_DIR)/*.c)
C_SOURCES += $(wildcard $(HAL_DIR)/*.c)
C_SOURCES += $(wildcard $(STD_PERIPH_DIR)/*.c)
# Note: RVMSIS usually has header only core_riscv.h, but check if any .c

ASM_SOURCES = $(STARTUP_DIR)/startup_CH572.S

# Includes
INCLUDES += -I$(APP_DIR)/include
INCLUDES += -I$(PROFILE_DIR)/include
INCLUDES += -I$(HAL_DIR)/include
INCLUDES += -I$(STD_PERIPH_DIR)/inc
INCLUDES += -IRVMSIS
INCLUDES += -I$(LIB_DIR)

# Compiler Flags
CFLAGS += -march=rv32imac -mabi=ilp32
CFLAGS += -Os -g
CFLAGS += -ffunction-sections -fdata-sections
CFLAGS += -DCH572 -DDEBUG
CFLAGS += $(INCLUDES)

# Linker Flags
LDFLAGS += -march=rv32imac -mabi=ilp32
LDFLAGS += -T$(LD_DIR)/Link.ld
LDFLAGS += -Wl,--gc-sections
LDFLAGS += -L$(LIB_DIR) -lCH572BLE_PERI -lISP572
LDFLAGS += -nostartfiles
LDFLAGS += --specs=nano.specs --specs=nosys.specs
# Actually, WCH startup uses "Main_Circulation" and "main" call.

# Build Rules
OBJS = $(C_SOURCES:.c=.o) $(ASM_SOURCES:.S=.o)

all: $(TARGET).bin $(TARGET).hex

$(TARGET).elf: $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o $@
	$(SIZE) $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

$(TARGET).hex: $(TARGET).elf
	$(OBJCOPY) -O ihex $< $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

%.o: %.S
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET).elf $(TARGET).bin $(TARGET).hex $(TARGET).map

flash: $(TARGET).bin
	minichlink -w $(TARGET).bin 0x00000000

.PHONY: all clean flash
