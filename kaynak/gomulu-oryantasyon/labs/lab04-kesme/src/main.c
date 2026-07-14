/* ============================================================================
 * main.c — GÖREV 4 çözümü: Buton Interrupt'ı
 *
 * Görev 3'ün polling ile okuduğu SW19'u (PS MIO22) GIC üzerinden bağlanan
 * bir GPIO kesmesine dönüştürür. Ana döngü DS50'yi (PS MIO23) bir kalp
 * atışı gibi çalıştırarak "kendi asıl işiyle meşgul" bir CPU'yu simüle
 * eder; buton basımı bu meşguliyeti hiç bölmeden, gecikmesiz fark edilir.
 *
 * Kurulum sırası Bölüm 7'deki beşli GIC deseninin birebir uygulamasıdır:
 *   LookupConfig -> CfgInitialize -> Xil_ExceptionRegisterHandler ->
 *   Connect -> Enable.
 *
 * ISR KURALI (Bölüm 7): kısa tut. buttonIsr() SADECE bu pinin kestiğini
 * doğrular, volatile bayrağı set eder, donanımı ack'ler. UART'a yazmak,
 * hesap yapmak, gecikmek YOK — hepsi ana döngünün işi.
 * ============================================================================ */

#include "xparameters.h"
#include "xgpiops.h"
#include "xscugic.h"
#include "xil_exception.h"
#include "xstatus.h"
#include "sleep.h"
#include "uart_ps.h"

#define KESME_PS_PIN_SW19       22U   /* SW19 butonu -> PS MIO22 (giris) */
#define KESME_PS_PIN_DS50       23U   /* DS50 LED'i  -> PS MIO23 (cikis, heartbeat) */
#define KESME_GIC_ID_GPIO       48U   /* GIC kesme ID'si: PS GPIO (Bolum 7) */

/* Ana dongunun "mesgul" asil isini simule eden heartbeat araligi. Kucuk
 * tutulmasinin sebebi: butona basip DS50'nin donmus gibi gorunmedigini,
 * ama yine de CPU'nun bu bekleme icinde oldugunu hissettirmek. */
#define KESME_HEARTBEAT_ARALIGI_US   150000U   /* 150 ms */

static XGpioPs S_sGpio;
static XScuGic S_sGic;

/* ISR'nin ana donguyle konustugu TEK degisken. volatile ZORUNLU: derleyici
 * bu degiskenin ISR tarafindan "beklenmedik bir anda" degistirilebilecegini
 * bilmeli, aksi halde ana dongudeki okumayi onbellege alip bir daha
 * guncellemeyebilir (Bolum 5 + Bolum 7'nin dersi). */
static volatile unsigned char G_ucButtonFlag = 0U;

/* --- kucuk yardimci: unsigned int -> ondalik metin, hazir printf'e ihtiyac yok --- */
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

/* --- ISR: KISA. Sadece bayrak + ack. --- */
static void buttonIsr(void* pvCallBackRef)
{
    XGpioPs* spGpio = (XGpioPs*)pvCallBackRef;

    if (XGpioPs_IntrGetStatusPin(spGpio, KESME_PS_PIN_SW19) != 0U)
    {
        G_ucButtonFlag = 1U;
        XGpioPs_IntrClearPin(spGpio, KESME_PS_PIN_SW19);
    }
    /* Buraya UART yazma, hesap, gecikme EKLEME — Bolum 7'nin "ISR'de
     * printf yok" kurali tam olarak bu satirin altina bir seyler
     * eklemek istedigin an devreye girer. */
}

/* --- GIC'i kurar ve buttonIsr'i kesme ID 48'e baglar --- */
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

    /* CPU'nun IRQ istisnasini GIC'in genel isleyicisine bagla — bu tek
     * satir her kesme kaynagi icin bir kez yapilir. */
    Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
        (Xil_ExceptionHandler)XScuGic_InterruptHandler, &S_sGic);
    Xil_ExceptionEnable();

    /* buttonIsr'i GPIO'nun kesme ID'sine bagla, sonra o kaynagi ac. */
    iStatus = XScuGic_Connect(&S_sGic, KESME_GIC_ID_GPIO,
        (Xil_ExceptionHandler)buttonIsr, (void*)&S_sGpio);
    if (iStatus != XST_SUCCESS)
    {
        return iStatus;
    }

    XScuGic_Enable(&S_sGic, KESME_GIC_ID_GPIO);

    return XST_SUCCESS;
}

int main(void)
{
    XGpioPs_Config* spGpioConfig;
    unsigned int uiPressCount;
    unsigned int uiLedState;

    uartInit();

    /* --- PS GPIO: SW19 giris, DS50 cikis (Gorev 1/3 ile ayni desen) --- */
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

    XGpioPs_SetDirectionPin(&S_sGpio, KESME_PS_PIN_SW19, 0U);
    XGpioPs_SetDirectionPin(&S_sGpio, KESME_PS_PIN_DS50, 1U);
    XGpioPs_SetOutputEnablePin(&S_sGpio, KESME_PS_PIN_DS50, 1U);

    /* --- SW19 icin kesme turu: yukselen kenar (Bolum 7) --- */
    XGpioPs_SetIntrTypePin(&S_sGpio, KESME_PS_PIN_SW19,
                            XGPIOPS_IRQ_TYPE_EDGE_RISING);

    if (setupInterruptSystem() != XST_SUCCESS)
    {
        uartSendString("HATA: setupInterruptSystem basarisiz.\n");
        while (1) { ; }
    }

    /* Pin duzeyinde kesmeyi en son aciyoruz — GIC hazir olmadan pini
     * acmak, henuz kimsenin dinlemedigi bir kesme uretebilir. */
    XGpioPs_IntrEnablePin(&S_sGpio, KESME_PS_PIN_SW19);

    uartSendString("\n--- GOREV 4: Buton Interrupt'i ---\n");
    uartSendString("Ana dongu DS50 ile 'mesgul': SW19'a bas, aninda tepki gorecek.\n\n");

    uiPressCount = 0U;
    uiLedState = 0U;

    while (1)
    {
        /* Ana dongunun "asil isi" burada simule ediliyor: DS50 heartbeat.
         * Gercek bir sistemde bu, sensor okuma, telemetri hesaplama,
         * ekran guncelleme gibi herhangi bir is olabilirdi — onemli olan,
         * CPU'nun butonu SORMADAN kendi isine devam edebilmesi. */
        usleep(KESME_HEARTBEAT_ARALIGI_US);
        uiLedState ^= 1U;
        XGpioPs_WritePin(&S_sGpio, KESME_PS_PIN_DS50, uiLedState);

        if (G_ucButtonFlag != 0U)
        {
            /* ONCE temizle, SONRA isle: ISR tam bu satirlar arasinda
             * tekrar tetiklenirse yeni basis kaybolmaz, bir sonraki turda
             * yakalanir. Sirayi tersine cevirseydik (once isle, sonra
             * temizle) ISR isleme sirasinda tekrar tetiklenirse o yeni
             * basisin bayragini isimiz bitince kosulsuzca sifirlayip
             * KAYBEDERDIK — Bolum 7'nin "kendini sina" sorusunun cevabi. */
            G_ucButtonFlag = 0U;

            uiPressCount++;
            uartSendString("buton basildi, sayac = ");
            printNumber(uiPressCount);
            uartSendString("\n");
        }
    }

    return 0;
}
