/*
 * lab07-axigpio / main.c
 *
 * TASK 7 -- "Talk to an IP Block in the PL" solution.
 *
 * In the team-provided bitstream/.xsa, an AXI GPIO IP block is connected to
 * the PL's 8 user LEDs (DS11-DS18, net name GPIO_LED[7:0]). This file
 * accesses that IP's registers directly from the PS with a volatile
 * pointer and produces a light that walks left to right across the 8 LEDs.
 *
 * Register map (source: AMD/Xilinx PG144, AXI GPIO v2.0 -- offsets
 * confirmed via web search in content/_arastirma-ek-E.md):
 *   GPIO_DATA  offset 0x0000  -- data: written value is the output, read
 *                                 value is the input
 *   GPIO_TRI   offset 0x0004  -- direction: bit=0 OUTPUT, bit=1 INPUT
 *
 * Difference from PS GPIO (Task 1, base address fixed in silicon at
 * 0xFF0A0000): the base address here is the window the hardware designer
 * assigned to this IP in Vivado's Address Editor -- it stays fixed in
 * silicon even if the board changes, but this address can vary from design
 * to design. Never hardcode the address by hand -- always take it from the
 * project's own xparameters.h (see README.md Step 2).
 */

#include "xparameters.h"
#include "xil_io.h"
#include "xil_printf.h"
#include "sleep.h"

/* AXI GPIO base address: comes automatically from xparameters.h once the
 * project is built. The instance name varies by hardware designer -- in
 * this lab the IP is assumed to be named "axi_gpio_0" in Vivado. If you
 * see a different name in your own project (e.g. "led_gpio"), the macro
 * name changes accordingly to XPAR_LED_GPIO_...; Task 7's "self-check"
 * question is asking about exactly this. */
#define AXI_GPIO_0_BASE_ADDR        XPAR_AXI_GPIO_0_BASEADDR

#define AXI_GPIO_OFSET_DATA     0x0000U
#define AXI_GPIO_OFSET_TRI      0x0004U

#define LED_MASKE_TUMU          0xFFU     /* GPIO_LED[7:0], 8 bits */
#define RUNNING_LIGHT_DELAY_US 150000U   /* 150 ms between steps */


/* axigpioSetDirection -- configures the bits on the given channel as
 * outputs. In TRI, bit=0 means OUTPUT; we clear to 0 the LED bits we want
 * as outputs. */
static void
axigpioSetDirection(unsigned int uiBase, unsigned int uiOutputMask)
{
    Xil_Out32(uiBase + AXI_GPIO_OFSET_TRI, ~uiOutputMask & LED_MASKE_TUMU);
}

/* axigpioWriteData -- writes directly to the DATA register. */
static void
axigpioWriteData(unsigned int uiBase, unsigned int uiValue)
{
    Xil_Out32(uiBase + AXI_GPIO_OFSET_DATA, uiValue);
}


int main(void)
{
    unsigned char ucIndex;
    unsigned int  uiPattern;

    xil_printf("\r\n--- Task 7: Walking Light on PL AXI GPIO ---\r\n");
    xil_printf("AXI GPIO base address: 0x%08X\r\n", (unsigned int)AXI_GPIO_0_BASE_ADDR);

    /* Direction first: all 8 bits as outputs. Forget this and the LEDs
     * never light at all -- TRI's power and its pitfall go hand in hand
     * (Task 7 "self-check"). */
    axigpioSetDirection(AXI_GPIO_0_BASE_ADDR, LED_MASKE_TUMU);

    for (;;)
    {
        for (ucIndex = 0U; ucIndex < 8U; ucIndex++)
        {
            uiPattern = (unsigned int)(1U << ucIndex);
            axigpioWriteData(AXI_GPIO_0_BASE_ADDR, uiPattern);
            xil_printf("LED pattern: 0x%02X\r\n", (unsigned int)uiPattern);
            usleep(RUNNING_LIGHT_DELAY_US);
        }
    }

    return 0;
}

/*
 * Deep dive -- the same job, with the ready-made driver:
 *
 * Xilinx's XGpio driver (for the AXI GPIO in the PL -- not PS GPIO's
 * XGpioPs; similarly named but a separate driver family) does the two
 * functions above for you:
 *
 *   #include "xgpio.h"
 *   XGpio sLedGpio;
 *   XGpio_Initialize(&sLedGpio, XPAR_AXI_GPIO_0_DEVICE_ID);
 *   XGpio_SetDataDirection(&sLedGpio, 1, ~LED_MASKE_TUMU & LED_MASKE_TUMU);
 *   XGpio_DiscreteWrite(&sLedGpio, 1, uiPattern);
 *
 * The "1" parameter is the channel number (this IP operates single-channel;
 * if dual channel is enabled, channel "2" is used for GPIO2_DATA/GPIO2_TRI).
 * Under the hood, XGpio_SetDataDirection writes to TRI and
 * XGpio_DiscreteWrite writes to DATA using the same offsets -- the driver
 * remembers the register map for you, but trusting a driver blindly
 * without ever having seen what the register actually is, even once, is
 * not a good habit in this profession.
 */
