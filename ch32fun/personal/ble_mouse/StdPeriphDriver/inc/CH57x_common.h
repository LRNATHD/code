#ifndef __CH57x_COMM_H__
#define __CH57x_COMM_H__

#ifdef __cplusplus
extern "C" {
#endif

#ifndef NULL
#define NULL 0
#endif
#define ALL 0xFFFF

#ifndef __HIGH_CODE
#define __HIGH_CODE __attribute__((section(".highcode")))
#endif

#ifndef __INTERRUPT
#ifdef INT_SOFT
#define __INTERRUPT __attribute__((interrupt()))
#else
#define __INTERRUPT __attribute__((interrupt("WCH-Interrupt-fast")))
#endif
#endif

#ifdef DEBUG
#include <stdio.h>
#endif

#ifdef DEBUG
#define PRINT(X...) printf(X)
#else
#define PRINT(X...)
#endif

/**
 * @brief  System Frequency (Hz)
 */
#ifndef FREQ_SYS
#define FREQ_SYS 100000000
#endif

#ifndef SAFEOPERATE
#define SAFEOPERATE asm volatile("fence.i")
#endif

#include <stdint.h>
#include <string.h>

/* Define TABLE_IRQN to prevent CH572SFR.h from defining it again */
#ifndef TABLE_IRQN
#define TABLE_IRQN 1
#endif

/* Manual Definition of IRQn to allow core_riscv.h to work reliably */
typedef enum IRQn {
  Reset_IRQn = 0,
  NMI_IRQn = 2,
  EXC_IRQn = 3,
  ECALL_M_IRQn = 5,
  ECALL_U_IRQn = 8,
  BREAKPOINT_IRQn = 9,
  SysTick_IRQn = 12,
  SWI_IRQn = 14,
  GPIO_A_IRQn = 17,
  SPI_IRQn = 19,
  BLEB_IRQn = 20,
  BLEL_IRQn = 21,
  USB_IRQn = 22,
  TMR_IRQn = 24,
  UART_IRQn = 27,
  RTC_IRQn = 28,
  CMP_IRQn = 29,
  I2C_IRQn = 30,
  PWMX_IRQn = 31,
  KEYSCAN_IRQn = 33,
  ENCODE_IRQn = 34,
  WDOG_BAT_IRQn = 35
} IRQn_Type;

/* Include SFR first */
#include <CH572SFR.h>

/* Include core_riscv */
#include "core_riscv.h"

// typedef enum { DISABLE = 0, ENABLE = !DISABLE } FunctionalState;

#include "CH57x_clk.h"
#include "CH57x_cmp.h"
#include "CH57x_flash.h"
#include "CH57x_gpio.h"
#include "CH57x_i2c.h"
#include "CH57x_keyscan.h"
#include "CH57x_pwm.h"
#include "CH57x_pwr.h"
#include "CH57x_spi.h"
#include "CH57x_sys.h"
#include "CH57x_timer.h"
#include "CH57x_uart.h"
#include "CH57x_usbdev.h"
#include "CH57x_usbhost.h"
#include "ISP572.h"

extern uint32_t Freq_LSI;

#define DelayMs(x) mDelaymS(x)
#define DelayUs(x) mDelayuS(x)

#define ROM_CFG_VERISON 0x7F010

#ifdef __cplusplus
}
#endif

#endif // __CH57x_COMM_H__
