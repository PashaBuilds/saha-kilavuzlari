/* ============================================================================
 * main.c — GÖREV 5 çözümü: Timer ile Kalp Atışı
 *
 * TTC0 kanal 0'ı (taban 0xFF11_0000) 1 Hz periyodik kesme üretecek şekilde
 * kurar; her tikte DS50'yi (PS MIO23) tersine çevirir ve UART'a "tick N"
 * satırı basar. Kurulum sırası Bölüm 7'deki beşli GIC desenidir; bu sefer
 * kesme kaynağı GPIO değil TTC0 kanal 0 (GIC ID 68).
 *
 * INTERVAL HESABI (Bölüm 7 / content/_arastirma-ek-D.md §D.3):
 *   TTC'nin Interval yazmacı ZynqMP'de 32-bit'tir, bu yüzden tipik LPD
 *   saat hızlarında (onlarca MHz) 1 Hz gibi düşük bir frekansa
 *   prescaler'sız da ulaşılır:
 *
 *       Interval = (XPAR_XTTCPS_0_CLOCK_HZ / hedef_tick_hz) - 1
 *
 *   XPAR_XTTCPS_0_CLOCK_HZ platformun .xsa'sına göre değişir — burada
 *   elle bir MHz rakamı VARSAYILMIYOR, xparameters.h'tan okunuyor.
 * ============================================================================ */

#include "xparameters.h"
#include "xttcps.h"
#include "xgpiops.h"
#include "xscugic.h"
#include "xil_exception.h"
#include "xstatus.h"
#include "uart_ps.h"

#define KESME_PS_PIN_DS50        23U   /* DS50 LED'i -> PS MIO23 (heartbeat) */
#define KESME_GIC_ID_TTC0_CH0    68U   /* GIC kesme ID'si: TTC0 kanal 0 (Bolum 7) */
#define TIMER_HEDEF_TICK_HZ      1U    /* saniyede bir tick */

static XGpioPs S_sGpio;
static XTtcPs  S_sTtc;
static XScuGic S_sGic;

/* ISR ile ana dongu arasindaki TEK kanal. volatile ZORUNLU (Bolum 5/7). */
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

/* --- ISR: KISA. Durumu oku+ack'le, bayragi set et, cik. --- */
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

    /* --- PS GPIO: yalniz DS50 cikis (heartbeat gostergesi) --- */
    spGpioConfig = XGpioPs_LookupConfig(XPAR_XGPIOPS_0_DEVICE_ID);
    if (spGpioConfig == NULL)
    {
        uartSendString("HATA: XGpioPs_LookupConfig basarisiz.\n");
        while (1) { ; }
    }

    if (XGpioPs_CfgInitialize(&S_sGpio, spGpioConfig,
                               spGpioConfig->BaseAddr) != XST_SUCCESS)
    {
        uartSendString("HATA: XGpioPs_CfgInitialize basarisiz.\n");
        while (1) { ; }
    }

    XGpioPs_SetDirectionPin(&S_sGpio, KESME_PS_PIN_DS50, 1U);
    XGpioPs_SetOutputEnablePin(&S_sGpio, KESME_PS_PIN_DS50, 1U);

    /* --- TTC0 kanal 0: interval mode, 1 Hz --- */
    spTtcConfig = XTtcPs_LookupConfig(XPAR_XTTCPS_0_DEVICE_ID);
    if (spTtcConfig == NULL)
    {
        uartSendString("HATA: XTtcPs_LookupConfig basarisiz.\n");
        while (1) { ; }
    }

    if (XTtcPs_CfgInitialize(&S_sTtc, spTtcConfig,
                              spTtcConfig->BaseAddress) != XST_SUCCESS)
    {
        uartSendString("HATA: XTtcPs_CfgInitialize basarisiz.\n");
        while (1) { ; }
    }

    XTtcPs_SetOptions(&S_sTtc, XTTCPS_OPTION_INTERVAL_MODE);

    /* Elle hesap — dosya basi yorumundaki formulun kod karsiligi.
     * XPAR_XTTCPS_0_CLOCK_HZ .xsa'dan uretilir, burada uydurulmuyor. */
    uiInterval = (XPAR_XTTCPS_0_CLOCK_HZ / TIMER_HEDEF_TICK_HZ) - 1U;
    XTtcPs_SetInterval(&S_sTtc, uiInterval);

    XTtcPs_EnableInterrupts(&S_sTtc, XTTCPS_IXR_INTERVAL_MASK);

    if (setupInterruptSystem() != XST_SUCCESS)
    {
        uartSendString("HATA: setupInterruptSystem basarisiz.\n");
        while (1) { ; }
    }

    XTtcPs_Start(&S_sTtc);

    uartSendString("\n--- GOREV 5: Timer ile Kalp Atisi ---\n");
    uartSendString("TTC0 kanal 0, 1 Hz. DS50 kalp gibi atiyor.\n\n");

    uiTickCount = 0U;
    uiLedState = 0U;

    while (1)
    {
        if (G_ucTickFlag != 0U)
        {
            G_ucTickFlag = 0U;   /* once temizle, sonra isle (Gorev 4'teki
                                    * yaris riskiyle ayni gerekce) */

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
