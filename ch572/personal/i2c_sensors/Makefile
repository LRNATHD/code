all : flash

TARGET:=mini_oled_screen
TARGET_MCU:=CH572
TARGET_MCU_PACKAGE:=CH572D

include ../../ch32fun/ch32fun.mk

flash :
	-$(MAKE) cv_flash
	del *.bin *.elf *.hex *.lst *.map *.o *.d

clean : 
	del *.bin *.elf *.hex *.lst *.map *.o *.d
