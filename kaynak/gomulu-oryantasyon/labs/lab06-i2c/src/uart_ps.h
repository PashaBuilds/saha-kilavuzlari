/* ============================================================================
 * uart_ps.h — UART0 register-level mini driver module (TASK 2 solution)
 *
 * An exact copy from lab02-uart — per _gorev-zinciri.md, every lab folder
 * carries its own copy and builds independently.
 * ============================================================================ */
#ifndef UART_PS_H
#define UART_PS_H

#include "xil_types.h"

/**
 * @brief Prepares UART0 for use. HONEST NOTE: this function does NOT
 * reconfigure the baud rate / frame format (115200-8N1) — at board boot,
 * the FSBL and the standalone BSP's stdout setup already leave UART0 with
 * this configuration (see the file-header comment in uart_ps.c below).
 * Here we merely treat the register base our own module will use as
 * "ready."
 */
void uartInit(void);

/**
 * @brief Sends a single character to the UART0 TX FIFO; if the FIFO is
 * full (TXFULL), waits until it drains.
 * @param cChar The character to send.
 */
void uartSendChar(char cChar);

/**
 * @brief Sends a NUL-terminated string character by character; upon
 * seeing '\n', sends '\r' first (see the explanation in uart_ps.c).
 * @param cpString The NUL-terminated string to send.
 */
void uartSendString(const char* cpString);

#endif /* UART_PS_H */
