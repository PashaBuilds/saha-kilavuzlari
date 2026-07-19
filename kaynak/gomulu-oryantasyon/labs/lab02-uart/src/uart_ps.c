/* ============================================================================
 * uart_ps.c — UART0 register seviyesi mini surucu modulu (GOREV 2 cozumu)
 *
 * Adresler ve bit maskeleri dogrudan content/_arastirma.md'den alinmistir
 * (UG1085 Tablo 10-6 + embeddedsw xuartps_hw.h):
 *   UART0 taban adresi   : 0xFF00_0000
 *   SR  (Channel Status) : offset 0x2C, RO
 *   FIFO (TX_RX FIFO)    : offset 0x30
 *   SR bit4 = TXFULL     : maske 0x10
 *
 * NOT (Bolum 5'te de aciklanir): kart acildiginda FSBL/BSP, UART0'i
 * zaten 115200-8N1 yapilandirilmis birakir (xil_printf'in hicbir ek
 * ayar olmadan calismasi bunun kanitidir). Buradaki uartInit(),
 * baud/bicim register'larina (CR/MR/Baud Rate Generator) DOKUNMAZ;
 * yalnizca bu modulun kullandigi register tabanini "hazir" ilan eder.
 * Sifirdan gercek bir init gerekirse (orn. UART1'i de ayaga kaldirmak
 * icin), eklenecegi yer burasidir.
 * ============================================================================ */

#include "uart_ps.h"

/* ---- UART0 taban adresi ve register offset'leri ---- */
#define UART0_BASE_ADDR   0xFF000000U
#define UART_OFS_SR         0x0000002CU   /* Channel Status Register, RO */
#define UART_OFS_FIFO       0x00000030U   /* TX_RX FIFO */
#define UART_SR_TXFULL      0x00000010U   /* SR bit4: TX FIFO dolu */

/* Volatile pointer ile register erisimi — Bolum 5'teki kalip: "sabit
 * bir adresi isaret et, oradan oku/yaz ve derleyicinin okumayi optimize
 * edip atmasina asla izin verme". Taban + offset, Bolum 4'teki formulun
 * ta kendisi. */
#define UART0_SR    (*(volatile unsigned int*)(UART0_BASE_ADDR + UART_OFS_SR))
#define UART0_FIFO  (*(volatile unsigned int*)(UART0_BASE_ADDR + UART_OFS_FIFO))

/**
 * @brief UART0'i kullanima hazirlar.
 */
void uartInit(void)
{
    /* Bilerek bos: dosya basligi yorumundaki nota bak. Fonksiyonu yine
     * de tutuyoruz ki main.c her modulde ayni "once ilklendir, sonra
     * kullan" akisini tek bicimde cagirabilsin — gercek bir init
     * gerekirse degistirilecek tek yer burasi. */
}

/**
 * @brief UART0 TX FIFO'ya tek karakter gonderir.
 */
void uartSendChar(char cChar)
{
    /* TXFULL biti temizlenene kadar bekle (polling — bu teknige resmi
     * adini Bolum 7'de verecegiz). Dolu FIFO'ya yazmak veri kaybettirir;
     * sonsuz dongude takilma riskini bilerek kabul ediyoruz cunku
     * buradaki donanim "hayir" demeyecek kadar guvenilirdir — TX FIFO
     * her zaman bosalir. */
    while ((UART0_SR & UART_SR_TXFULL) == UART_SR_TXFULL)
    {
        ;
    }

    UART0_FIFO = (unsigned int)cChar;
}

/**
 * @brief Null ile sonlanan string'i karakter karakter gonderir.
 */
void uartSendString(const char* cpString)
{
    while (*cpString != '\0')
    {
        /* Seri terminaller '\n' karakterini "bir satir asagi in, ayni
         * sutunda kal" (line feed) diye yorumlar; imleci gercekten sol
         * kenara dondurmek icin '\r' (carriage return) de gondermek
         * gerekir. Standart printf ailesi bu cevirimi host tarafinda
         * senin yerine yapar; burada ciplak UART ile konustugumuz icin
         * kendimiz hallediyoruz. */
        if (*cpString == '\n')
        {
            uartSendChar('\r');
        }

        uartSendChar(*cpString);
        cpString++;
    }
}
