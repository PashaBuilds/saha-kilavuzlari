/*
 * lab09-queue / ina226.c
 *
 * PS I2C0 (MIO14-15) -> PCA9544A mux (U23, I2C adresi 0x75) -> kanal 0
 * -> INA226 (I2C adresi 0x40, VCCINT rayi) yolunu yurur ve Bus Voltage
 * register'ini okur.
 *
 * Kaynaklar:
 *  - I2C agaci, INA226 adres/register seti, kanal-0 yolu:
 *    content/_arastirma.md §4.
 *  - PCA9544A kontrol bayti (0x04 = enable + kanal 0):
 *    content/_arastirma-ek-E.md §E.2 (web aramasiyla teyitli).
 */

#include "ina226.h"

#include "xparameters.h"
#include "xiicps.h"
#include "xstatus.h"
#include "xil_printf.h"

#define I2C0_CIHAZ_KIMLIGI            XPAR_XIICPS_0_DEVICE_ID
#define I2C_HIZI_HZ                   100000U   /* standart mod, 100 kHz */

#define PCA9544A_MUX_I2C_ADDR       0x75U
#define PCA9544A_CHANNEL0_SELECT           0x04U     /* B2=1 (enable), B1=0, B0=0 */

#define INA226_I2C_ADDR             0x40U
#define INA226_REG_BUS_GERILIM        0x02U
#define INA226_REG_MANUFACTURER_ID    0xFEU
#define INA226_MANUFACTURER_ID_EXPECTED 0x5449U   /* ASCII "TI" */

/* G_ oneki: modul icinde tek noktadan kullanilan surucu ornegi. */
static XIicPs G_sIic;


/* ina226SelectMuxChannel0 -- PCA9544A'ya tek baytlik kontrol sozcugu
 * yazip kanal 0'i etkinlestirir. Her olcumden once cagirmak, baska bir
 * I2C0 kullanicisinin mux'u bu arada degistirmis olma ihtimaline karsi
 * guvenlidir. */
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


/* ina226ReadRegister -- 8-bit register adresini yazar, sonra 16 bit
 * geri okur (big-endian/MSB-once, INA226'nin dogal bicimi). */
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

    /* LSB = 1.25 mV = 5/4 mV. Kayan nokta yerine tamsayi aritmetigi:
     * gomulu sistemlerde mumkunse float'tan kacinma aliskanligi Bolum
     * 5'te islenir. */
    *uipMilliVolt = ((unsigned int)usRaw * 5U) / 4U;

    return XST_SUCCESS;
}
