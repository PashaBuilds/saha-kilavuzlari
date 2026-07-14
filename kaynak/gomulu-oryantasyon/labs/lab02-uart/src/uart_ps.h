/* ============================================================================
 * uart_ps.h — UART0 register-level mini driver module (TASK 2 solution)
 *
 * Three functions that drive PS UART0 through direct register access, in
 * order to show what happens behind xil_printf and the XUartPs driver.
 * The API signatures match the contract in _gorev-zinciri.md exactly;
 * lab03+ carries a copy of this file (see that lab's README).
 * ============================================================================ */
#ifndef UART_PS_H
#define UART_PS_H

#include "xil_types.h"

/**
 * @brief Prepares UART0 for use.
 *
 * NOTE: this function does NOT reconfigure the baud rate or frame format
 * (115200-8N1) — the FSBL and the standalone BSP's stdout setup already
 * leave UART0 configured this way when the board boots (see the file
 * header comment in uart_ps.c below). Here we simply treat the register
 * base used by our own module as "ready".
 */
void uartInit(void);

/**
 * @brief Sends a single character to the UART0 TX FIFO.
 *
 * Waits until the FIFO is no longer full (TXFULL) before sending.
 *
 * @param cChar The character to send.
 */
void uartSendChar(char cChar);

/**
 * @brief Sends a null-terminated string character by character.
 *
 * Sends '\r' before '\n' whenever '\n' is encountered (see the
 * explanation in uart_ps.c).
 *
 * @param cpString The null-terminated string to send.
 */
void uartSendString(const char* cpString);

#endif /* UART_PS_H */
