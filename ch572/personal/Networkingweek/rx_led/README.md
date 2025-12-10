# RX LED Project

This project implements a simple RF receiver using the CH572D.

## Functionality
- Listens on RF Channel 37 (1M PHY) for packets.
- When a packet containing the magic sequence (`0xCA 0xFE 0xBA 0xBE`) is received, it triggers an action.
- **Action**: Turns on the LED on PA9 for 100ms.

## Hardware
- **MCU**: CH572D
- **LED**: Connected to PA9 (Active Low).

## Compilation
Run `make` to compile and flash.
