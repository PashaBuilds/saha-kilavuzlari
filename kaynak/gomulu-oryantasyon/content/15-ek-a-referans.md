# Ek A — Hızlı Referans

Bu ek, dokümanı baştan sona okuduktan sonra masana asıp göz ucuyla bakacağın
bir kopya kâğıdı. Şaka bir yana — gerçekten yazıcıya bas ve masana as; kod
yazarken bir register offset'ini ya da bir FreeRTOS çağrısının imzasını
hatırlamaya çalışıp dokümanın on sayfasını karıştırmaktan iyidir.

## Bit İşlem Makroları

Bölüm 5'te gördüğün set/clear/toggle/test kalıplarının kopyalanabilir hâli.
Kendi projene doğrudan yapıştırabilirsin.

```c
/* Bit işlem makroları — kopyala, projene yapıştır */
#define BIT(n)              (1u << (n))

#define BIT_SET(reg, n)     ((reg) |=  BIT(n))    /* biti 1 yap */
#define BIT_CLEAR(reg, n)   ((reg) &= ~BIT(n))     /* biti 0 yap */
#define BIT_TOGGLE(reg, n)  ((reg) ^=  BIT(n))     /* biti tersine çevir */
#define BIT_TEST(reg, n)    (((reg) >> (n)) & 1u)  /* bit 1 mi? 0/1 döner */

/* Çok bitlik alan (field) işlemleri: genişlik + başlangıç konumu ile */
#define FIELD_MASK(genislik, konum) \
    (((1u << (genislik)) - 1u) << (konum))

#define FIELD_GET(reg, genislik, konum) \
    (((reg) & FIELD_MASK(genislik, konum)) >> (konum))

#define FIELD_SET(reg, genislik, konum, deger) \
    ((reg) = ((reg) & ~FIELD_MASK(genislik, konum)) | \
             (((deger) << (konum)) & FIELD_MASK(genislik, konum)))
```

:::tuzak Makro parantez disiplini
`n` ve `reg` parametrelerini makro gövdesinde her zaman parantez içine al
(yukarıdaki gibi). Aksi hâlde `BIT_SET(reg, a + b)` gibi bir çağrıda operatör
önceliği makroyu sessizce bozar — derleyici hata vermez, davranış yanlış
olur.
:::

## Sık Kullanılan Vitis İşlemleri

Vitis Unified IDE'de en sık başvuracağın işlemler. **Tuşlar sürüme göre
değişebilir** — burada verilenler menü yolu; kısayol tuşunu IDE'nin
Run/Debug menüsünden ya da tercih (preferences) ekranından teyit et.

| İşlem | Nerede |
|---|---|
| Yeni platform/application projesi | File → New → Platform/Application Component |
| Derle (Build) | Proje sağ tık → Build Project, ya da araç çubuğundaki çekiç simgesi |
| Temizle (Clean) | Proje sağ tık → Clean |
| Debug konfigürasyonu oluştur | Proje sağ tık → Debug As → hedef seç |
| Debug başlat (JTAG üzerinden karta yükle) | Debug perspektifi → Launch/Run ikonu |
| Step Over | Debug araç çubuğu — "adımı atla" ikonu |
| Step Into | Debug araç çubuğu — "içine gir" ikonu |
| Step Out | Debug araç çubuğu — "dışına çık" ikonu |
| Resume / Continue | Debug araç çubuğu — "devam et" ikonu |
| Breakpoint ekle/kaldır | Kod satırı numarasının soluna tıkla |
| Register izleme | Debug perspektifi → Registers sekmesi |
| Memory izleme | Debug perspektifi → Memory sekmesi |
| XSCT konsolu aç | Vitis içinden ya da terminalden `xsct` komutu |

## UART / SPI / I2C Özet Karşılaştırma

Bölüm 8'in tel seviyesi anlatımının tablo hâli.

| Özellik | UART | SPI | I2C |
|---|---|---|---|
| Tel sayısı | 2 (TX, RX) + ortak GND | 4 (SCLK, MOSI, MISO, CS) + GND; her ek cihaz bir CS hattı daha ister | 2 (SDA, SCL) + GND; tüm cihazlar aynı iki hattı paylaşır |
| Senkron mu | Hayır — asenkron, iki uç önceden aynı baud'da anlaşır | Evet — SCLK master tarafından üretilir | Evet — SCL master tarafından üretilir |
| Topoloji | Nokta-nokta (point-to-point) | Bir master + birden çok slave, CS ile seçim | Bir (ya da çoklu) master + birden çok slave, 7/10 bit adresle seçim |
| Fiziksel katman | Push-pull, tek yönlü hatlar | Push-pull, tek yönlü hatlar | Open-drain + pull-up dirençler (Bölüm 8) |
| Tipik hız | 9.6 kbps – birkaç Mbps | Onlarca Mbps'e kadar | 100 kHz (standart) – 400 kHz (fast) – 1 MHz (fast mode+) |
| Onay (ACK) mekanizması | Yok | Yok | Var — her bayttan sonra alıcı ACK/NACK üretir |
| Bu dokümanda kullanıldığı yer | PS UART0, Görev 2 ve sonrası | Bölüm 8'de tanıtılır, bu yolculukta ayrı bir görevi yok | PS I2C0 → INA226, Görev 6 ve sonrası |

