#include "CH59x_common.h"

#define Right_Enable GPIO_Pin_13 // right motor
#define Right_Phase GPIO_Pin_15
#define right_Correction 1 // easily switch motor direction, should remove later

#define Left_Enable GPIO_Pin_12 // left motor
#define Left_Phase GPIO_Pin_14 
#define left_Correction 1 //easily be able to switch motor direction if code is off

#define Left_Encoder_A  GPIO_Pin_6 // B Left motor
#define Left_Encoder_B  GPIO_Pin_0 // B
volatile int32_t count_left = 0;

#define Right_Encoder_A  GPIO_Pin_4 //right motor
#define Right_Encoder_B  GPIO_Pin_5 
volatile int32_t count_right = 0;

// connects to screen, also to the buttons for counting
#define SDA GPIO_Pin_4 // B
#define SCL GPIO_Pin_7 // B
#define Boot_Button GPIO_Pin_22 // B
//buttons all pulled to ground, pullup should be used. SDA/SCL also connect to the screen, so it can be funky

// distances (meters)
volatile int32_t targetdistance = 0;
volatile int32_t currentdistance = 0;

// time (seconds)
volatile int32_t targettime = 0;
volatile int32_t currenttime = 0;

// max speed, gotten in calibration
static int32_t leftmotormaxspeed = 0;
static int32_t rightmotormaxspeed = 0;
static int32_t combinedmaxspeed = 0;

// speed (PWM)
volatile int32_t leftmotorspeed = 0;
volatile int32_t rightmotorspeed = 0;



__INTERRUPT // this is a interupt 
__HIGH_CODE // keep this in ram ready to go since its important
void TMR0_IRQHandler(void) 
{
    // Check if the interrupt was caused by the timer cycle ending
    if(TMR0_GetITFlag(TMR0_3_IT_CYC_END))
    {
        TMR0_ClearITFlag(TMR0_3_IT_CYC_END); 
        // do stuff
    }
}

__INTERRUPT // this is a interupt 
__HIGH_CODE // keep this in ram ready to go since its important
void calibrationIRQ(void) {
if(GPIOB_ReadITFlagBit(M3ENCA)) 
    {
        uint8_t a = (GPIOB_ReadPortPin(M3ENCA) != 0); // figure out which encoder was edging
        uint8_t b = (GPIOB_ReadPortPin(Lb) != 0);

        if (a == b) cal_count++; //count up/down (up=clockwise)
        else        cal_count--;

        if (a) GPIOB_ITModeCfg(La, GPIO_ITMode_FallEdge); // go onto the next closest encoder reading
        else   GPIOB_ITModeCfg(La, GPIO_ITMode_RiseEdge);

        GPIOB_ClearITFlagBit(La); //clear interupt register
    }

    if(GPIOB_ReadITFlagBit(Ra)) 
    {
        uint8_t a = (GPIOB_ReadPortPin(Ra) != 0); // figure out which encoder got edged
        uint8_t b = (GPIOB_ReadPortPin(Rb) != 0);

        if (a == b) count_m4++; //count up motors spin
        else        count_m4--;

        if (a) GPIOB_ITModeCfg(Ra, GPIO_ITMode_FallEdge); // read for the closest step
        else   GPIOB_ITModeCfg(Ra, GPIO_ITMode_RiseEdge);

        GPIOB_ClearITFlagBit(Ra); // clear
    }
}
__INTERRUPT // this is a interupt 
__HIGH_CODE // keep this in ram ready to go since its important
void runIRQ(void)
{
    if(GPIOB_ReadITFlagBit(M3ENCA)) 
    {
        uint8_t a = (GPIOB_ReadPortPin(M3ENCA) != 0); // figure out which encoder was edging
        uint8_t b = (GPIOB_ReadPortPin(Lb) != 0);

        if (a == b) count_m3++; //count up/down (up=clockwise)
        else        count_m3--;

        if (a) GPIOB_ITModeCfg(La, GPIO_ITMode_FallEdge); // go onto the next closest encoder reading
        else   GPIOB_ITModeCfg(La, GPIO_ITMode_RiseEdge);

        GPIOB_ClearITFlagBit(La); //clear interupt register
    }

    if(GPIOB_ReadITFlagBit(Ra)) 
    {
        uint8_t a = (GPIOB_ReadPortPin(Ra) != 0); // figure out which encoder got edged
        uint8_t b = (GPIOB_ReadPortPin(Rb) != 0);

        if (a == b) count_m4++; //count up motors spin
        else        count_m4--;

        if (a) GPIOB_ITModeCfg(Ra, GPIO_ITMode_FallEdge); // read for the closest step
        else   GPIOB_ITModeCfg(Ra, GPIO_ITMode_RiseEdge);

        GPIOB_ClearITFlagBit(Ra); // clear
    }
}

int main() {
    // Pre run
    SetSysClock(CLK_SOURCE_PLL_60MHz);

    GPIOA_ModeCfg(Left_Enable | Left_Phase | Right_Enable | Right_Phase, GPIO_ModeOut_PP_5mA); // make the motors bits configured for output
    GPIOB_ModeCfg(Left_Encoder_A | Left_Encoder_B | Right_Encoder_A | Right_Encoder_B, GPIO_ModeIN_PU); // make the encoders bits configured for input (pulled up)

    GPIOB_ITModeCfg(Left_Encoder_A, GPIO_ITMode_FallEdge); // setup the interupts, start at falling edge 
    GPIOA_ITModeCfg(Right_Encoder_A, GPIO_ITMode_FallEdge);
    






    rightmotormaxspeed = 
    combinedmaxspeed = min(leftmotormaxspeed, rightmotormaxspeed); 




    // Run
    PFIC_EnableIRQ(GPIO_B_IRQn); // turn on interupt
    PFIC_EnableIRQ(GPIO_A_IRQn);




    If targetdistance/targettime <= 

    // slow down 
    // Post Run

    GPIOA_SetBits(PH2A3); // turn all phases on
    GPIOA_SetBits(PH2B4); 
    GPIOA_SetBits(EN2A3); // turn all motors on
    GPIOA_SetBits(EN2B4);

    // --- PWM Setup ---
    PWMX_CLKCfg(4); 
    PWMX_CycleCfg(100000-1); // speeds of 0-100000
    PWMX_16bit_ACTOUT(CH_PWM4, 100000, High_Level, ENABLE);

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

int speedcalibration() {
    // spin the motors for a little bit at like 1%, 5% 10%, 25%, 50%, 100%. calibrate speed for those stages
    return 1;
}
