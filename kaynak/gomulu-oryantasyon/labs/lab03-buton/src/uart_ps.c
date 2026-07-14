/* ============================================================================
 * uart_ps.c — UART0 register-seviyesi mini sürücü modülü
 *
 * KOPYA NOTU: bu dosya lab02-uart/src/uart_ps.c'nin birebir kopyasıdır
 * (GÖREV 2'nin çözümü). Her lab klasörü bağımsız derlenebilsin diye kopya
 * taşınır; içerik değişmedi.
 *
 * Adresler ve bit maskeleri content/_arastirma.md'den (UG1085 Table 10-6 +
 * embeddedsw xuartps_hw.h) birebir alınmıştır:
 *   UART0 taban adresi   : 0xFF00_0000
 *   SR  (Channel Status) : offset 0x2C, RO
 *   FIFO (TX_RX FIFO)    : offset 0x30
 *   SR bit4 = TXFULL     : maske 0x10
 *
 * DÜRÜST NOT (bölüm 5'te de anlatılıyor): kart açılırken FSBL/BSP zaten
 * UART0'ı 115200-8N1'e ayarlamış durumda bırakır (xil_printf'in hiçbir ek
 * ayar yapmadan çalışması bunun kanıtıdır). uartInit() burada baud/format
 * yazmaçlarına (CR/MR/Baud Rate Generator) DOKUNMAZ; sadece bu modülün
 * kullanacağı register tabanını "hazır" ilan eder. Gerçek bir sıfırdan init
 * gerekirse (örn. UART1'i de açmak istersen) eklenecek yer burasıdır.
 * ============================================================================ */

#include "uart_ps.h"

/* ---- UART0 taban adresi ve yazmaç ofsetleri ---- */
#define UART0_TABAN_ADRES   0xFF000000U
#define UART_OFS_SR         0x0000002CU   /* Channel Status Register, RO */
#define UART_OFS_FIFO       0x00000030U   /* TX_RX FIFO */
#define UART_SR_TXFULL      0x00000010U   /* SR bit4: TX FIFO dolu */

/* Register'a volatile pointer ile erişim — Bölüm 5'te gördüğün desen:
 * "sabit bir adresi göster, oradan oku/yaz, derleyici bu okumayı ASLA
 * silmesin". Taban + offset toplamı Bölüm 4'teki formülün ta kendisi. */
#define UART0_SR    (*(volatile unsigned int*)(UART0_TABAN_ADRES + UART_OFS_SR))
#define UART0_FIFO  (*(volatile unsigned int*)(UART0_TABAN_ADRES + UART_OFS_FIFO))

/**
 * @brief UART0'ı kullanıma hazırlar.
 */
void uartInit(void)
{
    /* Bilerek boş: dosya başı yorumundaki dürüst nota bak. Fonksiyonu yine
     * de burada tutuyoruz ki main.c "önce baslat, sonra kullan" akışını
     * her modülde aynı şekilde çağırsın — yarın gerçek bir init eklemek
     * istediğinde tek değişiklik yeri burası olur. */
}

/**
 * @brief Tek bir karakteri UART0 TX FIFO'suna gönderir.
 */
void uartSendChar(char cChar)
{
    /* TXFULL biti düşene kadar bekle (polling — Bölüm 7'de adını koyacağız).
     * Dolu FIFO'ya yazmak veri kaybettirir; sonsuz döngüde takılma riskini
     * bile bile göze alıyoruz çünkü donanım burada asla "hayır" demeyecek
     * kadar güvenilir — TX her zaman boşalır. */
    while ((UART0_SR & UART_SR_TXFULL) == UART_SR_TXFULL)
    {
        ;
    }

    UART0_FIFO = (unsigned int)cChar;
}

/**
 * @brief Sıfır sonlandırmalı bir dizgiyi karakter karakter gönderir.
 */
void uartSendString(const char* cpString)
{
    while (*cpString != '\0')
    {
        /* Seri terminaller '\n'i "aynı sütunda bir alt satır" (line feed)
         * olarak yorumlar; satırın gerçekten sola dönmesi için ayrıca
         * '\r' (carriage return) göndermemiz gerekir. Standart printf
         * ailesi bu çeviriyi senin için host tarafında yapar; biz burada
         * çıplak UART'la konuştuğumuz için işi kendimiz üstleniyoruz. */
        if (*cpString == '\n')
        {
            uartSendChar('\r');
        }

        uartSendChar(*cpString);
        cpString++;
    }
}
