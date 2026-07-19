/* ============================================================
 * gpio_led_button.h — DS50 LED (MIO23) ve SW19 buton (MIO22)
 *
 * lab10-bughunt (Gorev 10 - Bug Hunt). DS50'yi PS GPIO uzerinden surer,
 * SW19'u interrupt ile izler. GIC baglantisi XPS_GPIO_INT_ID (48)
 * uzerinden yapilir.
 * ============================================================ */
#ifndef GPIO_LED_BUTTON_H
#define GPIO_LED_BUTTON_H

#include "xgpiops.h"
#include "xscugic.h"

#define DS50_PIN_NO   23U   /* PS MIO23 — kullanici LED'i */
#define SW19_PIN_NO   22U   /* PS MIO22 — kullanici butonu */

/* ISR ile ana dongu arasinda paylasilan durum.
   NOT: bu satirlarin niteleyicileri asagida (.c dosyasinda) tanimlidir. */
extern unsigned char G_ucButtonFlag;      /* buton ISR'sinde kurulur */
extern unsigned int  G_uiButtonCount;     /* toplam basis sayaci */

/**
 * @brief GPIO ve GIC baglantisini kurar (DS50 cikis, SW19 interrupt girisi).
 *
 * @param spGpio Ilklendirilecek GPIO surucu nesnesi.
 * @param spGic Interrupt'in baglanacagi GIC nesnesi.
 * @return Basarida XST_SUCCESS, aksi halde bir Xilinx hata kodu.
 */
int  gpioLedButtonInit(XGpioPs* spGpio, XScuGic* spGic);

/**
 * @brief DS50'nin durumunu tersler.
 *
 * @param spGpio Uzerinde islem yapilacak GPIO surucu nesnesi.
 */
void ledDs50Toggle(XGpioPs* spGpio);

#endif /* GPIO_LED_BUTTON_H */
