/* ============================================================================
 * main.c — TASK 2 solution: UART "Hello World" and what's behind printf
 *
 * A two-part demonstration:
 *   1) A single line via xil_printf — observe that the ready-made,
 *      lightweight printf already works.
 *   2) A multi-line welcome banner via your own uart_ps module (register
 *      level) — build by hand what is "behind" the printf you just saw.
 * ============================================================================ */

#include "xil_printf.h"
#include "uart_ps.h"

int main(void)
{
    /* xil_printf: a lightweight variant of standard printf tailored for
     * the embedded world. Its format engine is not as rich as standard
     * printf — the most concrete difference: %f (float/double
     * formatting) is NOT SUPPORTED. The reason is size: the code that
     * converts a float to text (a software floating-point formatter)
     * adds tens of KB to a bare-metal image, and in our world every KB
     * has a cost, so Xilinx deliberately left this support out. Integer
     * and string formatting (%d, %u, %x, %s, %c) work without issue. */
    xil_printf("xil_printf ready: UART0 already configured by the platform.\r\n");

    /* Bring our own module online — per the note in the file header
     * comment, this does not reconfigure baud/format, it only declares
     * the base address ready. */
    uartInit();

    uartSendString("\n");
    uartSendString("========================================\n");
    uartSendString("  Welcome to the team - ZCU111 / PS UART0\n");
    uartSendString("  These lines were printed by your uart_ps module.\n");
    uartSendString("  The TXFULL bit was checked, and data was written to the FIFO.\n");
    uartSendString("========================================\n");
    uartSendString("\n");

    /* main never returns in bare-metal; in a real application, the main
     * work loop (or the next task's polling loop) would start here. */
    while (1)
    {
        ;
    }

    return 0;
}
