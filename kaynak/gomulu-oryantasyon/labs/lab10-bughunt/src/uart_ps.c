/* ============================================================
 * uart_ps.c — PS UART0 icin minimal, register seviyesi surucu
 *
 * Adresler ve offset'ler UG1085 (Zynq UltraScale+ TRM) ve embeddedsw
 * xuartps_hw.h ile teyitlidir:
 *   UART0 taban adresi    : 0xFF00_0000
 *   SR  (Channel Status)  : offset 0x2C
 *   FIFO (TX_RX)          : offset 0x30
 *   XUARTPS_SR_TXFULL     : 0x10
 *
 * Bu dosya lab10-bughunt'in parcasidir ve bilinen 4 hatanin hicbirini
 * icermez — sorun UART'ta degil, interrupt/GPIO tarafindadir.
 * ============================================================ */
#include "uart_ps.h"
#include "xil_io.h"

#define UART0_BASE_ADDR     0xFF000000U

#define UART_OFS_CR     0x00U   /* Control Register */
#define UART_OFS_MR     0x04U   /* Mode Register */
#define UART_OFS_SR     0x2CU   /* Channel Status Register */
#define UART_OFS_FIFO   0x30U   /* TX_RX FIFO */

#define UART_CR_TXRES   (1U << 2)   /* TX FIFO/mantigini sifirla */
#define UART_CR_RXRES   (1U << 1)   /* RX FIFO/mantigini sifirla */
#define UART_CR_TXEN    (1U << 4)   /* verici etkin */

#define UART_MR_8N1     0x00000020U  /* 8 veri biti, parity yok, 1 stop */

#define UART_SR_TXFULL  0x00000010U


static inline void uartRegWrite(unsigned int uiOffset, unsigned int uiValue)
{
    Xil_Out32(UART0_BASE_ADDR + uiOffset, uiValue);
}


static inline unsigned int uartRegRead(unsigned int uiOffset)
{
    return Xil_In32(UART0_BASE_ADDR + uiOffset);
}


/**
 * @brief UART0'i kullanima hazirlar.
 */
void uartInit(void)
{
    /* TX/RX FIFO'larini ve durum mantigini sifirla. */
    uartRegWrite(UART_OFS_CR, UART_CR_TXRES | UART_CR_RXRES);

    /* 8N1, normal mod. Baud hizi (115200) acilista FSBL tarafindan
       zaten ayarlandigi icin burada Baud Rate Generator/Divider'a
       dokunmuyoruz; yalnizca mod ve vericinin etkinlestirilmesiyle
       ilgileniyoruz. */
    uartRegWrite(UART_OFS_MR, UART_MR_8N1);
    uartRegWrite(UART_OFS_CR, UART_CR_TXEN);
}


/**
 * @brief UART0 TX FIFO'ya tek karakter gonderir.
 */
void uartSendChar(char cChar)
{
    /* TX FIFO doluyken burada bekle. */
    while ((uartRegRead(UART_OFS_SR) & UART_SR_TXFULL) != 0U)
    {
        /* bos govde: FIFO'nun bosalmasini bekliyoruz */
    }

    uartRegWrite(UART_OFS_FIFO, (unsigned int)cChar);
}


/**
 * @brief NUL ile sonlanan string'i karakter karakter gonderir.
 */
void uartSendString(const char* cpString)
{
    while (*cpString != '\0')
    {
        uartSendChar(*cpString);
        cpString++;
    }
}
