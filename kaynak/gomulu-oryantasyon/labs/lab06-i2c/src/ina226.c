/* ============================================================================
 * ina226.c — PS I2C0 -> PCA9544A mux -> INA226 mini sürücü modülü
 * (GÖREV 6 çözümü)
 *
 * I2C AĞACI (content/_arastirma.md §4 + content/_arastirma-ek-D.md §D.4):
 *   PS I2C0 (MIO14-15) -> PCA9544A mux, U23, adres 0x75 -> kanal 0
 *                       -> INA226 güç monitörü, adres 0x40 (VCCINT rayı)
 *
 * PCA9544A KONTROL BAYTI (TI datasheet SCPS146G, Table 8-1, doğrulama notu
 * content/_arastirma-ek-D.md §D.4'te): bit2 = enable, bit1:0 = kanal no.
 * Kanal 0 için bayt = 0b0000_0100 = 0x04.
 *
 * SAVUNMACI PROGRAMLAMA (Bölüm 12'nin erken uygulaması): hiçbir I2C
 * çağrısı sonsuza kadar beklemez. Her gönder/al işlemi DENEME_SINIRI kadar
 * denenir, başarısız olursa hata döner — "timeout'suz sonsuz bekleme
 * yasak" kuralı burada koddadır.
 * ============================================================================ */

#include "ina226.h"
#include "xiicps.h"
#include "xparameters.h"
#include "xstatus.h"
#include "sleep.h"

#define IIC0_SAAT_HZ                100000U   /* I2C0: 100 kHz standart mod */

#define MUX_PCA9544A_I2C_ADRES      0x75U     /* U23 */
#define MUX_KANAL0_KOMUT_BAYTI      0x04U     /* enable(bit2) + kanal 0 (bit1:0=00) */

#define INA226_I2C_ADRES            0x40U     /* VCCINT rayı */
#define INA226_REG_MANUFACTURER_ID  0xFEU
#define INA226_REG_BUS_VOLTAGE      0x02U
#define INA226_MANUFACTURER_ID_TI   0x5449U   /* "TI" ASCII */

#define I2C_DENEME_SINIRI           5U        /* sonsuz bekleme YASAK */
#define I2C_DENEME_BEKLEME_US       1000U

static XIicPs S_sIic;

/* --- sınırlı denemeyle gönderme: sonsuz bekleme yerine DENEME_SINIRI --- */
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

        usleep(I2C_DENEME_BEKLEME_US);
    }

    return XST_FAILURE;
}

/* --- sınırlı denemeyle alma --- */
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

        usleep(I2C_DENEME_BEKLEME_US);
    }

    return XST_FAILURE;
}

/* --- "register pointer yaz, sonra oku" deseni: her I2C yazmaç okuması
 * aslında iki işlemdir. 16-bit sonucu big-endian (MSB önce) birleştirir
 * (INA226 tüm yazmaçlarını MSB önce gönderir). --- */
static int ina226RegRead(unsigned char ucRegAddr, unsigned short* uspValue)
{
    unsigned char ucPointer = ucRegAddr;
    unsigned char ucArrBuffer[2];

    if (i2cSendLimited(INA226_I2C_ADRES, &ucPointer, 1) != XST_SUCCESS)
    {
        return XST_FAILURE;
    }

    if (i2cRecvLimited(INA226_I2C_ADRES, ucArrBuffer, 2) != XST_SUCCESS)
    {
        return XST_FAILURE;
    }

    *uspValue = ((unsigned short)ucArrBuffer[0] << 8) | (unsigned short)ucArrBuffer[1];
    return XST_SUCCESS;
}

int ina226Init(void)
{
    XIicPs_Config* spIicConfig;
    unsigned char ucMuxCmd = MUX_KANAL0_KOMUT_BAYTI;
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

    /* Mux güç açılışında (POR) hiçbir kanalı seçili tutmaz — her seferinde
     * açıkça kanal 0'ı seçiyoruz, aksi halde INA226'ya giden hat kapalı
     * kalır. */
    if (i2cSendLimited(MUX_PCA9544A_I2C_ADRES, &ucMuxCmd, 1) != XST_SUCCESS)
    {
        return (int)XST_FAILURE;
    }

    /* Kimlik doğrulaması: yanlış mux kanalı, yanlış adres ya da kablolama
     * sorunu varsa bunu ölçüm almadan ÖNCE, net bir şekilde yakalarız —
     * aksi halde anlamsız bir "gerilim" değeriyle yola devam ederdik. */
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

    /* LSB = 1.25 mV = 5/4 mV — kayan noktaya gerek yok, tam sayı
     * aritmetiğiyle tam sonucu verir (INA226 datasheet SBOS547B, Table 7-1). */
    *uipMilliVolt = ((unsigned int)usRaw * 5U) / 4U;

    return (int)XST_SUCCESS;
}
