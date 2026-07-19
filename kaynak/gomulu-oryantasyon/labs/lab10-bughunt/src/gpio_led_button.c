/* ============================================================
 * gpio_led_button.c — DS50 LED ve SW19 buton, interrupt tabanli
 *
 * lab10-bughunt (Gorev 10 - Bug Hunt).
 * ============================================================ */
#include "gpio_led_button.h"
#include "uart_ps.h"
#include "xparameters.h"
#include "xil_exception.h"

/* Buton ISR'sinin ana donguyle konustugu bayrak. Ana dongu bayragi
   okur, ISR yazar — klasik producer/consumer kalibi. */
unsigned char G_ucButtonFlag  = 0;
unsigned int  G_uiButtonCount = 0;

/* DS50'nin yazilim tarafindaki golge durumu: 0 sonuk, 1 yanik. */
static unsigned int G_uiDs50State = 0;


/* ------------------------------------------------------------
 * buttonIsr — SW19 interrupt'i tetiklendiginde GIC tarafindan cagrilir.
 * ------------------------------------------------------------ */
static void buttonIsr(void* pvCallBackRef)
{
    XGpioPs*     spGpio = (XGpioPs*)pvCallBackRef;
    unsigned int uiDelayCount;

    if (XGpioPs_IntrGetStatusPin(spGpio, SW19_PIN_NO) != 0U)
    {
        XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);

        G_uiButtonCount++;
        G_ucButtonFlag = 1;   /* bayragi ana dongu okur */

        /* Butonun mekanik sekmesi (debounce) icin kisa bir oturma
           beklemesi ve hizli bir durum satiri — gelistirme sirasinda
           interrupt'in gercekten geldigini gormek istedik, ise de
           yaradi. */
        uartSendString("button interrupt received\r\n");
        for (uiDelayCount = 0; uiDelayCount < 200000U; uiDelayCount++)
        {
            /* bos govde: kisa bir oturma beklemesi */
        }
    }
}


/**
 * @brief GPIO ve GIC baglantisini kurar (DS50 cikis, SW19 interrupt girisi).
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

    /* DS50: cikis, baslangicta sonuk. */
    XGpioPs_SetDirectionPin(spGpio, DS50_PIN_NO, 1);
    XGpioPs_SetOutputEnablePin(spGpio, DS50_PIN_NO, 1);
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, 0);
    G_uiDs50State = 0;

    /* SW19: giris, yukselen kenarda interrupt uretir. */
    XGpioPs_SetDirectionPin(spGpio, SW19_PIN_NO, 0);
    XGpioPs_SetIntrTypePin(spGpio, SW19_PIN_NO,
                            XGPIOPS_IRQ_TYPE_EDGE_RISING);
    XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);
    XGpioPs_IntrEnablePin(spGpio, SW19_PIN_NO);

    /* GIC'e baglan: XPS_GPIO_INT_ID (48) — ZynqMP'de PS GPIO'nun tek
       interrupt kaynagi budur; hangi pinin tetikledigini ISR icinde
       ayirt ederiz (bkz. buttonIsr). */
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
 * @brief DS50'nin durumunu tersler.
 */
void ledDs50Toggle(XGpioPs* spGpio)
{
    /* durumu tersle */
    G_uiDs50State |= 1U;
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, G_uiDs50State);
}
