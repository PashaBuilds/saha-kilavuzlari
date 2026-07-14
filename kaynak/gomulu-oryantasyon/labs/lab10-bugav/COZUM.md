# COZUM.md — lab10-bugav (Görev 10) tam çözüm

Bu dosya ipucu merdiveninin en alt basamağıdır. Buraya gelmeden önce
`README.md`'deki spesifikasyonu ve belirtileri kendi başına en az bir
tur denediğinden emin ol.

Aşağıda dört hata da aynı sırayla: **konum**, **belirti**, **kök neden**
(tek cümle), **düzeltme**.

---

## Hata 1 — `G_ucButtonFlag` volatile değil

**Konum:** `src/gpio_led_buton.h`, global değişken bildirimi (`extern
unsigned char G_ucButtonFlag;`); tanımı `src/gpio_led_buton.c` başında.
Okunduğu yer `src/main.c`'nin ana döngüsü, yazıldığı yer `buttonIsr()`.

**Belirti:** Debug derlemesinde (`-O0`) buton çalışıyor gibi görünür; ama
release derlemesinde (`-O2`) SW19'a basmak hiçbir şey yapmaz.

**Kök neden:** Değişken bir ISR ile ana döngü arasında paylaşılıyor ama
`volatile` işaretli değil; `-O2` optimizasyonunda derleyici ana döngüde bu
değişkenin bellekte değişmeyeceğini varsayıp değerini bir register'a
alıyor ve döngü boyunca belleği bir daha okumuyor — ISR belleği güncellese
de ana döngü bunu göremiyor.

**Düzeltme:**

```c
/* src/gpio_led_buton.h — önce */
extern unsigned char  G_ucButtonFlag;

/* src/gpio_led_buton.h — sonra */
extern volatile unsigned char  G_ucButtonFlag;
```

```c
/* src/gpio_led_buton.c — önce */
unsigned char  G_ucButtonFlag = 0;

/* src/gpio_led_buton.c — sonra */
volatile unsigned char  G_ucButtonFlag = 0;
```

Bildirim (header) ve tanım (kaynak dosya) aynı niteliğe sahip olmalı;
ikisini birden değiştirmeyi unutma.

---

## Hata 2 — Buton ISR'inde uzun iş (xil_printf/uart + gecikme döngüsü)

**Konum:** `src/gpio_led_buton.c`, `buttonIsr()` fonksiyonu — `uartSendString(
"buton kesmesi geldi\r\n");` satırı ve hemen altındaki `for`
gecikme döngüsü.

**Belirti:** `tick N` satırları çoğu zaman düzgün gelir, ama arada bir
sayı atlanıyor ya da satır beklenenden geç çıkıyor — özellikle butona sık
basıldığında kötüleşiyor.

**Kök neden:** ISR'in içine "kesmenin geldiğini görmek için faydalı"
gerekçesiyle eklenen UART yazımı ve boş bekleme döngüsü, kesmeyi olması
gerekenden çok daha uzun süre CPU'da tutuyor; bu süre boyunca öncelik
sırasındaki TTC0 kesmeleri gecikiyor ya da art arda geldiklerinde
kaçırılıyor, bu da tick sayacının sekmesine ya da gecikmesine yol açıyor.

**Düzeltme:** ISR yalnızca durumu güncellesin (bayrak + sayaç); UART
yazımı ve debounce/gecikme mantığını ana döngüye taşı:

```c
/* src/gpio_led_buton.c — önce */
static void buttonIsr(void *pvCallBackRef)
{
    XGpioPs *spGpio = (XGpioPs *)pvCallBackRef;
    unsigned int uiDelayCount;

    if (XGpioPs_IntrGetStatusPin(spGpio, SW19_PIN_NO) != 0U)
    {
        XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);

        G_uiButtonCount++;
        G_ucButtonFlag = 1;

        uartSendString("buton kesmesi geldi\r\n");
        for (uiDelayCount = 0; uiDelayCount < 200000U; uiDelayCount++)
        {
            /* bos govde: kisa bir yerlesme suresi */
        }
    }
}

/* src/gpio_led_buton.c — sonra */
static void buttonIsr(void *pvCallBackRef)
{
    XGpioPs *spGpio = (XGpioPs *)pvCallBackRef;

    if (XGpioPs_IntrGetStatusPin(spGpio, SW19_PIN_NO) != 0U)
    {
        XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);

        G_uiButtonCount++;
        G_ucButtonFlag = 1;
    }
}
```

Debounce gerekiyorsa (mekanik sekme gerçek bir sorunsa) bunu ana döngüde,
tick sayacı ya da bir zaman damgasıyla karşılaştırarak yap — ISR içinde
asla bekleme döngüsü kurma.

---

## Hata 3 — DS50 toggle'da `|=` kullanılmış

