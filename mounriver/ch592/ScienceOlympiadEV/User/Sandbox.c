

#include "CH59x_common.h"
#include "oled_driver.h"



__INTERRUPT
__HIGH_CODE
void TMR0_IRQHandler(void)
{
    if(TMR0_GetITFlag(TMR0_3_IT_CYC_END))
    {
        TMR0_ClearITFlag(TMR0_3_IT_CYC_END);
        OLED_ShowString(0,2, "Timer");
    }
}

int main() {
    SetSysClock(CLK_SOURCE_PLL_60MHz);
    
    TMR0_TimerInit(FREQ_SYS);         
    TMR0_ITCfg(ENABLE, TMR0_3_IT_CYC_END);
    PFIC_EnableIRQ(TMR3_IRQn);
    DelayMs(200);
    OLED_Init();
    OLED_ShowString(0,0, "ABCDEFGH");
    while (1) {
        DelayMs(10);
    }
}

    