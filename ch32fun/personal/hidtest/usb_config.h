#ifndef _USB_CONFIG_H
#define _USB_CONFIG_H

#include "ch32fun.h"
#include "funconfig.h"


#define FUSB_CONFIG_EPS 2 // EP0 + EP1
#define FUSB_EP1_MODE 1   // TX (IN)

#define FUSB_HID_INTERFACES 1
#define FUSB_HID_USER_REPORTS 0 // We use standard descriptor handling
#define FUSB_USER_HANDLERS                                                     \
  0 // No custom handlers needed if we just send reports

#include "usb_defines.h"

#define FUSB_USB_VID 0x1209 // Generic VID (interim)
#define FUSB_USB_PID 0xFFFF // Generic PID
#define FUSB_USB_REV 0x0100

// Device Descriptor
static const uint8_t device_descriptor[] = {
    18,   // bLength
    0x01, // bDescriptorType (Device)
    0x00,
    0x02, // bcdUSB (2.00)
    0x00, // bDeviceClass (Defined in Interface)
    0x00, // bDeviceSubClass
    0x00, // bDeviceProtocol
    64,   // bMaxPacketSize0
    (uint8_t)(FUSB_USB_VID),
    (uint8_t)(FUSB_USB_VID >> 8),
    (uint8_t)(FUSB_USB_PID),
    (uint8_t)(FUSB_USB_PID >> 8),
    (uint8_t)(FUSB_USB_REV),
    (uint8_t)(FUSB_USB_REV >> 8),
    1, // iManufacturer
    2, // iProduct
    0, // iSerialNumber
    1  // bNumConfigurations
};

// HID Report Descriptor (Mouse)
static const uint8_t MyHIDReportDescriptor[] = {
    0x05,
    0x01, // Usage Page (Generic Desktop Ctrls)
    0x09,
    0x02, // Usage (Mouse)
    0xA1,
    0x01, // Collection (Application)
    0x09,
    0x01, //   Usage (Pointer)
    0xA1,
    0x00, //   Collection (Physical)
    0x05,
    0x09, //     Usage Page (Button)
    0x19,
    0x01, //     Usage Minimum (0x01)
    0x29,
    0x03, //     Usage Maximum (0x03)
    0x15,
    0x00, //     Logical Minimum (0)
    0x25,
    0x01, //     Logical Maximum (1)
    0x95,
    0x03, //     Report Count (3)
    0x75,
    0x01, //     Report Size (1)
    0x81,
    0x02, //     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null
          //     Position)
    0x95,
    0x01, //     Report Count (1)
    0x75,
    0x05, //     Report Size (5)
    0x81,
    0x03, //     Input (Const,Var,Abs,No Wrap,Linear,Preferred State,No Null
          //     Position)
    0x05,
    0x01, //     Usage Page (Generic Desktop Ctrls)
    0x09,
    0x30, //     Usage (X)
    0x09,
    0x31, //     Usage (Y)
    0x15,
    0x81, //     Logical Minimum (-127)
    0x25,
    0x7F, //     Logical Maximum (127)
    0x75,
    0x08, //     Report Size (8)
    0x95,
    0x02, //     Report Count (2)
    0x81,
    0x06, //     Input (Data,Var,Rel,No Wrap,Linear,Preferred State,No Null
          //     Position)
    0xC0, //   End Collection
    0xC0  // End Collection
};

// Configuration Descriptor
static const uint8_t config_descriptor[] = {
    9,        // bLength
    0x02,     // bDescriptorType (Configuration)
    34, 0x00, // wTotalLength (9+9+9+7 = 34)
    1,        // bNumInterfaces
    1,        // bConfigurationValue
    0,        // iConfiguration
    0x80,     // bmAttributes (Bus Powered)
    0x32,     // bMaxPower (100mA)

    // Interface Descriptor
    9,    // bLength
    0x04, // bDescriptorType (Interface)
    0,    // bInterfaceNumber
    0,    // bAlternateSetting
    1,    // bNumEndpoints
    0x03, // bInterfaceClass (HID)
    0x01, // bInterfaceSubClass (Boot Interface)
    0x02, // bInterfaceProtocol (Mouse)
    0,    // iInterface

    // HID Descriptor
    9,          // bLength
    0x21,       // bDescriptorType (HID)
    0x11, 0x01, // bcdHID (1.11)
    0,          // bCountryCode
    1,          // bNumDescriptors
    0x22,       // bDescriptorType (Report)
    sizeof(MyHIDReportDescriptor) & 0xFF,
    (sizeof(MyHIDReportDescriptor) >> 8) & 0xFF, // wDescriptorLength

    // Endpoint Descriptor
    7,       // bLength
    0x05,    // bDescriptorType (Endpoint)
    0x81,    // bEndpointAddress (IN, EP1)
    0x03,    // bmAttributes (Interrupt)
    8, 0x00, // wMaxPacketSize
    10       // bInterval (10ms)
};

struct usb_string_descriptor_struct {
  uint8_t bLength;
  uint8_t bDescriptorType;
  uint16_t wString[];
};

const static struct usb_string_descriptor_struct language
    __attribute__((section(".rodata"))) = {4, 3, {0x0409}};

const static struct usb_string_descriptor_struct string1
    __attribute__((section(".rodata"))) = {sizeof(u"WCH") + 2, 3, u"WCH"};

const static struct usb_string_descriptor_struct string2
    __attribute__((section(".rodata"))) = {sizeof(u"CH572 HID Mouse") + 2, 3,
                                           u"CH572 HID Mouse"};

// Descriptor List
const static struct descriptor_list_struct {
  uint32_t lIndexValue;
  const uint8_t *addr;
  uint8_t length;
} descriptor_list[] = {
    {0x00000100, device_descriptor, sizeof(device_descriptor)},
    {0x00000200, config_descriptor, sizeof(config_descriptor)},
    {0x00000300, (const uint8_t *)&language, 4},
    {0x04090301, (const uint8_t *)&string1, sizeof(u"WCH") + 2},
    {0x04090302, (const uint8_t *)&string2, sizeof(u"CH572 HID Mouse") + 2},
    // HID Report Descriptor (Type 0x22, Index 0, Interface 0)
    {0x00002200, MyHIDReportDescriptor, sizeof(MyHIDReportDescriptor)}};

#define DESCRIPTOR_LIST_ENTRIES                                                \
  ((sizeof(descriptor_list)) / (sizeof(struct descriptor_list_struct)))

#endif
