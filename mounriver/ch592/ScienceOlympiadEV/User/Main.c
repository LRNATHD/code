/********************************** (C) COPYRIGHT *******************************
 * File Name          : Main.c
 * Author             : WCH
 * Version            : V1.0
 * Date               : 2020/08/06
 * Description        : 串口1收发演示
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

#include "CH59x_common.h"

#define EN1A GPIOA_Pin_8
#define PH1A GPIO_Pin_6
#define EN1B GPIO_Pin_9
#define PH1B GPIO_Pin_7
#define EN2A GPIO_Pin_13
#define PH2A GPIO_Pin_15
#define EN2B GPIO_Pin_12
#define PH2B GPIO_Pin_14


int main()
{

    SetSysClock(CLK_SOURCE_PLL_60MHz);
    GPIOA_SetBits(EN2B); //basically turn on this pin
    GPIOA_SetBits(PH2B);

    GPIOA_ModeCfg(EN2B, GPIO_ModeOut_PP_5mA);
    GPIOA_ModeCfg(PH2B, GPIO_ModeOut_PP_5mA); 


    while(1) {

    }
}
