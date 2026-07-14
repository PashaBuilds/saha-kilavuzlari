/* ============================================================
 * timer.c — TTC0 channel 0, interrupt once per second
 *
 * lab10-bughunt (Task 10 - Bug Hunt). TTC0 channel 0's GIC interrupt ID
 * is 68 (XPAR_XTTCPS_0_INTR).
 *
 * The ISR is kept short: increments the counter, clears the interrupt
 * status, exits.
 * ============================================================ */
#include "timer.h"
#include "xparameters.h"
#include "xil_exception.h"

volatile unsigned int G_uiTickCount = 0;


/* ------------------------------------------------------------
 * ttcIsr — called by the GIC when the TTC0 channel 0 interval elapses.
 * ------------------------------------------------------------ */
static void ttcIsr(void* pvCallBackRef)
{
    XTtcPs*      spTtc = (XTtcPs*)pvCallBackRef;
    unsigned int uiEventState;

    uiEventState = XTtcPs_GetInterruptStatus(spTtc);
    XTtcPs_ClearInterruptStatus(spTtc, uiEventState);

    if ((uiEventState & XTTCPS_IXR_INTERVAL_MASK) != 0U)
    {
        G_uiTickCount++;
    }
}


/**
 * @brief Configures TTC0 channel 0 for 1 Hz, connects it to the GIC.
 */
int timerInit(XTtcPs* spTtc, XScuGic* spGic)
{
    XTtcPs_Config* spConfig;
    XInterval      intervalValue;
    unsigned char  ucPrescaler;
    int            iStatus;

    spConfig = XTtcPs_LookupConfig(XPAR_XTTCPS_0_DEVICE_ID);
    if (spConfig == NULL)
    {
        return XST_FAILURE;
    }

    iStatus = XTtcPs_CfgInitialize(spTtc, spConfig,
                                    spConfig->BaseAddress);
    if (iStatus != XST_SUCCESS)
    {
        return iStatus;
    }

    XTtcPs_SetOptions(spTtc, XTTCPS_OPTION_INTERVAL_MODE |
                              XTTCPS_OPTION_WAVE_DISABLE);

    /* Instead of computing the input clock frequency by hand, we use the
       driver's helper function — it works out the Interval/Prescaler
       pair itself for a 1.0 Hz target (see embeddedsw
       ttcps_intr_example). */
    XTtcPs_CalcIntervalFromFreq(spTtc, 1.0, &intervalValue, &ucPrescaler);
    XTtcPs_SetInterval(spTtc, intervalValue);
    XTtcPs_SetPrescaler(spTtc, ucPrescaler);

    iStatus = XScuGic_Connect(spGic, XPAR_XTTCPS_0_INTR,
                               (Xil_ExceptionHandler)ttcIsr,
                               (void*)spTtc);
    if (iStatus != XST_SUCCESS)
    {
        return iStatus;
    }
    XScuGic_Enable(spGic, XPAR_XTTCPS_0_INTR);

    XTtcPs_EnableInterrupts(spTtc, XTTCPS_IXR_INTERVAL_MASK);
    XTtcPs_Start(spTtc);

    return XST_SUCCESS;
}
