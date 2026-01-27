################################################################################
# MRS Version: 2.3.0
# Automatically-generated file. Do not edit!
################################################################################
-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include User/subdir.mk
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
ScienceOlympiadEV.hex \

SECONDARY_LIST += \
ScienceOlympiadEV.lst \

SECONDARY_SIZE += \
ScienceOlympiadEV.siz \


# All Target
all: 
	$(MAKE) --no-print-directory main-build 

main-build: ScienceOlympiadEV.elf secondary-outputs

# Tool invocations
ScienceOlympiadEV.elf: $(OBJS) $(USER_OBJS_ESCAPE)
	@	riscv-wch-elf-gcc -march=rv32imac -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8 -mno-save-restore -fmax-errors=20 -Os -fmessage-length=0 -fsigned-char -ffunction-sections -fdata-sections -fno-common -Wunused -Wuninitialized -g -T "c:/Users/LRNA/Desktop/code/mounriver/ch592/ScienceOlympiadEV/Ld/Link.ld" -nostartfiles -Xlinker --gc-sections -L"c:\Users\LRNA\Desktop\code\mounriver\ch592\ScienceOlympiadEV" -L"c:/Users/LRNA/Desktop/code/mounriver/ch592/ScienceOlympiadEV/StdPeriphDriver" -Xlinker --print-memory-usage -Wl,-Map,"ScienceOlympiadEV.map" --specs=nano.specs --specs=nosys.specs -o "ScienceOlympiadEV.elf" $(OBJS) $(LIBS)
ScienceOlympiadEV.hex: ScienceOlympiadEV.elf
	@	riscv-wch-elf-objcopy -O ihex "ScienceOlympiadEV.elf" "ScienceOlympiadEV.hex"
ScienceOlympiadEV.lst: ScienceOlympiadEV.elf
	@	riscv-wch-elf-objdump --source --all-headers --demangle --line-numbers --wide "ScienceOlympiadEV.elf" > "ScienceOlympiadEV.lst"
ScienceOlympiadEV.siz: ScienceOlympiadEV.elf
	riscv-wch-elf-size --format=berkeley "ScienceOlympiadEV.elf"

# Other Targets
clean:
	-$(RM) $(DIR_OBJS) $(SECONDARY_FLASH)$(SECONDARY_LIST)$(SECONDARY_SIZE) ScienceOlympiadEV.elf
	-$(RM) $(DIR_EXPANDS) $(CALLGRAPH_DOT)
	-$(RM) $(DIR_DEPS)
secondary-outputs: $(SECONDARY_FLASH) $(SECONDARY_LIST) $(SECONDARY_SIZE)

.PHONY: all clean dependents

-include ../makefile.targets