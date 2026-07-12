# Bölüm 13 — İki Zincirin Karşılaştırması

{{sec:11}} ve {{sec:12}}'yi aynı şablonda yazmamızın sebebi bu bölümdü:
şimdi iki sayfayı yan yana koyup "kim kimin dengi, ne farklı, neden?"
sorusuna cevap vereceğiz. Bu karşılaştırmanın amacı bir kazanan ilan etmek
değil — proje gerçeğinde zinciri çoğu zaman sen seçmezsin, kart sana
gelir. Amaç, **bir zinciri öğrenmiş beyninin öbürüne hızla adapte
olması**: hangi kavramın hangi çipte yaşadığını bilirsen, hangi kartla
karşılaşırsan karşılaş aynı zihinsel haritayla çalışırsın.

::: ogren
- Çip-çip rol eşleme tablosunu
- "Kim device clock'u üretir, kim SYSREF'i" sorusunun iki cevabını
- Dağıtım (LMX1204) ile yerel sentez (ADF4382) mimari farkını
- On-chip PLL'in iki zincirde de aynı trade-off olduğunu
- D02/D03'ü yan yana okuma rehberini
:::

## Rol eşleme tablosu

| Rol | TI zinciri | ADI zinciri | Ortak DNA / fark |
|---|---|---|---|
| RF-sampling AFE | AFE7900 (4T6R; 12G DAC, 3G ADC; 8 lane ≤29.5G) | AD9084 (4T4R; 28G DAC, 20G ADC; ≤48 lane ≤28.21G) | İkisi de: DSA + DDC/DUC + NCO + JESD204B/C, subclass 1; sınıf farkı: AD9084 daha yüksek hız/bant, AFE7900 entegre FB yollarıyla verici gözlemi |
| Jitter cleaner + SYSREF | LMK04832 | HMC7044 | Neredeyse ikiz: dual-loop, harici VCXO, ~2.5/3 GHz çift VCO, 14 çıkışlı DCLK/SYSREF çiftleri, darbe üretici, 25 ps sınıfı gecikme adımı |
| Çok GHz halkası | LMX1204 (dağıtıcı: buffer/÷/×, VCO'suz) | ADF4382 (sentezleyici: PLL + 11–22 GHz VCO) | **En büyük mimari fark** — aşağıda |
| FPGA | Versal (GT + JESD204C IP) | Versal (GT + JESD204C IP) | Ortak; {{sec:14}} her ikisine aynı şekilde uygulanır |
| Konfigürasyon aracı | TI ekosistemi (EVM/konfigürasyon araçları) | ADI ekosistemi (ACE/API, açık kaynak HDL+Linux sürücüleri) | ADI'nin açık kaynak FPGA/yazılım referansları belirgin artı; TI'ın EVM+script akışı olgun |

Jitter cleaner satırındaki benzerlik tesadüf değil: iki çip de aynı
problemi ({{sec:8}}'in dual-loop anlatımı) aynı topolojiyle çözüyor.
Birinden diğerine geçen yazılımcı için register adları değişir, kavram
haritası değişmez: "referans seç → PLL1 kilidi → PLL2 kilidi → çıkış
bölücüleri → SYSREF makinesi" akışı ikisinde de birebir vardır.

## Kim neyi üretir?

**Device clock:**

- **TI**: yüksek frekans clock *merkezde* üretilir (LMK04832 VCO'su ya da
  ayrı bir sentezleyici) ve LMX1204 **dağıtır** — bir kaynaktan N çipe,
  neredeyse sıfır ek jitterla (<30 fs additive). Alternatif: AFE7900'ün
  on-chip PLL'i (REFCLK± yolu).
- **ADI**: temiz *orta frekans* merkezde üretilir (HMC7044), yüksek
  frekans **her çipin dibinde yerel sentezlenir** (ADF4382 → CLKC±).
  Alternatif: AD9084'ün on-chip clock multiplier'ı (PLL REFCLK yolu).

**SYSREF:**

- **TI**: LMK04832 üretir (pulser 1/2/4/8 darbe), LMX1204 **repeater**
  modunda device clock'a yeniden zamanlayıp AFE'lere taşır — SYSREF ile
  device clock aynı çipten, aynı yoldan çıkar; setup/hold eşlemesi
  yapısal olarak kolaydır.
- **ADI**: HMC7044 üretir (pulse generator 1/2/4/8/16) ve SCLKOUT'lardan
  doğrudan dağıtır; ADF4382 SYSREF yoluna karışmaz. SYSREF–CLKC faz
  eşlemesi kart tasarımı + HMC7044 gecikme ayarlarıyla kurulur; kaskad
  sistemlerde RFSYNCIN/BSYNC mekanizmaları devreye girer.

**On-chip PLL** iki zincirde de aynı ikilem ({{sec:11}} ve {{sec:12}}'deki
tablolar): kart basitliği ile jitter kontrolü arasında seçim. Kural
üretici bağımsızdır — {{sec:2}}'nin jitter bütçesi dar ise harici tam hız
clock; bütçe genişse (düşük giriş frekansı, mütevazı ENOB hedefi) on-chip
PLL kart maliyetini düşürür.

## Dağıtım vs yerel sentez: neden ikisi de haklı?

İki felsefenin trade-off'u sistem ölçeğiyle netleşir:

- **Merkezî dağıtım (LMX1204)**: tek frekans kaynağı → tüm çipler *aynı*
  clock'u görür; kanallar arası frekans/faz ilişkisi yapısal olarak
  sağlam. Additive jitter femtosaniyeler. Ama: dağıtım hattı GHz'lerde
  uzun mesafe koşar (kart tasarımı zorlaşır) ve frekans esnekliği kaynağın
  esnekliğiyle sınırlıdır.
- **Yerel sentez (ADF4382)**: GHz sinyal yalnızca santimetrelerce koşar
  (sentezleyici AFE'nin dibinde); her çipin frekansı bağımsız
  ayarlanabilir (frequency hopping, farklı bantlar); referans dağıtımı
  düşük frekansta yapılır (kolay). Ama: çip sayısı kadar PLL (alan, güç,
  maliyet) ve faz tutarlılığı için ek mekanizma (ortak referans + SYSREF +
  faz ayarı/kalibrasyon) gerekir.

Kaba kural: **kanal sayısı büyüyüp frekans planı sabitse dağıtım;
frekans çevikliği ve kart yerleşimi baskınsa yerel sentez** cazipleşir.
İki üretici de iki yaklaşımı destekler (TI'ın LMX2820 sentezleyicisi,
ADI'nin dağıtım tamponları vardır); {{sec:11}}–{{sec:12}}'deki eşleşme,
ürün ailelerinin *tipik* referans tasarımlarını yansıtır.

## D02/D03'ü yan yana okuma rehberi

İki şemayı yan yana aç ({{fig:d02}}, {{fig:d03}}) ve şu üç izi sürerek
karşılaştır:

1. **Turuncu iz (device clock)**: TI'da referans → LMK → LMX → AFE tek
   hat; ADI'da referans iki kola ayrılır (HMC ve ADF), yüksek frekans
   yalnız ADF→CLKC kısacık segmentinde yaşar.
2. **Camgöbeği iz (SYSREF)**: TI'da LMK'dan çıkar ama AFE'ye LMX
   üzerinden (re-time edilerek) varır; ADI'da HMC'den doğrudan yayılır.
   İkisinde de FPGA'ya ayrı bir dal gider — {{sec:9}}'un "herkese SYSREF"
   kuralı.
3. **Kesikli iz (SPI)**: ikisinde de CPU'dan tüm çiplere; init sırası
   ({{sec:15}}) bu izin üzerinde koşar.

Bu üç izi iki şemada da gözün kapalı sürebiliyorsan, KISIM IV görevini
tamamladı: artık hangi kartı önüne koyarlarsa koysunlar, şemada
kaybolmazsın. Sırada zincirin FPGA ucu var — Versal'in GT'leri ve
JESD204C IP'si.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

Bu bölüm, {{sec:11}} ve {{sec:12}}'nin kaynaklarına dayanır (LMK04832,
LMX1204, AFE7900, HMC7044, ADF4382, AD9084 dokümanları); rol
sınıflandırmaları üreticilerin kendi ürün kategorilerinden alınmıştır.
Toplu liste: {{sec:19}}.

</details>