**Konum:** `src/gpio_led_buton.c`, `ledDs50Toggle()` fonksiyonu.

**Belirti:** İlk buton basışında DS50 yanıyor, ama sonraki basışlarda
sönmesi gerekirken yanık kalıyor.

**Kök neden:** Durumu tersine çevirmesi (toggle) gereken satır `^=` yerine
`|=` kullanıyor; bitwise OR ile 1 basmak her çağrıda durumu 1'e
sabitliyor, yani LED bir kez yandıktan sonra hiçbir zaman 0'a dönemiyor.

**Düzeltme:**

```c
/* src/gpio_led_buton.c — önce */
void ledDs50Toggle(XGpioPs *spGpio)
{
    /* durumu tersine cevir */
    G_uiDs50State |= 1U;
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, G_uiDs50State);
}

/* src/gpio_led_buton.c — sonra */
void ledDs50Toggle(XGpioPs *spGpio)
{
    /* durumu tersine cevir */
    G_uiDs50State ^= 1U;
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, G_uiDs50State);
}
```

Bu hatanın öğrettiği ders: yorum ("durumu tersine çevir") niyeti doğru
anlatıyor ama kod onu yapmıyor — yorumlara değil, koda güven.

---

## Hata 4 — 8 KB'lık yerel dizi → stack taşması

**Konum:** `src/main.c`, `printHealthSummary()` fonksiyonu —
`char cArrHistoryBuffer[8192];` satırı. Karşılaştırma için `src/lscript.ld`
içindeki `_STACK_SIZE` (bu lab'de 0x4000 = 16 KB).

**Belirti:** Sistem dakikalarca (bazen saatlerce) sorunsuz çalıştıktan
sonra rastgele çöküyor ya da anlamsız değerler basmaya başlıyor; net bir
tetikleyici yok gibi görünüyor.

**Kök neden:** `printHealthSummary()` her çağrıldığında (10 tick'te
bir) 8 KB'lık `cArrHistoryBuffer` dizisini stack üzerinde ayırıyor; bu proje
için ayrılan 16 KB'lık stack alanı, üstüne binen diğer çağrı çerçeveleri
(ve o an araya giren bir kesmenin kendi stack kullanımı) ile birlikte bunu
taşırabiliyor. Taşma komşu bellek bölgesini bozuyor; hangi verinin
bozulacağı çağrı anındaki stack derinliğine bağlı olduğundan çökme hemen
değil, sistem bir süre çalıştıktan sonra rastgele ortaya çıkıyor.

**Düzeltme:** Buffer'ı gerçek ihtiyaca göre küçült (bir tick/buton sayısı
metni için birkaç on bayt yeterli):

```c
/* src/main.c — önce */
static void printHealthSummary(unsigned int uiTick, unsigned int uiButton)
{
    char cArrHistoryBuffer[8192];

    snprintf(cArrHistoryBuffer, sizeof(cArrHistoryBuffer),
              "ozet: tick=%lu buton=%lu\r\n",
              (unsigned long)uiTick, (unsigned long)uiButton);
    uartSendString(cArrHistoryBuffer);
}

/* src/main.c — sonra */
static void printHealthSummary(unsigned int uiTick, unsigned int uiButton)
{
    char cArrHistoryBuffer[128];

    snprintf(cArrHistoryBuffer, sizeof(cArrHistoryBuffer),
              "ozet: tick=%lu buton=%lu\r\n",
              (unsigned long)uiTick, (unsigned long)uiButton);
    uartSendString(cArrHistoryBuffer);
}
```

Kalıcı disiplin olarak: gömülüde büyük yerel diziler her zaman şüpheli
olmalı. Gerçekten büyük bir tampon gerekiyorsa `static` yaparak stack
yerine `.bss`'e taşımayı, ya da `lscript.ld`'deki `_STACK_SIZE`'ı bilinçli
olarak büyütmeyi değerlendir — ama her iki durumda da bunu tesadüfen değil,
bilerek yap.

---

## Özet tablo

| # | Dosya / fonksiyon | Kök neden (tek cümle) |
|---|---|---|
| 1 | `gpio_led_buton.h/.c` — `G_ucButtonFlag` | `volatile` eksik olduğundan `-O2`'de derleyici bayrağın belleğini bir daha okumuyor. |
| 2 | `gpio_led_buton.c` — `buttonIsr()` | ISR içindeki UART yazımı ve gecikme döngüsü kesmeyi uzatıp TTC0 kesmelerini geciktiriyor/kaçırıyor. |
| 3 | `gpio_led_buton.c` — `ledDs50Toggle()` | `^=` yerine `|=` kullanıldığından LED durumu hep 1'e sabitleniyor. |
| 4 | `main.c` — `printHealthSummary()` | 8 KB'lık yerel dizi, projenin dar stack alanını taşırıp komşu belleği bozuyor. |
