# Bölüm 12 — ADI Apollo Zinciri: AD9084 + HMC7044 + ADF4382 + Versal

Aynı problemi bir de Analog Devices'ın gözünden çözelim. Bu bölüm bilinçli
olarak {{sec:11}} ile **aynı şablonda** yazıldı: önce AFE kuşbakışı, sonra
jitter cleaner, sonra yüksek frekans halkası, sonra clock tree ve init
iskeleti. Amaç, iki bölümü üst üste koyduğunda ({{sec:13}}) farkların
kendiliğinden görünmesi. TI zincirini okuduysan buradaki her başlık sana
tanıdık gelecek — farklı olan, rollerin çiplere dağıtılma biçimi.

::: ogren
- AD9084 Apollo MxFE'nin kuşbakışı mimarisini (public seviye)
- HMC7044'ün girişlerini, VCO'larını, CLKOUT/SCLKOUT çiftlerini, pulse
  generator'ını
- ADF4382'nin zincirdeki rolünü: çok GHz device clock sentezi
- Uçtan uca clock tree'yi (D03) ve iki device-clock yolunu
- ADI tarafında init/senkronizasyon iskeletini (TRIG pinleri dahil)
:::

## AD9084 kuşbakışı

AD9084 (Apollo MxFE — mixed-signal front end), public tanımıyla **4T4R**
bir dev: dört adet **16-bit 28 GS/s RF DAC** ve dört adet **12-bit 20 GS/s
RF ADC**. Analog giriş bandı **DC–18 GHz** (L'den Ku'ya doğrudan
örnekleme), anlık bant genişliği **10 GHz'e kadar** — {{sec:1}}'deki
"direct sampling nereye kadar gider" sorusunun 2020'ler cevabı. İçeride
{{sec:3}}'ün tüm makinesi: kaba+ince DDC/DUC kanalizerleri, FSRC
(fractional sample rate converter), NCO'lar; ayrıca on-chip clock
multiplier, düşük gecikmeli loopback ve DSP'yi atlayan bypass modu.

JESD tarafı etkileyici: **48 lane'e kadar** JESD204C (lane başına
**28.21 Gb/s**) veya 204B (20 Gb/s). Kıyas için: {{sec:5}}'teki 4 kanallı
örneğimiz 4 lane kullanıyordu; AD9084'ün tam bant genişliği, FPGA
tarafında ciddi bir GT filosu ister — Versal'de 8-lane'lik FMC
konfigürasyonları ({{sec:14}}) tipik başlangıçtır.

Clock arayüzü üç kapıdan oluşur (ADI dokümanlarındaki adlarıyla):
**CLKC±** (doğrudan çok GHz device clock girişi), **PLL REFCLK** (on-chip
clock multiplier kullanılacaksa referans) ve **SYSREF±**. Bu üçlü,
{{sec:9}}–{{sec:10}}'daki kavramların pin karşılığıdır.

::: pasa
AD9084'ün datasheet'i ve Device User Guide'ı (ön sürüm) public'tir —
TI tarafına göre daha açık bir dokümantasyon politikası. Yine de register
haritasının tamamı, bazı kalibrasyon/karakterizasyon detayları ve ürün
yol haritası dokümanları ADI'nin destek kanalı üzerinden gelir. Elindeki
ADI güvenli dokümanı/desteği varsa: AD9084/AD9088 Device User Guide'ın
tam sürümü ve Apollo API (adi_apollo_*) referansıyla çalış.
:::

## HMC7044: tanıdık kalp, farklı aksan

HMC7044, {{sec:8}} anatomisinin ADI gerçeklemesi ve LMK04832'nin kabaca
dengidir: **dual-loop, integer-N jitter attenuator**, 14 çıkış, 3.2 GHz.
Aksan farkları öğreticidir:

