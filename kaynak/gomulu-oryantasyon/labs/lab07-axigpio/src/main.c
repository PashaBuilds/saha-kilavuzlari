/*
 * lab07-axigpio / main.c
 *
 * GOREV 7 -- "PL'deki Bir IP Bloguyla Konus" cozumu.
 *
 * Ekibin sagladigi bitstream/.xsa icinde bir AXI GPIO IP blogu, PL'in
 * 8 kullanici LED'ine (DS11-DS18, net adi GPIO_LED[7:0]) baglidir. Bu
 * dosya o IP'nin register'larina PS'ten volatile pointer ile dogrudan
 * erisir ve 8 LED uzerinde soldan saga yuruyen bir isik uretir.
 *
 * Register haritasi (kaynak: AMD/Xilinx PG144, AXI GPIO v2.0 --
 * offset'ler content/_arastirma-ek-E.md'de web aramasiyla teyitli):
 *   GPIO_DATA  offset 0x0000  -- veri: yazilan deger cikis, okunan
 *                                 deger giristir
 *   GPIO_TRI   offset 0x0004  -- yon: bit=0 CIKIS, bit=1 GIRIS
 *
 * PS GPIO'dan (Gorev 1, taban adresi silikonda 0xFF0A0000'e sabit)
 * farki: buradaki taban adres, donanim tasarimcisinin Vivado'nun
 * Address Editor'unde bu IP'ye atadigi penceredir -- kart degisse de
 * silikonda sabit kalmaz; tasarimdan tasarima degisebilir. Adresi asla
 * elle hard-code etme -- her zaman projenin kendi xparameters.h'inden
 * al (bkz. README.md Adim 2).
 */

#include "xparameters.h"
#include "xil_io.h"
#include "xil_printf.h"
#include "sleep.h"

/* AXI GPIO taban adresi: proje build edilince xparameters.h'den
 * otomatik gelir. Instance adi donanim tasarimcisina gore degisir --
 * bu lab'de IP'nin Vivado'da "axi_gpio_0" adiyla anildigi varsayilir.
 * Kendi projende farkli bir ad gorursen (orn. "led_gpio"), makro adi
 * buna gore XPAR_LED_GPIO_... olur; Gorev 7'nin "kendini sina" sorusu
 * tam olarak bunu sorar. */
#define AXI_GPIO_0_BASE_ADDR        XPAR_AXI_GPIO_0_BASEADDR

#define AXI_GPIO_OFSET_DATA     0x0000U
#define AXI_GPIO_OFSET_TRI      0x0004U

#define LED_MASKE_TUMU          0xFFU     /* GPIO_LED[7:0], 8 bit */
#define RUNNING_LIGHT_DELAY_US 150000U   /* adimlar arasi 150 ms */


/* axigpioSetDirection -- verilen kanaldaki bitleri cikis yapar. TRI'de
 * bit=0 CIKIS demektir; cikis istedigimiz LED bitlerini 0'a ceker. */
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

    xil_printf("\r\n--- Task 7: Walking Light on PL AXI GPIO ---\r\n");
    xil_printf("AXI GPIO base address: 0x%08X\r\n", (unsigned int)AXI_GPIO_0_BASE_ADDR);

    /* Once yon: 8 bitin tumu cikis. Bunu unutursan LED'ler hic yanmaz
     * -- TRI'nin gucu ile tuzagi el eledir (Gorev 7 "kendini sina"). */
    axigpioSetDirection(AXI_GPIO_0_BASE_ADDR, LED_MASKE_TUMU);

    for (;;)
    {
        for (ucIndex = 0U; ucIndex < 8U; ucIndex++)
        {
            uiPattern = (unsigned int)(1U << ucIndex);
            axigpioWriteData(AXI_GPIO_0_BASE_ADDR, uiPattern);
            xil_printf("LED pattern: 0x%02X\r\n", (unsigned int)uiPattern);
            usleep(RUNNING_LIGHT_DELAY_US);
        }
    }

    return 0;
}

/*
 * Derin dalis -- ayni is, hazir surucuyle:
 *
 * Xilinx'in XGpio surucusu (PL'deki AXI GPIO icin -- PS GPIO'nun
 * XGpioPs'i degil; adlari benzer ama ayri bir surucu ailesi) yukaridaki
 * iki fonksiyonu senin yerine yapar:
 *
 *   #include "xgpio.h"
 *   XGpio sLedGpio;
 *   XGpio_Initialize(&sLedGpio, XPAR_AXI_GPIO_0_DEVICE_ID);
 *   XGpio_SetDataDirection(&sLedGpio, 1, ~LED_MASKE_TUMU & LED_MASKE_TUMU);
 *   XGpio_DiscreteWrite(&sLedGpio, 1, uiPattern);
 *
 * "1" parametresi kanal numarasidir (bu IP tek kanal calisir; dual
 * channel etkinse GPIO2_DATA/GPIO2_TRI icin kanal "2" kullanilir).
 * Perde arkasinda XGpio_SetDataDirection TRI'ye, XGpio_DiscreteWrite
 * DATA'ya ayni offset'lerle yazar -- register haritasini surucu senin
 * yerine ezberler; ama register'in ne oldugunu bir kez olsun gormeden
 * surucuye koru korune guvenmek bu meslekte iyi bir aliskanlik degildir.
 */
