# Bölüm 12 — Sabit Noktalı Aritmetik ve DSP Yapıtaşları
::kisim IV — FPGA'da DSP'nin Zemini
::meta onkosul=1,9,11 acar=13,14,15,16,18 blok=arayuz,nco,mixing,filtre rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "Kazancı 6 dB artırdım, sinyal büyüyeceğine spektrum çöp oldu;
neden?" MATLAB'da aynı deney sorunsuz çalışır, çünkü `double` 1e308'e kadar
sayı tutar. FPGA'da ise her sinyal sabit genişlikte bir kelimede yaşar: 14 bit,
16 bit, 18 bit. O kelimenin tavanına çarpan sayı ya duvara yapışır (saturation)
ya da öbür uçtan çıkar (wrap) — ikincisi, tam ölçek pozitif bir tepenin bir anda
tam ölçek negatif olması demektir. Register'a yazdığın her kazanç, eşik ve
katsayı bu kelimelerin içinde yaşar; birim dönüşümünü doğru yapmak için sayının
kaç bit olduğunu, ikili noktanın nerede durduğunu ve ara sonuçların nereye
kadar büyüdüğünü bilmen gerekir. Bu bölüm o zemini döşer: sonraki her sayısal
blok (NCO, mixer, filtre, FFT, CFAR) bu kuralların üstünde kurulur.
:::

## Sezgi: sabit genişlikte bir cetvel

Kayan noktalı sayı, mantis ve üstel taşıyan bir sayıdır: küçük sayıyı da büyük
sayıyı da aynı *bağıl* hassasiyetle tutar, çünkü ondalık nokta "kayar". Sabit
noktalı sayı ise sıradan bir tam sayıdır; ikili noktanın nerede olduğuna yalnızca
**sen** karar verirsin ve donanım bunu hiç bilmez. 16 bitlik bir register'da
duran `0x4000` sayısı, sen "en üst bit işaret, kalan 15 bit kesir" dediğin için
0.5'tir; "hepsi tam sayı" dersen 16 384'tür. Donanım için ikisi de aynı 16
bittir; toplama, çarpma aynı devreyle yapılır.

Cetvel analojisi işe yarar: sabit noktalı kelime, sabit uzunlukta ve sabit
çizgi aralıklı bir cetveldir. Çizgi aralığı (**LSB**) çözünürlüğün, cetvelin
boyu (tam ölçek) ölçebileceğin en büyük değerdir. Cetvelden uzun bir şeyi
ölçemezsin; çizgiler arasına düşen bir uzunluğu da en yakın çizgiye yuvarlarsın.
İki sayıyı çarptığında sonuç için daha uzun **ve** daha ince çizgili bir cetvel
gerekir; onu yine 16 bite sığdıracaksan ya boyundan ya da inceliğinden vermek
zorundasın. Bütün sabit nokta tasarımı bu tek kararın zincir boyunca tekrarıdır.

:::analoji Dolu kova
Kelime genişliği bir kovadır, sinyal içindeki sudur. Kova taşarsa su yere
dökülür — saturation'da dökülen kısım kaybolur ama kova dolu kalır, sinyal
"tavana yapışır". Wrap'te ise kova taşınca **boşalır** ve sıfırdan doldurmaya
başlar; tam ölçek artı bir damla, tam ölçek eksi olur. Kovayı bilerek biraz boş
bırakmak (**headroom**) sabit nokta tasarımının ilk refleksidir; kaç parmak boş
bırakılacağı ise sinyalin tepe/etkin değer oranına bağlıdır.
:::

## Kavram: Q formatı, işaret ve ölçek

İkili noktanın yerini söylemenin standart kısa yolu **Q notasyonudur**: Qm.n,
m tam sayı biti (işaret dahil), n kesir biti; toplam kelime m + n bit. Bu
kılavuzda ADC ve DDC verisi hep **Q1.(B−1)** olarak yorumlanır: en üst bit
işaret, gerisi kesir; değer aralığı −1 … +1 − LSB. Bu seçim sinyal işlemede
yaygındır çünkü tam ölçek "1" olur ve **dBFS** (dB relative to full scale — tam
ölçeğe göre dB, {{bolum:1}}) doğrudan bu 1'e göre tanımlanır. İşaretli sayılar
**ikinin tümleyeni** ile gösterilir: en üst bitin ağırlığı −$2^{m−1}$, gerisi
pozitif. Bu gösterimin güzelliği, toplama ve çıkarmanın işaretsiz tam sayıyla
aynı devrede yapılması ve taşmanın doğal olarak "sarma" (modulo $2^B$) olmasıdır
— {{bolum:14}}'te NCO akümülatörünün tam da bunu istediğini görmüştün.

