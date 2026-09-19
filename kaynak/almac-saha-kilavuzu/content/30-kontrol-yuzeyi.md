# Bölüm 30 — Gömülü Yazılımcının Kontrol Yüzeyi
::meta onkosul=13,14,16,19,23,24,26,29 acar= blok=ps rota=yazilimci

:::neden-onemli
Sahadan soru: "Kart geldi, bitstream yüklendi, register haritası elimde.
Hangi sırayla, neyi, hangi birimle yazacağım?" Kılavuzun bütün bölümleri
sonunda bu soruya iner. NCO'nun FTW'si, CFAR'ın α'sı, pencerenin seçimi,
FIFO'nun taşma sayacı — hepsi PL'de yaşayan birer register ve hepsi
senin `write32()` çağrınla anlam kazanıyor. Bu bölüm o yüzeyi tek parça
halinde gösterir: kurgusal ama gerçekçi bir register haritası, birim
dönüşümlerini toplayan küçük bir C kütüphanesi, kalibrasyon tabloları ve
açılış sırası. Format kurgusaldır; hiçbir gerçek ürünün haritası değildir —
ama her satırı önceki bölümlerde türetilmiş bir kavramın karşılığıdır.
:::

## Sezgi: kontrol yüzeyi bir kokpittir

Bir uçağın kokpitindeki her gösterge ve düğme uçağın bir alt sistemine
bağlıdır; pilot motoru görmez, motorun devir göstergesini görür. PS
tarafındaki yazılımcı da DDC'yi, CFAR'ı, FFT'yi görmez; onların
register'larını görür. Kokpitte bir düğmenin işlevini bilmeden çevirmek nasıl
tehlikeliyse, register'a birimini bilmeden değer yazmak da öyledir. İyi bir
kontrol yüzeyi tasarımı üç şeyi garanti eder: **her register'ın birimi ve
ölçeği bellidir**, **her yazma geri okunabilir**, **her hata bir sayaçta
birikir**. Bu üçü yoksa hata ayıklama {{bolum:29}}'daki karar ağacına
dönmeden önce günler yer.

