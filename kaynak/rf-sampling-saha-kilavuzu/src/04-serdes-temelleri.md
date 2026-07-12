# Bölüm 4 — SERDES Temelleri

{{sec:3}}'ün sonunda 47 Gb/s'lik yükü 4 seri lane'e bindirdik ve "tek çiftin
içinde skew yoktur" diye rahatladık. Ama dürüst olalım: bir çift bakır iz
üzerinde saniyede 12 milyar bit taşımak, fizikle pazarlıktır. Bu bölüm o
pazarlığın şartlarını anlatır — SERDES (serializer/deserializer) denen
makinenin içini. Bunu neden bilmen gerekiyor? Çünkü {{sec:14}}'te GT
transceiver register'larını sen konfigüre edeceksin, {{sec:16}}'da eye scan
sonuçlarına bakıp "kanal mı kötü, konfigürasyon mu yanlış" kararını sen
vereceksin. SERDES'i kara kutu bırakan yazılımcı, debug'da körleşir.

::: ogren
- Seri hattın fiziği: diferansiyel CML, empedans, AC kuplaj
- Embedded clock fikri ve CDR'ın nasıl çalıştığı
- Encoding'in (8b/10b, 64b/66b) hangi problemleri çözdüğü
- Kanal kayıpları ve eşitleme: pre-emphasis, CTLE, DFE
- Eye diagram ve BER: link sağlığının iki dili
- FPGA GT anatomisi: quad, kanal, refclk, PLL'ler
:::

## Seri hattın fiziği

**Diferansiyel sinyalleşme.** Gb/s hızlarında tek uçlu (single-ended) sinyal
yaşayamaz: zemin gürültüsü, crosstalk ve EMI her şeyi yer. Bu yüzden her
lane bir **çifttir**: aynı bilgi, biri pozitif biri negatif iki kopya halinde
gider; alıcı *farkı* okur. Ortak moda binen gürültü iki kopyayı birden aynı
yönde iter ve farkta yok olur. Bedeli pin sayısının ikilenmesi — {{sec:3}}'te
"4 lane = 8 pin" dememizin sebebi.

**CML sürücüler.** Bu çiftleri süren devre ailesi tipik olarak CML
(current-mode logic — akım modlu lojik): sabit bir akım kaynağı, iki koldan
birine yönlendirilir; hız, gerilim sallamak yerine akım yönlendirmekten
gelir. Hatlar karakteristik empedansla (çift başına nominal 100 Ω
diferansiyel) sonlandırılır; empedans süreksizliği = yansıma = kapanan göz
(birazdan geleceğiz).

**AC kuplaj.** TX ile RX arasına genellikle seri kondansatörler konur:
iki tarafın DC ortak-mod gerilimlerini birbirinden bağımsızlaştırır (farklı
üreticilerin çipleri farklı DC seviyelerde çalışır). Ama kondansatör DC
geçirmez — sinyalin **uzun vadeli ortalaması sıfır olmak zorundadır**. Bu
masum devre kararı, birazdan encoding'in varlık sebeplerinden biri olacak.
Şimdilik aklında tut: *AC kuplaj → DC balance şartı*.

## Embedded clock ve CDR

Paralel bus'ta veri hatlarının yanında bir clock hattı gider; alıcı, clock
kenarında veriyi örnekler. 12 Gb/s'de bu intihar olur: clock ile veri
arasındaki en ufak yol farkı bit periyodunun (≈82 ps!) önemli kısmını yer.
Seri linkin cevabı radikaldir: **clock hattını tamamen at**. Alıcı, clock'u
verinin kendisinden çıkarır — veri akışındaki 0→1 ve 1→0 geçişlerinin
zamanlaması, clock'un tüm bilgisini taşır.

Bunu yapan blok **CDR**'dır (clock and data recovery — clock ve veri geri
kazanımı): bir faz kilitli döngü (PLL benzeri yapı), yerel osilatörünü gelen
geçişlere hizalar ve veriyi göz açıklığının ortasında örnekler. CDR'ın iki
zaafı var ve ikisi de senin debug hayatına girecek:

1. **Geçişe muhtaçtır.** Uzun 000000 veya 111111 dizilerinde hizalayacak
   kenar bulamaz ve kaymaya başlar. Yani veri akışında geçiş yoğunluğu
   (transition density) garanti edilmelidir — encoding sebebi #2.
2. **Kilitlenmesi zaman alır.** Link ilk kalktığında CDR'ın frekans ve faz
   yakalaması gerekir; {{sec:6}}'daki CGS'in "anlamsız ama geçiş dolu
   karakter yağmuru" göndermesinin bir nedeni CDR'a kilitlenecek malzeme
   vermektir.

