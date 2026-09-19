# Bölüm 24 — PDW Nedir
::kisim VIII — PDW Üretimi
::meta onkosul=3,22,23 acar=25,26,27,30 blok=pdw rota=yazilimci

:::neden-onemli
Sahadan soru: "DMA tamponuna 16 baytlık kayıtlar düşüyor; hangi bayt ne,
TOA'yı nasıl saniyeye çeviririm?" Bir gömülü yazılımcının almaçla ilk
gerçek teması çoğu zaman budur: PDW. Antenden buraya kadar her blok
örnek üretti; PDW ilk kez örnek değil, **anlam** üretir — "şu anda, şu
frekansta, şu genişlikte bir darbe geldi." Bu bölüm o kaydın ne olduğunu, hangi
alanları taşıdığını, her alanın kaç bit hak ettiğini ve C'de nasıl parse
edildiğini anlatır. Formatı doğru okuyamazsan üstteki bütün zincir boşa
çalışmış olur; formatı doğru tasarlayamazsan FIFO'yu ve DDR bant genişliğini
gereksiz yere yakarsın.
:::

## Sezgi: örnek akışından olay kaydına

{{bolum:22}} ve {{bolum:23}}'te zincir, DDC çıkışındaki I/Q örneklerinden bir
güç zarfı üretti ve bu zarfı adaptif bir eşikle karşılaştırdı. Karşılaştırıcının
çıkışı hâlâ örnek hızında bir bit dizisidir: saniyede 300 milyon kez "var/yok".
Bu bit dizisinin içinde bizi ilgilendiren şey, "yok"ların arasındaki kısa
"var" adacıklarıdır — darbeler. **PDW** (Pulse Descriptor Word — darbe
tanımlayıcı sözcük), her adacığı tek bir sabit uzunluklu kayda sıkıştırır:
ne zaman başladı, ne kadar sürdü, ne kadar güçlüydü, hangi frekanstaydı, hangi
yönden geldi. Örnek akışı bir güvenlik kamerasının ham videosu ise PDW,
"saat 14:03:22'de kapıdan biri girdi, 1.8 m boyunda, mavi ceketli" satırıdır.

:::analoji Uçuş kayıt defteri
Bir havaalanı kulesi radar ekranındaki her pikseli saklamaz; her uçak için
bir satır tutar: çağrı kodu, geliş saati, pist, tip. Ekrandaki milyonlarca
piksel yerine dakikada birkaç satır. PDW de öyledir: darbenin 300 örneğini
değil, o 300 örnekten **çıkarılan** beş-altı sayıyı saklar. Satırın sütunları
sabittir; yeni bir uçak tipi gelince defterin formatı değişmez. Bu sabitlik
sonraki yazılımın (deinterleaving — karışık darbe akışını emiterlere ayırma —, tanımlama; {{bolum:27}}) işini kurar:
yazılım örnek değil, satır tüketir.
:::

## Kavram: veri indirgeme oranı

Neden PDW'ye ihtiyaç var, "ham I/Q'yu kaydedip yazılımda bakalım" neden
yetmez? Sayıya bak. DDC çıkışı {{s:ddc.cikis_fs_msps}} MSPS kompleks,
örnek başına {{s:ddc.cikis_bit_i}} + {{s:ddc.cikis_bit_q}} bit: sürekli
**{{s:ddc.cikis_veri_hizi_gbps}} Gbps**. Referans senaryoda saniyede
{{s:sinyal.prf_hz}} darbe geliyor ve her biri 128 bitlik bir PDW üretiyor: **128
kbps**. Aradaki oran beş basamaklıdır.

