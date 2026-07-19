/* ============================================================================
 * main.c — GOREV 3 cozumu: Butonu Oku (Polling)
 *
 * SW19'u (PS MIO22) surekli polling ile okur, durumunu DS50'ye
 * (PS MIO23) yansitir ve sayac tabanli debounce kullanarak "kac kez
 * basildi" bilgisini UART'a basar.
 *
 * NOT: karttaki 8 LED, 5 buton ve DIP switch PL pinlerindedir (Bolum
 * 2'de gorulur); bitstream olmadan onlara erisemeyiz. Bu yuzden
 * yalnizca tek PS butonu (SW19) ve tek PS LED'i (DS50) ile calisiyoruz
 * — 8'li LED karasimsegi PL kapisi Bolum 9'da acilinca gelecek.
 * ============================================================================ */

#include "xstatus.h"
#include "sleep.h"
#include "uart_ps.h"
#include "button_ps.h"

/* Ornekleme araligi: SW19'u her 5 ms'de bir oku. Mekanik buton tipik
 * olarak birkac ms icinde "sekmeyi" bitirir; ayni yeni degeri
 * DEBOUNCE_ESIK tur ART ARDA gormeden bir gecisi gercek saymayiz. */
#define DEBOUNCE_SAMPLE_INTERVAL_US   5000U   /* 5 ms */
#define DEBOUNCE_ESIK               4U      /* 4 * 5 ms = 20 ms kararlilik penceresi */

/* xil_printf %f desteklemiyordu (Gorev 2); burada ters yonde bir takas
 * yapiyoruz: sayi->string cevirimini KENDIMIZ yaziyoruz ki tum cikti
 * hazir bir printf'e ihtiyac duymadan uart_ps modulunden (yani kendi
 * kodumuzdan) gecsin. */
static void printNumber(unsigned int uiValue)
{
    char cArrBuffer[11];   /* 32-bit sayi en fazla 10 basamak + '\0' */
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
    unsigned int uiStableState;    /* debounce edilmis (kararli kabul edilen) buton durumu */
    unsigned int uiRawState;       /* bu tur okunan ham durum (sekiyor olabilir) */
    unsigned int uiUnstableCount;  /* uiStableState'ten farkli cikan art arda okuma sayisi */
    unsigned int uiPressCount;     /* debounce edilmis, gercek basma sayisi */

    uartInit();

    if (buttonInit() != XST_SUCCESS)
    {
        uartSendString("ERROR: buttonInit failed - check the GPIO DEVICE_ID.\n");
        while (1)
        {
            ;
        }
    }

    uartSendString("\n--- TASK 3: Read Button (Polling) ---\n");
    uartSendString("Press SW19: DS50 turns on. Release: it turns off. Count is debounced.\n\n");

    /* Baslangic durumunu oku ve LED'i ona esitle — kart acilirken buton
     * zaten basili olabilir; "her zaman sonuk" varsaymak yanlis olurdu. */
    uiStableState = buttonRead();
    uiUnstableCount = 0U;
    uiPressCount = 0U;
    ledPsWrite(uiStableState);

    while (1)
    {
        uiRawState = buttonRead();

        if (uiRawState == uiStableState)
        {
            /* Degisiklik yok — ya buton hic oynamadi ya da bir sekme
             * onceki durumuna geri dondu. Iki durumda da sayaci
             * sifirliyoruz; yarim kalmis bir gecisi asla gercek
             * saymayiz. */
            uiUnstableCount = 0U;
        }
        else
        {
            uiUnstableCount++;

            if (uiUnstableCount >= DEBOUNCE_ESIK)
            {
                /* Ayni yeni degeri DEBOUNCE_ESIK tur art arda gorduk —
                 * bu artik sekme degil, gercek bir gecis. */
                uiStableState = uiRawState;
                uiUnstableCount = 0U;

                ledPsWrite(uiStableState);

                if (uiStableState != 0U)
                {
                    uiPressCount++;
                    uartSendString("press #");
                    printNumber(uiPressCount);
                    uartSendString(" - DS50 ON\n");
                }
                else
                {
                    uartSendString("release   - DS50 OFF\n");
                }
            }
        }

        /* Polling'in maliyeti tam olarak budur: CPU bu beklemeden baska
         * hicbir sey yapmadan surekli SW19'u sorgular. Bolum 7'de ayni
         * isi interrupt ile yapip bu maliyeti ortadan kaldiracaksin. */
        usleep(DEBOUNCE_SAMPLE_INTERVAL_US);
    }

    return 0;
}
