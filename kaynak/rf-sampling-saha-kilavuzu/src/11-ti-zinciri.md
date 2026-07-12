# Bölüm 11 — TI Zinciri: AFE7900 + LMK04832 + LMX1204 + Versal

On bölümdür kavram anlattık; şimdi kart üstüne iniyoruz. Bu bölüm, TI
ekosistemiyle kurulmuş tipik bir direct RF sampling zincirini —
AFE7900 (RF AFE), LMK04832 (jitter cleaner), LMX1204 (GHz dağıtıcı) ve
Versal FPGA — {{sec:8}}'deki clock anatomisi ve {{sec:9}}'daki SYSREF
kavramlarıyla birebir eşleyerek anlatır. Amaç iki yönlü: şemayı eline
aldığında turuncu ve camgöbeği hatların nereden nereye gittiğini okumak;
init kodu yazarken hangi çipin hangi sırayla, neden ayaklandırıldığını
bilmek. Bölüm boyunca pin adları public datasheet'lerdeki yazımla verilir.

::: ogren
- AFE7900'ün kuşbakışı mimarisini (public seviye)
- LMK04832'nin girişlerini, PLL'lerini, CLKout çiftlerini, SYSREF makinesini
- LMX1204'ün zincirdeki rolünü: GHz dağıtımı + SYSREF repeater
- Uçtan uca clock tree'yi (D02) ve örnek frekans planını
- Gömülü yazılımcı gözüyle init sırasının iskeletini
:::

## AFE7900 kuşbakışı

Public ürün tanımıyla AFE7900, **4T6R** bir RF-sampling transceiver'dır:
4 verici (TX), 4 alıcı (RX) ve 2 geri besleme (feedback — FB, verici
gözlem) yolu. Sayılar etkileyici: verici tarafta dört adet **12 GS/s
RF-sampling DAC**, alıcı tarafta dört adet **3 GS/s ADC** + iki adet 3 GS/s
FB ADC; RF aralığı **5 MHz – 7.4 GHz** (L/S/C bantları doğrudan
örneklenir). {{sec:1}}–{{sec:3}}'te kurduğumuz her blok içeride mevcut:
kanal başına DSA (TX 40 dB, RX/FB 25 dB aralık), tek/çift bantlı DDC/DUC
zincirleri ve yol başına 16 NCO — hepsi senin SPI register'larınla
yönetilir (SPICLK/SPISDIO/SPISDO/SPISEN pinleri, RESETZ ile birlikte
public tablolarda görünür).

