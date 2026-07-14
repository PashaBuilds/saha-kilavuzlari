/* ============================================================
 * uart_ps.h — PS UART0 icin minimal, register seviyesinde surucu
 *
 * lab10-bugav (Gorev 10 - Bug Avi) projesinin bir parcasi. Sozlesme
 * Bolum 5 / Gorev 2'de ogrenilenle birebir aynidir:
 *   uartInit()            -> UART0'i 115200 8N1 icin hazirlar
 *   uartSendChar()        -> tek karakter yollar (TX FIFO dolu ise bekler)
 *   uartSendString()      -> '\0' ile biten dizgiyi tek tek yollar
 *
 * Bu lab kendi basina derlenebilsin diye modul burada tekrar tanimlandi;
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
 * @brief Tek bir karakteri UART0 TX FIFO'suna gonderir.
 *
 * FIFO doluysa bosalana kadar bekler.
 *
 * @param cChar Gonderilecek karakter.
 */
void uartSendChar(char cChar);

/**
 * @brief Sifir sonlandirmali bir dizgiyi karakter karakter gonderir.
 *
 * @param cpString Gonderilecek, sifir sonlandirmali dizgi.
 */
void uartSendString(const char* cpString);

#endif /* UART_PS_H */
