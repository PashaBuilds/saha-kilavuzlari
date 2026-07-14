/*
 * lab09-queue / ina226.h
 *
 * INA226 power monitor module -- for the INA226 (0x40, VCCINT rail)
 * sitting on channel 0 of the PCA9544A mux (U23, 0x75), via PS I2C0.
 *
 * The same module as lab06: even if lab06 has not been written yet, the
 * API contract is fixed in content/_gorev-zinciri.md; this file conforms
 * to that contract exactly, so once lab06 is written, they share the same
 * interface.
 */

#ifndef INA226_H
#define INA226_H

#include "xil_types.h"

/**
 * @brief Configures I2C0, switches the mux to channel 0, reads the
 * INA226's Manufacturer ID register (0xFE), and verifies it against
 * 0x5449 ("TI").
 * @return XST_SUCCESS / XST_FAILURE.
 */
int ina226Init(void);

/**
 * @brief Reads the Bus Voltage register (0x02), converts it to
 * millivolts at 1.25 mV/LSB, and writes it to *uipMilliVolt.
 * @param uipMilliVolt Address to which the measured bus voltage (mV) is written.
 * @return XST_SUCCESS / XST_FAILURE.
 */
int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt);

#endif /* INA226_H */
