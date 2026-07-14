/*
 * lab09-queue / main.c
 *
 * TASK 9 -- "Producer/Consumer with a Queue" solution.
 *
 * Two tasks talk to each other through a FreeRTOS queue:
 *   - producerTask : measures the VCCINT bus voltage (mV) every 500 ms
 *                    with ina226ReadBusVoltageMv(), and puts it on the
 *                    queue as a packet, together with a timestamp, via
 *                    xQueueSend.
 *   - consumerTask : waits with xQueueReceive, formats the incoming
 *                    packet, and prints it to UART.
 *
 * Deliberate design: only consumerTask writes to UART. If both tasks
 * called xil_printf at the same time, lines could interleave (UART is a
 * single resource that cannot be shared without locking); a
 * single-consumer design eliminates this problem architecturally --
 * "natural serialization."
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

/* SMeasurementPacket -- the sole contract between the producer and the
 * consumer. The queue carries this struct by value (by copying it). */
typedef struct
{
    unsigned int uiTimestampMs;
    unsigned int uiVccintMv;
} SMeasurementPacket;

static QueueHandle_t G_sMeasurementQueue;


/* producerTask -- takes periodic measurements, puts them on the queue. */
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

            /* We allow a short grace period (50 ms); if the queue is
             * still full, we drop this measurement -- we prefer to keep
             * the data flowing rather than accumulate the newest data. */
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


/* consumerTask -- waits for a packet on the queue, formats and prints it. */
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
