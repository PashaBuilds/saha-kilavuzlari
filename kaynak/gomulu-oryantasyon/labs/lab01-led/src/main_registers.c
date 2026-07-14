/*
 * main_registers.c — Task 1 (Chapter 4) deep dive: blinking the DS50 LED
 * (MIO23) WITHOUT the XGpioPs driver, using direct volatile pointer
 * access instead. This is meant to show exactly what
 * XGpioPs_WritePin/SetDirectionPin/SetOutputEnablePin do behind the
 * scenes.
 *
 * Register offsets (relative to GPIO base 0xFF0A0000) were VERIFIED
 * against the Xilinx/AMD embeddedsw xgpiops_hw.h — see the sourcing
 * note in content/_arastirma-ek-B.md.
 *
 *   DIRM_0  (Bank 0 Direction Mode, R/W)  base + 0x204
 *   OEN_0   (Bank 0 Output Enable,  R/W)  base + 0x208
 *   DATA_0  (Bank 0 Data,           R/W)  base + 0x040
 *
 * Bank 0 = MIO 0-25 (see Chapter 4 / _arastirma.md SS5); since DS50 =
 * MIO23, bit 23 of the Bank 0 registers is used.
 *
 * NOTE: This file is NOT compiled in the SAME project as main.c (both
 * define main()). Place this file in a separate, empty application
 * project and build it to observe the same DS50 blinking behavior.
 */

#include "xil_io.h"
#include "xil_types.h"
#include "xstatus.h"
#include "xil_printf.h"
#include "sleep.h"

/* Base address + Bank 0 offsets (see the file header comment). */
#define GPIO_BASE_ADDR    0xFF0A0000U
#define GPIO_DIRM_0_OFSET   0x00000204U
#define GPIO_OEN_0_OFSET    0x00000208U
#define GPIO_DATA_0_OFSET   0x00000040U

/* DS50 is bit 23 of Bank 0. */
#define DS50_LED_BIT_MIO    23U
#define DS50_LED_MASKE      (1U << DS50_LED_BIT_MIO)

#define LED_YANIP_SONME_US  500000U

int main(void)
{
    volatile unsigned int* uipDirm0 =
        (volatile unsigned int*)(GPIO_BASE_ADDR + GPIO_DIRM_0_OFSET);
    volatile unsigned int* uipOen0 =
        (volatile unsigned int*)(GPIO_BASE_ADDR + GPIO_OEN_0_OFSET);
    volatile unsigned int* uipData0 =
        (volatile unsigned int*)(GPIO_BASE_ADDR + GPIO_DATA_0_OFSET);

    /* Read-modify-write: set ONLY the MIO23 bit to output, without
     * touching the other 25 MIO pins in Bank 0. Writing '=' directly
     * would overwrite the direction of every pin in this bank — this is
     * exactly what Task 1's "Self-Check" question asks about. */
    *uipDirm0 |= DS50_LED_MASKE;
    *uipOen0  |= DS50_LED_MASKE;

    xil_printf("Task 1 (deep dive): DS50 via direct register access.\r\n");

    for (;;)
    {
        *uipData0 |= DS50_LED_MASKE;    /* turn DS50 on, leave others untouched */
        usleep(LED_YANIP_SONME_US);

        *uipData0 &= ~DS50_LED_MASKE;   /* turn DS50 off, leave others untouched */
        usleep(LED_YANIP_SONME_US);
    }

    return XST_SUCCESS;
}
