/* ============================================================================
 * main.c — GOREV 4 cozumu: Buton Interrupt'i
 *
 * Gorev 3'un polling ile okudugu SW19'u (PS MIO22) GIC uzerinden
 * baglanan bir GPIO interrupt'ina cevirir. Ana dongu DS50'yi (PS MIO23)
 * heartbeat gibi calistirarak "kendi gercek isiyle mesgul" bir CPU'yu
 * taklit eder; buton basisi o isi hic kesmeden, gecikmesiz fark edilir.
 *
 * Kurulum sirasi, Bolum 7'deki bes adimli GIC kalibinin birebir
 * uygulamasidir:
 *   LookupConfig -> CfgInitialize -> Xil_ExceptionRegisterHandler ->
 *   Connect -> Enable.
 *
 * ISR KURALI (Bolum 7): kisa tut. buttonIsr() YALNIZCA bu pinin
 * gercekten tetiklendigini dogrular, volatile bayragi kurar ve donanima
 * alindi bilgisi verir. UART'a yazma, hesap, gecikme yok — bunlarin
 * hepsi ana dongunun isidir.
 * ============================================================================ */

#include "xparameters.h"
#include "xgpiops.h"
#include "xscugic.h"
#include "xil_exception.h"
#include "xstatus.h"
#include "sleep.h"
#include "uart_ps.h"

#define KESME_PS_PIN_SW19       22U   /* SW19 buton -> PS MIO22 (giris) */
#define KESME_PS_PIN_DS50       23U   /* DS50 LED   -> PS MIO23 (cikis, heartbeat) */
#define KESME_GIC_ID_GPIO       48U   /* GIC interrupt ID: PS GPIO (Bolum 7) */

/* Ana dongunun "mesgul" gercek isini taklit eden heartbeat araligi.
 * Kisa tutulur ki butona bastiktan sonra DS50 donmus gibi gorunmesin,
 * ama CPU'nun bu beklemenin icinde oldugu da belli olsun. */
#define HEARTBEAT_INTERRUPT_INTERVAL_US   150000U   /* 150 ms */

static XGpioPs S_sGpio;
static XScuGic S_sGic;

/* ISR'nin ana donguyle konustugu TEK degisken. volatile ZORUNLUDUR:
 * derleyici bu degiskenin ISR tarafindan "beklenmedik bir anda"
 * degistirilebilecegini bilmelidir; aksi halde ana dongudeki okumayi
 * onbellege alip hic tazelemeyebilir (Bolum 5 + Bolum 7'nin dersi). */
static volatile unsigned char G_ucButtonFlag = 0U;

/* --- kucuk yardimci: unsigned int -> ondalik metin, hazir printf gerekmez --- */
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

/* --- ISR: KISA. Yalnizca bayrak + alindi bilgisi. --- */
static void buttonIsr(void* pvCallBackRef)
{
    XGpioPs* spGpio = (XGpioPs*)pvCallBackRef;

    if (XGpioPs_IntrGetStatusPin(spGpio, KESME_PS_PIN_SW19) != 0U)
    {
        G_ucButtonFlag = 1U;
        XGpioPs_IntrClearPin(spGpio, KESME_PS_PIN_SW19);
    }
    /* Buraya UART yazma, hesap ya da gecikme EKLEME — bu satirin altina
     * bir sey ekleme hevesi geldigi anda Bolum 7'nin "ISR'de printf yok"
     * kurali devreye girer. */
}

/* --- GIC'i kurar ve buttonIsr'yi interrupt ID 48'e baglar --- */
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

    /* CPU'nun IRQ exception'ini GIC'in genel handler'ina bagla — bu tek
     * satir, interrupt kaynagi basina bir kez yapilir. */
    Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
        (Xil_ExceptionHandler)XScuGic_InterruptHandler, &S_sGic);
    Xil_ExceptionEnable();

    /* buttonIsr'yi GPIO'nun interrupt ID'sine bagla, sonra o kaynagi etkinlestir. */
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

    /* --- PS GPIO: SW19 giris, DS50 cikis (Gorev 1/3'teki kalibin aynisi) --- */
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

    XGpioPs_SetDirectionPin(&S_sGpio, KESME_PS_PIN_SW19, 0U);
    XGpioPs_SetDirectionPin(&S_sGpio, KESME_PS_PIN_DS50, 1U);
    XGpioPs_SetOutputEnablePin(&S_sGpio, KESME_PS_PIN_DS50, 1U);

    /* --- SW19 icin interrupt tipi: yukselen kenar (Bolum 7) --- */
    XGpioPs_SetIntrTypePin(&S_sGpio, KESME_PS_PIN_SW19,
                            XGPIOPS_IRQ_TYPE_EDGE_RISING);

    if (setupInterruptSystem() != XST_SUCCESS)
    {
        uartSendString("ERROR: setupInterruptSystem failed.\n");
        while (1) { ; }
    }

    /* Pin seviyesindeki interrupt'i en son etkinlestiriyoruz — GIC hazir
     * olmadan pini etkinlestirmek, henuz kimsenin dinlemedigi bir
     * interrupt uretebilirdi. */
    XGpioPs_IntrEnablePin(&S_sGpio, KESME_PS_PIN_SW19);

    uartSendString("\n--- TASK 4: Button Interrupt ---\n");
    uartSendString("Main loop 'busy' with DS50: press SW19, you'll see an instant reaction.\n\n");

    uiPressCount = 0U;
    uiLedState = 0U;

    while (1)
    {
        /* Ana dongunun "gercek isi" burada taklit edilir: DS50
         * heartbeat'i. Gercek bir sistemde bu herhangi bir is olabilirdi
         * — sensor okuma, telemetri hesabi, ekran guncelleme; onemli
         * olan CPU'nun butonu POLLING yapmadan kendi isine devam
         * edebilmesidir. */
        usleep(HEARTBEAT_INTERRUPT_INTERVAL_US);
        uiLedState ^= 1U;
        XGpioPs_WritePin(&S_sGpio, KESME_PS_PIN_DS50, uiLedState);

        if (G_ucButtonFlag != 0U)
        {
            /* ONCE temizle, SONRA isle: bu satirlarin tam arasinda ISR
             * yeniden tetiklenirse yeni basis kaybolmaz — bir sonraki
             * turda yakalanir. Sirayi ters cevirseydik (once isle, sonra
             * temizle) ve biz islerken ISR yeniden tetiklenseydi, isimiz
             * bitince o yeni basisin bayragini kosulsuz temizler ve
             * basisi KAYBEDERDIK — Bolum 7'nin "Kendini sina" sorusunun
             * cevabi budur. */
            G_ucButtonFlag = 0U;

            uiPressCount++;
            uartSendString("button pressed, count = ");
            printNumber(uiPressCount);
            uartSendString("\n");
        }
    }

    return 0;
}
