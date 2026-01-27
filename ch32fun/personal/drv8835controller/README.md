# Antigravity Turret Control

This project controls a 2-axis turret (Base and Head) using two CH572 microcontrollers:
1. **Controller**: USB dongle that sends commands via RF (Radio).
2. **Stepper Receiver**: Receives RF commands and drives 2 stepper motors via DRV8835 or similar drivers.

## Hardware Setup (Stepper Receiver)

### Motor 1 (Base / Left-Right)
- **AIN1**: PA6
- **AIN2**: PA7
- **BIN1**: PA10
- **BIN2**: PA11

### Motor 2 (Head / Up-Down)
- **AIN1**: PA2
- **AIN2**: PA3
- **BIN1**: PA4
- **BIN2**: PA5

*Note: PA12/PA13 are reserved for the HSE Crystal, so Motor 2 uses PA2-PA5.*

## Software

### 1. Controller Firmware (`drv8835controller`)
This firmware runs on the USB dongle. It acts as a bridge, receiving commands from the PC via USB and broadcasting them via RF.

- Build and Flash:
  ```bash
  cd drv8835controller
  make
  # If using WCH-Link:
  # make flash
  # OR use wchisp:
  # wchisp flash drv8835controller.bin
  ```

### 2. Receiver Firmware (`drv8835stepper`)
This folder contains code for both split boards (Base and Head).
Both boards use standard pins:
- **AIN1**: PA6
- **AIN2**: PA7
- **BIN1**: PA10
- **BIN2**: PA11

**Build**:
```bash
make
```
This will generate `stepper_base.bin` and `stepper_head.bin`.

**Flash**:
- To flash the **Base** motor board:
  ```bash
  wchisp flash stepper_base.bin
  ```
- To flash the **Head** motor board:
  ```bash
  wchisp flash stepper_head.bin
  ```

### 3. Web GUI (`turret_server.py`)
A modern, dark-themed web interface to control the turret from your computer.

- **Prerequisites**: Python 3, `pyusb`
  ```bash
  pip install pyusb
  # On Windows, you also need the libusb DLL or driver installed (via Zadig).
  ```
- **Driver Setup (Windows)**:
  - Plug in the USB Dongle.
  - Open Zadig.
  - Select the device `1209:D035`.
  - Install **WinUSB** driver.

- **Run**:
  ```bash
  cd drv8835controller
  python turret_server.py
  ```
- Open **http://localhost:8000** in your web browser.

## Control
- **Arrow Keys**: Move Up/Down/Left/Right.
- **UI Buttons**: Click or Tap to move.
- **Sliders**: Adjust speed for each axis.

## Troubleshooting
- **"Nothing Happens"**:
  1. **Re-flash the Controller**: Ensure you have rebuilt and flashed `drv8835controller` *after* the firmware updates. If you used an old binary, it won't send the 8-byte packet required by the new receivers.
  2. **Check USB**: Does the Controller LED blink when you move the controls in the web UI? If not, check USB connection and Zadig driver.
  3. **Check Power**: Ensure Stepper motors have external power (if needed) or that USB power is sufficient.
  4. **Programmer Error**: If you see `Error: Could not initialize any supported programmers`, make sure your WCH-Link is plugged in and the target chip is in bootloader mode (hold Boot button while plugging in).
