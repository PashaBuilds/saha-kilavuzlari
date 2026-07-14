/* ============================================================
 * uart_ps.c — minimal, register-level driver for PS UART0
 *
 * Addresses and offsets are confirmed against UG1085 (Zynq UltraScale+
 * TRM) and embeddedsw xuartps_hw.h:
 *   UART0 base address    : 0xFF00_0000
 *   SR  (Channel Status)  : offset 0x2C
 *   FIFO (TX_RX)          : offset 0x30
 *   XUARTPS_SR_TXFULL     : 0x10
 *
 * This file is part of lab10-bughunt and contains none of the 4 known
 * bugs — the issue isn't in UART, it's on the interrupt/GPIO side.
 * ============================================================ */
#include "uart_ps.h"
#include "xil_io.h"

#define UART0_BASE_ADDR     0xFF000000U

#define UART_OFS_CR     0x00U   /* Control Register */
#define UART_OFS_MR     0x04U   /* Mode Register */
#define UART_OFS_SR     0x2CU   /* Channel Status Register */
#define UART_OFS_FIFO   0x30U   /* TX_RX FIFO */

#define UART_CR_TXRES   (1U << 2)   /* reset the TX FIFO/logic */
#define UART_CR_RXRES   (1U << 1)   /* reset the RX FIFO/logic */
#define UART_CR_TXEN    (1U << 4)   /* transmitter enable */

#define UART_MR_8N1     0x00000020U  /* 8 data bits, no parity, 1 stop */

#define UART_SR_TXFULL  0x00000010U


static inline void uartRegWrite(unsigned int uiOffset, unsigned int uiValue)
{
    Xil_Out32(UART0_BASE_ADDR + uiOffset, uiValue);
}


static inline unsigned int uartRegRead(unsigned int uiOffset)
{
    return Xil_In32(UART0_BASE_ADDR + uiOffset);
}


/**
 * @brief Prepares UART0 for use.
 */
void uartInit(void)
{
    /* Reset the TX/RX FIFOs and status logic. */
    uartRegWrite(UART_OFS_CR, UART_CR_TXRES | UART_CR_RXRES);

    /* 8N1, normal mode. Since the baud rate (115200) is already set by the
       FSBL at boot, we don't touch the Baud Rate Generator/Divider here;
       we only concern ourselves with the mode and enabling the
       transmitter. */
    uartRegWrite(UART_OFS_MR, UART_MR_8N1);
    uartRegWrite(UART_OFS_CR, UART_CR_TXEN);
}


/**
 * @brief Sends a single character to the UART0 TX FIFO.
 */
void uartSendChar(char cChar)
{
    /* Wait here while the TX FIFO is full. */
    while ((uartRegRead(UART_OFS_SR) & UART_SR_TXFULL) != 0U)
    {
        /* empty body: waiting for the FIFO to drain */
    }

    uartRegWrite(UART_OFS_FIFO, (unsigned int)cChar);
}


/**
 * @brief Sends a NUL-terminated string character by character.
 */
void uartSendString(const char* cpString)
{
    while (*cpString != '\0')
    {
        uartSendChar(*cpString);
        cpString++;
    }
}
