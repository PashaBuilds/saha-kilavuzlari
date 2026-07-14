/* ============================================================================
 * uart_ps.h — UART0 register-level mini driver module
 *
 * COPY NOTE: this file is an exact copy of lab02-uart/src/uart_ps.h
 * (the Task 2 solution). To keep every lab folder independently
 * buildable, the copy is carried per the _gorev-zinciri.md contract
 * instead of a reference/symbolic link. Content is unchanged.
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
