# Bölüm 0 — Giriş

Masana üzerinde RF-sampling AFE (analog front end — analog ön uç entegresi),
bir clock chip ve koca bir Versal FPGA olan bir kart geldi. Görevin: bu kartı
ayağa kaldırmak. Şemayı açtın; "JESD204C", "SYSREF", "GTY quad", "LMFC" gibi
terimler havada uçuşuyor. Donanımcıya sordun, "link'i sen kaldıracaksın" dedi.
Datasheet'i açtın; 400 sayfa. Bu kılavuz tam bu an için yazıldı.

::: ogren
- Bu dokümanın kimin için yazıldığını ve neyi vaat ettiğini
- Antenden bit'e bir sinyalin izlediği yolun büyük resmini
- Hangi bölümün hangi soruya cevap verdiğini ve okuma yollarını
- Callout kutularının (NOT, DİKKAT, SAHA NOTU, PAŞA NOTU) ne anlama geldiğini
:::

## Bu kılavuz kimin için?

Hedef okur, **gömülü yazılımcı**: register yazan, init sırası kurgulayan,
link ayağa kaldıran, düşen link'i debug eden kişi. RF devre tasarımı yapman
beklenmiyor; ama kartındaki entegrelerin *neden* orada olduğunu, *hangi
sinyalin neyi tetiklediğini* ve *senin kodunun nereye dokunduğunu* bilmen
gerekiyor. Bu doküman JESD204, SERDES ve clocking konusunda **sıfır bilgi**
varsayar; her kavramı kullanmadan önce tanımlar.

Somut hedef donanımlar da belli: TI tarafında AFE7900 sınıfı RF-sampling
transceiver'lar ({{sec:11}}), ADI tarafında AD9084 (Apollo MxFE) sınıfı
({{sec:12}}), FPGA tarafında AMD Versal ({{sec:14}}). Ama {{sec:1}}–{{sec:10}}
arası tamamen üreticiden bağımsızdır; başka bir AFE veya FPGA ile
çalışıyorsan da işine yarar.

## Büyük resim: antenden bit'e

Yolculuğun tamamı tek paragrafta şu: antene düşen RF sinyali önce analog ön
uçtan geçer — LNA (low-noise amplifier — düşük gürültülü yükselteç) sinyali
gürültü eklemeden büyütür, filtre istenmeyen bantları atar, balun sinyali
diferansiyele çevirir. Sonra AFE'nin içindeki ADC, sinyali **RF frekansında,
saniyede milyarlarca örnekle** doğrudan sayısallaştırır; DDC (digital
downconverter — sayısal aşağı çevirici) bu örnek selinden ilgilendiğin bandı
seçip hızı makul seviyeye indirir. Bu veri, JESD204 protokolüyle
paketlenip birkaç seri hat (lane) üzerinden çok Gb/s hızında FPGA'ya akar;
FPGA'daki GT (gigabit transceiver) alıcıları ve JESD204 IP'si veriyi çözer,
kullanıcı lojiğine teslim eder. Senin kodun bu zincirin her halkasını SPI ve
register erişimiyle yapılandırır, senkronize eder ve sağlığını izler. Tüm bu
zincirin kalp atışını ise iki sinyal belirler: **device clock** (örnekleme
saatinin kaynağı) ve **SYSREF** (herkesin sayaçlarını aynı ana hizalayan
senkronizasyon sinyali). Bu ikilinin hikâyesi, dokümanın kalbi olan
{{sec:8}}–{{sec:10}}'da anlatılır.

