/* ============================================================================
 * ina226.c — PS I2C0 -> PCA9544A mux -> INA226 mini driver module
 * (TASK 6 solution)
 *
 * I2C TREE (content/_arastirma.md §4 + content/_arastirma-ek-D.md §D.4):
 *   PS I2C0 (MIO14-15) -> PCA9544A mux, U23, address 0x75 -> channel 0
 *                       -> INA226 power monitor, address 0x40 (VCCINT rail)
 *
 * PCA9544A CONTROL BYTE (TI datasheet SCPS146G, Table 8-1, verification note
 * in content/_arastirma-ek-D.md §D.4): bit2 = enable, bit1:0 = channel no.
 * Byte for channel 0 = 0b0000_0100 = 0x04.
 *
 * DEFENSIVE PROGRAMMING (early application of Chapter 12): no I2C call
 * ever waits forever. Every send/receive operation is retried up to
 * DENEME_SINIRI times, and returns an error on failure — the "no infinite
 * waiting without a timeout" rule is encoded here.
 * ============================================================================ */

#include "ina226.h"
#include "xiicps.h"
#include "xparameters.h"
#include "xstatus.h"
#include "sleep.h"

#define IIC0_SAAT_HZ                100000U   /* I2C0: 100 kHz standard mode */

#define MUX_PCA9544A_I2C_ADDR      0x75U     /* U23 */
#define MUX_CHANNEL0_COMMAND_BYTE      0x04U     /* enable(bit2) + channel 0 (bit1:0=00) */

#define INA226_I2C_ADDR            0x40U     /* VCCINT rail */
#define INA226_REG_MANUFACTURER_ID  0xFEU
#define INA226_REG_BUS_VOLTAGE      0x02U
#define INA226_MANUFACTURER_ID_TI   0x5449U   /* "TI" ASCII */

#define I2C_DENEME_SINIRI           5U        /* infinite waiting is FORBIDDEN */
#define I2C_RETRY_WAIT_US       1000U

static XIicPs S_sIic;

/* --- send with a bounded retry: DENEME_SINIRI attempts instead of an infinite wait --- */
static int i2cSendLimited(unsigned short usSlaveAddr, unsigned char* ucpData, int iLength)
{
    unsigned int uiAttempt;
    int iStatus;

    for (uiAttempt = 0U; uiAttempt < I2C_DENEME_SINIRI; uiAttempt++)
    {
        if (XIicPs_BusIsBusy(&S_sIic) == (int)FALSE)
        {
            iStatus = XIicPs_MasterSendPolled(&S_sIic, ucpData, iLength, usSlaveAddr);
            if (iStatus == XST_SUCCESS)
            {
                return XST_SUCCESS;
            }
        }

        usleep(I2C_RETRY_WAIT_US);
    }

    return XST_FAILURE;
}

/* --- receive with a bounded retry --- */
static int i2cRecvLimited(unsigned short usSlaveAddr, unsigned char* ucpBuffer, int iLength)
{
    unsigned int uiAttempt;
    int iStatus;

    for (uiAttempt = 0U; uiAttempt < I2C_DENEME_SINIRI; uiAttempt++)
    {
        if (XIicPs_BusIsBusy(&S_sIic) == (int)FALSE)
        {
            iStatus = XIicPs_MasterRecvPolled(&S_sIic, ucpBuffer, iLength, usSlaveAddr);
            if (iStatus == XST_SUCCESS)
            {
                return XST_SUCCESS;
            }
        }

        usleep(I2C_RETRY_WAIT_US);
    }

    return XST_FAILURE;
}

/* --- "write register pointer, then read" pattern: every I2C register read
 * is actually two operations. Assembles the 16-bit result as big-endian
 * (MSB first), since the INA226 sends all its registers MSB first. --- */
static int ina226RegRead(unsigned char ucRegAddr, unsigned short* uspValue)
{
    unsigned char ucPointer = ucRegAddr;
    unsigned char ucArrBuffer[2];

    if (i2cSendLimited(INA226_I2C_ADDR, &ucPointer, 1) != XST_SUCCESS)
    {
        return XST_FAILURE;
    }

    if (i2cRecvLimited(INA226_I2C_ADDR, ucArrBuffer, 2) != XST_SUCCESS)
    {
        return XST_FAILURE;
    }

    *uspValue = ((unsigned short)ucArrBuffer[0] << 8) | (unsigned short)ucArrBuffer[1];
    return XST_SUCCESS;
}

int ina226Init(void)
{
    XIicPs_Config* spIicConfig;
    unsigned char ucMuxCmd = MUX_CHANNEL0_COMMAND_BYTE;
    unsigned short usId;

    spIicConfig = XIicPs_LookupConfig(XPAR_XIICPS_0_DEVICE_ID);
    if (spIicConfig == NULL)
    {
        return (int)XST_FAILURE;
    }

    if (XIicPs_CfgInitialize(&S_sIic, spIicConfig,
                              spIicConfig->BaseAddress) != XST_SUCCESS)
    {
        return (int)XST_FAILURE;
    }

    if (XIicPs_SetSClk(&S_sIic, IIC0_SAAT_HZ) != XST_SUCCESS)
    {
        return (int)XST_FAILURE;
    }

    /* On power-on reset (POR) the mux keeps no channel selected — we
     * explicitly select channel 0 every time, otherwise the path to the
     * INA226 stays closed. */
    if (i2cSendLimited(MUX_PCA9544A_I2C_ADDR, &ucMuxCmd, 1) != XST_SUCCESS)
    {
        return (int)XST_FAILURE;
    }

    /* Identity verification: a wrong mux channel, wrong address, or wiring
     * problem is caught here, clearly, BEFORE any measurement is taken —
     * otherwise we would proceed with a meaningless "voltage" value. */
    if (ina226RegRead(INA226_REG_MANUFACTURER_ID, &usId) != XST_SUCCESS)
    {
        return (int)XST_FAILURE;
    }

    if (usId != INA226_MANUFACTURER_ID_TI)
    {
        return (int)XST_FAILURE;
    }

    return (int)XST_SUCCESS;
}

int ina226ReadBusVoltageMv(unsigned int* uipMilliVolt)
{
    unsigned short usRaw;

    if (ina226RegRead(INA226_REG_BUS_VOLTAGE, &usRaw) != XST_SUCCESS)
    {
        return (int)XST_FAILURE;
    }

    /* LSB = 1.25 mV = 5/4 mV — no need for floating point; integer
     * arithmetic yields the exact result (INA226 datasheet SBOS547B, Table 7-1). */
    *uipMilliVolt = ((unsigned int)usRaw * 5U) / 4U;

    return (int)XST_SUCCESS;
}
