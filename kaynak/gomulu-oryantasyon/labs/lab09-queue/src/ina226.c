/*
 * lab09-queue / ina226.c
 *
 * Walks the PS I2C0 (MIO14-15) -> PCA9544A mux (U23, I2C address 0x75)
 * -> channel 0 -> INA226 (I2C address 0x40, VCCINT rail) path and reads
 * the Bus Voltage register.
 *
 * Sources:
 *  - I2C tree, INA226 address/register set, channel-0 path:
 *    content/_arastirma.md §4.
 *  - PCA9544A control byte (0x04 = enable + channel 0):
 *    content/_arastirma-ek-E.md §E.2 (confirmed via web search).
 */

#include "ina226.h"

#include "xparameters.h"
#include "xiicps.h"
#include "xstatus.h"
#include "xil_printf.h"

#define I2C0_CIHAZ_KIMLIGI            XPAR_XIICPS_0_DEVICE_ID
#define I2C_HIZI_HZ                   100000U   /* standard mode, 100 kHz */

#define PCA9544A_MUX_I2C_ADDR       0x75U
#define PCA9544A_CHANNEL0_SELECT           0x04U     /* B2=1 (enable), B1=0, B0=0 */

#define INA226_I2C_ADDR             0x40U
#define INA226_REG_BUS_GERILIM        0x02U
#define INA226_REG_MANUFACTURER_ID    0xFEU
#define INA226_MANUFACTURER_ID_EXPECTED 0x5449U   /* ASCII "TI" */

/* G_ prefix: driver instance used from a single point within the module. */
static XIicPs G_sIic;


/* ina226SelectMuxChannel0 -- writes a single-byte control word to the
 * PCA9544A, enabling channel 0. Calling this before every measurement is
 * safe against the possibility that another I2C0 user has changed the
 * mux in the meantime. */
static int
ina226SelectMuxChannel0(void)
{
    unsigned char ucWriteByte = PCA9544A_CHANNEL0_SELECT;
    int           iStatus;

    iStatus = XIicPs_MasterSendPolled(&G_sIic, &ucWriteByte, 1,
                                       PCA9544A_MUX_I2C_ADDR);
    if (iStatus != XST_SUCCESS)
    {
        return XST_FAILURE;
    }
    while (XIicPs_BusIsBusy(&G_sIic))
    {
    }

    return XST_SUCCESS;
}


/* ina226ReadRegister -- writes the 8-bit register address, then reads
 * back 16 bits (big-endian/MSB-first, the INA226's native format). */
static int
ina226ReadRegister(unsigned char ucRegAddress, unsigned short* uspValue)
{
    unsigned char ucArrBuffer[2];
    int           iStatus;

    iStatus = XIicPs_MasterSendPolled(&G_sIic, &ucRegAddress, 1,
                                       INA226_I2C_ADDR);
    if (iStatus != XST_SUCCESS)
    {
        return XST_FAILURE;
    }
    while (XIicPs_BusIsBusy(&G_sIic))
    {
    }

    iStatus = XIicPs_MasterRecvPolled(&G_sIic, ucArrBuffer, 2,
                                       INA226_I2C_ADDR);
    if (iStatus != XST_SUCCESS)
    {
        return XST_FAILURE;
    }
    while (XIicPs_BusIsBusy(&G_sIic))
    {
    }

    *uspValue = (unsigned short)(((unsigned short)ucArrBuffer[0] << 8) |
                                  (unsigned short)ucArrBuffer[1]);
    return XST_SUCCESS;
}


int
ina226Init(void)
{
    XIicPs_Config* spConfig;
    int            iStatus;
    unsigned short usId;

    spConfig = XIicPs_LookupConfig(I2C0_CIHAZ_KIMLIGI);
    if (spConfig == NULL)
    {
        return XST_FAILURE;
    }

    iStatus = XIicPs_CfgInitialize(&G_sIic, spConfig,
                                    spConfig->BaseAddress);
    if (iStatus != XST_SUCCESS)
    {
        return XST_FAILURE;
    }

    XIicPs_SetSClk(&G_sIic, I2C_HIZI_HZ);

    if (ina226SelectMuxChannel0() != XST_SUCCESS)
    {
        xil_printf("INA226: could not select mux channel 0\r\n");
        return XST_FAILURE;
    }

    if (ina226ReadRegister(INA226_REG_MANUFACTURER_ID, &usId) != XST_SUCCESS)
    {
        xil_printf("INA226: could not read identity register\r\n");
        return XST_FAILURE;
    }

    if (usId != INA226_MANUFACTURER_ID_EXPECTED)
    {
        xil_printf("INA226: unexpected identity 0x%04X (expected 0x%04X) -- "
                   "wrong device/channel selected?\r\n",
                   (unsigned int)usId,
                   (unsigned int)INA226_MANUFACTURER_ID_EXPECTED);
        return XST_FAILURE;
    }

    return XST_SUCCESS;
}


int
ina226ReadBusVoltageMv(unsigned int* uipMilliVolt)
{
    unsigned short usRaw;

    if (uipMilliVolt == NULL)
    {
        return XST_FAILURE;
    }

    if (ina226SelectMuxChannel0() != XST_SUCCESS)
    {
        return XST_FAILURE;
    }

    if (ina226ReadRegister(INA226_REG_BUS_GERILIM, &usRaw) != XST_SUCCESS)
    {
        return XST_FAILURE;
    }

    /* LSB = 1.25 mV = 5/4 mV. Integer arithmetic instead of floating
     * point: the habit of avoiding float where possible in embedded
     * systems is covered in Chapter 5. */
    *uipMilliVolt = ((unsigned int)usRaw * 5U) / 4U;

    return XST_SUCCESS;
}
