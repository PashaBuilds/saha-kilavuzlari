# Bölüm 13 — MATLAB'dan FPGA'ya: Algoritmanın Yolculuğu
::meta onkosul=3,9,12 acar=14,15,16,18,23,30 blok=arayuz,ps rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "MATLAB'da 0.3 dB kayıp veriyordu, kartta 4 dB; kim haklı?"
İkisi de. Modeli yazan mühendis kayan noktalı, sonsuz hassasiyetli bir dünyada
çalıştı; RTL'i yazan mühendis 16 bitlik yollarda, kesme noktalarıyla; PS'te
register'a katsayı yazan sen ise ikisinin arasında, elinde bir tabloyla.
Algoritma üç kez yazılır: bir kez doğru olsun diye, bir kez sığsın diye, bir kez
çalışsın diye. Üç yazımın **aynı sayıyı** ürettiğini kanıtlamanın yolu bit-true
referans ve donanımdan yakalanan veriyle kapanan bir doğrulama döngüsüdür. Bu
döngüyü bilmeyen yazılımcı, "kartta farklı" cümlesini duyduğunda nereden
başlayacağını bilmez; bilen yazılımcı bir snapshot alır ve bir saat içinde
farkın hangi kesme noktasında doğduğunu gösterir.
:::

## Sezgi: aynı hikâye, üç dil

Bir algoritma önce **matematik** olarak vardır: "sinyali NCO ile çarp, 150 MHz'e
kadar geçir, 8'e böl." Sonra bu cümle bir **modele** dönüşür: MATLAB ya da
Python'da birkaç satır, `double` ile. Model doğruysa hikâye doğrudur; ama henüz
hiçbir şey sığmamıştır. Üçüncü adımda hikâye **sabit noktaya çevrilir**: her
sinyal için bit genişliği, her kesme noktası için yuvarlama kuralı
({{bolum:12}}). Bu çeviri kaybı vardır ve kayıp **ölçülmelidir**: kayan noktalı
sonuçla sabit noktalı sonuç arasındaki fark, kabul sınırının altında mı? Son
adımda sabit noktalı model, **donanımın ürettiği bitlerin aynısını** üreten
bir referansa dönüşür — **bit-true model**. Bundan sonra RTL'in tek görevi bu
modelle bit bit eşleşmektir; "yaklaşık" yoktur.

:::analoji Mimar, müteahhit, kiracı
Mimar (algoritma mühendisi) çizimi yapar: odalar, ölçüler, ışık. Müteahhit
(sayısal tasarımcı) çizimi tuğlaya çevirir: duvar kalınlığı, kiriş, boru çapı —
mimarın çiziminde olmayan ama olmazsa ev yıkılan kararlar. Kiracı (gömülü
yazılımcı) evde yaşar: hangi anahtarın hangi lambayı yaktığını bilmek zorundadır
ve tesisat şemasını görmemişse yanlış sigortayı atar. Ev yalnızca üçü aynı
çizime bakıyorsa çalışır; bit-true model o ortak çizimdir.
:::

## Kavram: üç rol ve teslim nesneleri

| Rol | Dünyası | Ürettiği | Teslim ettiği |
|---|---|---|---|
| Sistem / algoritma mühendisi | MATLAB, Python; kayan nokta | Algoritma, performans bütçesi, **bit-true model** | Test vektörleri + golden çıktı, sabit nokta spesifikasyonu (bit, Q, yuvarlama) |
| Sayısal tasarımcı | RTL (VHDL/Verilog/SystemVerilog), HLS; sabit nokta | IP blokları, pipeline, SSR yapısı, register arayüzü | Bit-exact simülasyon raporu, **register haritası**, latency tablosu |
| Gömülü yazılımcı (PS) | C/C++, Linux/RTOS; register ve DMA | Sürücü, kalibrasyon, parametre yönetimi, telemetri | Sahada doğrulama: snapshot, karşılaştırma betikleri, hata raporu |

Üç rol arasında iki sözleşme dolaşır: **bit-true model + test vektörleri**
(algoritma → RTL) ve **register haritası + latency tablosu** (RTL → yazılım).
Sözleşmelerden biri eksikse ürün yine çıkar ama her hata üç kişinin toplantısı
olur.

## Kavram: akış — kayan noktadan donanıma

