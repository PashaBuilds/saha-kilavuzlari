/* ============================================================================
 * uart_ps.h — UART0 register seviyesi mini surucu modulu
 *
 * KOPYA NOTU: bu dosya lab02-uart/src/uart_ps.h'nin (Gorev 2 cozumu)
 * birebir kopyasidir. Her lab klasoru bagimsiz derlenebilsin diye
 * referans/sembolik baglanti yerine _gorev-zinciri.md sozlesmesi geregi
 * kopya tasinir. Icerik degismemistir.
 * ============================================================================ */
#ifndef UART_PS_H
#define UART_PS_H

#include "xil_types.h"

/**
 * @brief UART0'i kullanima hazirlar.
 *
 * NOT: bu fonksiyon baud hizini ya da cerceve bicimini (115200-8N1)
 * yeniden yapilandirmaz — kart acildiginda FSBL ve standalone BSP'nin
 * stdout kurulumu UART0'i zaten bu sekilde birakir (asagida uart_ps.c
 * dosya basligi yorumuna bak). Burada kendi modulumuzun kullandigi
 * register tabanini yalnizca "hazir" kabul ediyoruz.
 */
void uartInit(void);

/**
 * @brief UART0 TX FIFO'ya tek karakter gonderir.
 *
 * Gondermeden once FIFO'nun dolu olmamasini (TXFULL) bekler.
 *
 * @param cChar Gonderilecek karakter.
 */
void uartSendChar(char cChar);

/**
 * @brief Null ile sonlanan string'i karakter karakter gonderir.
 *
 * '\n' ile karsilastiginda once '\r' gonderir (uart_ps.c'deki
 * aciklamaya bak).
 *
 * @param cpString Gonderilecek, null ile sonlanan string.
 */
void uartSendString(const char* cpString);

#endif /* UART_PS_H */
