/* ============================================================================
 * ina226.h — PS I2C0 -> PCA9544A mux (U23, 0x75, kanal 0) -> INA226 (0x40)
 * mini sürücü modülü (GÖREV 6 çözümü)
 *
 * API imzaları _gorev-zinciri.md'deki sözleşmeyle birebir aynıdır — Görev 9
 * (lab09-kuyruk) bu modülü aynen kullanır.
 * ============================================================================ */
#ifndef INA226_H
#define INA226_H

#include "xil_types.h"

/**
 * @brief PS I2C0'ı 100 kHz'de başlatır, PCA9544A mux'ına (0x75) kanal-0
 * seçim baytını yazar, ardından INA226'nın (0x40) Manufacturer ID
 * yazmacını (0xFE) okuyup 0x5449 ("TI") ile doğrular.
 * @return 0 = başarılı, 0-dışı = hata (mux, adres ya da kimlik uyuşmazlığı).
 */
int ina226Init(void);

/**
 * @brief INA226'nın Bus Voltage yazmacını (0x02) okur, LSB = 1.25 mV ile
 * milivolt'a çevirip *uipMilliVolt'a yazar.
 * @param uipMilliVolt Okunan bus geriliminin (mV) yazılacağı adres.
 * @return 0 = başarılı, 0-dışı = hata (I2C zaman aşımı / yanıt yok).
 */
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);

#endif /* INA226_H */
