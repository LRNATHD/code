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

  // Startup indicator: 5 blinks
  blink(5, 50);

#define ACCESS_ADDRESS 0x12345678

  while (1) {
    // Only process and send RF when USB data arrives
    if (gs_usb_data_buf[0]) {
      // Toggle LED on each USB packet received
      static int led_state = 0;
      led_state = !led_state;
      funDigitalWrite(LED, led_state ? FUN_LOW : FUN_HIGH);

      // Send ACK back to PC
      while (USBFSCTX.USBFS_Endp_Busy[USB_EP_TX] & 1)
        ;
      USBFS_SendEndpointNEW(USB_EP_TX, (uint8_t *)&gs_usb_data_buf[1],
                            gs_usb_data_buf[0], 1);

      // Parse USB data (Expect 6 bytes: S1, D1, E1, S2, D2, E2)
      uint8_t s1 = 0, d1 = 0, e1 = 0;
      uint8_t s2 = 0, d2 = 0, e2 = 0;

      if (gs_usb_data_buf[0] >= 6) {
        s1 = gs_usb_data_buf[1];
        d1 = gs_usb_data_buf[2];
        e1 = gs_usb_data_buf[3];
        s2 = gs_usb_data_buf[4];
        d2 = gs_usb_data_buf[5];
        e2 = gs_usb_data_buf[6];
      }
      gs_usb_data_buf[0] = 0;

      // Build RF packet
      uint8_t rf_packet[10];
      rf_packet[0] = 0x00; // Header/PDU type
      rf_packet[1] = 8;    // Payload length: 8 bytes
      rf_packet[2] = 0xCA; // Magic 1
      rf_packet[3] = 0xFE; // Magic 2
      rf_packet[4] = s1;   // Speed 1
      rf_packet[5] = d1;   // Direction 1
      rf_packet[6] = e1;   // Enable 1
      rf_packet[7] = s2;   // Speed 2
      rf_packet[8] = d2;   // Direction 2
      rf_packet[9] = e2;   // Enable 2

      // Send 5 copies for reliability
      for (int i = 0; i < 5; i++) {
        Frame_TX(ACCESS_ADDRESS, rf_packet, sizeof(rf_packet), 37, PHY_1M);
        Delay_Ms(5);
      }
    }
  }
}
