

#include "CH59x_common.h"
#include "oled_driver.h"
int main() {
    SetSysClock(CLK_SOURCE_PLL_60MHz);

    OLED_Init();
    OLED_ShowString(0,0, "ABCDEFGH");
    OLED_ShowString(0,1, "1234567890");

    while(1) {
        
    }
}