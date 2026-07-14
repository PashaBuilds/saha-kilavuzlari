/*
 * lab09-kuyruk / ina226.h
 *
 * INA226 guc monitoru modulu -- PS I2C0 uzerinden, PCA9544A mux'in
 * (U23, 0x75) kanal 0'inda oturan INA226 (0x40, VCCINT rayi) icin.
 *
 * lab06 ile ayni modul: lab06 henuz yazilmamissa da API sozlesmesi
 * content/_gorev-zinciri.md'de sabitlenmis; bu dosya o sozlesmeye
 * birebir uyar, boylece lab06 yazildiginda ayni arayuzu paylasirlar.
 */

#ifndef INA226_H
#define INA226_H

#include "xil_types.h"

/**
 * @brief I2C0'i kurar, mux'i kanal 0'a alir, INA226'nin Manufacturer ID
 * yazmacini (0xFE) okuyup 0x5449 ("TI") ile dogrular.
 * @return XST_SUCCESS / XST_FAILURE.
 */
int ina226Init(void);

/**
 * @brief Bus Voltage yazmacini (0x02) okur, 1.25 mV/LSB ile milivolta
 * cevirip *uipMilliVolt'a yazar.
 * @param uipMilliVolt Okunan bus geriliminin (mV) yazilacagi adres.
 * @return XST_SUCCESS / XST_FAILURE.
 */
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);

#endif /* INA226_H */
