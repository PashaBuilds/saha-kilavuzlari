# SOLUTION.md — lab10-bughunt (Görev 10) tam çözüm

Bu dosya ipucu merdiveninin en alt basamağıdır. Buraya gelmeden önce
`README.md`'deki spesifikasyon ve belirtileri en az bir tur kendi
başına denediğinden emin ol.

Aşağıda dört hata da aynı düzeni izler: **yer**, **belirti**,
**kök neden** (tek cümle), **düzeltme**.

---

## Hata 1 — `G_ucButtonFlag` volatile değil

**Yer:** `src/gpio_led_button.h`, global değişken bildirimi
(`extern unsigned char G_ucButtonFlag;`); tanımı
`src/gpio_led_button.c`'nin başında. `src/main.c`'nin ana döngüsünde
okunur, `buttonIsr()` içinde yazılır.

**Belirti:** Debug build'de (`-O0`) buton çalışır görünür; ama release
build'de (`-O2`) SW19'a basmak hiçbir şey yapmaz.

**Kök neden:** Değişken bir ISR ile ana döngü arasında paylaşılıyor ama
`volatile` ile işaretlenmemiş; `-O2` optimizasyonu altında derleyici bu
değişkenin ana döngü içinde bellekte değişemeyeceğini varsayar, değerini
bir register'da önbelleğe alır ve döngünün geri kalanında belleği bir
daha hiç okumaz — ISR belleği güncellese de ana döngü bunu asla görmez.

**Düzeltme:**

```c
/* src/gpio_led_button.h — önce */
extern unsigned char  G_ucButtonFlag;

/* src/gpio_led_button.h — sonra */
extern volatile unsigned char  G_ucButtonFlag;
```

```c
/* src/gpio_led_button.c — önce */
unsigned char  G_ucButtonFlag = 0;

/* src/gpio_led_button.c — sonra */
volatile unsigned char  G_ucButtonFlag = 0;
```

Bildirim (header) ile tanım (kaynak dosya) aynı niteleyiciyi taşımalı;
ikisini de değiştirmeyi unutma.

---

## Hata 2 — buton ISR'sinde uzun iş (xil_printf/uart + gecikme döngüsü)

**Yer:** `src/gpio_led_button.c`, `buttonIsr()` fonksiyonu —
`uartSendString("button interrupt received\r\n");` satırı ve hemen
altındaki `for` gecikme döngüsü.

**Belirti:** `tick N` satırları çoğunlukla düzgün gelir, ama ara sıra
bir numara atlanır ya da bir satır beklenenden geç çıkar — özellikle
butona sık basılınca kötüleşir.

**Kök neden:** "Interrupt'ın geldiğini görmek için faydalı" gerekçesiyle
ISR'ye eklenen UART yazması ve busy-wait gecikme döngüsü, interrupt'ı
CPU üzerinde olması gerekenden çok daha uzun tutar; bu süre boyunca
arkasında bekleyen TTC0 interrupt'ları gecikir ya da art arda gelirlerse
kaçırılır — tick sayacının atlamasının/geride kalmasının nedeni budur.

**Düzeltme:** ISR yalnızca durumu güncellesin (bayrak + sayaç); UART
yazmasını ve her türlü debounce/gecikme mantığını ana döngüye taşı:

```c
/* src/gpio_led_button.c — önce */
static void buttonIsr(void *pvCallBackRef)
{
    XGpioPs *spGpio = (XGpioPs *)pvCallBackRef;
    unsigned int uiDelayCount;

    if (XGpioPs_IntrGetStatusPin(spGpio, SW19_PIN_NO) != 0U)
    {
        XGpioPs_IntrClearPin(spGpio, SW19_PIN_NO);

        G_uiButtonCount++;
        G_ucButtonFlag = 1;

        uartSendString("button interrupt received\r\n");
        for (uiDelayCount = 0; uiDelayCount < 200000U; uiDelayCount++)
        {
            /* empty body: a brief settling delay */
        }
    }
}

/* src/gpio_led_button.c — sonra */
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

Debounce gerçekten gerekiyorsa (mekanik sekme gerçek bir sorunsa), ana
döngüde tick sayacına ya da bir zaman damgasına karşılaştırarak yap —
ISR içine asla gecikme döngüsü kurma.

---

## Hata 3 — DS50 toggle `|=` kullanıyor

**Yer:** `src/gpio_led_button.c`, `ledDs50Toggle()` fonksiyonu.

**Belirti:** İlk buton basışında DS50 yanar, ama sonraki basışlarda
sönmesi gerekirken yanık kalır.

**Kök neden:** Durumu terslemesi (toggle) gereken satır `^=` yerine
`|=` kullanıyor; 1'i bit düzeyinde OR'lamak her çağrıda durumu 1'e
sabitler, yani LED bir kez yandıktan sonra bir daha asla 0'a dönemez.

**Düzeltme:**

```c
/* src/gpio_led_button.c — önce */
void ledDs50Toggle(XGpioPs *spGpio)
{
    /* durumu tersle */
    G_uiDs50State |= 1U;
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, G_uiDs50State);
}

