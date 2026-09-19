# Bölüm 14 — NCO: Sayısal Osilatör
::kisim V — Sayısal Almaç Zinciri (DDC)
::meta onkosul=2,8,12 acar=15,20,25,30 blok=nco rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "NCO register'ına ne yazacağım?" Bir yazılımcı bunu ilk kez
sorduğunda cevap tek satırdır: `ftw = f / fs * 2^32`. Ama aynı yazılımcı üç ay
sonra "spektrumda periyodik çiviler var, kaynağı bulamıyoruz" dediğinde cevap
o satırın arkasındaki mekanizmadadır: faz akümülatörü, faz kırpma, tablo
kuantizasyonu. NCO, sayısal almacın *saatidir*: LO'nun FPGA içindeki
karşılığı. Frekansını yanlış yazarsan sinyal baseband'e gelmez; işaretini
yanlış yazarsan spektrum aynalanır; tablosunu küçük tutarsan spur'lar tespit
eşiğini aşar. Bu bölüm o register'ın arkasındaki her biti açar.
:::

## Sezgi: dönen bir çark ve üzerindeki cetvel

Bir sinüs üretmenin en basit yolu, sabit hızla dönen bir çark düşünmektir.
Çarkın açısı fazdır; her saat vuruşunda sabit bir adım ilerler. Çarkın
kenarındaki noktanın yatay izdüşümü kosinüs, düşey izdüşümü sinüstür
({{bolum:2}}'de fazörün tam olarak bu olduğunu görmüştük). Adım büyükse çark
hızlı döner, frekans yüksektir; adım küçükse yavaş döner.

NCO bu çarkı sayılarla kurar. Açıyı 0°–360° yerine **0 … $2^N$ − 1** arası bir
tam sayıyla temsil eder; N tipik olarak 32 veya 48'dir. Her saatte bu sayıya
sabit bir değer, **FTW** (Frequency Tuning Word — frekans ayar sözcüğü) eklenir.
Sayı $2^N$'ye ulaşınca *taşar* ve başa döner; taşma, çarkın 360°'yi tamamlaması
demektir. Bu sayaç **faz akümülatörüdür**. Akümülatörün değerini bir sin/cos
tablosuna (LUT) adres olarak verirsin, tablo o fazın genliğini döndürür.
Hepsi bu: bir toplayıcı, bir register, bir tablo.

{{svg:g-140-faz-carki.svg|Faz çarkı ve akümülatör. Solda: çark her saat vuruşunda FTW kadar döner; $2^N$'ye ulaşınca taşıp başa sarar (bir tam periyot). Sağda: akümülatör değerinin zamanla testere dişi gibi artışı ve taşma anları; alt eksende üretilen kosinüs. FTW büyüdükçe diş sıklaşır, frekans yükselir.}}

:::analoji Kilometre sayacı
Arabanın kilometre sayacı 999 999'a gelince 000 000'a döner; kimse buna
"hata" demez, sayaç yalnızca bir turu tamamlamıştır. Faz akümülatörü de
öyle: 32 bitlik sayaç 4 294 967 295'ten sonra 0'a döner ve o an sinüs bir
periyodu bitirmiştir. Sayaca her saniye ne kadar eklediğin (FTW) "hızın",
sayacın kaç turda bir sıfırlandığı da "frekansın" olur. Taşma NCO'nun hatası
değil, çalışma ilkesidir; **saturation (doyurma) değil wrap (sarma)
istersin** — Bölüm 12'deki tek yerde.
:::

## Kavram: FTW, frekans çözünürlüğü ve gerçek frekans

Akümülatör $2^N$ adımda bir tam tur atar. Her saatte FTW adım ilerliyorsa bir
tur **$2^N$ / FTW** saat sürer; saat periyodu 1/fs olduğuna göre çıkış
frekansı fs · FTW / $2^N$ olur. Tersini çözersek FTW formülü çıkar:

:::formul id=ftw baslik="Frekans ayar sözcüğü"
f: FTW = round( frac{f_{out}}{f_s} · 2^N )
f: f_{gerçek} = frac{FTW}{2^N} · f_s      Δf = frac{f_s}{2^N}
s: FTW | akümülatöre her saatte eklenen tam sayı | —
s: f_{out} | istenen çıkış frekansı | Hz
s: f_s | NCO saat (örnekleme) frekansı | Hz
s: N | akümülatör genişliği | bit
s: Δf | frekans çözünürlüğü (en küçük ayar adımı) | Hz
o: f_out = {{s:ddc.nco_mhz}} MHz, f_s = {{s:adc.fs_msps}} MHz, N = {{s:ddc.akumulator_bit}} → FTW = 0.25 · 2^32 = **{{s:ddc.ftw_hex}}** (tam olarak 2^30)
o: Δf = 2400 MHz / 2^32 ≈ **{{s:turetilmis_beklenen.nco_cozunurluk_hz}} Hz** — 2.4 GHz'lik bir NCO'yu yarım hertz adımlarla ayarlayabilirsin.
:::

Çözünürlük insanı şaşırtacak kadar incedir: 32 bit ile yarım hertz, 48 bit ile
mikrohertz'in altı. Ama şu ayrımı hemen kur: **çözünürlük doğruluk
değildir.** Çıkış frekansının *doğruluğu* fs'i üreten saatin doğruluğu
kadardır; NCO yalnızca fs'in kesirlerini üretir. Saat 10 ppm kayarsa 600 MHz
de 6 kHz kayar, FTW'nin 32 biti bunu görmez.

Bir de yuvarlama var. İstediğin f_out, fs'in $2^N$'de biri katı değilse FTW
yuvarlanır ve gerçek frekans en fazla Δf/2 kadar sapar. Referans senaryoda
şanslıyız: 600/2400 = 1/4 tam olarak temsil edilir, hata sıfır. 601 MHz
isteseydin FTW = round(0.250416̄ · $2^32$) = 1 075 531 093; gerçek frekans
600.999 999 8 MHz — 0.2 Hz'lik hata, darbe ölçümü için tamamen önemsiz ama
"neden tam 601 değil" sorusunun cevabı bu.

## Fazdan genliğe: tablo, simetri ve CORDIC

Akümülatörün N biti fazı temsil eder; ama N = 32 bitlik bir tablo 4 milyar
girişli olurdu. Bu yüzden akümülatörün yalnızca **en anlamlı P biti** tabloya
adres olur (P tipik 10–16); geri kalan $N − P$ bit **kırpılır**. Tablonun her
girişi de sonlu, **A bitlik** bir genlik tutar (A tipik 14–18). İki kuantizasyon
var demek ki: faz kuantizasyonu (P) ve genlik kuantizasyonu (A). İkisi de spur
üretir; birazdan.

{{svg:g-141-nco-blok.svg|NCO iç blok şeması. Faz akümülatörü (N bit) her saatte FTW ekler; en anlamlı P bit LUT adresi olur, kalan bitler kırpılır (faz kırpma). LUT çeyrek dalga simetrisiyle küçültülür: üst iki bit çeyreği seçer, kalan P−2 bit tabloyu adresler; sin ve cos aynı tablodan 90° kaydırmayla okunur. Çıkış A bit. Dither, kırpılan bitlere eklenen küçük rastgele sayıdır. PS tarafından yazılan register'lar yeşil.}}

Tabloyu küçültmenin klasik yolu **çeyrek dalga simetrisidir**: sinüsün
yalnızca 0–90° arası saklanır; adresin en üst iki biti hangi çeyrekte
olduğumuzu söyler, çeyreğe göre adres ters çevrilir ve işaret değiştirilir.
Tablo dörtte bire iner. sin ve cos için ayrı tablo da gerekmez: cos(θ) =
sin(θ + 90°), yani aynı tabloya P−2 bitlik adresin çeyrek sayısını bir
artırarak ikinci kez bakarsın. FPGA'da bu, çift portlu bir BRAM'in iki
portundan aynı saatte iki okuma demektir.

Alternatif yol **CORDIC**tir: tablo yerine, yalnızca kaydırma ve toplama ile
bir vektörü istenen açıya döndüren yinelemeli algoritma. Her yineleme yaklaşık
bir bit doğruluk kazandırır; 16 bit için 16 kademe pipeline. BRAM harcamaz,
LUT/FF harcar; genliği ve fazı aynı anda üretir. Yüksek fs'te ve çok kanallı
tasarımlarda tablo, düşük kaynak bütçesinde CORDIC tercih edilir; ikisi de
yaygındır ve satın aldığın NCO IP'sinde genellikle seçenek olarak vardır.

## Spur'lar: faz kırpmanın ve tablonun bedeli

Faz kırpma bir hata sinyalidir: gerçek faz ile tabloya verilen faz arasındaki
fark. Bu fark rastgele değil, **periyodiktir** — FTW'nin alt bitleri kendi
kendine tekrar eden bir örüntü üretir. Periyodik hata, spektrumda ayrık
çizgiler demektir: **faz kırpma spur'ları**. En kötü durumda en büyük spur
yaklaşık **−6.02·P dBc** seviyesindedir. P = 12 bit için −72 dBc, P = 16
için −96 dBc. Genlik kuantizasyonu ise A bitlik ideal kuantizörün
gürültüsünü ekler; bu da spur'lara katkı yapar ama genellikle daha yayvan
kalır.

:::formul id=nco-spur baslik="NCO spur seviyeleri (kestirim)"
f: SFDR_{faz} ≈ 6.02 · P  dBc
f: SNR_{genlik} ≈ 6.02 · A + 1.76  dB
s: P | LUT adres biti (kırpma sonrası faz biti) | bit
s: A | LUT çıkış (genlik) biti | bit
o: P = 12 → en kötü faz spur'u ≈ −72 dBc. Referans senaryoda ADC'nin SFDR'ı ~75 dBc mertebesinde olduğundan NCO'nun bunun altında kalması için **P ≥ 14** (≈ −84 dBc) seçilir.
o: A = 16 → genlik kuantizasyon SNR'ı ≈ 98 dB; 14-bit ADC'nin 86 dB'sinin yanında görünmez.
:::

{{svg:g-142-faz-kirpma-spektrum.svg|Aynı 601 MHz tonu için NCO çıkış spektrumu üç ayarda (hesaplanmış). Üstte P = 8 bit, dither kapalı: faz kırpma hatası periyodik, spektrumda −48 dBc civarında düzenli çiviler. Ortada aynı P ile dither açık: çiviler gürültüye dağılır, taban hafifçe yükselir. Altta P = 14 bit: spur'lar −84 dBc'nin altına iner. Kırmızı kesikli çizgi −6.02·P kestirimi, altın nokta ölçülen en büyük spur.}}

Faz spur'larını dağıtmanın standart hilesi **dither**: kırpılan bitlere
her saatte küçük bir rastgele sayı eklemek. Hata artık periyodik değil,
gürültü gibi davranır; çizgiler kaybolur, karşılığında gürültü tabanı biraz
yükselir. Birkaç LFSR biti ile yapılır, neredeyse bedavadır ve çoğu NCO IP'si
"phase dither" seçeneği sunar. Tespit almaçlarında genellikle açıktır:
tespit eşiğini periyodik bir çivinin aşması, tabanın 1 dB yükselmesinden
çok daha kötüdür.

:::widget id=w11 ad="NCO laboratuvarı"
- **Referans senaryo** preset'inde FTW'nin 0x40000000 ve gerçek frekansın tam 600 MHz olduğunu doğrula. 600/2400 = 1/4 olduğundan FTW'nin kırpılan alt bitleri sıfırdır: spektrumda hiç faz spur'u yok ("kırpılan bitler" satırı). Hedef frekansı 601 MHz yap: FTW değişsin, hata satırında sıfırdan farklı ama Δf/2'den küçük bir sayı gör ve spur'lar belirsin.
- Akümülatör genişliğini 32'den 16'ya indir: çözünürlük 0.56 Hz'den 36.6 kHz'e çıksın, 601 MHz artık tam tutturulamasın.
- 601 MHz'de LUT adres bitini 14'ten 8'e indir ve dither'ı kapat: faz kırpma spur'ları −48 dBc civarına yükselsin; "ölçülen SFDR" satırını formülle (−6.02·P) karşılaştır.
- Aynı ayarda **dither**'ı aç: çiviler dağılsın, gürültü tabanı hafifçe yükselsin. Sonra genlik bitini 8'e indir ve tabanın nasıl yükseldiğini izle.
- Frekansı negatif yap (−600 MHz): zaman çiziminde Q'nun I'ya göre öne geçtiğini, spektrumda tonun sol yarıya taşındığını gör — Bölüm 15'teki "evrik spektrumu düzeltme" bu düğmedir.
:::

## Faz sürekliliği, ofset ve çok kanallı koherentlik

FTW'yi değiştirdiğinde akümülatör sıfırlanmaz; yalnızca adım büyüklüğü
değişir. Bu yüzden NCO **faz sürekli** frekans atlar: çıkışta sıçrama olmaz,
spektrumda geçici bir sıçrama (splatter) oluşmaz. Bu, analog PLL'in saniyeler
değil mikrosaniyeler bile süren kilitlenme süresine karşı NCO'nun en büyük
avantajıdır; taramalı bir almaçta bir sonraki banda geçmek tek register
yazmasıdır.

İkinci register **faz ofsetidir** (POW, phase offset word): akümülatör
çıkışına eklenen sabit. Çıkışın fazını, frekansına dokunmadan kaydırır.
Tek kanalda nadiren gerekir; **çok kanallı** almaçta hayatidir. Yön bulma için
iki antenin sinyalleri arasındaki faz farkını ölçeceksen ({{bolum:25}}), iki
kanalın NCO'ları aynı anda, aynı fazdan başlamalı ve aynı FTW ile ilerlemeli.
Bu "aynı anda başlatma" bir **senkron reset** hattıyla yapılır; tek FPGA
içinde kolay, birden çok çip veya karta dağılmış kanallarda SYSREF benzeri
ortak bir zaman işaretine bağlanır ({{bolum:11}}). Başlatma anında bir kanal
bir saat geç kalırsa, kanallar arasında $FTW·2π/2^N$ radyan sabit bir faz hatası
oluşur ve yön ölçümü kalıcı olarak kayar.

## Negatif frekans ve evrik spektrum

{{bolum:2}}'de kompleks üstelin iki yönde dönebildiğini görmüştük: $e^{+jθ}$
saat yönünün tersine, $e^{−jθ}$ saat yönünde. NCO'da bu, FTW'nin işaretidir:
ikinin tümleyeni bir FTW'de en üst bit 1 ise akümülatör her saatte "geri"
sayar ve sin bileşeni işaret değiştirir. Çarpımda ne olduğu Bölüm 15'in konusu;
burada bilmen gereken şu: referans senaryoda IF ikinci Nyquist bölgesinden
katlandığı için spektrum **evriktir** ({{bolum:8}}) ve bunu düzeltmenin en
ucuz yolu NCO'yu ters yönde döndürmek ya da çıkışta I ile Q'yu yer
değiştirmektir. İkisi matematiksel olarak aynı kapıya çıkar; hangisinin
seçildiği tasarımcının kararıdır ve **register haritasında bir "spectral
inversion" biti** olarak karşına çıkar. O bitin ne yaptığını bilmeyen
yazılımcı, sinyali 5 MHz yukarıda ararken 5 MHz aşağıda bulur.

:::pasaport durak="NCO çıkışı (referans)" alan=sayisal
Alan: sayısal (FPGA)
!Frekans: {{s:ddc.nco_mhz}} MHz kompleks ton, $e^{−j2π·600e6·n/fs}$
!Tip: kompleks (cos + j·sin)
fs: {{s:adc.fs_msps}} MSPS (ADC saati ile aynı)
!Bit: 2 × 16 bit (I, Q)
SFDR: ≈ −84 dBc (P = 14) · dither açık
Register: FTW = {{s:ddc.ftw_hex}}, POW = 0, INV = 1
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
NCO, analog LO'nun sayısal ikizidir; ama faz gürültüsü yoktur — yalnızca
fs'i üreten saatin faz gürültüsünü "miras alır". Bu yüzden analog
tasarımcının LO için harcadığı çaba (düşük faz gürültülü VCO, temiz PLL),
sayısal almaçta ADC örnekleme saatine kayar ({{bolum:9}} ve {{bolum:11}}).
NCO'nun kendi kusurları deterministik spur'lardır ve tablo boyutu ile
dither'la kontrol edilir. Frekans atlama anlıktır: analog sentezleyicideki
kilitlenme süresi ve geçici spektral yayılma yoktur. Tek "analog" sınırı,
fs/2'nin üstünde frekans üretememesidir.
::fpga::
Referans gerçekleme: 32 bitlik akümülatör (bir DSP slice ya da fabric
toplayıcı, tek saatte), en üst 14 bit adres, çeyrek dalga simetrili 4096 ×
16 bit sin tablosu (bir 36 kb BRAM'e sığar; iki port sin ve cos için), 3
bitlik LFSR dither. Latency: akümülatör 1 + adres/çeyrek mantığı 1 + BRAM
okuma 2 + işaret düzeltme 1 = **5 saat**. fs = 2400 MHz fabric saatini aşar;
bu yüzden NCO **SSR** modunda çalışır ({{bolum:12}}): örneğin 8 paralel örnek
/ 300 MHz saat. SSR NCO'da tek akümülatör her saatte 8·FTW ekler ve 8 faz
çıkışı (acc, acc+FTW, …, acc+7·FTW) paralel üretilir; 8 tablo okuması için
BRAM sayısı artar ya da CORDIC dizisi kullanılır. Kaynak: ~1 BRAM + ~200
LUT/FF (tek örnek), SSR-8'de ~4–8 BRAM.
::yazilim::
Yazılımcının gördüğü üç register: `NCO_FTW` (32 bit), `NCO_POW` (faz ofseti,
genellikle 16 bit), `NCO_CTRL` (inversion biti, dither açık/kapalı, senkron
reset tetikleyici). FTW hesabı aşağıda; tuzaklar: 64-bit ara sonuç, işaret,
yuvarlama ve **fs'in gerçekten ne olduğu** (ADC saati mi, decimation sonrası
saat mi? NCO ADC hızında çalışıyorsa fs = 2400 MHz'dir, DDC çıkış hızı
değil). Frekansı okurken de aynı formülü tersten uygula; register'ı
"MHz" sanıp okuma.
:::

:::matlab-fpga
::matlab::
Modelde NCO tek satırdır ve sonsuz çözünürlüklüdür:

```matlab
n   = (0:N-1).';
lo  = exp(-1j*2*pi*f_nco/fs*n);   % ideal kompleks LO
y   = x .* lo;
```

Bit-true modele geçince akümülatör, kırpma ve tablo açıkça yazılır:

```matlab
ftw  = round(f_nco/fs * 2^32);
acc  = mod(cumsum(repmat(ftw,N,1)) - ftw, 2^32);
addr = floor(acc / 2^(32-14));          % 14 bit faz
lut  = round(sin(2*pi*(0:2^14-1)/2^14) * (2^15-1));
q    = lut(addr+1); i = lut(mod(addr+2^12, 2^14)+1);
```
::fpga::
Aynı şeyin RTL iskeleti (tek örnek/saat):

```verilog
reg  [31:0] acc;
wire [13:0] addr = acc[31:18];       // faz kırpma
always @(posedge clk)
  if (sync_rst) acc <= 32'd0;
  else          acc <= acc + ftw;    // wrap: taşma istenen davranış
// çeyrek dalga LUT (BRAM), iki port:
//   port A: addr           -> sin
//   port B: addr + 14'h1000 -> cos
```

Bit-true karşılaştırma ({{bolum:13}}): MATLAB `q`/`i` dizileri ile ILA'dan
yakalanan NCO çıkışı **bit bit eşit** olmalı; ilk 5 örnek latency farkı
hizalanır.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>
#include <math.h>

/* NCO frekans ayar sözcüğü. fs_hz: NCO'nun gerçekten çalıştığı saat
 * (ADC hızı, decimation sonrası değil). Negatif f_hz = ters dönüş. */
static uint32_t nco_ftw(double f_hz, double fs_hz)
{
    double oran = f_hz / fs_hz;                 /* -0.5 .. +0.5 */
    long long ftw = llround(oran * 4294967296.0); /* 2^32, 64-bit ara sonuç */
    return (uint32_t)(ftw & 0xFFFFFFFFll);      /* ikinin tümleyeni sarma */
}

static double nco_gercek_frekans(uint32_t ftw, double fs_hz)
{
    int32_t isaretli = (int32_t)ftw;             /* üst bit = yön */
    return (double)isaretli / 4294967296.0 * fs_hz;
}

/* referans senaryo: nco_ftw(600e6, 2400e6) == 0x40000000 */
```

Üç tuzak bu on satırın içinde: (1) `f_hz / fs_hz * 4294967296.0` ifadesini
`float` ile yaparsan 24 bit mantis 32 bitlik FTW'nin alt 8 bitini çöpe atar;
`double` kullan. (2) `(uint32_t)(f/fs*4294967296.0)` yazarsan negatif
frekansta tanımsız davranış; önce imzalı 64-bit'e yuvarla, sonra maskele.
(3) `round` yerine `(int)` ile kırparsan sistematik olarak aşağı yuvarlarsın:
0.5 LSB'lik frekans hatası önemsiz görünür ama iki kanalda farklı yönde
yuvarlanırsa kanallar arası frekans farkı → zamanla büyüyen faz kayması.

:::saha-notu Register'ı okuyarak fs'i doğrula
Elinde bir kartın NCO'sunun hangi fs ile çalıştığına dair belge yoksa,
bilinen bir CW ton ver, spektrumda nereye düştüğüne bak ve FTW'yi bir bit
değiştirip tonun kaç Hz kaydığını ölç: kayma = $fs / 2^N$. Bu tek ölçüm hem fs'i
hem N'i verir; belgeye güvenmek yerine üç dakikada doğrulanır.
:::

:::tuzak "FTW'yi MHz cinsinden yazdım"
Kurgusal ama yaşanmış: bir ekip register arayüzüne "NCO_FREQ_MHZ" diye bir
sarmalayıcı yazar, sürücü içinde MHz → FTW dönüşümünü yapar. Sonra biri
sürücüyü atlayıp doğrudan register'a 600 yazar. FTW = 600 → gerçek frekans =
600 / $2^32$ · 2400 MHz = 0.33 Hz. Sinyal baseband'e gelmez, herkes RF tarafını
suçlar. Belirtiler: DDC çıkışında ADC'nin katlanmış spektrumunun kaymamış hali
(600 MHz'de ton) ve "NCO çalışmıyor" hissi. Kontrol: register'ı geri oku ve
`nco_gercek_frekans` ile MHz'e çevir; sayı mantıksızsa birim hatasıdır.
:::

:::tuzak Faz kırpma spur'u "harmonik" sanılır
Spektrumda tonun yakınında düzenli aralıklı küçük çiviler görünce ilk
refleks "ADC harmoniği" demektir. Ama harmonikler f_in'in katlarında
katlanır ({{bolum:8}}); NCO faz spur'ları ise **FTW'nin alt bitlerine**
bağlı konumlarda çıkar ve FTW'yi bir LSB değiştirdiğinde yer değiştirirler.
Teşhis: FTW'yi 1 artır. Çiviler kayarsa NCO'dur (P'yi artır ya da dither'ı aç);
kaymazsa ADC'ye bak.
:::

:::ozet
- NCO = faz akümülatörü (N bit, her saatte FTW eklenir, taşarak sarar) + faz→genlik tablosu (veya CORDIC).
- FTW = f_out / fs · $2^N$; çözünürlük $fs / 2^N$ (32 bit, 2.4 GHz → 0.56 Hz). Çözünürlük ≠ doğruluk; doğruluk saatin doğruluğudur.
- Tabloya akümülatörün yalnızca P biti girer → faz kırpma spur'ları ≈ −6.02·P dBc; genlik biti A ideal kuantizasyon gürültüsü ekler.
- Dither periyodik spur'ları gürültüye dağıtır; tespit almaçlarında genellikle açıktır.
- FTW değişimi faz süreklidir (anında, splatter'sız frekans atlama); çok kanalda senkron reset ve faz ofseti koherentliği sağlar.
- Negatif FTW ters dönüş demektir; evrik spektrumu düzeltmenin yolu NCO işareti ya da I/Q swap'tır (inversion biti).
- Yazılımda: double ile hesapla, 64-bit'e yuvarla, maskele; fs'in hangi saat olduğunu bil.
:::

:::kendini-sina
S: fs = 2400 MHz, N = 32 iken 601 MHz için FTW ve gerçek frekans hatası nedir?
C: FTW = round(601/2400 · $2^32$) = 1 075 531 093. Gerçek frekans = FTW/$2^32$ · 2400 MHz = 600.999 999 8 MHz; hata ≈ 0.2 Hz, çözünürlüğün (0.56 Hz) yarısından küçük.
S: LUT adres biti P = 10 olsaydı en kötü faz kırpma spur'u kaç dBc olurdu ve 14-bit ADC'li bir almaçta bu kabul edilebilir mi?
C: ≈ −60 dBc. 14-bit ADC'nin SFDR'ı tipik 70–80 dBc olduğundan NCO en baskın spur kaynağı olurdu; zayıf bir sinyalin yanında güçlü bir sinyal varken −60 dBc'lik spur tespit eşiğini aşabilir. P ≥ 14 ya da dither gerekir.
S: İki kanallı bir yön bulma almacında NCO'lardan biri senkron reset'i bir saat geç aldı. Ne olur?
C: Kanallar arasında $FTW·360°/2^N$ sabit bir faz farkı oluşur (600 MHz/2400 MHz için 90°). Yön ölçümü kalıcı bir ofsetle kayar; kalibrasyonla düzeltilebilir ama reset her tekrarlandığında farklı olabilir. Doğru çözüm ortak senkron reset hattıdır.
S: FTW'yi değiştirdiğinde spektrumda neden geçici bir yayılma (splatter) görülmez?
C: Akümülatör sıfırlanmaz, yalnızca adım büyüklüğü değişir; faz süreklidir. Analog PLL'de ise VCO yeni frekansa kilitlenene kadar frekans süpürülür ve geçici spektral yayılma olur.
:::

:::kopru
NCO tek başına yalnızca bir ton üretir. Marifet, o tonu ADC'den gelen reel
örneklerle çarpmaktadır: spektrum kayar, istenen bant baseband'e gelir,
istenmeyen bir kopya da beraberinde gelir. Bölüm 15 bu çarpımı adım adım,
spektrumun dört karesiyle izler.
:::
