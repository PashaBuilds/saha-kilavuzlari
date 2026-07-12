# Bölüm 7 — JESD204C Derinlemesine

204B'yi öğrendin; şimdi elindeki AFE7900 veya AD9084'ün ana dili olan
204C'ye geçiyoruz. İyi haber: kavramsal iskelet aynı — transport aynı
transport, deterministic latency yine bir sayaç hizalama meselesi. Değişen,
data link katmanının **tamamen yeniden yazılmış** olması: K-karakterleri
yok, SYNC~ yok, ILAS yok. Yerlerinde daha verimli, daha ölçeklenebilir ama
ilk bakışta daha soyut bir yapı var: sync header stream. Bu bölümün sonunda
B'deki her kavramın C karşılığını gösteren köprü tablosu seni bekliyor.

::: ogren
- 64b/66b blok yapısını ve sync header'ın gerçekte ne taşıdığını (W03)
- Block → multiblock → extended multiblock hiyerarşisini ve E'yi
- Kilitlenme merdivenini: SH lock → EoEMB → EMB lock (M01c)
- LEMC'yi ve LMFC ile akrabalığını
- CRC-12 / FEC / command channel seçeneklerini
- SYNC~ pininin yokluğunun bring-up'a etkilerini
- B ↔ C kavram eşleme tablosunu
:::

## 64b/66b ve sync header stream

Temel birim **blok**tur: 2 bit'lik sync header (SH) + 64 bit (8 oktet)
payload = 66 bit ({{fig:w03}}, üst şerit). {{sec:4}}'ten hatırla: ~%3 ek
yük, geçiş yoğunluğu ve DC dengeyi scrambler sağlıyor, hizalamayı SH deseni
veriyor. Buraya kadar Ethernet'in 64b/66b'sine benziyor; şimdi kritik fark:

::: dikkat
Ethernet'te SH, "bu blok veri mi kontrol mü" bilgisini taşır (01=veri,
10=kontrol). **JESD204C'de böyle bir ayrım yoktur — tüm bloklar veridir.**
SH çifti her blokta ya 01 ya 10'dur (00 ve 11 illegal, hizalama ihlali);
kodladığı şey, **sync word denen yan kanalın 1 bitidir**: 01 = lojik 1,
10 = lojik 0 (geçiş yönü bilgiyi taşır). Ethernet alışkanlığıyla 204C
SH'sini okumaya kalkmak, yaygın ve sinsi bir kafa karışıklığıdır.
:::

Yani her 66-bit blok, 64 bit kullanıcı verisi + sync word'e 1 bit katkı
taşır. Bu mütevazı yan kanal — blok başına tek bit — birazdan göreceğin
gibi multiframe işaretlerini, CRC'yi, FEC'i ve komut kanalını taşıyacak
kadar zengindir.

## Hiyerarşi: blok → multiblock → extended multiblock

- **Multiblock**: 32 blok = 32×66 = 2112 bit (lane başına 256 oktet
  payload). Sabittir; B'deki multiframe'in ritim tutan rolünü üstlenir.
  32 bloğun 32 SH biti, multiblock başına **32 bit'lik sync word**'ü
  oluşturur.
- **Extended multiblock (EMB)**: E adet multiblock. E, {{sec:5}}'ten
  tanıdığın parametredir ve şu kuralı güder: EMB, **tamsayı sayıda frame**
  içermelidir. F, 256'yı bölüyorsa (bizim örnekte F=4: 256/4=64 frame)
  E=1 yeterlidir; kimi egzotik F değerlerinde frame sınırının multiblock
  sınırına oturması için E>1 gerekir.

Frame'ler ({{sec:5}}'teki transport tanımı) bu yapının *içine* gömülür:
204C, frame kavramını korur ama frame sınırlarını hatta işaretlemez —
çerçeveleme tamamen sayaçlarla yürür. B'nin /F/, /A/ bekçileri yoktur;
onların yerini SH deseninin sürekli doğrulanması alır.