Dış dünyaya bağlantı: **8 SerDes lane** ({1:8}SRX± alıcı, {1:8}STX±
verici), **JESD204B ve 204C**, lane başına **29.5 Gb/s'ye kadar**, subclass
1 desteğiyle. Clock tarafında üç kritik giriş görürsün: **REFCLK±**
(dahili PLL/VCO kullanılacaksa referans), **CLK±** (dahili PLL yerine
doğrudan yüksek frekans converter clock'u vermek istersen) ve **SYSREF±**.
Datasheet, SYSREF± için CLK+ kenarına göre **50 ps setup / 50 ps hold**
verir — {{sec:9}}'daki pencerenin sayısal hali — ve bir "SYSREF alignment
detector"dan söz eder: {{sec:9}}'daki windowing/monitoring donanımının bu
çipteki adı.

::: pasa
AFE7900'ün public datasheet'i (SBASA44B) kısaltılmıştır: **pin
yerleşimi/ball map, register haritası ve programlama detayı public
değildir** ("request full data sheet" akışı). Bu kılavuzdaki pin adları
yalnızca public tablolarda geçenlerdir. Tam pinout, register adresleri,
init register dizileri ve DDC/DUC-JESD konfigürasyon ayrıntısı için
elindeki TI güvenli dokümanlarına bak: AFE7900 tam datasheet'i ve AFE79xx
programlama/konfigürasyon kılavuzu (TI secure/MySecure üzerinden).
:::

## LMK04832: zincirin kalbi

{{sec:8}}'de anlattığımız clock chip anatomisi, LMK04832'de (datasheet
SNAS688) şöyle ete kemiğe bürünür:

- **Girişler**: referanslar **CLKin0/CLKin0\*, CLKin1/CLKin1\*,
  CLKin2/CLKin2\*** (otomatik/manuel seçim; CLKin1 pinleri gerektiğinde
  0-delay geri besleme **FBCLKin** veya harici VCO girişi **Fin1** olarak
  görev değiştirir); **OSCin/OSCin\*** ise PLL1'in kilitlediği harici
  VCXO'nun döndüğü kapıdır.
- **PLL1 — temizlik**: kirli referansı OSCin'deki VCXO'ya dar bantla
  kilitler ({{sec:8}}'deki jitter cleaning).
- **PLL2 — çarpma**: VCXO'yu dahili VCO'lardan birine çarpar: **VCO0
  2440–2580 MHz, VCO1 2945–3255 MHz** (gerekirse Fin1'den harici VCO).
  Maksimum çıkış frekansı **3255 MHz**.
- **Çıkışlar**: 14 diferansiyel çıkış, fiziksel adlarıyla
  **CLKout0/CLKout0\* … CLKout13/CLKout13\*** (+ tamponlu **OSCout**).
  Blok şemada bunlar 7 çift olarak işlevsel ad taşır: **DCLKout0, 2, …,
  12** (device clock) ve **SDCLKout1, 3, …, 13** (SYSREF). {{sec:8}}'in
  "DCLK/SYSREF çifti" kavramı, bu çipte pin düzeninin ta kendisidir: her
  çift aynı bölücü zincirinden türediği için faz ilişkileri bilinir.
- **SYSREF makinesi**: SYSREF bölücüsü **8–8191** aralığında; çıkışa
  **25 ps adımlı analog gecikme** + dijital gecikmeler eklenebilir
  ({{sec:9}}'daki pencere ortalama işi için). Modlar {{sec:9}}'daki
  tiplerin karşılığıdır: **SYSREF Pulser** (SPI'dan ya da
  **SYNC/SYSREF_REQ** pininden tetiklenen **1/2/4/8 darbe**), **Continuous**
  (datasheet'in kendisi crosstalk nedeniyle önermez!) ve **SYSREF Request**
  (harici pin yüksekken sürekli akış).

Yazılımcı gözüyle: LMK04832 init'i, {{sec:8}}'deki kilit merdivenidir —
PLL1 kilidini bekle, PLL2 kilidini bekle, çıkış bölücülerini/formatlarını
yaz, SYSREF makinesini kur ama **tetikleme** ({{sec:15}}'teki sıraya kadar)
bekle.

## LMX1204: GHz dağıtıcısı

LMK04832'nin 3.2 GHz tavanı ve sınırlı fan-out'u, çok çipli yüksek frekans
sistemlerde bir halka daha ister. LMX1204 (SNAS800B) tam bu iş için bir
**clock dağıtıcıdır**: 0.3–12.8 GHz girişi (**CLKIN_P/N**) alır; ÷1…÷8
böler ya da dahili PLL'le ×2/×3/×4 çarpar; **dört eş çıkışa**
(**CLKOUT0..3_P/N**) dağıtır — ve additive jitter'ı yalnızca birkaç
femtosaniyedir (12 kHz–20 MHz bandında 5 fs; DC'den taşıyıcıya <30 fs).
{{sec:8}}'deki "zincirin her halkası gürültü ekler" cümlesinin çözümü:
dağıtım halkası, eklemeyen bir halka olmalı.

Zincirin zarif detayı SYSREF'tedir: her clock çıkışının yanında eşlenik
bir **SYSREFOUT0..3_P/N** vardır. SYSREF ya çip içinde üretilir (generator
modu) ya da — bizim topolojide — LMK04832'den **SYSREFREQ_P/N** girişine
gelir ve **repeater modunda** device clock'a yeniden zamanlanarak
(re-time) dağıtılır: SYSREF, AFE'lere device clock ile *aynı yoldan, aynı
çipten, bilinen fazla* varır. {{sec:9}}'un setup/hold derdi için ayrıca
508 adımlı gecikme (12.8 GHz'te adım <2.5 ps) ve SYSREFREQ girişinde
windowing vardır. FPGA tarafı için bonus: **LOGICLKOUT_P/N** (÷ ile
1–800 MHz) ve **LOGISYSREFOUT_P/N**, fabric clock/SYSREF ihtiyacını
karşılar. SPI pinleri: **SCK, SDI, CS#, MUXOUT**.

## Uçtan uca clock tree

![TI zinciri clock tree: pin adları public datasheet yazımıyla. Turuncu = device clock, camgöbeği = SYSREF, kesikli = SPI. Frekanslar örnek plandır.](../diagrams/svg/d02.svg)

{{fig:d02}}'yi {{sec:3}}–{{sec:5}}'teki örnek sistemimizle sayısal olarak
dolduralım (ADC fs = 2.94912 GS/s, JESD204C, LEMC = 5.76 MHz):

| İhtiyaç | Değer | Kaynak |
|---|---|---|
| AFE converter clock | 2949.12 MHz | LMK VCO1 → LMX1204 ÷1 (CLKOUT0..1) |
| FPGA GT refclk | 368.64 MHz | LMK VCO1 ÷ 8 (DCLKout8) |
| SYSREF (herkese) | 1.44 MHz | LMK VCO1 ÷ 2048 (8–8191 aralığında ✓) |
| SYSREF ≟ LEMC böleni | 5.76 / 1.44 = 4 | {{sec:9}} kuralı ✓ |
| FPGA core clock | LOGICLKOUT'tan | lane rate/66 hesabı {{sec:14}}'te |

Planın güzelliği tek VCO'dan türemesinde: her frekans 2949.12 MHz'in tam
sayıya bölümü, dolayısıyla hepsi birbirine faz-kilitli. AFE'nin dahili
PLL/VCO seçeneği (REFCLK± üzerinden) alternatif bir topolojidir — kart
basitleşir, ama converter clock'un jitter'ı artık AFE'nin dahili PLL'inin
insafındadır; jitter bütçesi dar sistemler bu yüzden genelde harici tam
hız clock (CLK±) yolunu seçer. Bu trade-off {{sec:13}}'te ADI zinciriyle
karşılaştırılırken yeniden karşımıza çıkacak.

::: saha
Çok çipli senkronizasyonun TI dünyasındaki public kanıtı TIDA-010230
referans tasarımıdır: iki AFE7950, LMK04832 + iki LMX2820 (sentezleyici)
zinciriyle, 8847.36 MHz device clock ve 1.92 MHz SYSREF kullanılarak
**<10 ps** kanal hizasına getirilmiştir. Dağıtıcı olarak LMX1204'ün
AFE79xx SYSREF girişleriyle eşleşmesi ise LMX1204 datasheet'inin uygulama
bölümünde açıkça gösterilir. İki topoloji de meşrudur: sentezleyici
(LMX2820 sınıfı) frekans esnekliği, dağıtıcı (LMX1204) mutlak jitter
düşüklüğü yönünde ağırlık koyar.
:::

## Init sırasının iskeleti

Ayrıntılı akış {{sec:15}}'te; TI zincirine özgü omurga şu:

1. **LMK04832**: referansı seç (CLKin0), PLL1 kilidini bekle, PLL2
   kilidini bekle, çıkışları aç. SYSREF'i **henüz tetikleme**.
2. **LMX1204**: bölücü/çarpan ve çıkış formatlarını yaz; SYSREF repeater
   yolunu kur; windowing/gecikme ayarını yap.
3. **AFE7900**: RESETZ ile temiz başlat; clock modunu (CLK± doğrudan /
   REFCLK±+dahili PLL) kur; DSA, DDC/DUC, NCO ve JESD parametrelerini yaz;
   SYSREF alignment detector'ı oku — pencere marjinini logla ({{sec:9}}).
4. **FPGA**: {{sec:14}}'teki GT + JESD204C IP kurulumunu yap.
5. **SYSREF tetikle** (LMK04832 pulser, 1/2/4/8 darbe): tüm LMFC/LEMC'ler
   ve NCO fazları hizalanır ({{sec:10}}).
6. **Doğrula**: link durumları, SYSREF monitörleri, CRC sayaçları.

::: pasa
Adım 3'ün register düzeyi içeriği (AFE7900 init register dizisi, hangi
kalibrasyonların hangi sırayla koşulacağı, JESD konfigürasyon
register'ları) public dokümantasyonda yoktur. Elindeki TI güvenli
kaynaklarına bak: AFE79xx programlama kılavuzu ve TI'ın sağladığı
konfigürasyon aracı çıktıları (Latte/EVM script'leri). Multi-chip sync
akışının AFE79xx özel app note'u da aynı kapsamdadır.
:::

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- TI, AFE7900 ürün sayfası ve SBASA44B public datasheet — kanal/hız/
  arayüz özellikleri, public pin adları, SYSREF setup/hold.
- TI, SNAS688 (LMK04832 datasheet) — mimari, pin adları, VCO aralıkları,
  SYSREF modları.
- TI, SNAS800B (LMX1204 datasheet) — pin adları, bölücü/çarpan,
  SYSREF generator/repeater, jitter değerleri, AFE79xx arayüz şekli.
- TI, TIDUEZ6 (TIDA-010230 referans tasarımı) — çok çipli senkronizasyon
  örneği ve sayıları.
- TI, SBAU338 (AFE79xxEVM kılavuzu) — EVM clock topolojisi.
- Toplu ve linkli liste: {{sec:19}}.

</details>
