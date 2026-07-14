/* ============================================================================
 * main.c — TASK 3 solution: Read Button (Polling)
 *
 * Reads SW19 (PS MIO22) via continuous polling, reflects its state onto
 * DS50 (PS MIO23), and prints the "number of times pressed" to UART using
 * counter-based debounce.
 *
 * NOTE: the 8 LEDs, 5 buttons, and DIP switch on the board are on PL pins
 * (as seen in Chapter 2); we cannot access them without a bitstream. This
 * is why we work with only the single PS button (SW19) and single PS LED
 * (DS50) — you will get the 8-LED chaser once the PL gate opens in
 * Chapter 9.
 * ============================================================================ */

#include "xstatus.h"
#include "sleep.h"
#include "uart_ps.h"
#include "button_ps.h"

/* Sampling interval: read SW19 once every 5 ms. A mechanical button
 * typically finishes "bouncing" within a few ms; we do not count a
 * transition as real unless we see the same new value for DEBOUNCE_ESIK
 * CONSECUTIVE rounds. */
#define DEBOUNCE_SAMPLE_INTERVAL_US   5000U   /* 5 ms */
#define DEBOUNCE_ESIK               4U      /* 4 * 5 ms = 20 ms stability window */

/* xil_printf did not support %f (Task 2); here we make the opposite
 * trade-off: we write the number->string conversion OURSELVES so that
 * all output goes through the uart_ps module (i.e. our own code) without
 * needing a ready-made printf. */
static void printNumber(unsigned int uiValue)
{
    char cArrBuffer[11];   /* a 32-bit number is at most 10 digits + '\0' */
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

int main(void)
{
    unsigned int uiStableState;    /* debounced (accepted-as-stable) button state */
    unsigned int uiRawState;       /* raw state read this round (may be bouncing) */
    unsigned int uiUnstableCount;  /* count of consecutive readings that differ from uiStableState */
    unsigned int uiPressCount;     /* debounced, real press count */

    uartInit();

    if (buttonInit() != XST_SUCCESS)
    {
        uartSendString("ERROR: buttonInit failed - check the GPIO DEVICE_ID.\n");
        while (1)
        {
            ;
        }
    }

    uartSendString("\n--- TASK 3: Read Button (Polling) ---\n");
    uartSendString("Press SW19: DS50 turns on. Release: it turns off. Count is debounced.\n\n");

    /* Read the initial state and sync the LED to it — the button may
     * already be held down when the board boots, so assuming "always
     * off" would be wrong. */
    uiStableState = buttonRead();
    uiUnstableCount = 0U;
    uiPressCount = 0U;
    ledPsWrite(uiStableState);

    while (1)
    {
        uiRawState = buttonRead();

        if (uiRawState == uiStableState)
        {
            /* No change — either the button never moved, or a bounce
             * returned to its previous state. Either way we reset the
             * counter; we never count a half-finished transition as
             * real. */
            uiUnstableCount = 0U;
        }
        else
        {
            uiUnstableCount++;

            if (uiUnstableCount >= DEBOUNCE_ESIK)
            {
                /* We saw the same new value for DEBOUNCE_ESIK consecutive
                 * rounds — this is no longer a bounce, it is a real
                 * transition. */
                uiStableState = uiRawState;
                uiUnstableCount = 0U;

                ledPsWrite(uiStableState);

                if (uiStableState != 0U)
                {
                    uiPressCount++;
                    uartSendString("press #");
                    printNumber(uiPressCount);
                    uartSendString(" - DS50 ON\n");
                }
                else
                {
                    uartSendString("release   - DS50 OFF\n");
                }
            }
        }

        /* This is exactly the cost of polling: the CPU does nothing
         * other than this wait, constantly querying SW19. In Chapter 7
         * you will do the same job with an interrupt and eliminate this
         * cost. */
        usleep(DEBOUNCE_SAMPLE_INTERVAL_US);
    }

    return 0;
}
