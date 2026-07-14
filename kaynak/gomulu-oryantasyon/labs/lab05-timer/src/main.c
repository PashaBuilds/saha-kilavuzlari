/* ============================================================================
 * main.c — TASK 5 solution: Heartbeat via Timer
 *
 * Configures TTC0 channel 0 (base 0xFF11_0000) to generate a periodic 1 Hz
 * interrupt; on every tick it toggles DS50 (PS MIO23) and prints a
 * "tick N" line to UART. The setup order is the five-step GIC pattern
 * from Chapter 7; this time the interrupt source is not a GPIO but TTC0
 * channel 0 (GIC ID 68).
 *
 * INTERVAL CALCULATION (Chapter 7 / content/_arastirma-ek-D.md §D.3):
 *   The TTC's Interval register is 32-bit on the ZynqMP, so at typical
 *   LPD clock speeds (tens of MHz) a low frequency like 1 Hz can be
 *   reached even without a prescaler:
 *
 *       Interval = (XPAR_XTTCPS_0_CLOCK_HZ / target_tick_hz) - 1
 *
 *   XPAR_XTTCPS_0_CLOCK_HZ varies according to the platform's .xsa — no
 *   MHz figure is hardcoded here; it is read from xparameters.h.
 * ============================================================================ */

#include "xparameters.h"
#include "xttcps.h"
#include "xgpiops.h"
#include "xscugic.h"
#include "xil_exception.h"
#include "xstatus.h"
#include "uart_ps.h"

#define KESME_PS_PIN_DS50        23U   /* DS50 LED -> PS MIO23 (heartbeat) */
#define KESME_GIC_ID_TTC0_CH0    68U   /* GIC interrupt ID: TTC0 channel 0 (Chapter 7) */
#define TIMER_TARGET_TICK_HZ      1U    /* one tick per second */

static XGpioPs S_sGpio;
static XTtcPs  S_sTtc;
static XScuGic S_sGic;

/* The ONE channel between the ISR and the main loop. volatile is
 * MANDATORY (Chapter 5/7). */
static volatile unsigned char G_ucTickFlag = 0U;

static void printNumber(unsigned int uiValue)
{
    char cArrBuffer[11];
    int iIndex = 10;

    cArrBuffer[10] = '\0';

    if (uiValue == 0U)
    {
        uartSendChar('0');
        return;
    }

    while ((uiValue > 0U) && (iIndex > 0))
    {
        iIndex--;
        cArrBuffer[iIndex] = (char)('0' + (uiValue % 10U));
        uiValue /= 10U;
    }

    uartSendString(&cArrBuffer[iIndex]);
}

/* --- ISR: SHORT. Read+ack the status, set the flag, exit. --- */
static void tickIsr(void* pvCallBackRef)
{
    XTtcPs* spTtc = (XTtcPs*)pvCallBackRef;
    unsigned int uiStatus;

    uiStatus = XTtcPs_GetInterruptStatus(spTtc);
    XTtcPs_ClearInterruptStatus(spTtc, uiStatus);

    G_ucTickFlag = 1U;
}

static int setupInterruptSystem(void)
{
    int iStatus;
    XScuGic_Config* spGicConfig;

    spGicConfig = XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
    if (spGicConfig == NULL)
    {
        return XST_FAILURE;
    }

    iStatus = XScuGic_CfgInitialize(&S_sGic, spGicConfig,
                                     spGicConfig->CpuBaseAddress);
    if (iStatus != XST_SUCCESS)
    {
        return iStatus;
    }

    Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
        (Xil_ExceptionHandler)XScuGic_InterruptHandler, &S_sGic);
    Xil_ExceptionEnable();

    iStatus = XScuGic_Connect(&S_sGic, KESME_GIC_ID_TTC0_CH0,
        (Xil_ExceptionHandler)tickIsr, (void*)&S_sTtc);
    if (iStatus != XST_SUCCESS)
    {
        return iStatus;
    }

    XScuGic_Enable(&S_sGic, KESME_GIC_ID_TTC0_CH0);

    return XST_SUCCESS;
}

int main(void)
{
    XGpioPs_Config* spGpioConfig;
    XTtcPs_Config*  spTtcConfig;
    unsigned int uiInterval;
    unsigned int uiTickCount;
    unsigned int uiLedState;

    uartInit();

    /* --- PS GPIO: DS50 output only (heartbeat indicator) --- */
    spGpioConfig = XGpioPs_LookupConfig(XPAR_XGPIOPS_0_DEVICE_ID);
    if (spGpioConfig == NULL)
    {
        uartSendString("ERROR: XGpioPs_LookupConfig failed.\n");
        while (1) { ; }
    }

    if (XGpioPs_CfgInitialize(&S_sGpio, spGpioConfig,
                               spGpioConfig->BaseAddr) != XST_SUCCESS)
    {
        uartSendString("ERROR: XGpioPs_CfgInitialize failed.\n");
        while (1) { ; }
    }

    XGpioPs_SetDirectionPin(&S_sGpio, KESME_PS_PIN_DS50, 1U);
    XGpioPs_SetOutputEnablePin(&S_sGpio, KESME_PS_PIN_DS50, 1U);

    /* --- TTC0 channel 0: interval mode, 1 Hz --- */
    spTtcConfig = XTtcPs_LookupConfig(XPAR_XTTCPS_0_DEVICE_ID);
    if (spTtcConfig == NULL)
    {
        uartSendString("ERROR: XTtcPs_LookupConfig failed.\n");
        while (1) { ; }
    }

    if (XTtcPs_CfgInitialize(&S_sTtc, spTtcConfig,
                              spTtcConfig->BaseAddress) != XST_SUCCESS)
    {
        uartSendString("ERROR: XTtcPs_CfgInitialize failed.\n");
        while (1) { ; }
    }

    XTtcPs_SetOptions(&S_sTtc, XTTCPS_OPTION_INTERVAL_MODE);

    /* Manual calculation — the code counterpart of the formula in the
     * file header comment. XPAR_XTTCPS_0_CLOCK_HZ is generated from the
     * .xsa, not made up here. */
    uiInterval = (XPAR_XTTCPS_0_CLOCK_HZ / TIMER_TARGET_TICK_HZ) - 1U;
    XTtcPs_SetInterval(&S_sTtc, uiInterval);

    XTtcPs_EnableInterrupts(&S_sTtc, XTTCPS_IXR_INTERVAL_MASK);

    if (setupInterruptSystem() != XST_SUCCESS)
    {
        uartSendString("ERROR: setupInterruptSystem failed.\n");
        while (1) { ; }
    }

    XTtcPs_Start(&S_sTtc);

    uartSendString("\n--- TASK 5: Heartbeat via Timer ---\n");
    uartSendString("TTC0 channel 0, 1 Hz. DS50 beats like a heart.\n\n");

    uiTickCount = 0U;
    uiLedState = 0U;

    while (1)
    {
        if (G_ucTickFlag != 0U)
        {
            G_ucTickFlag = 0U;   /* clear first, process second (same
                                    * rationale as the race risk in Task 4) */

            uiTickCount++;
            uiLedState ^= 1U;
            XGpioPs_WritePin(&S_sGpio, KESME_PS_PIN_DS50, uiLedState);

            uartSendString("tick ");
            printNumber(uiTickCount);
            uartSendString("\n");
        }
    }

    return 0;
}