{{svg:g-300-ps-pl-yuzey.svg|PS–PL kontrol ve veri yüzeyi. Solda PS: sürücü katmanı, birim dönüşüm kütüphanesi, kalibrasyon tabloları ve uygulama. Ortada AXI-Lite (kontrol/durum register'ları, yeşil) ve AXI-Stream + DMA (PDW ve snapshot akışı, mavi). Sağda PL: her DSP bloğunun kontrol register'ları ve durum sayaçları. Kesintiler (IRQ) FIFO seviye ve hata olaylarını PS'e taşır.|kaydir}}

## Kurgusal register haritası

Aşağıdaki harita öğretici amaçlıdır. Gerçek bir tasarımda adresler, bit
alanları ve birimler farklı olacaktır; ama **kategoriler** hemen her almaç
kartında aynıdır: saat/ADC durumu, DDC, filtre/mod, FFT, tespit, PDW, snapshot,
sayaçlar. Adres ofsetleri 32-bit, tüm register'lar geri okunabilir
(yazma-tetikleyici olanlar hariç, onlar `W1P` — write-one-to-pulse).

{{tablo: genis}}
| Ofset | Ad | Bit | Erişim | Birim / ölçek | Bölüm |
|---|---|---|---|---|---|
| 0x000 | `ID_VERSION` | 31:0 | R | sabit sihirli sayı + sürüm | — |
| 0x004 | `CLK_STATUS` | 3:0 | R | bit0 ADC PLL kilitli, bit1 SYSREF görüldü, bit2 JESD link up, bit3 fabric MMCM kilitli | 11 |
| 0x008 | `ADC_OVR_CNT` | 31:0 | R/W1C | ADC overrange olay sayacı (yazınca sıfırlanır) | 9 |
| 0x010 | `NCO_FTW` | 31:0 | R/W | FTW, fs = ADC saati ({{s:adc.fs_msps}} MHz), 2^32 tam tur | 14 |
| 0x014 | `NCO_POW` | 15:0 | R/W | faz ofseti, 2^16 = 360° | 14 |
| 0x018 | `NCO_CTRL` | 2:0 | R/W | bit0 spektral inversion, bit1 dither, bit2 senkron reset (W1P) | 14, 15 |
| 0x020 | `DDC_MODE` | 3:0 | R/W | decimation seçimi: 0=↓4, 1=↓8, 2=↓16 (kademe etkin bitleri) | 16 |
| 0x024 | `FIR_COEF_ADDR` | 7:0 | R/W | katsayı RAM adresi | 16 |
| 0x028 | `FIR_COEF_DATA` | 17:0 | R/W | katsayı, Q1.17 işaretli | 12, 16 |
| 0x02C | `FIR_COEF_COMMIT` | 0 | W1P | çift tamponlu (double-buffered) katsayıları etkinleştir | 16 |
| 0x030 | `FFT_CTRL` | 7:0 | R/W | bit1:0 pencere (0 rect, 1 Hann, 2 BH, 3 Kaiser), bit3:2 log2(N)−8, bit4 overlap %50 | 18, 19 |
| 0x034 | `FFT_SCALE` | 15:0 | R/W | kademe başına kaydırma takvimi — scaling schedule (2 bit × 8 kademe) | 20 |
| 0x040 | `DET_THR_FIXED` | 19:0 | R/W | sabit eşik, güç birimi (I²+Q²), Q4.16 tam ölçek = 1.0 | 21, 23 |
| 0x044 | `CFAR_CTRL` | 15:0 | R/W | bit1:0 tip (0 CA, 1 GO, 2 SO, 3 OS), bit7:2 N/2 (taraf başına), bit11:8 guard, bit12 etkin | 23 |
| 0x048 | `CFAR_ALPHA` | 15:0 | R/W | α, Q6.10 (21.94 → 0x57C2) | 23 |
| 0x04C | `DET_HYST` | 7:0 | R/W | histerezis, 0.25 dB adım (3 dB → 12) | 23 |
| 0x050 | `DET_MIN_PW` | 15:0 | R/W | asgari darbe genişliği, örnek ({{s:ddc.ornek_suresi_ns}} ns) | 23, 26 |
| 0x054 | `DET_MAX_PW` | 23:0 | R/W | azami darbe (CW parçalama), örnek | 26 |
| 0x058 | `NOISE_EST` | 19:0 | R | anlık gürültü tahmini, güç birimi | 23 |
| 0x060 | `PDW_FIFO_LEVEL` | 15:0 | R | FIFO doluluk (128-bit sözcük) | 26 |
| 0x064 | `PDW_FIFO_CTRL` | 3:0 | R/W | bit0 etkin, bit1 taşmada en eskisini at, bit2 sıfırla (W1P) | 26 |
| 0x068 | `PDW_DROP_CNT` | 31:0 | R/W1C | taşma nedeniyle atılan PDW sayısı | 26 |
| 0x06C | `PDW_COUNT` | 31:0 | R | üretilen toplam PDW (sıra numarası kaynağı) | 26 |
| 0x070 | `SNAP_CTRL` | 7:0 | R/W | bit0 tetik kaynağı (0 yazılım, 1 ilk tespit), bit1 kur (arm, W1P), bit2 hazır (R) | 26, 29 |
| 0x074 | `SNAP_LEN` | 15:0 | R/W | yakalama uzunluğu, örnek | 29 |
| 0x078 | `SNAP_PRETRIG` | 15:0 | R/W | tetik öncesi örnek | 29 |
| 0x080 | `IRQ_STATUS` | 7:0 | R/W1C | bit0 FIFO yarım, bit1 FIFO taşma, bit2 ADC overrange, bit3 JESD link düştü, bit4 snapshot hazır | 26 |
| 0x084 | `IRQ_MASK` | 7:0 | R/W | kesme maskesi | 26 |
| 0x090 | `CAL_GAIN_DB` | 15:0 | R/W | dBFS → dBm ofseti, Q8.8 işaretli (kanal başına, sıcaklık düzeltmeli) | 25 |
| 0x094 | `CAL_FREQ_PPM` | 15:0 | R/W | saat düzeltmesi, ppm × 100, işaretli | 25 |
| 0x0A0 | `TEST_GEN_CTRL` | 7:0 | R/W | dahili test üreteci: bit0 etkin, bit2:1 tip (CW, çift ton, darbe, gürültü) | 29 |
| 0x0A4 | `TEST_GEN_FTW` | 31:0 | R/W | test tonu FTW | 29 |

{{svg:g-302-register-bit-haritasi.svg|Üç register'ın bit haritası (kurgusal). CFAR_CTRL alanları ve referans senaryodaki değeri; CFAR_ALPHA'nın Q6.10 yerleşimi ve yanlış Q formatı okumanın sonucu; NCO_FTW'nin 32 bitlik tam tur yorumu.}}

:::saha-notu Register haritasında okunacak ilk üç satır
Bir haritayı ilk kez açtığında şu üçünü ara: (1) **hangi register'ların fs'i
hangisi** — NCO FTW ADC saatiyle, FFT bin'i DDC çıkış saatiyle ölçeklenir;
ikisini karıştırmak sekiz kat hata demektir. (2) **Sabit nokta biçimleri** —
Q6.10 mu Q10.6 mı; yanlış okursan α 21.9 yerine 1.37 olur ve false alarm
patlar. (3) **W1C / W1P alanları** — sayaç sıfırlamak için 1 yazılır, 0
yazmak hiçbir şey yapmaz; "sayaç sıfırlanmıyor" şikâyetlerinin çoğu budur.
:::

## Birim dönüşümleri kütüphanesi

Her dönüşüm önceki bir bölümde türetildi; burada hepsi tek C dosyasında
toplanıyor. Kütüphane RTOS/bare-metal bağımsızdır: donanıma dokunmaz, yalnızca
sayı çevirir. Donanım erişimi ayrı bir katmanda (`reg_write32`) durur; böylece
kütüphane PC'de birim testine sokulabilir ({{bolum:13}}'teki bit-true mantığı
yazılım için de geçerlidir).

```c
/* almac_units.h — birim dönüşümleri (kurgusal harita için; RTOS bağımsız) */
#include <stdint.h>
#include <math.h>

#define ADC_FS_HZ        2400e6      /* NCO ve ADC saati            (B8, B14) */
#define DDC_FS_HZ        300e6       /* DDC çıkışı, FFT ve PDW saati (B16)    */
#define FFT_N            1024
#define LO_HZ            7.6e9       /* low-side LO                  (B6)     */
#define NYQ_ZONE_INV     1           /* 2. bölge: evrik              (B8)     */

/* --- frekans ------------------------------------------------------------ */
static inline uint32_t hz_to_ftw(double f_hz) {                       /* B14 */
    long long v = llround(f_hz / ADC_FS_HZ * 4294967296.0);
    return (uint32_t)(v & 0xFFFFFFFFll);
}
static inline double ftw_to_hz(uint32_t ftw) {
    return (double)(int32_t)ftw / 4294967296.0 * ADC_FS_HZ;
}
static inline double bin_to_hz(int bin) {                             /* B18 */
    /* fftshift'li indeks: 0..N-1 → -fs/2..+fs/2 */
    return ((double)bin - FFT_N / 2) * DDC_FS_HZ / FFT_N;
}
/* baseband ofseti → RF: NCO ekle, bölgeyi aç, LO ekle (B8, B15, B25) */
static inline double baseband_to_rf(double f_bb_hz, uint32_t ftw) {
    double f_alias = f_bb_hz + ftw_to_hz(ftw);          /* 1. Nyquist'te konum */
    double f_if    = NYQ_ZONE_INV ? (ADC_FS_HZ - f_alias) : f_alias;
    return LO_HZ + f_if;                                 /* low-side: RF = LO + IF */
}

/* --- seviye ------------------------------------------------------------- */
static inline double pow_reg_to_dbfs(uint32_t q4_16) {                /* B12, B22 */
    return 10.0 * log10((double)q4_16 / 65536.0);       /* güç birimi: 1.0 = tam ölçek */
}
static inline uint32_t dbfs_to_pow_reg(double dbfs) {
    double lin = pow(10.0, dbfs / 10.0);
    if (lin > 15.99) lin = 15.99;                        /* Q4.16 tavanı */
    return (uint32_t)llround(lin * 65536.0);
}
static inline double dbfs_to_dbm(double dbfs, int16_t cal_q8_8) {     /* B25 */
    return dbfs + (double)cal_q8_8 / 256.0;              /* CAL_GAIN_DB */
}

/* --- tespit ------------------------------------------------------------- */
static inline uint16_t pfa_to_alpha_reg(double pfa, int n_ref) {      /* B23 */
    double a = n_ref * (pow(pfa, -1.0 / n_ref) - 1.0);   /* CA-CFAR */
    if (a > 63.9) a = 63.9;                              /* Q6.10 tavanı */
    return (uint16_t)llround(a * 1024.0);
}
static inline uint8_t db_to_hyst_reg(double db) { return (uint8_t)llround(db / 0.25); }

/* --- zaman --------------------------------------------------------------- */
static inline double samples_to_ns(uint32_t n) { return n * 1e9 / DDC_FS_HZ; }   /* B25 */
static inline uint32_t ns_to_samples(double ns) { return (uint32_t)llround(ns * DDC_FS_HZ / 1e9); }
```

Kütüphaneye üç birim testi ekle; her biri kılavuzdaki bilinen bir cevaptır:
`hz_to_ftw(600e6) == 0x40000000`, `pfa_to_alpha_reg(1e-6, 16) == 0x57C2`
(21.94 · 1024 = 22 467 = 0x57C3 ± 1 yuvarlama), `baseband_to_rf(0, 0x40000000)
== 9.4e9`. Testler geçmiyorsa kartla uğraşma, önce kütüphaneyi düzelt.

:::formul id=rf-geri baslik="Baseband ofsetinden RF'e geri dönüş (referans zincir)"
f: f_{alias} = f_{bb} + f_{NCO}
f: f_{IF} = f_s − f_{alias}      (çift Nyquist bölgesi: evrik)
f: f_{RF} = f_{LO} + f_{IF}      (low-side enjeksiyon)
s: f_{bb} | FFT tepe ya da anlık frekans ölçümü (DDC çıkışında) | Hz
s: f_{NCO} | NCO frekansı (FTW'den) | Hz
s: f_s | ADC örnekleme frekansı | Hz
s: f_{LO} | yerel osilatör | Hz
o: f_bb = 0 → f_alias = {{s:ddc.nco_mhz}} MHz → f_IF = 2400 − 600 = 1800 MHz → f_RF = 7600 + 1800 = **{{s:sinyal.rf_ghz}} GHz** ✓
o: f_bb = +5 MHz ölçüldüyse gerçek RF **9.395 GHz**'dir (evrik bölge işareti çevirir) — Bölüm 8 ve 25.
:::

## Kalibrasyon

Register'lardaki sayılar fiziksel birimlere üç tabloyla bağlanır; üçü de
üretim testinde ölçülüp kalıcı belleğe yazılır ve açılışta yüklenir:

- **Genlik tablosu** (dBFS → dBm): ön uç kazancı frekansa ve sıcaklığa
  bağlıdır. Tablo, birkaç frekans noktasında ve birkaç sıcaklıkta ölçülen
  ofsetleri tutar; yazılım aradeğerleme (interpolasyon) yapıp `CAL_GAIN_DB`'yi günceller.
  Sıcaklık okumasız kalibrasyon tipik olarak birkaç dB kayar ({{bolum:25}}).
- **Frekans düzeltmesi** (ppm): referans osilatörün sapması PDW'deki RF ve TOA
  ölçümünü birlikte kaydırır. Disiplinli sistemlerde harici referans (10 MHz,
  PPS) kullanılır; değilse sıcaklık–ppm eğrisi tabloya girer.
- **Kanal eşleme** (çok kanallı kart): kanallar arası kazanç ve faz farkı
  ({{bolum:14}}'teki senkron reset ve {{bolum:25}}'teki AOA için) bir
  kalibrasyon tonu enjekte edilerek ölçülür; düzeltme PL'de kompleks bir
  katsayı çarpımıyla ya da PS'te PDW sonrası uygulanır.

:::uc-goz
::rf::
RF tarafı kalibrasyon tablosunu "kazanç düzlüğü" ve "sıcaklık katsayısı"
olarak düşünür: preselector'ın bant kenarında 1–2 dB düşüş, LNA'nın
sıcaklıkla ~0.01 dB/°C kayması normaldir. Yazılımcıdan beklediği şey, bu
eğrileri düzeltmesi değil, ölçümü **hangi frekans ve sıcaklıkta** yaptığını
PDW ile birlikte kaydetmesidir; düzeltme sonradan da yapılabilir, kayıp veri
geri gelmez.
::fpga::
PL tarafı için kontrol yüzeyi bir AXI-Lite slave ve bir avuç register
dosyasıdır. İyi pratik: kritik parametreler (katsayılar, α, eşik)
**double-buffered**'dır — PS yeni değerleri yazar, `COMMIT` ile hepsi aynı saat
vuruşunda etkinleşir; yoksa zincir yarı eski yarı yeni ayarlarla birkaç
mikrosaniye çalışır ve bir avuç sahte PDW üretir. Sayaçlar taşmaz, doyar;
durum bitleri **sticky**'dir (yapışkan) ve W1C ile temizlenir.
::yazilim::
Sürücü üç katmandır: (1) register erişimi (`reg_read32/write32`, adres +
maske), (2) birim kütüphanesi (yukarıdaki), (3) yapılandırma nesnesi
(`almac_config_t`: hedef RF, bant, Pfa, N, pencere…) ve onu register'lara
indiren `almac_apply()`. Uygulama yalnızca 3. katmanla konuşur. Her `apply`
sonrası geri okuma ile doğrulama ve bir günlük satırı: "NCO 600.000 MHz
(0x40000000), CFAR CA N=16 α=21.94 (0x57C2), eşik −68 dBm ≙ 0x0A3D".
:::

## Açılış sırası

Zincir aşağıdan yukarı ayağa kalkar; sıra bozulursa belirtiler yanıltıcıdır
(saat kilitlenmeden JESD linki kurulmaz, link kurulmadan ADC verisi gelmez,
veri gelmeden "CFAR çalışmıyor" denir).

{{svg:g-301-acilis-sirasi.svg|Açılış sırası akış şeması. Saat ağacı → ADC/JESD link → kalibrasyon yükleme → DDC ayarı → tespit ayarı → PDW akışı. Her adımın bir doğrulama koşulu ve başarısızlıkta gidilecek Bölüm 29 dalı vardır.}}

1. **Saat ağacı.** Referansı seç, PLL'leri programla, `CLK_STATUS` bit0 ve
   bit3'ü bekle (zaman aşımı ile). Kilit yoksa devam etme: sonraki her adım
   yanlış sonuç verir ({{bolum:11}}).
2. **ADC ve arayüz.** ADC'yi yapılandır, SYSREF üret, JESD linkinin
   kurulmasını bekle (`CLK_STATUS` bit1–2). `ADC_OVR_CNT`'yi sıfırla.
3. **Kalibrasyon.** Kalıcı bellekten tabloları oku, sıcaklığı ölç,
   `CAL_GAIN_DB` ve `CAL_FREQ_PPM`'yi yaz.
4. **DDC.** `NCO_FTW`, `NCO_POW`, `NCO_CTRL` (inversion biti bölgeye göre),
   `DDC_MODE`, katsayılar + `FIR_COEF_COMMIT`. Senkron reset ile çok kanallı
   NCO'ları hizala ({{bolum:14}}).
5. **Frekans kolu.** `FFT_CTRL` (pencere, N), `FFT_SCALE` takvimi ({{bolum:20}}).
6. **Tespit.** Önce sabit eşik yüksekte, CFAR kapalı; `NOISE_EST`'i oku ve
   beklenen gürültü tabanıyla ({{s:turetilmis_beklenen.gurultu_tabani_dbm}} dBm ≙ dBFS karşılığı) karşılaştır;
   makulse `CFAR_ALPHA`, `CFAR_CTRL`, `DET_HYST`, `DET_MIN_PW` yaz ve CFAR'ı aç ({{bolum:23}}).
7. **PDW akışı.** DMA ring buffer'ını kur, `IRQ_MASK` ile FIFO yarım ve taşma
   kesmelerini aç, `PDW_FIFO_CTRL` etkinleştir. İlk 100 PDW'yi günlüğe yaz:
   sıra numaraları ardışık mı, `PDW_DROP_CNT` sıfır mı ({{bolum:26}}).
8. **Self-test (kendi kendini test).** Dahili test üretecini bir CW ton ile aç, PDW'de
   beklenen RF ve PA'yı gör; kapat. Bu adım {{bolum:29}}'daki teşhisin ilk
   dalıdır ve açılışta yapılırsa sahada saatler kazandırır.

```c
/* açılış iskeleti — hata durumunda Bölüm 29'un ilgili dalına gider */
int almac_bringup(const almac_config_t *cfg)
{
    if (clk_init(cfg) != OK)            return FAIL_CLOCK;     /* B11 / B29 dal 1 */
    if (adc_link_init(cfg) != OK)       return FAIL_LINK;      /* B11 / B29 dal 1 */
    cal_load(cfg->kanal);                                      /* B25 */
    ddc_apply(cfg);  fft_apply(cfg);                           /* B14–B20 */
    if (noise_floor_check(cfg) != OK)   return FAIL_NOISE;     /* B23 / B29 dal 3 */
    det_apply(cfg);  pdw_stream_start(cfg);                    /* B23, B26 */
    return selftest_cw(cfg);                                   /* B29 dal 0 */
}
```

:::tuzak Eşiği dBm sanıp dBFS yazmak
Kurgusal vaka: sistem mühendisi "eşik −68 dBm olsun" der. Yazılımcı
`dbfs_to_pow_reg(-68)` yazar; register dBFS bekliyordur ve −68 dBFS, gürültü
tabanının (ADC'de yaklaşık −60 dBFS) **8 dB altındadır**. Eşik gürültünün
içine gömülür, FIFO saniyede yüz binlerce "darbe" ile dolar, `PDW_DROP_CNT`
fırlar. Doğru zincir: dBm → (kalibrasyon ofseti ile) dBFS → güç birimi
register. Kütüphanedeki `dbfs_to_dbm` ve tersi bunun için var; eşiği hep
önce dBFS'e çevir, sonra register'a yaz, sonra geri oku ve günlüğe her iki
birimde bas.
:::

:::tuzak Double buffer yokken katsayı yüklemek
Filtre katsayılarını çalışan zincire tek tek yazarsan her yazma anında
filtre yarı eski yarı yeni bir dürtü yanıtına sahip olur; çıkışta birkaç
mikrosaniyelik geçici bozulma, tespitte bir avuç sahte PDW üretir. Haritada
`FIR_COEF_COMMIT` gibi bir tetikleyici varsa **mutlaka** kullan; yoksa
katsayı değişimini tespiti geçici olarak kapatarak ve PDW akışını
duraklatarak yap, sonra sayaçları sıfırla.
:::

:::tuzak W1C sayaçlara 0 yazmak
`ADC_OVR_CNT`'yi sıfırlamak için 0 yazan kod hiçbir şey yapmaz; sayaç
"write-one-to-clear"dır. Sayaç asla sıfırlanmayınca "ADC sürekli doyuyor"
sanılır ve kazanç gereksiz yere kısılır; hassasiyet düşer. Sürücüde
`reg_clear_w1c(addr)` diye açık bir yardımcı yaz ve haritadaki erişim
sütununu koda yorum olarak taşı.
:::

:::ozet
- Kontrol yüzeyi PL'deki her DSP bloğunun register'larıdır; iyi yüzeyde her register'ın birimi/ölçeği bellidir, geri okunabilir ve hatalar sayaçta birikir.
- Kurgusal harita kategorileri: saat/ADC durumu, DDC (FTW, POW, CTRL, mod, katsayı), FFT (pencere, N, ölçek), tespit (sabit eşik, CFAR tipi/N/guard/α, histerezis, min/max PW), PDW FIFO (seviye, taşma, sayaç), snapshot, kesme, kalibrasyon, test üreteci.
- Birim kütüphanesi: Hz↔FTW (fs = ADC saati), bin↔Hz (fs = DDC saati), baseband→RF (NCO ekle, bölgeyi aç, LO ekle), dBFS↔güç register (Q4.16), dBFS↔dBm (kalibrasyon ofseti), Pfa→α (Q6.10), örnek↔ns.
- Kalibrasyon üç tablodur: genlik (frekans × sıcaklık), frekans (ppm), kanal eşleme (kazanç/faz).
- Açılış sırası: saat → ADC/JESD → kalibrasyon → DDC → FFT → tespit (önce gürültü tabanını doğrula) → PDW akışı → self-test.
- Kritik parametreler double-buffered ve `COMMIT` ile atomik; sayaçlar doyar, durum bitleri sticky'dir (W1C).
- Her `apply` sonrası geri oku ve iki birimde günlüğe yaz.
:::

:::kendini-sina
S: `CFAR_ALPHA` register'ı Q6.10 formatında. N = 16, Pfa = 10⁻⁶ için hangi hex değer yazılır?
C: α = 16·(10⁶ʼ¹⁶ − 1) ≈ 21.94; 21.94 · 1024 ≈ 22 467 = 0x57C3 (yuvarlamaya göre 0x57C2–0x57C3). Q10.6 diye yanlış okunursa 21.94·64 = 1404 = 0x57C yazılır ve α 1.37 olur: false alarm patlar.
S: FFT'de tepe bin 532 çıktı (N = 1024, fftshift'li). Gerçek RF nedir?
C: f_bb = (532 − 512) · 300 MHz / 1024 = +5.86 MHz. f_alias = 605.86 MHz; evrik bölge: f_IF = 2400 − 605.86 = 1794.14 MHz; f_RF = 7600 + 1794.14 = 9394.14 MHz. Evriklik unutulursa 9405.86 MHz denir: 11.7 MHz hata.
S: Açılışta CFAR'ı açmadan önce neden `NOISE_EST` okunur?
C: Gürültü tahmini beklenen tabandan (yaklaşık −83 dBm'in dBFS karşılığı) çok farklıysa zincirin üstünde bir sorun vardır: saat kilitsiz, JESD link yanlış, kazanç ayarı hatalı ya da ADC doyumda. CFAR bu durumda "çalışır" ama anlamsız PDW üretir; hata teşhisi katmanlar aşağıda yapılmalıdır.
S: Katsayı yükleme sırasında neden `COMMIT` register'ı gerekir?
C: Çalışan filtre katsayılarını tek tek değiştirmek, dürtü yanıtını geçici olarak bozar ve birkaç mikrosaniye boyunca sahte tespit üretir. Double buffer + COMMIT tüm katsayıları aynı saat vuruşunda değiştirir.
:::

:::kopru
Kontrol yüzeyi kılavuzun son durağı: darbe antenden girdi, PDW olarak senin
tamponuna düştü ve artık her register'ın arkasındaki mekanizmayı biliyorsun.
Bundan sonrası ekler: sözlük (Ek A), bütün formüller tek sayfada (Ek B),
hızlı hesap tabloları (Ek C), pencere tablosu (Ek D), kaynakça (Ek E) ve
görsel dizini (Ek F). Bir sonraki adım için Ek E'nin son paragrafına bak.
:::
