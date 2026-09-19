# Bölüm 10 — ADC Mimarileri ve Direct RF-Sampling ADC'ler
::meta onkosul=6,7,8,9 acar=11,27,28 blok=adc rota=

:::neden-onemli
Sahadan soru: "Yeni kartta mixer yok, LO yok; ADC doğrudan X-bandı
örnekliyormuş. O zaman Bölüm 6'daki her şey çöp mü oldu?" Olmadı — yalnızca
silikonun içine taşındı. Direct RF-sampling ADC, mixer'ı ve IF zincirini
kaldırır ama karşılığında saat kalitesi, giriş bant genişliği, güç ve veri
hızı faturalarını büyütür; çip içine gömdüğü DDC de {{bolum:15}}'teki
matematiğin aynısıdır. Hangi ADC mimarisinin hangi hız–çözünürlük köşesinde
yaşadığını bilmek, datasheet'teki "12 bit, 5 GSPS" satırının neden
"14 bit, 500 MSPS"ten farklı bir hayvan olduğunu anlamaktır; ve RFSoC gibi
bir çipte ADC'nin nerede bitip FPGA'nın nerede başladığını bilmek, hangi
register'ın kimin olduğunu bilmektir.
:::

## Sezgi: dört terazi

Bir ağırlığı ölçmenin dört yolu var. **Flash**: $2^N − 1$ terazi yan yana,
her biri farklı bir referansa ayarlı; hepsi aynı anda bakar, tek adımda
cevap çıkar — çok hızlı, ama 8 bit için 255 terazi gerekir. **SAR**
(successive approximation): tek terazi, ikili arama; "yarısından büyük mü?
çeyreğinden?" diye N adımda daralır — az donanım, N saat sürer. **Pipeline**:
kaba bir terazi ilk birkaç biti bulur, kalanı (artığı) büyütüp bir
sonraki teraziye verir; her kademe farklı örnek üzerinde çalışır, boru
hattı dolunca her saatte bir sonuç çıkar ama gecikme kademe sayısı
kadardır. **Sigma-delta**: çok kaba (1 bitlik) bir terazi, ölçümü çok hızlı
tekrarlar ve hatayı geri besleyerek gürültüyü ilgilenmediğin frekanslara
iter; sonra sayısal filtreyle ortalama alır — yavaş ama çok hassas.
**Time-interleaving** mimari değil, çoğaltma hilesidir: M teraziyi sırayla
çalıştırıp hızı M katına çıkarırsın; bedelini {{bolum:9}}'da gördün.

