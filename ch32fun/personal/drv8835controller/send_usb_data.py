#!/usr/bin/env python
import usb.core
import usb.util
import time

CH_USB_VENDOR_ID    = 0x1209
CH_USB_PRODUCT_ID   = 0xd035
CH_USB_EP_OUT       = 0x02

def main():
    print(f"Looking for device 0x{CH_USB_VENDOR_ID:04x}:0x{CH_USB_PRODUCT_ID:04x}...")
    try:
        device = usb.core.find(idVendor=CH_USB_VENDOR_ID, idProduct=CH_USB_PRODUCT_ID)
    except usb.core.NoBackendError:
        print("Error: No USB backend found.")
        print("Please ensure libusb is installed and configured.")
        print("For Windows, you may need to use 'Zadig' to install the 'WinUSB' driver for this device.")
        return

    if device is None:
        print("Device not found. Make sure it is connected and driver is installed.")
        return

    print("Device found!")
    
    # Detach kernel driver if needed
    # Detach kernel driver if needed
    try:
        if device.is_kernel_driver_active(0):
            try:
                device.detach_kernel_driver(0)
            except usb.core.USBError as e:
                print(f"Could not detach kernel driver: {str(e)}")
    except NotImplementedError:
        pass # Not implemented on this OS/Backend (e.g. Windows)

    device.set_configuration()

    print("Sending data to trigger LED blink...")
    
    # Send a few packets
    for i in range(1):
        # Send [Speed=100, Dir=0, Enable=1]
        data = bytearray([100, 0, 1])
        try:
            device.write(CH_USB_EP_OUT, data)
            print(f"Sent packet {i+1}")
            time.sleep(0.5)
        except usb.core.USBError as e:
            print(f"Error sending data: {str(e)}")
            break

    print("Done.")

if __name__ == '__main__':
    main()
