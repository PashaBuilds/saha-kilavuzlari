/* ============================================================================
 * main.c — GOREV 6 cozumu: I2C ile Gercek Bir Ciple Konus
 *
 * ina226Init() ile PS I2C0 -> PCA9544A mux (kanal 0) -> INA226 (0x40)
 * zincirini kurar ve kimligini dogrular; sonra VCCINT bus gerilimini
 * saniyede bir okuyup UART'a "VCCINT = NNN mV" olarak basar.
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

    uartSendString("\n--- TASK 6: Talk to a Real Chip over I2C ---\n");
    uartSendString("PS I2C0 -> PCA9544A(0x75) channel 0 -> INA226(0x40)\n\n");

    if (ina226Init() != 0)
    {
        uartSendString("ERROR: ina226Init failed - check the mux channel, address, or\n");
        uartSendString("wiring (Manufacturer ID 0x5449 could not be verified).\n");
        while (1)
        {
            ;
        }
    }

    uartSendString("INA226 identity verified (0x5449). Measurement starting.\n\n");

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
            uartSendString("WARNING: measurement read failed (I2C timeout).\n");
        }

        usleep(1000000U);   /* saniyede bir */
    }

    return 0;
}
