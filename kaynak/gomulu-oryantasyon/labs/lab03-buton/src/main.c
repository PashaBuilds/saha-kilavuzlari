/* ============================================================================
 * main.c — GÖREV 3 çözümü: Buton Oku (Polling)
 *
 * SW19'u (PS MIO22) sürekli sorgulama (polling) ile okur, DS50'ye (PS MIO23)
 * yansıtır ve sayaç-tabanlı debounce ile "kaç kez basıldığını" UART'a basar.
 *
 * NOT: karttaki 8 LED, 5 buton ve DIP switch PL pinlerindedir (Bölüm 2'de
 * gördün); bitstream olmadan onlara erişemeyiz. Bu yüzden tek PS butonu
 * (SW19) ve tek PS LED'i (DS50) ile çalışıyoruz — Bölüm 9'da PL kapısı
 * açılınca 8 LED'lik yürüyen ışığa kavuşacaksın.
 * ============================================================================ */

#include "xstatus.h"
#include "sleep.h"
#include "uart_ps.h"
#include "buton_ps.h"

/* Örnekleme aralığı: her 5 ms'de bir SW19'u oku. Mekanik bir buton
 * genelde birkaç ms içinde "sıçramasını" bitirir; DEBOUNCE_ESIK kadar
 * ARDIŞIK turda aynı yeni değeri görmeden geçişi gerçek saymıyoruz. */
#define DEBOUNCE_ORNEK_ARALIGI_US   5000U   /* 5 ms */
#define DEBOUNCE_ESIK               4U      /* 4 * 5 ms = 20 ms kararlılık penceresi */

/* xil_printf %f'i desteklemiyordu (Görev 2); burada da tam tersi bir
 * fedakarlık yapıyoruz: sayı->dizgi çevirimini KENDİMİZ yazıyoruz ki tüm
 * çıktı uart_ps modülünden (yani kendi kodumuzdan) geçsin — hazır bir
 * printf'e ihtiyaç duymadan. */
static void printNumber(unsigned int uiValue)
{
    char cArrBuffer[11];   /* 32-bit sayı en fazla 10 basamak + '\0' */
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
    unsigned int uiStableState;    /* debounce'lu (kararlı kabul edilen) buton durumu */
    unsigned int uiRawState;       /* bu turda okunan ham (sıçramalı olabilir) durum */
    unsigned int uiUnstableCount;  /* uiStableState'ten farklı ardışık okuma sayacı */
    unsigned int uiPressCount;     /* debounce'lu, gerçek basma sayısı */

    uartInit();

    if (buttonInit() != XST_SUCCESS)
    {
        uartSendString("HATA: buttonInit basarisiz - GPIO DEVICE_ID'yi kontrol et.\n");
        while (1)
        {
            ;
        }
    }

    uartSendString("\n--- GOREV 3: Buton Oku (Polling) ---\n");
    uartSendString("SW19'a bas: DS50 yanar. Birak: soner. Sayac debounce'lu.\n\n");

    /* Başlangıç durumunu okuyup LED'i onunla eşitliyoruz — kart açılırken
     * buton zaten basılı tutuluyor olabilir, "her zaman söndür" varsaymak
     * yanlış olurdu. */
    uiStableState = buttonRead();
    uiUnstableCount = 0U;
    uiPressCount = 0U;
    ledPsWrite(uiStableState);

    while (1)
    {
        uiRawState = buttonRead();

        if (uiRawState == uiStableState)
        {
            /* Değişiklik yok — ya buton hiç oynamadı ya da bir sıçrama
             * eski durumuna geri döndü. İkisinde de sayacı sıfırlıyoruz;
             * yarım kalmış bir geçişi "gerçek" saymayız. */
            uiUnstableCount = 0U;
        }
        else
        {
            uiUnstableCount++;

            if (uiUnstableCount >= DEBOUNCE_ESIK)
            {
                /* DEBOUNCE_ESIK ardışık turda aynı yeni değeri gördük —
                 * artık bu bir sıçrama değil, gerçek bir geçiş. */
                uiStableState = uiRawState;
                uiUnstableCount = 0U;

                ledPsWrite(uiStableState);

                if (uiStableState != 0U)
                {
                    uiPressCount++;
                    uartSendString("basma #");
                    printNumber(uiPressCount);
                    uartSendString(" - DS50 YANDI\n");
                }
                else
                {
                    uartSendString("birakma    - DS50 SONDU\n");
                }
            }
        }

        /* Polling'in bedeli tam olarak burada: CPU bu bekleme dışında
         * başka hiçbir iş yapmıyor, sürekli SW19'u soruyor. Bölüm 7'de
         * aynı işi interrupt'la yapıp bu bedeli ortadan kaldıracaksın. */
        usleep(DEBOUNCE_ORNEK_ARALIGI_US);
    }

    return 0;
}
