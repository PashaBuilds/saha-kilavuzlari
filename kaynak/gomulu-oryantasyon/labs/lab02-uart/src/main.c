/* ============================================================================
 * main.c — GOREV 2 cozumu: UART "Hello World" ve printf'in arkasindaki sey
 *
 * Iki parcali gosterim:
 *   1) xil_printf ile tek satir — hazir, hafif printf'in zaten
 *      calistigini gozle.
 *   2) Kendi uart_ps modulunle (register seviyesi) cok satirli karsilama
 *      afisi — az once gordugun printf'in "arkasindakini" elinle kur.
 * ============================================================================ */

#include "xil_printf.h"
#include "uart_ps.h"

int main(void)
{
    /* xil_printf: standart printf'in gomulu dunyaya uyarlanmis hafif
     * varyanti. Format motoru standart printf kadar zengin degildir —
     * en somut fark: %f (float/double bicimleme) DESTEKLENMEZ. Sebep
     * boyut: float'i metne ceviren kod (yazilimsal kayan nokta
     * bicimleyici) bare-metal imaja onlarca KB ekler ve bizim dunyada
     * her KB'nin maliyeti vardir; Xilinx bu destegi bilerek disarida
     * birakmistir. Tamsayi ve string bicimleme (%d, %u, %x, %s, %c)
     * sorunsuz calisir. */
    xil_printf("xil_printf ready: UART0 already configured by the platform.\r\n");

    /* Kendi modulumuzu devreye al — dosya basligi yorumundaki nota
     * gore bu cagri baud/bicim ayarini yeniden yapmaz, yalnizca taban
     * adresi hazir ilan eder. */
    uartInit();

    uartSendString("\n");
    uartSendString("========================================\n");
    uartSendString("  Welcome to the team - ZCU111 / PS UART0\n");
    uartSendString("  These lines were printed by your uart_ps module.\n");
    uartSendString("  The TXFULL bit was checked, and data was written to the FIFO.\n");
    uartSendString("========================================\n");
    uartSendString("\n");

    /* Bare-metal'de main asla donmez; gercek bir uygulamada ana is
     * dongusu (ya da sonraki gorevin polling dongusu) burada baslardi. */
    while (1)
    {
        ;
    }

    return 0;
}
