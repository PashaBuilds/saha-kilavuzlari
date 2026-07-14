/* ============================================================================
 * uart_ps.c — UART0 register-level mini driver module (TASK 2 solution)
 *
 * An exact copy from lab02-uart. Addresses and bit masks are from
 * content/_arastirma.md (UG1085 Table 10-6 + embeddedsw xuartps_hw.h):
 *   UART0 base address   : 0xFF00_0000
 *   SR  (Channel Status) : offset 0x2C, RO
 *   FIFO (TX_RX FIFO)    : offset 0x30
 *   SR bit4 = TXFULL     : mask 0x10
 * ============================================================================ */

#include "uart_ps.h"

#define UART0_BASE_ADDR   0xFF000000U
#define UART_OFS_SR         0x0000002CU   /* Channel Status Register, RO */
#define UART_OFS_FIFO       0x00000030U   /* TX_RX FIFO */
#define UART_SR_TXFULL      0x00000010U   /* SR bit4: TX FIFO full */

#define UART0_SR    (*(volatile unsigned int*)(UART0_BASE_ADDR + UART_OFS_SR))
#define UART0_FIFO  (*(volatile unsigned int*)(UART0_BASE_ADDR + UART_OFS_FIFO))

void uartInit(void)
{
    /* Intentionally empty — see the file-header note in uart_ps.h: the
     * FSBL/BSP already leaves UART0 configured for 115200-8N1. */
}

void uartSendChar(char cChar)
{
    while ((UART0_SR & UART_SR_TXFULL) == UART_SR_TXFULL)
    {
        ;
    }

    UART0_FIFO = (unsigned int)cChar;
}

void uartSendString(const char* cpString)
{
    while (*cpString != '\0')
    {
        if (*cpString == '\n')
        {
            uartSendChar('\r');
        }

        uartSendChar(*cpString);
        cpString++;
    }
}