- **Girişler**: dört referans girişi **CLKIN0–CLKIN3**; çoğu çok işlevli:
  **CLKIN0/RFSYNCIN** (deterministik gecikmeli RF senkron girişi — kaskad
  clock ağaçlarında üst kattan gelen senkron darbesi için),
  **CLKIN1/FIN** (harici VCO girişi), **CLKIN2/OSCOUT0** (çift yönlü).
  VCXO **OSCIN**'e bağlanır; ayrıca çok çipli senkronizasyon için ayrı bir
  **SYNC** pini vardır.
- **PLL2 VCO'ları**: iki dahili VCO (tipik kapsama 2150–2880 ve
  2650–3550 MHz; **garanti edilen aralık 2400–3200 MHz**).
- **Çıkışlar**: 14 kanal, 7 çift halinde: **CLKOUT0, 2, …, 12** (varsayılan
  device-clock profili) ve **SCLKOUT1, 3, …, 13** (varsayılan SYSREF
  profili). İnce ama önemli fark: datasheet'in kendi ifadesiyle kanallar
  **mantıksal olarak özdeştir** — DCLK/SYSREF ayrımı donanım değil SPI
  konfigürasyonudur. LMK04832'de de işlevsel adlar benzerdi; HMC7044 bu
  esnekliği açıkça vurgular (eval kartının bir SCLKOUT'u FPGA refclk'i
  olarak kullanması bundandır).
- **SYSREF/pulse generator**: {{sec:9}}'daki tiplerin register karşılığı —
  level-sensitive, **1/2/4/8/16 darbe** veya continuous (%50); tetik SPI,
  GPI ya da SYNC pininden. 12-bit SYSREF timer'ı ≤4 MHz.

::: dikkat
HMC7044'ün çıkışlarında ince analog gecikme (fine delay) bloğu vardır ve
cazip görünür — ama datasheet açıkça uyarır: analog gecikme yolu faz
gürültüsünü **12 dB'ye kadar** bozabilir. Kural: ince analog gecikmeyi
SYSREF kanallarında (SCLKOUTx) kullan, gürültüye duyarlı device clock
kanallarında (CLKOUTx) kullanma. SYSREF'in kendisi zaten bir "kenar
zamanlaması" sinyalidir, jitter toleransı yüksektir; device clock ise
{{sec:2}}'deki tabloya doğrudan girer.
:::

## ADF4382: dağıtmak yerine sentezlemek

TI zincirinde yüksek frekans halkası bir *dağıtıcıydı* (LMX1204). ADI
zincirinde aynı halka bir **sentezleyicidir**: ADF4382, entegre VCO'lu
fraksiyonel-N PLL — temel VCO oktavı **11–22 GHz**, çıkış bölücüleriyle
**687.5 MHz–22 GHz**, ve etkileyici bir jitter: 20 GHz taşıyıcıda
**20 fs** (100 Hz–100 MHz entegrasyonuyla — {{sec:8}}'deki bant uyarısını
hatırla: bu geniş bantta 20 fs, ciddi bir rakamdır). AD9084'ün CLKC±
girişini süren tipik kaynak budur: HMC7044'ün temizlediği referans
ADF4382'ye gider (REFP/N), ADF4382 çok GHz device clock'u **çipin dibinde,
yerel olarak** sentezler (RFOUT1P/N → CLKC±).

Bu "yerel sentez" felsefesinin sonucu: çok çipli sistemde **her AD9084'e
bir ADF4382** düşer. Faz tutarlılığı, ortak referans + SYSREF hizalaması +
gerektiğinde ADF4382'nin faz ayar yetenekleriyle (<1 ps sınıfı) kurulur.
{{sec:13}}'te bunun LMX1204'ün "merkezî dağıtım" felsefesiyle
karşılaştırması, iki zincir arasındaki en öğretici mimari farktır.

## Uçtan uca clock tree

![ADI Apollo zinciri clock tree: EVAL-AD9084 clock ağacından uyarlanmış örnek. İki device-clock yolu (CLKC± doğrudan / PLL REFCLK + on-chip multiplier) birlikte gösterildi; gerçek tasarımda biri seçilir.](../diagrams/svg/d03.svg)