![JESD204C hiyerarşisi: 66-bit bloklar (üstte) ve sync-word bitlerinin multiblock üzerinde taşıdığı EoEMB deseni (altta). Kalan sync-word bitleri (p) pilot/CRC/komut taşır.](../diagrams/wavedrom/w03.json5)

## Kilitlenme merdiveni: SH lock → EoEMB → EMB lock

204C RX'i üç basamak tırmanır ({{fig:m01c}}):

1. **SH lock**: RX, 66-bit hizasını bilmez; bir hiza varsayar ve her 66
   bit'te bir SH çiftinin geçerli (01/10) olup olmadığına bakar. Geçersizse
   hizayı bir bit kaydırır, yeniden dener — 66 olasılık içinde doğru hiza,
   **64 ardışık geçerli blok** görülünce ilan edilir: SH lock. B'deki
   comma kilidinin karşılığıdır; farkı, özel karakter yerine istatistiksel
   desen kullanması.
2. **EoEMB arama**: SH bitlerinden sync word'ü okumaya başlayan RX,
   **EoEMB** (end of extended multiblock) adlı sabit deseni arar: sync
   word bitlerinde **1-0-0-0-0-1** dizisi, EMB sınırını işaretler
   ({{fig:w03}}, alt şerit).
3. **EMB lock**: 4 ardışık, doğru aralıklı EoEMB görülünce RX, EMB
   sınırlarına kilitlenmiştir. Artık frame/multiblock sayaçları kurulur,
   veri fazına geçilir; buffer release ({{sec:6}}'daki mekanizmanın C
   versiyonu) LEMC cetveline göre yapılır.

![JESD204C RX kilitlenme merdiveni — SH lock ve EMB lock, status register'larında ayrı bayraklar olarak görünür.](../diagrams/mermaid/m01c.mmd)

**Debug değeri**: bu merdivenin her basamağı ayrı status bitidir. "SH lock
var, EMB lock yok" ile "SH lock bile yok" tamamen farklı arızalardır —
ilki çerçeve/senkron problemi (SYSREF, LEMC), ikincisi fiziksel katman
(CDR, polarite, eşitleme) kokar. {{sec:16}}'daki semptom tablosunun C
tarafı bu merdiven üzerine kuruludur.

## LEMC: takvimin C sürümü

B'de LMFC vardı; C'de **LEMC** (local extended multiblock clock) var —
her cihazın EMB sınırlarını sayan yerel sayacı:

```text
f_LEMC = frame clock / (frame/EMB)     (örneğimizde 368.64 MHz / 64 = 5.76 MHz)
```

Rolü LMFC ile birebir aynıdır: ILAS'ın yerine geçen kilitlenme süreci,
buffer release ve multi-device hizalama hep LEMC cetveline bakar. Ve aynı
soru yine açıktır: iki cihazın LEMC'leri aynı fazda mı? Cevap yine
SYSREF'tir — {{sec:9}}'da SYSREF'in LMFC/LEMC fazını *nasıl* sıfırladığını
göreceğiz.

## Sync word'ün bütçesi: CRC, FEC, komut kanalı

Multiblock başına 32 sync-word bitinin birkaçı yapısal işaretlere (EoEMB
ve pilot bitleri) gider; kalan bütçe üç seçenekten birine harcanır:

- **CRC-12** (varsayılan yol): önceki multiblock'un verisi üzerinden
  hesaplanan 12 bit'lik sağlama. Hatayı **tespit eder**, düzeltmez; RX
  sayaç artırır, senin izleme yazılımın da o sayacı okur. Daha küçük
  bütçeli CRC-3 varyantı da tanımlıdır.
- **FEC** (forward error correction): multiblock başına 26 parite biti;
  tespitle kalmaz, kısa hata patlamalarını **düzeltir**. Uzun kablolar,
  backplane'ler, agresif lane hızları için.
- **Command channel**: TX'ten RX'e düşük hızlı bir yan haberleşme kanalı.
  Standart, ne için kullanılacağını uygulamaya bırakır; CRC-12 formatında
  sync word'de bu kanala ayrılmış 7 bit vardır.

Bunlar bağımsız seçenekler değil, **aynı 32 bit'lik sync word'ün alternatif
formatlarıdır**: CRC-12 formatında bitler CRC + komut kanalı arasında
bölüşülür; FEC formatında 26 bit'i parite kaplar ve CRC/komut bitlerine yer
kalmaz. Yani FEC ile CRC-12 aynı anda kullanılamaz; hangi formatın
kullanılacağı iki uçta da aynı register ayarıyla seçilir. Pratikte RF AFE +
FPGA IP kombinasyonlarında varsayılan CRC-12'dir; FEC desteği iki uçta da
varsa ve BER bütçen dardaysa düşünürsün.

Scrambling konusunda not: B'de opsiyoneldi; C'nin 64b/66b modunda
scrambler **her zaman açıktır** — geçiş yoğunluğu garantisinin tek kaynağı
odur, kapatma seçeneği yoktur.

## SYNC~ öldü — yaşasın ne?

204C'de RX'in TX'e sinyal çekebileceği özel bir pin yoktur. CGS isteği,
hata bildirimi gibi SYNC~'in taşıdığı her şey **uygulama katmanına**
devredilmiştir. Pratikte bu şu demektir:

- **Link kurulumu artık koreografi ister**: TX'e "başla" demek, RX'in
  hazır olduğundan emin olmak, kilitlenmeyi doğrulamak — hepsi senin
  init akışının SPI/register adımlarıdır. B'de SYNC~'in kabloda hallettiği
  el sıkışmayı, C'de yazılımın sırası halleder. {{sec:15}}'teki bring-up
  akışının C linklerinde daha "prosedürlü" olmasının sebebi budur.
- **Hata geri bildirimi izlemeye dönüşür**: RX bir şey ters gittiğinde
  TX'in bundan kendiliğinden haberi olmaz; senin izleme döngün (CRC
  sayaçları, kilit bayrakları) fark eder ve gerekiyorsa linki yeniden
  kurar.

