################################################################################
# MRS Version: 2.3.0
# Automatically-generated file. Do not edit!
################################################################################
-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include src/subdir.mk
-include StdPeriphDriver/subdir.mk
-include Startup/subdir.mk
-include RVMSIS/subdir.mk
-include subdir.mk
-include objects.mk

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(S_DEPS)),)
-include $(S_DEPS)
endif
ifneq ($(strip $(S_UPPER_DEPS)),)
-include $(S_UPPER_DEPS)
endif
ifneq ($(strip $(ASM_DEPS)),)
-include $(ASM_DEPS)
endif
ifneq ($(strip $(ASM_UPPER_DEPS)),)
-include $(ASM_UPPER_DEPS)
endif
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
endif

-include ../makefile.defs

# Add inputs and outputs from these tool invocations to the build variables 
SECONDARY_FLASH += \
TMR.hex \

SECONDARY_LIST += \
TMR.lst \

SECONDARY_SIZE += \
TMR.siz \


# All Target
all: 
	$(MAKE) --no-print-directory main-build 

main-build: TMR.elf secondary-outputs

# Tool invocations
TMR.elf: $(OBJS) $(USER_OBJS_ESCAPE)
	@	riscv-none-embed-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -g -T "c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/Ld/Link.ld" -nostartfiles -Xlinker --gc-sections -L"c:\Users\LRNA\Downloads\ch592-main\ch592-main\EVT\EXAM\TMR" -L"c:/Users/LRNA/Downloads/ch592-main/ch592-main/EVT/EXAM/SRC/StdPeriphDriver" -Xlinker --print-memory-usage -Wl,-Map,"TMR.map" --specs=nano.specs --specs=nosys.specs -o "TMR.elf" $(OBJS) $(LIBS)
TMR.hex: TMR.elf
	@	riscv-none-embed-objcopy -O ihex "TMR.elf" "TMR.hex"
TMR.lst: TMR.elf
	@	riscv-none-embed-objdump --source --all-headers --demangle --line-numbers --wide "TMR.elf" > "TMR.lst"
TMR.siz: TMR.elf
	riscv-none-embed-size --format=berkeley "TMR.elf"

# Other Targets
clean:
	-$(RM) $(DIR_OBJS) $(SECONDARY_FLASH)$(SECONDARY_LIST)$(SECONDARY_SIZE) TMR.elf
	-$(RM) $(DIR_EXPANDS) $(CALLGRAPH_DOT)
	-$(RM) $(DIR_DEPS)
secondary-outputs: $(SECONDARY_FLASH) $(SECONDARY_LIST) $(SECONDARY_SIZE)

.PHONY: all clean dependents

-include ../makefile.targets