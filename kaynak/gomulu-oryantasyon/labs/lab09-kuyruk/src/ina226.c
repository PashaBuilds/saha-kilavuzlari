/*
 * lab09-kuyruk / ina226.c
 *
 * PS I2C0 (MIO14-15) -> PCA9544A mux (U23, I2C adresi 0x75) -> kanal 0
 * -> INA226 (I2C adresi 0x40, VCCINT rayi) yolunu yuruyup Bus Voltage
 * yazmacini okur.
 *
 * Kaynaklar:
 *  - I2C agaci, INA226 adresi/yazmac seti, kanal-0 yolu:
 *    content/_arastirma.md SS4.
 *  - PCA9544A kontrol bayti (0x04 = etkin + kanal 0):
 *    content/_arastirma-ek-E.md SS E.2 (web ile teyitli).
 */

#include "ina226.h"

#include "xparameters.h"
#include "xiicps.h"
#include "xstatus.h"
#include "xil_printf.h"

#define I2C0_CIHAZ_KIMLIGI            XPAR_XIICPS_0_DEVICE_ID
#define I2C_HIZI_HZ                   100000U   /* standart mod, 100 kHz */

#define PCA9544A_MUX_I2C_ADRESI       0x75U
#define PCA9544A_KANAL0_SEC           0x04U     /* B2=1 (etkin), B1=0, B0=0 */

#define INA226_I2C_ADRESI             0x40U
#define INA226_REG_BUS_GERILIM        0x02U
#define INA226_REG_MANUFACTURER_ID    0xFEU
#define INA226_MANUFACTURER_ID_BEKLENEN 0x5449U   /* ASCII "TI" */

/* G_ onekli: surucu ornegi, modul icinde tek noktadan kullanilir. */
static XIicPs G_sIic;


/* ina226SelectMuxChannel0 -- PCA9544A'ya tek baytlik kontrol yazar,
 * kanal 0'i etkinlestirir. Her olcumden once cagirmak, mux'i baska
 * bir I2C0 kullanicisinin degistirmis olma ihtimaline karsi guvenlidir. */
static int
ina226SelectMuxChannel0(void)
{
    unsigned char ucWriteByte = PCA9544A_KANAL0_SEC;
    int           iStatus;

    iStatus = XIicPs_MasterSendPolled(&G_sIic, &ucWriteByte, 1,
                                       PCA9544A_MUX_I2C_ADRESI);
    if (iStatus != XST_SUCCESS)
    {
        return XST_FAILURE;
    }
    while (XIicPs_BusIsBusy(&G_sIic))
    {
    }

    return XST_SUCCESS;
}


/* ina226ReadRegister -- 8 bitlik yazmac adresini yazar, ardindan 16 bit
 * (buyuk-uc-once/big-endian, INA226'nin dogal formati) geri okur. */
static int
ina226ReadRegister(unsigned char ucRegAddress, unsigned short* uspValue)
{
    unsigned char ucArrBuffer[2];
    int           iStatus;

    iStatus = XIicPs_MasterSendPolled(&G_sIic, &ucRegAddress, 1,
                                       INA226_I2C_ADRESI);
    if (iStatus != XST_SUCCESS)
    {
        return XST_FAILURE;
    }
    while (XIicPs_BusIsBusy(&G_sIic))
    {
    }

    iStatus = XIicPs_MasterRecvPolled(&G_sIic, ucArrBuffer, 2,
                                       INA226_I2C_ADRESI);
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
        xil_printf("INA226: mux kanal 0 secilemedi\r\n");
        return XST_FAILURE;
    }

    if (ina226ReadRegister(INA226_REG_MANUFACTURER_ID, &usId) != XST_SUCCESS)
    {
        xil_printf("INA226: kimlik yazmaci okunamadi\r\n");
        return XST_FAILURE;
    }

    if (usId != INA226_MANUFACTURER_ID_BEKLENEN)
    {
        xil_printf("INA226: beklenmeyen kimlik 0x%04X (beklenen 0x%04X) -- "
                   "yanlis cihaz/kanal mi secildi?\r\n",
                   (unsigned int)usId,
                   (unsigned int)INA226_MANUFACTURER_ID_BEKLENEN);
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

    /* LSB = 1.25 mV = 5/4 mV. Kayan nokta yerine tam sayi aritmetigi:
     * gomulude float'tan mumkunse kacinma aliskanligi Bolum 5'te. */
    *uipMilliVolt = ((unsigned int)usRaw * 5U) / 4U;

    return XST_SUCCESS;
}
