# Ek A — Hızlı Referans

Bu ek, doküman baştan sona okunduktan sonra elinin altında duracak bir hızlı
başvuru sayfasıdır. Register offset'leri, API imzaları ve sık gereken
değerleri tek yerde toplar; kod yazarken metnin tamamında arama yapma
ihtiyacını azaltır.

## Bit Manipülasyon Makroları

Bölüm 5'te tanıtılan set/clear/toggle/test kalıplarının kopyala-yapıştır
hâli. Bu makroları doğrudan projene alabilirsin.

```c
/* Bit manipulation macros — copy into your project */
#define BIT(n)              (1u << (n))

#define BIT_SET(reg, n)     ((reg) |=  BIT(n))    /* set bit to 1 */
#define BIT_CLEAR(reg, n)   ((reg) &= ~BIT(n))     /* set bit to 0 */
#define BIT_TOGGLE(reg, n)  ((reg) ^=  BIT(n))     /* invert bit */
#define BIT_TEST(reg, n)    (((reg) >> (n)) & 1u)  /* is bit 1? returns 0/1 */

/* Multi-bit field operations: by width and starting position */
#define FIELD_MASK(width, position) \
    (((1u << (width)) - 1u) << (position))

#define FIELD_GET(reg, width, position) \
    (((reg) & FIELD_MASK(width, position)) >> (position))

#define FIELD_SET(reg, width, position, value) \
    ((reg) = ((reg) & ~FIELD_MASK(width, position)) | \
             (((value) << (position)) & FIELD_MASK(width, position)))
```

:::tuzak Makroda parantez disiplini
Makro gövdesinde `n` ve `reg` parametrelerini her zaman paranteze al
(yukarıdaki gibi). Aksi hâlde `BIT_SET(reg, a + b)` gibi bir çağrıda
operatör önceliği makronun davranışını sessizce bozar — derleyici hata
vermez, sonuç yanlış çıkar.
:::

## Sık Kullanılan Vitis İşlemleri

Vitis Unified IDE'de en sık ihtiyaç duyacağın işlemler. **Klavye
kısayolları sürüme göre değişebilir** — aşağıdaki satırlar menü yolunu
verir; kısayol tuşunu IDE'nin Run/Debug menüsünden veya tercihler
ekranından teyit et.

| İşlem | Yeri |
|---|---|
| Yeni platform/uygulama projesi | File → New → Platform/Application Component |
| Build | Projeye sağ tık → Build Project, veya araç çubuğundaki çekiç simgesi |
| Clean | Projeye sağ tık → Clean |
| Debug konfigürasyonu oluşturma | Projeye sağ tık → Debug As → hedefi seç |
| Debug başlatma (JTAG ile karta yükleme) | Debug perspektifi → Launch/Run simgesi |
| Step Over | Debug araç çubuğu — "step over" simgesi |
| Step Into | Debug araç çubuğu — "step into" simgesi |
| Step Out | Debug araç çubuğu — "step out" simgesi |
| Resume / Continue | Debug araç çubuğu — "resume" simgesi |
| Breakpoint ekleme/kaldırma | Kod editöründe satır numarasının soluna tıkla |
| Register izleme | Debug perspektifi → Registers sekmesi |
| Bellek izleme | Debug perspektifi → Memory sekmesi |
| XSCT konsolu açma | Vitis içinden veya terminalde `xsct` komutuyla |

## UART / SPI / I2C Karşılaştırma Özeti

Bölüm 8'deki hat seviyesi anlatımın tablo hâli.

| Özellik | UART | SPI | I2C |
|---|---|---|---|
| Kablo sayısı | 2 (TX, RX) + ortak GND | 4 (SCLK, MOSI, MISO, CS) + GND; her ek cihaz bir ek CS hattı ister | 2 (SDA, SCL) + GND; tüm cihazlar aynı iki hattı paylaşır |
| Senkron mu | Hayır — asenkron; iki taraf aynı baud hızında önceden anlaşmalı | Evet — SCLK'yı master üretir | Evet — SCL'yi master üretir |
| Topoloji | Noktadan noktaya | Bir master + çok slave, seçim CS ile | Bir (veya birden çok) master + çok slave, seçim 7/10 bit adresle |
| Fiziksel katman | Push-pull, tek yönlü hatlar | Push-pull, tek yönlü hatlar | Open-drain + pull-up dirençleri (Bölüm 8) |
| Tipik hız | 9.6 kbps – birkaç Mbps | Onlarca Mbps'e kadar | 100 kHz (standard) – 400 kHz (fast) – 1 MHz (fast mode+) |
| Alındı (ACK) mekanizması | Yok | Yok | Var — alıcı her byte sonrası ACK/NACK üretir |
| Bu dokümandaki kullanım | PS UART0, Görev 2 ve sonrası | Bölüm 8'de tanıtıldı; bu yolculukta ayrı görev konusu değil | PS I2C0 → INA226, Görev 6 ve sonrası |

