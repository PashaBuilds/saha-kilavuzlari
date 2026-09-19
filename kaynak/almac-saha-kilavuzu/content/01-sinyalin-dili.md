# Bölüm 1 — Sinyalin Dili: Genlik, Frekans, Faz ve dB
::kisim I — Temeller: Sinyal, Spektrum, Gürültü
::meta onkosul= acar=2,3,4 blok= rota=

:::neden-onemli
Sahadan soru: "Eşik register'ına ne yazayım, gürültü tabanı −83 dBm'miş?" Bu
cümlede üç şey saklı: bir güç seviyesi, o seviyenin neye göre ölçüldüğü ve
register'ın hangi birimde saydığı. Üçünü ayırt edemeyen yazılımcı ya 20 dB
fazla yazar ve hiçbir darbe göremez ya da 20 dB az yazar ve yanlış alarm
patlar. Bu kılavuzdaki her sayı — gürültü tabanı, hassasiyet, SNR, SFDR,
dBFS — bu bölümde kurulan dille yazılır. Sinüsün üç parametresi, zaman ile
frekansın aynı şeyin iki görünümü olduğu fikri ve dB ailesinin hangi üyesinin
neye göre olduğu: bunlar öğrenildikten sonra bir datasheet ya da spektrum
ekranı okunabilir hale gelir.
:::

## Sezgi: bir sinüsü tarif etmek için üç sayı yeter

Radyo frekansında dolaşan her şey, ne kadar karmaşık görünürse görünsün,
sinüslerden kurulur. Bir sinüsü tam olarak tarif etmek için üç sayı gerekir:
ne kadar büyük (**genlik**, A), saniyede kaç kez tekrarlıyor (**frekans**, f)
ve zaman sıfırında salınımın neresinde (**faz**, φ). Matematiksel karşılığı
$x(t) = A·cos(2πft + φ)$; parantezin içi, radyan cinsinden anlık açıdır ve
her saniye $2πf$ radyan artar. Periyot $T = 1/f$: 1 MHz'lik bir sinüs her
mikrosaniyede bir kendini tekrarlar, 9.4 GHz'lik bir X-bant taşıyıcısı her
106 pikosaniyede bir.

Bu üç sayı bu kılavuzun üç ölçüm eksenidir. Bir darbenin **genliğini**
ölçüp PA (pulse amplitude) alanına yazacağız ({{bolum:25}}), **frekansını**
FFT ile bulacağız ({{bolum:18}}), **fazını** iki anten arasında
karşılaştırıp yön bulacağız ({{bolum:25}}). Faz özellikle sinsidir: tek bir
sinüste "faz kaç?" sorusunun anlamı yoktur, faz hep *bir referansa göre*
ölçülür — ikinci bir sinüse, bir saat kenarına ya da bir önceki örneğe göre.
Bunu {{bolum:2}}'de I/Q'nun neden iki kanal olduğunu anlarken kullanacağız.

:::analoji Ses ve tuş
Bir piyano tuşuna ne kadar sert bastığın genliktir; hangi tuşa bastığın
frekanstır; iki elinle iki tuşa *aynı anda mı yoksa biri hafif gecikmeli mi*
bastığın fazdır. Kulak, karışık bir akordu tek tek notalara ayırır — yani
kulak bir frekans analizörüdür. FFT'nin yaptığı da kulağın yaptığıdır:
zaman ekseninde iç içe geçmiş sinüsleri frekans ekseninde yan yana dizmek.
:::

## Kavram: aynı sinyalin iki görünümü

Bir osiloskop sinyali zaman ekseninde gösterir: yatay eksen saniye, düşey
eksen volt. Bir spektrum analizörü aynı sinyali frekans ekseninde gösterir:
yatay eksen hertz, düşey eksen güç. İkisi aynı sinyalin iki fotoğrafıdır;
biri diğerinden hesaplanabilir. Bu hesap **Fourier dönüşümüdür** ve fikri
şudur: herhangi bir sinyal, farklı frekanslarda, farklı genlik ve fazlarda
sinüslerin toplamı olarak yazılabilir. Frekans domaini, o toplamdaki her
sinüsün "ne kadar var" listesidir.

