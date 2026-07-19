/*
 * lab09-queue / ina226.h
 *
 * INA226 guc monitoru modulu -- PS I2C0 uzerinden, PCA9544A mux'in
 * (U23, 0x75) kanal 0'inda oturan INA226 (0x40, VCCINT rayi) icin.
 *
 * lab06 ile ayni modul: lab06 henuz yazilmamis olsa bile API sozlesmesi
 * content/_gorev-zinciri.md'de sabittir; bu dosya o sozlesmeye birebir
 * uyar, dolayisiyla lab06 yazildiginda ayni arayuzu paylasirlar.
 */

#ifndef INA226_H
#define INA226_H

#include "xil_types.h"

/**
 * @brief I2C0'i yapilandirir, mux'u kanal 0'a alir, INA226'nin
 * Manufacturer ID register'ini (0xFE) okur ve 0x5449 ("TI") ile
 * dogrular.
 * @return XST_SUCCESS / XST_FAILURE.
 */
int ina226Init(void);

/**
 * @brief Bus Voltage register'ini (0x02) okur, 1.25 mV/LSB ile
 * milivolta cevirir ve *uipMilliVolt'a yazar.
 * @param uipMilliVolt Olculen bus geriliminin (mV) yazilacagi adres.
 * @return XST_SUCCESS / XST_FAILURE.
 */
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);

#endif /* INA226_H */