{{svg:g-100-adc-mimari-haritasi.svg|ADC mimarileri hız–çözünürlük haritası (yaklaşık, öğretici bölgeler). Sigma-delta yüksek çözünürlük düşük hız; SAR orta; pipeline yüksek hız 12–16 bit; flash çok yüksek hız az bit; time-interleaved pipeline/SAR bölgeyi GSPS'e uzatır. Yeşil çerçeve direct RF-sampling ADC bölgesi (≈ 1–10 GSPS, 12–14 bit); altın nokta referans senaryo (2.4 GSPS, 14 bit). Genel eğilim: hız 10 kat artınca çözünürlük 2–3 bit düşer.}}

## Kavram: hangi mimari nerede yaşar

| Mimari | Tipik hız | Tipik çözünürlük | Gecikme | Güçlü yanı | Zayıf yanı | Almaçta yeri |
|---|---|---|---|---|---|---|
| Flash | GSPS+ | 4–8 bit | 1 saat | En hızlı | Alan/güç $2^N$ ile büyür, INL zor | Monobit/IFM almaçlar ({{bolum:7}}), interleaved çekirdek |
| SAR | kSPS–yüz MSPS (interleaved ile GSPS) | 8–18 bit | N saat | Az güç, kolay ölçeklenir | Tek başına yavaş | Modern GSPS ADC çekirdeklerinin çoğu |
| Pipeline | on MSPS–birkaç GSPS | 10–16 bit | 5–15 saat | Hız × çözünürlük dengesi | Kademe uyumsuzluğu → spur, güç | Klasik IF-sampling ADC'ler |
| ΣΔ (sigma-delta) | kSPS–on MSPS | 16–24 bit | uzun (filtre) | Doğrusallık, çözünürlük | Dar bant, gecikme | Ses, ölçüm; RF almaçta yalnızca dar bant IF |
| Time-interleaved | 1–100 GSPS | 6–14 bit | çekirdek + kalibrasyon | Hız | Ofset/kazanç/skew spur'ları, kalibrasyon | Bütün direct RF ADC'ler (çekirdek SAR ya da pipeline) |

Haritanın kuralı basittir: aynı teknolojide **hız 10 kat artınca çözünürlük
2–3 bit düşer**. Nedeni {{bolum:9}}'dan tanıdık: yüksek giriş frekansında
jitter tavanı bitleri yer, çekirdek sayısı arttıkça uyumsuzluk spur'ları
büyür, güç bütçesi karşılaştırıcıların gürültüsünü sınırlar. Bu yüzden
"12 bit 5 GSPS" ile "16 bit 100 MSPS" aynı ENOB'a sahip olabilir;
karşılaştırma bit ile değil NSD ve SFDR ile yapılır.

## Kavram: direct RF-sampling ADC nedir

Dört özelliğin bir arada olduğu cihaza direct RF-sampling ADC deriz:

1. **Geniş analog giriş bant genişliği** — birkaç GHz'ten 8–10 GHz'e; ADC'nin
   giriş katı (tampon + örnekle-tut) RF frekansını fs'ten bağımsız olarak
   *görebilir*. Bu satır olmadan bant geçiren örnekleme ({{bolum:8}}) mümkün
   değildir.
2. **GSPS sınıfı örnekleme** — 1 ile 10 GSPS arası, içeride time-interleaved
   SAR/pipeline çekirdekler ve çip içi interleave kalibrasyonu.
3. **Entegre DDC** — NCO, kompleks mixer ve decimation filtreleri çipin
   içinde; çıkışa tam hız reel örnek yerine düşük hız I/Q verilir. Matematik
   {{bolum:14}}–{{bolum:16}} ile birebir aynıdır; yalnızca yeri farklıdır.
4. **Yüksek hızlı seri arayüz** — JESD204B/C (ayrı çip) ya da çip içi
   AXI-Stream (RFSoC); 30–100 Gbps'lik ham veriyi FPGA'ya taşımanın tek
   pratik yolu ({{bolum:11}}).

{{svg:g-101-direct-rf-adc-blok.svg|Jenerik direct RF-sampling ADC iç yapısı. Analog (altın): giriş tamponu, örnekle-tut, M yollu time-interleaved çekirdekler. Sayısal (mavi): interleave kalibrasyonu, kanal başına DDC (NCO + kompleks mixer + filtre + decimation), bypass yolu (tam hız reel örnek), JESD204 verici ve lane'ler. Saat (gri kesikli): giriş saati, çip içi PLL/bölücü, SYSREF. Kontrol (yeşil): SPI/register — kalibrasyon, NCO FTW, decimation, JESD parametreleri.}}

Bu cihaz RF zincirinden **neyi siler**: mixer'ı, LO sentezleyicisini, IF
filtresini ve IF yükseltecini — yani {{bolum:6}}'nın frekans planındaki
image problemini ve LO faz gürültüsünü. **Neyi silmez**: limiter'ı ve
LNA'yı (gürültü şekli hâlâ ilk kademede belirlenir, {{bolum:4}}), bant
seçici filtreyi (artık "preselector" değil "Nyquist bölgesi seçici" olarak
görev yapar — {{bolum:8}}'deki AAF'nin RF'teki hali), kazanç kontrolünü ve
**saat zincirini**. Hatta saat zincirini büyütür: 1.8 GHz IF'te 100 fs ile
yaşanabilen jitter, 9.4 GHz'te 44.6 dB SNR demektir ({{bolum:9}}, F.
jitter); aynı 57 dB'yi tutmak için ≈ 19 fs gerekir ve bu, saat çipinden
kart yerleşimine kadar her şeyi zorlar.

:::formul id=direct-rf-sart baslik="Direct RF örnekleme için üç şart"
f: f_{üst} ≤ BW_{giriş}        ⌊ frac{f_{alt}}{f_s/2} ⌋ = ⌊ frac{f_{üst}}{f_s/2} ⌋        σ_j ≤ frac{10^{−SNR_{hedef}/20}}{2π · f_{üst}}
s: f_{alt}, f_{üst} | sinyal bandının gerçek RF kenarları | Hz
s: BW_{giriş} | ADC analog giriş bant genişliği (−3 dB, datasheet) | Hz
s: f_s | örnekleme frekansı | Hz
s: σ_j | toplam rms jitter (saat + aperture) | s
s: SNR_{hedef} | bantta istenen jitter-sınırlı SNR | dB
o: Referans darbe RF {{s:sinyal.rf_ghz}} GHz, bant 300 MHz (9.25–9.55 GHz), örnek f_s = 5 GSPS: ⌊9250/2500⌋ = ⌊9550/2500⌋ = 3 → **4. bölge**, alias = 2·5000 − 9400 = **600 MHz, evrik** — IF örneklemedeki katlanmış konumun aynısı, mixer'sız.
o: 57 dB için σ_j ≤ 10^(−2.85)/(2π · 9.55e9) ≈ **19 fs**; giriş BW ≥ 9.55 GHz. İkisi de "sıradan" ADC ve saat çipinin dışındadır — direct RF'in gerçek maliyeti bu iki satırdır.
:::

{{svg:g-103-superhet-vs-direct.svg|Aynı darbe için iki zincir. Üstte referans senaryo: süperhet + IF örnekleme (mixer, LO 7.6 GHz, IF 1.8 GHz, AAF, ADC 2400 MSPS, FPGA'da DDC). Altta direct RF sampling: mixer, LO, IF filtre ve IF yükselteç silinmiş (kırmızı kesikli); bant seçici filtre ve LNA kalmış; RF ADC ≈ 5 GSPS (örnek), 9.4 GHz 4. bölgeden 600 MHz'e evrik iner, DDC çip içinde. Saat jitter'ının bedeli altta 5 kat ağır: aynı 100 fs, 58.9 yerine 44.6 dB.}}

## Kavram: avantajlar ve bedeller

**Kazandıkların.** Frekans çevikliği: LO'yu kilitlemeden, tek bir NCO
register'ıyla ({{bolum:14}}) bantta istediğin yere anında gidersin —
taramalı EH almacı için büyük fark. Anlık bant: fs/2'lik bölgenin tamamı
(2.5 GHz) aynı anda "görünür", DDC kanalları ({{bolum:17}}) bunu paylaşır;
çoklu emiter ve POI ({{bolum:7}}) kazanır. Kanal eşleşmesi: yön bulma için
birden çok kanalın kazanç/faz eşleşmesi analog IF zincirinde sıcaklıkla
kayardı; sayısal tarafta sabittir, kalibrasyonu yazılımla yapılır
({{bolum:25}}). Kart alanı, parça sayısı, LO kaçağı ve image derdi azalır.

**Ödediklerin.** Jitter: yukarıda. Giriş bant genişliği: ADC'nin tampon
katı GHz'lerde kazanç düşüklüğü ve doğrusalsızlık gösterir; datasheet'teki
SFDR-vs-f_in eğrisi yüksek frekansta aşağı kıvrılır. Güç: 5–10 GSPS bir
çekirdek ailesi 3–6 W ister, soğutma kart tasarımına girer. Veri hızı:
5 GSPS × 12 bit = 60 Gbps ham; çip içi DDC bunu geri alır ama "tam bant
kaydet" seçeneği pahalanır. Hassasiyet: NF'i 30 dB olan bir ADC'nin
önüne yine 30–40 dB kazanç gerekir; kazancın tamamı RF'te olduğu için IF
kademesinin ucuz kazancı yoktur, güçlü emitere pay daralır. Bant seçici
filtre: 9.25–9.55 GHz'i geçirip komşu Nyquist bölgelerini (5. bölge
10–12.5 GHz, 3. bölge 5–7.5 GHz) 60 dB bastıran bir RF filtre, 1.8 GHz'lik
IF filtresinden daha zor ve daha kayıplıdır.

Kural: **ön uç ölmedi, yer değiştirdi.** {{bolum:7}}'deki karşılaştırma
çubuklarında direct sampling "anlık BW" ve "frekans doğruluğu"nda öne,
"hassasiyet" ve "dinamik aralık"ta geri düşer; hibrit çözüm (bir kez
karıştırıp geniş bir IF'te direct sampling — referans senaryonun kendisi)
çoğu zaman en dengeli noktadır.

## Örnek cihaz aileleri

Aşağıdaki liste yalnızca **kamuya açık ürün belgelerinden bilinen genel
düzeyde** verilmiştir; bu oturumda hiçbir sayı üreticinin güncel
datasheet'inden doğrulanmamıştır. Bu yüzden her sayı "≈" taşır ve son sütun
bunu açıkça söyler. Sipariş, teklif ya da tasarım kararı için **güncel
datasheet'e bak**; aşağıdaki değerler yalnızca "hangi lige ait" sezgisi
içindir.

{{tablo: genis}}
| Aile | Çözünürlük | Maks fs | Analog giriş BW | Arayüz | Entegre DSP | Doğrulama |
|---|---|---|---|---|---|---|
| AMD Zynq UltraScale+ RFSoC, RF-ADC Gen 1 (ZU2xDR sınıfı) | ≈ 12 bit | ≈ 4 GSPS (ikili) / ≈ 2 GSPS (dörtlü) tile | ≈ 4 GHz | çip içi AXI-Stream → PL | mixer/NCO, decimation, QMC, eşik, MTS | ≈, doğrulanmadı — bkz. DS926 / PG269 |
| AMD RFSoC RF-ADC Gen 3 (ZU4xDR sınıfı) | ≈ 14 bit | ≈ 5 GSPS | ≈ 6 GHz | çip içi AXI-Stream → PL | Gen 1 + geniş decimation seçenekleri, DSA, çok tile senkron | ≈, doğrulanmadı — bkz. DS926 / PG269 |
| TI ADC12DJxx00 serisi (ör. ADC12DJ3200 / 5200) | ≈ 12 bit | ≈ 3.2–5.2 GSPS ikili, ≈ 6.4–10.4 GSPS tekli | ≈ 8 GHz | JESD204B / 204C | DDC modları, NCO'lar | ≈, doğrulanmadı — bkz. datasheet |
| TI ADCxxRF serisi (ör. ADC32RF4x) | ≈ 14 bit | ≈ 3 GSPS ikili | ≈ 3–4 GHz | JESD204B | ikili DDC, NCO, decimation | ≈, doğrulanmadı — bkz. datasheet |
| ADI AD92xx RF ADC'ler (ör. AD9208, AD9213) | ≈ 14 bit (AD9208) / ≈ 12 bit (AD9213) | ≈ 3 GSPS ikili / ≈ 10 GSPS tekli | ≈ 6–9 GHz | JESD204B | DDC, NCO, decimation (AD9208) | ≈, doğrulanmadı — bkz. datasheet |
| ADI MxFE AD908x (ör. AD9081 / AD9082) | ≈ 12 bit ADC + ≈ 16 bit DAC | ≈ 4–6 GSPS ADC, ≈ 12 GSPS DAC | ≈ 6–8 GHz | JESD204B / 204C | çok kademeli DDC/DUC, NCO'lar, kanallaştırma | ≈, doğrulanmadı — bkz. datasheet |

İki ayrı dünya görüyorsun. **Ayrı ADC + FPGA** (TI, ADI): ADC kendi
kalibrasyonunu, DDC'sini ve JESD204 vericisini taşır; FPGA'da JESD204 alıcı
IP'si, SYSREF ve saat çipi kart üzerinde ayrı parçalardır. **Tek silikon**
(RFSoC): RF-ADC, FPGA kumaşı (PL) ve işlemci (PS) aynı çiptedir; JESD204
yoktur, örnekler AXI-Stream ile PL'ye gelir, yapılandırma PS'ten AXI-Lite
ile yapılır ve üretici bunun için bir sürücü kütüphanesi ("RF Data
Converter" sürücüsü) verir. Sayısal almaç için ikinci yol çekicidir çünkü
{{bolum:11}}'in arayüz ve senkronizasyon derdinin büyük kısmı silikon
içinde çözülmüştür; bedeli, ADC'yi FPGA'dan bağımsız seçememektir.

{{svg:g-102-rfsoc-tile.svg|RFSoC RF-ADC tile yapısı, jenerik gösterim. Bir tile içinde birden çok RF-ADC bloğu; her blokta ADC çekirdeği, eşik/QMC düzeltme, NCO'lu kompleks mixer, decimation, FIFO ve PL'ye AXI-Stream çıkışı (saat başına N örnek, 16 bit sözcük). Tile ortak kaynakları: giriş saati, çip içi PLL, SYSREF ve çok tile senkron. PS, RF Data Converter sürücüsüyle AXI-Lite üzerinden NCO, decimation, eşik ve kalibrasyonu yapılandırır. Blok sayısı ve adlar nesle göre değişir.}}

Referans senaryo bir RFSoC'a taşınsaydı: IF 1.8 GHz RF0 girişine,
fs {{s:adc.fs_msps}} MSPS, tile mixer'ı NCO = {{s:ddc.nco_mhz}} MHz,
decimation ÷{{s:ddc.decimation_toplam}} → PL'ye {{s:ddc.cikis_fs_msps}} MSPS
I/Q. Kısım V'teki DDC'nin *tamamı* tile içinde yapılabilir; PL'de yalnızca
kanallaştırma, FFT ve tespit kalır. Ya da tile "bypass" modunda tam hız reel
örnek verir ve DDC'yi sen PL'de kurarsın — öğrenmek ve spur'ları kontrol
etmek için ikinci yol, kaynak için birinci yol.

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
RF tasarımcı için direct sampling, mixer yerine **bant seçici filtre +
saat** problemidir. Filtre: geçirme bandı hedef Nyquist bölgesinin
ortasında, komşu bölgeleri (özellikle image'ın düşeceği simetrik frekansı)
en az 60 dB bastıran; X-bantta bu genellikle boşluk (cavity) ya da
dalga kılavuzu filtresidir. Saat: hedef SNR için jitter bütçesi
(9.5 GHz, 57 dB → ≈ 19 fs) yazılır, saat çipi faz gürültüsü maskesi ve
kart üstü dağıtım buna göre seçilir; ADC'nin aperture jitter'ı tek başına
bütçeyi aşıyorsa hedef SNR gerçekçi değildir ve ya IF'li hibrit mimariye
dönülür ya da bant/frekans düşürülür. Kazanç: 30–40 dB'nin tamamı RF'te;
LNA + sürücü doğrusallığı (IP3, {{bolum:5}}) ADC'nin SFDR'ını sahada
belirleyen şeydir.
::fpga::
FPGA tasarımcısı için fark, verinin geldiği kapıdadır. Ayrı ADC'de JESD204
alıcı IP'si, SYSREF yakalama ve deterministik gecikme yapılandırması
({{bolum:11}}) senin sorumluluğundadır; RFSoC'ta üreticinin IP'si
AXI-Stream verir. Her iki durumda da veri SSR'dır: 2.4 GSPS reel ya da
300 MSPS I/Q, fabric saatinin katı olarak paralel örnek sözcükleriyle
({{bolum:12}}). Çip içi DDC kullanıyorsan onun decimation filtrelerinin
geçiş bandını ve grup gecikmesini bil: TOA ölçümü ({{bolum:24}}) o gecikmeyi
kalibre etmek zorundadır ve decimation oranı değişince gecikme değişir.
Çok kanallı yön bulma için çip içi NCO'ların **senkron başlatılması**
(çok tile senkron / SYSREF) şarttır; {{bolum:14}}'teki faz ofseti problemi
burada silikon düzeyinde çözülür — doğru yapılandırılırsa.
::yazilim::
Yazılımcı için direct RF ADC, register haritası büyümüş bir ADC'dir:
NCO frekansı (kanal başına, çoğu 48 bit FTW), decimation oranı, mixer
modu (reel/kompleks, bypass), eşik dedektörleri, DSA/kazanç, kalibrasyon
komutları ve durum bitleri (PLL kilidi, kalibrasyon tamam, overrange).
RFSoC'ta bunlar üreticinin sürücü API'si üzerinden çağrılır; API'nin
arkasında yine bu bölümün FTW'si vardır ve birim tuzakları ({{bolum:14}},
"MHz mi FTW mi") aynen geçerlidir. İki ek görev: **başlatma sırası** (saat
çipi kilidi → ADC PLL kilidi → kalibrasyon → SYSREF/senkron → veri aç;
sıra bozulursa link kalkar ama veri çöp olur) ve **decimation değişince
NCO'nun fs'inin değişmediğini** hatırlamak (NCO çip içinde tam hızda
çalışır).
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>

/* Çip içi DDC'li bir RF ADC için kurgusal başlatma sırası (öğretici; gerçek API üreticiye özgü).
 * Her adım bir önceki tamamlanmadan atılmaz — "link var, veri yok" hatalarının çoğu sıradadır. */
typedef struct { int (*saat_kilit)(void); int (*adc_pll_kilit)(void);
                 int (*kalibrasyon)(void); int (*senkron)(void); void (*veri_ac)(void); } adc_ops_t;

static int adc_baslat(const adc_ops_t *ops, uint32_t (*wr)(uint32_t, uint32_t),
                      double f_nco_hz, double fs_hz, unsigned dec)
{
    if (!ops->saat_kilit())    return -1;   /* 1. saat çipi PLL1/PLL2 kilidi */
    if (!ops->adc_pll_kilit()) return -2;   /* 2. ADC iç PLL / saat algılandı */
    if (!ops->kalibrasyon())   return -3;   /* 3. interleave + ofset kalibrasyonu, "done" bekle */
    /* 4. DDC: NCO tam hız fs ile hesaplanır, decimation'dan bağımsız (Bölüm 14) */
    uint64_t ftw48 = (uint64_t)((f_nco_hz / fs_hz) * 281474976710656.0 + 0.5);   /* 2^48 */
    wr(0x0200, (uint32_t)(ftw48 & 0xFFFFFFFFu));
    wr(0x0204, (uint32_t)(ftw48 >> 32));
    wr(0x0208, dec);                          /* decimation oranı */
    if (!ops->senkron())       return -4;   /* 5. SYSREF / çok tile senkron: NCO'lar aynı anda başlar */
    ops->veri_ac();                          /* 6. veri yolu açılır */
    return 0;
}
/* referans senaryo: f_nco = 600e6, fs = 2400e6 → ftw48 = 0x4000_0000_0000 (tam olarak 2^46) */
```

Register adresleri ve 48-bit FTW **kurgusaldır**; gerçek cihazın sürücüsü
bu adımları kendi adlarıyla yapar. Kalıcı olan sıradır ve NCO hesabında
fs'in tam hız olduğu gerçeğidir.

:::tuzak "Mixer gitti, frekans planı da gitti"
Belirti: direct sampling karta geçilir, LO ve image derdi kalmadı diye
frekans planı yapılmaz; sahada bandın içinde açıklanamayan bir ton belirir.
Katlanma mixer'a değil örneklemeye aittir ({{bolum:8}}): komşu Nyquist
bölgelerinden gelen sinyaller, HD2/HD3 ve interleaving spur'ları aynen
katlanır — üstelik giriş frekansı yüksek olduğu için HD2 artık 19 GHz'de
doğar ve nereye düşeceği daha az sezgiseldir. Bant seçici filtrenin komşu
bölge bastırması ve spur haritası (W-07, fs = 5 GSPS preset'i) direct
sampling'de de zorunludur.
:::

:::tuzak "RFSoC'ta ADC ile FPGA aynı çip, o yüzden senkron sorunu yok"
Belirti: çok kanallı yön bulma kartında kanallar arası faz her açılışta
farklı. Aynı silikonda olmak, tile'ların ve çip içi NCO'ların aynı anda
başladığı anlamına gelmez; her tile'ın kendi bölücüsü ve FIFO'su vardır.
Çok tile senkron mekanizması (SYSREF ile) açıkça çalıştırılmalı, başarı
durumu okunmalı ve her yeniden yapılandırmadan sonra tekrarlanmalıdır.
Kalıcı bir kanal farkı kalibre edilir; açılıştan açılışa değişen fark
senkronun çalışmadığının işaretidir ({{bolum:11}}).
:::

:::ozet
- Dört temel ADC mimarisi hız–çözünürlük haritasının farklı köşelerinde: flash (hızlı, az bit), SAR (esnek), pipeline (hız × çözünürlük), ΣΔ (hassas, yavaş); time-interleaving hepsini GSPS'e taşır, spur bedeliyle.
- Direct RF-sampling ADC = geniş giriş BW + GSPS örnekleme + çip içi DDC + JESD204/AXI-Stream. Mixer, LO, IF filtre ve IF yükselteci siler; limiter, LNA, bant seçici filtre ve saat zincirini silmez.
- Bedel: jitter (9.5 GHz'te 57 dB için ≈ 19 fs), giriş BW, güç, veri hızı, RF filtre zorluğu; kazanç: frekans çevikliği, anlık bant, kanal eşleşmesi, parça sayısı.
- Katlanma mixer'a değil örneklemeye aittir; direct sampling'de de frekans planı ve bölge seçici filtre zorunludur.
- Cihaz aileleri iki dünyada: ayrı ADC + FPGA (JESD204; TI, ADI) ve tek silikon (RFSoC; AXI-Stream, PS sürücüsü). Tablodaki sayılar ≈ ve doğrulanmamıştır; karar için güncel datasheet.
- Çip içi DDC, Kısım V'teki DDC ile aynı matematiktir; NCO tam hızda çalışır, decimation gecikmesi TOA kalibrasyonuna girer.
- Başlatma sırası: saat kilidi → ADC PLL → kalibrasyon → NCO/decimation → senkron → veri.
:::

:::kendini-sina
S: 9.25–9.55 GHz bandını fs = 4 GSPS ile doğrudan örneklemek ister misin? Hesapla.
C: fs/2 = 2 GHz; 9250/2000 = 4.6 ve 9550/2000 = 4.78 → ikisi de 5. bölgede, sığar. Alias: 9400 mod 4000 = 1400 ≤ 2000 → 1400 MHz, bölge tek → düz. Bant 1250–1550 MHz'e iner. Ama HD2 (18.5–19.1 GHz) → 4. bölgeden 18500 mod 4000 = 2500 → 1500 MHz civarına, bandın *içine* katlanır; fs = 5 GSPS'te HD2 → 18500 mod 5000 = 3500 → 1500, sinyal 450–750'de: temiz. Plan fs'e bağlıdır.
S: Direct RF ADC'nin çip içi DDC'sini kullanmak yerine tam hız reel örneği FPGA'ya alıp DDC'yi orada kurmanın bir avantajı var mı?
C: Var: filtre yanıtını, decimation oranını ve NCO davranışını kendin belirlersin, spur'ları ve grup gecikmesini bit-true doğrularsın ({{bolum:13}}); birden çok bandı aynı ham veriden kanallaştırabilirsin. Bedeli veri hızı (5 GSPS × 12 bit = 60 Gbps) ve FPGA kaynağıdır. Çoğu tasarım kaba decimation'ı çipte, ince işlemeyi FPGA'da yapar.
S: Neden 12-bit 5 GSPS bir ADC ile 14-bit 500 MSPS bir ADC aynı ENOB'a sahip olabilir?
C: ENOB'u SINAD belirler; SINAD'ı yüksek hızda jitter, interleaving spur'ları ve karşılaştırıcı gürültüsü sınırlar. 5 GSPS cihazın etiketi 12 bit olsa da 9–10 ENOB'a iner; 500 MSPS pipeline 14 bit etiketle 11–12 ENOB verir. Karşılaştırma NSD ve SFDR ile yapılır.
S: Direct sampling almacın hassasiyeti aynı NF'li süperhetten neden genellikle biraz düşüktür?
C: Kazancın tamamı RF'tedir (IF kademesinin ucuz, doğrusal kazancı yoktur), ADC'nin NF'i ≈ 30 dB olduğundan bu kazanç zorunludur ve güçlü emitere pay daralır; jitter gürültüsü yüksek f_in'de tabana eklenir; bant seçici RF filtre daha kayıplıdır. Bunlar 1–3 dB'lik farklardır ve çeviklik/anlık bant kazancıyla takas edilir.
:::

:::kopru
ADC hangi mimaride olursa olsun çıkışında saniyede otuz-kırk gigabit veri
var ve bu veri FPGA'nın 300 MHz'lik saatine sığmak zorunda. Bölüm 11, bu
akışı taşıyan arayüzü (JESD204B/C, RFSoC'ta AXI-Stream), veriyi süren saat
ağacını ve tek hızlı akışı sekiz paralel şeride bölen SSR düzenini anlatır —
FPGA'daki DSP'nin ilk satırının yazıldığı yer.
:::
