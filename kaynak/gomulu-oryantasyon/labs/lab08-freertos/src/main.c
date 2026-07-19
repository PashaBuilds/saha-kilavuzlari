/*
 * lab08-freertos / main.c
 *
 * GOREV 8 -- "Ilk FreeRTOS Uygulaman" cozumu.
 *
 * Uc task ayni anda calisir (gercekte: tek cekirdekte hizla zaman
 * dilimlenerek):
 *   - heartbeatTask    : DS50 LED'ini (PS MIO23) 500 ms periyotla yakip
 *                        sondurur, vTaskDelay ile bekler (busy loop
 *                        YOK).
 *   - statusTask       : her 2 saniyede bir UART'a durum satiri basar.
 *   - buttonHandlerTask: SW19 (PS MIO22) basildiginda ISR'nin
 *                        xSemaphoreGiveFromISR ile verdigi semaphore'u
 *                        xSemaphoreTake ile bekler; basis oldugu anda
 *                        bir satir basar.
 *
 * Donanim degerleri (kaynak: content/_arastirma.md): DS50=MIO23,
 * SW19=MIO22, PS GPIO IRQ ID = 48 (XPS_GPIO_INT_ID).
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
#define BUTTON_GIC_INTERRUPT_ID       XPS_GPIO_INT_ID   /* ZynqMP PS GPIO = 48 */

#define PRIORITY_HEARTBEAT       (tskIDLE_PRIORITY + 1)
#define PRIORITY_STATUS            (tskIDLE_PRIORITY + 1)
#define ONCELIK_BUTTON_ISLEYICI   (tskIDLE_PRIORITY + 2)

#define HEARTBEAT_PERIOD_MS    500U
#define DURUM_PERIYOT_MS         2000U

/* G_ oneki: FreeRTOS nesneleri ve surucu ornekleri task'ler arasinda
 * paylasilir; ISR'den de erisildikleri icin global kalmak zorundalar. */
static XGpioPs           G_sGpio;
static XScuGic           G_sGic;
static SemaphoreHandle_t G_sButtonSemaphore;


/* ledPsWrite -- DS50'yi PS GPIO uzerinden yakar/sondurur. */
static void
ledPsWrite(unsigned int uiState)
{
    XGpioPs_WritePin(&G_sGpio, DS50_MIO_PINI, uiState);
}


/* buttonIsr -- SW19 interrupt'i. Kisa tutulur: bayrak/is islemez,
 * yalnizca semaphore'u verir ve interrupt'in temizlenmesini saglar. */
static void
buttonIsr(void* pvCallBackRef)
{
    XGpioPs*   spGpio = (XGpioPs*)pvCallBackRef;
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;

    XGpioPs_IntrClearPin(spGpio, SW19_MIO_PINI);

    xSemaphoreGiveFromISR(G_sButtonSemaphore, &xHigherPriorityTaskWoken);

    /* ISR'den cikarken, semaphore'u bekleyen task daha yuksek
     * oncelikliyse scheduler'a hemen ona gecmesini soyluyoruz --
     * bloklamadan sinyal vermek budur. */
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}


/* heartbeatTask -- DS50'yi 500 ms periyotla toggle'lar. */
static void
heartbeatTask(void* pvParameters)
{
    unsigned int uiLedState = 0U;

    (void)pvParameters;

    for (;;)
    {
        uiLedState ^= 1U;
        ledPsWrite(uiLedState);

        /* vTaskDelay: CPU'yu bosa dondurmez; scheduler bu task'i
         * Blocked durumuna alir ve o sure boyunca CPU'yu diger
         * task'lere verir. */
        vTaskDelay(pdMS_TO_TICKS(HEARTBEAT_PERIOD_MS));
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
        xil_printf("[Status] period %u -- heartbeatTask and buttonHandlerTask running\r\n",
                   (unsigned int)uiCounter);
        vTaskDelay(pdMS_TO_TICKS(DURUM_PERIYOT_MS));
    }
}


/* buttonHandlerTask -- semaphore'u bekler, ISR verdigi anda uyanir. */
static void
buttonHandlerTask(void* pvParameters)
{
    unsigned int uiPressCount = 0U;

    (void)pvParameters;

    for (;;)
    {
        /* portMAX_DELAY: suresiz bekle -- bu task semaphore gelene
         * kadar Blocked kalir, CPU zamanindan hicbir sey calmaz. */
        if (xSemaphoreTake(G_sButtonSemaphore, portMAX_DELAY) == pdTRUE)
        {
            uiPressCount++;
            xil_printf("[Button] SW19 pressed (%u times)\r\n",
                       (unsigned int)uiPressCount);
        }
    }
}


/* hardwareInit -- GPIO + GIC kurulumu; bare-metal Gorev 4 ile birebir
 * ayni, tek fark bunun scheduler baslamadan once main() icinde
 * kosmasidir. */
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

    iStatus = XScuGic_Connect(&G_sGic, BUTTON_GIC_INTERRUPT_ID,
                               (Xil_ExceptionHandler)buttonIsr,
                               (void*)&G_sGpio);
    if (iStatus != XST_SUCCESS)
    {
        return XST_FAILURE;
    }
    XScuGic_Enable(&G_sGic, BUTTON_GIC_INTERRUPT_ID);

    return XST_SUCCESS;
}


int main(void)
{
    xil_printf("\r\n--- Task 8: Your First FreeRTOS Application ---\r\n");

    if (hardwareInit() != XST_SUCCESS)
    {
        xil_printf("ERROR: hardware initialization failed, halting.\r\n");
        for (;;)
        {
        }
    }

    G_sButtonSemaphore = xSemaphoreCreateBinary();
    if (G_sButtonSemaphore == NULL)
    {
        xil_printf("ERROR: could not create semaphore, halting.\r\n");
        for (;;)
        {
        }
    }

    xTaskCreate(heartbeatTask, "Heartbeat", configMINIMAL_STACK_SIZE,
                NULL, PRIORITY_HEARTBEAT, NULL);
    xTaskCreate(statusTask, "Status", configMINIMAL_STACK_SIZE,
                NULL, PRIORITY_STATUS, NULL);
    xTaskCreate(buttonHandlerTask, "ButtonHandler", configMINIMAL_STACK_SIZE,
                NULL, ONCELIK_BUTTON_ISLEYICI, NULL);

    /* Scheduler'i baslat -- normal akista kontrol bu satirin otesine
     * bir daha dogru duzgun donmez; artik uc task arasinda paylasilir. */
    vTaskStartScheduler();

    xil_printf("ERROR: scheduler stopped unexpectedly.\r\n");
    for (;;)
    {
    }

    return 0;
}