## FreeRTOS API Hızlı Kartı

Bölüm 10 ve sonraki görevlerde en sık gereken çağrılar.

| Çağrı | Ne yapar |
|---|---|
| `xTaskCreate(...)` | Yeni bir task oluşturur ve scheduler'a kaydeder |
| `vTaskDelete(handle)` | Task'ı sonlandırır (`NULL` ile çağırılırsa çağıran task kendini siler) |
| `vTaskDelay(ticks)` | Çağıran task'ı belirtilen tick sayısı kadar bloklar, CPU'yu bırakır |
| `vTaskDelayUntil(...)` | Sabit periyotlu gecikme; zamanlama kaymasını (drift) önler |
| `xQueueCreate(length, size)` | Belirtilen kapasitede mesaj kuyruğu oluşturur |
| `xQueueSend(q, &data, wait)` | Kuyruğa veri koyar (task bağlamından çağrılır) |
| `xQueueSendFromISR(q, &data, &woken)` | Kuyruğa veri koyar (yalnızca ISR içinden çağrılır) |
| `xQueueReceive(q, &data, wait)` | Kuyruktan veri okur; veri gelene kadar bloklayabilir |
| `xSemaphoreCreateBinary()` | Binary semaphore oluşturur |
| `xSemaphoreCreateMutex()` | Karşılıklı dışlama (mutex) semaphore'u oluşturur |
| `xSemaphoreGive(sem)` / `xSemaphoreGiveFromISR(...)` | Semaphore'u serbest bırakır (task / ISR bağlamı) |
| `xSemaphoreTake(sem, wait)` | Semaphore'u almayı dener; müsait olana kadar bloklayabilir |
| `portYIELD_FROM_ISR(woken)` | ISR sonunda, uyandırılan task daha yüksek öncelikliyse hemen ona geçer |
| `uxTaskGetStackHighWaterMark(handle)` | Task'ın hiç kullanılmamış minimum stack miktarını bildirir (taşma tespiti) |

## ZCU111 Kilit Adres ve Cihaz Özeti

Tüm değerlerin kaynağı `_arastirma.md` (UG1271/UG1085'ten türetilmiş);
kartla bağımsız doğrulama gerekirse o kaynağa dön.

| Çevre birimi | Taban adres | Not |
|---|---|---|
| UART0 | `0xFF00_0000` | PS_UART0, MIO 18-19, hello-world mesajını basan port |
| GPIO (PS) | `0xFF0A_0000` | DS50 (MIO23) buradan sürülür, SW19 (MIO22) buradan okunur |
| TTC0 | `0xFF11_0000` | Triple Timer Counter 0; kanal 0, Görev 5'te kullanılır |
| GICD | `0xF901_0000` | GIC-400 distributor |
| GICC | `0xF902_0000` | GIC-400 CPU arayüzü |

**PS tek LED/buton çifti:** DS50 = MIO23 (LED), SW19 = MIO22 (buton) —
bitstream olmadan erişilebilen tek çift budur (Bölüm 2, Bölüm 4).

**I2C ağacı özeti:** PS I2C0 (MIO 14-15) → PCA9544A 4 kanallı mux (U23,
adres `0x75`) → kanal 0 → INA226 güç monitörleri. Laboratuvarda iki ray:
**`0x40` = VCCINT**, **`0x42` = VCC1V8** (tam liste `_arastirma.md` §4'te).

**SW6 boot mode anahtarı** (4 kutuplu DIP, Mode[3:0] = SW6[4:1], ON = 0):

| Boot modu | SW6 [4:1] |
|---|---|
| JTAG | ON, ON, ON, ON |
| QSPI32 (fabrika varsayılanı) | ON, ON, OFF, ON |
| SD | OFF, OFF, OFF, ON |

**Interrupt (GIC) ID'leri:** PS GPIO = **48**, UART0 = **53**, TTC0 kanal 0 =
**68** (ZynqMP'ye özgü; Zynq-7000 ile karıştırma — Bölüm 7).
