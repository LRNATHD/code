all: base head

base:
	$(MAKE) -f Makefile.inc TARGET=stepper_base

head:
	$(MAKE) -f Makefile.inc TARGET=stepper_head

base_clean:
	$(MAKE) -f Makefile.inc TARGET=stepper_base clean

head_clean:
	$(MAKE) -f Makefile.inc TARGET=stepper_head clean

clean: base_clean head_clean

flash_base:
	$(MAKE) -f Makefile.inc TARGET=stepper_base flash

flash_head:
	$(MAKE) -f Makefile.inc TARGET=stepper_head flash
