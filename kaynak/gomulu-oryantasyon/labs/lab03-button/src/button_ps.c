/* ============================================================================
 * button_ps.c — SW19 (PS MIO22) / DS50 (PS MIO23) mini driver module
 * (TASK 3 solution)
 *
 * POLARITY NOTE: UG1271 does not explicitly state whether SW19/DS50 is
 * active-high or active-low (see the independent verification attempt
 * and rationale in content/_arastirma-ek-C.md §C.1). This file uses the
 * convention already adopted in the Task 3/4 chain of this document —
 * SW19 reads 1 while pressed, and DS50 turns on when written 1. If you
 * observe the exact opposite on your board, the single place to change
 * is: invert the return line of buttonRead() with `!`.
 * ============================================================================ */

#include "button_ps.h"
#include "xgpiops.h"
#include "xparameters.h"
#include "xstatus.h"

#define BUTTON_PS_PIN_SW19   22U   /* SW19 button → PS MIO22 (input) */
#define BUTTON_PS_PIN_DS50   23U   /* DS50 LED    → PS MIO23 (output) */

static XGpioPs S_sGpio;

/**
 * @brief Prepares the PS GPIO hardware: sets SW19 as input, DS50 as output.
 */
int buttonInit(void)
{
    int iStatus;
    XGpioPs_Config* spConfig;

    /* Classic (DEVICE_ID) flow — one of the two patterns from Chapter 4.
     * In the SDT flow this is replaced by
     * XGpioPs_LookupConfig(XPAR_XGPIOPS_0_BASEADDR), and CfgInitialize is
     * given the base address directly. */
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

    /* Reading/writing is meaningless without correctly setting the
     * direction register (DIRM) first — the lesson from Task 1. Without
     * SW19 as input (0), DS50 as output (1), and output enable (OEN),
     * the value you write never reaches the pin. */
    XGpioPs_SetDirectionPin(&S_sGpio, BUTTON_PS_PIN_SW19, 0U);
    XGpioPs_SetDirectionPin(&S_sGpio, BUTTON_PS_PIN_DS50, 1U);
    XGpioPs_SetOutputEnablePin(&S_sGpio, BUTTON_PS_PIN_DS50, 1U);

    return XST_SUCCESS;
}

/**
 * @brief Reads the INSTANTANEOUS (raw, non-debounced) state of SW19.
 */
unsigned int buttonRead(void)
{
    return XGpioPs_ReadPin(&S_sGpio, BUTTON_PS_PIN_SW19);
}

/**
 * @brief Writes DS50.
 */
void ledPsWrite(unsigned int uiState)
{
    XGpioPs_WritePin(&S_sGpio, BUTTON_PS_PIN_DS50, (uiState != 0U) ? 1U : 0U);
}