{{svg:g-10-zaman-frekans.svg|Aynı sinyalin iki görünümü. Üstte tek bir ton: zaman ekseninde genlik A, periyot T = 1/f ve referansa göre faz kayması φ okunur; frekans ekseninde tek bir çizgi. Altta 1 MHz ve 3 MHz'lik iki tonun toplamı: zamanda göz ayıramaz, frekansta iki temiz çizgi.}}

Tek bir sinüs, frekans ekseninde tek bir çizgidir: yeri frekansı, boyu
genliği söyler (faz da orada saklıdır ama genlik spektrumu onu göstermez).
İki ton toplandığında zaman görünümü hemen karmaşıklaşır; frekans görünümü
ise yalnızca iki çizgi olur. Almaç tasarımının büyük kısmı bu iki görünüm
arasında gidip gelmektir: darbenin genişliğini zaman ekseninde ölçersin,
bant genişliğini frekans ekseninde; filtreyi frekans ekseninde tasarlarsın,
onun darbeyi ne kadar yumuşattığını zaman ekseninde görürsün. Kılavuz
boyunca sinyal gösteren neredeyse her görselde iki panel yan yana olacak.
Fourier'nin sezgisi şimdilik bu kadar; hesabın kendisi (DFT, FFT, bin,
pencere) {{bolum:18}} ve {{bolum:19}}'un konusu.

## Kavram: güç, gerilim ve 50 Ω dünyası

RF'te seviyeler gerilimle değil **güçle** konuşulur; çünkü anten, kablo,
yükselteç ve ADC girişi arasındaki her arayüz **50 Ω** karakteristik
empedansa göre tasarlanır ve 50 Ω sabitken güç ile gerilim birbirine
kilitlidir. Bir sinüsün ortalama gücü, rms (etkin) gerilimin karesinin
dirence bölümüdür; sinüs için rms, tepe genliğin $1/√2$ katıdır, tepeden
tepeye (Vpp) değerin ise $1/(2√2)$ katı.

:::formul id=guc-gerilim baslik="Güç, Vrms ve Vpp (50 Ω)"
f: P = frac{V_{rms}^2}{R}      V_{rms} = frac{A}{√2} = frac{V_{pp}}{2√2}
s: P | ortalama güç | W
s: V_{rms} | etkin gerilim | V
s: A | tepe genlik | V
s: V_{pp} | tepeden tepeye gerilim | V
s: R | yük direnci (RF'te 50) | Ω
o: ADC tam ölçeği {{s:adc.tam_olcek_vpp}} Vpp → V_rms = 0.354 V → P = 0.354² / 50 = 2.5 mW ≈ **+{{s:adc.tam_olcek_dbm}} dBm** (aşağıda dBm'i tanımlayınca bu sayı geri gelecek)
o: Gelen darbe {{s:sinyal.seviye_dbm_giris}} dBm = 1 nW → V_rms = √(1e−9 · 50) = **224 µV** — anten girişinde darbe, bir AA pilin on binde biri kadar gerilim.
:::

Gerilim tarafı yazılımcıya uzak görünebilir ama ADC datasheet'i tam
ölçeğini volt (Vpp) olarak verir, spektrum analizörü dBm okur; ikisini
birbirine çevirmeden "ADC'yi doyurur muyum?" sorusu cevaplanamaz. 50 Ω
varsayımı kritik: aynı 1 Vpp, 75 Ω'luk bir video hattında farklı bir güçtür.

## Kavram: dB ailesi — hangisi neye göre

Almaçta seviyeler femtowatt'tan watt'a, on beş büyüklük mertebesi yayılır.
Bu aralığı çarpma ve bölmeyle yönetmek yerine **logaritmik** ölçeğe geçilir:
oranlar toplamaya, zincirdeki kazanç ve kayıplar da art arda eklenen
sayılara dönüşür. **Desibel** (dB) bir oranın on tabanında logaritmasının on
katıdır — *güç* oranı için. Gerilim oranı için yirmi katı; çünkü güç
gerilimin karesiyle gider ve karenin logaritması logaritmanın iki katıdır.

:::formul id=db baslik="dB: güç için 10·log, genlik için 20·log"
f: dB = 10 · log_{10} frac{P_2}{P_1} = 20 · log_{10} frac{V_2}{V_1}
s: P_1, P_2 | karşılaştırılan güçler (aynı birim) | W
s: V_1, V_2 | karşılaştırılan gerilimler (aynı yük üzerinde) | V
o: Ön uç kazancı {{s:on_uc.kazanc_toplam_db}} dB → güç ×10 000, gerilim ×100. Aynı 40 dB; sayı değişmez, yalnızca hangi büyüklüğün oranı olduğuna göre lineer karşılığı değişir.
o: Güç ×2 = 3.01 dB, ×10 = 10 dB, ×1000 = 30 dB; gerilim ×2 = 6.02 dB. Bu dört sayı ezberdir.
:::

dB tek başına bir *oran*dır; birim değil. Bir seviyeyi mutlak olarak
yazmak için oranın paydasına sabit bir referans konur ve referansın adı dB'nin
kuyruğuna eklenir. Ailenin üyeleri:

| Birim | Referans | Ne için kullanılır | Örnek |
|---|---|---|---|
| **dBm** | 1 mW | mutlak güç; almacın ana para birimi | gürültü tabanı {{s:turetilmis_beklenen.gurultu_tabani_dbm}} dBm |
| **dBW** | 1 W | verici gücü | +30 dBm = 0 dBW |
| **dBc** | taşıyıcı (carrier) gücü | spur, harmonik, faz gürültüsü: "taşıyıcının kaç dB altında" | NCO spur'u −84 dBc ({{bolum:14}}) |
| **dBFS** | ADC tam ölçeği (full scale) | sayısal alanda seviye; ADC ve FFT çıkışının dili | −1 dBFS: doyuma 1 dB kaldı ({{bolum:9}}) |
| **dBm/Hz** | 1 mW, 1 Hz bantta | güç spektral yoğunluğu; gürültü için | kTB = {{s:turetilmis_beklenen.ktb_dbm_hz}} dBm/Hz ({{bolum:4}}) |
| **dBi / dBd** | izotropik / dipol anten | anten kazancı | ({{bolum:5}}) |

Kural basit: **iki mutlak seviye çıkarılırsa dB (oran) çıkar; bir mutlak
seviyeye dB eklenirse yine aynı türden mutlak seviye çıkar.** −60 dBm'lik
darbeye 40 dB kazanç → −20 dBm. −20 dBm'i +4 dBm'lik tam ölçekle
karşılaştır → −24 dBFS. İki dBm birbirine *toplanmaz*; "−60 dBm + −60 dBm"
diye bir işlem yoktur (aşağıdaki tuzağa bak).

{{svg:g-11-db-merdiveni.svg|dB merdiveni: −180 dBm'den +40 dBm'e. Sol kolonlarda her 20 dB'de mutlak güç ve 50 Ω'daki rms gerilim; sağda referans senaryonun durakları: kTB −174 dBm/Hz, 2 MHz ve 300 MHz bantta gürültü tabanı, MDS, gelen darbe, LNA ve IF çıkışı, ADC tam ölçeği. Kırmızı bölge doyum, gri bölge gürültünün altı. Sağ altta ezber kartı.}}

Merdivende iki bölge işaretli. Altta gri: 300 MHz bantta gürültü tabanının
altı — oraya düşen sinyal görünmez ({{bolum:4}}). Üstte kırmızı: ADC tam
ölçeğinin üstü, **doyum** (saturation) bölgesi — oraya çıkan sinyal kırpılır
(clipping, {{bolum:9}}). Almacın
**dinamik aralığı**, kabaca bu ikisinin arasıdır; tasarımın büyük kısmı
darbeyi bu koridorda tutmaktır. Merdivenin bir başka faydası büyüklük hissi
vermesidir: −83 dBm ile −68 dBm arasındaki 15 dB, "çok az" değil, gücün
otuz iki katıdır.

### dBFS: sayısal dünyanın dBm'i

ADC'den sonra volt ve miliwatt anlamını yitirir; elde yalnızca sayılar
vardır. Sayısal alanda seviye, ADC'nin üretebileceği en büyük sinüse göre
verilir: **dBFS**. Tam ölçekli sinüs (tepe değeri $2^{N−1}$ − 1 olan) 0 dBFS'tir;
her 6.02 dB aşağısı bir bit eksiktir. Analog dünyayla köprü tek sayıdır: ADC
girişinde 0 dBFS'e karşılık gelen güç (referans senaryoda +{{s:adc.tam_olcek_dbm}} dBm).
Bu sayıyı bilmeden FFT ekranındaki −90 dBFS'lik tabanın kaç dBm olduğu
söylenemez. Dikkat: dBFS tanımı üreticiye göre "tam ölçekli sinüs" ya da
"tam ölçekli kare/DC" olabilir; ikisi arasında 3 dB fark vardır. Bu kılavuzda
hep sinüs referansı kullanılır ({{bolum:9}}'da tekrar).

{{svg:g-12-uc-cetvel.svg|Üç cetvel: aynı seviyenin anten girişinde dBm, ADC girişinde dBm (+40 dB zincir kazancı) ve sayısal alanda dBFS (0 dBFS = +4 dBm) karşılıkları. Referans darbe −60 dBm → −20 dBm → −24 dBFS; gürültü tabanı ve MDS aynı üç cetvelde. İki sabit — zincir kazancı ve ADC'nin tam ölçek dBm'i — FFT ekranını anten girişine bağlar.}}

Şekildeki iki ok, yazılımcının elindeki iki kalibrasyon sabitidir: zincir
kazancı (sıcaklıkla ve kazanç ayarıyla kayar, ölçülür) ve ADC'nin tam ölçek
gücü (datasheet'ten, sabit). Sayısal alanda gördüğün her dBFS, bu iki
sabitle anten girişindeki dBm'e çevrilir; PDW'deki PA alanı ({{bolum:24}})
bu çevrimin sonucudur.

:::widget id=w01 ad="dB dönüştürücü"
- **Referans senaryo** preset'inde −60 dBm'in 1 nW ve 224 µVrms (50 Ω) olduğunu, tam ölçeğe göre −64 dBFS'te durduğunu gör. Sonra "IF çıkışı" preset'i: aynı darbe 40 dB kazançla −20 dBm = 2.24 mVrms, −24 dBFS.
- Seviyeyi +4 dBm'e çek: Vpp tam 1.0 V olsun ve dBFS satırı 0'a gelsin; bir adım daha yukarı çıkınca "ADC doyar" uyarısı belirsin. Yük direncini 50'den 75 Ω'a değiştir: dBm aynı kalırken Vrms 224 µV'tan 274 µV'a çıksın — dBm'in yükten bağımsız, gerilimin bağımlı olduğunu gör.
- Oranı 2 yap: güç için 3.01 dB, tür kutusunu genliğe çevirince 6.02 dB. Oranı 10 000 yap: 40 dB (güç) — ön uç kazancı.
- Seviyeyi −83.2 dBm'e (gürültü tabanı) çek: 15.5 µVrms. Merdivende gri bölgenin sınırındasın; MDS için 15 dB daha yukarı çıkman gerektiğini işaretle ({{bolum:4}}).
:::

## Yazılımcıya dokunan yer

dB hesabı gömülü kodda üç biçimde karşına çıkar: PS tarafında `log10f` ile
(ucuz, float var), FPGA ya da kesme içinde tablo ile (log yok, zaman yok) ve
register'larda **sabit noktalı dB** olarak (örneğin PA alanı 0.25 dB
adımlarla, {{s:pdw.pa_lsb_db}} dB LSB — {{bolum:24}}). Üçünü de bir arada:

```c
#include <stdint.h>
#include <math.h>

/* 1) PS tarafı: güç (lineer, tam ölçek kare = 1.0) → dBFS. Kurgusal, öğretici. */
static float guc_dbfs(float p_lin)
{
    if (p_lin < 1e-30f) return -300.0f;          /* log(0) koruması */
    return 10.0f * log10f(p_lin);                /* güç → 10·log */
}

/* 2) Kesme / hızlı yol: 10·log10(x) için 64 girişli tablo + lineer ara değer.
 *    x = m · 2^e biçiminde ayrıştırılır; 10·log10(2) = 3.0103 dB / oktav. */
static const float LOG_TAB[65] = { /* 10*log10(1 + k/64), k = 0..64 */ 0.0f /* ... */ };
static float guc_db_hizli(uint32_t x)
{
    if (x == 0) return -300.0f;
    int e = 31 - __builtin_clz(x);               /* en anlamlı bit: oktav */
    uint32_t m = (e >= 6) ? (x >> (e - 6)) : (x << (6 - e));  /* 7-bit mantis, 64..127 */
    int k = (int)(m - 64);
    return 3.0103f * (float)e + LOG_TAB[k];      /* ara değer eklenebilir */
}

/* 3) Register formatı: Q8.8 işaretli dB (1/256 dB çözünürlük) ↔ float.
 *    Ölçek KURGUSAL; gerçek karttaki LSB'yi register haritasından oku. */
static int16_t db_to_q88(float db) { return (int16_t)lrintf(db * 256.0f); }
static float   q88_to_db(int16_t r) { return (float)r / 256.0f; }

/* dBFS ↔ dBm köprüsü: tek sabit, ADC girişinde 0 dBFS'in gücü. */
#define ADC_TAM_OLCEK_DBM  (4.0f)               /* referans senaryo */
static float dbfs_to_dbm(float dbfs) { return dbfs + ADC_TAM_OLCEK_DBM; }
```

Üç nokta: (1) `log10f` argümanı güç mü genlik mi, kod okunurken belli
olmalı; genlik (zarf, √(I²+Q²)) veriyorsan 20 çarpanı gerekir. (2) Tabloya
giden değer tam sayı güç ise ölçek biti (Q formatı) dB'ye sabit bir ofset
olarak eklenir: $2^{−30}$ ölçekli bir güç için −90.3 dB. (3) Register'a
yazılan dB, hemen her zaman sabit bir LSB ile tam sayıdır; float'ı
yuvarlamadan `(int)` ile kesmek (truncation) yarım LSB'lik sistematik hata bırakır.

:::tuzak "Genlik ölçtüm, 10·log aldım"
Zarf dedektöründen gelen büyüklük (√(I²+Q²)) bir *genliktir*. Yazılımcı bunu
`10*log10()` ile dB'ye çevirirse çıkan sayı gerçek dB'nin yarısıdır: 20 dB'lik
bir SNR ekranda 10 dB görünür, eşik "çok gevşek" sanılıp sıkılır ve zayıf
darbeler kaybolur. Aynı hata tersine de olur: güç zarfı (I²+Q²) 20·log ile
çevrilince her şey iki kat abartılır. Kural: **karesi alınmış büyüklük → 10,
alınmamış → 20.** Şüphede kalınca bilinen bir sinyal ver ve iki katına
çıkar: 3 dB artıyorsa güç, 6 dB artıyorsa genlik ölçüyorsun.
:::

:::tuzak "İki −60 dBm'lik sinyal −120 dBm eder"
dBm'ler toplanmaz, çıkarılmaz; güçler toplanır. Aynı bantta iki eşit güçlü,
ilişkisiz sinyal (ya da iki gürültü kaynağı) toplam güçte iki katına, yani
**+3 dB**'ye çıkar: −60 dBm + −60 dBm = −57 dBm. Aynı frekans ve fazda iki
*koherent* sinyal ise gerilimde toplanır: +6 dB. Bu ayrım {{bolum:4}}'te
gürültü kaynaklarını birleştirirken, {{bolum:9}}'da ADC'nin kuantizasyon ve
jitter gürültüsünü toplarken karşına çıkacak: önce lineer güce çevir, topla,
sonra dB'ye dön. dsp-core'daki `snrBirlestir` tam olarak bunu yapar.
:::

:::saha-notu Spektrum analizörünün "dBm"i neye göre?
Analizör ekranındaki gürültü tabanı, cihazın **çözünürlük bant genişliğine**
(RBW — resolution bandwidth) göre ölçülmüş güçtür: RBW 1 MHz'te −114 dBm okuyan taban, RBW 1 kHz'te
−144 dBm olur. Sayıyı not ederken RBW'yi de not et; iki ekranı
karşılaştırırken $10·log(RBW_2/RBW_1)$ düzeltmesini uygula. Aynı şey FFT
ekranı için de geçerlidir — orada RBW'nin adı "bin genişliği"dir ({{bolum:18}}).
:::

:::ozet
- Bir sinüs üç sayıyla tarif edilir: genlik A, frekans f (periyot 1/f), faz φ — faz her zaman bir referansa göredir.
- Zaman ve frekans domaini aynı sinyalin iki görünümüdür; Fourier fikri: her sinyal sinüslerin toplamıdır, spektrum "hangi frekanstan ne kadar var" listesidir.
- RF'te seviye güçtür ve 50 Ω sabittir: P = V_rms²/R, V_rms = V_pp/(2√2). 1 Vpp ≈ +4 dBm.
- dB bir orandır: güç için 10·log, gerilim/genlik için 20·log. ×2 güç = 3 dB, ×2 gerilim = 6 dB, ×10 güç = 10 dB.
- Kuyruk referansı söyler: dBm (1 mW), dBW (1 W), dBc (taşıyıcı), dBFS (ADC tam ölçeği), dBm/Hz (1 Hz bantta güç yoğunluğu).
- Mutlak − mutlak = oran; mutlak + oran = mutlak. dBm'ler toplanmaz, güçler toplanır (+3 dB kuralı).
- Yazılımda: neyin logaritmasını aldığını bil (güç/genlik), Q formatı ofsetini ekle, register LSB'sine yuvarla.
:::

:::kendini-sina
S: −20 dBm'lik bir sinyal 50 Ω'da kaç Vrms ve kaç Vpp'dir?
C: −20 dBm = 10 µW. V_rms = √(10e−6 · 50) = 22.4 mV; V_pp = 22.4 mV · 2√2 = 63.2 mVpp. +4 dBm'lik tam ölçeğe göre −24 dBFS.
S: Bir yükselteç gerilimi 100 katına çıkarıyor. Kazancı kaç dB? Aynı yükselteç gücü kaç katına çıkarır?
C: 20·log10(100) = 40 dB. Güç 10^(40/10) = 10 000 katına çıkar (gerilim karesi). Aynı 40 dB, iki farklı lineer oran.
S: Spektrumda taşıyıcı −10 dBm, yanındaki spur −75 dBm okunuyor. Spur kaç dBc'dir ve bu değer kazanç değişince değişir mi?
C: −75 − (−10) = −65 dBc. Zincire kazanç eklenirse her iki seviye birlikte kayar, dBc değişmez; dBc bu yüzden lineer olmayan bozulmaları ve spur'ları kazançtan bağımsız tarif etmek için kullanılır.
S: FFT ekranında bir ton −30 dBFS görünüyor; ADC'nin tam ölçeği +4 dBm. Tonun ADC girişindeki gücü kaç dBm? Ön uç kazancı 40 dB ise antende kaç dBm'di?
C: −30 + 4 = −26 dBm ADC girişinde. Antende −26 − 40 = −66 dBm. Yalnızca iki sabit (tam ölçek dBm'i ve zincir kazancı) bilinirse FFT ekranı anten girişine referanslanabilir.
:::

:::kopru
Bir sinüsün üç sayısından ikisini — genlik ve frekans — tek bir reel dalga
şeklinden okuyabilirsin; faz için ise bir referans, yani ikinci bir ölçüm
gerekir. Almaç bu ikinci ölçümü sinyalin 90° kaydırılmış kopyasıyla yapar ve
sonuçta her örnek iki sayı olur: I ve Q. Bölüm 2, bu iki sayının neden bir
"kompleks sayı" olduğunu, dönen bir vektörün neden negatif frekansı doğal
kıldığını ve I ile Q yer değiştirince spektrumun neden aynalandığını anlatır.
:::
