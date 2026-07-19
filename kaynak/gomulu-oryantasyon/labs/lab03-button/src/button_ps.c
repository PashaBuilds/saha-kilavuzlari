/* ============================================================================
 * button_ps.c — SW19 (PS MIO22) / DS50 (PS MIO23) mini surucu modulu
 * (GOREV 3 cozumu)
 *
 * POLARITE NOTU: UG1271, SW19/DS50'nin active-high mi active-low mu
 * oldugunu acikca soylemez (bagimsiz teyit denemesi ve gerekce icin
 * bkz. content/_arastirma-ek-C.md §C.1). Bu dosya, dokumanin Gorev 3/4
 * zincirinde zaten benimsenen kabulu kullanir — SW19 basiliyken 1
 * okunur, DS50'ye 1 yazilinca yanar. Kartinda tam tersini gozlersen
 * degistirilecek tek yer: buttonRead() icindeki return satirini `!`
 * ile tersle.
 * ============================================================================ */

#include "button_ps.h"
#include "xgpiops.h"
#include "xparameters.h"
#include "xstatus.h"

#define BUTTON_PS_PIN_SW19   22U   /* SW19 buton → PS MIO22 (giris) */
#define BUTTON_PS_PIN_DS50   23U   /* DS50 LED   → PS MIO23 (cikis) */

static XGpioPs S_sGpio;

/**
 * @brief PS GPIO donanimini hazirlar: SW19'u giris, DS50'yi cikis yapar.
 */
int buttonInit(void)
{
    int iStatus;
    XGpioPs_Config* spConfig;

    /* Klasik (DEVICE_ID) akis — Bolum 4'teki iki kaliptan biri. SDT
     * akisinda bunun yerini
     * XGpioPs_LookupConfig(XPAR_XGPIOPS_0_BASEADDR) alir ve
     * CfgInitialize'a taban adres dogrudan verilir. */
    spConfig = XGpioPs_LookupConfig(XPAR_XGPIOPS_0_DEVICE_ID);
    if (spConfig == NULL)
    {
        return XST_FAILURE;
    }

    iStatus = XGpioPs_CfgInitialize(&S_sGpio, spConfig, spConfig->BaseAddr);
    if (iStatus != XST_SUCCESS)
    {
        return iStatus;
    }

    /* Once yon register'ini (DIRM) dogru kurmadan okumak/yazmak
     * anlamsizdir — Gorev 1'in dersi. SW19 giris (0), DS50 cikis (1)
     * ve output enable (OEN) olmadan yazdigin deger pine asla ulasmaz. */
    XGpioPs_SetDirectionPin(&S_sGpio, BUTTON_PS_PIN_SW19, 0U);
    XGpioPs_SetDirectionPin(&S_sGpio, BUTTON_PS_PIN_DS50, 1U);
    XGpioPs_SetOutputEnablePin(&S_sGpio, BUTTON_PS_PIN_DS50, 1U);

    return XST_SUCCESS;
}

/**
 * @brief SW19'un ANLIK (ham, debounce'suz) durumunu okur.
 */
unsigned int buttonRead(void)
{
    return XGpioPs_ReadPin(&S_sGpio, BUTTON_PS_PIN_SW19);
}

/**
 * @brief DS50'yi yazar.
 */
void ledPsWrite(unsigned int uiState)
{
    XGpioPs_WritePin(&S_sGpio, BUTTON_PS_PIN_DS50, (uiState != 0U) ? 1U : 0U);
}
