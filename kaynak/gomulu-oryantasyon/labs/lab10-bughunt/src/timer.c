/* ============================================================
 * timer.c — TTC0 kanal 0, saniyede bir interrupt
 *
 * lab10-bughunt (Gorev 10 - Bug Hunt). TTC0 kanal 0'in GIC interrupt
 * ID'si 68'dir (XPAR_XTTCPS_0_INTR).
 *
 * ISR kisa tutulur: sayaci artirir, interrupt durumunu temizler, cikar.
 * ============================================================ */
#include "timer.h"
#include "xparameters.h"
#include "xil_exception.h"

volatile unsigned int G_uiTickCount = 0;


/* ------------------------------------------------------------
 * ttcIsr — TTC0 kanal 0 araligi dolunca GIC tarafindan cagrilir.
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
 * @brief TTC0 kanal 0'i 1 Hz icin yapilandirir, GIC'e baglar.
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

    /* Giris saat frekansini elle hesaplamak yerine surucunun yardimci
       fonksiyonunu kullaniyoruz — 1.0 Hz hedefi icin Interval/Prescaler
       ciftini kendisi cikarir (bkz. embeddedsw ttcps_intr_example). */
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
