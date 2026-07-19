/* ============================================================================
 * ina226.c — PS I2C0 -> PCA9544A mux -> INA226 mini surucu modulu
 * (GOREV 6 cozumu)
 *
 * I2C AGACI (content/_arastirma.md §4 + content/_arastirma-ek-D.md §D.4):
 *   PS I2C0 (MIO14-15) -> PCA9544A mux, U23, adres 0x75 -> kanal 0
 *                       -> INA226 guc monitoru, adres 0x40 (VCCINT rayi)
 *
 * PCA9544A KONTROL BAYTI (TI datasheet SCPS146G, Tablo 8-1, teyit notu
 * content/_arastirma-ek-D.md §D.4'te): bit2 = enable, bit1:0 = kanal no.
 * Kanal 0 icin bayt = 0b0000_0100 = 0x04.
 *
 * SAVUNMACI PROGRAMLAMA (Bolum 12'nin erken uygulamasi): hicbir I2C
 * cagrisi sonsuza dek beklemez. Her gonderme/alma islemi en fazla
 * DENEME_SINIRI kez denenir ve basarisizlikta hata doner — "timeout'suz
 * sonsuz bekleme yok" kurali burada kodlanmistir.
 * ============================================================================ */

#include "ina226.h"
#include "xiicps.h"
#include "xparameters.h"
#include "xstatus.h"
#include "sleep.h"

#define IIC0_SAAT_HZ                100000U   /* I2C0: 100 kHz standart mod */

#define MUX_PCA9544A_I2C_ADDR      0x75U     /* U23 */
#define MUX_CHANNEL0_COMMAND_BYTE      0x04U     /* enable(bit2) + kanal 0 (bit1:0=00) */

#define INA226_I2C_ADDR            0x40U     /* VCCINT rayi */
#define INA226_REG_MANUFACTURER_ID  0xFEU
#define INA226_REG_BUS_VOLTAGE      0x02U
#define INA226_MANUFACTURER_ID_TI   0x5449U   /* "TI" ASCII */

#define I2C_DENEME_SINIRI           5U        /* sonsuz bekleme YASAK */
#define I2C_RETRY_WAIT_US       1000U

static XIicPs S_sIic;

/* --- sinirli tekrarli gonderme: sonsuz bekleme yerine DENEME_SINIRI deneme --- */
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

/* --- sinirli tekrarli alma --- */
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

/* --- "register pointer'i yaz, sonra oku" kalibi: her I2C register
 * okumasi aslinda iki islemdir. INA226 tum register'larini MSB once
 * gonderdigi icin 16-bit sonuc big-endian (MSB once) birlestirilir. --- */
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

    /* Power-on reset (POR) sonrasi mux hicbir kanali secili tutmaz —
     * kanal 0'i her seferinde acikca seciyoruz, yoksa INA226'ya giden
     * yol kapali kalir. */
    if (i2cSendLimited(MUX_PCA9544A_I2C_ADDR, &ucMuxCmd, 1) != XST_SUCCESS)
    {
        return (int)XST_FAILURE;
    }

    /* Kimlik dogrulama: yanlis mux kanali, yanlis adres ya da kablolama
     * sorunu, herhangi bir olcum alinmadan ONCE burada net bicimde
     * yakalanir — yoksa anlamsiz bir "gerilim" degeriyle yola devam
     * ederdik. */
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

    /* LSB = 1.25 mV = 5/4 mV — kayan noktaya gerek yok; tamsayi
     * aritmetigi tam sonucu verir (INA226 datasheet SBOS547B, Tablo 7-1). */
    *uipMilliVolt = ((unsigned int)usRaw * 5U) / 4U;

    return (int)XST_SUCCESS;
}