::: not
CDR bit'leri bulur ama **bit'lerin nerede başladığını bilmez**: akışta
"buradan itibaren say" diyen bir işaret gerekir. 8b/10b dünyasında bu işi
comma karakteri (K28.5), 64b/66b dünyasında sync header deseni yapar —
{{sec:6}} ve {{sec:7}}'nin açılış konuları.
:::

## Encoding: bit'lere çeki düzen

Ham veriyi olduğu gibi hatta basamazsın; üç şart koştuk bile: DC balance
(AC kuplaj), geçiş yoğunluğu (CDR) ve hizalama işaretleri (bit sınırları).
Line encoding, ham bit'leri bu şartları garanti eden bir forma çevirir.
JESD dünyasında iki nesil:

**8b/10b** (JESD204B): her 8-bit oktet, 10-bit'lik bir koda çevrilir.
Kod tablosu öyle kurulmuştur ki her kod sözcüğünde yeterli geçiş vardır ve
**running disparity** mekanizması (1'lerle 0'ların koşan sayımı) uzun vadeli
DC dengeyi tutar. Ayrıca veri uzayının dışında **K-karakterleri** denen
özel kodlar vardır (K28.5 gibi) — "bu bir kontrol işaretidir" diyebilmek,
JESD204B'nin CGS/ILAS mekaniğinin temelidir. Bedel: her 8 bit için 10 bit
hat kapasitesi; hat bant genişliğinin **%20'si** kodlamaya gider.

**64b/66b** (JESD204C): 64 bit'lik bloğun önüne 2 bit'lik sync header
eklenir; 66 bit'te yalnız 2 bit ek yük → **%3.1**. DC balance ve geçiş
yoğunluğu, kod tablosuyla değil **scrambler** ile (veriyi bilinen bir
polinomla karıştırarak) istatistiksel olarak sağlanır; hizalamayı sync
header'ların 66 bit'te bir tekrarlayan deseni verir. K-karakteri diye bir
şey artık yoktur — bu yokluğun sonuçlarını {{sec:7}}'de göreceğiz.

| | 8b/10b | 64b/66b |
|---|---|---|
| Ek yük | hat kapasitesinin %20'si | %3.1 |
| DC/geçiş garantisi | kod tablosu (deterministik) | scrambler (istatistiksel) |
| Hizalama | comma (K28.5) | sync header deseni |
| Kontrol işaretleri | K-karakterleri | yok (yan kanallar üstlenir) |
| Kullanım | JESD204/A/B | JESD204C |

12.5 Gb/s hat ile 8b/10b'de 10 Gb/s payload taşırsın; 64b/66b'de aynı
payload ~10.3 Gb/s hatla taşınır. Lane hızları GT sınırlarına dayandığında
bu %17'lik fark, lane sayısı veya güç olarak faturaya yansır — 204C'nin
varlık sebeplerinden biri.

## Kanal: bakırın intikamı

TX'ten çıkan keskin kare dalga, RX'e yumuşamış, bulanık bir tepecik olarak
varır. Kanal (PCB izi + via'lar + konnektörler + kablolar) bir alçak geçiren
filtredir: yüksek frekansları frekansla artan oranda yutar (skin effect,
dielektrik kaybı). Sonuç **ISI**'dır (inter-symbol interference —
semboller arası girişim): bir bit'in enerjisi komşu bit'lerin zaman
dilimlerine taşar; hızlı 1-0-1-0 desenleri, yavaş 1-1-1-0 desenlerinden
daha çok zayıflar.

Çare, kanalın tersini elektronikle uygulamak — **eşitleme (equalization)**:

- **TX tarafında — pre-emphasis / de-emphasis**: geçiş içeren bit'leri
  bilerek daha güçlü (veya geçişsizleri daha zayıf) sür; kanalın yüksek
  frekans kaybını önceden telafi et.
- **RX tarafında — CTLE** (continuous-time linear equalizer): yüksek
  frekansları yükselten analog filtre. Kaba ama etkili ilk savunma.
- **RX tarafında — DFE** (decision feedback equalizer): son kararlaştırılan
  bit'lerin ISI katkısını hesaplayıp gelen sinyalden çıkaran uyarlanır
  yapı. İnce işçilik; yüksek kayıplı kanalların kurtarıcısı.

**Yazılıma dokunduğu yer:** bu blokların hepsi GT register'larıyla ayarlanır.
Modern transceiver'larda adaptasyon donanımı çoğunu kendi bulur, ama
başlangıç ayarları, adaptasyonun açık/kapalı olması ve link kalitesi
raporları senin init kodunun ve debug oturumlarının parçasıdır. "Kartın
birinde link geliyor, diğerinde gelmiyor" vakalarının bir kısmı, iki kartın
kanal kaybı farkının eşitleyici ayarlarıyla örtüşmemesidir ({{sec:16}}).