## FreeRTOS API Mini Kartı

Bölüm 10 ve sonraki görevlerde en sık elinin altında olacak çağrılar.

| Çağrı | Ne işe yarar |
|---|---|
| `xTaskCreate(...)` | Yeni bir task oluşturur ve scheduler'a kaydeder |
| `vTaskDelete(handle)` | Bir task'ı sonlandırır (`NULL` ile çağıran kendini siler) |
| `vTaskDelay(ticks)` | Çağıran task'ı belirtilen tick kadar bloklar, CPU'yu bırakır |
| `vTaskDelayUntil(...)` | Sabit periyotlu gecikme; zamanla sürüklenmeyi önler |
| `xQueueCreate(uzunluk, boyut)` | Belirtilen kapasitede bir mesaj kuyruğu oluşturur |
| `xQueueSend(q, &veri, bekleme)` | Kuyruğa veri koyar (task bağlamında çağrılır) |
| `xQueueSendFromISR(q, &veri, &uyandi)` | Kuyruğa veri koyar (yalnızca ISR içinde çağrılır) |
| `xQueueReceive(q, &veri, bekleme)` | Kuyruktan veri okur; veri gelene kadar bloklanabilir |
| `xSemaphoreCreateBinary()` | İkili (binary) semaphore oluşturur |
| `xSemaphoreCreateMutex()` | Karşılıklı dışlama (mutex) semaphore'u oluşturur |
| `xSemaphoreGive(sem)` / `xSemaphoreGiveFromISR(...)` | Semaphore'u serbest bırakır (task / ISR bağlamı) |
| `xSemaphoreTake(sem, bekleme)` | Semaphore'u almaya çalışır; gelene kadar bloklanabilir |
| `portYIELD_FROM_ISR(uyandi)` | ISR sonunda, uyanan task daha öncelikliyse hemen ona geçiş yaptırır |
| `uxTaskGetStackHighWaterMark(handle)` | Task'ın kullanmadığı en düşük stack miktarını raporlar (taşma tespiti) |

## ZCU111 Önemli Adres ve Cihaz Özeti

Tüm değerler `_arastirma.md`'den (UG1271/UG1085 kaynaklı) — kart üstünde
kendi gözünle doğrulamak istersen kaynak orada.

| Çevre birimi | Taban adres | Not |
|---|---|---|
| UART0 | `0xFF00_0000` | PS_UART0, MIO 18-19, hello-world çıktısının geldiği port |
| GPIO (PS) | `0xFF0A_0000` | DS50 (MIO23) ve SW19 (MIO22) buradan sürülür/okunur |
| TTC0 | `0xFF11_0000` | Triple Timer Counter 0, kanal 0 Görev 5'te kullanılır |
| GICD | `0xF901_0000` | GIC-400 dağıtıcı (distributor) |
| GICC | `0xF902_0000` | GIC-400 CPU arayüzü |

**PS tek LED/buton çifti:** DS50 = MIO23 (LED), SW19 = MIO22 (buton) —
bitstream'siz erişilebilen tek çift budur (Bölüm 2, Bölüm 4).

**I2C ağacı özeti:** PS I2C0 (MIO 14-15) → PCA9544A 4 kanallı mux (U23,
adres `0x75`) → kanal 0 → INA226 güç monitörleri. İki laboratuvar rayı:
**`0x40` = VCCINT**, **`0x42` = VCC1V8** (tam liste `_arastirma.md` §4'te).

**SW6 boot modu anahtarı** (4 kutuplu DIP, Mode[3:0] = SW6[4:1], ON = 0):

| Boot modu | SW6 [4:1] |
|---|---|
| JTAG | ON, ON, ON, ON |
| QSPI32 (fabrika varsayılanı) | ON, ON, OFF, ON |
| SD | OFF, OFF, OFF, ON |

**Kesme (GIC) ID'leri:** PS GPIO = **48**, UART0 = **53**, TTC0 kanal 0 =
**68** (ZynqMP'ye özgü; Zynq-7000 ile karıştırma — Bölüm 7).