Bu, gömülü yazılımcı için net bir sorumluluk artışıdır — ve bu dokümanın
V. kısmının neden bu kadar "yazılım ağırlıklı" olduğunun açıklaması.

## B ↔ C köprü tablosu

B bilen birinin C'ye geçiş sözlüğü:

| Kavram | JESD204B | JESD204C |
|---|---|---|
| Kodlama | 8b/10b (%20 hat vergisi) | 64b/66b (%3.1) |
| Maks. lane hızı | 12.5 Gb/s | 32 Gb/s |
| Bit/sözcük hizası | comma (K28.5) | SH deseni (01/10) |
| Link kurulumu | CGS + ILAS | SH lock → EoEMB → EMB lock |
| Takvim birimi | multiframe (K frame) | multiblock (32 blok) × E |
| Yerel sayaç | LMFC | LEMC |
| RX→TX sinyali | SYNC~ pini | yok — uygulama katmanı |
| Konfig beyanı | ILAS /Q/ verisi | yok — iki uç register'la kurulur |
| Hiza bekçisi | /F/, /A/ replacement | sürekli SH doğrulama |
| Hata tespiti | 8b/10b kod ihlalleri | CRC-12 (veya CRC-3/FEC) |
| Determinizm çapası | SYSREF → LMFC | SYSREF → LEMC |
| Scrambling | opsiyonel (pratikte açık) | her zaman açık |

Tablodaki son iki satır, iki dünyanın da aynı yere çıktığını gösteriyor:
ne B ne C, SYSREF olmadan deterministik olamıyor. Protokolü bitirdik;
şimdi dokümanın kalbine — clock'un ve SYSREF'in dünyasına — giriyoruz.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- Analog Devices, *JESD204C Primer* (Analog Dialogue, 2 kısım) — blok/
  multiblock/EMB yapısı, sync word, kilitlenme merdiveni, LEMC.
- TI, SBAA517 ve SBAA402 — SH kodlaması (01/10, geçiş = sync bit),
  CRC/FEC/komut seçenekleri, scrambler polinomları, B/C karşılaştırması.
- chipinterfaces.com, *JESD204 synchronizing receiver* — EoEMB/EMB lock
  akışı.
- Toplu ve linkli liste: {{sec:19}}.

</details>
