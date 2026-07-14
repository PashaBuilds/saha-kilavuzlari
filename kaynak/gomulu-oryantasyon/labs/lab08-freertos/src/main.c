/*
 * lab08-freertos / main.c
 *
 * TASK 8 -- "Your First FreeRTOS Application" solution.
 *
 * Three tasks run at the same time (in reality: time-sliced rapidly on a
 * single core):
 *   - heartbeatTask    : toggles the DS50 LED (PS MIO23) on and off with a
 *                        500 ms period, waiting via vTaskDelay (NO busy
 *                        loop).
 *   - statusTask       : prints a status line to UART every 2 seconds.
 *   - buttonHandlerTask: waits with xSemaphoreTake on the semaphore the ISR
 *                        gives via xSemaphoreGiveFromISR when SW19
 *                        (PS MIO22) is pressed; prints a line the moment a
 *                        press occurs.
 *
 * Hardware values (source: content/_arastirma.md): DS50=MIO23,
 * SW19=MIO22, PS GPIO IRQ ID = 48 (XPS_GPIO_INT_ID).
 * FreeRTOS BSP: freertos10_xilinx, configTICK_RATE_HZ = 100 default.
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

/* G_ prefix: FreeRTOS objects and driver instances are shared between
 * tasks; since they are also accessed from the ISR, they must remain
 * global. */
static XGpioPs           G_sGpio;
static XScuGic           G_sGic;
static SemaphoreHandle_t G_sButtonSemaphore;


/* ledPsWrite -- turns DS50 on/off via PS GPIO. */
static void
ledPsWrite(unsigned int uiState)
{
    XGpioPs_WritePin(&G_sGpio, DS50_MIO_PINI, uiState);
}


/* buttonIsr -- SW19 interrupt. Kept short: does not process flags/work,
 * only gives the semaphore and lets the GIC clear the interrupt. */
static void
buttonIsr(void* pvCallBackRef)
{
    XGpioPs*   spGpio = (XGpioPs*)pvCallBackRef;
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;

    XGpioPs_IntrClearPin(spGpio, SW19_MIO_PINI);

    xSemaphoreGiveFromISR(G_sButtonSemaphore, &xHigherPriorityTaskWoken);

    /* When leaving the ISR, if the task waiting on the semaphore has
     * higher priority, we tell the scheduler to switch to it immediately
     * -- this is what it means to signal without blocking. */
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}


/* heartbeatTask -- toggles DS50 with a 500 ms period. */
static void
heartbeatTask(void* pvParameters)
{
    unsigned int uiLedState = 0U;

    (void)pvParameters;

    for (;;)
    {
        uiLedState ^= 1U;
        ledPsWrite(uiLedState);

        /* vTaskDelay: does not spin the CPU idly, the scheduler moves this
         * task to Blocked and hands the CPU to other tasks for that
         * duration. */
        vTaskDelay(pdMS_TO_TICKS(HEARTBEAT_PERIOD_MS));
    }
}


/* statusTask -- prints a status line to UART every 2 seconds. */
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


/* buttonHandlerTask -- waits on the semaphore, wakes the instant the ISR gives it. */
static void
buttonHandlerTask(void* pvParameters)
{
    unsigned int uiPressCount = 0U;

    (void)pvParameters;

    for (;;)
    {
        /* portMAX_DELAY: wait indefinitely -- this task stays Blocked until
         * the semaphore arrives, stealing no CPU time at all. */
        if (xSemaphoreTake(G_sButtonSemaphore, portMAX_DELAY) == pdTRUE)
        {
            uiPressCount++;
            xil_printf("[Button] SW19 pressed (%u times)\r\n",
                       (unsigned int)uiPressCount);
        }
    }
}


/* hardwareInit -- GPIO + GIC setup; identical to bare-metal Task 4, the
 * only difference being that this runs inside main() before the scheduler
 * starts. */
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

    /* Start the scheduler -- control never correctly returns past this
     * line in the normal flow; it is now shared among the three tasks. */
    vTaskStartScheduler();

    xil_printf("ERROR: scheduler stopped unexpectedly.\r\n");
    for (;;)
    {
    }

    return 0;
}
