/* ============================================================================
 * buton_ps.h — SW19 (PS MIO22) / DS50 (PS MIO23) mini sürücü modülü
 * (GÖREV 3 çözümü). XGpioPs sürücüsünü sarmalar; API imzaları
 * _gorev-zinciri.md'deki sözleşmeyle birebir aynıdır.
 * ============================================================================ */
#ifndef BUTON_PS_H
#define BUTON_PS_H

#include "xil_types.h"

/**
 * @brief PS GPIO donanımını hazırlar: SW19'u giriş, DS50'yi çıkış yapar.
 *
 * @return XST_SUCCESS / XST_FAILURE (ya da alt katman hata kodu) döner —
 *         dönüş değerini kontrol etme alışkanlığı Bölüm 12'de tam olarak
 *         işlenecek.
 */
int buttonInit(void);

/**
 * @brief SW19'un ANLIK (debounce'suz, ham) durumunu okur.
 *
 * KABUL — aktif-yüksek, yani 1 = basılı, 0 = serbest (bkz. buton_ps.c dosya
 * başı notu).
 *
 * @return SW19'un anlık pin durumu (1 = basılı, 0 = serbest).
 */
unsigned int buttonRead(void);

/**
 * @brief DS50'yi yazar.
 *
 * @param uiState 0 dışında bir değer ise DS50 yanar, 0 ise söner.
 */
void ledPsWrite(unsigned int uiState);

#endif /* BUTON_PS_H */
