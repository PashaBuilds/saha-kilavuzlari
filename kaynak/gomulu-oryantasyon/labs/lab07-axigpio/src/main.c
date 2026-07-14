/*
 * lab07-axigpio / main.c
 *
 * GOREV 7 -- "PL'deki IP ile Konus" cozumu.
 *
 * Ekipce saglanan bitstream/.xsa'da bir AXI GPIO IP'si PL'deki 8 kullanici
 * LED'ine (DS11-DS18, net adi GPIO_LED[7:0]) baglidir. Bu dosya, o IP'nin
 * register'larina PS'ten dogrudan volatile pointer ile erisip 8 LED'de
 * soldan saga yuruyen isik olusturur.
 *
 * Register haritasi (kaynak: AMD/Xilinx PG144, AXI GPIO v2.0 -- ofsetler
 * content/_arastirma-ek-E.md'de web ile teyitli):
 *   GPIO_DATA  ofset 0x0000  -- veri: yazinca cikis degeri, okununca giris
 *   GPIO_TRI   ofset 0x0004  -- yon: bit=0 CIKIS, bit=1 GIRIS
 *
 * PS GPIO (Gorev 1, taban adresi silikonda sabit 0xFF0A0000) ile fark:
 * buradaki taban adres donanimcinin Vivado Address Editor'da bu IP'ye
 * verdigi penceredir; kart degisse de silikon degismez ama bu adres
 * tasarimdan tasarima degisebilir. Adresi asla elle uydurma -- her zaman
 * projenin kendi xparameters.h'inden al (bkz. README.md Adim 2).
 */

#include "xparameters.h"
#include "xil_io.h"
#include "xil_printf.h"
#include "sleep.h"

/* AXI GPIO taban adresi: xparameters.h'ten proje derlenince otomatik
 * gelir. Instance adi donanimciya gore degisir -- bu lab'da IP Vivado'da
 * "axi_gpio_0" olarak adlandirildigi varsayildi. Kendi projende farkli
 * bir isim gorursen (ornegin "led_gpio"), makro adi da XPAR_LED_GPIO_...
 * seklinde degisir; Gorev 7'nin "kendini sina" sorusu tam bunu sorguluyor. */
#define AXI_GPIO_0_TABAN        XPAR_AXI_GPIO_0_BASEADDR

#define AXI_GPIO_OFSET_DATA     0x0000U
#define AXI_GPIO_OFSET_TRI      0x0004U

#define LED_MASKE_TUMU          0xFFU     /* GPIO_LED[7:0], 8 bit */
#define YURUYEN_ISIK_GECIKME_US 150000U   /* 150 ms basamak arasi */


/* axigpioSetDirection -- verilen kanaldaki bitleri cikis olarak kurar.
 * TRI'de bit=0 CIKIS demektir; cikis istedigimiz LED bitlerini 0'lariz. */
static void
axigpioSetDirection(unsigned int uiBase, unsigned int uiOutputMask)
{
    Xil_Out32(uiBase + AXI_GPIO_OFSET_TRI, ~uiOutputMask & LED_MASKE_TUMU);
}

/* axigpioWriteData -- DATA register'ina dogrudan yazar. */
static void
axigpioWriteData(unsigned int uiBase, unsigned int uiValue)
{
    Xil_Out32(uiBase + AXI_GPIO_OFSET_DATA, uiValue);
}


int main(void)
{
    unsigned char ucIndex;
    unsigned int  uiPattern;

    xil_printf("\r\n--- Gorev 7: PL AXI GPIO ile Yuruyen Isik ---\r\n");
    xil_printf("AXI GPIO taban adresi: 0x%08X\r\n", (unsigned int)AXI_GPIO_0_TABAN);

    /* Once yon: 8 bitin hepsi cikis. Bunu unutursan LED'ler hic yanmaz --
     * TRI'nin gucu ve tuzagi bir aradadir (Gorev 7 "kendini sina"). */
    axigpioSetDirection(AXI_GPIO_0_TABAN, LED_MASKE_TUMU);

    for (;;)
    {
        for (ucIndex = 0U; ucIndex < 8U; ucIndex++)
        {
            uiPattern = (unsigned int)(1U << ucIndex);
            axigpioWriteData(AXI_GPIO_0_TABAN, uiPattern);
            xil_printf("LED deseni: 0x%02X\r\n", (unsigned int)uiPattern);
            usleep(YURUYEN_ISIK_GECIKME_US);
        }
    }

    return 0;
}

/*
 * Derin dalis -- ayni is, hazir surucuyle:
 *
 * Xilinx'in XGpio surucusu (PL'deki AXI GPIO icin -- PS GPIO'nun XGpioPs'i
 * degil, ismi benzer ama ayri bir surucu ailesidir) yukaridaki iki
 * fonksiyonu senin yerine yapar:
 *
 *   #include "xgpio.h"
 *   XGpio sLedGpio;
 *   XGpio_Initialize(&sLedGpio, XPAR_AXI_GPIO_0_DEVICE_ID);
 *   XGpio_SetDataDirection(&sLedGpio, 1, ~LED_MASKE_TUMU & LED_MASKE_TUMU);
 *   XGpio_DiscreteWrite(&sLedGpio, 1, uiPattern);
 *
 * "1" parametresi kanal numarasi (bu IP tek kanal calisiyor; cift kanal
 * acilirsa GPIO2_DATA/GPIO2_TRI icin kanal "2" kullanilir). Perde arkasinda
 * XGpio_SetDataDirection de TRI'ye, XGpio_DiscreteWrite de DATA'ya ayni
 * ofsetlerle yazar -- surucu, register haritasini senin yerine hatirlar,
 * ama register'in ne oldugunu bir kez elle gormeden surucuye korukorune
 * guvenmek bu meslekte iyi bir aliskanlik degildir.
 */
