/*
 * lab09-queue / main.c
 *
 * GOREV 9 -- "Queue ile Producer/Consumer" cozumu.
 *
 * Iki task bir FreeRTOS queue uzerinden konusur:
 *   - producerTask : VCCINT bus gerilimini (mV) her 500 ms'de bir
 *                    ina226ReadBusVoltageMv() ile olcer ve zaman
 *                    damgasiyla birlikte paket olarak xQueueSend ile
 *                    kuyruga koyar.
 *   - consumerTask : xQueueReceive ile bekler, gelen paketi bicimler
 *                    ve UART'a basar.
 *
 * Bilincli tasarim: UART'a yalnizca consumerTask yazar. Iki task ayni
 * anda xil_printf cagirsaydi satirlar ic ice gecebilirdi (UART,
 * kilitsiz paylasilaMAYAN tek bir kaynaktir); tek-tuketici tasarim bu
 * sorunu mimari duzeyde ortadan kaldirir -- "dogal serilestirme".
 */

#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"

#include "xil_printf.h"
#include "xstatus.h"

#include "ina226.h"

#define KUYRUK_UZUNLUGU        5U
#define URETICI_PERIYOT_MS     500U

#define ONCELIK_URETICI        (tskIDLE_PRIORITY + 1)
#define ONCELIK_TUKETICI       (tskIDLE_PRIORITY + 1)

/* SMeasurementPacket -- producer ile consumer arasindaki tek sozlesme.
 * Queue bu struct'i degerle (kopyalayarak) tasir. */
typedef struct
{
    unsigned int uiTimestampMs;
    unsigned int uiVccintMv;
} SMeasurementPacket;

static QueueHandle_t G_sMeasurementQueue;


/* producerTask -- periyodik olcum alir, kuyruga koyar. */
static void
producerTask(void* pvParameters)
{
    SMeasurementPacket sPacket;
    unsigned int       uiMilliVolt;

    (void)pvParameters;

    for (;;)
    {
        if (ina226ReadBusVoltageMv(&uiMilliVolt) == XST_SUCCESS)
        {
            sPacket.uiTimestampMs = (unsigned int)(xTaskGetTickCount() * portTICK_PERIOD_MS);
            sPacket.uiVccintMv    = uiMilliVolt;

            /* Kisa bir tolerans (50 ms) taniyoruz; kuyruk hala doluysa
             * bu olcumu atiyoruz -- en yeni veriyi biriktirmek yerine
             * verinin akmaya devam etmesini tercih ediyoruz. */
            if (xQueueSend(G_sMeasurementQueue, &sPacket, pdMS_TO_TICKS(50)) != pdTRUE)
            {
                xil_printf("[Producer] queue full, this measurement was dropped\r\n");
            }
        }
        else
        {
            xil_printf("[Producer] INA226 read error\r\n");
        }

        vTaskDelay(pdMS_TO_TICKS(URETICI_PERIYOT_MS));
    }
}


/* consumerTask -- kuyruktan paket bekler, bicimleyip basar. */
static void
consumerTask(void* pvParameters)
{
    SMeasurementPacket sPacket;

    (void)pvParameters;

    for (;;)
    {
        if (xQueueReceive(G_sMeasurementQueue, &sPacket, portMAX_DELAY) == pdTRUE)
        {
            xil_printf("[%8u ms] VCCINT = %4u mV\r\n",
                       (unsigned int)sPacket.uiTimestampMs,
                       (unsigned int)sPacket.uiVccintMv);
        }
    }
}


int main(void)
{
    xil_printf("\r\n--- Task 9: Producer/Consumer with a Queue ---\r\n");

    if (ina226Init() != XST_SUCCESS)
    {
        xil_printf("ERROR: could not initialize INA226, halting.\r\n");
        for (;;)
        {
        }
    }

    G_sMeasurementQueue = xQueueCreate(KUYRUK_UZUNLUGU, sizeof(SMeasurementPacket));
    if (G_sMeasurementQueue == NULL)
    {
        xil_printf("ERROR: could not create queue, halting.\r\n");
        for (;;)
        {
        }
    }

    xTaskCreate(producerTask, "Producer", configMINIMAL_STACK_SIZE,
                NULL, ONCELIK_URETICI, NULL);
    xTaskCreate(consumerTask, "Consumer", configMINIMAL_STACK_SIZE,
                NULL, ONCELIK_TUKETICI, NULL);

    vTaskStartScheduler();

    xil_printf("ERROR: scheduler stopped unexpectedly.\r\n");
    for (;;)
    {
    }

    return 0;
}
