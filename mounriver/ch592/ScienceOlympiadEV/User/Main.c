#include "CH59x_common.h"
// pin def, driver, A/B, motor
// Example: Enable pin on driver 1 driving the A line which is also motor 1
#define EN1A1 GPIO_Pin_8
#define PH1A1 GPIO_Pin_6

#define EN1B2 GPIO_Pin_9
#define PH1B2 GPIO_Pin_7

#define EN2A3 GPIO_Pin_13
#define PH2A3 GPIO_Pin_15

#define EN2B4 GPIO_Pin_12
#define PH2B4 GPIO_Pin_14

#define M1ENCA  GPIO_Pin_15 // B
#define M1ENCB  GPIO_Pin_14 // B
#define M2ENCA  GPIO_Pin_13 // B
#define M2ENCB  GPIO_Pin_12 // B

#define M3ENCA  GPIO_Pin_6 // B
#define M3ENCB  GPIO_Pin_0 // B
#define M4ENCA  GPIO_Pin_4 
#define M4ENCB  GPIO_Pin_5 

#define SDA GPIO_Pin_4 // B
#define SCL GPIO_Pin_7 // B

volatile int32_t count_m3 = 0;
volatile int32_t count_m4 = 0;

__INTERRUPT
__HIGH_CODE
void GPIOB_IRQHandler(void)
{
    if(GPIOB_ReadITFlagBit(M3ENCA)) 
    {
        uint8_t a = (GPIOB_ReadPortPin(M3ENCA) != 0);
        uint8_t b = (GPIOB_ReadPortPin(M3ENCB) != 0);

        if (a == b) count_m3++; 
        else        count_m3--;

        if (a) GPIOB_ITModeCfg(M3ENCA, GPIO_ITMode_FallEdge);
        else   GPIOB_ITModeCfg(M3ENCA, GPIO_ITMode_RiseEdge);

        GPIOB_ClearITFlagBit(M3ENCA);
    }

    if(GPIOB_ReadITFlagBit(M4ENCA)) 
    {
        uint8_t a = (GPIOB_ReadPortPin(M4ENCA) != 0);
        uint8_t b = (GPIOB_ReadPortPin(M4ENCB) != 0);

        if (a == b) count_m4++; 
        else        count_m4--;

        if (a) GPIOB_ITModeCfg(M4ENCA, GPIO_ITMode_FallEdge);
        else   GPIOB_ITModeCfg(M4ENCA, GPIO_ITMode_RiseEdge);

        GPIOB_ClearITFlagBit(M4ENCA);
    }
}

int main() {
    SetSysClock(CLK_SOURCE_PLL_60MHz);

    GPIOA_ModeCfg(EN1A1 | PH1A1 | EN1B2 | PH1B2, GPIO_ModeOut_PP_5mA);
    GPIOA_ModeCfg(EN2A3 | PH2A3 | EN2B4 | PH2B4, GPIO_ModeOut_PP_5mA);

    GPIOB_ModeCfg(M3ENCA | M3ENCB | M4ENCA | M4ENCB, GPIO_ModeIN_PU);

    GPIOB_ITModeCfg(M3ENCA, GPIO_ITMode_FallEdge);
    GPIOB_ITModeCfg(M4ENCA, GPIO_ITMode_FallEdge);
    PFIC_EnableIRQ(GPIO_B_IRQn);

    GPIOA_SetBits(PH2A3); 
    GPIOA_SetBits(PH2B4); 
    GPIOA_SetBits(EN2A3); 
    GPIOA_SetBits(EN2B4);

    while(1) {
        if (count_m3 > 5000) {
            GPIOA_ResetBits(EN2A3);
        }
        if (count_m4 > 5000) {
            GPIOA_ResetBits(EN2B4);
        }
        DelayMs(10);
    }
}