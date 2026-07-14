/* ============================================================
 * main.c — lab10-bugav: sayac + buton + UART durum (Gorev 10, Bug Avi)
 *
 * Beklenen davranis (bkz. README.md):
 *   - TTC0 kanal 0 ile saniyede bir "tick N" satiri
 *   - SW19 basisinda "buton: M" satiri + DS50 toggle
 *   - Sayaclar dogru artar, sistem saatlerce kararli calisir
 *
 * Bu proje senden onceki stajyerden kaldi: derleniyor, karta yukleniyor,
 * ama dort yerinde bir seyler beklendigi gibi yurumuyor. Once kendin
 * bulmayi dene — ipuclari ve tam cozum Bolum 11 / Gorev 10 kartinda ve
 * COZUM.md'de.
 * ============================================================ */
#include <stdio.h>
#include "xparameters.h"
#include "xscugic.h"
#include "xgpiops.h"
#include "xttcps.h"
#include "xil_exception.h"

#include "uart_ps.h"
#include "gpio_led_buton.h"
#include "zamanlayici.h"

/* Kac tick'te bir sistem saglik ozeti basilsin. */
#define OZET_TICK_ARALIGI   10U


static XScuGic S_sGic;
static XGpioPs S_sGpio;
static XTtcPs  S_sTtc;


/* ------------------------------------------------------------
 * printHealthSummary — periyodik ozet satiri.
 *
 * Onceki stajyerin notu: "ileride cok satirli gecmis logu eklenebilir"
 * diye genis tutulan bir calisma tamponu kullanir.
 * ------------------------------------------------------------ */
static void printHealthSummary(unsigned int uiTick, unsigned int uiButton)
{
    /* Gecmis ozetini tek seferde basmak icin ayrilan genis calisma
       alani (ilerde coklu satir eklenirse diye pay birakildi). */
    char cArrHistoryBuffer[8192];

    snprintf(cArrHistoryBuffer, sizeof(cArrHistoryBuffer),
              "ozet: tick=%lu buton=%lu\r\n",
              (unsigned long)uiTick, (unsigned long)uiButton);
    uartSendString(cArrHistoryBuffer);
}


int main(void)
{
    XScuGic_Config* spGicConfig;
    unsigned int    uiLastSeenTick    = 0;
    unsigned int    uiLastSummaryTick = 0xFFFFFFFFU;

    uartInit();
    uartSendString("lab10-bugav basladi\r\n");

    /* GIC: her iki cevre biriminden once kurulmali. */
    spGicConfig = XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
    if (spGicConfig == NULL)
    {
        uartSendString("HATA: GIC yapilandirmasi bulunamadi\r\n");
        return XST_FAILURE;
    }
    if (XScuGic_CfgInitialize(&S_sGic, spGicConfig,
                               spGicConfig->CpuBaseAddress) != XST_SUCCESS)
    {
        uartSendString("HATA: GIC baslatilamadi\r\n");
        return XST_FAILURE;
    }

    Xil_ExceptionInit();
    Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_INT,
                                  (Xil_ExceptionHandler)XScuGic_InterruptHandler,
                                  &S_sGic);

    if (gpioLedButtonInit(&S_sGpio, &S_sGic) != XST_SUCCESS)
    {
        uartSendString("HATA: GPIO/buton baslatilamadi\r\n");
        return XST_FAILURE;
    }

    if (timerInit(&S_sTtc, &S_sGic) != XST_SUCCESS)
    {
        uartSendString("HATA: TTC0 baslatilamadi\r\n");
        return XST_FAILURE;
    }

    Xil_ExceptionEnable();

    uartSendString("kurulum tamam, dongu basliyor\r\n");

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

            /* Belirli araliklarla sistem saglik ozeti bas. */
            if ((uiLastSeenTick % OZET_TICK_ARALIGI) == 0U &&
                uiLastSeenTick != uiLastSummaryTick)
            {
                uiLastSummaryTick = uiLastSeenTick;
                printHealthSummary(uiLastSeenTick, G_uiButtonCount);
            }
        }

        /* Buton bayragi set edildiyse isle. */
        if (G_ucButtonFlag)
        {
            char cArrLine[32];

            G_ucButtonFlag = 0;

            snprintf(cArrLine, sizeof(cArrLine), "buton: %lu\r\n",
                      (unsigned long)G_uiButtonCount);
            uartSendString(cArrLine);
            ledDs50Toggle(&S_sGpio);
        }
    }

    /* Buraya hic ulasilmaz. */
}
