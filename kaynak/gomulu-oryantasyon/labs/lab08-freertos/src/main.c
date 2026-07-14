/*
 * lab08-freertos / main.c
 *
 * GOREV 8 -- "Ilk FreeRTOS Uygulaman" cozumu.
 *
 * Uc gorev (task) ayni anda (aslinda: tek cekirdekte hizli dilimlenerek)
 * calisir:
 *   - heartbeatTask    : DS50 LED'ini (PS MIO23) 500 ms periyotla yakip
 *                        sondurur, vTaskDelay ile bekler (bos dongu YOK).
 *   - statusTask       : her 2 saniyede bir UART'a bir durum satiri basar.
 *   - buttonHandlerTask: SW19 butonuna (PS MIO22) basildiginda ISR'in
 *                        xSemaphoreGiveFromISR ile verdigi semaforu
 *                        xSemaphoreTake ile bekler; basis aninda bir
 *                        satir basar.
 *
 * Donanim degerleri (kaynak: content/_arastirma.md): DS50=MIO23,
 * SW19=MIO22, PS GPIO IRQ kimligi = 48 (XPS_GPIO_INT_ID).
 * FreeRTOS BSP: freertos10_xilinx, configTICK_RATE_HZ = 100 varsayilan.
 */

#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"

#include "xparameters.h"
#include "xgpiops.h"
#include "xscugic.h"
#include "xil_exception.h"
#include "xil_printf.h"

#define DS50_MIO_PINI            23U
#define SW19_MIO_PINI            22U
#define BUTON_GIC_KESME_ID       XPS_GPIO_INT_ID   /* ZynqMP PS GPIO = 48 */

#define ONCELIK_KALP_ATISI       (tskIDLE_PRIORITY + 1)
#define ONCELIK_DURUM            (tskIDLE_PRIORITY + 1)
#define ONCELIK_BUTON_ISLEYICI   (tskIDLE_PRIORITY + 2)

#define KALP_ATISI_PERIYOT_MS    500U
#define DURUM_PERIYOT_MS         2000U

/* G_ onekli: FreeRTOS nesneleri ve surucu ornekleri, task'lar arasi
 * paylasilir; ISR'den de erisildigi icin global kalmalari gerekir. */
static XGpioPs           G_sGpio;
static XScuGic           G_sGic;
static SemaphoreHandle_t G_sButtonSemaphore;


/* ledPsWrite -- DS50'yi PS GPIO uzerinden yakar/sondurur. */
static void
ledPsWrite(unsigned int uiState)
{
    XGpioPs_WritePin(&G_sGpio, DS50_MIO_PINI, uiState);
}


/* buttonIsr -- SW19 kesmesi. Kisa tutulur: bayrak/is islemez, yalnizca
 * semaforu verir ve GIC'e kesmeyi temizletir. */
static void
buttonIsr(void* pvCallBackRef)
{
    XGpioPs*   spGpio = (XGpioPs*)pvCallBackRef;
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;

    XGpioPs_IntrClearPin(spGpio, SW19_MIO_PINI);

    xSemaphoreGiveFromISR(G_sButtonSemaphore, &xHigherPriorityTaskWoken);

    /* ISR'den cikarken, semaforu bekleyen gorev daha yuksek oncelikliyse
     * scheduler'a hemen ona gecmesini soyleriz -- bloklamadan haber verme
     * budur. */
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}


/* heartbeatTask -- DS50'yi 500 ms periyotla toggle eder. */
static void
heartbeatTask(void* pvParameters)
{
    unsigned int uiLedState = 0U;

    (void)pvParameters;

    for (;;)
    {
        uiLedState ^= 1U;
        ledPsWrite(uiLedState);

        /* vTaskDelay: CPU'yu bosta dondurmez, scheduler bu gorevi
         * Blocked'a alir ve o sure boyunca baska gorevlere CPU verir. */
        vTaskDelay(pdMS_TO_TICKS(KALP_ATISI_PERIYOT_MS));
    }
}


/* statusTask -- her 2 saniyede bir UART'a durum satiri basar. */
static void
statusTask(void* pvParameters)
{
    unsigned int uiCounter = 0U;

    (void)pvParameters;

    for (;;)
    {
        uiCounter++;
        xil_printf("[Durum] %u. periyot -- heartbeatTask ve buttonHandlerTask calisiyor\r\n",
                   (unsigned int)uiCounter);
        vTaskDelay(pdMS_TO_TICKS(DURUM_PERIYOT_MS));
    }
}