:::formul id=pdw-indirgeme baslik="Ham örnekten PDW'ye indirgeme oranı"
f: R_{ham} = f_s · (b_I + b_Q)
f: R_{PDW} = b_{PDW} · PRF
f: İndirgeme = frac{R_{ham}}{R_{PDW}}
s: f_s | DDC çıkış örnekleme hızı | örnek/s
s: b_I, b_Q | I ve Q bit genişliği | bit
s: b_{PDW} | bir PDW'nin uzunluğu | bit
s: PRF | saniyedeki darbe sayısı (1/PRI) | darbe/s
o: R_ham = 300e6 · 32 = **{{s:ddc.cikis_veri_hizi_gbps}} Gbps**; R_PDW = {{s:pdw.bit}} · {{s:sinyal.prf_hz}} = **128 kbps**; indirgeme = **{{s:pdw.indirgeme_orani}} : 1**
o: ADC çıkışından sayarsan ({{s:adc.veri_hizi_gbps_14bit}} Gbps) oran 262 500 : 1; yalnız darbe içindeki örnekleri saysan bile (300 örnek × 32 bit = 9600 bit) PDW 75 kat küçüktür.
:::

{{svg:g-241-indirgeme.svg|Darbeden PDW'ye indirgeme. Üstte 1 ms'lik PRI içinde 1 µs'lik darbe (binde bir doluluk; ölçeksiz çizildi) ve ondan çıkan tek PDW. Altta log ölçekte veri hızları: ADC çıkışı 33.6 Gbps, DDC çıkışı 9.6 Gbps, yalnız darbe örnekleri 9.6 Mbps, PDW akışı 128 kbps. 9.6 Gbps'yi DDR'a yazmak mümkün değildir; 128 kbps'yi bir UART bile taşır.}}

Oran iki şeyi birden söyler. Birincisi, PDW olmadan sistem kurulamaz: 9.6
Gbps'lik akışı sürekli kaydetmek ne bellek ne yazılım açısından
gerçekçidir. İkincisi, PDW **kayıplı** bir özet olduğundan darbenin kaydedilmeyen
her özelliği sonsuza dek gider — darbe içi modülasyonun ince ayrıntısı, kenar
şekli, çakışan ikinci darbe. Bu yüzden iyi tasarımlar PDW'nin yanına
tetiklemeli bir ham I/Q **snapshot** yolu koyar ({{bolum:26}}): şüpheli
darbeler için "videoyu geri sarma" imkânı. Oran ayrıca darbe yoğunluğuyla
doğrusal büyür: saniyede 1 000 değil 1 000 000 darbe gelen yoğun bir
ortamda PDW akışı 128 Mbps'ye çıkar; bu hâlâ taşınabilir ama artık FIFO
derinliği ve DMA politikası tasarım sorusu olur (yine {{bolum:26}}).

## Kavram: tipik PDW alanları

Alanlar iki gruba ayrılır: darbenin fiziksel **ölçümleri** ve almaçın bu
ölçümler hakkında söylediği **meta bilgi**. Aşağıdaki liste açık literatürde
(Wiley, Tsui — {{ek:e}}) tekrarlanan çekirdektir; adlandırma ve sıra
üreticiden üreticiye değişir.

{{tablo: genis}}
| Alan | Ne söyler | Nasıl ölçülür ({{bolum:25}}) | Tipik birim |
|---|---|---|---|
| **TOA** (Time of Arrival) | darbenin geliş anı | eşik geçişinde serbest koşan sayaç örneklenir | örnek sayısı ya da ns; mutlak zamana PPS ile bağlanır |
| **PW** (Pulse Width) | darbe süresi | bitiş geçişi − TOA (eşik/histerezis tanımına bağlı) | örnek ya da ns |
| **PA** (Pulse Amplitude) | darbe gücü | darbe içi tepe ya da kenarlar hariç ortalama güç | dBFS → kalibrasyonla dBm |
| **RF** | taşıyıcı frekansı | darbe içi anlık frekans ortalaması ya da FFT tepesi + NCO/LO geri ekleme | Hz (mutlak) |
| **AOA** (Angle of Arrival) | geliş yönü | genlik karşılaştırma / faz interferometresi / TDOA | derece |
| **MOP** tipi | darbe içi modülasyon var mı, ne tür | anlık frekans/faz profili: eğim, faz atlaması | kod (yok / LFM / faz kodlu / bilinmiyor) |
| **BW** | darbenin kapladığı bant | FFT tepe etrafı −3 dB genişliği ya da LFM süpürme | Hz |
| **SNR / kalite** | ölçümlere ne kadar güvenilir | PA − gürültü tahmini ({{bolum:23}}) | dB ya da kalite kodu |
| **kanal** | hangi anten/almaç kanalı, hangi bant | sabit etiket | kod |
| **bayraklar** | istisnai durumlar | FSM ve ADC durum bitleri | bit alanı |
| **sıra no** | üretim sırası | PDW sayacı | mod 2^k |

