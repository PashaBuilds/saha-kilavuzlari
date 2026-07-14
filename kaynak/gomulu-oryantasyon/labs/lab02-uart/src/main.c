/* ============================================================================
 * main.c — GÖREV 2 çözümü: UART "Merhaba Dünya" ve printf'in arkası
 *
 * İki bölümlü gösteri:
 *   1) xil_printf ile tek satır — hazır, hafif printf'in zaten çalıştığını
 *      gör.
 *   2) uart_ps modülünle (register seviyesi) çok satırlı bir karşılama
 *      ekranı — az önce gördüğün printf'in "arkasında" ne olduğunu elinle
 *      yap.
 * ============================================================================ */

#include "xil_printf.h"
#include "uart_ps.h"

int main(void)
{
    /* xil_printf: standart printf'in gömülü dünyaya özel, hafifletilmiş
     * hâli. Format motoru standart printf kadar zengin değildir — en somut
     * fark: %f (float/double biçimlendirme) DESTEKLENMEZ. Nedeni boyut:
     * float'ı metne çevirme kodu (yazılım kayan nokta biçimlendirici)
     * bare-metal bir imgeye onlarca KB ekler; bizim dünyamızda her KB'nin
     * bir bedeli var, bu yüzden Xilinx bu desteği bilerek çıkarmış. Tamsayı
     * ve dizgi biçimlendirme (%d, %u, %x, %s, %c) sorunsuz çalışır. */
    xil_printf("xil_printf hazir: UART0 platform tarafindan zaten ayarli.\r\n");

    /* Kendi modülümüzü devreye alıyoruz — dosya başı yorumundaki dürüst nota
     * göre bu, baud/format'ı yeniden kurmuyor, sadece taban adresi hazır
     * ilan ediyor. */
    uartInit();

    uartSendString("\n");
    uartSendString("========================================\n");
    uartSendString("  Ekibe hos geldin - ZCU111 / PS UART0\n");
    uartSendString("  Bu satirlari senin uart_ps modulun bastı.\n");
    uartSendString("  TXFULL biti kontrol edildi, FIFO'ya yazildi.\n");
    uartSendString("========================================\n");
    uartSendString("\n");

    /* Bare-metal'de main geri dönmez; gerçek bir uygulamada burada asıl iş
     * döngüsü (ya da bir sonraki görevin polling döngüsü) başlardı. */
    while (1)
    {
        ;
    }

    return 0;
}
