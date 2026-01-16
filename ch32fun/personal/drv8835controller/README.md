# DRV8835 Controller for CH572

This project is a USB controller for the DRV8835 stepper driver, running on a CH572 microcontroller.

## Project Structure
- `drv8835controller.c`: Main firmware source code.
- `send_usb_data.py`: Python host script to test the connection.
- `Makefile`: Build configuration.
- `usb_config.h`: USB descriptor and configuration.
- `funconfig.h`: System clock and ch32fun configuration.

## How to Build and Flash
1. **Compile**:
   ```bash
   make
   ```
   This will generate `drv8835controller.bin`.

2. **Flash**:
   Use `wchisp` or `WCH-LinkUtility` to flash the binary to your CH572 device.

   Example with wchisp:
   ```bash
   wchisp flash drv8835controller.bin
   ```

3. **Flash Stepper Receiver**:
   Navigate to `../drv8835stepper` and run `make`.
   Flash `drv8835stepper.bin` to your second CH572 device connected to the DRV8835.
   
   Ensure the Stepper pins are:
   - AIN1: PA6
   - AIN2: PA7
   - BIN1: PA10
   - BIN2: PA11

## USB Driver Setup
The device uses a testing VID/PID combination: `0x1209:0xd035`.
To communicate with it on Windows using Python/libusb, you must install the **WinUSB** driver.

1. Download **Zadig** from [https://zadig.akeo.ie/](https://zadig.akeo.ie/) and run it.
2. In Zadig, select **Options** -> **List All Devices**.
3. Select "Bulk demo" (or the device with ID `1209:D035`) from the dropdown.
4. Select **WinUSB** as the target driver.
5. Click **Replace Driver** (or Install Driver).

## Testing
1. Power up the **Stepper Receiver** (drv8835stepper).
2. Plug in the **USB Controller** (drv8835controller).
3. Run the python script:
   ```bash
   python send_usb_data.py
   ```
4. The USB Controller LED should blink.
5. The Stepper Motor should spin for approx 0.5 seconds.
