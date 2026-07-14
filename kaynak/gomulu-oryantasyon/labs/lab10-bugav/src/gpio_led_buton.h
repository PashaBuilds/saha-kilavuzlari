/* ============================================================
 * gpio_led_buton.h — DS50 LED'i (MIO23) ve SW19 butonu (MIO22)
 *
 * lab10-bugav (Gorev 10 - Bug Avi). PS GPIO uzerinden DS50'yi surer,
 * SW19'u kesme (interrupt) ile izler. GIC bagi XPS_GPIO_INT_ID (48)
 * uzerinden yapilir.
 * ============================================================ */
#ifndef GPIO_LED_BUTON_H
#define GPIO_LED_BUTON_H

#include "xgpiops.h"
#include "xscugic.h"

#define DS50_PIN_NO   23U   /* PS MIO23 — kullanici LED'i */
#define SW19_PIN_NO   22U   /* PS MIO22 — kullanici butonu */

/* ISR ile ana dongu arasinda paylasilan durum.
   NOT: bu satirlarin nitelikleri asagida (.c dosyasinda) tanimli. */
extern unsigned char G_ucButtonFlag;      /* buton ISR'inde set edilir */
extern unsigned int  G_uiButtonCount;     /* toplam basis sayaci */

/**
 * @brief GPIO'yu ve GIC bagini kurar (DS50 cikis, SW19 kesmeli giris).
 *
 * @param spGpio Baslatilacak GPIO surucu nesnesi.
 * @param spGic Kesmenin baglanacagi GIC nesnesi.
 * @return XST_SUCCESS basarili ise, aksi halde Xilinx hata kodu.
 */
int  gpioLedButtonInit(XGpioPs* spGpio, XScuGic* spGic);

/**
 * @brief DS50'nin durumunu tersine cevirir.
 *
 * @param spGpio Uzerinde islem yapilacak GPIO surucu nesnesi.
 */
void ledDs50Toggle(XGpioPs* spGpio);

#endif /* GPIO_LED_BUTON_H */
