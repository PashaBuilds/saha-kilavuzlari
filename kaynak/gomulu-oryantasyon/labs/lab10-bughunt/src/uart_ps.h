/* ============================================================
 * uart_ps.h — PS UART0 icin minimal, register seviyesi surucu
 *
 * lab10-bughunt (Gorev 10 - Bug Hunt) projesinin parcasi. Sozlesme,
 * Bolum 5 / Gorev 2'de ogrenilenle birebir aynidir:
 *   uartInit()            -> UART0'i 115200 8N1 icin hazirlar
 *   uartSendChar()        -> tek karakter gonderir (TX FIFO doluysa bekler)
 *   uartSendString()      -> '\0' ile biten string'i karakter karakter gonderir
 *
 * Bu lab bagimsiz derlenebilsin diye modul burada yeniden tanimlidir;
 * her lab klasoru kendi kopyasini tasir.
 * ============================================================ */
#ifndef UART_PS_H
#define UART_PS_H

#include "xil_types.h"

/**
 * @brief UART0'i kullanima hazirlar.
 */
void uartInit(void);

/**
 * @brief UART0 TX FIFO'ya tek karakter gonderir.
 *
 * FIFO doluysa bosalana kadar bekler.
 *
 * @param cChar Gonderilecek karakter.
 */
void uartSendChar(char cChar);

/**
 * @brief NUL ile sonlanan string'i karakter karakter gonderir.
 *
 * @param cpString Gonderilecek, NUL ile sonlanan string.
 */
void uartSendString(const char* cpString);

#endif /* UART_PS_H */