Bayraklar küçük ama kıymetli: **CW / parçalı** (darbe azami süreyi aştı,
bu PDW bir parçadır), **pulse-on-pulse** (darbe içinde ikinci bir darbe
başladı, ölçümler karışık olabilir), **kırpılmış** (bir alan sayısal
aralığını aştı — örneğin PW alanı doydu), **doymuş** (darbe sırasında ADC
overrange gördü; PA ve RF güvenilmez), **AOA geçersiz** (tek kanallı ölçüm
ya da kanal uyumsuzluğu). Bayrağı olmayan bir PDW formatı, hatalı ölçümü doğru
ölçümden ayırt edemeyen bir yazılım demektir.

## Kavram: birim, çözünürlük, dinamik aralık → bit sayısı

Her alanın genişliği bir sorunun cevabıdır: *en küçük anlamlı adım nedir* ve
*en büyük değer nedir?* Bu ikisinin oranının log2'si bit sayısını verir. Adımı
gereğinden ince seçmek bit israfıdır — ölçüm zaten o kadar hassas değildir
({{bolum:25}}'te SNR–hata ilişkisi); aralığı gereğinden dar seçmek doyma (saturation) ve
sarma (wrap-around) hatası demektir.

:::formul id=alan-bit baslik="Alan genişliği seçimi"
f: b = ⌈ log_2 ( frac{aralık}{çözünürlük} ) ⌉
s: b | alanın bit sayısı | bit
s: aralık | alanın temsil etmesi gereken en büyük değer (ya da en büyük − en küçük) | alanın birimi
s: çözünürlük | 1 LSB'nin karşılığı | alanın birimi
o: TOA: LSB = 1 örnek = {{s:ddc.ornek_suresi_ns}} ns, **{{s:pdw.toa_bit}} bit** → sarmadan önce 2^48 · 3.333 ns ≈ 10.9 gün. 32 bit seçseydin 14.3 s'de sarardı ve yazılım sarmayı takip etmek zorunda kalırdı.
o: PW: LSB = {{s:pdw.pw_lsb_ns}} ns, **{{s:pdw.pw_bit}} bit** → azami 3.5 ms; 1 µs darbe = {{s:ddc.darbe_ornek_sayisi}}. Daha uzun darbe FSM tarafından parçalanır ({{bolum:26}}).
o: PA: LSB = {{s:pdw.pa_lsb_db}} dB (log ölçek), **{{s:pdw.pa_bit}} bit** → 256 dB aralık; lineer güç saklasaydın 90 dB'lik dinamik aralık için 30 bit gerekirdi.
o: RF: LSB = {{s:pdw.rf_lsb_khz}} kHz, **{{s:pdw.rf_bit}} bit** → mutlak 0–10.49 GHz. {{s:sinyal.rf_ghz}} GHz = 940 000 = 0xE57E0. 10 kHz, 15 dB SNR'da 1 µs darbeden elde edilebilecek en iyi frekans hatasıyla (CRLB ≈ 5.7 kHz, {{bolum:25}}) uyumludur; daha ince bir LSB ölçümün taşımadığı basamak olurdu.
o: AOA: LSB = {{s:pdw.aoa_lsb_derece}}°, **{{s:pdw.aoa_bit}} bit** → 409.6° ≥ 360°; 4095 kodu "geçersiz" için ayrılır.
:::

{{svg:g-242-alan-bit-butcesi.svg|Alan başına bit bütçesi. Her çubuk alanın bit sayısı; yanında LSB'si ve bu LSB ile ulaşılan aralık. Beş ölçüm alanı 110 bit tutar; kalan 18 bit meta bilgiye (bayraklar, sıra numarası, MOP tipi, kanal) gider. Alttaki şerit 128 bitin nasıl dolduğunu gösterir. Bütçe kurgusaldır; ilke değildir: her alanın genişliği aralık/çözünürlük oranından türetilir.}}

Üç tasarım notu. **PA log ölçekte saklanır**; çünkü 0.25 dB'lik adım güçlü
ve zayıf darbede aynı göreli hassasiyeti verir ve kalibrasyon bir toplama
işlemine iner ({{bolum:30}}'daki `CAL_GAIN_DB`). **RF mutlak saklanır**,
baseband ofseti değil; NCO ve LO'yu geri ekleme işi PL'de yapılır ki PDW'yi
tüketen yazılım almaçın iç frekans planını bilmek zorunda kalmasın (zincir
{{bolum:25}}'te). **TOA örnek sayacıyla saklanır**, ns'ye çevrilmiş halde
değil; çarpma PL'de kaynak, yazılımda ise bir satırdır ve sayaç olarak
saklamak yuvarlama hatası biriktirmez.

## Öğretici bir 128-bit PDW formatı (kurgusal)

Aşağıdaki format **kurgusal ve öğreticidir**; hiçbir gerçek ürünün ya da
projenin PDW yapısı değildir. Amacı, yukarıdaki bit bütçesinin dört 32-bit
sözcüğe nasıl yerleştiğini ve C'de nasıl okunduğunu göstermektir. Sözcükler
little-endian, bit 0 en anlamsız bittir; TOA'nın 48 biti iki sözcüğe
yayılır, diğer hiçbir alan sözcük sınırı geçmez.

{{svg:g-240-pdw-bit-haritasi.svg|Kurgusal 128-bit PDW formatının bit alan haritası. W0: TOA'nın alt 32 biti. W1: TOA'nın üst 16 biti, 10 bitlik PA, 6 bitlik bayraklar. W2: 20 bitlik PW, 12 bitlik AOA. W3: 20 bitlik mutlak RF, 8 bitlik sıra numarası, 2 bitlik MOP tipi, 2 bitlik kanal. Mavi alanlar ölçüm, yeşil alanlar meta bilgidir. Format öğretim amaçlıdır.|kaydir}}

| Sözcük | Bit | Alan | Kodlama |
|---|---|---|---|
| W0 | 31:0 | `TOA[31:0]` | örnek sayacı, LSB = {{s:pdw.toa_lsb_ns}} ns (DDC saati) |
| W1 | 15:0 | `TOA[47:32]` | aynı sayacın üst 16 biti |
| W1 | 25:16 | `PA` | dBFS = 0.25 · kod − 255.75 (1023 → 0 dBFS) |
| W1 | 31:26 | `FLAGS` | bit0 SEG (parçalı/CW) · bit1 POP · bit2 CLIP (alan doydu) · bit3 SAT (ADC overrange) · bit4 AOA_INV · bit5 EXT (uzantı sözcüğü izler) |
| W2 | 19:0 | `PW` | örnek, LSB = {{s:pdw.pw_lsb_ns}} ns |
| W2 | 31:20 | `AOA` | derece = 0.1 · kod; 4095 = geçersiz |
| W3 | 19:0 | `RF` | Hz = 10 000 · kod (mutlak RF) |
| W3 | 27:20 | `SEQ` | sıra numarası, mod 256 |
| W3 | 29:28 | `MOP` | 0 yok · 1 LFM · 2 faz kodlu · 3 bilinmiyor |
| W3 | 31:30 | `CH` | kanal / bant kodu |

BW ve SNR bu 128 bite sığmadı; bu bilinçli bir tercih. Bayraklardaki `EXT`
biti, aynı FIFO'ya yazılan ikinci bir 128-bit **uzantı sözcüğünün** (chirp
eğimi, BW, SNR, faz kodu uzunluğu) bu PDW'yi izlediğini söyler ve uzantı
yalnızca MOP ≠ 0 ya da kalite düşükken üretilir. Böylece sıradan darbe 16
bayt, "ilginç" darbe 32 bayt tutar. Gerçek tasarımlar bu dengeyi farklı kurar
— 192 ya da 256 bitlik sabit PDW de yaygındır; ilke aynıdır: **her bit, FIFO
derinliğinden ve DDR bant genişliğinden ödenir.**

## Yazılımcıya dokunan yer

C'de ilk refleks bit alanlı bir `struct` yazmaktır. Yapma: bit alanlarının
sırası, hizalaması ve sözcük sınırı davranışı derleyiciye bağlıdır; aynı kod
başka bir araç zinciriyle sessizce farklı parse eder. Taşınabilir yol dört
`uint32_t` ve kaydır-maskele (shift-and-mask) yardımcılarıdır:

```c
#include <stdint.h>
#include <stdbool.h>

/* Kurgusal, öğretici 128-bit PDW — gerçek bir ürün formatı değildir.
 * 4 × 32-bit little-endian sözcük; DMA tamponunda ardışık. */
typedef struct { uint32_t w[4]; } pdw_raw_t;          /* tam 16 bayt */

#define PDW_TOA_LSB_NS   3.3333333      /* 1 / 300 MSPS */
#define PDW_PW_LSB_NS    3.3333333
#define PDW_PA_LSB_DB    0.25
#define PDW_RF_LSB_HZ    10000.0
#define PDW_AOA_LSB_DEG  0.1

enum { PDW_F_SEG = 1u << 0, PDW_F_POP = 1u << 1, PDW_F_CLIP = 1u << 2,
       PDW_F_SAT = 1u << 3, PDW_F_AOA_INV = 1u << 4, PDW_F_EXT = 1u << 5 };

static inline uint32_t bits(uint32_t w, unsigned lsb, unsigned n)
{ return (w >> lsb) & ((n == 32) ? 0xFFFFFFFFu : ((1u << n) - 1u)); }

typedef struct {
    uint64_t toa_ornek;   /* 48 bit sayaç */
    double   toa_s, pw_s, pa_dbfs, rf_hz, aoa_deg;
    uint8_t  flags, seq, mop, ch;
    bool     aoa_gecerli;
} pdw_t;

static void pdw_parse(const pdw_raw_t *r, pdw_t *o)
{
    o->toa_ornek = ((uint64_t)bits(r->w[1], 0, 16) << 32) | r->w[0];
    o->toa_s     = (double)o->toa_ornek * PDW_TOA_LSB_NS * 1e-9;   /* 64-bit → double: 48 bit tam temsil edilir */
    o->pa_dbfs   = PDW_PA_LSB_DB * bits(r->w[1], 16, 10) - 255.75;
    o->flags     = (uint8_t)bits(r->w[1], 26, 6);
    o->pw_s      = bits(r->w[2], 0, 20) * PDW_PW_LSB_NS * 1e-9;
    uint32_t aoa = bits(r->w[2], 20, 12);
    o->aoa_gecerli = (aoa != 4095u) && !(o->flags & PDW_F_AOA_INV);
    o->aoa_deg   = aoa * PDW_AOA_LSB_DEG;
    o->rf_hz     = bits(r->w[3], 0, 20) * PDW_RF_LSB_HZ;
    o->seq       = (uint8_t)bits(r->w[3], 20, 8);
    o->mop       = (uint8_t)bits(r->w[3], 28, 2);
    o->ch        = (uint8_t)bits(r->w[3], 30, 2);
}

/* Referans senaryodaki darbe (kurgusal değerler):
 *   w[0]=0x1DCD6500 w[1]=0x030F0000 w[2]=0xFFF0012C w[3]=0x00EE57E0
 *   → TOA = 500 000 000 örnek = 1.6667 s, PA = 0.25·783 − 255.75 = −60 dBFS
 *     PW = 300 örnek = 1.000 µs, AOA geçersiz (4095), RF = 940 000 · 10 kHz = 9.4 GHz
 *     SEQ = 14, MOP = 0, CH = 0, flags = 0 */
```

Parse'ın üç hassas noktası: (1) **TOA 64-bit'te birleştirilir**; 32-bit
aritmetikle `w[1] << 32` sıfırlanır ve TOA 14 saniyede bir sarar gibi
görünür. (2) **Birim sabitleri tek yerde** durur ve `scenario`/register
haritasındaki değerlerle aynıdır; PW ve TOA LSB'si DDC saatinden gelir,
ADC saatinden değil — 8 kat hata klasik hatadır ({{bolum:30}}). (3) **Bayraklar
önce okunur**: `SAT` ya da `CLIP` kalkmışsa PA ve RF'e güvenme; `SEG`
kalkmışsa PW bir parçadır, sonraki PDW'lerle birleştirilmelidir; `EXT`
kalkmışsa bir sonraki 16 bayt PDW değil uzantıdır — bunu atlayan bir okuma
döngüsü akışta bir sözcük kayar ve her şeyi çöp okur.

:::uc-goz
::rf::
RF mühendisi PDW'ye "ölçüm raporu" gözüyle bakar ve her alanın arkasındaki
belirsizliği bilmek ister: PA'nın kalibrasyonu hangi sıcaklıkta yapıldı, RF
hangi referansa göre, TOA hangi noktada (eşik mi, %50 mi). PDW'nin sayıları
ancak bu tanımlar belliyse anlamlıdır; iyi bir PDW belgesi format tablosunun
yanına bir "tanımlar" sayfası koyar ({{bolum:25}} tam olarak o sayfadır).
::fpga::
PL'de PDW, FSM'in EMIT durumunda tek saatte paketlenen 128 bitlik bir
vektördür: ölçüm register'ları (TOA latch, PW sayacı, tepe tutucu, faz
biriktirici) sabit konumlara kaydırılıp birleştirilir, sıra sayacı bir
artırılır ve FIFO'ya `wr_en` verilir. 128 bit, AXI-Stream'in 128-bit veri
genişliğine tam oturur; bu yüzden 128 (ya da katları) seçilir — 110 bitlik
"tam yeten" bir sözcük hizalama nedeniyle hiçbir şey kazandırmaz.
::yazilim::
Yazılımcı için PDW bir `struct` değil bir **sözleşmedir**: sürüm numarası
(`ID_VERSION` register'ı — {{bolum:30}}), LSB tablosu, bayrak anlamları. Sürücü
açılışta sürümü okur ve bilmediği bir formatla karşılaşırsa akışı başlatmaz.
Parse fonksiyonu PC'de birim testine sokulur: bilinen dört sözcük → bilinen
fiziksel değerler; yukarıdaki yorumdaki örnek böyle bir testtir.
:::

:::tuzak Bit alanlı struct ile parse
Kurgusal ama sık yaşanır: bir ekip `struct { uint64_t toa:48; uint32_t pw:20;
… }` yazar, geliştirme kartında çalışır. Derleyici ya da hedef değişince PW
sıfır okunmaya, TOA rastgele sıçramaya başlar; çünkü bit alanlarının paketleme
sırası ve 32-bit sınırını geçip geçemeyeceği standartta tanımsızdır.
Belirti: aynı FIFO verisi iki platformda farklı parse edilir. Çözüm:
`uint32_t w[4]` + kaydır-maskele; struct'ın boyutunu `_Static_assert(sizeof
== 16)` ile sabitle.
:::

:::tuzak "PDW'yi ns cinsinden saklayalım"
TOA'yı PL'de ns'ye çevirip saklamak cazip görünür; yazılım çarpma
yapmaz. Ama 3.333… ns tam temsil edilemez: her PDW'de yuvarlanan kesir
milyonlarca darbede birikmez (her TOA bağımsız yuvarlanır), fakat **PRI
ölçümü** iki yuvarlanmış TOA'nın farkıdır ve ±1 ns'lik titreşim kazanır;
kararlı bir PRI'yi "jitter'lı" diye sınıflandırırsın. Sayaç değerini sakla,
dönüşümü tüketen tarafta `double` ile yap; PRI'yi örnek cinsinden hesapla,
en sonda ns'ye çevir.
:::

:::ozet
- PDW, bir darbenin ölçülmüş özelliklerinin sabit formatlı kaydıdır; zincir ilk kez örnek değil olay üretir.
- Referans senaryoda indirgeme 9.6 Gbps → 128 kbps = 75 000 : 1; PDW olmadan sistem kurulamaz, ama PDW kayıplı bir özettir (snapshot yolu bunu telafi eder).
- Çekirdek alanlar TOA, PW, PA, RF, AOA; meta alanlar MOP tipi, BW, SNR/kalite, kanal, bayraklar (SEG, POP, CLIP, SAT, AOA geçersiz), sıra numarası.
- Alan genişliği = ⌈log2(aralık / çözünürlük)⌉: TOA 48 bit @ 3.333 ns (10.9 gün), PW 20 bit (3.5 ms), PA 10 bit @ 0.25 dB log, RF 20 bit @ 10 kHz mutlak, AOA 12 bit @ 0.1°.
- Öğretici 128-bit format: 110 bit ölçüm + 18 bit meta, dört 32-bit little-endian sözcük; yalnız TOA sözcük sınırı geçer; uzantı sözcüğü isteğe bağlı. Format kurgusaldır.
- C'de bit alanlı struct değil, `uint32_t w[4]` + kaydır-maskele; TOA 64-bit'te birleştirilir; LSB sabitleri DDC saatinden gelir; bayraklar ölçümlerden önce okunur.
:::

:::kendini-sina
S: Darbe yoğunluğu saniyede 200 000'e çıkarsa 128-bit PDW akışı kaç Mbps olur ve indirgeme oranı ne olur?
C: 128 bit × 200 000 = 25.6 Mbps. Ham akış değişmediğinden (9.6 Gbps) oran 375 : 1'e düşer. Hâlâ büyük, ama artık FIFO derinliği ve DMA tampon boyutu tasarım kararına dönüşür.
S: TOA alanını 32 bit yapsaydık ne olurdu?
C: 2^32 × 3.333 ns ≈ 14.3 s'de sarardı. Yazılım her PDW'de sarmayı izlemek ve bir "epoch" sayacı tutmak zorunda kalırdı; kaçırılan tek bir PDW (FIFO taşması) sarma sayımını bozabilirdi. 48 bit bu yükü ortadan kaldırır.
S: PA neden lineer güç değil de 0.25 dB adımlı log değer olarak saklanır?
C: Log ölçek güçlü ve zayıf darbede aynı göreli hassasiyeti verir ve dBFS → dBm kalibrasyonu bir toplamaya iner. 90 dB'lik dinamik aralık lineerde 30 bit ister; log'da 0.25 dB adımla 9 bit yeter (10 bit pay bırakır).
S: Bir PDW'de `EXT` bayrağı kalkmışsa okuma döngüsü ne yapmalı?
C: Bir sonraki 128-bit sözcüğü yeni bir PDW olarak değil, bu PDW'nin uzantısı olarak okumalı. Atlarsa akış bir sözcük kayar ve sonraki tüm kayıtlar çöp parse edilir; sıra numarası kontrolü bunu hemen yakalar.
:::

:::kopru
Formatı biliyorsun; şimdi sayıların nereden geldiğine bakalım. TOA'nın "eşik
geçişi" tam olarak hangi an, PW hangi kenar tanımıyla, PA tepe mi ortalama
mı, RF'e 9.4 GHz nasıl yazılıyor ve bütün bunlar SNR düştükçe ne kadar
bozuluyor? Bölüm 25 her alanı tek darbe üzerinde ölçer ve hatasını hesaplar.
:::
