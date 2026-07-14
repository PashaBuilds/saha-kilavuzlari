/* ============================================================================
 * buton_ps.c — SW19 (PS MIO22) / DS50 (PS MIO23) mini sürücü modülü
 * (GÖREV 3 çözümü)
 *
 * POLARİTE NOTU: UG1271, SW19/DS50 için "aktif-yüksek mi aktif-düşük mü"
 * bilgisini açıkça yazmıyor (bağımsız doğrulama denemesi ve gerekçe:
 * content/_arastirma-ek-C.md §C.1). Bu dokümanın Görev 3/4 zincirinde zaten
 * benimsenen kabul — SW19 basılıyken 1 okunur, DS50'ye 1 yazılınca yanar —
 * burada da kullanılıyor. Kartında tam tersini gözlemlersen tek değişiklik
 * yeri: buttonRead()'in return satırını `!` ile tersine çevirmek.
 * ============================================================================ */

#include "buton_ps.h"
#include "xgpiops.h"
#include "xparameters.h"
#include "xstatus.h"

#define BUTON_PS_PIN_SW19   22U   /* SW19 butonu → PS MIO22 (giriş) */
#define BUTON_PS_PIN_DS50   23U   /* DS50 LED'i  → PS MIO23 (çıkış) */

static XGpioPs S_sGpio;

/**
 * @brief PS GPIO donanımını hazırlar: SW19'u giriş, DS50'yi çıkış yapar.
 */
int buttonInit(void)
{
    int iStatus;
    XGpioPs_Config* spConfig;

    /* Klasik (DEVICE_ID) akış — Bölüm 4'te gördüğün iki desenden biri.
     * SDT akışında yerine XGpioPs_LookupConfig(XPAR_XGPIOPS_0_BASEADDR)
     * çağrılır ve CfgInitialize'a doğrudan taban adres verilir. */
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

    /* Yön register'ını (DIRM) doğru kurmadan okuma/yazma anlamsızdır —
     * Görev 1'in dersi. SW19 giriş (0), DS50 çıkış (1) + çıkış etkinleştirme
     * (OEN) olmadan yazdığın değer pine hiç ulaşmaz. */
    XGpioPs_SetDirectionPin(&S_sGpio, BUTON_PS_PIN_SW19, 0U);
    XGpioPs_SetDirectionPin(&S_sGpio, BUTON_PS_PIN_DS50, 1U);
    XGpioPs_SetOutputEnablePin(&S_sGpio, BUTON_PS_PIN_DS50, 1U);

    return XST_SUCCESS;
}

/**
 * @brief SW19'un ANLIK (debounce'suz, ham) durumunu okur.
 */
unsigned int buttonRead(void)
{
    return XGpioPs_ReadPin(&S_sGpio, BUTON_PS_PIN_SW19);
}

/**
 * @brief DS50'yi yazar.
 */
void ledPsWrite(unsigned int uiState)
{
    XGpioPs_WritePin(&S_sGpio, BUTON_PS_PIN_DS50, (uiState != 0U) ? 1U : 0U);
}
