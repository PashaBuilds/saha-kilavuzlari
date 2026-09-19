# Bölüm 15 — Sayısal Mixing ve Quadrature Demodülasyon
::meta onkosul=2,6,8,12,14 acar=16,17,18,22,25 blok=mixing rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "Üreteçten IF'in 5 MHz üstünde ton veriyorum, DDC çıkışında
−5 MHz'de görüyorum; ADC mi bozuk?" Hayır: sinyal ikinci Nyquist bölgesinden
katlanırken evrilmişti ({{bolum:8}}) ve NCO'nun dönüş yönü bunu düzeltecek
biçimde seçilmemişti. Sayısal mixing, ADC'den gelen reel örnek dizisini bir
kompleks üstelle çarparak spektrumu kaydırma işlemidir; analog mixer'ın
({{bolum:6}}) sayısal ikizi, ama iki farkla: kusursuz quadrature (I ve Q tam
90°, tam eşit genlik) ve yönü seçilebilir kaydırma. Bu bölüm çarpımın
spektrumda ne yaptığını dört karede izler, "toplam frekans" kopyasının nereye
düştüğünü ve neden filtrelenmesi gerektiğini gösterir, çarpımın ADC içinde mi
FPGA'da mı yapılacağı kararını tartar ve referans senaryonun NCO'sunun neden
çarpıcısız gerçeklenebildiğini açıklar.
:::

## Sezgi: döner tablayı geri çevirmek

{{bolum:2}}'de bir sinüsün, zıt yönlerde dönen iki fazörün toplamı olduğunu
görmüştün: $cos(ωn) = ½e^{jωn} + ½e^{−jωn}$. Reel bir sinyalin spektrumu bu
yüzden simetriktir; +600 MHz'de ne varsa −600 MHz'de aynası vardır. Kompleks
mixing bu tabloyu bir bütün olarak döndürmektir: sinyali $e^{−jω_0n}$ ile
çarpmak, spektrumdaki her şeyi $ω_0$ kadar **sola** kaydırır. Gerçek sinyalin
+600'deki kopyası 0 Hz'e iner ve orada "durur" (döner tablayı sinyalin hızında
geri çevirdin); −600'deki kopyası ise −1200 MHz'e gider. İstediğin ilki,
istemediğin ikincisidir. Analog mixer'daki "fark frekansı / toplam frekansı"
ikilisi burada aynen vardır: fark 0'a, toplam −1200'e düşer ve toplamı
arkadan gelen filtre ({{bolum:16}}) temizler.

:::analoji Atlıkarınca
Dönen bir atlıkarıncada oturan çocuğun elindeki bayrağı fotoğraflamak
istiyorsun. Kameran sabitse bayrak her karede başka yerde: frekansı var.
Kamerayı atlıkarıncanın hızında, **ters yönde** döndürürsen bayrak karede
sabitlenir — frekansı sıfırlandı. Aynı anda arka plandaki sabit ağaç, artık
kameraya göre iki kat hızla döner: o "toplam frekans" bileşenidir; netlik
istiyorsan ağacı çerçeveden çıkarırsın (filtre). Kamerayı yanlış yöne
döndürürsen bayrak yavaşlamaz, hızlanır: NCO işaret hatasının tam karşılığı.
:::

## Kavram: reel çarpı kompleks üstel, adım adım

ADC çıkışı reel bir dizidir: $x[n]$, {{s:adc.bit}} bit, fs =
{{s:adc.fs_msps}} MSPS. NCO ({{bolum:14}}) iki dizi üretir: $cos(ω_0n)$ ve
$sin(ω_0n)$. Çarpım iki reel çarpımdır:

