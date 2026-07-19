/*
 * main_registers.c — Gorev 1 (Bolum 4) derin dalis: DS50 LED'ini
 * (MIO23) XGpioPs surucusu OLMADAN, dogrudan volatile pointer erisimi
 * ile yakip sondurme. Amac, XGpioPs_WritePin/SetDirectionPin/
 * SetOutputEnablePin cagrilarinin perde arkasinda tam olarak ne
 * yaptigini gostermektir.
 *
 * Register offset'leri (GPIO taban adresi 0xFF0A0000'e gore)
 * Xilinx/AMD embeddedsw xgpiops_hw.h uzerinden TEYIT edildi — kaynak
 * notu icin bkz. content/_arastirma-ek-B.md.
 *
 *   DIRM_0  (Bank 0 Direction Mode, R/W)  taban + 0x204
 *   OEN_0   (Bank 0 Output Enable,  R/W)  taban + 0x208
 *   DATA_0  (Bank 0 Data,           R/W)  taban + 0x040
 *
 * Bank 0 = MIO 0-25 (bkz. Bolum 4 / _arastirma.md SS5); DS50 = MIO23
 * oldugundan Bank 0 register'larinin 23. biti kullanilir.
 *
 * NOT: Bu dosya main.c ile AYNI projede derlenmez (ikisi de main()
 * tanimlar). Bu dosyayi ayri, bos bir uygulama projesine koy ve build
 * ederek ayni DS50 yanip sonme davranisini gozle.
 */

#include "xil_io.h"
#include "xil_types.h"
#include "xstatus.h"
#include "xil_printf.h"
#include "sleep.h"

/* Taban adres + Bank 0 offset'leri (bkz. dosya basligi yorumu). */
#define GPIO_BASE_ADDR    0xFF0A0000U
#define GPIO_DIRM_0_OFSET   0x00000204U
#define GPIO_OEN_0_OFSET    0x00000208U
#define GPIO_DATA_0_OFSET   0x00000040U

/* DS50, Bank 0'in 23. bitidir. */
#define DS50_LED_BIT_MIO    23U
#define DS50_LED_MASKE      (1U << DS50_LED_BIT_MIO)

#define LED_YANIP_SONME_US  500000U

int main(void)
{
    volatile unsigned int* uipDirm0 =
        (volatile unsigned int*)(GPIO_BASE_ADDR + GPIO_DIRM_0_OFSET);
    volatile unsigned int* uipOen0 =
        (volatile unsigned int*)(GPIO_BASE_ADDR + GPIO_OEN_0_OFSET);
    volatile unsigned int* uipData0 =
        (volatile unsigned int*)(GPIO_BASE_ADDR + GPIO_DATA_0_OFSET);

    /* Oku-degistir-yaz: Bank 0'daki diger 25 MIO pinine dokunmadan
     * YALNIZCA MIO23 bitini cikis yap. Dogrudan '=' ile yazmak bu
     * bank'taki her pinin yonunu ezerdi — Gorev 1'in "Kendini sina"
     * sorusu tam olarak bunu sorar. */
    *uipDirm0 |= DS50_LED_MASKE;
    *uipOen0  |= DS50_LED_MASKE;

    xil_printf("Task 1 (deep dive): DS50 via direct register access.\r\n");

    for (;;)
    {
        *uipData0 |= DS50_LED_MASKE;    /* DS50'yi yak, digerlerine dokunma */
        usleep(LED_YANIP_SONME_US);

        *uipData0 &= ~DS50_LED_MASKE;   /* DS50'yi sondur, digerlerine dokunma */
        usleep(LED_YANIP_SONME_US);
    }

    return XST_SUCCESS;
}
