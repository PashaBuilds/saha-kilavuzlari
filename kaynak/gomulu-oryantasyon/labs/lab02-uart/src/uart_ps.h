/* ============================================================================
 * uart_ps.h — UART0 register-seviyesi mini sürücü modülü (GÖREV 2 çözümü)
 *
 * xil_printf'in ve XUartPs sürücüsünün arkasında ne olduğunu göstermek için
 * PS UART0'ı doğrudan register erişimiyle konuşturan üç fonksiyon.
 * API imzaları _gorev-zinciri.md'deki sözleşmeyle birebir aynıdır; lab03+
 * bu dosyanın bir kopyasını taşır (bkz. o labın README'si).
 * ============================================================================ */
#ifndef UART_PS_H
#define UART_PS_H

#include "xil_types.h"

/**
 * @brief UART0'ı kullanıma hazırlar.
 *
 * DÜRÜST NOT: bu fonksiyon baud hızını / kare formatını (115200-8N1) YENİDEN
 * KURMAZ — kart açılırken FSBL ve standalone BSP'nin stdout ayarı UART0'ı
 * zaten bu ayarla bırakmış durumdadır (aşağıdaki uart_ps.c dosya başı
 * yorumuna bak). Biz burada sadece kendi modülümüzün kullanacağı register
 * tabanını "hazır" sayıyoruz.
 */
void uartInit(void);

/**
 * @brief Tek bir karakteri UART0 TX FIFO'suna gönderir.
 *
 * FIFO doluysa (TXFULL) boşalana kadar bekler.
 *
 * @param cChar Gönderilecek karakter.
 */
void uartSendChar(char cChar);

/**
 * @brief Sıfır sonlandırmalı bir dizgiyi karakter karakter gönderir.
 *
 * '\n' gördüğünde önce '\r' gönderir (bkz. uart_ps.c'deki açıklama).
 *
 * @param cpString Gönderilecek, sıfır sonlandırmalı dizgi.
 */
void uartSendString(const char* cpString);

#endif /* UART_PS_H */
