all : build

TARGET_MCU:=CH572
TARGET_MCU_PACKAGE:=CH572D

EXTRA_CFLAGS:=-I../../extralibs
MINICHLINK:=../../../antigravity-mounriver/tools

include ../../ch32fun/ch32fun.mk

build : $(TARGET).bin
clean : cv_clean
flash : cv_flash