## Eye diagram ve BER: linkin iki dili

Link kalitesi iki dilde konuşulur:

**Eye diagram (göz diyagramı)**: sinyalin ardışık bit periyotlarını üst üste
bindirilmiş hali. Açık bir "göz", RX'in veriyi rahat örnekleyebildiğini
gösterir; ISI ve jitter gözü yatay/dikey kapatır. Modern GT'ler, veri
akarken gözün fotoğrafını çekebilen **eye scan** donanımı taşır
({{sec:16}}'da IBERT ile kullanacağız).

**BER (bit error ratio — bit hata oranı)**: istatistiksel gerçek. Seri
linklerde klasik hedef **10⁻¹²** mertebesidir — 12.17 Gb/s'lik lane'de
yaklaşık 82 saniyede bir bit hatası bütçesi. "Link çalışıyor" cümlesi
aslında "BER hedefin altında" demektir; göz ne kadar açıksa BER o kadar
düşüktür. İkisi aynı gerçeğin analog ve istatistik dilidir.

::: dikkat
BER 10⁻¹² "hata olmaz" demek değildir. 8 lane × 12 Gb/s'lik bir sistemde
10⁻¹² BER, ortalama ~10 saniyede bir bit hatası demektir. JESD204C'nin
CRC/FEC mekanizmalarının ({{sec:7}}) varlık sebebi budur: hata *olacaktır*;
mesele yakalamak ve — mümkünse — düzeltmektir. Payload'daki tek bit hatası
scrambler yüzünden patlayarak çoğalmaz ama tespitsiz de geçmemelidir.
:::

## FPGA GT anatomisi: ilk tanışma

FPGA tarafında bu makinelerin yaşadığı yer **GT** (gigabit transceiver)
blokları. Versal ayrıntısı {{sec:14}}'te; burada mimarinin dilini öğrenelim:

- **Kanal (channel)**: bir TX + bir RX çifti; SerDes, CDR, eşitleyiciler,
  8b/10b-64b/66b donanımı hepsi kanalın içindedir.
- **Quad**: 4 kanal + ortak kaynakların paketi. FPGA kenarında GT'ler
  quad'lar halinde dizilir; JESD linkinin L lane'i (bizim örnekte 4), tipik
  olarak bir quad'ı doldurur.
- **Refclk girişi**: her quad'ın özel, düşük jitter'lı referans clock
  girişleri vardır. Bu clock **fabric'ten gelmez** — kart üstündeki clock
  chip'ten özel pinlere gelir. Neden? {{sec:2}}'nin jitter tablosunu FPGA
  içi clock dağıtımının picosaniye jitter'ıyla birleştir: fabric clock'uyla
  beslenen bir GT PLL'i, lane'i çalıştırır belki ama jitter bütçeni yer.
  {{sec:8}} ve {{sec:11}}–{{sec:12}}'de clock tree'yi çizerken GT refclk,
  masadaki en önemli müşterilerden biri olacak.
- **PLL'ler**: refclk'ten lane hızını üreten çarpanlar. İki aile görürsün:
  **LC PLL** (LC tank osilatörlü; düşük jitter, dar-orta ayar aralığı,
  kanallar arasında paylaşımlı) ve **ring PLL** (halka osilatörlü; esnek
  ama daha gürültülü). Aile adları FPGA nesline göre değişir — UltraScale
  QPLL/CPLL der, Versal LCPLL/RPLL ({{sec:14}}) — ama iş bölümü aynıdır:
  yüksek hızlı JESD linkleri pratikte LC PLL'den sürülür; hangi PLL'in
  hangi lane hızını destekleyeceği, {{sec:14}}'teki hesabın parçasıdır.

Fizik katmanının makinesini gördün. Şimdi bu makinenin üstünde koşan
protokole çıkıyoruz: JESD204 tam olarak neyi standartlaştırır, o meşhur
L/M/F/S harfleri ne anlama gelir ve bir link konfigürasyonu uçtan uca nasıl
hesaplanır?

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- TI, SBAA517: *JESD204B/C overview* — kodlama ek yükleri, encoding
  karşılaştırması.
- Analog Devices, JESD204 teknik makale serisi — embedded clock, CGS/CDR
  ilişkisi.
- AMD/Xilinx transceiver mimari dokümantasyonu (GTY sınıfı) — quad/kanal/
  PLL kavramları (Versal ayrıntısı ve doküman numaraları {{sec:14}}'te).
- TI, SNLA180 ve Lattice TN1114 — CML sonlandırma, AC kuplaj ve DC-balance
  ilişkisi.
- Genel yüksek hızlı seri link literatürü — eşitleme, eye mask, 10⁻¹² BER
  hedefi.
- Toplu ve linkli liste: {{sec:19}}.

</details>
