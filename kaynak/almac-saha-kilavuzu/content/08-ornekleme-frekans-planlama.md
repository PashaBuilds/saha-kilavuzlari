# Bölüm 8 — Örnekleme ve Frekans Planlama
::kisim III — Analogdan Sayısala: ADC
::meta onkosul=2,4,6 acar=9,10,14,15 blok=adc rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "Spektrumda 600 MHz'de bir ton var ama IF'imiz 1.8 GHz; ve
üstüne üstlük LO'yu yukarı çekince ton *aşağı* kayıyor. Kart bozuk mu?" Kart
bozuk değil; ADC, {{s:adc.fs_msps}} MSPS ile 1.8 GHz'i örneklediğinde
spektrum katlanmış ve aynalanmış olarak gelir — tasarım tam da bunu ister.
Ama aynı katlanma, sinyalin yanına ADC'nin kendi harmoniklerini ve
interleaving spur'larını da taşır. fs'i ve IF'i "temiz bir bant" bırakacak
biçimde seçmek frekans planlamadır; bu bölüm, RF Örnekleme kılavuzunun
bıraktığı yerden başlayıp o planın almaçtaki halini kurar.
:::

## Sezgi: kâğıdı katlayınca ne olur

Uzun bir kâğıt şerit düşün; üzerinde frekans ekseni 0'dan sonsuza uzanıyor.
Örnekleme, bu şeridi fs/2'nin her katında **akordeon gibi katlar**. Katlanmış
şeride üstten baktığında yalnızca 0 ile fs/2 arasını görürsün; ama o dilimin
üzerinde kâğıdın *bütün* katları üst üste durur. Tek katlar (1., 3., 5. bölge)
düz iner; çift katlar (2., 4., 6.) ters çevrilmiş olarak — bir bandın alçak
kenarı yüksek kenarın yerine geçer. Sinyal 2. bölgedeyse ADC çıkışında
**evriktir**.

Bu görüntünün önemli sonucu şu: ADC çıkışına bakarak sinyalin hangi kattan
geldiğini *söyleyemezsin*. 600 MHz'de gördüğün ton 600 MHz'den de, 1800'den
de, 3000'den de gelmiş olabilir. Hangi katın "sinyal", hangilerinin
"istenmeyen" olduğuna ADC değil, ADC'nin önündeki **anti-alias filtre (AAF)**
karar verir: filtre yalnızca bir katı geçirir, gerisini örneklemeden önce
bastırır.

