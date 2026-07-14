/*
 * main.c — Gorev 1 (Bolum 4): LED Yak (Merhaba Donanim)
 *
 * DS50 LED'ini (PS MIO23) XGpioPs surucusu ile 500 ms periyotla
 * yakip sondurur. DS50/SW19 ikilisi bu kartta bitstream'siz erisilebilen
 * TEK PS LED'i/butonudur (bkz. Bolum 2 ve Bolum 4) — 8 kullanici LED'i
 * (DS11-DS18) PL pinlerindedir, onlara Gorev 7'de (AXI GPIO ile) geliriz.
 *
 * Akis KLASIK Vitis yaklasimini kullanir: cihaz XPAR_..._DEVICE_ID ile
 * bulunur. Vitis Unified/SDT akisinda yerine
 *     XGpioPs_LookupConfig(XPAR_XGPIOPS_0_BASEADDR)
 * gelir — LookupConfig taban adresi dogrudan parametre olarak alir,
 * DEVICE_ID diye bir sey kalmaz. Iki desen de Bolum 4'te anlatildi.
 */

#include "xgpiops.h"
#include "xparameters.h"
#include "xil_printf.h"
#include "sleep.h"

/* DS50 LED'i PS MIO23'e bagli (UG1271, "GPIO (MIO 22-23)"). */
#define DS50_LED_PIN_MIO    23U

/* Basari kriteri: 500 ms acik / 500 ms kapali. */
#define LED_YANIP_SONME_US  500000U

int main(void)
{
    XGpioPs sGpio;
    XGpioPs_Config* spGpioConfig;
    int iStatus;

    /* 1. Adim: konfigurasyonu cihaz kimligiyle bul. */
    spGpioConfig = XGpioPs_LookupConfig(XPAR_XGPIOPS_0_DEVICE_ID);
    if (spGpioConfig == NULL)
    {
        xil_printf("HATA: GPIO konfigurasyonu bulunamadi.\r\n");
        return XST_FAILURE;
    }

    /* 2. Adim: surucuyu bu konfigurasyonla baslat. */
    iStatus = XGpioPs_CfgInitialize(&sGpio, spGpioConfig,
                                     spGpioConfig->BaseAddr);
    if (iStatus != XST_SUCCESS)
    {
        xil_printf("HATA: GPIO baslatilamadi (kod=%d).\r\n", iStatus);
        return XST_FAILURE;
    }

    /* 3. Adim: MIO23'u cikis yap ve cikis tamponunu etkinlestir.
     * Ikisi de gerekli: SetDirectionPin DIRM'i, SetOutputEnablePin OEN'i
     * ayarlar (bkz. Bolum 4 derin-dalis — main_registerli.c). */
    XGpioPs_SetDirectionPin(&sGpio, DS50_LED_PIN_MIO, 1U);
    XGpioPs_SetOutputEnablePin(&sGpio, DS50_LED_PIN_MIO, 1U);

    xil_printf("Gorev 1: DS50 500 ms periyotla yanip sonecek.\r\n");

    /* 4. Adim: sonsuz dongude yak-sondur. */
    for (;;)
    {
        XGpioPs_WritePin(&sGpio, DS50_LED_PIN_MIO, 1U);
        usleep(LED_YANIP_SONME_US);

        XGpioPs_WritePin(&sGpio, DS50_LED_PIN_MIO, 0U);
        usleep(LED_YANIP_SONME_US);
    }

    return XST_SUCCESS;
}