:::formul id=mix baslik="Kompleks aşağı çevirim"
f: y[n] = x[n] · e^{−jω_0n} = x[n]·cos(ω_0n) − j · x[n]·sin(ω_0n)      I[n] = x[n]·cos(ω_0n),  Q[n] = −x[n]·sin(ω_0n)
f: x[n] = cos(ω_1n)  →  y[n] = ½e^{j(ω_1−ω_0)n} + ½e^{−j(ω_1+ω_0)n}
s: x[n] | ADC çıkışı (reel) | LSB
s: ω_0 = 2π f_{NCO}/f_s | NCO açısal frekansı | rad/örnek
s: ω_1 | giriş tonunun (katlanmış) frekansı | rad/örnek
s: I, Q | eş fazlı ve dik bileşen (kompleks çıkışın gerçek ve sanal kısmı) | LSB
o: f_1 = {{s:adc.alias_mhz}} MHz (IF {{s:on_uc.if_ghz}} GHz'in 2. bölgeden katlanmış hali), f_NCO = {{s:ddc.nco_mhz}} MHz → fark bileşeni **0 MHz**, toplam bileşeni −1200 MHz (= fs/2, tam bant kenarında).
o: IF'in 5 MHz üstündeki bir ton katlanınca 595 MHz'e gelir (evrik); e^{−jω_0n} ile çarpınca **−5 MHz**'e iner. Evrikliği düzeltmek için NCO e^{+jω_0n} döndürülür: −595 MHz'deki kopya +5 MHz'e gelir, +595'teki kopya +1195 MHz'e gider ve filtrelenir.
:::

Formüldeki ikinci satır bütün hikâyedir: reel bir tonun iki fazöründen biri
$ω_1 − ω_0$'a, diğeri $−(ω_1 + ω_0)$'a gider. Genlikler yarıya iner (½) — bu
kompleks gösterimin doğal sonucudur, kayıp değildir: iki fazörün gücü tek
kompleks fazörde toplanır. Filtre toplam bileşenini attıktan sonra elinde
kalan tek fazör, reel tonun **tüm bilgisini** taşır.

{{svg:g-150-ddc-dort-kare.svg|DDC'nin dört karelik spektrum hikâyesi (referans senaryo, hesaplanmış). (1) ADC çıkışı: reel, fs = 2400 MSPS; 1.8 GHz IF'teki darbeli sinyal 2. Nyquist bölgesinden 600 MHz'e evrik katlanmış, ±600 MHz'de simetrik iki kopya, gri gürültü tabanı tüm bantta. (2) NCO = −600 MHz ile çarpım sonrası: istenen kopya 0 Hz'de (mavi), "toplam frekans" kopyası −1200 MHz'de bant kenarında (kırmızı); gürültü tabanı yerinde. (3) ±150 MHz alçak geçiren filtre sonrası (altın kesikli yanıt): image ve bant dışı gürültü atıldı, sinyal 0 Hz çevresinde, gürültü gücü 8 kat azaldı. (4) 8'e decimation sonrası: fs = 300 MSPS, eksen ±150 MHz — spektrum aynı, yalnızca "boş" kısım atıldı; 300 MHz'lik kompleks bant 300 MSPS ile tam temsil edilir.|kaydir}}

Dört karede iki şeye dikkat et. Gürültü tabanı ilk iki karede **aynı yerde**
kalır: mixing gürültüyü de kaydırır ama gücünü değiştirmez. Üçüncü karede
filtre bant dışı gürültüyü atınca toplam gürültü gücü fs/2 : BW oranında
düşer — bu, decimation'ın "işlem kazancı"dır ve Bölüm 16'da sayıya
dökülür ({{s:turetilmis_beklenen.islem_kazanci_1200_300_db}} dB). Dördüncü
karede eksen daralır ama spektrumun **şekli değişmez**: decimation bilgi
atmaz, yalnızca artık gerekmeyen örnekleri atar. Bu ancak filtre önce
çalıştıysa doğrudur; sırayı bozarsan üçüncü kare olmadan dördüncüye
gidersin ve image ile gürültü bandın içine katlanır.

## Kavram: reel giriş, kompleks çıkış — veri hızı neden "iki katına" çıkar

ADC'den saniyede 2400 milyon reel örnek gelir. Mixer çıkışı saniyede 2400
milyon **kompleks** örnektir: I ve Q, ikişer 16 bit. Veri hızı görünürde iki
katına çıkmıştır: {{s:adc.veri_hizi_gbps_16bit_paket}} Gbps'ten 76.8 Gbps'e.
Ama bilgi iki katına çıkmadı — reel sinyalin negatif frekansları pozitiflerin
aynasıydı, kompleks gösterim bu fazlalığı açıkça taşıyor. Kompleks bir dizinin
fs örnek/saniye ile temsil edebildiği bant fs'tir (−fs/2 … +fs/2), reel dizinin
ise fs/2. Yani 2400 MSPS kompleks veri 2400 MHz'lik bir bant taşıyabilir, oysa
elindeki sinyal en fazla 1200 MHz'lik bir bantta yaşıyor. Fazlalığı geri
almanın yolu decimation'dır: 2'ye bölersen veri hızı ADC'dekine döner; 8'e
bölersen ({{s:ddc.decimation_toplam}}) {{s:ddc.cikis_veri_hizi_gbps}} Gbps'e
iner ve ±{{s:ddc.cikis_bant_mhz}} MHz'lik kompleks bant kalır.

:::pasaport durak="Mixer çıkışı" alan=sayisal
Alan: sayısal (FPGA, SSR-8)
!Frekans: baseband — sinyal 0 Hz çevresinde, image −1200 MHz'de (henüz filtrelenmedi)
!Tip: kompleks I/Q
fs: {{s:adc.fs_msps}} MSPS (ADC saati ile aynı)
!Bit: 2 × 16 bit (30 bitlik çarpım yuvarlanarak 16'ya, {{bolum:12}})
!Veri hızı: 2400 · 32 = **76.8 Gbps** (ADC'nin iki katı; decimation geri alacak)
SNR: ADC ile aynı (ideal {{s:turetilmis_beklenen.snr_ideal_14bit_db}} dB tam bantta); mixing SNR değiştirmez
:::

{{svg:g-151-ddc-blok.svg|DDC blok şeması (ortak sembol kütüphanesi). ADC'den gelen reel 14 bit örnek iki sayısal mixer'a girer; NCO'nun cos çıkışı I yolunu, −sin çıkışı Q yolunu besler (işaret = dönüş yönü, INV register biti). Her yolda 30 bitlik çarpım 16 bite yuvarlanır. Ardından iki özdeş alçak geçiren FIR ve ↓8 decimator (Bölüm 16'da CIC + halfband olarak açılır). Çıkış 300 MSPS, 16 + 16 bit. Yeşil: PS register'ları (FTW, POW, INV, filtre katsayıları). Kesikli gri: 300 MHz fabric saati, SSR-8.}}

## Kavram: çarpım nerede yapılır — ADC içinde mi, FPGA'da mı

Modern RF-örnekleyen ADC'lerin ve RFSoC'lerin çoğunda ADC çekirdeğinin hemen
arkasında bir **entegre DDC** vardır: NCO, kompleks mixer ve sabit yapılı
decimation filtreleri (2×, 4×, 8× …) çipin içindedir; JESD204 ya da RFSoC iç
yolu üzerinden FPGA'ya **decimation sonrası** kompleks veri gelir. Alternatif,
ADC'den ham reel örnekleri alıp her şeyi FPGA fabric'inde yapmaktır. Karar
sistem düzeyinde verilir ve yazılımcıyı doğrudan etkiler: NCO register'ı hangi
çipte?

| Ölçüt | Entegre DDC (ADC / RFSoC içinde) | FPGA fabric'te DDC |
|---|---|---|
| Arayüz bant genişliği | Düşük: yalnızca decimation sonrası veri (9.6 Gbps) | Yüksek: ham örnekler ({{s:adc.veri_hizi_gbps_16bit_paket}} Gbps), daha çok JESD şeridi ya da RFSoC iç yolu |
| FPGA kaynağı | Neredeyse sıfır (DSP, BRAM boş kalır) | SSR-8 mixer + CIC + FIR: onlarca DSP, BRAM |
| Esneklik | Sabit filtre şekilleri, sınırlı decimation kümesi, tek ya da az sayıda kanal | İstediğin filtre, oran, kanal sayısı; kanallaştırıcı ({{bolum:17}}) mümkün |
| Eşzamanlı bant | Çıkış bandı decimation ile sınırlı (ör. 300 MHz) | Tam Nyquist bandı fabric'te kalır; birden çok DDC paralel çalışabilir |
| NCO çözünürlüğü / faz kontrolü | Genelde 48 bit, faz sürekli, çok kanal senkronu SYSREF ile | Tasarımcının seçimi; kanal senkronu tek çipte kolay |
| Latency | Düşük ve sabit ama çip içinde, ölçmesi zor | Bilinir, latency tablosunda; snapshot ile ölçülür |
| Yazılımcı için register | ADC'nin SPI/AXI haritasında (üretici sürücüsü) | Kendi register haritanda ({{bolum:30}}) |
| Tipik seçim | Az kanallı, sabit bantlı almaç; radar alıcı kanalı | Geniş bant EH almacı, kanallaştırıcı, araştırma kartı |

Pratikte melez çözümler yaygındır: ADC'nin DDC'si kaba bir 2× decimation ve
kaba frekans kaydırma yapar, ince NCO ve asıl filtreleme fabric'tedir. O zaman
iki NCO vardır ve yazılımcının "frekans" dediği şey ikisinin toplamıdır — bu
kılavuzun referans senaryosunda çarpım fabric'te yapılır ve tek NCO vardır.

## Kavram: fs/4 hilesi — çarpıcısız mixing

NCO frekansını tam fs/4 seçersen $e^{−jπn/2}$ dizisi yalnızca dört değer alır:
1, −j, −1, +j. Yani cos dizisi 1, 0, −1, 0 ve −sin dizisi 0, −1, 0, 1'dir.
Çarpım artık çarpım değildir: örneği ya olduğu gibi al, ya işaretini çevir, ya
sıfırla. **Hiç DSP slice harcamadan** kompleks aşağı çevirim.

:::formul id=fs4 baslik="fs/4 mixing"
f: e^{−jπn/2} = { 1, −j, −1, +j, 1, … }
f: I[n] = x[n] · {1, 0, −1, 0}      Q[n] = x[n] · {0, −1, 0, 1}
s: n | örnek indeksi | —
s: x[n] | reel giriş | LSB
o: Referans senaryoda f_NCO = {{s:ddc.nco_mhz}} MHz = {{s:adc.fs_msps}}/4 → **tam fs/4**. FTW = 2^30 = {{s:ddc.ftw_hex}} olması bunun aynısıdır: akümülatörün yalnızca üst 2 biti değişir, faz kırpma hatası sıfırdır ({{bolum:14}}).
o: SSR-8'de her saatte 8 örnek gelir; dört değerli örüntü 8'e tam böler: I = {x0, 0, −x2, 0, x4, 0, −x6, 0}, Q = {0, −x1, 0, x3, 0, −x5, 0, x7}. Yalnızca kablo ve işaret çevirme; **0 DSP**.
:::

{{svg:g-152-fs4-hilesi.svg|fs/4 hilesi örnek örnek (hesaplanmış, 660 MHz ton, 2400 MSPS). Üstte ADC örnekleri; ortada cos ve −sin dizileri (1, 0, −1, 0 ve 0, −1, 0, 1); altta I ve Q çıkışları: I yalnızca çift indisli örneklerden (her ikide bir işaret ters), Q yalnızca tek indisli örneklerden oluşur. Çarpma yok — işaret çevirme ve sıfırlama; fs/4'ten 60 MHz ötedeki ton I/Q'da 60 MHz'lik yavaş dönüş olarak görünür.}}

Frekans planı böyle seçildiğinde (IF'in katlanmış hali fs/4'e denk gelecek
biçimde) tasarımcı büyük bir kaynak kazanır ve I/Q çıkışlarının yarısı yapısal
olarak sıfır olur — bu da filtreyi yarıya böler. Bedeli esnekliktir: fs/4 tek
bir frekanstır; taramalı bir almaçta NCO'yu 601 MHz'e çekmek istediğinde
çarpıcıya geri dönersin. Bu yüzden birçok tasarım iki yolu birden taşır: fs/4
"hızlı yol" ve genel NCO yolu, register ile seçilir.

## Kavram: Hilbert alternatifi

Kompleks baseband'e gitmenin ikinci yolu, önce reel sinyalden **analitik
sinyal** üretmektir: $x_a[n] = x[n] + j·H{x[n]}$; H, 90° faz kaydıran
**Hilbert filtresidir** (bir FIR). Analitik sinyalin negatif frekansları
sıfırdır; sonra istediğin frekansa kaydırırsın ya da doğrudan zarf ve anlık
frekans alırsın. Dezavantajı, Hilbert FIR'ın 0 Hz ve fs/2 yakınında zayıf
olması ve geniş bantta çok tap istemesidir; avantajı, mixing'siz doğrudan
"reel → kompleks" dönüşümü ve IFM benzeri anlık frekans ölçümleri
({{bolum:25}}) için uygun olmasıdır. Geniş bant EH almaçlarında ana yol
NCO + mixer'dır; Hilbert, dar bantlı ya da özel ölçüm kollarında görülür.

:::widget id=w12 ad="DDC laboratuvarı"
- **Referans senaryo** preset'inde dört paneli izle: (1) ±600 MHz'de simetrik ton, (2) NCO = −600 MHz sonrası 0 Hz'de ton ve −1200 MHz'de image, (3) filtre sonrası yalnızca 0 Hz, (4) decimation-by-8 sonrası ±150 MHz eksende aynı ton. Sonuç satırlarında filtre sonrası toplam gürültü gücünün ≈ 9 dB (2400 : 300 = 8 kat), sinyal gücünün 3 dB (image yarısı gitti) düştüğünü, yani SNR'ın **≈ 6 dB** arttığını gör — Bölüm 16'nın işlem kazancı.
- Giriş tonunu **595 MHz** yap (IF'in 5 MHz üstünün evrik hali): çıkışta −5 MHz gör. NCO işaretini **+** yap: ton +5 MHz'e geçsin — "spectral inversion" bitinin yaptığı budur.
- NCO'yu 601 MHz'e kaydır ve filtre bandını 150 MHz'den **400 MHz**'e genişlet: decimation-by-8 sonrası image ve bant dışı gürültü ±150 MHz'in içine katlansın; "katlanan güç" satırı kırmızıya dönsün. Bandı 150'ye geri al: temizlensin.
- Giriş tipini **darbe** yap (1 µs): 4. panelde spektrumun sinc zarfı ({{bolum:3}}), ana lob genişliği 2 MHz. Filtre bandını 1 MHz'e daraltırsan darbe spektrumunun yan lobları kesilir ve zaman çiziminde kenarlar yumuşar — Bölüm 16'nın "BW ↔ rise time" konusu.
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Analog I/Q demodülatör ({{bolum:6}}) iki mixer, bir 90° hibrit ve iki LPF ile
aynı işi yapar; ama I ve Q yolları hiçbir zaman tam eşit değildir: 0.5 dB
genlik, 2° faz hatası tipiktir ve bu, {{bolum:2}}'de gördüğün image'ı
−30 dBc civarında bırakır. Sayısal mixer'da cos ve sin **aynı tablodan** okunur,
çarpıcılar özdeştir; quadrature hatası LSB düzeyindedir (≈ −90 dBc). DC ofseti
ve LO sızıntısı da yoktur — 0 Hz'deki tek çivi kaynağı truncation bias'ıdır
({{bolum:12}}). Direct IF sampling mimarisinin ({{bolum:7}}) analog I/Q'ya
üstünlüğünün büyük kısmı bu paragraftır.
::fpga::
Genel NCO yolu: SSR-8'de her saatte 8 reel örnek × 8 kompleks NCO değeri = 16
reel çarpım → **16 DSP slice**, 14 × 16 bit, her biri tek slice. Çarpım 30 bit,
yuvarlayarak 16 bite (round-half-up, DSP'nin kendi yuvarlama girişi ile
bedava). Doyurma gerekmez: |x| < 1 ve |NCO| ≤ 1 − LSB olduğundan çarpım tam
ölçeği aşamaz — tek doyurmasız kesme noktası budur. fs/4 yolu: 0 DSP,
yalnızca işaret çevirme (bir toplayıcıdan ucuz) ve çoklayıcı. Latency: NCO 5
saat + çarpım 3 saat + yuvarlama 1 = 9 saat. Çıkış AXI-Stream: tdata 8 × 32 =
256 bit @ 300 MHz.
::yazilim::
Register olarak gördüklerin NCO'nunkilerdir ({{bolum:14}}): `NCO_FTW`,
`NCO_POW`, `NCO_CTRL.INV`, artı `MIX_CTRL.FS4_EN` (fs/4 hızlı yol) ve
`MIX_CTRL.BYPASS` (test: I = x, Q = 0). Sahada ilk kontrol sırası: sinyal
beklenen yerde değilse önce işaret (INV), sonra fs'in hangi saat olduğu, sonra
FS4_EN'in FTW ile çelişip çelişmediği (FS4 açıkken FTW yok sayılır — belgede
yazmalı). Bypass modu, ADC'nin reel spektrumunu DDC çıkışında görmenin en hızlı
yoludur: 0 Hz çevresinde simetrik bir spektrum görüyorsan bypass açıktır.
:::

:::matlab-fpga baslik="Kompleks mixer: genel NCO ve fs/4 yolu"
::matlab::
```matlab
% genel yol: ideal kompleks LO ile çarpım
n  = (0:N-1).';
lo = exp(-1j*2*pi*f_nco/fs*n);      % isaret: -1 asagi, +1 yukari
y  = x .* lo;                        % x reel, y kompleks

% fs/4 yolu: carpim yerine dort degerli oruntu
c  = [1 0 -1 0].';  s = [0 -1 0 1].';
I  = x .* repmat(c, N/4, 1);
Q  = x .* repmat(s, N/4, 1);
% bit-true: x ve NCO 16 bit, carpim Q2.30 -> round -> Q1.15
yq = floor((round(x*2^15) .* round(real(lo)*(2^15-1)) + 2^14) / 2^15);
```
::fpga::
```verilog
// fs/4 yolu, tek ornek/saat: 2-bit faz sayaci, DSP yok
reg [1:0] ph;
always @(posedge clk) ph <= ph + 2'd1;
always @(posedge clk) case (ph)
  2'd0: begin i_out <=  x;      q_out <= 16'sd0; end
  2'd1: begin i_out <= 16'sd0;  q_out <= -x;     end
  2'd2: begin i_out <= -x;      q_out <= 16'sd0; end
  2'd3: begin i_out <= 16'sd0;  q_out <=  x;     end
endcase
// inv=1 icin q_out isaretini cevir (e^{+j} yonu)

// genel yol, DSP48 ile: 14x16 carpim + yuvarlama
wire signed [29:0] pi = x * nco_cos;           // Q2.28
wire signed [29:0] pq = x * nco_sin_neg;
assign i_out = (pi + 30'sd8192) >>> 14;        // +2^13, 14 bit at -> Q1.15
assign q_out = (pq + 30'sd8192) >>> 14;
```
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>

/* Kurgusal mixer kontrol register'ı */
#define MIX_CTRL_FS4_EN   (1u << 0)   /* fs/4 hızlı yol; FTW yok sayılır */
#define MIX_CTRL_INV      (1u << 1)   /* dönüş yönü: 1 = e^{+j}, evrik spektrumu düzeltir */
#define MIX_CTRL_BYPASS   (1u << 2)   /* I = x, Q = 0 (test) */

/* Baseband'de gözlenen frekansı RF'e çevir (ve tersi).
 * f_bb: DDC çıkışında ölçülen frekans (Hz, işaretli)
 * Zincir: RF -> IF = RF - LO (low-side) -> 2. bölgeden katlanır (evrik):
 *         f_alias = fs - IF  -> NCO ile 0'a çekilir.
 * inv=1 ise NCO evrikliği düzeltmiştir; f_bb doğrudan IF ofsetidir. */
static double bb_to_rf(double f_bb, double lo_hz, double if_hz, int inv)
{
    double if_ofset = inv ? f_bb : -f_bb;       /* inv=0: evrik, işaret ters */
    return lo_hz + if_hz + if_ofset;
}
/* Örnek: f_bb = +5 MHz, inv = 1 → RF = 7.6 GHz + 1.8 GHz + 5 MHz = 9.405 GHz
 *        f_bb = -5 MHz, inv = 0 → aynı RF (9.405 GHz) */
```

Yazılımcı için mixing'in tek kalıcı sonucu bu fonksiyondur: **baseband
frekansından RF'e dönüş**, evriklik ve NCO yönü dahil. PDW'deki RF alanı
({{bolum:25}}) bu fonksiyonla üretilir; INV biti değişir de fonksiyon
güncellenmezse bütün PDW'ler ofsetin iki katı kadar yanlış RF taşır. Bant
genişliğini de doğru say: DDC çıkışında ±150 MHz **tek** bir 300 MHz'lik
kompleks banttır; "150 MHz bant genişliği" diyen biri tek taraflı konuşuyordur,
"300 MHz" diyen çift taraflı. Gürültü tabanı hesabında ({{bolum:4}}) B = 300 MHz
kullanılır.

:::tuzak Spektrum aynalı: sinyal −5 MHz'de
Klasik belirti: LFM darbenin ({{bolum:3}}) chirp yönü ters ölçülür, ya da
bilinen bir ton IF'in üstündeyken baseband'in altında çıkar. İki neden aynı
sonucu verir: Nyquist bölgesi evrikliği düzeltilmemiş (INV = 0 olmalıyken 1
ya da tersi) veya I/Q kabloları/kanalları yer değiştirmiş. Teşhis: tek tonu
IF'in 5 MHz üstüne koy, sonra 10 MHz üstüne; baseband'de −5'ten −10'a
gidiyorsa spektrum evriktir. Çözüm register'dadır (INV) ya da yazılımda
(I ↔ Q, ya da Q'nun işaretini çevir; üçü matematiksel olarak aynıdır). Sakın
"frekansı yazılımda mutlak değer al" ile geçiştirme: chirp yönü ve frekans
ölçümü kalıcı olarak yanlış kalır.
:::

:::tuzak Image'ı decimation'dan önce atmadım
Kaynak kısıtı yüzünden filtre kısa tutulur ya da sıra karıştırılır: mixer →
↓2 → filtre. Toplam frekans kopyası (−1200 MHz'de) ve bant dışı gürültü
decimation'da bandın içine katlanır ({{bolum:8}}'in katlanma haritası, bu kez
sayısal): −1200 MHz, 1200 MSPS'te 0 Hz'e düşer — **tam sinyalin üstüne**.
Belirti: sinyal seviyesi doğru ama SNR beklenenden 3 dB kötü, ya da 0 Hz'de
sinyal olmadan bir bileşen. Kontrol: DDC widget'ında filtre bandını genişletip
"katlanan güç" satırını izle; donanımda snapshot'ı decimation öncesinden al ve
image'ın seviyesine bak. Kural değişmez: **önce filtre, sonra at**
({{bolum:16}}).
:::

:::ozet
- Reel sinyal iki zıt fazördür; $e^{−jω_0n}$ ile çarpmak spektrumu ω₀ kadar sola kaydırır: biri fark frekansına (istenen), diğeri toplam frekansına (image) gider; image'ı filtre atar.
- Referans: 600 MHz katlanmış ton × NCO −600 → 0 Hz + image −1200 MHz; evrik spektrumu düzeltmek için NCO ters döndürülür (INV biti) ya da I/Q takas edilir.
- Mixing gürültüyü kaydırır, gücünü değiştirmez; SNR kazancı filtre + decimation'da gelir.
- Reel → kompleks veri hızı ikiye katlanır (76.8 Gbps) ama bilgi katlanmaz; kompleks fs, fs genişliğinde bant taşır; decimation fazlalığı geri alır (9.6 Gbps).
- Çarpım ADC içinde (az arayüz bandı, az kaynak, az esneklik) ya da FPGA'da (tam bant, kanallaştırıcı, kendi register haritan) yapılır; melez yaygındır, o zaman iki NCO vardır.
- fs/4 NCO'su çarpıcısızdır (1, 0, −1, 0); referans senaryonun 600 MHz'i tam fs/4'tür — 0 DSP, faz kırpma hatası sıfır.
- Hilbert filtresi analitik sinyal üreten alternatiftir; geniş bantta pahalı, dar bant ve anlık frekans ölçümünde kullanışlı.
:::

:::kendini-sina
S: fs = 2400 MSPS, giriş tonu katlanmış hâliyle 700 MHz, NCO −600 MHz. Mixer çıkışında hangi frekanslarda bileşen vardır; 8'e decimation'dan önce filtre bandı en az ne olmalı?
C: Fark: +100 MHz (istenen). Toplam: −700 − 600 = −1300 MHz ≡ +1100 MHz (fs'e göre sarar). Decimation-by-8 sonrası fs = 300 MSPS; ±150 MHz dışındaki her şey katlanır. Filtre ±150 MHz'den dar ve +1100 MHz'de (300 MSPS'te −100 MHz'e katlanır!) yeterince zayıflatıcı olmalı — image, tam olarak sinyalin aynasına düşer.
S: Referans senaryoda NCO neden çarpıcısız gerçeklenebilir, 601 MHz'de neden gerçeklenemez?
C: 600 MHz = 2400/4 = fs/4; e^{−jπn/2} yalnızca 1, −j, −1, +j değerlerini alır, çarpım işaret çevirme ve sıfırlamaya iner. 601 MHz'de NCO dizisi 2400 örnekte bir tekrar eden genel bir sinüs olur; tablo ve gerçek çarpıcı gerekir (SSR-8'de 16 DSP).
S: Mixer çıkışında veri hızı 76.8 Gbps. Bu ADC'nin iki katı; bilgi de iki katına mı çıktı?
C: Hayır. Reel sinyalin negatif frekans yarısı pozitifin aynasıydı; kompleks gösterim bu fazlalığı açıkça taşır. 2400 MSPS kompleks veri 2400 MHz bant temsil eder ama sinyal 1200 MHz'lik bir bantta; decimation-by-2 hızı ADC'ye geri getirir, by-8 ise 300 MHz'lik ilgilenilen banda indirir (9.6 Gbps).
S: Sayısal mixer'da image bastırma neden analog I/Q demodülatörden çok daha iyidir?
C: Analog yolda iki ayrı mixer, hibrit ve filtre genlik/faz hatası taşır (tipik 0.5 dB / 2° → −30 dBc image). Sayısal yolda cos ve sin aynı tablodan okunur, çarpıcılar özdeştir; hata LSB düzeyinde, image ≈ −90 dBc. DC ofset ve LO sızıntısı da yoktur.
:::

:::kopru
Mixer sinyali baseband'e getirdi ama yanında bir image ve tam bant gürültü de
getirdi. İkisini atan ve veri hızını sekizde birine indiren blok filtredir —
ve o filtre yalnızca spektrumu değil, darbenin kenarını da şekillendirir.
Bölüm 16'da FIR, halfband ve CIC'i, decimation'ın alias'ı nasıl geri
katladığını ve referans senaryonun 2400 → 600 → 300 MSPS zincirini açıyoruz.
:::
