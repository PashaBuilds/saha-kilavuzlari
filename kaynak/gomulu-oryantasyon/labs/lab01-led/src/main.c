/*
 * main.c — Task 1 (Chapter 4): Turn On the LED (Hello Hardware)
 *
 * Blinks the DS50 LED (PS MIO23) with a 500 ms period using the XGpioPs
 * driver. The DS50/SW19 pair is the ONLY PS LED/button on this board that
 * is accessible without a bitstream (see Chapter 2 and Chapter 4) — the
 * 8 user LEDs (DS11-DS18) are on PL pins, which we revisit in Task 7
 * (using AXI GPIO).
 *
 * The flow uses the CLASSIC Vitis approach: the device is located via
 * XPAR_..._DEVICE_ID. In the Vitis Unified/SDT flow this is replaced by
 *     XGpioPs_LookupConfig(XPAR_XGPIOPS_0_BASEADDR)
 * — LookupConfig takes the base address directly as a parameter, and
 * there is no such thing as DEVICE_ID. Both patterns are explained in
 * Chapter 4.
 */

#include "xgpiops.h"
#include "xparameters.h"
#include "xil_printf.h"
#include "sleep.h"

/* DS50 LED is connected to PS MIO23 (UG1271, "GPIO (MIO 22-23)"). */
#define DS50_LED_PIN_MIO    23U

/* Success criterion: 500 ms on / 500 ms off. */
#define LED_YANIP_SONME_US  500000U

int main(void)
{
    XGpioPs sGpio;
    XGpioPs_Config* spGpioConfig;
    int iStatus;

    /* Step 1: locate the configuration by device ID. */
    spGpioConfig = XGpioPs_LookupConfig(XPAR_XGPIOPS_0_DEVICE_ID);
    if (spGpioConfig == NULL)
    {
        xil_printf("ERROR: GPIO configuration not found.\r\n");
        return XST_FAILURE;
    }

    /* Step 2: initialize the driver with this configuration. */
    iStatus = XGpioPs_CfgInitialize(&sGpio, spGpioConfig,
                                     spGpioConfig->BaseAddr);
    if (iStatus != XST_SUCCESS)
    {
        xil_printf("ERROR: GPIO initialization failed (code=%d).\r\n", iStatus);
        return XST_FAILURE;
    }

    /* Step 3: set MIO23 as output and enable the output buffer.
     * Both calls are required: SetDirectionPin sets DIRM, and
     * SetOutputEnablePin sets OEN (see the Chapter 4 deep dive —
     * main_registers.c). */
    XGpioPs_SetDirectionPin(&sGpio, DS50_LED_PIN_MIO, 1U);
    XGpioPs_SetOutputEnablePin(&sGpio, DS50_LED_PIN_MIO, 1U);

    xil_printf("Task 1: DS50 will blink with a 500 ms period.\r\n");

    /* Step 4: turn on/off in an infinite loop. */
    for (;;)
    {
        XGpioPs_WritePin(&sGpio, DS50_LED_PIN_MIO, 1U);
        usleep(LED_YANIP_SONME_US);

        XGpioPs_WritePin(&sGpio, DS50_LED_PIN_MIO, 0U);
        usleep(LED_YANIP_SONME_US);
    }

    return XST_SUCCESS;
}
