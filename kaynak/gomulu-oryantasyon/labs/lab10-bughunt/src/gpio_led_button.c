/* ============================================================
 * gpio_led_button.c — DS50 LED and SW19 button, interrupt-based
 *
 * lab10-bughunt (Task 10 - Bug Hunt).
 * ============================================================ */
#include "gpio_led_button.h"
#include "uart_ps.h"
#include "xparameters.h"
#include "xil_exception.h"

/* The flag through which the button ISR talks to the main loop. The main
   loop reads the flag, the ISR writes it — the classic producer/consumer
   pattern. */
unsigned char G_ucButtonFlag  = 0;
unsigned int  G_uiButtonCount = 0;

/* DS50's software-side shadow state: 0 off, 1 lit. */
static unsigned int G_uiDs50State = 0;


/* ------------------------------------------------------------
 * buttonIsr — called by the GIC when the SW19 interrupt fires.
 * ------------------------------------------------------------ */
static void buttonIsr(void* pvCallBackRef)
{
    XGpioPs*     spGpio = (XGpioPs*)pvCallBackRef;
    unsigned int uiDelayCount;

    if (XGpioPs_IntrGetStatusPin(spGpio, SW19_PIN_NO) != 0U)
    {
        XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);

        G_uiButtonCount++;
        G_ucButtonFlag = 1;   /* the main loop reads the flag */

        /* A brief settling delay for the button's mechanical bounce
           (debounce), and a quick status line — during development we
           wanted to see that the interrupt was actually arriving, and
           it proved useful. */
        uartSendString("button interrupt received\r\n");
        for (uiDelayCount = 0; uiDelayCount < 200000U; uiDelayCount++)
        {
            /* empty body: a brief settling delay */
        }
    }
}


/**
 * @brief Sets up GPIO and the GIC binding (DS50 output, SW19 interrupt input).
 */
int gpioLedButtonInit(XGpioPs* spGpio, XScuGic* spGic)
{
    XGpioPs_Config* spConfig;
    int             iStatus;

    spConfig = XGpioPs_LookupConfig(XPAR_XGPIOPS_0_DEVICE_ID);
    if (spConfig == NULL)
    {
        return XST_FAILURE;
    }

    iStatus = XGpioPs_CfgInitialize(spGpio, spConfig,
                                     spConfig->BaseAddr);
    if (iStatus != XST_SUCCESS)
    {
        return iStatus;
    }

    /* DS50: output, initially off. */
    XGpioPs_SetDirectionPin(spGpio, DS50_PIN_NO, 1);
    XGpioPs_SetOutputEnablePin(spGpio, DS50_PIN_NO, 1);
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, 0);
    G_uiDs50State = 0;

    /* SW19: input, generates an interrupt on the rising edge. */
    XGpioPs_SetDirectionPin(spGpio, SW19_PIN_NO, 0);
    XGpioPs_SetIntrTypePin(spGpio, SW19_PIN_NO,
                            XGPIOPS_IRQ_TYPE_EDGE_RISING);
    XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);
    XGpioPs_IntrEnablePin(spGpio, SW19_PIN_NO);

    /* Connect to the GIC: XPS_GPIO_INT_ID (48) — on ZynqMP this is PS
       GPIO's single interrupt source; we distinguish which pin triggered
       it inside the ISR (see buttonIsr). */
    iStatus = XScuGic_Connect(spGic, XPS_GPIO_INT_ID,
                               (Xil_ExceptionHandler)buttonIsr,
                               (void*)spGpio);
    if (iStatus != XST_SUCCESS)
    {
        return iStatus;
    }
    XScuGic_Enable(spGic, XPS_GPIO_INT_ID);

    return XST_SUCCESS;
}


/**
 * @brief Inverts DS50's state.
 */
void ledDs50Toggle(XGpioPs* spGpio)
{
    /* invert the state */
    G_uiDs50State |= 1U;
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, G_uiDs50State);
}
