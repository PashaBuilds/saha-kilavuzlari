/* ============================================================
 * main.c — lab10-bughunt: sayac + buton + UART durum (Gorev 10, Bug Hunt)
 *
 * Beklenen davranis (bkz. README.md):
 *   - TTC0 kanal 0 saniyede bir "tick N" satiri basar
 *   - SW19 basisinda "button: M" satiri + DS50 toggle
 *   - sayaclar dogru artar, sistem saatlerce kararli calisir
 *
 * Bu proje senden onceki stajyerden kaldi: derleniyor, karta
 * yukleniyor, ama dort yerde bir seyler beklendigi gibi calismiyor.
 * Once kendin bulmayi dene — ipuclari ve tam cozum Bolum 11 / Gorev 10
 * kartinda ve SOLUTION.md'de.
 * ============================================================ */
#include <stdio.h>
#include "xparameters.h"
#include "xscugic.h"
#include "xgpiops.h"
#include "xttcps.h"
#include "xil_exception.h"

#include "uart_ps.h"
#include "gpio_led_button.h"
#include "timer.h"

/* Kac tick'te bir sistem saglik ozeti basilacagi. */
#define SUMMARY_TICK_INTERVAL   10U


static XScuGic S_sGic;
static XGpioPs S_sGpio;
static XTtcPs  S_sTtc;


/* ------------------------------------------------------------
 * printHealthSummary — periyodik ozet satiri.
 *
 * Onceki stajyerin notu: "ileride cok satirli bir gecmis logu
 * eklenirse diye" genis tutulmus bir calisma buffer'i kullanir.
 * ------------------------------------------------------------ */
static void printHealthSummary(unsigned int uiTick, unsigned int uiButton)
{
    /* Gecmis ozetini tek seferde basmak icin ayrilan genis calisma
       alani (ileride birden cok satir eklenirse diye yer birakildi). */
    char cArrHistoryBuffer[8192];

    snprintf(cArrHistoryBuffer, sizeof(cArrHistoryBuffer),
              "summary: tick=%lu button=%lu\r\n",
              (unsigned long)uiTick, (unsigned long)uiButton);
    uartSendString(cArrHistoryBuffer);
}


int main(void)
{
    XScuGic_Config* spGicConfig;
    unsigned int    uiLastSeenTick    = 0;
    unsigned int    uiLastSummaryTick = 0xFFFFFFFFU;

    uartInit();
    uartSendString("lab10-bughunt started\r\n");

    /* GIC: iki cevre biriminden once kurulmus olmali. */
    spGicConfig = XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
    if (spGicConfig == NULL)
    {
        uartSendString("ERROR: GIC configuration not found\r\n");
        return XST_FAILURE;
    }
    if (XScuGic_CfgInitialize(&S_sGic, spGicConfig,
                               spGicConfig->CpuBaseAddress) != XST_SUCCESS)
    {
        uartSendString("ERROR: could not initialize GIC\r\n");
        return XST_FAILURE;
    }

    Xil_ExceptionInit();
    Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_INT,
                                  (Xil_ExceptionHandler)XScuGic_InterruptHandler,
                                  &S_sGic);

    if (gpioLedButtonInit(&S_sGpio, &S_sGic) != XST_SUCCESS)
    {
        uartSendString("ERROR: could not initialize GPIO/button\r\n");
        return XST_FAILURE;
    }

    if (timerInit(&S_sTtc, &S_sGic) != XST_SUCCESS)
    {
        uartSendString("ERROR: could not initialize TTC0\r\n");
        return XST_FAILURE;
    }

    Xil_ExceptionEnable();

    uartSendString("setup complete, loop starting\r\n");

    for (;;)
    {
        /* Yeni bir tick geldiyse bas. */
        if (G_uiTickCount != uiLastSeenTick)
        {
            char cArrLine[32];

            uiLastSeenTick = G_uiTickCount;

            snprintf(cArrLine, sizeof(cArrLine), "tick %lu\r\n",
                      (unsigned long)uiLastSeenTick);
            uartSendString(cArrLine);

            /* Duzenli araliklarla sistem saglik ozeti bas. */
            if ((uiLastSeenTick % SUMMARY_TICK_INTERVAL) == 0U &&
                uiLastSeenTick != uiLastSummaryTick)
            {
                uiLastSummaryTick = uiLastSeenTick;
                printHealthSummary(uiLastSeenTick, G_uiButtonCount);
            }
        }

        /* Buton bayragi kurulduysa isle. */
        if (G_ucButtonFlag)
        {
            char cArrLine[32];

            G_ucButtonFlag = 0;

            snprintf(cArrLine, sizeof(cArrLine), "button: %lu\r\n",
                      (unsigned long)G_uiButtonCount);
            uartSendString(cArrLine);
            ledDs50Toggle(&S_sGpio);
        }
    }

    /* Buraya asla ulasilmaz. */
}
