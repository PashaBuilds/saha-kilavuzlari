# Bölüm 19 — Pencereleme
::meta onkosul=3,16,18 acar=20,23,25 blok=fft rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "Güçlü bir emiterin 3 MHz yanındaki zayıf emiteri FFT'de
göremiyoruz; ADC'nin dinamik aralığı yetmiyor mu?" Çoğu zaman yetiyordur;
görmeyi engelleyen ADC değil, FFT'ye dikdörtgen pencereyle girilmiş
olmasıdır. Güçlü tonun yan lobları 12 bin ötede hâlâ −32 dB'dedir ve −70
dBFS'lik komşu o zarfın 40 dB altında kalır. Bir register'la pencereyi
Blackman-Harris'e çevirdiğinde zayıf emiter ortaya çıkar; bedeli, ana lobun
iki katına genişlemesi ve gürültü tabanının 3 dB yükselmesidir. Pencere seçimi
FFT tabanlı ölçümde bit sayısı kadar belirleyicidir ve tamamen senin
elindedir: `WIN_SEL` register'ı. Bu bölüm o register'ın her değerinin ne
aldığını, ne verdiğini sayılarla kurar.
:::

## Sezgi: kapıyı çarpmadan kapatmak

{{bolum:18}}'de gördük: DFT, N örneklik çerçeveyi sonsuza dek tekrarlanıyor
sayar. Çerçevenin sonundaki örnekle başındaki örnek birbirini tutmuyorsa
tekrarın her ekleminde bir sıçrama vardır; sıçrama, kapının çarpılmasıdır —
kısa ve geniş bantlı bir ses. Spektrumda bu ses, sinc yan lobları olarak
görünür. Pencere (window), kapıyı çarpmadan kapatmaktır: çerçevenin başını ve sonunu
yumuşakça sıfıra indiren bir eğriyle örnekleri çarparsın; eklemde artık
sıçrama yoktur, çünkü iki taraf da sıfırdır.

Matematiksel olarak sonlu gözlem zaten bir pencereleme işlemidir: N örnek
almak, sonsuz sinyali **dikdörtgen** bir pencereyle çarpmaktır ve zaman
domaininde çarpım frekans domaininde **konvolüsyondur** ({{bolum:3}}'te
darbenin spektrumu için aynı kural). Sinyalin her spektral çizgisi,
pencerenin spektrumuyla (dikdörtgen için sinc) bulanır. Dikdörtgeni başka bir
şekille değiştirmek, bulanıklığın *biçimini* seçmektir: sinc'in dar ama yavaş
sönen yan lobları yerine daha geniş ama hızla çöken bir ana lob.

:::analoji Fotoğraf makinesinin diyaframı
Keskin kenarlı bir diyafram (dikdörtgen pencere) parlak bir yıldızın etrafında
uzun kırınım ışınları üretir; ışınlar sönük komşu yıldızı örter. Kenarları
yumuşatılmış (apodize edilmiş) bir diyafram ışınları söndürür, ama yıldızın
kendisi biraz daha büyük bir leke olur. Astronomlar "apodizasyon", DSP'ciler
"pencereleme" der; takas aynıdır: yan lob bastırma ↔ ana lob genişliği.
:::

## Kavram: pencere ailesi ve dört sayı

Her pencere dört sayıyla tarif edilir ve dördü de aynı takasın yüzleridir:

- **Ana lob genişliği** (−3 dB, bin): iki yakın tonu ayırma sınırı. Dar iyi.
- **En yüksek yan lob** (dB): güçlü tonun yanında zayıf ton görme sınırı. Düşük iyi.
- **ENBW** (Equivalent Noise Bandwidth — eşdeğer gürültü bant genişliği, bin):
  bir bin'in kaç bin genişliğinde gürültü topladığı; taban 10·log10(ENBW)
  kadar yükselir. Küçük iyi.
- **Scalloping kaybı** (dB): tonun iki bin arasına düşmesinin en kötü kaybı;
  genlik doğruluğu. Küçük iyi.