/* buttonHandlerTask -- semaforu bekler, ISR'in verdigi anda uyanir. */
static void
buttonHandlerTask(void* pvParameters)
{
    unsigned int uiPressCount = 0U;

    (void)pvParameters;

    for (;;)
    {
        /* portMAX_DELAY: sinirsiz bekle -- bu gorev semafor gelene kadar
         * Blocked'ta durur, CPU'dan hicbir sey calmaz. */
        if (xSemaphoreTake(G_sButtonSemaphore, portMAX_DELAY) == pdTRUE)
        {
            uiPressCount++;
            xil_printf("[Buton] SW19 basildi (%u. kez)\r\n",
                       (unsigned int)uiPressCount);
        }
    }
}


/* hardwareInit -- GPIO + GIC kurulumu; bare-metal Gorev 4'teki ile
 * aynidir, tek fark scheduler baslamadan once, main() icinde yapilmasi. */
static int
hardwareInit(void)
{
    XGpioPs_Config* spGpioConfig;
    XScuGic_Config* spGicConfig;
    int             iStatus;

    spGpioConfig = XGpioPs_LookupConfig(XPAR_XGPIOPS_0_DEVICE_ID);
    if (spGpioConfig == NULL)
    {
        return XST_FAILURE;
    }
    iStatus = XGpioPs_CfgInitialize(&G_sGpio, spGpioConfig,
                                     spGpioConfig->BaseAddr);
    if (iStatus != XST_SUCCESS)
    {
        return XST_FAILURE;
    }

    XGpioPs_SetDirectionPin(&G_sGpio, DS50_MIO_PINI, 1U);
    XGpioPs_SetOutputEnablePin(&G_sGpio, DS50_MIO_PINI, 1U);
    XGpioPs_SetDirectionPin(&G_sGpio, SW19_MIO_PINI, 0U);

    XGpioPs_SetIntrTypePin(&G_sGpio, SW19_MIO_PINI,
                            XGPIOPS_IRQ_TYPE_EDGE_RISING);
    XGpioPs_IntrEnablePin(&G_sGpio, SW19_MIO_PINI);

    spGicConfig = XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
    if (spGicConfig == NULL)
    {
        return XST_FAILURE;
    }
    iStatus = XScuGic_CfgInitialize(&G_sGic, spGicConfig,
                                     spGicConfig->CpuBaseAddress);
    if (iStatus != XST_SUCCESS)
    {
        return XST_FAILURE;
    }

    Xil_ExceptionInit();
    Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_INT,
                                  (Xil_ExceptionHandler)XScuGic_InterruptHandler,
                                  &G_sGic);
    Xil_ExceptionEnable();

    iStatus = XScuGic_Connect(&G_sGic, BUTON_GIC_KESME_ID,
                               (Xil_ExceptionHandler)buttonIsr,
                               (void*)&G_sGpio);
    if (iStatus != XST_SUCCESS)
    {
        return XST_FAILURE;
    }
    XScuGic_Enable(&G_sGic, BUTON_GIC_KESME_ID);

    return XST_SUCCESS;
}


int main(void)
{
    xil_printf("\r\n--- Gorev 8: Ilk FreeRTOS Uygulaman ---\r\n");

    if (hardwareInit() != XST_SUCCESS)
    {
        xil_printf("HATA: donanim baslatilamadi, duruyorum.\r\n");
        for (;;)
        {
        }
    }

    G_sButtonSemaphore = xSemaphoreCreateBinary();
    if (G_sButtonSemaphore == NULL)
    {
        xil_printf("HATA: semafor olusturulamadi, duruyorum.\r\n");
        for (;;)
        {
        }
    }

    xTaskCreate(heartbeatTask, "Heartbeat", configMINIMAL_STACK_SIZE,
                NULL, ONCELIK_KALP_ATISI, NULL);
    xTaskCreate(statusTask, "Status", configMINIMAL_STACK_SIZE,
                NULL, ONCELIK_DURUM, NULL);
    xTaskCreate(buttonHandlerTask, "ButtonHandler", configMINIMAL_STACK_SIZE,
                NULL, ONCELIK_BUTON_ISLEYICI, NULL);

    /* Scheduler'i baslat -- bu satirdan sonrasina normal akista asla
     * dogru donulmez, kontrol artik uc gorev arasinda paylasilir. */
    vTaskStartScheduler();

    xil_printf("HATA: scheduler beklenmedik sekilde durdu.\r\n");
    for (;;)
    {
    }

    return 0;
}
