#!/usr/bin/env python
"""
Simple USB test script for the DRV8835 controller.
Tests if USB communication works by sending a test packet and reading the echo.
"""
import usb.core
import usb.util

CH_USB_VENDOR_ID    = 0x1209
CH_USB_PRODUCT_ID   = 0xd035
CH_USB_EP_OUT       = 0x02   # OUT endpoint (host -> device)
CH_USB_EP_IN        = 0x81   # IN endpoint (device -> host)
CH_USB_TIMEOUT_MS   = 2000

print("Looking for USB device...")

device = usb.core.find(idVendor=CH_USB_VENDOR_ID, idProduct=CH_USB_PRODUCT_ID)

if device is None:
    print(f"ERROR: Device with VID={hex(CH_USB_VENDOR_ID)} PID={hex(CH_USB_PRODUCT_ID)} not found!")
    print("\nMake sure:")
    print("  1. The controller board is plugged in")
    print("  2. It enumerates as a USB device")
    print("  3. The VID/PID matches (check in Device Manager)")
    exit(1)

print(f"Found device: {device}")
print(f"  Manufacturer: {usb.util.get_string(device, device.iManufacturer)}")
print(f"  Product: {usb.util.get_string(device, device.iProduct)}")
print(f"  Serial: {usb.util.get_string(device, device.iSerialNumber)}")

# Set configuration
try:
    device.set_configuration()
    print("Configuration set successfully")
except Exception as e:
    print(f"Error setting configuration: {e}")

# Test sending data
test_payload = bytearray([100, 0, 1, 100, 0, 1])  # S1=100, D1=0, E1=1, S2=100, D2=0, E2=1
print(f"\nSending test payload: {list(test_payload)}")

try:
    bytes_written = device.write(CH_USB_EP_OUT, test_payload)
    print(f"Successfully wrote {bytes_written} bytes to EP {hex(CH_USB_EP_OUT)}")
except Exception as e:
    print(f"ERROR writing to device: {e}")
    exit(1)

# Try to read echo back
print(f"\nReading from EP {hex(CH_USB_EP_IN)}...")
try:
    response = device.read(CH_USB_EP_IN, 64, CH_USB_TIMEOUT_MS)
    print(f"Received: {list(response)}")
    if list(response) == list(test_payload):
        print("SUCCESS! Echo matches!")
    else:
        print("Warning: Echo doesn't match sent data")
except usb.core.USBTimeoutError:
    print("Timeout waiting for response (this might be OK if device doesn't echo)")
except Exception as e:
    print(f"ERROR reading from device: {e}")

print("\n=== Test Complete ===")
