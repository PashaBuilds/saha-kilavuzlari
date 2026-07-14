/* ============================================================
 * uart_ps.h — minimal, register-level driver for PS UART0
 *
 * Part of the lab10-bughunt (Task 10 - Bug Hunt) project. The contract
 * matches exactly what is learned in Chapter 5 / Task 2:
 *   uartInit()            -> prepares UART0 for 115200 8N1
 *   uartSendChar()        -> sends a single character (waits if the TX FIFO is full)
 *   uartSendString()      -> sends a string ending in '\0' character by character
 *
 * The module is redefined here so this lab can be built standalone;
 * each lab folder carries its own copy.
 * ============================================================ */
#ifndef UART_PS_H
#define UART_PS_H

#include "xil_types.h"

/**
 * @brief Prepares UART0 for use.
 */
void uartInit(void);

/**
 * @brief Sends a single character to the UART0 TX FIFO.
 *
 * Waits until it drains if the FIFO is full.
 *
 * @param cChar The character to send.
 */
void uartSendChar(char cChar);

/**
 * @brief Sends a NUL-terminated string character by character.
 *
 * @param cpString The NUL-terminated string to send.
 */
void uartSendString(const char* cpString);

#endif /* UART_PS_H */
