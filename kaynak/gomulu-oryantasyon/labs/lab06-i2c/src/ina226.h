/* ============================================================================
 * ina226.h — PS I2C0 -> PCA9544A mux (U23, 0x75, channel 0) -> INA226 (0x40)
 * mini driver module (TASK 6 solution)
 *
 * The API signatures match the contract in _gorev-zinciri.md exactly — Task 9
 * (lab09-queue) uses this module as-is.
 * ============================================================================ */
#ifndef INA226_H
#define INA226_H

#include "xil_types.h"

/**
 * @brief Initializes PS I2C0 at 100 kHz, writes the channel-0 selection
 * byte to the PCA9544A mux (0x75), then reads the INA226's (0x40)
 * Manufacturer ID register (0xFE) and verifies it against 0x5449 ("TI").
 * @return 0 = success, non-zero = error (mux, address, or identity mismatch).
 */
int ina226Init(void);

/**
 * @brief Reads the INA226's Bus Voltage register (0x02), converts it to
 * millivolts with LSB = 1.25 mV, and writes it to *uipMilliVolt.
 * @param uipMilliVolt Address to which the measured bus voltage (mV) is written.
 * @return 0 = success, non-zero = error (I2C timeout / no response).
 */
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);

#endif /* INA226_H */