{{svg:g-120-q-format.svg|Q formatı bit haritası. Üstte 16 bitlik Q1.15 kelimesi: işaret biti ağırlığı −1, kesir bitleri 1/2, 1/4 … 1/32768; en küçük adım LSB = $2^{−15}$ ≈ 3.05·10⁻⁵, aralık −1 … +0.999 97. Ortada aynı 16 bitin Q4.12 yorumu: aralık −8 … +8, LSB 1/4096 — bitler aynı, yalnızca noktanın yeri farklı. Altta ADC'nin 14 bitlik Q1.13 kelimesi ve 16 bitlik yola nasıl yerleştiği: ya sola hizalı (üst bitler doludur, 2 bit ince kesir boş) ya da sağa hizalı (2 bit headroom). İki seçim de meşrudur; hangisinin kullanıldığı belgede yazmalıdır.}}

:::formul id=q-format baslik="Qm.n kelimesinin aralığı ve çözünürlüğü"
f: LSB = 2^{−n}      aralık = [ −2^{m−1} ,  +2^{m−1} − 2^{−n} ]
f: değer = tamsayı · 2^{−n}      dBFS = 20 · log10( frac{|değer|_{tepe}}{2^{m−1}} )
s: m | tam sayı biti (işaret dahil) | bit
s: n | kesir biti | bit
s: LSB | en küçük adım (çözünürlük) | —
s: tamsayı | register'da duran ikinin tümleyeni sayı | —
o: DDC çıkışı Q1.15 (16 bit): LSB = $2^{−15}$ ≈ 3.05·10⁻⁵, aralık −1 … +0.999 97. Register'da `0x4000` = 16 384 · $2^{−15}$ = 0.5 → tepe 0.5 olan bir ton **−6.02 dBFS**.
o: ADC çıkışı Q1.13 (14 bit): LSB = $2^{−13}$ ≈ 1.22·10⁻⁴; {{s:adc.bit}} bit ideal kuantizasyon SNR'ı {{s:turetilmis_beklenen.snr_ideal_14bit_db}} dB ({{bolum:9}}) bu LSB'nin gürültüsüdür.
:::

Aynı bit dizisinin farklı Q yorumları olabileceği için sabit noktalı tasarımda
en çok yapılan hata ölçek hatasıdır: bir bloğun Q1.15 diye ürettiğini sonraki
bloğun Q2.14 sanması sinyali 2 kat küçültür — 6 dB'lik "gizemli" kayıp. Bu
yüzden her sinyal hattının belgesinde üç şey yazmalıdır: bit genişliği, Q
formatı ve tam ölçeğin fiziksel karşılığı (ADC için dBm, {{bolum:9}}).

## Kavram: bit büyümesi

Aritmetik işlem sonucun temsil edilebilir aralığını büyütür; kaç bit büyüdüğü
işleme bağlıdır ve **öngörülebilirdir**. Üç kural bütün zinciri kapsar:

- **Toplama**: iki B bitlik sayının toplamı B + 1 bit ister. K sayının toplamı
  B + ⌈log₂ K⌉ bit.
- **Çarpma**: N × M bitlik çarpım N + M bit üretir (ikinin tümleyeninde, her
  iki işaret biti de tam ölçekte çarpılırsa; pratikte N + M − 1 yeter ama
  −1 × −1 = +1 istisnası yüzünden N + M ayrılır). Q formatı da toplanır:
  Q1.13 × Q1.15 = Q2.28.
- **Akümülatör**: L örneğin ardışık toplamı B + ⌈log₂ L⌉ bit ister. Bir FIR'da
  büyüme, katsayıların mutlak toplamı kadardır: ⌈log₂ ∑|h_k|⌉; CIC'de
  N · log₂ R ({{bolum:16}}).

:::formul id=bit-buyume baslik="Bit büyümesi kuralları"
f: B_{topla} = B + ⌈ log_2 K ⌉      B_{çarp} = N + M      B_{FIR} = B + ⌈ log_2 ∑|h_k| ⌉      B_{CIC} = B + N_{kademe} · log_2 R
s: B | giriş kelime genişliği | bit
s: K | toplanan terim sayısı | —
s: N, M | çarpanların genişlikleri | bit
s: h_k | FIR katsayıları | —
s: N_{kademe}, R | CIC kademe sayısı ve decimation oranı | —
o: Mixer: ADC {{s:adc.bit}} bit × NCO 16 bit → **30 bit** çarpım (Q2.28); 16 bite indirilir.
o: CIC (R = 4, N = 4): 16 + 4 · log₂ 4 = 16 + **8** = 24 bitlik akümülatör; çıkışta yine 16 bite indirilir.
o: Halfband (23 tap): ∑|h_k| ≈ 1.4 → büyüme ⌈log₂ 1.4⌉ = 1 bit; 16 × 18 bit çarpım 34 bit, toplayıcı ağacı 35 bit, çıkışta 16 bit.
:::

{{svg:g-121-bit-buyumesi-zinciri.svg|Referans senaryonun bit genişliği yolculuğu. ADC 14 bit (Q1.13) → NCO ile 16 bitlik çarpım 30 bit → **kesme noktası 1**: yuvarlayarak 16 bite (Q1.15) → CIC R = 4, N = 4 akümülatörü +8 bit = 24 bit → **kesme noktası 2**: 16 bite → kompanzasyon FIR'ı ve halfband 16 × 18 bit çarpım, toplayıcı ağacı 36 bit (∑|h| ≈ 2.5 → +2 bit) → **kesme noktası 3**: 16 bit I, 16 bit Q çıkış. Her kesme noktası bir kuantizasyon gürültüsü kaynağıdır; her birinin altında o noktadaki gürültü seviyesi (dBFS) ve seçilen yuvarlama/taşma davranışı yazılıdır. Kırmızı: kesilen bitler.|kaydir}}

Şekildeki üç kesme noktası tesadüf değil: her çarpma ve her akümülatör sonrası
kelime yeniden **kesilir** (requantize), çünkü aksi hâlde 30, 38, 46 bit
genişliğinde yollar taşırsın. Kesme kararının iki bileşeni vardır: alt bitleri
nasıl atacağın (yuvarlama) ve üst bitlerin sığmadığı durumda ne yapacağın
(taşma). İkisi de bir sonraki iki başlığın konusu.

## Kavram: truncation ve rounding — DC bias

Alt bitleri atmanın en ucuz yolu **truncation** (kesme, `floor`): bitleri
görmezden gelirsin, donanım maliyeti sıfırdır. Bedeli sistematiktir: ikinin
tümleyeninde `floor` her zaman **aşağı** yuvarlar, dolayısıyla hata 0 ile
−1 LSB arasında, ortalaması **−0.5 LSB** olan bir sinyaldir. Bu ortalama bir
**DC bileşenidir**. Tek bir kesme noktasında −0.5 LSB önemsiz görünür (16 bit
için ≈ −96 dBFS); ama kompleks bir zincirde I ve Q'da aynı yönde biriken DC,
baseband'de 0 Hz'de bir çivi olur — ve 0 Hz baseband, RF'te **NCO frekansının
tam üstü** demektir ({{bolum:15}}). CIC gibi 24 bitlik akümülatörü olan bir
blokta truncation önce büyütülür sonra kesilirse çivi kolayca −60 dBFS'e
tırmanır.

**Rounding** (yuvarlama) bu bias'ı kaldırır: atılan bitlerin en üstü 1 ise
1 eklersin (`round half up`). Maliyet, kesme noktasında bir toplayıcıdır —
DSP slice'ın içinde çoğu zaman bedava. Yalnız bir incelik kalır: tam 0.5'ler
hep yukarı gider, bu da +LSB/$2^{k+1}$'lik çok küçük bir bias bırakır (k atılan
bit sayısı). Titiz tasarımlar **convergent rounding** (round half to even)
kullanır; HDL Coder ve Vitis DSP IP'lerinde seçenek olarak vardır. Pratik
kural: kesme noktalarında yuvarla, akümülatör içinde kesme yapma, DC'ye duyarlı
yollarda (kompleks baseband, FFT girişi) convergent rounding düşün.

:::formul id=kesme-gurultu baslik="Kesme noktasının gürültüsü ve bias'ı"
f: σ_q^2 = frac{LSB^2}{12}      N_q = −( 6.02 · B + 1.76 )  dBFS  (tam ölçek sinüse göre)
f: μ_{trunc} = −frac{LSB}{2}      μ_{round} ≈ 0
s: B | kesme sonrası kelime genişliği | bit
s: σ_q | eklenen kuantizasyon gürültüsünün etkin değeri | —
s: μ | hatanın ortalaması (DC bias) | —
o: 16 bite yuvarlama: N_q = −(6.02 · 16 + 1.76) = **−98.1 dBFS**; ADC'nin kendi 14 bitlik gürültüsü −86.0 dBFS'in 12 dB altında kalır → kesme noktası zincirin SNR'ını bozmaz.
o: 16 bite truncation: ek olarak DC = −0.5 LSB = −1.5·10⁻⁵ → **−96.3 dBFS** çivi, 0 Hz'de. Tek başına zararsız; üç kesme noktası ve CIC kazancıyla birikince değil.
:::

## Kavram: saturation ve wrap-around

Üst tarafta sığmama olduğunda iki davranış vardır. **Wrap-around**: sayı modulo
$2^B$ sarar; +0.999 97'ye bir LSB eklersen −1 olur. **Saturation**: sonuç en
yakın uca yapıştırılır, +1 − LSB'de kalır. Wrap bedavadır (toplayıcının doğal
davranışı), saturation bir karşılaştırıcı ve çoklayıcı ister. Ama davranış
farkı dramatiktir: saturation sinyali kırpar ve harmonik üretir — kötü ama
tanıdık ve sınırlı bir bozulma. Wrap ise dalga şeklinin tepesini **tam ölçek
genlikli bir sıçramaya** çevirir; spektrumda geniş bantlı bir patlama olur,
tespit eşiği her yerde aşılır, ölçülen PW ve frekans anlamsızlaşır.

{{svg:g-122-wrap-vs-saturate.svg|Wrap ve saturation, aynı sinyal üzerinde (hesaplanmış). Solda zaman: +2.5 dBFS'lik bir tonun (tepe 1.33) 16 bit Q1.15'e sığdırılması. Saturation (altın) tepeleri düz keser; wrap (kırmızı) tepe her tam ölçeği aştığında sinyali −1'e fırlatır. Sağda spektrum: ideal ton (mavi), saturation tek harmoniklerle −24 dBFS (≈ −19 dBc) civarı bir bozulma, wrap ise tüm bandı ≈ −58 dBFS'lik bir tabanla doldurur ve en büyük bileşenleri −15 dBFS'e çıkar. −70 dBFS'lik örnek tespit eşiği (kesikli) wrap durumunda her bin'de aşılır.}}

Kural açık: **veri yolunda saturation, faz akümülatöründe wrap.** Faz için
sarma çalışma ilkesidir ({{bolum:14}}); genlik için felakettir. Kazanç
kontrolü, eşik toplama, CFAR ortalaması, FFT kelebeği — hepsi doyurmalı
toplayıcı ister. FPGA araçlarında bu bir sentez özniteliği ya da IP seçeneğidir
("saturate on overflow"); elle yazılan RTL'de ise unutulması en kolay iki
satırdır. Bir de "**sticky overflow bayrağı**" ekle: doyurma gerçekleştiğinde
set olan ve PS okuyana kadar kalan bir bit. Sahada "spektrum çöp oldu"nun ilk
kontrolü bu bayraktır.

:::widget id=w10 ad="Sabit nokta oyun alanı"
- **Referans senaryo** preset'inde (−6 dBFS ton, 16 bit, yuvarlama, saturation) ölçülen SNR'ın (sinyale göre) 6.02·16 + 1.76 − 6 dB headroom ≈ 92 dB olduğunu, hata sinyalinin ±0.5 LSB içinde kaldığını ve DC bias satırının ≈ 0 olduğunu gör. Bit sayısını 8'e indir: SNR ≈ 44 dB'ye düşsün, hata sinyali (LSB cinsinden aynı, mutlak olarak) 256 kat büyüsün.
- Yuvarlama modunu **truncation** yap: hata sinyali 0 … −1 LSB arasına kaysın, "DC bias" satırı −0.5 LSB'yi göstersin ve spektrumda 0 Hz'de bir çivi belirsin (16 bitte ≈ −96 dBFS; 8 bitte ≈ −48 dBFS).
- Giriş seviyesini **+2 dBFS**'e çıkar, taşma modunu saturation'da bırak: tepeler kırpılsın, tek harmonikler belirsin, "taşan örnek" sayacı 1700 civarına çıksın; SNR ≈ 20 dB'ye düşsün ama ana ton hâlâ en güçlü bileşen kalsın.
- Aynı seviyede **wrap felaketi** preset'ine geç: zaman çiziminde tepeler −1'e fırlasın, spektrumun tamamı −60 dBFS'in üstüne çıksın, SNR 10 dB'nin altına insin. Seviyeyi −0.5 dBFS'e çek: bir anda temizlensin — 2.5 dB'lik kazanç farkı çalışan bir almaçla çöp arasındaki mesafedir.
:::

## Kavram: headroom, dBFS ve ölçek bütçesi

Sabit noktalı zinciri tasarlamak, her kademede sinyalin tam ölçeğe ne kadar
yaklaşacağını planlamaktır. İki uç arasında yaşarsın: çok yukarıda taşma, çok
aşağıda kuantizasyon gürültüsü. Aradaki payın adı **headroom**: tepe değerin
tam ölçeğe uzaklığı, dB cinsinden. Tek bir CW ton için tepe/etkin değer oranı
(crest factor) 3 dB'dir; Gauss gürültüsü için tepe pratikte 4σ (12 dB) alınır;
iki eşit ton üst üste geldiğinde tepe 6 dB büyür. EH almacında en kötü durum
**iki güçlü eşzamanlı emiter + gürültüdür**: bu yüzden ADC'nin tam ölçeği
tek tonda −6 … −12 dBFS'e ayarlanır ve bu pay zincir boyunca korunur.

Ölçek bütçesi bir tablodur: her blok için giriş tam ölçeği, bloğun kazancı
(FIR'da ∑|h_k|, CIC'de $R^N$, mixer'da NCO genliği), çıkış tam ölçeği ve
kesme sonrası yeniden ölçek. Referans senaryo için kısaltılmış hali:

| Kademe | Giriş | Kazanç (tepe) | Ham çıkış | Kesme → | Not |
|---|---|---|---|---|---|
| ADC | — | — | 14 bit Q1.13 | — | tam ölçek {{s:adc.tam_olcek_dbm}} dBm; ton −6 dBFS hedef |
| Mixer (× NCO 16 bit, genlik 1 − LSB) | 14 bit | 1.0 | 30 bit Q2.28 | 16 bit Q1.15, round, sat | kompleks; I ve Q ayrı |
| CIC R = 4, N = 4 | 16 bit | $4^4$ = 256 = 8 bit | 24 bit | 16 bit, round | kazanç tam $2^8$ → sağa 8 kaydırma, bit kaybı yok |
| Kompanzasyon FIR (31 tap) | 16 bit | ∑|h| ≈ 2.5 | 36 bit | 16 bit, round, sat | +2 bit büyüme; katsayı 18 bit Q2.16 |
| Halfband (23 tap) | 16 bit | ∑|h| ≈ 1.4 | 35 bit | 16 bit Q1.15, round, sat | çıkış: DDC pasaportu |

Tablonun anlattığı: kademeler arası kazanç 1'e yakın tutulur, büyümeler
kaydırma ile geri alınır ve her kesmede yuvarlama + doyurma seçilir. CIC'in
kazancının tam ikinin kuvveti olması (R ve N'nin böyle seçilmesi) tesadüf
değildir: bölme yerine kaydırma yeter.

## FPGA'da nasıl gerçeklenir

### DSP slice, pipeline, kaynak türleri

FPGA'nın aritmetik atomu **DSP slice**'tır (AMD'de DSP48E2 / DSP58, Intel'de
DSP block): bir ön toplayıcı, bir çarpıcı (DSP48E2'de 27 × 18 bit), 48 bitlik
bir akümülatör/ALU ve aralarında pipeline register'ları. Bir MAC (çarp-topla)
işlemi tek slice'ta, tam pipeline ile fabric saatinde (tipik 300–500 MHz)
çalışır. Bir 16 bit × 18 bit çarpım tek slice, 24 × 24 iki slice'tır; kelime
genişliği bu sınırları aşınca kaynak **katlanarak** artar — 16 biti 18 bitin
altında tutmanın nedeni budur.

Kaynak türleri dört tanedir ve her biri farklı işe yarar: **LUT** (mantık,
küçük toplayıcı, çoklayıcı), **FF** (register, pipeline), **BRAM** (tablolar,
FIFO, gecikme hattı; 36 kb bloklar), **DSP** (çarp-topla). Bir tasarım hangi
kaynakta sıkıştıysa orada pahalanır: 128 kanallı bir kanallaştırıcı DSP'de,
uzun bir NCO tablosu BRAM'de, karmaşık bir FSM LUT'ta sıkışır.

**Pipeline** ve **latency / throughput** ayrımı yazılımcı için en yabancı
kavramdır. Fabric'te bir işlemin sonucunu aynı saatte kullanmak yerine araya
register koyarsın; her register bir saat gecikme (latency) ekler ama saat
hızını (throughput) yükseltir. 63 tap'lik bir FIR'ın latency'si 20 saat
olabilir; bu her örneğin 20 saat sonra çıktığı anlamına gelir, saniyede işlenen
örnek sayısı değişmez. Sistem düzeyinde latency yalnızca **TOA ofseti** olarak
karşına çıkar ({{bolum:25}}): sabit ve bilinir, kalibre edilir.

### Akış arayüzü: AXI-Stream ve backpressure

Bloklar arası veri yolu neredeyse her yerde **AXI-Stream**'dir: `tdata`
(örnek), `tvalid` (bu saatte veri var), `tready` (alıcı kabul ediyor),
`tlast` (paket/çerçeve sonu), isteğe bağlı `tuser`. Aktarım yalnızca
`tvalid && tready` olduğu saatte gerçekleşir. Yazılımcının bildiği FIFO/DMA
dünyasında alıcı `tready`'yi düşürerek göndereni bekletir; buna
**backpressure** denir.

Gerçek zamanlı almaç zincirinde bunun bir istisnası vardır: **ADC beklemez.**
Her saat yeni örnek gelir; `tready` düşerse örnek kaybolur, kaybolan örnek
tekrar gelmez. Bu yüzden ADC'den zarf dedektörüne kadar olan hat **her saatte
bir örnek** ilkesiyle tasarlanır: tüm bloklar aynı fs'te, `tready` ya hiç
yoktur ya da hep 1'dir. Backpressure ancak **olay tabanlı** veriye geçince
(PDW'ler, snapshot'lar) meşrudur; orada FIFO'lar ve taşma politikası devreye
girer: FIFO dolunca en eskiyi mi atarsın, en yeniyi mi, yoksa bir "overflow"
bayrağı ile PS'i uyarır mısın? Referans senaryoda PDW FIFO'su en yeniyi düşürür
ve `PDW_OVF` bayrağını set eder ({{bolum:26}}).

### SSR: GSPS veriyi birkaç yüz MHz fabric'te işlemek

ADC saniyede {{s:adc.fs_msps}} milyon örnek üretir; fabric 300 MHz'de
çalışır. Çözüm, her saatte **birden çok örneği yan yana** taşımaktır:
**SSR** (Super-Sample Rate). SSR-8'de bir AXI-Stream kelimesi 8 ardışık örnek
taşır (8 × 16 = 128 bit), saat 2400/8 = 300 MHz'dir. Her DSP bloğu bunun
farkındadır: SSR FIR 8 örneği paralel üretir, SSR NCO tek akümülatörle 8 faz
çıkarır ({{bolum:14}}), decimation-by-8 ise tam SSR-8'de "sekiz girişten
birini seç" kadar basitleşir.

Bunun bedeli **kaynak çarpanıdır**: 63 tap'lik bir FIR tek örnek/saat'te 63
(simetriyle 32) çarpıcı ister; SSR-8'de 8 kat. **Polyphase** yapı
({{bolum:16}}) bu çarpanı decimation oranına bölerek geri kazanır: decimation
yapılacaksa atılacak örnekleri hesaplamak anlamsızdır, filtre R alt-filtreye
bölünür ve her biri çıkış hızında çalışır. SSR ve polyphase aynı fikrin iki
yüzüdür: örnek hızı ile saat hızını birbirinden ayırmak.

:::formul id=ssr baslik="SSR çarpanı ve veri yolu genişliği"
f: SSR = ⌈ frac{f_s}{f_{fabric}} ⌉      W_{tdata} = SSR · B      R_{veri} = f_s · B
s: f_s | örnek hızı | Hz
s: f_{fabric} | FPGA mantık saati | Hz
s: B | örnek genişliği (kompleks için 2 × bit) | bit
s: W_{tdata} | AXI-Stream veri genişliği | bit
o: ADC yolu: 2400 / 300 = **8** örnek/saat; 16 bit paketli örnekle tdata = 128 bit; veri hızı 2400 · 16 = **{{s:adc.veri_hizi_gbps_16bit_paket}} Gbps**.
o: DDC çıkışı: fs = {{s:ddc.cikis_fs_msps}} MSPS → SSR = 1; tdata = 32 bit (16 I + 16 Q); veri hızı **{{s:ddc.cikis_veri_hizi_gbps}} Gbps**.
:::

:::uc-goz
::rf::
RF tasarımcı için sabit nokta, ADC'nin tam ölçeğinden başlayan bir **seviye
planıdır**: dBm cinsinden düşünülen seviye diyagramı ({{bolum:5}}) ADC'de dBFS'e
çevrilir ve sayısal zincirde aynı mantıkla devam eder. Analog kazanç dağıtımında
"hiçbir kademe sıkışmasın, gürültü tabanı hiçbir kademede baskın çıkmasın"
kuralı neyse, sayısal ölçek bütçesi de odur. Fark: sayısal kademelerde "sıkışma"
keskindir (1 LSB üstü taşma), kayıp ise gürültü değil doğrudan kesme
gürültüsüdür. RF'te 1 dB compression noktası neyse, sayısalda tam ölçek odur.
::fpga::
Sayısal tasarımcı için üç somut karar: (1) her hattın Q formatı ve genişliği
(16 bit veri, 18 bit katsayı, DSP48'in 27 × 18 sınırına göre); (2) her kesme
noktasında yuvarlama + doyurma (RTL'de `$signed` aritmetik, `+ (1 << (k−1))`
ile yuvarlama, üst bitlerin XOR'u ile taşma tespiti); (3) SSR faktörü ve
pipeline derinliği. Kaynak kestirimi: SSR-8, 63 tap simetrik FIR ≈ 256 DSP;
CIC çarpıcısız (yalnızca toplayıcı, LUT/FF); NCO 1–8 BRAM. Timing kapanmıyorsa
önce pipeline ekle, sonra kelime genişliğini sorgula.
::yazilim::
Yazılımcı sabit noktayı **register'larda** görür: eşik register'ı Q1.15 mi,
Q8.8 mi; katsayı register'ı 18 bit Q2.16 mı; kazanç register'ı 4.12 mi?
Belgede "16 bit" yazması yetmez; ikili noktanın yeri olmadan sayı anlamsızdır.
Dönüşüm hep aynı kalıptır: `reg = round(deger * 2^n)`, doyurma ile. Geri
okurken işaret genişletmeyi (`int16_t` cast) unutma. Taşma bayraklarını
(`OVF` sticky bitleri) telemetriye al: spektrumun bozulduğu ilk anda kim
taştı sorusunun cevabı oradadır.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>
#include <math.h>

/* Kayan noktalı bir değeri Qm.n sabit noktalı register kelimesine çevir.
 * n: kesir biti, bits: toplam kelime genişliği (işaret dahil, <= 32).
 * Yuvarlama: round-half-away-from-zero; taşma: saturation. */
static int32_t q_encode(double deger, int n, int bits, int *doydu)
{
    double olcekli = deger * ldexp(1.0, n);            /* deger * 2^n */
    double maks    =  ldexp(1.0, bits - 1) - 1.0;      /* +2^(bits-1) - 1 */
    double min     = -ldexp(1.0, bits - 1);            /* -2^(bits-1)      */
    long long r    = llround(olcekli);
    if (doydu) *doydu = 0;
    if (r > (long long)maks) { r = (long long)maks; if (doydu) *doydu = 1; }
    if (r < (long long)min)  { r = (long long)min;  if (doydu) *doydu = 1; }
    return (int32_t)r;
}

/* Register'dan okunan Qm.n kelimeyi geri çevir (işaret genişletme dahil). */
static double q_decode(uint32_t ham, int n, int bits)
{
    int32_t v = (int32_t)(ham << (32 - bits)) >> (32 - bits);  /* işaret genişlet */
    return (double)v * ldexp(1.0, -n);
}

/* Örnek: -20 dBFS eşik, Q1.15 register:
 *   q_encode(pow(10, -20.0/20), 15, 16, NULL) == 3277  (0x0CCD)  */
```

İki tuzak bu kodun dışında kalır ama aynı ölçekten doğar. Birincisi
**dBFS'in hangi tam ölçeğe göre** olduğudur: 14 bitlik ADC kelimesinin tam
ölçeği ile 16 bitlik DDC çıkışının tam ölçeği aynı fiziksel seviye olabilir de
olmayabilir de (şekil 1'deki sola/sağa hizalama). Sola hizalıysa 14 bitlik
tam ölçek = 16 bitlik tam ölçek; sağa hizalıysa 14 bit tam ölçek, 16 bit
dünyasında −12 dBFS'tir. İkincisi **güç değerleri**: zarf dedektörü I² + Q²
üretir ({{bolum:22}}), yani Q1.15 × Q1.15 = Q2.30 ve tam ölçek güç 1.0'dır;
güç domenindeki eşik dBFS'e çevrilirken 10·log10, genlik domenindeki 20·log10
kullanır. Register belgesi "eşik, dBFS" yazıyorsa hangisi olduğunu sor.

:::tuzak "Kazancı 6 dB artırdım, her şey bozuldu"
Klasik senaryo: zayıf sinyalleri görmek için sayısal kazanç register'ı
2 katına çıkarılır. Güçlü emiter geldiğinde mixer sonrası kesme noktasında
taşma olur; blok wrap yapacak biçimde sentezlenmişse (varsayılan davranış!)
spektrum tüm bantta yükselir, CFAR yüzlerce yanlış alarm üretir ve zayıf
sinyal zaten görünmez olur. Belirti: sorun yalnızca güçlü sinyal varken
çıkar ve kazancı geri alınca kaybolur. Kontrol: overflow sticky bayrakları;
yoksa snapshot alıp ({{bolum:13}}) tam ölçeğe yakın örneklerin işaret
değiştirip değiştirmediğine bak. Çözüm: doyurma + headroom; kazanç
gerçekten gerekiyorsa decimation sonrasında, bit kazandıktan sonra uygula.
:::

:::tuzak Truncation'ın DC'si NCO frekansında spur olur
Bit-true model MATLAB'da `floor` ile yazılmış, RTL de aynı. Her şey bit-exact
eşleşiyor, ama spektrumda tam NCO frekansında ({{s:ddc.nco_mhz}} MHz) küçük bir
çivi var ve sinyal olmayınca da kaybolmuyor. Nedeni, I ve Q yollarında
kesme noktalarının bıraktığı −0.5 LSB'lik DC'nin baseband'de 0 Hz'de
toplanması; 0 Hz baseband = RF'te NCO frekansıdır. CIC'in 256 katlık
kazancından **önce** yapılan bir truncation, DC'yi 48 dB büyütür. Teşhis: NCO
frekansını 1 MHz kaydır; çivi spektrumda yerinde kalıyorsa (baseband 0 Hz)
DC'dir, sinyalle birlikte kayıyorsa gerçek sinyaldir. Çözüm: yuvarlama
(tercihen convergent), kesmeyi kazançtan sonra yapmak, gerekirse çıkışta DC
giderici.
:::

:::tuzak "16 bit" yazan register'ın ikili noktası
Register haritasında `THRESH[15:0]` yazar, birim yazmaz. Bir yazılımcı bunu
tam sayı genlik sanıp 1000 yazar (Q1.15'te 0.03 → −30 dBFS); diğeri Q8.8
sanıp 4 yazar (Q1.15'te 0.000 12 → −78 dBFS, her şey tespit edilir). İkisi de
"çalışıyor" ama farklı almaçlar gibi davranır. Çözüm belge disiplinidir: her
register alanı için genişlik, Q formatı, birim ve örnek değer (bu kılavuzda
{{bolum:30}}'daki kurgusal haritanın yaptığı gibi).
:::

:::ozet
- Sabit noktalı sayı, ikili noktanın yerini **senin** bildiğin bir tam sayıdır; Qm.n: m tam (işaret dahil), n kesir; LSB = $2^{−n}$; veri yolları bu kılavuzda Q1.(B−1) ve dBFS tam ölçek 1'e göre.
- Bit büyümesi öngörülebilir: toplama +1 (K terim: +log₂K), çarpma N + M, akümülatör +log₂L; FIR +log₂∑|h|, CIC +N·log₂R. Referans zincir: 14 × 16 → 30 → 16; CIC +8 → 24 → 16.
- Truncation −0.5 LSB DC bias bırakır; rounding kaldırır. Kesme noktalarında yuvarla, kesmeyi kazançtan sonra yap.
- Veri yolunda **saturation**, faz akümülatöründe **wrap**; wrap veri yolunda felakettir (tam ölçek sıçraması, geniş bant patlama). Sticky overflow bayrağı ekle.
- Headroom: tek ton için 3 dB, gürültü için ~12 dB, iki eşit ton için +6 dB; ölçek bütçesi tablosu her kademede giriş/kazanç/çıkış/kesme yazar.
- DSP slice = çarp-topla (27 × 18, 48 bit akümülatör); pipeline latency ekler, throughput'u korur; latency sabit TOA ofsetidir.
- Gerçek zamanlı hatta backpressure yoktur: her saatte bir örnek; SSR = fs / f_fabric (2400/300 = 8) örnek yan yana; polyphase SSR'ın decimation'lı ikizidir.
:::

:::kendini-sina
S: Q1.15 bir register'da 0x2000 duruyor. Değeri ve dBFS karşılığı nedir? Aynı bitler Q4.12 yorumlanırsa?
C: 0x2000 = 8192; Q1.15'te 8192 · $2^{−15}$ = 0.25 → 20·log10(0.25) = −12.04 dBFS (tepe genlik olarak). Q4.12'de 8192 · $2^{−12}$ = 2.0. Aynı bitler, farklı ölçek — belge olmadan sayı anlamsızdır.
S: 14 bitlik örneği 16 bitlik NCO ile çarpıp 16 bite indiriyorsun. Kaç bit atılır, atılan bitlerin gürültüsü ADC gürültüsüne göre nerededir?
C: Çarpım 30 bit; 16'ya inince 14 bit atılır. 16 bitlik yuvarlamanın gürültüsü −98.1 dBFS, ADC'nin 14 bitlik gürültüsü −86.0 dBFS; kesme 12 dB aşağıda kalır, toplam SNR'ı 0.3 dB'den az bozar. Truncation seçilseydi ayrıca −96 dBFS'lik bir DC gelirdi.
S: CIC R = 4, N = 4 çıkışını kompanzasyon FIR'ına vermeden önce 24 bitten 16 bite indirdin ama kaydırma miktarını 7 yaptın (8 yerine). Ne olur?
C: Çıkış 2 kat (6 dB) büyük olur; tam ölçek girişte kelime taşar. Doyurma varsa güçlü sinyaller kırpılır, wrap varsa spektrum patlar. Bit-true modelde de aynı hata yapılmışsa karşılaştırma "geçer" — bit-exact eşleşme doğruluk garantisi değildir ({{bolum:13}}).
S: 300 MHz fabric'te 2400 MSPS veriyi işleyen 63 tap simetrik bir FIR kaç DSP slice ister; decimation-by-8 ile polyphase yapılırsa?
C: SSR-8 → 8 paralel çıkış × 32 çarpıcı (simetri) = 256 DSP. Çıkış hızı 300 MSPS olacaksa polyphase yapı 8 alt-filtreye böler ve yalnızca gereken çıkışları hesaplar: 63 ≈ 64 çarpıcı; simetri kısmen kullanılırsa daha az. Aynı filtre, 4 kat az kaynak.
:::

:::kopru
Artık sayının kaç bit olduğunu, nereye kadar büyüdüğünü ve nerede kesildiğini
biliyorsun. Ama bu kararları kim, ne zaman verir? Algoritma MATLAB'da kayan
noktayla doğar, sabit noktaya indirilir ve bir noktada RTL olur; iki dünyanın
aynı sayıyı ürettiğini kanıtlamak da ayrı bir zanaattır. Bölüm 13 bu yolculuğu,
rolleri ve bit-true doğrulama döngüsünü anlatır.
:::
