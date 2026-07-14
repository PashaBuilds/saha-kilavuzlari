/* ============================================================================
 * uart_ps.c — UART0 register-level mini driver module
 *
 * COPY NOTE: this file is an exact copy of lab02-uart/src/uart_ps.c
 * (the Task 2 solution). To keep every lab folder independently
 * buildable, the copy is carried across; content is unchanged.
 *
 * Addresses and bit masks are taken directly from content/_arastirma.md
 * (UG1085 Table 10-6 + embeddedsw xuartps_hw.h):
 *   UART0 base address   : 0xFF00_0000
 *   SR  (Channel Status) : offset 0x2C, RO
 *   FIFO (TX_RX FIFO)    : offset 0x30
 *   SR bit4 = TXFULL     : mask 0x10
 *
 * NOTE (also explained in Chapter 5): when the board boots, the FSBL/BSP
 * already leaves UART0 configured at 115200-8N1 (the fact that xil_printf
 * works without any additional configuration is proof of this).
 * uartInit() here does NOT touch the baud/format registers (CR/MR/Baud
 * Rate Generator); it merely declares the register base used by this
 * module as "ready". If a genuine from-scratch init is ever needed (e.g.
 * to also bring up UART1), this is where it would be added.
 * ============================================================================ */

#include "uart_ps.h"

/* ---- UART0 base address and register offsets ---- */
#define UART0_BASE_ADDR   0xFF000000U
#define UART_OFS_SR         0x0000002CU   /* Channel Status Register, RO */
#define UART_OFS_FIFO       0x00000030U   /* TX_RX FIFO */
#define UART_SR_TXFULL      0x00000010U   /* SR bit4: TX FIFO full */

/* Register access via a volatile pointer — the pattern from Chapter 5:
 * "point at a fixed address, read/write from there, and never let the
 * compiler optimize the read away". Base + offset is exactly the formula
 * from Chapter 4. */
#define UART0_SR    (*(volatile unsigned int*)(UART0_BASE_ADDR + UART_OFS_SR))
#define UART0_FIFO  (*(volatile unsigned int*)(UART0_BASE_ADDR + UART_OFS_FIFO))

/**
 * @brief Prepares UART0 for use.
 */
void uartInit(void)
{
    /* Intentionally empty: see the note in the file header comment. We
     * still keep the function here so that main.c can call the same
     * "initialize first, then use" flow uniformly across every module —
     * if a real init is ever needed, this is the single place to change. */
}

/**
 * @brief Sends a single character to the UART0 TX FIFO.
 */
void uartSendChar(char cChar)
{
    /* Wait until the TXFULL bit clears (polling — we will formally name
     * this technique in Chapter 7). Writing to a full FIFO would lose
     * data; we knowingly accept the risk of stalling in an infinite loop
     * because the hardware here is reliable enough to never say "no" —
     * the TX FIFO always drains. */
    while ((UART0_SR & UART_SR_TXFULL) == UART_SR_TXFULL)
    {
        ;
    }

    UART0_FIFO = (unsigned int)cChar;
}

/**
 * @brief Sends a null-terminated string character by character.
 */
void uartSendString(const char* cpString)
{
    while (*cpString != '\0')
    {
        /* Serial terminals interpret '\n' as "move down a line, same
         * column" (line feed); to actually return the cursor to the left
         * margin we also need to send '\r' (carriage return). The
         * standard printf family performs this translation for you on
         * the host side; since we are talking to bare UART here, we
         * handle it ourselves. */
        if (*cpString == '\n')
        {
            uartSendChar('\r');
        }

        uartSendChar(*cpString);
        cpString++;
    }
}
