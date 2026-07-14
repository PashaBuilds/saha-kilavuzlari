/* ============================================================
 * uart_ps.c — PS UART0 icin minimal, register seviyesinde surucu
 *
 * Adresler ve ofsetler UG1085 (Zynq UltraScale+ TRM) ve embeddedsw
 * xuartps_hw.h ile teyitlidir:
 *   UART0 taban adresi   : 0xFF00_0000
 *   SR  (Channel Status)  : ofset 0x2C
 *   FIFO (TX_RX)           : ofset 0x30
 *   XUARTPS_SR_TXFULL     : 0x10
 *
 * Bu dosya lab10-bugav'in bir parcasidir ve bilinen 4 hatadan hicbirini
 * icermez — mesele UART'ta degil, kesme/GPIO tarafinda.
 * ============================================================ */
#include "uart_ps.h"
#include "xil_io.h"

#define UART0_TABAN     0xFF000000U

#define UART_OFS_CR     0x00U   /* Control Register */
#define UART_OFS_MR     0x04U   /* Mode Register */
#define UART_OFS_SR     0x2CU   /* Channel Status Register */
#define UART_OFS_FIFO   0x30U   /* TX_RX FIFO */

#define UART_CR_TXRES   (1U << 2)   /* TX FIFO/mantigini sifirla */
#define UART_CR_RXRES   (1U << 1)   /* RX FIFO/mantigini sifirla */
#define UART_CR_TXEN    (1U << 4)   /* gonderici etkin */

#define UART_MR_8N1     0x00000020U  /* 8 veri biti, parite yok, 1 stop */

#define UART_SR_TXFULL  0x00000010U


static inline void uartRegWrite(unsigned int uiOffset, unsigned int uiValue)
{
    Xil_Out32(UART0_TABAN + uiOffset, uiValue);
}


static inline unsigned int uartRegRead(unsigned int uiOffset)
{
    return Xil_In32(UART0_TABAN + uiOffset);
}


/**
 * @brief UART0'i kullanima hazirlar.
 */
void uartInit(void)
{
    /* TX/RX FIFO'lari ve durum mantigini sifirla. */
    uartRegWrite(UART_OFS_CR, UART_CR_TXRES | UART_CR_RXRES);

    /* 8N1, normal mod. Baud hizi (115200) FSBL tarafindan acilista zaten
       ayarlandigi icin burada Baud Rate Generator/Divider'a dokunmuyoruz;
       yalnizca mod ve gonderici etkinlestirmesiyle ilgileniyoruz. */
    uartRegWrite(UART_OFS_MR, UART_MR_8N1);
    uartRegWrite(UART_OFS_CR, UART_CR_TXEN);
}


/**
 * @brief Tek bir karakteri UART0 TX FIFO'suna gonderir.
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
 * @brief Sifir sonlandirmali bir dizgiyi karakter karakter gonderir.
 */
void uartSendString(const char* cpString)
{
    while (*cpString != '\0')
    {
        uartSendChar(*cpString);
        cpString++;
    }
}
