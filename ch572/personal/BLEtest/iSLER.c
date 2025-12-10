/* 
 * Packet Spoofer - Simplified (CH572)
 * Broadcasts a custom packet every 300ms.
 * Includes heartbeat on PA9.
 */
#include "ch32fun.h"
#include "iSLER.h"

#define LED PA9

// Packet Payload
uint8_t adv[] = {
    // AdvA (MAC Address)
    11, 22, 33, 44, 55, 66,
    // AdvData
    0x1E, 0xFF, 0x06, 0x00, 0x01, 0x09, 0x20, 0x22, 
    0x6F, 0x7B, 0x56, 0x00, 0xBD, 0xA6, 0x9A, 0xB6, 
    0xFF, 0x9A, 0x3A, 0x6D, 0xAF, 0xA3, 0x43, 0x95, 
    0x00, 0xE0, 0xDD, 0xC2, 0x33, 0xA3, 0x11
};

uint8_t adv_channels[] = {37, 38, 39};

void Frame_TX_Simple(uint8_t *payload, size_t len, uint8_t channel) {
    // 37 bytes payload + 2 header bytes
    __attribute__((aligned(4))) uint8_t TX_BUF[64]; 

    BB->CTRL_TX = (BB->CTRL_TX & 0xfffffffc) | 1;

    DevSetChannel(channel);
    DevSetMode(DEVSETMODE_TX);

    // Custom Access Address as requested by USER
    BB->ACCESSADDRESS1 = 0x11111111; 
    BB->CRCINIT1 = 0x555555; 
    
    // CH572 Specific Registers
    BB->ACCESSADDRESS2 = 0x11111111;
    BB->CRCINIT2 = 0x555555;
    BB->CRCPOLY1 = (BB->CRCPOLY1 & 0xff000000) | 0x80032d; 
    BB->CRCPOLY2 = (BB->CRCPOLY2 & 0xff000000) | 0x80032d;

    // Construct Packet
    TX_BUF[0] = 0x42; // PDU Type 2 (ADV_NONCONN_IND), TxAdd=1 (Random)
    TX_BUF[1] = len;  // Length (37)
    memcpy(&TX_BUF[2], payload, len);

    // Load Packet into Hardware (CH572)
    LL->FRAME_BUF = (uint32_t)TX_BUF;

    // Wait for PLL/Tuning
    for( int timeout = 3000; !(RF->RF26 & 0x1000000) && timeout >= 0; timeout-- );

    // Configure for 1M PHY (Use Correct Mask from iSLER.h)
    BB->CTRL_CFG = (BB->CTRL_CFG & 0xfffffcff) | 0x100; 
    
    // CH572 Specific PHY setting
    BB->BB9 = (BB->BB9 & 0xf9ffffff) | 0x2000000;

    LL->LL4 &= 0xfffdffff; 
    LL->STATUS = LL_STATUS_TX;

    // Set Timeout/Duration based on packet length + overhead
    LL->TMR = (uint32_t)(len * 512 + 5000); 

    // Start TX
    BB->CTRL_CFG |= CTRL_CFG_START_TX;
    BB->CTRL_TX &= 0xfffffffc;
    LL->LL0 = 2; 

    // Wait for completion
    while(LL->TMR); 

    // Cleanup
    DevSetMode(0);
    if(LL->LL0 & 3) {
        LL->CTRL_MOD &= CTRL_MOD_RFSTOP;
        LL->LL0 |= 0x08;
    }
}

int main()
{
    SystemInit();
    funGpioInitAll();
    funPinMode( LED, GPIO_CFGLR_OUT_2Mhz_PP ); // Enable LED for Heartbeat

    RFCoreInit(LL_TX_POWER_0_DBM);

    while(1) {
        funDigitalWrite( LED, FUN_LOW ); // LED On

        for(int c = 0; c < sizeof(adv_channels); c++) {
            Frame_TX_Simple(adv, sizeof(adv), adv_channels[c]);
        }
        
        funDigitalWrite( LED, FUN_HIGH ); // LED Off
        Delay_Ms(300); 
    }
}
