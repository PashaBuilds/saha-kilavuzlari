/*
 * main.c — Gorev 1 (Bolum 4): LED'i Yak (Merhaba Donanim)
 *
 * DS50 LED'ini (PS MIO23) XGpioPs surucusuyle 500 ms periyotla yakip
 * sondurur. DS50/SW19 cifti bu kartta bitstream olmadan erisilebilen
 * TEK PS LED/buton ikilisidir (bkz. Bolum 2 ve Bolum 4) — 8 kullanici
 * LED'i (DS11-DS18) PL pinlerindedir; onlara Gorev 7'de (AXI GPIO ile)
 * donecegiz.
 *
 * Akis KLASIK Vitis yaklasimini kullanir: aygit XPAR_..._DEVICE_ID ile
 * bulunur. Vitis Unified/SDT akisinda bunun yerini
 *     XGpioPs_LookupConfig(XPAR_XGPIOPS_0_BASEADDR)
 * alir — LookupConfig taban adresi dogrudan parametre olarak alir ve
 * DEVICE_ID diye bir sey yoktur. Iki kalip da Bolum 4'te aciklanir.
 */

#include "xgpiops.h"
#include "xparameters.h"
#include "xil_printf.h"
#include "sleep.h"

/* DS50 LED'i PS MIO23'e baglidir (UG1271, "GPIO (MIO 22-23)"). */
#define DS50_LED_PIN_MIO    23U

/* Basari kriteri: 500 ms yanik / 500 ms sonuk. */
#define LED_YANIP_SONME_US  500000U

int main(void)
{
    XGpioPs sGpio;
    XGpioPs_Config* spGpioConfig;
    int iStatus;

    /* Adim 1: konfigurasyonu aygit ID'siyle bul. */
    spGpioConfig = XGpioPs_LookupConfig(XPAR_XGPIOPS_0_DEVICE_ID);
    if (spGpioConfig == NULL)
    {
        xil_printf("ERROR: GPIO configuration not found.\r\n");
        return XST_FAILURE;
    }

    /* Adim 2: surucuyu bu konfigurasyonla ilklendir. */
    iStatus = XGpioPs_CfgInitialize(&sGpio, spGpioConfig,
                                     spGpioConfig->BaseAddr);
    if (iStatus != XST_SUCCESS)
    {
        xil_printf("ERROR: GPIO initialization failed (code=%d).\r\n", iStatus);
        return XST_FAILURE;
    }

    /* Adim 3: MIO23'u cikis yap ve cikis tamponunu etkinlestir.
     * Iki cagri da zorunludur: SetDirectionPin DIRM'i,
     * SetOutputEnablePin OEN'i ayarlar (bkz. Bolum 4 derin dalis —
     * main_registers.c). */
    XGpioPs_SetDirectionPin(&sGpio, DS50_LED_PIN_MIO, 1U);
    XGpioPs_SetOutputEnablePin(&sGpio, DS50_LED_PIN_MIO, 1U);

    xil_printf("Task 1: DS50 will blink with a 500 ms period.\r\n");

    /* Adim 4: sonsuz dongude yak/sondur. */
    for (;;)
    {
        XGpioPs_WritePin(&sGpio, DS50_LED_PIN_MIO, 1U);
        usleep(LED_YANIP_SONME_US);

        XGpioPs_WritePin(&sGpio, DS50_LED_PIN_MIO, 0U);
        usleep(LED_YANIP_SONME_US);
    }

    return XST_SUCCESS;
}
