/* ============================================================================
 * uart_ps.c — UART0 register-seviyesi mini sürücü modülü (GÖREV 2 çözümü)
 *
 * lab02-uart'tan birebir kopyadır. Adresler ve bit maskeleri
 * content/_arastirma.md'den (UG1085 Table 10-6 + embeddedsw xuartps_hw.h):
 *   UART0 taban adresi   : 0xFF00_0000
 *   SR  (Channel Status) : offset 0x2C, RO
 *   FIFO (TX_RX FIFO)    : offset 0x30
 *   SR bit4 = TXFULL     : maske 0x10
 * ============================================================================ */

#include "uart_ps.h"

#define UART0_TABAN_ADRES   0xFF000000U
#define UART_OFS_SR         0x0000002CU   /* Channel Status Register, RO */
#define UART_OFS_FIFO       0x00000030U   /* TX_RX FIFO */
#define UART_SR_TXFULL      0x00000010U   /* SR bit4: TX FIFO dolu */

#define UART0_SR    (*(volatile unsigned int*)(UART0_TABAN_ADRES + UART_OFS_SR))
#define UART0_FIFO  (*(volatile unsigned int*)(UART0_TABAN_ADRES + UART_OFS_FIFO))

void uartInit(void)
{
    /* Bilerek boş — bkz. uart_ps.h dosya başı notu: FSBL/BSP UART0'ı
     * zaten 115200-8N1'e ayarlamış bırakır. */
}

void uartSendChar(char cChar)
{
    while ((UART0_SR & UART_SR_TXFULL) == UART_SR_TXFULL)
    {
        ;
    }

    UART0_FIFO = (unsigned int)cChar;
}

void uartSendString(const char* cpString)
{
    while (*cpString != '\0')
    {
        if (*cpString == '\n')
        {
            uartSendChar('\r');
        }

        uartSendChar(*cpString);
        cpString++;
    }
}
