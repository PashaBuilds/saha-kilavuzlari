/* ============================================================
 * main.c — lab10-bughunt: counter + button + UART status (Task 10, Bug Hunt)
 *
 * Expected behavior (see README.md):
 *   - TTC0 channel 0 prints a "tick N" line once per second
 *   - a "button: M" line + DS50 toggle on an SW19 press
 *   - counters increment correctly, system runs stably for hours
 *
 * This project was left behind by the intern who preceded you: it
 * compiles, it loads onto the board, but something isn't working as
 * expected in four places. Try to find them yourself first — hints and
 * the full solution are on the Chapter 11 / Task 10 card and in
 * SOLUTION.md.
 * ============================================================ */
#include <stdio.h>
#include "xparameters.h"
#include "xscugic.h"
#include "xgpiops.h"
#include "xttcps.h"
#include "xil_exception.h"

#include "uart_ps.h"
#include "gpio_led_button.h"
#include "timer.h"

/* How many ticks between printing a system health summary. */
#define SUMMARY_TICK_INTERVAL   10U


static XScuGic S_sGic;
static XGpioPs S_sGpio;
static XTtcPs  S_sTtc;


/* ------------------------------------------------------------
 * printHealthSummary — periodic summary line.
 *
 * Previous intern's note: uses a work buffer kept wide "in case a
 * multi-line history log gets added later."
 * ------------------------------------------------------------ */
static void printHealthSummary(unsigned int uiTick, unsigned int uiButton)
{
    /* Wide work area allocated to print the history summary in one shot
       (room was left in case multiple lines are added later). */
    char cArrHistoryBuffer[8192];

    snprintf(cArrHistoryBuffer, sizeof(cArrHistoryBuffer),
              "summary: tick=%lu button=%lu\r\n",
              (unsigned long)uiTick, (unsigned long)uiButton);
    uartSendString(cArrHistoryBuffer);
}


int main(void)
{
    XScuGic_Config* spGicConfig;
    unsigned int    uiLastSeenTick    = 0;
    unsigned int    uiLastSummaryTick = 0xFFFFFFFFU;

    uartInit();
    uartSendString("lab10-bughunt started\r\n");

    /* GIC: must be set up before either peripheral. */
    spGicConfig = XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
    if (spGicConfig == NULL)
    {
        uartSendString("ERROR: GIC configuration not found\r\n");
        return XST_FAILURE;
    }
    if (XScuGic_CfgInitialize(&S_sGic, spGicConfig,
                               spGicConfig->CpuBaseAddress) != XST_SUCCESS)
    {
        uartSendString("ERROR: could not initialize GIC\r\n");
        return XST_FAILURE;
    }

    Xil_ExceptionInit();
    Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_INT,
                                  (Xil_ExceptionHandler)XScuGic_InterruptHandler,
                                  &S_sGic);

    if (gpioLedButtonInit(&S_sGpio, &S_sGic) != XST_SUCCESS)
    {
        uartSendString("ERROR: could not initialize GPIO/button\r\n");
        return XST_FAILURE;
    }

    if (timerInit(&S_sTtc, &S_sGic) != XST_SUCCESS)
    {
        uartSendString("ERROR: could not initialize TTC0\r\n");
        return XST_FAILURE;
    }

    Xil_ExceptionEnable();

    uartSendString("setup complete, loop starting\r\n");

    for (;;)
    {
        /* Print if a new tick has arrived. */
        if (G_uiTickCount != uiLastSeenTick)
        {
            char cArrLine[32];

            uiLastSeenTick = G_uiTickCount;

            snprintf(cArrLine, sizeof(cArrLine), "tick %lu\r\n",
                      (unsigned long)uiLastSeenTick);
            uartSendString(cArrLine);

            /* Print a system health summary at regular intervals. */
            if ((uiLastSeenTick % SUMMARY_TICK_INTERVAL) == 0U &&
                uiLastSeenTick != uiLastSummaryTick)
            {
                uiLastSummaryTick = uiLastSeenTick;
                printHealthSummary(uiLastSeenTick, G_uiButtonCount);
            }
        }

        /* Handle it if the button flag has been set. */
        if (G_ucButtonFlag)
        {
            char cArrLine[32];

            G_ucButtonFlag = 0;

            snprintf(cArrLine, sizeof(cArrLine), "button: %lu\r\n",
                      (unsigned long)G_uiButtonCount);
            uartSendString(cArrLine);
            ledDs50Toggle(&S_sGpio);
        }
    }

    /* Never reached. */
}
