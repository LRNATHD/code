#include "ch32fun.h"
#include "fsusb.h"

int main() {
  SystemInit();
  funGpioInitAll();

  // Enable USB
  USBFSSetup();

  while (1) {
    // Wait for connection? USBFS_DevEnumStatus == 0x01 means Configured.
    if (USBFSCTX.USBFS_DevEnumStatus) {
      if (USBFS_GetEPBufferIfAvailable(1)) {
        uint8_t *buf = USBFS_GetEPBufferIfAvailable(1);
        buf[0] = 0;  // Buttons
        buf[1] = 0;  // X
        buf[2] = -1; // Y (Up)
        USBFS_SendEndpoint(1, 3);

        Delay_Ms(20); // Move slowly
      }
    }
  }
}
