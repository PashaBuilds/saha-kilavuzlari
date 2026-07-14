/*
 * lab09-kuyruk / main.c
 *
 * GOREV 9 -- "Queue ile Uretici/Tuketici" cozumu.
 *
 * Iki gorev, bir FreeRTOS queue'su ile konusur:
 *   - producerTask : her 500 ms'de ina226ReadBusVoltageMv() ile VCCINT
 *                    bus gerilimini (mV) olcer, zaman damgasiyla birlikte
 *                    bir paket olarak xQueueSend ile kuyruga koyar.
 *   - consumerTask : xQueueReceive ile bekler, gelen paketi formatlayip
 *                    UART'a basar.
 *
 * Bilincli tasarim: UART'a yalnizca consumerTask yazar. Iki gorev ayni
 * anda xil_printf cagirsaydi satirlar birbirine karisabilirdi (UART tek
 * kaynaktir, kilitlenmeden paylasilamaz); tek tuketicili tasarim bu
 * sorunu mimari olarak ortadan kaldirir -- "dogal serilesme".
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

/* SMeasurementPacket -- uretici ile tuketici arasindaki tek sozlesme.
 * Kuyruk bu struct'i deger olarak (kopyalayarak) tasir. */
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

            /* Kisa bir bekleme payi taniriz (50 ms); kuyruk hala doluysa
             * bu olcumu atlariz -- en yeni veriyi biriktirmemeyi, akan
             * veriyi tercih ederiz. */
            if (xQueueSend(G_sMeasurementQueue, &sPacket, pdMS_TO_TICKS(50)) != pdTRUE)
            {
                xil_printf("[Uretici] kuyruk dolu, bu olcum atlandi\r\n");
            }
        }
        else
        {
            xil_printf("[Uretici] INA226 okuma hatasi\r\n");
        }

        vTaskDelay(pdMS_TO_TICKS(URETICI_PERIYOT_MS));
    }
}


/* consumerTask -- kuyruktan paket bekler, formatlayip basar. */
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
    xil_printf("\r\n--- Gorev 9: Queue ile Uretici/Tuketici ---\r\n");

    if (ina226Init() != XST_SUCCESS)
    {
        xil_printf("HATA: INA226 baslatilamadi, duruyorum.\r\n");
        for (;;)
        {
        }
    }

    G_sMeasurementQueue = xQueueCreate(KUYRUK_UZUNLUGU, sizeof(SMeasurementPacket));
    if (G_sMeasurementQueue == NULL)
    {
        xil_printf("HATA: kuyruk olusturulamadi, duruyorum.\r\n");
        for (;;)
        {
        }
    }

    xTaskCreate(producerTask, "Producer", configMINIMAL_STACK_SIZE,
                NULL, ONCELIK_URETICI, NULL);
    xTaskCreate(consumerTask, "Consumer", configMINIMAL_STACK_SIZE,
                NULL, ONCELIK_TUKETICI, NULL);

    vTaskStartScheduler();

    xil_printf("HATA: scheduler beklenmedik sekilde durdu.\r\n");
    for (;;)
    {
    }

    return 0;
}
