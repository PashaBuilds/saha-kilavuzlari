/* ============================================================================
 * button_ps.h — SW19 (PS MIO22) / DS50 (PS MIO23) mini surucu modulu
 * (GOREV 3 cozumu). XGpioPs surucusunu sarmalar; API imzalari
 * _gorev-zinciri.md'deki sozlesmeyle birebir aynidir.
 * ============================================================================ */
#ifndef BUTTON_PS_H
#define BUTTON_PS_H

#include "xil_types.h"

/**
 * @brief PS GPIO donanimini hazirlar: SW19'u giris, DS50'yi cikis yapar.
 *
 * @return XST_SUCCESS / XST_FAILURE (ya da alt katman hata kodu) doner
 *         — donus degeri kontrol etme aliskanligi Bolum 12'de butunuyle
 *         islenecek.
 */
int buttonInit(void);

/**
 * @brief SW19'un ANLIK (ham, debounce'suz) durumunu okur.
 *
 * KABUL — active-high, yani 1 = basili, 0 = birakilmis (button_ps.c
 * dosya basligi notuna bak).
 *
 * @return SW19'un anlik pin durumu (1 = basili, 0 = birakilmis).
 */
unsigned int buttonRead(void);

/**
 * @brief DS50'yi yazar.
 *
 * @param uiState Sifir olmayan her deger DS50'yi yakar; 0 sondurur.
 */
void ledPsWrite(unsigned int uiState);

#endif /* BUTTON_PS_H */
