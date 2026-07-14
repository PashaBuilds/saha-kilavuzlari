/*
 * main_registerli.c — Gorev 1 (Bolum 4) derin-dalis: XGpioPs surucusu
 * OLMADAN, dogrudan volatile pointer ile DS50 LED'ini (MIO23) yakip
 * sondurme. XGpioPs_WritePin/SetDirectionPin/SetOutputEnablePin'in
 * perde arkasinda tam olarak bunu yaptigini gormek icindir.
 *
 * Register ofsetleri (GPIO tabani 0xFF0A0000'e gore), Xilinx/AMD
 * embeddedsw xgpiops_hw.h'den DOGRULANDI — kaynakli not:
 * content/_arastirma-ek-B.md.
 *
 *   DIRM_0  (Bank 0 Direction Mode, R/W)  taban + 0x204
 *   OEN_0   (Bank 0 Output Enable,  R/W)  taban + 0x208
 *   DATA_0  (Bank 0 Data,           R/W)  taban + 0x040
 *
 * Bank 0 = MIO 0-25 (bkz. Bolum 4 / _arastirma.md SS5); DS50 = MIO23
 * oldugu icin Bank 0 register'larinin 23. biti kullanilir.
 *
 * DIKKAT: Bu dosya main.c ile AYNI projede derlenmez (ikisi de main()
 * tanimliyor). Ayri, bos bir uygulama projesine bu dosyayi koyup
 * derersen ayni DS50 yanip sonme davranisini gorursun.
 */

#include "xil_io.h"
#include "xil_types.h"
#include "xstatus.h"
#include "xil_printf.h"
#include "sleep.h"

/* Taban adres + Bank 0 ofsetleri (bkz. dosya basi yorumu). */
#define GPIO_TABAN_ADRES    0xFF0A0000U
#define GPIO_DIRM_0_OFSET   0x00000204U
#define GPIO_OEN_0_OFSET    0x00000208U
#define GPIO_DATA_0_OFSET   0x00000040U

/* DS50, Bank 0'in 23. biti. */
#define DS50_LED_BIT_MIO    23U
#define DS50_LED_MASKE      (1U << DS50_LED_BIT_MIO)

#define LED_YANIP_SONME_US  500000U

int main(void)
{
    volatile unsigned int* uipDirm0 =
        (volatile unsigned int*)(GPIO_TABAN_ADRES + GPIO_DIRM_0_OFSET);
    volatile unsigned int* uipOen0 =
        (volatile unsigned int*)(GPIO_TABAN_ADRES + GPIO_OEN_0_OFSET);
    volatile unsigned int* uipData0 =
        (volatile unsigned int*)(GPIO_TABAN_ADRES + GPIO_DATA_0_OFSET);

    /* Oku-degistir-yaz: SADECE MIO23 bitini cikis yap, Bank 0'daki
     * diger 25 MIO pinine dokunma. Dogrudan '=' yazsaydik bu bank'taki
     * butun pinlerin yonunu ezerdik — Gorev 1'in "Kendini sina"
     * sorusu tam olarak bunu sorguluyor. */
    *uipDirm0 |= DS50_LED_MASKE;
    *uipOen0  |= DS50_LED_MASKE;

    xil_printf("Gorev 1 (derin dalis): dogrudan register erisimi ile DS50.\r\n");

    for (;;)
    {
        *uipData0 |= DS50_LED_MASKE;    /* DS50 yak, digerlerine dokunma */
        usleep(LED_YANIP_SONME_US);

        *uipData0 &= ~DS50_LED_MASKE;   /* DS50 sondur, digerlerine dokunma */
        usleep(LED_YANIP_SONME_US);
    }

    return XST_SUCCESS;
}