{{svg:g-80-nyquist-akordeon.svg|Nyquist bölgeleri akordeon görünümü. Üstte gerçek frekans ekseni altı bölgeye bölünmüş; her bölgede aynı asimetrik bant (A alçak kenar, B yüksek kenar). Altta eksen fs/2 katlarında katlanır: tek bölgeler düz, çift bölgeler aynalı iner. Sağda ADC çıkışı — hepsi 0–fs/2 üzerinde üst üste; hangisinin kalacağına AAF karar verir. Referans senaryoda IF 1800 MHz 2. bölgeden 600 MHz'e evrik iner.}}

## Kısa hatırlatma: örnekleme, Nyquist ve bölgeler

Bu kavramlar kardeş kılavuzda derinlemesine işlendi; burada yalnızca bu
bölümün üzerine kurulacağı beş cümle var. Her birinin yanındaki bağlantı
ayrıntıya gider.

- **Örnekleme** sinyali fs hızında noktalara indirger; noktaların arasını
  tek anlamlı doldurabilmek için sinyalin *bant genişliği* fs/2'den küçük
  olmalıdır — en yüksek frekansı değil ({{rf:ornekleme-surekli-dunyadan-sayilara|RF Örnekleme: örnekleme teoremi}}).
- **Aliasing**, fs/2'nin üstündeki her bileşenin 0–fs/2 aralığında bir
  "takma ad" kazanmasıdır; örneklendikten sonra geri alınamaz.
- **Nyquist bölgeleri**: n. bölge (n−1)·fs/2 ile n·fs/2 arasıdır. Her bölge
  1. bölgeye iner; **çift bölgeler aynalı** iner
  ({{rf:nyquist-bolgeleri-ve-undersampling|RF Örnekleme: Nyquist bölgeleri ve undersampling}}).
- **Bant geçiren örnekleme (undersampling)**: bant tek bir bölgenin içinde
  kalıyorsa, ADC'yi sinyalin frekansından *düşük* fs ile çalıştırıp katlanmayı
  mixer yerine kullanabilirsin. Bedeli: ADC'nin analog giriş bant genişliği
  sinyali görebilmeli ve jitter cezası sinyalin gerçek frekansından kesilir
  ({{bolum:9}}).
- **Frekans planlama**: katlanma yalnızca sinyale değil, ADC'nin kendi
  ürettiği bozulmalara da uygulanır; fs seçimi bunların nereye düşeceğini
  belirler ({{rf:frekans-planlama-ve-folding|RF Örnekleme: frekans planlama ve folding}}).

:::formul id=katlanma baslik="Nyquist bölgesi ve alias konumu"
f: n = ⌊ frac{f}{f_s/2} ⌋ + 1        r = f mod f_s
f: f_{alias} = r  (r ≤ f_s/2)  ·  f_{alias} = f_s − r  (r > f_s/2)  ·  evrik ⇔ n çift
s: f | gerçek giriş frekansı | Hz
s: f_s | örnekleme frekansı | Hz
s: n | Nyquist bölgesi numarası (1'den başlar) | —
s: f_{alias} | ADC çıkışında görünen frekans, 0 … f_s/2 | Hz
o: f = {{s:on_uc.if_ghz}} GHz, f_s = {{s:adc.fs_msps}} MHz → n = ⌊1800/1200⌋ + 1 = **{{s:adc.nyquist_bolgesi}}**, r = 1800 → f_alias = 2400 − 1800 = **{{s:adc.alias_mhz}} MHz**, n çift → **evrik**.
o: IF bandı 1650–1950 MHz (±{{s:ddc.cikis_bant_mhz}} MHz) → 750–450 MHz: alt kenar 1650 **750**'ye, üst kenar 1950 **450**'ye gider — kenarlar yer değiştirir.
:::

## Kavram: AAF, bölgeyi seçen filtredir

ADC datasheet'inde "anti-alias filtre" diye bir blok yoktur; o filtre senin
kartındadır ve **hangi Nyquist bölgesinin sinyal sayılacağını** o belirler.
Referans senaryoda AAF, 1650–1950 MHz'i geçiren bir bant geçiren filtredir:
2. bölgenin ortasında 300 MHz'lik bir pencere. Pencerenin dışında kalan her
şey — 1. bölgedeki IF yükselteç gürültüsü, 3. bölgedeki mixer ürünleri,
5. bölgeye düşen {{s:on_uc.image_ghz}} GHz image kalıntısı — örneklenmeden
önce bastırılmalıdır, çünkü örneklendikten sonra hepsi 450–750 MHz'in üstüne
biner ve hiçbir sayısal filtre onları ayıramaz.

Buradan üç tasarım kuralı çıkar. **Birincisi**, AAF'nin geçirme bandı bölge
sınırlarına yaslanmamalı: gerçek filtrenin geçiş bandı vardır, bant kenarı
1200 ya da 2400 MHz'e yakınsa geçiş bandı komşu bölgeye taşar ve komşu
bölgenin gürültüsü katlanıp bandın kenarına gelir. Bandı bölgenin ortasına
koymak (senaryoda 1800 = 1.5 · fs/2) geçiş bandına iki yandan 450'şer MHz yer
bırakır. **İkincisi**, AAF'nin durdurma bandı bastırması, o bölgeden
katlanacak en güçlü istenmeyenin seviyesine göre seçilir: image 5.8 GHz'de
preselector'dan sonra hâlâ −40 dBc kalıyorsa ve sen onu tespit eşiğinin
20 dB altında istiyorsan AAF'nin 5.8 GHz'de en az 60 dB bastırması gerekir.
**Üçüncüsü**, AAF ADC'nin analog giriş bandını değiştirmez: ADC'nin kendi
giriş katı 1.95 GHz'i göremiyorsa hiçbir filtre bunu düzeltmez; datasheet'te
"analog input bandwidth" satırı bu yüzden fs'ten ayrı bir satırdır.

{{svg:g-82-aaf-bolge-secimi.svg|AAF'nin bölge seçimindeki rolü, iki plan. Üstte iyi plan: 300 MHz'lik bant 2. bölgenin ortasında (1650–1950 MHz); AAF'nin geçiş bantları bölge sınırlarına 450 MHz uzakta, komşu bölgeler 40 dB'den fazla bastırılmış, ADC çıkışında bant temiz. Altta kötü plan: bant 2100–2400 MHz, bölge sınırına yaslanmış; AAF'nin geçiş bandı 3. bölgeye taşar ve 3. bölgenin gürültüsü katlanıp bandın üst kenarına biner — sayısal filtre bunu geri alamaz.}}

:::analoji Radyo kadranı ve aynı istasyonun kopyaları
Eski bir radyo kadranında aynı istasyonu birkaç yerde yakalayabilirsin;
almaç, LO'nun harmoniklerinde de karışım yapar. Kadranda hangisinin
"gerçek" olduğunu radyo bilmez; ön uçtaki bant filtresi yalnızca birini
geçirdiği için gerçek olan odur. AAF de aynı işi yapar: ADC için 1800 MHz
ile 600 MHz aynı istasyondur; hangisinin var sayılacağına ADC'nin önünde
karar verilir.
:::

## Kavram: bozulmalar da katlanır — HD2, HD3 ve interleaving

Şimdi bu kılavuzun asıl eklediği katman. ADC'nin giriş katı doğrusal
değildir; sinyalin 2 ve 3 katında **harmonik bozulma** üretir (HD2, HD3;
tanım ve seviyeleri {{bolum:9}}). Harmonikler sinyalin *gerçek* frekansının
katlarında doğar, sonra fs etrafında katlanır. Aynı şey ADC'nin içindeki
**time-interleaving** çekirdeklerinin uyumsuzluğundan doğan spur'lar için de
geçerlidir: M çekirdekli bir ADC'de ofset uyumsuzluğu k·fs/M'de, kazanç ve
zamanlama uyumsuzluğu k·fs/M ± f_in'de tonlar üretir (mekanizma
{{bolum:9}}'da, {{rf:interleaved-adc-hiz-hilesi-ve-bedeli|RF Örnekleme'de de}}). Bunların hepsi ADC'nin
*içinde* doğduğu için AAF onları göremez; tek savunma, katlanıp nereye
düştüklerini önceden hesaplayıp sinyal bandını oradan uzak tutmaktır.

:::formul id=spur-katlanma baslik="Harmonik ve interleaving spur'larının katlandığı yer"
f: f_{HDk} = katla( k · f_{in} )        k = 2, 3, …
f: f_{ofset} = katla( m · f_s / M )        f_{image} = katla( m · f_s / M ± f_{in} )        m = 1 … M−1
s: k | harmonik derecesi | —
s: f_{in} | sinyalin gerçek (ADC girişindeki) frekansı | Hz
s: M | time-interleaved çekirdek sayısı | —
s: m | interleaving spur indisi | —
s: katla(·) | F. katlanma kartındaki alias işlemi | Hz → Hz
o: IF {{s:on_uc.if_ghz}} GHz: HD2 = 3600 MHz → katla → **1200 MHz** (bölge sınırı); HD3 = 5400 MHz → 5. bölge → **600 MHz** — sinyalin tam üstü.
o: M = 2: ofset spur'u katla(1200) = **1200 MHz**; image katla(1200 − 1800) = **600 MHz** — yine sinyalin üstü. M = 4: ofset spur'u katla(600) = **600 MHz**.
o: Bantlar da katlanır: HD2 bandı 3300–3900 → 900–1200 (bandın dışında); HD3 bandı 4950–5850 → 150–1050, üç kat genişleyip 450–750'nin üstüne biner.
:::

{{svg:g-81-katlanma-haritasi.svg|Referans senaryonun katlanma haritası. Üstte gerçek frekans ekseni: IF bandı (mavi) 2. bölgede, HD2 bandı 3300–3900 MHz 3.–4. bölgeye yayılmış, HD3 bandı 4950–5850 MHz 5. bölgede, mixer image'ı 5.8 GHz; altın kesikli eğri AAF'nin bant geçiren yanıtı. Oklar 1. bölgeye katlanmayı gösterir. Altta ADC çıkışı: sinyal 450–750 MHz evrik, HD2 900–1200 MHz'e (bandın dışına), HD3 150–1050 MHz'e (bandın üstüne) iner; image AAF ile bastırılmazsa 1000 MHz'de belirir.}}

Haritada iki şey dikkat çekmeli. Birincisi, **HD2 bandın dışına düşüyor**:
900–1200 MHz, bizim 450–750'mizle kesişmez; sayısal filtre ({{bolum:16}})
onu atar. İkincisi, **HD3 bandın üstüne düşüyor** ve bunu hiçbir fs seçimi
tamamen çözemez, çünkü 300 MHz'lik bir bandın üçüncü harmoniği 900 MHz
genişliğindedir; fs/2 = 1200 MHz'lik bir bölgeye sığmadan katlanır. Geniş
bantlı almaçta HD3 ile yaşamayı öğrenirsin: seviyesini ADC seçimiyle
(datasheet HD3, tipik −70 … −80 dBc) ve giriş seviyesini düşük tutarak
(HD3 gücü sinyal gücünün küpüyle gider; girişi 6 dB kıs, HD3 18 dB düşer,
dBc olarak 12 dB kazan) kontrol edersin.

## Kavram: "temiz bant" nasıl seçilir

Frekans planlama, bir tablo doldurmaktır: her bozulma kaynağı için (HD2,
HD3, gerekirse HD4–HD5; her interleaving indisi için ofset ve image)
katlanmış aralığı yaz, sinyalin katlanmış aralığıyla kesişip kesişmediğine
bak. Kesişmiyorsa bant "temizdir"; kesişiyorsa üç kolun var: **fs'i
değiştir** (spur'lar fs'e bağlı yerlere düşer, sinyal de kayar), **IF'i
değiştir** (LO'yu kaydırmak IF'i ve harmoniklerini birlikte kaydırır),
**bandı daralt** (dar bant, dar harmonik). Gerçek projede bu tabloyu
üreticinin frekans planlama aracı çıkarır; ama aracın "temiz" dediği plan,
senin AAF'nin gerçekten bastırdığını varsayar. Aracı besleyen mantık
aşağıdaki widget'ta.

Referans senaryonun planı dürüstçe değerlendirildiğinde **kusursuz
değildir**: 600 MHz = fs/4 seçimi NCO için mükemmeldir (FTW tam olarak
2^30, {{bolum:14}}), ama HD3 ve 2 yollu interleaving image'ı tam fs/4'e
katlanır. Bu senaryoda bilinçli bir öğretme tercihidir: iki spur'un da
bant merkezine düştüğünü görmek, "spektrumdaki bu çizgi nereden geldi"
sorusunu sorma refleksini kazandırır. Tuzak kutusunda aynı konuya
döneceğiz.

:::widget id=w07 ad="Katlanma ve spur haritası"
- **Referans senaryo** preset'inde alt panelde sinyalin 450–750 MHz'e evrik indiğini, HD2'nin 900–1200'e (bandın dışına), HD3'ün 150–1050'ye (bandın üstüne) katlandığını gör; "temiz bant" satırı HD3 ve M = 2 image'ını (600 MHz) kirletici olarak saysın.
- f_in'i 1800'den 1700 MHz'e kaydır (M = 4): alias 700'e, katlanmış bant 550–850'ye gitsin; şimdi HD2 bandı (700–1200) da bandın içine giriyor — IF'i kaydırmak bir spur'u kaçırırken başkasını getirir. Bandı 300'den 20 MHz'e daralt: bant 690–710, HD3 5100 → 300 MHz, M = 4 ofset spur'u 600 MHz bandın dışında; "temiz bant" satırı yeşile dönsün.
- **Bölge sınırında bant** preset'i: merkez 1250 MHz, bant 1100–1400 → bant fs/2 = 1200'ü aşıyor; alt panelde bandın kendi üstüne katlanıp 1000–1200 aralığına sıkıştığını gör. "bant tek bölgede mi" satırı kırmızı.
- fs'i 2400'den 3000 MHz'e çıkar (f_in 1800, bant 300): bölge 2 kalır, alias 1200 MHz, evrik; HD3 merkezi 5400 → 600 MHz'e gider ve HD3 bandı (150–1050) sinyal bandının (1050–1350) yalnızca kenarına değer. fs seçiminin spur'ları nasıl "taşıdığını" gör.
- **Direct RF 9.4 GHz, 5 GSPS** preset'i: 9.4 GHz 4. bölgeden yine 600 MHz'e evrik iner — direct sampling'in {{bolum:10}}'daki hikâyesi burada başlar.
:::

## Referans senaryo: 1.8 GHz → 600 MHz, evrik — ve düzeltilmesi

Zinciri sayılarla kapatalım. Anten girişinde {{s:sinyal.rf_ghz}} GHz'lik
darbe, {{s:on_uc.lo_ghz}} GHz low-side LO ile {{s:on_uc.if_ghz}} GHz IF'e
iner ({{bolum:6}}). IF filtresi ve AAF 1650–1950 MHz'i bırakır. ADC
{{s:adc.fs_msps}} MSPS ile örnekler: 2. bölge, alias {{s:adc.alias_mhz}} MHz,
**spektrum evrik**. Evriklik şu demektir: darbenin içinde frekans zamanla
*yukarı* süpürülüyorsa (varyant B'nin LFM'i, {{bolum:3}}), ADC çıkışında
*aşağı* süpürülür; RF'te 9.405 GHz'de duran bir emiter (IF 1805 MHz), ADC
çıkışında 605 MHz'de değil, 2400 − 1805 = 595 MHz'de görünür: RF'te +5 MHz,
baseband'de −5 MHz. Bir kez daha evrilirse
düzelir — ve LO low-side olduğu için mixer zaten *evirmemişti*; toplam
evrilme sayısı tektir, düzeltmek gerekir.

Düzeltmenin iki ucuz yolu var ve ikisi de {{bolum:14}}'ün NCO'sunda
yaşar: **NCO'yu ters yönde döndürmek** ($e^{+jωn}$ yerine $e^{−jωn}$, yani
FTW'nin işaretini değiştirmek) ya da mixer çıkışında **I ile Q'yu yer
değiştirmek**. İkisi matematiksel olarak aynı kapıya çıkar: kompleks
baseband spektrumu sıfır etrafında aynalanır. Yazılımcıya bu, register
haritasında tek bir bit olarak görünür ("spectral inversion", "NCO_INV",
"IQ_SWAP" gibi adlarla). Bit yanlışsa her şey çalışır gibi görünür —
darbe tespit edilir, PW doğru ölçülür — yalnızca frekans ölçümünün işareti
ve chirp yönü terstir. Kurgusal register örneği {{bolum:30}}'da.

:::pasaport durak="ADC girişi (AAF çıkışı)" alan=analog
Alan: analog IF
!Frekans: {{s:on_uc.if_ghz}} GHz merkez, 1650–1950 MHz (AAF penceresi) — 2. Nyquist bölgesi
Tip: reel, bant geçiren
!Bant genişliği: 300 MHz (AAF), darbe kendisi ≈ 2 MHz
!Seviye: {{s:sinyal.seviye_dbm_giris}} dBm + {{s:on_uc.kazanc_toplam_db}} dB = −20 dBm tepe (tam ölçek {{s:adc.tam_olcek_dbm}} dBm → 24 dB pay)
!Gürültü: {{s:turetilmis_beklenen.gurultu_tabani_dbm}} dBm + 40 dB = −43.2 dBm (300 MHz'te)
SNR: −20 − (−43.2) ≈ 23 dB (300 MHz bantta; dar banda inince artacak)
Katlanacağı yer: {{s:adc.alias_mhz}} MHz, evrik
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Frekans planı RF tasarımcının tablosudur ama girdilerini üç yerden alır:
mixer'ın ürün tablosu ({{bolum:6}}), ADC datasheet'inin HD2/HD3 ve
interleaving spur satırları ({{bolum:9}}) ve AAF'nin ölçülmüş durdurma bandı.
AAF, ADC'den *önce* ve ADC girişine yakın konur; sürücü yükselteç ile ADC
arasındaki filtre ADC'nin örnekleme anındaki "kick-back" gürültüsünü de
yutar. Bant kenarlarını bölge sınırlarından uzak tut, image ve LO
kaçaklarının katlanacağı yerleri işaretle, ölçüm planına "boş bantta spur
taraması" maddesi ekle.
::fpga::
FPGA'ya katlanmış örnekler gelir; katlanmayı geri alacak bir blok yoktur ve
gerekmez. FPGA'nın yaptığı iki şey: (1) NCO ile katlanmış merkezi (600 MHz)
sıfıra taşımak, (2) evrikliği NCO işareti ya da I/Q swap ile düzeltmek.
İkincisi tek bir `assign`'dır: `assign {i_out, q_out} = inv ? {q_mix, i_mix}
: {i_mix, q_mix};` — ama bu bit'in NCO işaretiyle *birlikte* değil, ikisinden
yalnızca birinin kullanıldığından emin ol; ikisi birden evrilirse
düzeltilmemiş olur. Spur haritası FPGA'ya da yol gösterir: HD2'nin 900–1200
MHz'e düştüğünü bildiğin için DDC'nin ilk filtresinin durdurma bandını
oraya göre boyutlandırırsın ({{bolum:16}}).
::yazilim::
Yazılımcının gördüğü: `SPEC_INV` bit'i, NCO frekans register'ı ve PDW'deki
frekans alanının yorumu. Frekans okurken zincir şudur: PDW'deki baseband
frekans f_bb → katlanmış konum 600 + s·f_bb → IF 1800 − s'·(…) → RF. Her
adımdaki işaret (s, s') o adımın evrik olup olmadığıyla belirlenir; low-side
mixer düz, 2. bölge evrik. Sürücüde bu hesabı tek bir fonksiyona koy ve
işaretleri sabit tablodan oku; "elle" çevrilen frekanslar bir gün ters
işaretle çevrilir.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>

/* Katlanma: gerçek frekans -> (bölge, alias, evrik). Birim: Hz.
 * Referans senaryo: katla(1800e6, 2400e6) -> bolge 2, alias 600e6, evrik 1 */
typedef struct { int bolge; double alias_hz; int evrik; } katla_t;

static katla_t katla(double f_hz, double fs_hz)
{
    katla_t k;
    double nyq = fs_hz / 2.0;
    k.bolge = (int)(f_hz / nyq) + 1;
    double r = f_hz - fs_hz * (double)(long long)(f_hz / fs_hz);   /* f mod fs */
    k.alias_hz = (r > nyq) ? (fs_hz - r) : r;
    k.evrik = (k.bolge % 2 == 0);
    return k;
}

/* Baseband ölçümünden RF'e: her evrilme işareti çevirir.
 * f_bb: DDC çıkışında ölçülen frekans (Hz, işaretli); nco: 600e6; if: 1.8e9; lo: 7.6e9 low-side */
static double bb_to_rf(double f_bb_hz, int inv_bit_acik)
{
    double s_adc = inv_bit_acik ? +1.0 : -1.0;   /* evriklik FPGA'da düzeltildiyse +1 */
    double f_kat = 600e6 + s_adc * f_bb_hz;      /* katlanmış konum, 1. bölge */
    double f_if  = 2400e6 - f_kat;               /* 2. bölge: evrik geri al */
    return 7.6e9 + f_if;                         /* low-side LO: RF = LO + IF */
}
```

İki tuzak: `fmod` yerine `(int)` ile bölge hesabı negatif frekansta patlar
(yalnızca pozitif gerçek frekans ver); ve `bb_to_rf` içindeki işaretler
kartın gerçek yapılandırmasından (LO tarafı, bölge, INV bit'i) okunmalı,
sabitlenmemeli — farklı bir LO planıyla üretilen ikinci kart aynı sürücüyle
frekansları aynalı raporlar.

:::tuzak "fs/4 her zaman en iyi yerdir"
fs/4, NCO tasarımcısının en sevdiği frekanstır: FTW tam olarak 2^(N−2)'dir,
mixer çarpımı ±1 ve 0 katsayılarına iner, spur yoktur. Ama fs/4 aynı zamanda
**M = 4 interleaved ADC'nin birinci ofset spur'u**, **HD3'ün katlandığı
yer** (3 · 3fs/4 = 9fs/4 → fs/4) ve **M = 2 image'ının** (fs/2 − fs/4) adresidir.
Referans senaryo bunu bilerek yapıyor; sahada ise IF'i fs/4'ten birkaç MHz
kaydırmak (NCO'nun yarım hertzlik çözünürlüğü bunu zaten karşılar,
{{bolum:14}}) spur'ları bandın *ortasından* alıp kenara ya da dışına
taşır. Belirti: sinyal olmadığında bile tam bant merkezinde duran, kazanç
ayarıyla seviyesi değişmeyen bir çizgi (ofset spur'u) ya da sinyalle birlikte
hareket eden ama ters yönde giden bir kopya (image).
:::

:::tuzak "Sinyal ters çıkıyor, LO tarafı yanlış olmalı"
Belirti: chirp yönü ters, frekans ölçümleri gerçeğin aynası. İlk şüphe
genellikle mixer'ın high/low-side ayarına gider; oysa evrilme sayısı
zincirin toplamıdır: mixer (low-side: 0, high-side: 1) + Nyquist bölgesi
(çift: 1) + FPGA'daki INV bit'i. Toplam tekse spektrum terstir. Teşhis için
bilinen bir CW ton ver ve frekansını 1 MHz *yukarı* al: baseband'de ton
yukarı gidiyorsa toplam çift, aşağı gidiyorsa tektir. Üç dakikalık bu test,
üç günlük "LO'yu değiştirelim" tartışmasını bitirir.
:::

:::ozet
- Örnekleme frekans eksenini fs/2 katlarında akordeon gibi katlar; tek bölgeler düz, çift bölgeler aynalı iner. Derin anlatım RF Örnekleme kılavuzunda.
- ADC çıkışından kaynağın hangi bölge olduğu anlaşılmaz; **AAF**, sinyal sayılacak bölgeyi seçen filtredir ve bant kenarları bölge sınırlarından uzak durmalıdır.
- Referans senaryo: IF {{s:on_uc.if_ghz}} GHz, fs {{s:adc.fs_msps}} MSPS → 2. bölge, alias {{s:adc.alias_mhz}} MHz, **evrik**; 1650–1950 bandı 750–450'ye kenarları yer değiştirerek iner.
- Bozulmalar da katlanır: HD2 → 1200 MHz (bant dışı), HD3 → 600 MHz (bandın üstü, 3× geniş); interleaving spur'ları k·fs/M ve k·fs/M ± f_in'de.
- "Temiz bant": her spur'un katlanmış aralığını sinyal bandıyla kesiştir; kirliyse fs'i, IF'i ya da bandı değiştir. fs/4 NCO için ideal ama spur'lar için en kalabalık adrestir.
- Evrilme, NCO işareti ya da I/Q swap ile tek bit'le düzeltilir; toplam evrilme sayısı (mixer + bölge + INV) tekse spektrum terstir.
- Yazılımda frekans çevirisi tek fonksiyonda, işaretler yapılandırmadan okunarak yapılır.
:::

:::kendini-sina
S: fs = 2400 MSPS iken 2.9 GHz'lik bir ton ADC çıkışında nerede ve hangi yönde görünür?
C: 2900 / 1200 = 2.42 → 3. bölge; r = 2900 mod 2400 = 500 ≤ 1200 → alias 500 MHz. Bölge tek olduğu için spektrum düz (evrik değil).
S: IF bandı 1650–1950 MHz iken HD2 bandı neden 900–1200 MHz'e "sıkışır"?
C: HD2 bandı 3300–3900 MHz'dir ve tam ortasından bölge sınırı 3600 (= 3·fs/2) geçer. 3300–3600 kısmı 3. bölgeden düz olarak 900–1200'e, 3600–3900 kısmı 4. bölgeden aynalı olarak yine 1200–900'e iner; iki yarı üst üste biner ve 600 MHz'lik bant 300 MHz'e katlanır.
S: Bir kartta mixer high-side, IF 2. bölgede ve FPGA'da INV bit'i açık. Spektrum düz mü, evrik mi?
C: Evrilme sayısı: high-side 1 + çift bölge 1 + INV 1 = 3, tek → spektrum evrik. INV bit'i kapatılmalı (ya da NCO işareti çevrilmeli); ikisini birden değil.
S: 300 MHz'lik sinyal bandını 3. harmoniğinden tamamen kurtaracak bir fs var mı?
C: Yok. HD3 bandı 900 MHz genişliğindedir; fs/2 < 900 MHz ise katlandığında 1. bölgenin tamamını kaplar, fs/2 > 900 olsa bile 300 MHz'lik bir boşluk bulmak fs'i çok yükseltir. Pratik çözüm HD3'ü fs ile değil, ADC seçimi ve giriş seviyesiyle (dBc) kontrol etmektir.
:::

:::kopru
Sinyalin nereye katlandığını biliyoruz; şimdi oraya *ne kadar temiz*
geldiğini soralım. 14 bit yazan bir ADC neden 9–10 bit gibi davranır,
gürültü tabanı nereden gelir, 100 fs'lik bir saat titremesi 1.8 GHz'te kaç
dB götürür? Bölüm 9, ADC datasheet'inin ilk sayfasını satır satır okunur
hale getirir.
:::