/* src/gpio_led_button.c — sonra */
void ledDs50Toggle(XGpioPs *spGpio)
{
    /* durumu tersle */
    G_uiDs50State ^= 1U;
    XGpioPs_WritePin(spGpio, DS50_PIN_NO, G_uiDs50State);
}
```

Bu hatanın öğrettiği ders: yorum ("durumu tersle") niyeti doğru
söylüyor ama kod bunu yerine getirmiyor — yorumlara değil, koda güven.

---

## Hata 4 — 8 KB'lik yerel dizi stack overflow'a yol açıyor

**Yer:** `src/main.c`, `printHealthSummary()` fonksiyonu —
`char cArrHistoryBuffer[8192];` satırı. `src/lscript.ld`'deki
`_STACK_SIZE` ile karşılaştır (bu lab'de 0x4000 = 16 KB).

**Belirti:** Sistem dakikalarca (bazen saatlerce) sorunsuz çalışır,
sonra rastgele çöker ya da anlamsız değerler basmaya başlar; belirgin
bir tetikleyici görünmez.

**Kök neden:** `printHealthSummary()` her çağrıldığında (10 tick'te
bir) 8 KB'lik `cArrHistoryBuffer` dizisini stack'te ayırır; bu projeye
tanınan 16 KB'lik stack alanı, bu tahsisin üstüne binen diğer çağrı
çerçeveleri (ve o anda denk gelen herhangi bir interrupt'ın stack
kullanımı) ile birlikte aşılabilir. Taşma komşu belleği bozar; hangi
verinin bozulacağı çağrı anındaki stack derinliğine bağlı olduğu için
çöküş hemen değil, sistem bir süre çalıştıktan sonra rastgele ortaya
çıkar.

**Düzeltme:** Buffer'ı gerçekten gereken boyuta indir (tick/buton sayısı
mesajı için birkaç düzine bayt yeter):

```c
/* src/main.c — önce */
static void printHealthSummary(unsigned int uiTick, unsigned int uiButton)
{
    char cArrHistoryBuffer[8192];

    snprintf(cArrHistoryBuffer, sizeof(cArrHistoryBuffer),
              "summary: tick=%lu button=%lu\r\n",
              (unsigned long)uiTick, (unsigned long)uiButton);
    uartSendString(cArrHistoryBuffer);
}

/* src/main.c — sonra */
static void printHealthSummary(unsigned int uiTick, unsigned int uiButton)
{
    char cArrHistoryBuffer[128];

    snprintf(cArrHistoryBuffer, sizeof(cArrHistoryBuffer),
              "summary: tick=%lu button=%lu\r\n",
              (unsigned long)uiTick, (unsigned long)uiButton);
    uartSendString(cArrHistoryBuffer);
}
```

Kalıcı disiplin olarak: gömülü sistemlerde büyük yerel diziler her
zaman şüpheli sayılmalıdır. Gerçekten büyük bir buffer gerekiyorsa,
`static` yapıp stack'ten `.bss`'e taşımayı ya da `lscript.ld`'de
`_STACK_SIZE`'ı bilinçli büyütmeyi değerlendir — ama her iki durumda da
kazara değil, bilerek yap.

---

## Özet tablo

| # | Dosya / fonksiyon | Kök neden (tek cümle) |
|---|---|---|
| 1 | `gpio_led_button.h/.c` — `G_ucButtonFlag` | `volatile` eksikliği yüzünden derleyici `-O2` altında bayrağın belleğini yeniden okumayı bırakır. |
| 2 | `gpio_led_button.c` — `buttonIsr()` | ISR içindeki UART yazması ve gecikme döngüsü ISR'yi uzatır, TTC0 interrupt'larını geciktirir/kaçırtır. |
| 3 | `gpio_led_button.c` — `ledDs50Toggle()` | `^=` yerine `|=` kullanmak LED durumunu kalıcı olarak 1'e sabitler. |
| 4 | `main.c` — `printHealthSummary()` | 8 KB'lik yerel dizi, projenin dar stack alanını taşırıp komşu belleği bozar. |
