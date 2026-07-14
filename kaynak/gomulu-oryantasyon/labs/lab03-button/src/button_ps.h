/* ============================================================================
 * button_ps.h — SW19 (PS MIO22) / DS50 (PS MIO23) mini driver module
 * (TASK 3 solution). Wraps the XGpioPs driver; the API signatures match
 * the contract in _gorev-zinciri.md exactly.
 * ============================================================================ */
#ifndef BUTTON_PS_H
#define BUTTON_PS_H

#include "xil_types.h"

/**
 * @brief Prepares the PS GPIO hardware: sets SW19 as input, DS50 as output.
 *
 * @return Returns XST_SUCCESS / XST_FAILURE (or a lower-layer error code)
 *         — the habit of checking return values will be covered in full
 *         in Chapter 12.
 */
int buttonInit(void);

/**
 * @brief Reads the INSTANTANEOUS (raw, non-debounced) state of SW19.
 *
 * CONVENTION — active-high, i.e. 1 = pressed, 0 = released (see the file
 * header note in button_ps.c).
 *
 * @return The instantaneous pin state of SW19 (1 = pressed, 0 = released).
 */
unsigned int buttonRead(void);

/**
 * @brief Writes DS50.
 *
 * @param uiState Any nonzero value turns DS50 on; 0 turns it off.
 */
void ledPsWrite(unsigned int uiState);

#endif /* BUTTON_PS_H */
