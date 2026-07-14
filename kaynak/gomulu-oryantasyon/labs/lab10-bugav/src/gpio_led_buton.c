/* ============================================================
 * gpio_led_buton.c — DS50 LED'i ve SW19 butonu, kesme tabanli
 *
 * lab10-bugav (Gorev 10 - Bug Avi).
 * ============================================================ */
#include "gpio_led_buton.h"
#include "uart_ps.h"
#include "xparameters.h"
#include "xil_exception.h"

/* Buton ISR'inin ana donguyle konustugu bayrak. Bayragi ana dongu okuyor,
   ISR yaziyor — klasik uretici/tuketici deseni. */
unsigned char G_ucButtonFlag  = 0;
unsigned int  G_uiButtonCount = 0;

/* DS50'nin yazilim tarafindaki golge durumu: 0 sonuk, 1 yanik. */
static unsigned int G_uiDs50State = 0;


/* ------------------------------------------------------------
 * buttonIsr — SW19 kesmesi geldiginde GIC tarafindan cagrilir.
 * ------------------------------------------------------------ */
static void buttonIsr(void* pvCallBackRef)
{
    XGpioPs*     spGpio = (XGpioPs*)pvCallBackRef;
    unsigned int uiDelayCount;

    if (XGpioPs_IntrGetStatusPin(spGpio, SW19_PIN_NO) != 0U)
    {
        XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);

        G_uiButtonCount++;
        G_ucButtonFlag = 1;   /* bayragi ana dongu okuyor */

        /* Butonun mekanik sekmesi (debounce) icin kisa bir yerlesme
           suresi ve hizli bir durum satiri — gelistirme sirasinda
           kesmenin gercekten geldigini gormek istedik, faydali oldu. */
        uartSendString("buton kesmesi geldi\r\n");
        for (uiDelayCount = 0; uiDelayCount < 200000U; uiDelayCount++)
        {
            /* bos govde: kisa bir yerlesme suresi */
        }
    }
}


/**
 * @brief GPIO'yu ve GIC bagini kurar (DS50 cikis, SW19 kesmeli giris).
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

    /* SW19: giris, yukselen kenarda (rising edge) kesme uretir. */
    XGpioPs_SetDirectionPin(spGpio, SW19_PIN_NO, 0);
    XGpioPs_SetIntrTypePin(spGpio, SW19_PIN_NO,
                            XGPIOPS_IRQ_TYPE_EDGE_RISING);
    XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);
    XGpioPs_IntrEnablePin(spGpio, SW19_PIN_NO);

    /* GIC'e bagla: XPS_GPIO_INT_ID (48) — ZynqMP'de PS GPIO'nun tek
       kesme kaynagidir, hangi pinin tetikledigini ISR icinde ayirt
       ederiz (bkz. buttonIsr). */
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
 * @brief DS50'nin durumunu tersine cevirir.
 */
void ledDs50Toggle(XGpioPs* spGpio)
{
    /* durumu tersine cevir */
    G_uiDs50State |= 1U;
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, G_uiDs50State);
}
