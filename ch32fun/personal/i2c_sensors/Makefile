all : flash

TARGET:=mini_oled_screen
TARGET_MCU:=CH592
TARGET_MCU_PACKAGE:=CH592X

include ../../ch32fun/ch32fun.mk

flash :
	-$(MAKE) cv_flash
	del *.elf *.hex *.lst *.map *.o *.d

clean : 
	del *.elf *.hex *.lst *.map *.o *.d
