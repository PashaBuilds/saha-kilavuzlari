/* ============================================================================
 * ina226.h — PS I2C0 -> PCA9544A mux (U23, 0x75, kanal 0) -> INA226 (0x40)
 * mini surucu modulu (GOREV 6 cozumu)
 *
 * API imzalari _gorev-zinciri.md'deki sozlesmeyle birebir aynidir —
 * Gorev 9 (lab09-queue) bu modulu oldugu gibi kullanir.
 * ============================================================================ */
#ifndef INA226_H
#define INA226_H

#include "xil_types.h"

/**
 * @brief PS I2C0'i 100 kHz'de ilklendirir, PCA9544A mux'a (0x75)
 * kanal-0 secim baytini yazar, sonra INA226'nin (0x40) Manufacturer ID
 * register'ini (0xFE) okuyup 0x5449 ("TI") ile dogrular.
 * @return 0 = basari, sifir disi = hata (mux, adres ya da kimlik uyusmazligi).
 */
int ina226Init(void);

/**
 * @brief INA226'nin Bus Voltage register'ini (0x02) okur, LSB = 1.25 mV
 * ile milivolta cevirir ve *uipMilliVolt'a yazar.
 * @param uipMilliVolt Olculen bus geriliminin (mV) yazilacagi adres.
 * @return 0 = basari, sifir disi = hata (I2C zaman asimi / cevap yok).
 */
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);

#endif /* INA226_H */
