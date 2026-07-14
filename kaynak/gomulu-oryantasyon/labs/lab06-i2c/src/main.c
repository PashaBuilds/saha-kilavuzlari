/* ============================================================================
 * main.c — GÖREV 6 çözümü: I2C ile Gerçek Bir Çiple Konuş
 *
 * ina226Init() ile PS I2C0 -> PCA9544A mux (kanal 0) -> INA226 (0x40)
 * zincirini kurar ve kimliği doğrular; sonra saniyede bir VCCINT bus
 * gerilimini okuyup UART'a "VCCINT = NNN mV" biçiminde basar.
 * ============================================================================ */

#include "xstatus.h"
#include "sleep.h"
#include "uart_ps.h"
#include "ina226.h"

static void printNumber(unsigned int uiValue)
{
    char cArrBuffer[11];
    int iIndex = 10;

    cArrBuffer[10] = '\0';

    if (uiValue == 0U)
    {
        uartSendChar('0');
        return;
    }

    while ((uiValue > 0U) && (iIndex > 0))
    {
        iIndex--;
        cArrBuffer[iIndex] = (char)('0' + (uiValue % 10U));
        uiValue /= 10U;
    }

    uartSendString(&cArrBuffer[iIndex]);
}

int main(void)
{
    unsigned int uiMilliVolt;

    uartInit();

    uartSendString("\n--- GOREV 6: I2C ile Gercek Bir Ciple Konus ---\n");
    uartSendString("PS I2C0 -> PCA9544A(0x75) kanal 0 -> INA226(0x40)\n\n");

    if (ina226Init() != 0)
    {
        uartSendString("HATA: ina226Init basarisiz - mux kanali, adres ya da\n");
        uartSendString("kablolamayi kontrol et (Manufacturer ID 0x5449 dogrulanamadi).\n");
        while (1)
        {
            ;
        }
    }

    uartSendString("INA226 kimligi dogrulandi (0x5449). Olcum basliyor.\n\n");

    while (1)
    {
        if (ina226ReadBusVoltageMv(&uiMilliVolt) == 0)
        {
            uartSendString("VCCINT = ");
            printNumber(uiMilliVolt);
            uartSendString(" mV\n");
        }
        else
        {
            uartSendString("UYARI: olcum okunamadi (I2C zaman asimi).\n");
        }

        usleep(1000000U);   /* saniyede bir */
    }

    return 0;
}