![Antenden bit'e: sinyalin yolculuğu. Parantezdeki bölüm numaraları o halkanın nerede derinleştiğini gösterir.](../diagrams/svg/d01.svg)

{{fig:d01}}'deki renk kodu dokümanın tamamında sabittir: **turuncu/amber**
çizgiler device clock yollarını, **camgöbeği** çizgiler SYSREF yollarını,
kalın nötr çizgiler SerDes veri hatlarını, kesikli çizgiler SPI benzeri
kontrol yollarını gösterir. Bir şemada turuncu bir hat gördüğünde onun bir
clock, camgöbeği bir hat gördüğünde onun bir senkronizasyon sinyali
olduğunu düşünmeden bileceksin.

## Bu dokümanı nasıl okumalı?

Doküman altı kısma ayrılır ve **her kavram, kendisine ihtiyaç duyan
kavramdan önce** anlatılır:

| Kısım | Bölümler | Soru |
|---|---|---|
| I — Temeller | 1–3 | RF sinyali nasıl sayıya dönüşür? |
| II — SERDES ve JESD204 | 4–7 | Sayılar FPGA'ya nasıl taşınır? |
| III — Clocking ve SYSREF | 8–10 | Herkes aynı âna nasıl hizalanır? |
| IV — Donanım zincirleri | 11–13 | Gerçek kartlarda bu nasıl görünür? |
| V — Versal entegrasyonu | 14–16 | FPGA tarafında ne olur, nasıl debug edilir? |
| VI — Kapanış | 17–19 | Kontrol listesi, sözlük, kaynakça |

Üç okuma yolu öneriyorum:

1. **Baştan sona (önerilen).** JESD'e sıfırdan başlıyorsan bölümleri sırayla
   oku; her bölüm bir öncekinin üstüne kurulur.
2. **Acil bring-up yolu.** Kart masada, süre dar: {{sec:0}} (bu bölüm) →
   {{sec:5}} link parametreleri → {{sec:9}} SYSREF → kendi zincirin
   ({{sec:11}} TI veya {{sec:12}} ADI) → {{sec:15}} bring-up akışı. Takıldığın
   kavram olursa terminoloji haritasından ilgili bölüme dal.
3. **"Link'im düşüyor" yolu.** Sistem bir şekilde çalışmış ama dertli:
   doğruca {{sec:16}} debug bölümüne git; oradaki semptom→sebep tablosu ve
   karar ağacı seni ilgili teoriye yönlendirir.

Metin boyunca dört tür kutu göreceksin:

::: not
Ana akışı bozmayan ek bilgi, hatırlatma veya bağlam.
:::

::: dikkat
Yaygın hata, tuzak veya geri dönüşü zor karar. Bunları atlamadan oku.
:::

::: saha
Gerçek kartlarda yaşanmış, datasheet'te yazmayan türden ders. Anonimleştirilmiş
saha tecrübesi.
:::

::: pasa
NDA (non-disclosure agreement — gizlilik sözleşmesi) kapsamındaki detayın
kasten boş bırakıldığı yer. Bu kutu sana hangi güvenli dokümana bakacağını
söyler; bu dokümanda o bilgi **yoktur** ve olmayacaktır.
:::

## Terminoloji haritası

Aşağıdaki tablo, karşına çıkacak terim ailelerini ve her birinin nerede
tanımlandığını gösterir. Şimdi anlamıyor olman normal; harita, kaybolduğunda
dönüp bakman için burada.

| Alan | Terimler | Nerede |
|---|---|---|
| Örnekleme | Nyquist, aliasing, Nyquist bölgesi, undersampling, folding | {{sec:1}} |
| RF mimarisi | superheterodyne, zero-IF, direct RF sampling, LNA, DSA, balun | {{sec:1}} |
| ADC/DAC | ENOB, SNR, SFDR, NSD, IMD3, interleaving, sinc roll-off, mix-mode | {{sec:2}} |
| Dijital yol | DDC, DUC, NCO, decimation, interpolation, I/Q | {{sec:3}} |
| SERDES | CML, CDR, 8b/10b, 64b/66b, eşitleme (CTLE/DFE), eye, BER, GT | {{sec:4}} |
| JESD204 | L/M/F/S/N/N′/K/E, subclass, transport/link katmanları | {{sec:5}} |
| JESD204B | SYNC~, CGS, ILAS, frame, multiframe, LMFC, RBD | {{sec:6}} |
| JESD204C | sync header, block/multiblock/EMB, SH/EMB lock, EoEMB, LEMC, CRC/FEC | {{sec:7}} |
| Clocking | faz gürültüsü, integrated jitter, dual-loop PLL, jitter cleaner | {{sec:8}} |
| Senkronizasyon | SYSREF, setup/hold penceresi, continuous/gapped/one-shot | {{sec:9}} |
| Determinizm | deterministic latency, elastic buffer, multi-chip sync, NCO reset | {{sec:10}} |
| Donanım | AFE7900, LMK04832, LMX1204, AD9084, HMC7044, ADF4382 | {{sec:11}}–{{sec:13}} |
| Versal | GTY/GTYP, quad, refclk, JESD204C IP, core/link clock | {{sec:14}} |
| Saha | bring-up sırası, loopback, IBERT, eye scan, semptom→sebep | {{sec:15}}–{{sec:16}} |

## Bu doküman ne değildir?

Dürüst olalım:

- **RF devre tasarımı kılavuzu değildir.** Empedans eşleme, filtre sentezi,
  PCB yerleşimi gibi konulara ancak yazılımı etkilediği kadar gireriz.
- **Datasheet'in yerine geçmez.** Amaç, datasheet'i *okuyabilir* hale
  gelmen; register haritasını ezberletmek değil.
- **NDA malzemesi içermez.** AFE7900'ün tam datasheet'i ve AD9084
  dokümantasyonunun bir kısmı NDA'lıdır. Bu dokümandaki her bilgi public
  kaynaklardan gelir; NDA gerektiren her nokta PAŞA NOTU kutusuyla açıkça
  işaretlenir ve boş bırakılır.
- **Ürün reklamı değildir.** İki üretici zincirini de aynı şablonla anlatır,
  trade-off'ları olduğu gibi veririz ({{sec:13}}).

Hazırsan, işin fiziğinden başlayalım: bir RF sinyalini saniyede milyarlarca
kez örneklemek ne demek ve neden buna cesaret edebiliyoruz?

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

Bu bölüm yol haritası niteliğindedir; teknik iddialar ilgili bölümlerin
kaynaklarına dayanır (toplu liste: {{sec:19}}).

</details>