{{svg:g-130-gelistirme-akisi.svg|Uçtan uca geliştirme akışı. Kayan noktalı model (MATLAB/Python) → sabit noktalı model (bit genişlikleri, yuvarlama, saturation kararları; kayan noktayla fark ölçülür) → bit-true referans (donanımın üreteceği bitlerin aynısı) → HDL üretimi dört yoldan biriyle: elle RTL, HDL Coder, Vitis Model Composer, HLS → RTL simülasyonu (test vektörleriyle bit-exact karşılaştırma) → sentez / yerleştirme / timing → donanımda doğrulama (ILA, snapshot, DMA ile yakalama → aynı karşılaştırma). Yeşil oklar PS'e açılan parametreleri, kırmızı geri oklar bir kapıda başarısız olunca dönülen adımı gösterir.|kaydir}}

Akışın kapıları şunlardır:

1. **Kayan noktalı model.** Algoritma doğru mu? Ölçütler sistem düzeyindedir:
   hassasiyet, Pfa, PW hatası. Bu aşamada bit yoktur; `double` kullanılır.
2. **Sabit noktalı model.** Her sinyale bit genişliği ve Q formatı, her kesme
   noktasına yuvarlama ve taşma davranışı atanır. Kayan nokta ile fark ölçülür:
   "16 bit veri, 18 bit katsayı ile stopband 87 dB'ye düşüyor, 93 yerine —
   kabul." Bu aşama iteratiftir; MATLAB Fixed-Point Designer ya da Python'da
   elle `np.round(x * 2**15)` ile yapılır, fark etmez.
3. **Bit-true referans.** Sabit noktalı model, donanımın **birebir** yapacağı
   işlemleri yapar hâle getirilir: aynı sırada çarp, aynı noktada yuvarla,
   aynı genişlikte doyur. Sonuç artık bir dizi tam sayıdır. Bu referansın çıktısı
   **golden** dosyadır.
4. **HDL üretimi.** Dört yol vardır; hepsi meşru, seçim ekibe ve bloğa bağlıdır:
   - *Elle RTL*: en çok kontrol, en çok emek; yüksek hızlı SSR yollar ve
     arayüzler için standart.
   - *HDL Coder* (Simulink/MATLAB'dan): bit-true model ile RTL aynı kaynaktan
     çıkar, eşleşme neredeyse otomatik; SSR ve pipeline desteği vardır.
   - *Vitis Model Composer*: Simulink içinde AMD IP blokları; DSP-yoğun zincirler
     için hızlı.
   - *HLS* (C/C++'tan): kontrol mantığı ve algoritmik bloklar için üretken;
     bit genişlikleri `ap_fixed<16,1>` gibi türlerle açıkça yazılır.
5. **RTL simülasyonu.** Test vektörleri RTL'e verilir, çıkış golden ile
   karşılaştırılır. Ölçüt: **bit-exact**, yani fark tam sıfır. Fark varsa ya
   RTL ya model yanlıştır; hangisi olduğunu bulmak akışın en öğretici adımıdır.
6. **Sentez ve timing.** Tasarım fabric'e sığıyor mu, saat kapanıyor mu?
   Burada başarısızlık algoritmaya dönüş demektir: kelime kısalt, pipeline ekle,
   SSR'ı artır.
7. **Donanımda doğrulama.** Karta gerçek ya da sentetik sinyal verilir, iç
   noktalardan veri yakalanır ve **aynı golden** ile karşılaştırılır.

:::formul id=bit-exact baslik="Bit-exact karşılaştırma ve hizalama"
f: e[n] = y_{RTL}[n + L] − y_{ref}[n]      max_n |e[n]| = 0
f: L = L_{pipeline} + L_{arayüz}      (grup gecikmesi her iki tarafta da vardır, L'ye girmez)
s: y_{RTL}, y_{ref} | donanım/RTL çıkışı ve bit-true referans çıkışı | tam sayı (LSB)
s: L | RTL'in modele göre ek gecikmesi | örnek
s: L_{pipeline} | bloğun register gecikmesi (latency tablosundan) | saat
s: L_{arayüz} | AXI-Stream / FIFO / yakalama gecikmesi | saat
o: 15 tap'lik FIR örneği (aşağıda): pipeline 4 saat (çarpım 1 + toplayıcı ağacı 2 + yuvarlama 1) → L = 4; grup gecikmesi 7 örnek iki tarafta da aynıdır. Karşılaştırma `y_rtl(5:end)` ile `y_ref(1:end-4)` arasında yapılır, ilk 7 + 4 örnek "ısınma" olarak atlanır.
o: Referans senaryoda DDC çıkışı için tipik L ≈ 60–120 örnek (300 MSPS'te 0.2–0.4 µs); bu değer PDW TOA'sına sabit ofset olarak girer ve kalibre edilir ({{bolum:25}}).
:::

## İlk karşılaşma: 15 tap'lik bir FIR iki dünyada

Aşağıdaki iki sütun aynı filtredir: kesim 0.2·fs, Hamming pencereli, 15 tap.
Solda kayan noktalı model ve onun bit-true hâli; sağda RTL. Katsayılar 16 bit
Q1.15'e yuvarlanmıştır (toplamı tam 32 768 = 1.0 olacak biçimde), veri 16 bit,
çarpım 32 bit, toplayıcı ağacı 36 bit, çıkış yuvarlayarak 16 bit. Bu
kılavuzda `matlab-fpga` kutusunu her gördüğünde soldaki "ne yapıyor", sağdaki
"nasıl yapıyor" sorusunun cevabıdır.

:::matlab-fpga baslik="15 tap alçak geçiren FIR"
::matlab::
Kayan noktalı model — sonsuz hassasiyet, tek satır konvolüsyon:

```matlab
fc = 0.2;  Ntap = 15;  m = (Ntap-1)/2;
n  = (0:Ntap-1) - m;
h  = 2*fc*sinc(2*fc*n) .* hamming(Ntap).';
h  = h / sum(h);                 % DC kazancı 1
y  = filter(h, 1, x);            % x: double
```

Bit-true hâli — katsayı ve veri Q1.15, çarpım Q2.30, yuvarlayarak Q1.15:

```matlab
hq = round(h * 2^15);            % 16-bit tam sayı katsayı
% [70 207 0 -1082 -1309 2527 9438 13066 9438 2527 -1309 -1082 0 207 70]
xq = round(x * 2^15);            % 16-bit veri
acc = filter(hq, 1, xq);         % 36-bit'e kadar tam sayı toplam
yq  = floor((acc + 2^14) / 2^15);       % yuvarla (round half up), 15 bit at
yq  = max(-32768, min(32767, yq));      % doyur → golden
```
::fpga::
Aynı filtrenin RTL iskeleti (tek örnek/saat, Verilog):

```verilog
module fir15 (input clk, input signed [15:0] x, output reg signed [15:0] y);
  // katsayılar Q1.15 — bit-true modeldeki hq ile birebir
  localparam signed [15:0] H [0:14] = '{
    16'sd70, 16'sd207, 16'sd0, -16'sd1082, -16'sd1309, 16'sd2527,
    16'sd9438, 16'sd13066, 16'sd9438, 16'sd2527, -16'sd1309,
    -16'sd1082, 16'sd0, 16'sd207, 16'sd70 };
  reg signed [15:0] d [0:14];            // gecikme hattı
  reg signed [35:0] acc;                 // 32-bit çarpım + 4 bit büyüme
  integer k;
  always @(posedge clk) begin
    d[0] <= x;
    for (k = 1; k < 15; k = k + 1) d[k] <= d[k-1];
    acc = 36'sd0;
    for (k = 0; k < 15; k = k + 1) acc = acc + d[k] * H[k];
    // yuvarla (round half up) ve doyur: Q2.30 → Q1.15
    acc = acc + 36'sd16384;                          // +2^14
    if (acc[35:30] != {6{acc[35]}})                  // taşma tespiti
      y <= acc[35] ? -16'sd32768 : 16'sd32767;
    else
      y <= acc[30:15];
  end
endmodule
```

Gerçek tasarımda `for` döngüsü DSP slice'lara açılır, simetri (h[k] = h[14−k])
çarpıcı sayısını 8'e indirir ve araya pipeline register'ları girer; hesap aynı
kalır. Bit-true karşılaştırma: `yq` ile `y`, pipeline gecikmesi kadar
kaydırılıp **tam eşit** olmalı.
:::

Bu örnekte iki ayrıntı bütün akışın özetidir. Birincisi, yuvarlama satırı
iki tarafta **aynı** olmalıdır: MATLAB'da `floor((acc + 2^14)/2^15)`, RTL'de
`acc + 16384` sonra `[30:15]`. MATLAB'ın `round` fonksiyonu "half away from
zero" yapar, bu satır "half up" yapar — negatif tam yarımlarda farklıdırlar ve
bit-exact karşılaştırmayı bozarlar. İkincisi, doyurma da modelde vardır: model
doyurmuyorsa RTL doyurduğunda fark çıkar, model doyuruyorsa RTL'de doyurma
unutulmuşsa fark çıkar. **Bit-true model, sabit noktanın bütün kararlarını
içerir; RTL bunları icat etmez, kopyalar.**

## Kavram: test vektörleri ve golden referans

Test vektörü, bit-true modele ve RTL'e verilen **aynı giriş dizisidir**; golden
referans, modelin bu girişe ürettiği çıktıdır. İyi bir test vektörü kümesi
rastgele değil, **kasıtlı** tasarlanır:

- **Impuls ve basamak**: filtrenin katsayıları ve gecikmesi doğrudan okunur;
  ilk bakışta yanlış bağlanmış bir tap bile görünür.
- **Tek ton, bin ortasında**: kazanç ve faz; tam ölçeğe yakın seviyede (−1 dBFS)
  ve çok düşük seviyede (−80 dBFS, LSB davranışı).
- **İki ton**: intermodülasyon ve taşma; toplamları tam ölçeği aşacak biçimde
  — **saturation yolunu zorlamayan test yoktur**.
- **Referans darbe**: {{s:sinyal.pw_us}} µs, {{s:sinyal.rise_time_ns}} ns
  kenar; geçici rejim ve TOA ofseti.
- **Gürültü**: tohumlu, tekrarlanabilir; gürültü tabanının modele göre
  yerini doğrular ve "sıfır giriş" (yalnızca LSB titreşimi) durumunu içerir.
- **Uç değerler**: tam ölçek pozitif, tam ölçek negatif, sıfır, +1 LSB, −1 LSB.
  Ardışık tam ölçek işaret değişimi (kare dalga) akümülatör sınırlarını sınar.
- **Register senaryoları**: her PS parametresi için en az iki değer (FTW pozitif
  ve negatif, eşik düşük ve yüksek, katsayı seti A ve B).

Vektörler dosya olarak saklanır (metin ya da ikili; ikili hızlıdır, metin
`diff`lenebilir) ve sürüm kontrolüne girer. Golden dosyası **bit-true modelin
sürümüyle** etiketlenir: model değişince golden değişir, RTL'in eşleşmemesi o
zaman haberdir, hata değil.

## Kavram: donanımdan yakalama ve kapanan döngü

{{svg:g-131-dogrulama-dongusu.svg|Doğrulama döngüsü. Aynı test vektörü iki yoldan gider: solda bit-true model (MATLAB/Python) golden çıktıyı üretir; sağda vektör donanıma girer — ya ADC'nin önüne bir sinyal üretecinden analog olarak ya da ADC'yi atlayıp bir test örüntüsü enjektöründen sayısal olarak. Zincirin iç noktalarından ILA (küçük, tetiklemeli), snapshot buffer (BRAM/DDR, PS tarafından okunur) veya DMA (sürekli akış) ile veri yakalanır. Karşılaştırma betiği hizalar (L), farkı bit bit hesaplar ve ilk farkın örnek numarasını raporlar. Yeşil: PS register'ları (enjektör seçimi, snapshot tetik ve nokta seçimi). Kapanış: fark sıfırsa geç; değilse fark hangi noktada başladıysa o bloğa dön.|kaydir}}

Simülasyon RTL'in modele eşit olduğunu söyler; donanımın RTL'e eşit olduğunu
söylemez. Saat geçişleri (CDC), JESD hizalaması, reset sırası, sıcaklık,
sentez sırasında yanlış kısıtlanmış bir yol — bunlar ancak kartta görünür. Bu
yüzden döngü donanımda kapanır ve üç yakalama aracı vardır:

**ILA** (Integrated Logic Analyzer): fabric içine gömülen, tetikleme koşuluyla
birkaç bin örnek yakalayan araç. Hızlı, her sinyale takılabilir; ama derinliği
küçüktür (BRAM'e sığan kadar), yeniden sentez ister ve PS'ten değil JTAG'dan
okunur. Tasarımcının aracıdır; yazılımcı sonuçlarını CSV olarak alır.

**Snapshot buffer**: tasarımın kalıcı bir parçası olarak zincirin seçilebilir
bir noktasından N örneği BRAM'e ya da DDR'a yazan blok; PS bir register ile
tetikler, nokta seçer ve dolunca okur. Referans senaryoda DDC çıkışında 64k
örnek (64k × 32 bit = 256 KB, 218 µs) tipik bir boyuttur. Yazılımcının
aracıdır: sahada, JTAG olmadan, saniyeler içinde.

**DMA akışı**: zincirin bir noktasından sürekli veri. DDC çıkışı
{{s:ddc.cikis_veri_hizi_gbps}} Gbps'tir — DDR ve PCIe için ağır ama
mümkün; ADC çıkışı ({{s:adc.veri_hizi_gbps_16bit_paket}} Gbps) pratikte
yalnızca kısa patlamalarla. Uzun kayıtlar ve istatistiksel testler (Pfa
ölçümü, {{bolum:21}}) için tek yol.

Yakalanan veri modele **aynı stimulusla** karşılaştırılır. Stimulus iki yoldan
gelir: analog (sinyal üreteci → ADC; gerçekçi ama gürültü ve faz rastgele, bit
bit karşılaştırma yapılamaz, istatistiksel karşılaştırma yapılır) ya da sayısal
(**test örüntüsü enjektörü** — test pattern injector: ADC yerine BRAM'den okunan ya da PS'ten
yüklenen bir dizi; deterministik, bit-exact karşılaştırma mümkündür). İyi bir
kartta ikisi de vardır ve enjektör seçimi bir register bitidir.

## Kavram: hangi parametreler PS'e açılır

Her sayısal blok iki tür parametreye sahiptir: **sentez zamanı sabitleri**
(kelime genişliği, tap sayısı, SSR faktörü, decimation yapısı, akümülatör
genişliği) ve **çalışma zamanı parametreleri** (register). Kural: bir parametre
donanımın **yapısını** değiştiriyorsa sabittir; **davranışını** değiştiriyorsa
register olur. Register olması gerekenler ve tipik biçimleri:

| Parametre | Register mi? | Biçim | Neden |
|---|---|---|---|
| NCO FTW, POW, işaret | Evet | 32 bit tam sayı, 16 bit, 1 bit | Frekans planı çalışma zamanında değişir ({{bolum:14}}) |
| Tespit eşiği, CFAR α, N, guard | Evet | Q formatlı 16 bit; küçük tam sayılar | Ortama göre ayarlanır ({{bolum:23}}) |
| Filtre katsayıları | Çoğu zaman | 18 bit Q2.16 dizisi, katsayı RAM'i | Bant değişimi, kalibrasyon; tap sayısı sabittir |
| Kazanç / ölçek | Evet | Q4.12 ya da kaydırma miktarı | Seviye planı; taşma riskiyle birlikte |
| Decimation oranı | Bazen | Sınırlı küme (2, 4, 8) | CIC R değişebilir; yapı (N kademe) sabittir |
| Mod bitleri: bypass, enjektör, inversion, dither | Evet | 1 bit | Test ve konfigürasyon |
| Sticky bayraklar: OVF, FIFO dolu, JESD hata | Evet (salt okunur, yazarak temizle) | 1 bit | Teşhis ({{bolum:12}}) |
| Bit genişlikleri, tap sayısı, SSR, pipeline | Hayır | Sentez parametresi | Yapıyı değiştirir |

Bir parametrenin register olması onun **doğrulanması gerektiği** anlamına
gelir: test vektörü kümesinde her register alanı için en az iki değer ve
geçersiz değer davranışı (ör. eşik 0 → her örnek tespit) bulunmalıdır. Register
haritası da bit-true modelin bir parçasıdır: modelde `params.thresh_q15`
diye bir alan varsa RTL'de `THRESH[15:0]` vardır ve ikisinin dönüşümü tek
yerde yazılıdır.

:::uc-goz
::rf::
RF mühendisi için bu akış, analog ölçümün sayısal karşılığıdır: spektrum
analizörle bakılan nokta artık bir snapshot register'ıdır. Katkısı iki
noktadadır: (1) test stimulusunun gerçekçi olması — tek ton ADC'yi lineer
bölgede sınar, ama gerçek almaç iki güçlü emiter + zayıf sinyal + gürültüyle
yaşar; test vektörleri bu karışımı içermelidir. (2) Analog yol ile sayısal yolun
sınırındaki seviye kalibrasyonu: −60 dBm giriş ADC'de kaç dBFS? Bu tek sayı
yanlışsa bütün sayısal zincir "doğru ama yanlış ölçekte" çalışır.
::fpga::
Tasarımcının günlük döngüsü: golden dosyayı testbench'e oku, RTL'i çalıştır,
farkı `assert` et, ilk fark örneğini yazdır. Bit-exact hedefi RTL'i **model
kadar iyi** yapar, daha iyi değil; modelin kabul edilen kaybı RTL'in kaybıdır.
Latency tablosu (her bloğun saat cinsinden gecikmesi) teslim belgesidir;
karşılaştırma betiği L'yi bu tablodan alır. Sentez sonrası davranış farkı
(simülasyon geçer, kart geçmez) çoğu zaman CDC, reset polaritesi ya da
kısıtlanmamış bir yoldur; ilk bakılacak yer timing raporudur, RTL değil.
::yazilim::
Yazılımcının doğrulama araç kutusu üç parçadır: (1) snapshot sürücüsü —
tetikle, bekle, oku, dosyaya yaz; (2) enjektör sürücüsü — test vektörünü yükle,
ADC'yi atla; (3) karşılaştırma betiği — Python/NumPy ile hizala, farkı ölç,
raporla. Bunlar ürün koduna girmez ama ürün kodu kadar bakım görür. Register
yazımlarında model ile aynı dönüşüm fonksiyonunu kullan (`q_encode`,
{{bolum:12}}); dönüşüm iki yerde yazılıysa bir gün farklı olur.
:::

## Yazılımcıya dokunan yer

Kurgusal, öğretici bir snapshot arayüzü (register adları {{bolum:30}}'daki
haritayla uyumludur):

```c
#include <stdint.h>
#include <stdio.h>

/* Kurgusal snapshot bloğu: zincirin seçilen noktasından N kompleks örnek
 * yakalar. SNAP_SRC: 0 = ADC (reel 16 bit paketli), 1 = mixer çıkışı,
 * 2 = CIC çıkışı, 3 = DDC çıkışı (16+16 bit I/Q). */
#define SNAP_CTRL   0x0100   /* [0] tetikle, [1] enjektör açık, [7:4] kaynak */
#define SNAP_STAT   0x0104   /* [0] dolu, [1] OVF (yakalama sırasında taşma) */
#define SNAP_LEN    0x0108   /* örnek sayısı */
#define SNAP_DATA   0x1000   /* BRAM penceresi: 32 bit/örnek (I[31:16], Q[15:0]) */

extern uint32_t reg_rd(uint32_t off);
extern void     reg_wr(uint32_t off, uint32_t v);

/* DDC çıkışından n örnek yakala, ikili dosyaya yaz (int16 I, int16 Q). */
int snapshot_ddc(const char *dosya, uint32_t n)
{
    reg_wr(SNAP_LEN,  n);
    reg_wr(SNAP_CTRL, (3u << 4) | 1u);              /* kaynak = DDC, tetikle */
    while (!(reg_rd(SNAP_STAT) & 1u)) { /* bekle: 64k örnek @300 MSPS = 218 µs */ }
    FILE *f = fopen(dosya, "wb");
    if (!f) return -1;
    for (uint32_t k = 0; k < n; k++) {
        uint32_t w = reg_rd(SNAP_DATA + 4 * k);
        int16_t iq[2] = { (int16_t)(w >> 16), (int16_t)(w & 0xFFFF) };
        fwrite(iq, sizeof iq, 1, f);
    }
    fclose(f);
    return (reg_rd(SNAP_STAT) & 2u) ? 1 : 0;        /* 1: yakalamada taşma vardı */
}
```

Karşılaştırma tarafı Python'da birkaç satırdır ve hep aynı iskeleti taşır:

```python
import numpy as np
hw  = np.fromfile("snap_ddc.bin", dtype="<i2").reshape(-1, 2)   # I, Q int16
ref = np.load("golden_ddc.npy")                                 # bit-true model, int16
L   = 96                                                         # latency tablosundan
n   = min(len(hw) - L, len(ref))
e   = hw[L:L + n].astype(int) - ref[:n].astype(int)
print("maks |fark| =", np.abs(e).max(), "LSB; ilk fark örneği:",
      (np.nonzero(e.any(axis=1))[0][:1] or ["yok"])[0])
```

{{svg:g-132-fark-desenleri.svg|Karşılaştırma betiğinin dört tipik çıktısı (öğretici, sentetik veri): (a) seyrek, ±1 LSB, yalnızca negatif örneklerde → yuvarlama kuralı uyuşmazlığı; (b) sinyal biçimli büyük fark → hizalama hatası, doğru L ile sıfırlanır; (c) belirli bir örnekten sonra yalnızca tepelerde → taşma/saturation farkı; (d) yalnızca ilk örneklerde → başlangıç durumu farkı, ısınma atlanır. Fark deseninin biçimi, kaynağı adıyla söyler.}}

Sonuç "maks |fark| = 0" ise donanım modeldir. 1 LSB'lik fark bir yuvarlama
farkıdır (half-up / half-even / away-from-zero uyuşmazlığı — ilk kontrol);
büyük ve rastgele fark hizalama (L) hatası ya da farklı test vektörüdür;
belirli bir örnekten sonra başlayan fark taşma ya da akümülatör sınırıdır.

:::tuzak Bit-exact ama yanlış
Bit-true model CIC'in çıkışını 7 bit kaydırarak kesiyor (8 yerine), RTL de
modelden kopyalandığı için aynı şeyi yapıyor. Simülasyon bit-exact geçer,
donanım bit-exact geçer, ama almaç 6 dB fazla kazançla çalışır ve güçlü
sinyallerde doyar. Bit-exact karşılaştırma yalnızca "RTL = model" der; "model =
doğru" demez. Modelin doğruluğu **kayan noktalı referansla** ayrıca ölçülür
(2. kapı) ve bu ölçüm sabit noktaya geçişte bir kez değil, her model
değişikliğinde tekrarlanır. Sahada belirti: sistem düzeyi ölçümler
(hassasiyet, kayıp) tasarım bütçesinden sistematik olarak sapar, ama kimse
"fark" bulamaz.
:::

:::tuzak İlk 200 örnek farklı, gerisi aynı
Karşılaştırma betiği yüzlerce fark raporlar, hepsi kaydın başında. Nedeni
hizalama değil **başlangıç durumu**dur: modelin gecikme hatları sıfırdan
başlar, donanımınki önceki sinyalin kalıntısıyla ya da reset'ten sonra
tanımsız/rastgele değerle. Snapshot'ı reset'ten hemen sonra almak yerine
zincir "ısındıktan" (en uzun grup gecikmesi + pipeline kadar örnek geçtikten)
sonra almak ve karşılaştırmayı o kadar örnek atlayarak başlatmak gerekir.
Uzun bir CIC + FIR zincirinde bu birkaç yüz örnektir. Tersi de tuzaktır: her
şeyi atlayan bir betik, gerçekten kayıtta olan geçici bir hatayı (JESD
yeniden hizalanması gibi) görmez; atlanan miktar tabloya dayanmalı, "artık
eşleşene kadar" seçilmemelidir.
:::

:::tuzak Test vektörü tam ölçeği hiç görmedi
Bütün vektörler −20 dBFS ton ve gürültü. Simülasyon ve donanım eşleşir; sahada
yakın bir emiter gelince mixer çıkışı taşar ve RTL'de unutulan saturation, wrap
olarak ortaya çıkar ({{bolum:12}}). Model saturation yapıyordu, RTL yapmıyordu;
ama hiçbir vektör o yolu çalıştırmadığı için fark hiç oluşmadı. Bit-exact
karşılaştırmanın kapsamı vektörlerin kapsamıdır: **her saturation, her taşma
bayrağı, her register sınırı en az bir vektörle tetiklenmeli** ve
karşılaştırma raporu "hangi yollar çalıştı" bilgisini (coverage) içermelidir.
:::

:::ozet
- Algoritma üç kez yazılır: kayan nokta (doğru mu?), sabit nokta (sığıyor mu, kayıp ne?), bit-true referans (donanım tam olarak bunu üretir).
- Üç rol, iki sözleşme: bit-true model + test vektörleri (algoritma → RTL); register haritası + latency tablosu (RTL → yazılım).
- HDL dört yoldan üretilir: elle RTL, HDL Coder, Model Composer, HLS; hangisi olursa olsun kapı aynıdır: golden ile **bit-exact** (fark = 0).
- Test vektörleri kasıtlıdır: impuls, ton, iki ton (taşma), referans darbe, gürültü, uç değerler, her register için ≥ 2 değer.
- Donanımdan yakalama: ILA (tasarımcı, JTAG, sığ), snapshot buffer (yazılımcı, register, orta), DMA (uzun kayıt, bant genişliği sınırlı); enjektör deterministik karşılaştırmayı mümkün kılar.
- Karşılaştırma: L kadar hizala, ısınmayı atla, fark ölç; 1 LSB = yuvarlama uyuşmazlığı, büyük rastgele = hizalama, belirli örnekten sonra = taşma.
- Register olan parametreler davranışı değiştirir (FTW, eşik, katsayı, kazanç, mod bitleri); yapıyı değiştirenler sentez sabitidir. Her register test vektörüne ve dönüşüm fonksiyonuna sahiptir.
:::

:::kendini-sina
S: RTL çıkışı ile golden arasında yalnızca ±1 LSB'lik, seyrek farklar var. İlk şüphelin nedir?
C: Yuvarlama kuralı uyuşmazlığı: model `round` (half away from zero), RTL `+2^(k−1)` sonra kesme (half up) yapıyordur; ikisi negatif tam yarımlarda farklı sonuç verir. Convergent rounding kullanılıyorsa çift/tek kuralı da kontrol edilir. Fark ±1 LSB ile sınırlı ve seyrekse hizalama ya da taşma değildir.
S: Snapshot'tan gelen veri golden ile hiçbir kaydırmada eşleşmiyor, ama spektrumları birbirine benziyor. Ne olmuş olabilir?
C: Stimulus deterministik değildir: analog üreteçten gelen sinyal ADC gürültüsü ve rastgele başlangıç fazı taşır; bit-exact karşılaştırma ancak sayısal enjektörle yapılabilir. Analog stimulusla yalnızca istatistiksel karşılaştırma (güç, spektrum, SNR) yapılır. İkinci olasılık: farklı test vektörü sürümü ya da farklı register ayarı (FTW işareti gibi).
S: Filtre tap sayısı neden register değil de sentez sabitidir; katsayılar neden register olabilir?
C: Tap sayısı DSP slice sayısını, gecikme hattı uzunluğunu ve pipeline'ı belirler — yapıyı değiştirir, çalışma zamanında değiştirilemez. Katsayılar aynı yapının içindeki değerlerdir; katsayı RAM'ine yazılarak davranış değişir. Bu yüzden "63 tap'lik yapıda 31 tap'lik filtre" istenirse üst katsayılar sıfırlanır; yapı aynı kalır.
S: Bit-exact geçen bir tasarım sahada tasarım bütçesinden 6 dB kötü çalışıyor. Nereye bakarsın?
C: Bit-exact yalnızca RTL = model der. Modelin kendisi kayan noktalı referansla karşılaştırılır (ölçek, kaydırma, kazanç hataları burada çıkar) ve analog-sayısal sınırındaki seviye kalibrasyonu (dBm ↔ dBFS) doğrulanır. Ayrıca sticky OVF bayrakları okunur: model ve RTL aynı taşmayı yapıyor olabilir.
:::

:::kopru
Akışı ve doğrulama döngüsünü bildiğine göre artık zincirin sayısal bloklarını
tek tek açabiliriz — her birinde "modelde bir satır, RTL'de şu yapı, register'da
şu alan" üçlüsünü göreceksin. İlk blok, sayısal almacın saati olan NCO'dur:
Bölüm 14'te faz akümülatörü, FTW ve faz kırpma spur'larıyla başlıyoruz.
:::