{{fig:d03}}, ADI'nin kendi değerlendirme kartının (UG-2326) public clock
ağacından uyarlanmıştır: referans (125 MHz sınıfı) bir dağıtım tamponuyla
hem HMC7044'e (CLKIN3) hem ADF4382'ye (REFP/N) gider. HMC7044'ün
SCLKOUT'ları SYSREF'leri üretir (AD9084 SYSREF± + FPGA), bir CLKOUT'u
FPGA GT refclk'ini, istenirse bir diğeri AD9084 PLL REFCLK'ini besler.
Device clock için iki yol vardır ve bu bir **tasarım kararıdır**:

| Yol | Mekanizma | Artı | Eksi |
|---|---|---|---|
| (a) CLKC± | ADF4382 doğrudan çok GHz clock verir | En düşük jitter; converter clock'u tamamen senin kontrolünde | Çip başına bir sentezleyici, kart alanı/güç |
| (b) PLL REFCLK | AD9084'ün on-chip clock multiplier'ı çarpar | Basit kart, az parça | Jitter, on-chip PLL'in insafına |

AFE7900'ün REFCLK±/CLK± ikilemiyle birebir aynı trade-off — üreticiden
bağımsız bir mimari gerçek.

## Init ve senkronizasyon iskeleti

Sıra TI zincirindekiyle aynı omurgayı izler; ADI'ye özgü renkler şunlar:

1. **HMC7044**: referans seç, PLL1/PLL2 kilitlerini bekle, çıkış
   profillerini (CLKOUT/SCLKOUT) yaz; pulse generator'ı kur, tetikleme.
2. **ADF4382**: N bölücü/çıkış gücünü yaz, kilit bekle — CLKC artık canlı.
3. **AD9084**: Device UG'nin deyişiyle "Phase 0 — SYSREF Configuration and
   Alignment": subclass 1 için SYSREF yakalama/hizalama kurulumu; sonra
   DDC/DUC, NCO ve JESD konfigürasyonu. Senkronizasyon tetikleme iki
   yoldan: **dyn_cfg_sync** (SPI'dan yazılımla) veya **trig_sync**
   (**TRIG_A/TRIG_B** harici tetik pinleri) — API'de
   `adi_apollo_clk_mcs_*` ailesi.
4. **FPGA**: {{sec:14}}.
5. **SYSREF tetikle** (HMC7044 pulse generator) → LMFC/LEMC + NCO hizası
   ({{sec:10}}'daki akış; Apollo'da NCO reset LEMC kenarına bağlanabilir).
6. **Doğrula**: SYSREF monitörleri, link durumları, kanal-arası faz testi.

::: saha
Çok kartlı/kaskad sistemlerde ADI'nin Quad-Apollo referans tasarımı
zarif bir numara kullanır: ADF4030 sınıfı bir "SYSREF kaynağı" ile
**BSYNC gidiş-dönüş kalibrasyonu** — SYSREF izlerinin yol gecikmeleri
sistem çalışırken ölçülüp sıfırlanır. Kartlar arası SYSREF eşleme derdin
varsa (kablo boyları!), bu yaklaşımın public makalesini oku; kavram,
üretici bağımsız ilham verir.
:::

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- ADI, AD9084 ürün sayfası + datasheet + AD9084/AD9088 Device User Guide
  (ön sürüm, public) — mimari, hızlar, lane sayısı, CLKC/PLL REFCLK/
  SYSREF, Phase 0 / dyn_cfg_sync / trig_sync.
- ADI, UG-2326 (EVAL-AD9084 kılavuzu) — clock ağacı (Fig. 8), ADF4382 →
  CLKC yolu, HMC7044 çıkış atamaları.
- ADI, HMC7044 datasheet (Rev C) — pinler, VCO kapsamaları, pulse
  generator modları, analog gecikme uyarısı.
- ADI, ADF4382 datasheet — frekans aralığı, jitter, MxFE clocking rolü.
- ADI, Quad-Apollo MxFE referans tasarım makalesi ve Quad-MxFE MCS wiki —
  çok çipli senkronizasyon, ADF4030/BSYNC.
- Toplu ve linkli liste: {{sec:19}}.

</details>
