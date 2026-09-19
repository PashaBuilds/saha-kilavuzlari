# Bölüm 3 — Darbeli Sinyalin Anatomisi
::meta onkosul=1,2 acar=16,20,22,25 blok= rota=yazilimci

:::neden-onemli
Sahadan soru: "PDW'de PW 0.9 µs okunuyor ama emiter 1 µs gönderiyor; ölçüm
mü bozuk?" Ya da: "Filtreyi daralttım, gürültü düştü ama darbeler kısaldı ve
tepe seviyesi 4 dB azaldı — neden?" İkisi de darbenin *ne olduğunu* tam
bilmemekten gelir: bir darbe yalnızca "1 µs boyunca açık" değildir; kenarı
vardır, tepesi eğilir, spektrumu tek bir çizgi değil megahertz'lerce
genişlikte bir zarftır ve içinde modülasyon taşıyabilir. Almacın bant
genişliği, örnekleme hızı, eşik histerezisi ve PW/TOA ölçüm doğruluğu hep bu
anatomiye göre seçilir. Bu bölüm, ölçeceğin şeyi ölçmeden önce tanıman içindir.
:::

## Sezgi: kısa süren her şey geniş banttır

Bir kapıyı hızla çarparsan "pat" diye geniş bantlı bir ses çıkar; yavaşça
kapatırsan neredeyse hiç ses çıkmaz. Zaman ekseninde kısa olan şey, frekans
ekseninde geniştir; bu, Fourier'nin en temel takasıdır ve darbeli sinyalin
bütün davranışını belirler. Bir mikrosaniyelik darbe, taşıyıcısı 9.4 GHz'de
olsa bile, taşıyıcının etrafına yaklaşık 1/PW = 1 MHz'lik bir "yayılma"
getirir. Darbe on kat kısalırsa yayılma on kat genişler. Almaç bu yayılmayı
geçirecek kadar geniş olmak zorundadır; geniş oldukça da daha çok gürültü
alır ({{bolum:4}}). Darbe genişliği ile bant genişliği arasındaki bu ip, bu
bölümün omurgasıdır.

:::analoji Deklanşör
Fotoğraf makinesinde deklanşör süresi darbe genişliğidir. Kısa pozlama
hareketi dondurur ama az ışık toplar; uzun pozlama çok ışık toplar ama
bulanıklaştırır. Radar da aynı takası yaşar: kısa darbe menzil çözünürlüğü
verir ama enerjisi azdır; uzun darbe enerji taşır ama çözünürlük kaybeder.
Darbe içi modülasyon (LFM, faz kodu) bu takası kırmanın hilesidir: uzun
darbenin enerjisini, kısa darbenin bant genişliğiyle birleştirir.
:::

## Kavram: darbenin ölçü noktaları

{{svg:g-30-darbe-anatomisi.svg|Darbe anatomisi. Üstte tek darbenin zarfı: tepe genliği (PA), %10–%90 yükselme süresi, düşme süresi, tepe aşımı (overshoot), tepe eğimi (droop) ve %50 noktaları arasında ölçülen PW = 1 µs; zarfın içinde taşıyıcı. Altta darbe katarı: PRI = 1 ms, PRF = 1 kHz, duty = %0.1 — bu ölçekte 1 µs darbe bir çizgi kalınlığındadır; ortalama güç tepenin 30 dB altında.}}

Bir darbeyi tarif eden büyüklükler, PDW'nin alanlarıyla neredeyse birebir
örtüşür ({{bolum:24}}):

- **PW** (pulse width — darbe genişliği): darbenin "açık" süresi. Tanımı
  kritik: bu kılavuzda ve çoğu EH sisteminde **%50 genlik noktaları** (yani
  güçte −6 dB) arasıdır; bazı kaynaklar gücün %50'sini (−3 dB genlik noktası,
  %70.7) kullanır. Kenar 50 ns iken iki tanım arasındaki fark ~15 ns'dir —
  "0.9 µs okunuyor" sorusunun cevaplarından biri budur.
