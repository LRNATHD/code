#include "ch32fun.h"
#include "fsusb.h"
#include "iSLER.h"

#define LED PA9
#define USB_DATA_BUF_SIZE 64

__attribute__((
    aligned(4))) static volatile uint8_t gs_usb_data_buf[USB_DATA_BUF_SIZE];

// __HIGH_CODE // Removed HIGH_CODE to avoid potential issues
void blink(int n, int delay) {
  for (int i = 0; i < n; i++) {
    funDigitalWrite(LED, FUN_LOW);
    Delay_Ms(delay);
    funDigitalWrite(LED, FUN_HIGH);
    Delay_Ms(delay);
  }
}

void GPIOSetup() {
  funPinMode(LED, GPIO_CFGLR_OUT_2Mhz_PP);
  funDigitalWrite(LED, FUN_HIGH); // Start OFF (assuming Active Low)
}

int HandleSetupCustom(struct _USBState *ctx, int setup_code) { return 0; }

int HandleInRequest(struct _USBState *ctx, int endp, uint8_t *data, int len) {
  return 0;
}

__HIGH_CODE
void HandleDataOut(struct _USBState *ctx, int endp, uint8_t *data, int len) {
  // this is actually the data rx handler
  if (endp == 0) {
    // this is in the hsusb.c default handler
    ctx->USBFS_SetupReqLen = 0; // To ACK
  } else if (endp == USB_EP_RX) {
    if (len == 4 && ((uint32_t *)data)[0] == 0x010001a2) {
      USBFSReset();
      blink(10, 20); // Fast blink on reset command
      jump_isprom();
    } else if (gs_usb_data_buf[0] == 0) {
      gs_usb_data_buf[0] = len;
      for (int i = 0; i < len; i++) {
        gs_usb_data_buf[i + 1] = data[i];
      }

    } else {
      // Buffer full, drop packet
    }

    ctx->USBFS_Endp_Busy[USB_EP_RX] = 0;
  }
}

int main() {
  SystemInit();
  DCDCEnable(); // Required for RF power

  funGpioInitAll(); // no-op on ch5xx
  GPIOSetup();

  RFCoreInit(LL_TX_POWER_0_DBM);

  USBFSSetup();

  // Distinct startup pattern: 10 fast blinks (20ms)
  // If you see this repeatedly, the board is resetting.
  blink(10, 20);

  while (1) {
    if (gs_usb_data_buf[0]) {
      blink(1, 100); // Shorter blink to minimize delay
      // Send data back to PC.
      while (USBFSCTX.USBFS_Endp_Busy[USB_EP_TX] & 1)
        ;
      USBFS_SendEndpointNEW(
          USB_EP_TX, (uint8_t *)&gs_usb_data_buf[1], gs_usb_data_buf[0],
          /*copy=*/1); // USBFS needs a copy      // RF Transmission Logic
#define ACCESS_ADDRESS 0x12345678

      // Packet: [Magic1, Magic2, Speed, Dir, Enable]
      // USB Data expected: [Speed, Dir, Enable] at buf[1], buf[2], buf[3]
      uint8_t rf_packet[5];
      rf_packet[0] = 0xCA;               // Magic 1
      rf_packet[1] = 0xFE;               // Magic 2
      rf_packet[2] = gs_usb_data_buf[1]; // Speed
      rf_packet[3] = gs_usb_data_buf[2]; // Direction
      rf_packet[4] = gs_usb_data_buf[3]; // Enable

      // Disable Whitening
      BB->CTRL_CFG |= (1 << 6);

      // Burst send 3 packets (reduced from 5)
      for (int i = 0; i < 3; i++) {
        Frame_TX(ACCESS_ADDRESS, rf_packet, sizeof(rf_packet), 37, PHY_1M);
        Delay_Ms(5);
      }

      gs_usb_data_buf[0] = 0;
    }
  }
}
