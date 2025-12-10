# TX Button Project

This project implements a simple RF transmitter using the CH572D.

## Functionality
- Configures PA4 as a button input with internal pull-up.
- When the button is pressed (logic low), it sends a 4-byte magic packet (`0xCA 0xFE 0xBA 0xBE`) via 2.4GHz RF (Channel 37, 1M PHY).
- Debounces for 200ms.

## Hardware
- **MCU**: CH572D
- **Button**: Connected between PA4 and GND. Internal pull-up is enabled.

## Compilation
Run `make` to compile and flash.