- **PA** (pulse amplitude — darbe genliği): tepe seviyesi; dBm ya da dBFS.
- **Yükselme / düşme süresi** (rise/fall time): genliğin %10'dan %90'a
  çıkması / inmesi için geçen süre. Referans darbede {{s:sinyal.rise_time_ns}} ns.
  Kenar ne kadar dikse TOA o kadar keskin ölçülür ({{bolum:25}}) ve
  spektrum o kadar geniş olur.
- **Overshoot** (tepe aşımı) ve **droop** (tepe eğimi): vericinin
  modülatöründen gelen kusurlar; darbenin "parmak izi"dir, emiter
  tanımlamada kullanılır ama PW/PA ölçümünü de bozar.
- **PRI** (pulse repetition interval — darbe tekrar aralığı) ve tersi
  **PRF** (pulse repetition frequency): ardışık iki darbenin başlangıçları
  arasındaki süre. **Duty cycle** (görev oranı): PW/PRI.

:::formul id=darbe-katari baslik="PRF, duty ve ortalama güç"
f: PRF = frac{1}{PRI}      duty = frac{PW}{PRI}      P_{ort} = P_{tepe} · duty
s: PRI | darbe tekrar aralığı | s
s: PRF | darbe tekrar frekansı | Hz
s: PW | darbe genişliği (%50 noktaları arası) | s
s: P_{tepe}, P_{ort} | tepe ve ortalama güç | W (dBm'de: P_ort = P_tepe + 10·log duty)
o: PRI = {{s:sinyal.pri_ms}} ms → PRF = **{{s:sinyal.prf_hz}} Hz**; PW = {{s:sinyal.pw_us}} µs → duty = **%{{s:sinyal.duty_yuzde}}**; ortalama güç tepenin 10·log(0.001) = **30 dB** altında: {{s:sinyal.seviye_dbm_giris}} dBm tepe → −90 dBm ortalama.
:::

Ortalama gücün tepeden 30 dB aşağıda olması, EH almacının neden **tek
darbeyle** çalışmak zorunda olduğunu anlatır: darbeler arası 999 µs boşlukta
ortalama alacak bir şey yoktur; darbe geldiği mikrosaniyede yakalanmalı ve
ölçülmelidir. Radar almacı ise kendi darbelerini bildiği için yüzlerce darbeyi
koherent toplayabilir; aradaki hassasiyet farkının bir kaynağı budur
({{bolum:0}}'daki karşılaştırma tablosu).

## Kavram: darbe katarının spektrumu — sinc zarfı ve PRF çizgileri

Tek bir dikdörtgen darbenin spektrumu **sinc** fonksiyonudur: taşıyıcı
etrafında bir ana lob, iki yanında gittikçe küçülen yan loblar. Ana lobun
sıfırları taşıyıcıdan ±1/PW uzaktadır; ilk yan lob ana lobdan 13.3 dB
aşağıdadır ve yan loblar ancak 1/f hızıyla söner — dikdörtgen darbe
"kirli" bir spektrumdur. Darbe periyodik tekrarlanınca bu sürekli zarf,
PRF aralıklı **ayrık çizgilere** bölünür: zarf aynı kalır, altında yalnızca
$k·PRF$ frekanslarında çizgiler bulunur. Referans senaryoda ana lob 2 MHz,
çizgi aralığı 1 kHz; ana lobun içinde iki bin çizgi vardır.

:::formul id=darbe-spektrum baslik="Dikdörtgen darbenin spektrumu"
f: |X(f)| ∝ PW · |sinc(f · PW)|      sinc(x) = frac{sin(πx)}{πx}
f: B_{sıfır−sıfır} = frac{2}{PW}      B_{−3dB} ≈ frac{0.886}{PW}      çizgi aralığı = PRF
s: f | taşıyıcıdan uzaklık | Hz
s: B_{sıfır−sıfır} | ana lob genişliği (ilk sıfırlar arası) | Hz
s: B_{−3dB} | ana lobun yarı güç genişliği | Hz
o: PW = {{s:sinyal.pw_us}} µs → ilk sıfır 1 MHz, ana lob **{{s:turetilmis_beklenen.ana_lob_null_null_mhz}} MHz**, −3 dB genişliği 886 kHz. Anten girişi pasaportundaki "≈ 2 MHz" buradan gelir.
o: PW = 0.25 µs → ana lob 8 MHz. Aynı almaç bandı içinde dört kat daha geniş yayılma; bant 2 MHz'te kalsaydı bu darbenin enerjisinin çoğu dışarıda kalırdı.
:::

{{svg:g-31-pw-spektrum.svg|Darbe genişliği ile spektrum (hesaplanmış). Üstte 1 µs darbe: ilk sıfır 1 MHz, ana lob 2 MHz, −3 dB genişliği 886 kHz, ilk yan lob −13.3 dB. Altta 0.25 µs darbe: ana lob 8 MHz. Sağ üstteki büyüteç zarfın altındaki PRF = 1 kHz aralıklı çizgileri gösterir; zarfın şekli PW'ye, çizgi sıklığı PRI'ye bağlıdır.}}

"Bant genişliği ≈ 1/PW" kaba kuralı bu şekilden çıkar; ama hangi bant
genişliği? −3 dB'de 0.886/PW, sıfırdan sıfıra 2/PW, enerjinin %90'ını
tutmak için yaklaşık 1/PW. Almaç tasarımcısı genellikle IF/DDC filtresini
**1/PW ile 2/PW arasında** seçer: daha darsa darbenin kenarı yumuşar
(yükselme süresi filtreye göre uzar), tepesi düşer ve PW ölçümü kayar; daha
genişse gereksiz gürültü girer ({{bolum:4}}, {{bolum:16}}). Kenar ile bant
genişliği arasında da bir kural vardır: bir alçak geçiren sistemin
%10–%90 yükselme süresi yaklaşık **0.35/B**'dir; taşıyıcı etrafındaki
B_IF genişliğinde bir bant geçiren filtre için zarfın bandı B_IF/2
olduğundan **t_r ≈ 0.7/B_IF**. Filtre 2 MHz ise kenar en iyi ihtimalle
350 ns olur — emiterin 50 ns'lik kenarı almaçta görünmez; almaç kendi
kenarını dayatır. Tersten: 50 ns'lik kenarı korumak 14 MHz'lik IF bandı
ister. TOA doğruluğunun neden filtre bant genişliğine bağlı olduğu
({{bolum:25}}) burada saklıdır.

## Kavram: darbe içi modülasyon (MOP)

Modern radarların çoğu darbenin içini boş bırakmaz; frekansı ya da fazı
darbe boyunca değiştirir. Buna **MOP** (modulation on pulse — darbe içi
modülasyon) denir. Amaç, uzun darbenin enerjisiyle kısa darbenin
çözünürlüğünü birleştirmektir (darbe sıkıştırma); EH almacı için sonucu,
bant genişliğinin artık 1/PW'den bağımsız ve çok daha geniş olabilmesidir.

{{svg:g-32-mop-turleri.svg|Dört MOP türünün üç görünümü (hesaplanmış, PW = 1 µs). Sütunlar: modülasyonsuz darbe; 10 MHz LFM chirp; Barker-13 faz kodu; dört adımlı frekans atlamalı darbe. Satırlar: zaman dalga şekli, darbe boyunca anlık frekans ya da faz, genlik spektrumu. Sabit darbede bant ≈ 1/PW = 1 MHz; LFM'de ≈ 10 MHz; Barker-13'te ≈ 13/PW = 13 MHz; atlamalıda adımlar ayrı ayrı görünür.}}

- **LFM / chirp** (linear frequency modulation): anlık frekans darbe boyunca
  doğrusal olarak B kadar süpürülür. Spektrum yaklaşık B genişliğinde ve
  dikdörtgene yakın düzdür (B·PW ≫ 1 iken). Referans senaryonun B varyantı:
  {{s:sinyal.varyant_b.chirp_bw_mhz}} MHz, 1 µs → **B·T = 10**; almaç bandı
  en az 10 MHz olmalı, DDC çıkışında ({{bolum:15}}) darbe artık sabit değil
  eğimli bir anlık frekans çizgisi olarak görünür ({{bolum:20}}).
- **Faz kodlu** (Barker, poliphase): darbe N "chip"e bölünür, her chip'te
  faz 0° ya da 180°. Bant genişliği ≈ 1/(chip süresi) = N/PW; Barker-13 için
  13 MHz. Anlık frekans hesabı ({{bolum:2}}) chip sınırlarında ±fs/2'ye
  fırlayan sıçramalar gösterir — MOP tanıma bunu kullanır.
- **Frekans atlamalı** (frequency agile / hopping): darbe içinde ya da
  darbeden darbeye taşıyıcı adım adım değişir. Almaç ya çok geniş banda
  bakar ya da her adımı ayrı darbe sanır.
- **CW ve FMCW**: darbe yok (duty %100); FMCW'de frekans sürekli süpürülür.
  Darbe FSM'i için ({{bolum:26}}) "hiç bitmeyen darbe" demektir; ayrı
  işlenir ({{bolum:27}}).

:::formul id=lfm baslik="LFM chirp: bant genişliği, eğim ve B·T çarpımı"
f: f_{anlık}(t) = f_0 + frac{B}{PW} · (t − frac{PW}{2})      B · T = B · PW
s: B | süpürme (chirp) bant genişliği | Hz
s: B/PW | chirp eğimi | Hz/s
s: B·T | zaman–bant genişliği çarpımı; sıkıştırma oranı ve işlem kazancı (10·log) | —
o: B = {{s:sinyal.varyant_b.chirp_bw_mhz}} MHz, PW = {{s:sinyal.pw_us}} µs → eğim 10 MHz/µs, B·T = 10, radar tarafında sıkıştırma kazancı 10 dB. EH almacı için: bant 1 MHz'ten 10 MHz'e çıktı, gürültü tabanı 10 dB yükseldi.
:::

## Kavram: PRI türleri (tanım düzeyi)

Darbeden darbeye PRI'nin nasıl değiştiği emiterin kimliğidir ve PDW
akışını yorumlayan yazılımın ({{bolum:27}}) işidir; burada yalnızca adları:

| PRI türü | Davranış | Almaca etkisi |
|---|---|---|
| Sabit | PRI değişmez | en kolay; TOA farkları tek değerde toplanır |
| Stagger | birkaç PRI değeri sabit sırayla döner | TOA farkları birkaç ayrık değerde kümelenir |
| Jitter | PRI rastgele (örn. ±%10) | fark histogramı yayvan; PRI "ortalama ± sapma" ile verilir |
| Dwell & switch | bir PRI ile bir süre, sonra başka bir PRI | zaman içinde bloklar halinde değişim |
| Sliding | PRI monoton artar/azalır, sonra sıfırlanır | testere dişi fark dizisi |

Almaç donanımı bunların hiçbirini bilmek zorunda değildir: her darbeyi tek
tek yakalar ve TOA'sını yazar; PRI analizi yazılımda, TOA farklarından
yapılır. Ama donanımın **TOA çözünürlüğü** ({{s:ddc.ornek_suresi_ns}} ns,
bir örnek) jitter'ı stagger'dan ayırt edebilme sınırını belirler.

:::widget id=w03 ad="Darbe katarı ↔ spektrum"
- **Referans senaryo**: 1 µs, PRI 1 ms. Spektrumda ilk sıfır 1 MHz, −3 dB genişliği 886 kHz, ilk yan lob −13.3 dB. Sonuç satırında ana lobda ≈ 2000 çizgi olduğunu, bu ölçekte çizilemediğini oku. PRI'yi 10 µs'ye indir (**Yüksek PRF** preset'i): çizgiler 100 kHz aralıkla görünür olsun, ana lobda 20 çizgi; duty %10, ortalama güç tepenin 10 dB altına çıksın.
- PW'yi 1 µs'den 0.2 µs'ye indir (**Kısa darbe** preset'i): ana lob 2 MHz'ten 10 MHz'e açılsın; zarfın şekli aynı, yalnızca ölçeği değişir.
- Yükselme süresini 0'dan 300 ns'ye çek: zaman çiziminde kenar yumuşasın, spektrumda yan loblar hızla çöksün (dik kenar = uzak yan loblar). "Kenar için gereken IF bandı ≈ 0.7/t_r" satırı 50 ns için 14 MHz gösterir: kenarı korumak, ana lobdan çok daha geniş bant ister.
- **Varyant B: LFM 10 MHz**: spektrum 1 MHz'lik sinc'ten 10 MHz'lik düz bir bloğa dönüşsün; B·T = 10. **Barker-13**: 13 chip, spektrum ≈ 13 MHz; zaman çiziminde kırmızı chip sınırlarında fazın 180° döndüğünü gör.
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Darbenin anatomisi almacın analog bant genişliğini belirler: IF filtre en az
darbenin ana lobunu (2/PW) geçirmeli; LFM/faz kodlu emiterler için B ya da
N/PW kadar açılmalı. EH almacı emiteri bilmediği için bandı en kötü duruma
göre geniş tutar ({{bolum:5}}); bedeli {{bolum:4}}'te. Filtrenin **grup
gecikmesi** darbenin kenarını yayar ve bant içinde düz değilse LFM'in
farklı frekans dilimlerini farklı zamanlarda geçirir; bu, chirp'in
ölçülen eğimini bozar. Vericinin overshoot/droop'u ise almacın işi değil,
emiter parmak izidir.
::fpga::
DDC çıkışında ({{s:ddc.cikis_fs_msps}} MSPS) 1 µs darbe **{{s:ddc.darbe_ornek_sayisi}}
örnektir**; 50 ns kenar 15 örnek, Barker-13'ün 77 ns'lik chip'i 23 örnek.
Darbe FSM'i ({{bolum:26}}) PW'yi örnek sayarak ölçer: eşik aşılınca sayaç
başlar, altına inince durur; çözünürlük bir örnek = {{s:ddc.ornek_suresi_ns}} ns.
Yükselme süresi kenardaki örnek sayısından, anlık frekans ardışık faz
farklarından ({{bolum:2}}) çıkar; LFM eğimi bu farkların darbe boyunca
doğrusal artışından ({{bolum:25}}). Kısa darbe (0.1 µs = 30 örnek) için
PW ölçüm hatası %3'e çıkar; **min PW** register'ı ({{s:tespit.min_pw_ornek}}
örnek) bundan daha kısa "darbeleri" gürültü sayar.
::yazilim::
PDW'de PW ve TOA, örnek periyodu LSB'siyle tam sayıdır: {{s:pdw.pw_lsb_ns}} ns.
Yazılımcı bunları saniyeye çevirirken fs'in *DDC çıkış hızı* olduğunu
bilmelidir, ADC hızı değil. PW tanımı (%50 genlik mi, güç eşiği mi)
donanımın eşik yapısına gömülüdür; emiter kütüphanesiyle karşılaştırırken
aynı tanımı kullan. PRI, ardışık TOA'ların farkıdır; stagger/jitter
ayrımı için farkların histogramına bakılır. Duty ve ortalama güç PDW'den
türetilir, ölçülmez.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>

#define FS_DDC_HZ      300000000.0     /* DDC çıkış hızı — PW/TOA LSB'si buna göre */
#define ORNEK_NS       (1e9 / FS_DDC_HZ)   /* 3.333 ns */

/* PDW'den gelen ham alanlar (KURGUSAL format; Bölüm 24'te tanımlanır). */
typedef struct { uint64_t toa_lsb; uint32_t pw_lsb; int16_t pa_q88; } pdw_ham_t;

static double pw_us(const pdw_ham_t *p)  { return p->pw_lsb * ORNEK_NS / 1e3; }
static double toa_us(const pdw_ham_t *p) { return (double)p->toa_lsb * ORNEK_NS / 1e3; }

/* Ardışık iki PDW'den PRI (µs) ve duty. TOA 64 bit: 3.33 ns LSB ile ~1950 yıl sarmaz. */
static double pri_us(const pdw_ham_t *onceki, const pdw_ham_t *simdiki)
{
    return (double)(simdiki->toa_lsb - onceki->toa_lsb) * ORNEK_NS / 1e3;
}
static double duty(const pdw_ham_t *onceki, const pdw_ham_t *simdiki)
{
    double pri = pri_us(onceki, simdiki);
    return pri > 0 ? pw_us(simdiki) / pri : 0.0;
}
/* Ortalama güç (dBm) = tepe + 10·log10(duty); dBm toplanmaz, log eklenir (Bölüm 1). */

/* referans senaryo: pw_lsb = 300 → 1.000 µs; TOA farkı 300 000 LSB → PRI 1000 µs; duty 0.001 */
```

Dikkat edilecekler: PW'yi 32 bit tutan format en fazla $2^{32}·3.33$ ns ≈ 14 s
darbe taşır (CW için ayrı bayrak gerekir, {{bolum:24}}); TOA farkı alırken
unsigned aritmetik sarma güvenlidir ama iki farklı kanalın TOA'sı aynı
sayaçtan gelmiyorsa fark anlamsızdır ({{bolum:11}}).

:::tuzak "PW yanlış ölçülüyor" — hangi PW?
Emiter 1.00 µs gönderir, PDW 0.93 µs yazar, ekip donanımı suçlar. Oysa üç
tanım farkı üst üste binmiştir: (1) emiterin PW'si %50 genlikte tanımlı,
almacın eşiği gücün %50'sinde (−3 dB) — kenar başına ~7 ns fark; (2) almaç
filtresi kenarı 350 ns'ye yaymış, eşik sabit dBm'de olduğundan zayıf
darbede eşik geçişi kenarın daha yukarısında, PW daha kısa (SNR'a bağlı
"kısalma", {{bolum:25}}); (3) histerezis düşüş eşiği yükseliş eşiğinden
3 dB aşağıda, bu da PW'yi *uzatır*. Doğru refleks: bilinen bir test darbesiyle
almacın PW'sini SNR'a karşı çizmek ve PDW'yi buna göre yorumlamak; donanımı
değil tanımı düzeltmek.
:::

:::tuzak "Bandı daralttım, hassasiyet arttı"
Filtreyi 2 MHz'ten 500 kHz'e indirmek gürültü tabanını 6 dB düşürür; ama
1 µs darbenin ana lobunun büyük kısmı artık filtrenin dışındadır: tepe
seviyesi birkaç dB düşer, kenar ≈ 0.7/500 kHz = 1.4 µs'ye — darbenin
kendisinden uzun bir süreye — yayılır, darbe üçgene döner. Net SNR kazancı
sıfıra yakındır, PW ve TOA ölçümü ise belirgin bozulur. Darbeli sinyal için "en iyi" bant genişliği 1/PW
civarındadır (darbeye uyarlanmış **matched bant**); daha dar değil. LFM'de sınır B'dir: 10 MHz'lik
chirp'i 2 MHz'lik filtreden geçirmek darbeyi parçalara böler ve
frekans ölçümünü anlamsızlaştırır.
:::

:::ozet
- Darbeyi PW (%50 noktaları — tanımı belirt), PA, yükselme/düşme süresi, overshoot/droop, PRI/PRF ve duty tarif eder; bunlar PDW alanlarıyla örtüşür.
- P_ort = P_tepe · duty: %0.1 duty ile ortalama güç tepenin 30 dB altında → EH almacı tek darbeyle çalışır.
- Dikdörtgen darbenin spektrumu sinc'tir: ilk sıfır 1/PW, ana lob 2/PW, −3 dB 0.886/PW, ilk yan lob −13.3 dB; darbe kısaldıkça spektrum genişler.
- Periyodik katar, zarfı PRF aralıklı çizgilere böler; zarfın şekli PW'ye, çizgi sıklığı PRI'ye bağlıdır.
- Kenar ↔ bant: yükselme süresi ≈ 0.35/B (alçak geçiren) ≈ 0.7/B_IF (bant geçiren); almaç filtresi emiterin kenarını kendi kenarıyla değiştirir.
- MOP bant genişliğini 1/PW'den koparır: LFM ≈ B (B·T çarpımı), faz kodlu ≈ N/PW, atlamalı adımlara yayılır; CW/FMCW'nin darbesi yoktur.
- PRI türleri (sabit, stagger, jitter, dwell-switch, sliding) yazılımda TOA farklarından çıkarılır; donanım yalnızca her darbeyi yakalar.
:::

:::kendini-sina
S: 0.5 µs'lik bir darbe için ana lob genişliği, −3 dB bant genişliği ve önerilen almaç filtre bandı nedir?
C: Ana lob 2/PW = 4 MHz, −3 dB genişliği 0.886/0.5 µs = 1.77 MHz. Filtre 1/PW–2/PW arası, yani 2–4 MHz; gürültü tabanı 1 µs darbeye göre 3 dB daha yüksek olur.
S: PRI 250 µs, PW 2 µs olan bir emiterin duty'si ve ortalama/tepe güç oranı nedir? Spektrumda çizgi aralığı kaçtır?
C: duty = 2/250 = %0.8; ortalama güç tepenin 10·log(0.008) = −21 dB altında. Çizgi aralığı PRF = 4 kHz; 1 MHz'lik ana lobda 250 çizgi.
S: 20 MHz'lik LFM taşıyan 2 µs'lik darbe için B·T çarpımı nedir; almacın bandı 2/PW = 1 MHz'e göre seçilseydi ne olurdu?
C: B·T = 40. 1 MHz'lik bant chirp'in yalnızca 1/20'sini, yani darbenin 100 ns'lik bir dilimini geçirir: almaç 2 µs yerine ~0.1 µs'lik zayıf bir darbe görür, frekansı chirp'in filtreden geçen dilimine göre okur, PW ve MOP tamamen yanlış olur.
S: Bir almacın yükselme süresi ölçümleri hangi emiter gelirse gelsin 180 ns civarında çıkıyor. Neden?
C: Almacın (IF/DDC) filtre bandı yaklaşık 0.7/180 ns ≈ 4 MHz; emiterin kenarı bundan dikse almaç kendi kenarını dayatır. Ölçülen 180 ns emiterin değil almacın parmak izidir; yükselme süresini emiter parametresi olarak kullanmadan önce almaç bandının izin verdiği sınırı bil.
:::

:::kopru
Darbenin spektrumu almacın bant genişliğini dayattı; bant genişliği ise
almacın göreceği gürültünün miktarını belirler. Bölüm 4, o gürültünün
nereden geldiğini (kTB), zincirde nasıl büyüdüğünü (Friis) ve almacın
"−68 dBm'e kadar duyar" cümlesinin tam olarak nasıl hesaplandığını anlatır.
Bu bölümdeki 2 MHz ile 300 MHz arasındaki 21.8 dB'lik fark, orada EH
almacının temel ikilemi olarak geri gelecek.
:::