Bir de **coherent gain** (CG): pencerenin ortalama değeri, yani tepe genliğini
ne kadar düşürdüğü. Bu bir kayıp değildir; dBFS ölçeğinde $∑w$'ye bölerek
tamamen telafi edilir ({{bolum:18}}'deki formül). Ama telafi etmeyi unutan
yazılım Hann'da 6 dB, Blackman-Harris'te 8.9 dB düşük seviye okur.

{{svg:g-190-pencere-galerisi.svg|Altı pencerenin zaman şekli (üst küçük panel, altın) ve frekans yanıtı (alt panel, ±12 bin, dB; hesaplanmış). Dikdörtgen: 1 bin ana lob, −13.3 dB yan lob. Hann: yan lob −31.5 dB ve uzaklıkla hızla düşer. Hamming: ilk yan lobu −42.7 dB'ye bastırır ama uzak yan loblar yavaş düşer (Hann'ın altına inemez). Blackman-Harris 4 terim: −92 dB, 2 bin ana lob. Kaiser β = 8: ayarlanabilir orta yol. Flat-top: 3.75 bin genişliğinde düz tepe, 0.01 dB scalloping — genlik ölçümü için. Her panelde Ek D'den en yüksek yan lob, ENBW ve scalloping kaybı yazılıdır.}}

Galeriyi okurken üç kalıbı yakala. **Hann ↔ Hamming:** ikisi de yükseltilmiş
kosinüstür; Hamming katsayıları ilk yan lobu bastıracak biçimde ayarlanmıştır
(0.54/0.46) ama uçları sıfıra inmez, bu yüzden uzak yan lobları 6 dB/oktav
ile yavaş düşer; Hann uçlarda sıfırdır ve 18 dB/oktav ile çöker. Yakın komşu
için Hamming, uzak güçlü emiter için Hann. **Blackman-Harris ↔ Kaiser ↔
Chebyshev:** hepsi "yan lobu istediğin kadar bastır, ana lobu o kadar
genişlet" ailesi; Kaiser'de β, Chebyshev'de yan lob seviyesi doğrudan
parametredir, Chebyshev tüm yan lobları eşit yükseklikte tutar (equiripple).
**Flat-top:** ana lobu bilerek düzleştirilmiş; frekans çözünürlüğünü feda
edip genlik doğruluğu alır — kalibrasyon ve PA ölçümü penceresi, tespit
penceresi değil.

{{tablo: genis}}
| Pencere | −3 dB ana lob (bin) | En yüksek yan lob (dB) | Yan lob düşüşü | ENBW (bin) | CG (dB) | Scalloping (dB) |
|---|---|---|---|---|---|---|
| Dikdörtgen | 1.00 | −13.3 | 6 dB/oktav | 1.000 | 0.00 | 3.92 |
| Hann | 1.50 | −31.5 | 18 dB/oktav | 1.500 | −6.02 | 1.42 |
| Hamming | 1.38 | −42.7 | 6 dB/oktav | 1.363 | −5.35 | 1.75 |
| Blackman | 1.75 | −58.1 | 18 dB/oktav | 1.727 | −7.54 | 1.10 |
| Blackman-Harris (4) | 2.00 | −92.0 | 6 dB/oktav | 2.004 | −8.90 | 0.83 |
| Kaiser β = 8 | 1.63 | −58.7 | ~6 dB/oktav | 1.667 | −7.22 | 1.18 |
| Chebyshev −80 dB | 1.75 | −80.0 | 0 (düz) | 1.743 | −7.66 | 1.09 |
| Flat-top | 3.75 | −93* | — | 3.770 | −13.33 | 0.01 |

Sayılar {{ek:d}}'den; kılavuzun DSP çekirdeğiyle N = 1024 için hesaplanmış,
harris (1978) tablosuyla ±0.1 dB içindedir. Yan lob düşüş hızı literatür
değeridir. (*) Flat-top'ın yan lobu ilk dipten sonra ölçülür; üretici
tanımlarına göre −70…−95 dB arasında verilir.

:::formul id=enbw baslik="ENBW ve gürültü tabanına etkisi"
f: ENBW = frac{N · ∑ w_n^2}{( ∑ w_n )^2}      Taban_{pencere} = Taban_{dikd.} + 10 · log_{10}(ENBW)
s: w_n | pencere katsayıları (n = 0 … N−1) | —
s: N | pencere/FFT boyu | —
s: ENBW | eşdeğer gürültü bant genişliği | bin
o: Hann → ENBW = **{{s:turetilmis_beklenen.hann_enbw}} bin** → taban +1.76 dB; referans senaryoda −122.2 (dikdörtgen) yerine **−120.4 dBFS/bin**
o: Blackman-Harris → 2.004 bin → +3.02 dB; flat-top → 3.77 bin → +5.76 dB. Tespit hassasiyeti bu kadar düşer; flat-top'ı tespit yolunda kullanma.
:::

:::formul id=scalloping-pencere baslik="Pencereli scalloping ve coherent gain"
f: CG = frac{1}{N} ∑ w_n      L_{sc} = −20 · log_{10} frac{|W(0.5 bin)|}{|W(0)|}
s: CG | coherent gain: tepe genliğinin dikdörtgene göre oranı | —
s: W(f) | pencerenin frekans yanıtı (DTFT) | —
s: L_{sc} | yarım bin kaymış tonun en kötü kaybı | dB
o: Hann: CG = 0.500 (−6.02 dB, ∑w ile telafi edilir), L_sc = **1.42 dB**; dikdörtgen 3.92 dB; flat-top 0.01 dB.
o: PA ölçümü ±0.5 dB isteniyorsa ({{bolum:25}}) Hann tek başına yetmez: flat-top, zero-padding ya da tepe interpolasyonu ({{bolum:20}}) gerekir.
:::

## Kavram: yan lobun zayıf sinyali maskelemesi

Açılış sorusunun şekli aşağıda. Aynı 1024 örnek, aynı iki ton; yalnızca
pencere farklı. Dikdörtgen pencerede güçlü tonun yan lob zarfı yaklaşık
$1/(π·δ)$ ile düşer (δ bin cinsinden uzaklık): 12 bin ötede −31 dB. −70 dBFS'lik
zayıf ton o bin'de −33 dBFS'lik sızıntının altında kalır; FFT'de görünen
şey tamamen güçlü tonun sızıntısıdır ve ikinci bir emiter olduğuna dair hiçbir
iz yoktur. Blackman-Harris'te yan loblar −92 dB'ye çöker; zayıf ton −70
dBFS'te, olduğu yerde, tam genliğiyle görünür.

{{svg:g-191-yan-lob-maskeleme.svg|Yan lobun zayıf sinyali maskelemesi (hesaplanmış, N = 1024, fs = 300 MSPS). 0 dBFS ton bin 34.27'de, −70 dBFS ton 11.8 bin ötede (altın halka). Üstte dikdörtgen: zayıf tonun bin'inde −33 dBFS okunur, ama bu güçlü tonun sızıntısıdır; zayıf ton 37 dB altındadır ve yoktur. Altta Blackman-Harris: yan loblar −92 dB'nin altında, zayıf ton −69.9 dBFS'te okunur. Bedel: ana lob 2 bin, gürültü tabanı +3 dB.}}

Sayıyı genelle: dinamik aralık ihtiyacın D dB ise (en güçlü emiter ile
görmek istediğin en zayıf emiter arası), pencerenin yan lobu D'nin altında
olmalı **ve** o yan lobun altına indiği uzaklık, iki emiter arasındaki bin
farkından küçük olmalı. Dikdörtgenin yan lobu 40 dB'nin altına ancak 30 bin
(8.8 MHz) ötede iner; Hann 5 bin'de −50 dB'dedir; Blackman-Harris 2.5 bin'den
sonra hep −92 dB'nin altındadır. Bu yüzden EH almacında genel amaçlı seçim
Hann ya da Kaiser/Blackman-Harris'tir; dikdörtgen yalnızca koherent test
sinyallerinde (ADC karakterizasyonu, {{bolum:9}}) kullanılır.

:::widget id=w15 ad="Pencere laboratuvarı"
- **Referans senaryo** (Hann) preset'inde ENBW'nin 1.500 bin, en yüksek yan lobun −31.5 dB, scalloping'in 1.42 dB olduğunu Ek D ile karşılaştır. "Ton 2 görünür mü" satırı **evet** desin: 12 bin ötedeki −70 dBc ton, Hann'ın oradaki −60 dB'nin altındaki sızıntısının üstünde kalır.
- **Dikdörtgen: maskeleme** preset'ine geç: ton 2'nin bin'inde −33 dBc okunur ama bu ton 1'in sızıntısıdır (gri çizgi = tek tonlu spektrum ile üst üste); karar **hayır**. Ton 2'yi −25 dBc'ye çıkar: ancak o zaman sızıntıdan ayrılır.
- **Blackman-Harris** preset'inde yan lob −92 dB, ton 2 −70 dBc'de açıkça görünür; ENBW 2.00 bin (taban +3 dB). Ton 2 seviyesini −100 dBc'ye indir: hâlâ yan lobun üstünde ama artık −120 dBFS'lik gürültü tabanına yaklaşır.
- **Yakın iki ton (1.5 bin)** preset'inde dikdörtgen iki tepeyi ayırır (−3 dB ana lob 1.0 bin); pencereyi Hann yap: tek tümsek (ana lob 1.5 bin). Blackman-Harris'te 2.0 bin'e kadar ayrılmaz. Kaiser'de β'yı 2'den 16'ya kaydır: ana lob genişlerken yan lob çöksün — tek parametreyle takas.
- **Flat-top: genlik** preset'inde ton 1 tam yarım bin kaymış (kesir 0.5) olmasına rağmen "ton 1 kaybı" 0.01 dB; aynı ayarda Hann 1.42, dikdörtgen 3.92 dB kaybeder. Bedel: ana lob 3.75 bin, ENBW 3.77 (taban +5.8 dB).
:::

## Kavram: seçim rehberi

Pencere seçimi, "hangi soruyu soruyorum" sorusudur:

- **Yakın iki emiteri ayırmak istiyorum** (frekans çözünürlüğü): dar ana lob
  → dikdörtgen (koherentse) ya da Hamming; ama dinamik aralık 40 dB ile sınırlı.
- **Güçlü emiterin yanında zayıf emiter arıyorum** (dinamik aralık): düşük
  yan lob → Blackman-Harris, Chebyshev, Kaiser β ≥ 8; ana lob 2 bin'i göze al.
- **Genliği doğru ölçmek istiyorum** (PA, kalibrasyon): düşük scalloping →
  flat-top; frekans çözünürlüğünü unut.
- **Genel amaçlı tespit ve spektrogram**: Hann — yan lob makul (−31.5 dB ve
  hızlı düşüş), ENBW makul (+1.76 dB), scalloping makul (1.42 dB), %50
  overlap ile toplam kaybı sıfırlanır. Referans senaryonun seçimi budur.
- **Tek register, ayarlanabilir**: Kaiser — β = 0 dikdörtgen, β ≈ 5 Hamming
  benzeri, β = 8 Blackman benzeri, β ≥ 12 Blackman-Harris bölgesi. Pencere
  ROM'una farklı β tabloları yüklenir ya da PS β'ya göre tabloyu yeniden yazar.

## Kavram: overlap ve pencere kaybının telafisi

Pencere, çerçevenin uçlarını sıfıra indirir: Hann'da ilk ve son %10'luk
dilimlerin ağırlığı %10'un altındadır. Ardışık çerçeveler uç uca eklenirse
çerçeve sınırına düşen kısa bir darbe neredeyse *görünmez* olur — pencere onu
söndürmüştür. Çözüm **overlap** (örtüşme): yeni çerçeveyi N değil N/2 örnek
sonra başlatmak. %50 overlap'te Hann pencerelerinin toplamı zaman ekseninde
tam olarak sabittir ($w[n] + w[n + N/2] = 1$); hiçbir örnek "az ağırlıklı"
kalmaz. Blackman-Harris gibi daha dar pencerelerde eşdeğer düzlük için %75
overlap gerekir. Bedel hesap yükü: %50 overlap FFT hızını ikiye, %75 dörde
katlar. FPGA'da bu, çekirdeğin giriş hızının örnek hızının 2 ya da 4 katı
olması ya da paralel çekirdek demektir ({{bolum:20}}).

{{svg:g-192-overlap-rom.svg|Solda: %50 overlap'li ardışık Hann pencereleri (altın) ve toplamları (mavi) — toplam zaman ekseninde tam 1'dir, hiçbir örnek az ağırlıklı kalmaz; overlap'siz dizilişte (gri kesikli) çerçeve sınırlarında ağırlık sıfıra iner. Sağda: FPGA'da pencere çarpımı — adres sayacı N/2'de yön değiştirir, simetrik ROM yalnızca 512 katsayı tutar, tek çarpıcı I ve Q'yu zaman paylaşımlı çarpar; WIN_SEL üst adres biti olarak tabloyu seçer.}}

:::formul id=overlap baslik="Overlap ve çerçeve hızı"
f: adım = N · (1 − overlap)      f_{çerçeve} = frac{f_s}{adım}
s: adım | ardışık çerçeve başlangıçları arasındaki örnek sayısı | örnek
s: overlap | örtüşme oranı (0 … 1) | —
s: f_{çerçeve} | saniyedeki FFT çerçevesi | 1/s
o: N = {{s:fft.n}}, overlap = %{{s:fft.overlap_yuzde}} → adım 512 örnek = 1.71 µs → **586 k çerçeve/s**; FFT çekirdeği örnek hızının 2 katında (600 MSPS eşdeğeri) çalışmalı.
o: Hann + %50 overlap: en kötü durumda bile 1 µs darbenin ≥ %75'i bir çerçevenin yüksek ağırlıklı bölgesine düşer; overlap'siz Hann'da darbenin tamamı pencere ucuna gelirse 20 dB'ye varan kayıp olur.
:::

## Kavram: iki farklı "pencere" — karıştırma

Bu kılavuzda "pencere" kelimesi iki ayrı yerde geçer ve ikisi aynı matematik
nesnesi olsa da işleri farklıdır:

1. **FFT veri penceresi** (bu bölüm): FFT'ye girecek *örnekleri* çarpar. Amaç
   spektral sızıntıyı biçimlendirmek. Her çerçevede uygulanır, gerçek zamanlı
   bir çarpmadır, `WIN_SEL` register'ından seçilir.
2. **FIR tasarım penceresi** ({{bolum:16}}): ideal filtrenin sonsuz uzunluktaki
   *katsayılarını* (sinc) sonlu tap sayısına kesmek için katsayılarla çarpılır.
   Tasarım zamanında bir kez uygulanır; sonucu filtrenin geçiş bandı genişliği
   ve durdurma bandı bastırmasıdır. Çalışma anında hiçbir "pencere" yoktur,
   yalnızca katsayılar vardır.

Aynı Kaiser tablosu iki yerde de kullanılabilir; ama "FIR'ın penceresini
Hann yaptık, FFT'de de sızıntı azalır mı" sorusunun cevabı hayırdır — FIR
penceresi filtrenin yan lob davranışını (durdurma bandı) belirler, FFT'nin
sızıntısını değil. Register haritasında ikisinin adı farklı olmalı;
kurgusal örnekte `WIN_SEL` (FFT) ve `FIR_COEF_*` (katsayılar) ayrı bloklardır.

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Analog dünyada pencerenin karşılığı, spektrum analizörünün RBW filtresinin
*şeklidir*: Gauss RBW filtresi (yan lobsuz, yavaş geçişli) ile dikdörtgene
yakın FFT-RBW'nin farkı, Hann ile dikdörtgenin farkıdır. Analizör
datasheet'lerindeki "shape factor" (60 dB / 3 dB bant genişliği oranı) ile
pencere tablosundaki "ana lob / yan lob" aynı takası anlatır. Pencere, RF
tarafında yapılan hiçbir şeyin yerine geçmez: iki emiter ADC'de birbirine
karışmışsa (intermod, {{bolum:5}}) pencere ayıramaz; yalnızca FFT'nin kendi
eklediği sızıntıyı temizler.
::fpga::
Pencere çarpımı örnek başına bir kompleks × reel çarpmadır: I ve Q için iki
DSP slice ya da zaman paylaşımlı tek slice. Katsayılar bir ROM'da (BRAM ya
da dağıtık RAM) durur; **simetriden** yararlanılır: $w[n] = w[N − 1 − n]$
olduğundan yalnızca N/2 katsayı saklanır, adres sayacı yarıda geri döner.
1024 × 16 bit Hann → 512 × 16 bit = 8 kb, bir BRAM'in çeyreği. Birden çok
pencere için ROM'a birden çok tablo yüklenir ve `WIN_SEL` üst adres biti olur;
ya da PS, çalışma anında tabloyu yeniden yazar (BRAM'in ikinci portu
AXI-Lite'a bağlı). Katsayı biti: 16 bit, en yüksek yan lobu −96 dB'nin
altında tutmaya yeter (kuantizasyon gürültüsü 6.02·16 = 96 dB); Blackman-Harris
için 18 bit tercih edilir. Latency: ROM okuma 1–2 + çarpma 3–4 = ~5 saat,
FFT çekirdeğinin ~1100 saatinin yanında ihmal edilir. Pencere çarpımı
genliği düşürdüğü için (CG 0.5) FFT girişinin bit genişliğini artırmaz;
aksine bir bit headroom kazandırır ({{bolum:12}}).
::yazilim::
Yazılımcı için pencere üç sayı demektir: hangisinin seçildiği (`WIN_SEL`),
∑w (dBFS ölçekleme için; ROM tablosundan hesaplanır ya da sabit olarak
belgelenir) ve ENBW (gürültü tabanı ve eşik hesabı için). PS'ten Kaiser β
değiştiriliyorsa tablo yeniden üretilir ve **∑w ile ENBW de yeniden
hesaplanır** — bunu unutan yazılım, β'yı 6'dan 12'ye çekince tespit eşiğini
1 dB yanlış koyar ve sızıntı seviyelerini yanlış okur. Kalibrasyon
verilerinin (PA düzeltme tablosu) hangi pencereyle alındığı kayıt altında
olmalı; flat-top ile kalibre edilip Hann ile çalışan sistem sistematik
1.4 dB'ye kadar PA hatası taşır.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>
#include <math.h>

/* Kurgusal, öğretici register haritası (FFT bloğu) */
#define FFT_WIN_SEL      0x40  /* 0 dikd., 1 Hann, 2 Blackman-Harris, 3 Kaiser(PS tablosu) */
#define FFT_WIN_SUMW     0x44  /* RO: seçili tablonun katsayı toplamı, Q16 (donanım toplar) */
#define FFT_WIN_RAM      0x800 /* Kaiser için PS'in yazdığı 512 x int16 (simetrik yarı) */

/* Kaiser tablosunu üret, ROM'a yaz, ölçekleme sabitlerini döndür.
 * beta: yan lob ↔ ana lob düğmesi; N: FFT boyu; q: katsayı biti (16) */
static double bessel_i0(double x) { double s = 1, t = 1; for (int k = 1; k < 50; k++) { t *= (x / (2 * k)) * (x / (2 * k)); s += t; if (t < 1e-12 * s) break; } return s; }

static void kaiser_yukle(volatile uint32_t *fft, int N, double beta, double *sum_w, double *enbw)
{
    double i0b = bessel_i0(beta), s1 = 0, s2 = 0;
    for (int n = 0; n < N / 2; n++) {                       /* simetrik: yalnızca ilk yarı */
        double r = 2.0 * n / (N - 1) - 1.0;
        double w = bessel_i0(beta * sqrt(1.0 - r * r)) / i0b;   /* 0..1 */
        int16_t q = (int16_t)lrint(w * 32767.0);
        fft[FFT_WIN_RAM / 4 + n] = (uint16_t)q;
        s1 += 2 * w; s2 += 2 * w * w;                        /* diğer yarı aynadır */
    }
    *sum_w = s1;                                             /* dBFS: 20log10(|X| / (sum_w * tam_olcek)) */
    *enbw  = N * s2 / (s1 * s1);                             /* taban düzeltmesi: +10log10(enbw) dB */
    fft[FFT_WIN_SEL / 4] = 3;
}
/* referans: beta = 8, N = 1024 → sum_w ≈ 445.8 (CG 0.435), enbw ≈ 1.667 bin (+2.22 dB) */
```

İki dikkat: `lrint(w · 32767)` ile katsayı **asla 32768'e taşmaz** (Q1.15
sınırı; taşarsa pencerenin tepesi negatife sarar ve spektrum bozulur,
{{bolum:12}}). Ve `sum_w` donanımın gerçekten kullandığı *kuantize*
katsayılardan hesaplanmalı; yukarıdaki kayan noktalı toplam 16 bitte 0.01
dB'den az sapar, 8 bitlik katsayıda saparak seviye hatası olur — donanım
`FFT_WIN_SUMW`'yi kendi toplayıp okutuyorsa onu kullan.

:::tuzak "Blackman-Harris her zaman daha iyidir"
Yan lobu −92 dB olan pencere "en iyi" görününce her yere konur; sonra iki
emiter 500 kHz (1.7 bin) arayla gelir ve tek emiter olarak PDW'lenir —
ana lob 2 bin'dir. Aynı zamanda gürültü tabanı 3 dB yükseldiği için
hassasiyet 1.3 dB (Hann'a göre) düşmüştür. Pencere bir dinamik aralık
düğmesi değil, dinamik aralık ↔ çözünürlük ↔ hassasiyet üçgeninde bir
konumdur. Sorunun dinamik aralık olduğundan emin değilsen Hann'da kal.
:::

:::tuzak Coherent gain'i iki kez telafi etmek (ya da hiç)
Donanım çıkışı zaten ∑w'ye göre ölçeklenmişse yazılımın bir kez daha Hann için
+6 dB eklemesi, tüm PA'ları 6 dB yüksek okutur; tersi 6 dB düşük okutur. Test
basittir: bilinen −20 dBFS'lik CW ton ver, bin merkezine oturt, pencereyi
dikdörtgenden Hann'a çevir. Okunan tepe değişmiyorsa telafi doğru yerde bir
kez yapılıyordur; 6 dB oynuyorsa ya hiç ya iki kez yapılıyordur.
:::

:::tuzak FIR penceresini FFT penceresi sanmak
"DDC'nin FIR'ında Kaiser kullandık, o yüzden FFT'de sızıntı yok" cümlesi
duyulmuş bir cümledir. FIR'ın tasarım penceresi filtrenin durdurma bandını
belirler ({{bolum:16}}), FFT'ye giren örneklerle ilgisi yoktur. FFT
çerçevesi hâlâ dikdörtgen kesiliyorsa sızıntı −13 dB'dir. İki pencerenin
register'ları, dokümanları ve sahipleri ayrı olmalı.
:::

:::ozet
- Sonlu gözlem = dikdörtgen pencere ile çarpım = spektrumda sinc ile konvolüsyon; sızıntı buradan gelir. Pencere, çerçeve kenarlarını yumuşatarak sinc'in yan loblarını çökertir.
- Dört sayı: ana lob genişliği (çözünürlük), en yüksek yan lob (dinamik aralık), ENBW (gürültü tabanı, +10·log10 ENBW), scalloping (genlik doğruluğu). Coherent gain ∑w ile telafi edilir, kayıp değildir.
- Hann: −31.5 dB, 1.5 bin, ENBW 1.5 (+1.76 dB), 1.42 dB scalloping — genel amaçlı seçim. Blackman-Harris: −92 dB, 2 bin, +3 dB. Flat-top: 0.01 dB scalloping, 3.75 bin. Kaiser: β ile ayarlanır.
- Dikdörtgenin yan lobu 12 bin ötede −31 dB'dir; −70 dBFS komşu emiter görünmez. Pencere bit sayısı kadar belirleyicidir.
- %50 overlap (Hann) pencerenin söndürdüğü kenarları telafi eder; çerçeve hızı 2 katına çıkar (586 k çerçeve/s).
- FFT veri penceresi ile FIR tasarım penceresi farklı işlerdir; biri çalışma anında örnekleri, diğeri tasarım anında katsayıları çarpar.
- FPGA'da: simetrik ROM (N/2 katsayı), tek çarpıcı, WIN_SEL register'ı; yazılım ∑w ve ENBW'yi pencereyle birlikte günceller.
:::

:::kendini-sina
S: Hann pencereli FFT'de gürültü tabanı dikdörtgene göre kaç dB yükselir ve tespit hassasiyeti aynı oranda mı düşer?
C: 10·log10(1.5) = 1.76 dB yükselir. Bin merkezindeki ton için hassasiyet 1.76 dB düşer; ama rastgele frekanslı ton için dikdörtgenin ortalama scalloping kaybı (~1.5 dB'ye kadar) Hann'ınkinden (~0.7 dB) büyük olduğundan pratikte fark 1 dB civarına iner. Overlap ile de kenar kaybı telafi edilir.
S: İki emiter 1 MHz arayla (3.4 bin) geliyor; biri 0 dBFS, diğeri −55 dBFS. Hangi pencere ikisini de gösterir?
C: Dikdörtgenin yan lobu 3.4 bin'de ≈ −20 dB: zayıf emiter kaybolur. Hann 3.4 bin'de ≈ −45 dB: hâlâ sınırda/maskeli. Blackman-Harris 3.4 bin'de −92 dB: görünür; ana lobu 2 bin olduğundan 3.4 bin ayrım da yeterli. Kaiser β ≈ 10 da uygun.
S: ROM'da 1024 katsayı yerine 512 saklamak neden mümkün? Simetrik olmayan bir pencere olsaydı ne değişirdi?
C: Tüm standart pencereler $w[n] = w[N−1−n]$ simetrisine sahiptir; adres sayacı N/2'de yön değiştirir. Simetrisiz pencere yok denecek kadar nadirdir; olsaydı tam N katsayı ve bir BRAM daha gerekirdi, çarpıcı sayısı değişmezdi.
S: %50 overlap ile FFT çekirdeğinin işlem yükü nasıl değişir ve FPGA'da nasıl karşılanır?
C: Çerçeve hızı ikiye katlanır (586 k/s); çekirdek örnek hızının iki katı örnek işlemelidir. Karşılık: çekirdeği 2× saatte (600 MHz — çoğu fabric için fazla) çalıştırmak, iki çekirdek dönüşümlü kullanmak ya da SSR-2 çekirdek (örnek başına 2 giriş, Bölüm 12).
:::

:::kopru
Pencereyi ve N'i seçtin; şimdi bunları saniyede 586 000 kez, 300 MSPS akan
veri üzerinde, PS'i boğmadan çalıştırmak gerekiyor. Ve asıl soru henüz
sorulmadı: 3.41 µs'lik çerçevenin içinde 1 µs'lik bir darbe varsa, o
darbenin frekansını kaç Hz doğrulukla ölçebilirsin? Bölüm 20 FFT'yi FPGA'ya
indirir ve darbeli sinyalde frekans ölçümünün sınırlarını kurar.
:::
