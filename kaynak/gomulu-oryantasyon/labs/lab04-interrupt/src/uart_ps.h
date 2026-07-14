/* ============================================================================
 * uart_ps.h — UART0 register-level mini driver module (TASK 2 solution)
 *
 * An exact copy from lab02-uart — per the _gorev-zinciri.md contract,
 * every lab folder carries its own copy and builds independently.
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
 * @brief Sends a single character to the UART0 TX FIFO; waits until the
 * FIFO is no longer full (TXFULL) before sending.
 *
 * @param cChar The character to send.
 */
void uartSendChar(char cChar);

/**
 * @brief Sends a null-terminated string character by character; sends
 * '\r' before '\n' whenever '\n' is encountered (see the explanation in
 * uart_ps.c).
 *
 * @param cpString The null-terminated string to send.
 */
void uartSendString(const char* cpString);

#endif /* UART_PS_H */
