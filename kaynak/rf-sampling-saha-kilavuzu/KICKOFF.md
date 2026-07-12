# KICKOFF — rf-sampling-saha-kilavuzu

> Bu dosya, projenin tek başlangıç talimatıdır. Claude Code bu dosyayı okuyarak
> üretime başlar. Repo kökünde durur; içeriği CLAUDE.md'ye referans verilir.

---

## 1. Proje Kimliği

- **Klasör / repo adı:** `rf-sampling-saha-kilavuzu`
- **Doküman adı:** *Doğrudan RF Örnekleme ve Ön Uç Tasarımı — Saha Kılavuzu*
- **Seri:** "Saha Kılavuzu" serisi (önceki: Bellek Mimarisi Saha Kılavuzu)
- **Hedef kitle:** JESD/SERDES/clocking konusunda sıfır veya çok az bilgisi olan,
  bu entegreleri (AFE7900, AD9084 vb.) projesinde kullanmak zorunda olan
  **gömülü yazılımcı**. Donanımcı değil; register yazan, link ayağa kaldıran,
  debug eden kişi.
- **Misyon:** Tek başına literatür oluşturacak kapsamda, Türkçe, pedagojik,
  "çok kaliteli bir blog okuyorum" hissi veren tek bir HTML doküman üretmek.
- **Dil:** Türkçe gövde; teknik terimler İngilizce korunur, ilk geçtiği yerde
  parantez içinde Türkçe açıklama verilir. Örn: "deterministic latency
  (deterministik gecikme)". Kısaltmalar ilk kullanımda açılır.

---

## 2. Repo Yapısı

```
rf-sampling-saha-kilavuzu/
├── KICKOFF.md              # bu dosya
├── CLAUDE.md               # çalışma kuralları (KICKOFF §4–§5 özetlenir)
├── package.json
├── src/
│   ├── 00-giris.md
│   ├── 01-ornekleme-ve-rf-mimarileri.md
│   ├── 02-adc-dac-kavramlari.md
│   ├── 03-dijital-sinyal-yolu.md
│   ├── 04-serdes-temelleri.md
│   ├── 05-jesd204-standardi.md
│   ├── 06-jesd204b-derinlemesine.md
│   ├── 07-jesd204c-derinlemesine.md
│   ├── 08-clock-kalitesi.md
│   ├── 09-sysref.md
│   ├── 10-deterministic-latency-ve-sync.md
│   ├── 11-ti-zinciri.md
│   ├── 12-adi-apollo-zinciri.md
│   ├── 13-zincir-karsilastirmasi.md
│   ├── 14-versal-gt-ve-jesd-ip.md
│   ├── 15-bringup-akisi.md
│   ├── 16-debug-ve-loopback.md
│   ├── 17-tasarim-kontrol-listesi.md
│   ├── 18-sozluk.md
│   └── 19-kaynakca.md
├── diagrams/
│   ├── svg/                # elle yazılmış SVG (blok şema, clock tree)
│   ├── wavedrom/           # .json5 timing diyagramları
│   └── mermaid/            # .mmd akış/state diyagramları
├── scripts/
│   └── build.mjs           # md + şemalar → dist/index.html
├── templates/
│   └── page.html           # blog şablonu (tipografi, TOC, tema)
└── dist/
    └── index.html          # TEK, self-contained çıktı
```

---

## 3. Araç Zinciri ve Build Pipeline

**Prensip:** Kaynak = markdown + şema kaynak dosyaları (git'te yaşar, diff'lenir).
Çıktı = tek self-contained HTML (air-gapped ortama tek dosya olarak taşınır,
tarayıcıda açılır, gerekirse print CSS ile PDF'e basılır).

- **Node 20+**, bağımlılıklar: `markdown-it` (+ anchor/toc eklentileri),
  `wavedrom-cli`, `@mermaid-js/mermaid-cli`, kod renklendirme için `shiki`
  veya `prismjs`.
- `scripts/build.mjs`:
  1. `src/*.md` dosyalarını numara sırasıyla birleştirir.
  2. ` ```wavedrom ` ve ` ```mermaid ` çitli blokları ve
     `![](../diagrams/...)` referanslarını **inline SVG**'ye çevirir
     (dosya hash'i ile cache'ler, her build'de yeniden üretmez).
  3. `templates/page.html` içine gömer → `dist/index.html`.
- **Self-contained şartları:** hiçbir dış istek yok. Webfont YOK —
  air-gapped ortamda çekilemez; **system font stack** kullanılır
  (başlık: `Georgia, 'Times New Roman', serif` benzeri; gövde:
  `system-ui, -apple-system, 'Segoe UI', sans-serif`; kod: `ui-monospace`).
- **Blog hissi:** maks. ~72ch satır ölçüsü, bol beyaz alan, sticky içindekiler
  (solda), dark/light tema toggle'ı (CSS custom properties), şekil altyazıları
  (`<figure>/<figcaption>`, "Şekil 9.2 — ..." numaralaması), bölüm başlarında
  kısa "Bu bölümde ne öğreneceksin" kutusu, önemli uyarılar için callout
  blokları (NOT / DİKKAT / SAHA NOTU). Tasarım aşamasında **frontend-design
  skill'i** kullanılacak.

### Şema araçları — hangisi ne için (kalite kuralı)

| Araç | Kullanım alanı | Kullanılmayacağı yer |
|---|---|---|
| **Elle yazılmış SVG** | Donanım blok şemaları, clock tree'ler, pin-to-pin bağlantı diyagramları, mimari karşılaştırmalar | Timing |
| **WaveDrom** | Tüm timing diyagramları (SYSREF setup/hold, CGS/ILAS, sync header akışı, LMFC/LEMC hizalama) | Blok şema |
| **Mermaid** | Yalnızca state machine ve karar ağaçları | Donanım şeması, clock tree (layout kontrolü yetersiz) |

SVG kalite kuralları: 12 sütunluk görünmez grid üzerine hizalama; tutarlı blok
stili (yuvarlatılmış köşe, tek vurgu rengi clock yolları için, ikinci vurgu
SYSREF için — dokümanın tamamında aynı renk kodu); tüm sinyal isimleri
datasheet'teki pin adıyla birebir; ok uçları ve yön tutarlı; her SVG hem açık
hem koyu temada okunur (CSS `currentColor` + tema değişkenleri).

---

## 4. Yazım Kuralları

1. **Pedagojik sıra:** her kavram, kendisine ihtiyaç duyan kavramdan ÖNCE
   anlatılır. İleri referans gerekirse "bunu §X'te derinleştireceğiz" denir.
2. **Somutlaştırma:** her soyut kavram bir sayısal örnekle bağlanır
   (örn. link parametreleri anlatılırken gerçekçi bir M/L/F/S/K/E hesabı
   uçtan uca yapılır; jitter-SNR ilişkisi gerçek GHz/fs değerleriyle).
3. **"Neden" önce gelir:** SYSREF'in ne olduğu değil, önce hangi problemi
   çözdüğü anlatılır. Her bölüm bir motivasyon paragrafıyla açılır.
4. **Gömülü yazılımcı perspektifi:** her donanım kavramının "senin yazılımına
   dokunduğu yer" ayrıca işaretlenir (init sırası, hangi status register'ına
   bakacağı, hangi hatayı nasıl göreceği).
5. Ton: teknik, net, samimi ama laubali değil. LinkedIn dili ve klişe yok.
   Abartı yok; trade-off'lar dürüstçe verilir.

---

## 5. Doğruluk ve NDA Politikası (KRİTİK)

1. **Uydurma yasak.** Emin olunmayan her sayısal değer, register adı, pin adı
   `[DOĞRULA: ...]` etiketiyle işaretlenir ve web erişimli oturumda
   datasheet'ten teyit edilir. Teyit edilemeyen değer dokümana girmez.
2. **NDA boşlukları:** AFE7900'ün tam datasheet'i ve AD9084 dokümantasyonunun
   bir kısmı NDA'lıdır. Bu noktalar `> PAŞA NOTU: bu detay için elindeki
   TI/ADI güvenli dokümanına bak (doküman adı/bölümü)` bloklarıyla açık
   bırakılır. Public bilgi (ürün sayfası, kısa datasheet, app note) ile
   NDA bilgisi asla karıştırılmaz.
3. Standart isimleri ve doküman numaraları (JESD204C, AMD PG/AM/UG numaraları)
   ilk kullanımdan önce web'den teyit edilir; tahmini numara yazılmaz.
4. Her bölümün sonunda o bölümün dayandığı kaynaklar listelenir (kaynakça
   §19'da toplanır).

---

## 6. İçindekiler (tam kapsam)

### Bölüm 0 — Giriş
Kimin için, nasıl okunmalı; büyük resim: **antenden bit'e** bir sinyalin
yolculuğu (tek paragraf + D01 şeması); terminoloji haritası; okuma yolları
("acil bring-up yapacağım" hızlı yolu vs. baştan sona öğrenme yolu).

### KISIM I — TEMELLER

**Bölüm 1 — Örnekleme teorisi ve RF mimarileri.** Nyquist teoremi, aliasing,
Nyquist bölgeleri ve undersampling (2./3. bölge örnekleme — direct sampling'in
sırrı); superheterodyne → zero-IF → direct RF sampling evrimi, her mimarinin
artı/eksisi (D09); direct sampling'de bile analog ön ucun (LNA, filtre, balun,
DSA) neden ölmediği; frekans planlama ve folding (D10).

**Bölüm 2 — ADC/DAC kavramları.** Çözünürlük, kuantalama gürültüsü, ENOB,
SNR, SFDR, NSD, IMD3; clock jitter'inin SNR'ı nasıl katlettiği (formül +
gerçekçi GHz/fs örneği — clocking kısmının motivasyonu buradan doğar);
interleaved ADC mimarisi ve interleaving spur'ları; DAC tarafı: imajlar,
sinc roll-off, mix-mode, rekonstrüksiyon filtresi.

**Bölüm 3 — Dijital sinyal yolu.** DDC/DUC, decimation/interpolation, NCO,
kompleks (I/Q) veri; kanal başına veri hızı hesabı (çok kanallı bir AFE
senaryosuyla uçtan uca: örnekleme hızı → decimation → JESD hattı ihtiyacı);
paralel arayüzlerin (LVDS) neden duvara tosladığı ve JESD'in doğuşu (D05, D06).

### KISIM II — SERDES ve JESD204

**Bölüm 4 — SERDES temelleri.** Seri hat fiziği: diferansiyel CML, AC kuplaj,
empedans; embedded clock ve CDR; encoding'in varlık sebebi (DC balance,
transition density) — 8b/10b vs 64b/66b; kanal kayıpları ve eşitleme
(pre-emphasis, CTLE, DFE); eye diagram ve BER; FPGA GT anatomisi: quad,
kanal, refclk, LC/ring PLL kavramları (Versal'e §14'te dönülecek).

**Bölüm 5 — JESD204 standardı: A'dan C'ye.** Neden versiyonlar var; katman
modeli: transport / scrambling / data link / physical (D04); **link
parametreleri tek tek**: L, M, F, S, N, N', K, E, CS, CF, HD — her birinin
anlamı, birbirine bağı, seçim mantığı; uçtan uca örnek konfigürasyon hesabı
(line rate = f(M, N', S, L, encoding) türetilerek); subclass 0/1/2 ve
deterministic latency'nin hangi subclass'ta nasıl geldiği.

**Bölüm 6 — JESD204B derinlemesine.** SYNC~ sinyali; CGS (K28.5 akışı),
ILAS (4 multiframe yapısı, /A/ /F/ /K/ /R/ karakterleri) (W02); frame ve
multiframe, LMFC; RBD ve elastic buffer release; karakter tabanlı hizalama
ve character replacement; 8b/10b'nin bant genişliği vergisi.

**Bölüm 7 — JESD204C derinlemesine.** 64b/66b ve sync header stream;
block → multiblock → extended multiblock hiyerarşisi ve E parametresi (W03);
kilitlenme merdiveni: SH lock → EMB lock → EoEMB; LEMC (LMFC'nin C'deki
karşılığı); CRC-12 / FEC seçenekleri, command channel; SYNC~ pininin yokluğu
ve sonuçları; **B↔C kavram eşleme tablosu** (B bilenin C'ye köprüsü).

### KISIM III — CLOCKING ve SYSREF (dokümanın kalbi)

**Bölüm 8 — Clock kalitesi.** Faz gürültüsü grafiği okuma; integrated jitter
ve entegrasyon bandı seçimi; referans → PLL → dağıtım zinciri; dual-loop PLL
mimarisi (jitter cleaning) — LMK04832 ve HMC7044'ün ortak DNA'sı; clock chip
anatomisi: giriş seçici, PLL1 (temizlik), PLL2 (çarpma), çıkış bölücüler,
DCLK/SYSREF çifti kavramı.

**Bölüm 9 — SYSREF: neden var, nasıl çalışır.** Problem tanımı: iki cihazın
LMFC/LEMC sayaçları aynı anda başlamazsa ne olur; SYSREF'in tanımı: device
clock'a göre belirli setup/hold penceresinde örneklenen, LMFC/LEMC fazını
sıfırlayan sinyal (W01); frekans kuralı (LMFC/LEMC periyodunun tam böleni);
tipleri: continuous / gapped periodic / one-shot — hangisi ne zaman, sürekli
SYSREF'in kirlilik (coupling) riski; capture modları ve SYSREF windowing/
monitoring (AFE'lerin "SYSREF geç geldi/erken geldi" sayaçları); SYSREF'in
**hem AFE'ye hem FPGA'ya** gitmesinin sebebi.

**Bölüm 10 — Deterministic latency ve multi-device sync.** Neden: faz koherent
sistemler, beamforming, kanal eşleme; buffer release mekanizması adım adım
(W04); RBD seçimi; multi-chip senkronizasyon akışı (NCO reset dahil) (W05);
deterministic latency ≠ faz koherensi — kalibrasyonun hâlâ gerekli olduğu yer.

### KISIM IV — DONANIM ZİNCİRLERİ

**Bölüm 11 — TI zinciri: AFE7900 + LMK04832 + LMX1204 + Versal.**
AFE7900 kuşbakışı (public seviye): RF-sampling transceiver AFE — ADC/DAC
çekirdekleri, DSA, DDC/DUC, on-chip PLL, SerDes; LMK04832: dual PLL jitter
cleaner, 7 çift DCLK/SDCLK çıkışı, SYSREF üretim/dağıtımı; LMX1204: çok GHz
sınıfı clock distribution — device clock'un yüksek frekansta dağıtımı ve
SYSREF ile ilişkisi; **uçtan uca clock tree (D02)**: hangi çıkış hangi pine,
FPGA'ya giden üçlü (GT refclk / core clock / SYSREF) dahil; tipik frekans
planı örneği; gömülü yazılımcı için init sırası özeti.

**Bölüm 12 — ADI Apollo zinciri: AD9084 + HMC7044 + ADF4382 + Versal.**
AD9084 (Apollo MxFE) kuşbakışı (public seviye); HMC7044: dual PLL, 14 çıkış,
CLK/SYSREF çiftleri, RFSYNC kavramı; ADF4382: çok düşük jitter PLL/VCO —
yüksek frekans device clock üretimi; **uçtan uca clock tree (D03)**; TI
zinciriyle aynı şablonda anlatım (okuyucu ikisini üst üste koyabilsin).

**Bölüm 13 — İki zincirin karşılaştırması.** Rol eşleme tablosu:
LMK04832 ↔ HMC7044, LMX1204 ↔ ADF4382 (+dağıtım mimarisi farkları),
AFE7900 ↔ AD9084; kim device clock'u üretir, kim SYSREF'i, on-chip PLL ne
zaman kullanılır; aynı sistem gereksinimi iki zincirde nasıl karşılanır
(yan yana D02/D03 okuma rehberi).

### KISIM V — VERSAL ENTEGRASYONU

**Bölüm 14 — Versal GT ve JESD204C IP.** GTY/GTYP mimarisi, quad yapısı,
refclk yerleşim kuralları (aynı/komşu quad); AMD JESD204C IP kuşbakışı:
register arayüzü, core clock / link clock ilişkileri, SYSREF girişi (D07);
line rate → refclk → core clock hesabı örneği; IP konfigürasyon
parametrelerinin §5'teki link parametreleriyle eşlemesi.

**Bölüm 15 — Bring-up akışı (yazılımcının bölümü).** Uçtan uca sıra:
clock chip init → AFE init → FPGA GT reset sırası → link enable → SYSREF
tetikleme → doğrulama; her adımda "neye bakacaksın" (status register
kavramsal düzeyde); init state machine önerisi; sık yapılan sıra hataları.

**Bölüm 16 — Debug ve loopback.** Loopback türleri haritası (D08): FPGA
near-end PCS/PMA, far-end PCS/PMA, AFE dijital loopback noktaları — her biri
zincirin hangi parçasını test eder; IBERT ve eye scan; **semptom → sebep
tablosu**: SH lock yok / EMB lock var EoEMB yok / CGS'de takılı / ILAS hatası
/ CRC hataları artıyor / link geliyor ama veri kayık / sıcaklıkla düşen link;
SYSREF kaynaklı kaymaların teşhisi; saha vakaları (sync header lock ve GT
reset sırası vakası anonimleştirilmiş ders olarak) (M02 karar ağacı).

### KISIM VI — KAPANIŞ

**Bölüm 17 — Sistem tasarım kontrol listesi.** Frekans planı, jitter bütçesi,
SYSREF stratejisi, link parametre seçimi, reset sırası — tek sayfalık
uygulanabilir checklist.

**Bölüm 18 — Sözlük.** Tüm kısaltmalar ve terimler, alfabetik, tek cümlelik
tanımlarla; her madde ilgili bölüme link verir.

**Bölüm 19 — Kaynakça ve okuma yolu.** Aşağıdaki §8 kaynak listesinin
doğrulanmış hali + "buradan sonra ne okumalı" rehberi.

---

## 7. Şema Envanteri

| ID | Araç | Bölüm | İçerik |
|---|---|---|---|
| D01 | SVG | 0 | Antenden bit'e sistem genel blok şeması (AFE → JESD → Versal → yazılım) |
| D02 | SVG | 11 | TI zinciri clock tree: LMK04832 + LMX1204 + AFE7900 + Versal, pin adlarıyla |
| D03 | SVG | 12 | ADI zinciri clock tree: HMC7044 + ADF4382 + AD9084 + Versal, pin adlarıyla |
| D04 | SVG | 5 | JESD204 katman modeli (transport/link/physical, TX↔RX ayna yapısı) |
| D05 | SVG | 3 | ADC yolu: analog giriş → ADC core → DDC/NCO → transport → SerDes |
| D06 | SVG | 3 | DAC yolu (D05'in aynası) |
| D07 | SVG | 14 | Versal GT quad/refclk yapısı + JESD IP clock bağlantıları |
| D08 | SVG | 16 | Loopback noktaları haritası (zincir üzerinde numaralı test noktaları) |
| D09 | SVG | 1 | Superheterodyne vs zero-IF vs direct sampling mimari karşılaştırma |
| D10 | SVG | 1 | Nyquist bölgeleri ve spektrum folding |
| W01 | WaveDrom | 9 | SYSREF–device clock setup/hold ve LMFC/LEMC faz reset'i |
| W02 | WaveDrom | 6 | JESD204B CGS → ILAS → data geçişi |
| W03 | WaveDrom | 7 | JESD204C sync header stream, block/multiblock/EMB yapısı |
| W04 | WaveDrom | 10 | Elastic buffer release ve deterministic latency |
| W05 | WaveDrom | 10 | Multi-device sync: iki AFE'nin LEMC hizalanması |
| M01 | Mermaid | 6–7 | Link bring-up state machine (B ve C ayrı) |
| M02 | Mermaid | 16 | Debug karar ağacı (semptomdan teste) |

Renk kodu (tüm şemalarda sabit): device clock yolları = vurgu-1,
SYSREF yolları = vurgu-2, veri (SerDes) = nötr kalın, kontrol (SPI vb.) = kesikli.

---

## 8. Kaynak Listesi (üretim sırasında web'den doğrulanacak)

- JEDEC JESD204B / JESD204C standart dokümanları
- TI: LMK04832 datasheet, LMX1204 datasheet, AFE79xx public ürün sayfası ve
  app note'ları, TI'ın JESD204B/C eğitim serisi (Precision Labs / app notes)
- ADI: HMC7044 datasheet, ADF4382 datasheet, AD9084 (Apollo MxFE) public
  sayfası ve mevcut UG'ler, ADI MxFE / JESD204 app note'ları (AN-...)
- AMD/Xilinx: Versal GTY/GTYP Transceivers Architecture Manual, JESD204C
  LogiCORE IP Product Guide, ilgili clocking UG'leri
  `[DOĞRULA: tüm AM/PG/UG numaraları ilk kullanımda web'den teyit edilecek]`
- NDA malzeme (dokümana girmez, PAŞA NOTU olarak işaretlenir): AFE7900 tam
  datasheet, AD9084 detay dokümantasyonu

---

## 9. Üretim Fazları (Claude Code çalışma sırası)

- **Faz 0 — İskelet:** repo yapısı, package.json, build.mjs, page.html
  şablonu (frontend-design skill ile), boş bölüm dosyaları başlık iskeletiyle.
  Build'in uçtan uca çalıştığı kanıtlanır (dummy içerik + 1 örnek SVG +
  1 örnek WaveDrom + 1 örnek Mermaid render edilir). **Önce boru hattı.**
- **Faz 1 — Temeller:** Bölüm 0–3 + D01, D05, D06, D09, D10.
- **Faz 2 — JESD:** Bölüm 4–7 + D04, W02, W03, M01.
- **Faz 3 — Clocking/SYSREF:** Bölüm 8–10 + W01, W04, W05. (En kritik faz;
  timing diyagramları datasheet doğrulamasından sonra çizilir.)
- **Faz 4 — Donanım zincirleri:** Bölüm 11–13 + D02, D03. (Pin adları
  datasheet'ten birebir; NDA boşlukları PAŞA NOTU ile.)
- **Faz 5 — Versal + saha:** Bölüm 14–16 + D07, D08, M02.
- **Faz 6 — Kapanış ve cila:** Bölüm 17–19, çapraz linkler, şekil
  numaralarının denetimi, sözlük taraması, tipografi/tema son geçişi,
  print CSS kontrolü.

Her faz sonunda: build çalışır durumda + `[DOĞRULA]` etiketleri sıfırlanmış
+ git commit. Bir sonraki faza geçmeden mevcut faz okunabilir olmalı.

## 10. Definition of Done

- [ ] `npm run build` tek komutla `dist/index.html` üretiyor
- [ ] HTML self-contained: dış istek yok, system font, tek dosya
- [ ] Tüm 17 şema render ediliyor, açık/koyu temada okunuyor
- [ ] Hiç `[DOĞRULA]` etiketi kalmadı; NDA boşlukları PAŞA NOTU olarak açık
- [ ] Sıfır bilgiyle başlayan bir gömülü yazılımcı Bölüm 0'dan 16'ya
      kopmadan ilerleyebiliyor (her kavram kullanımından önce tanımlı)
- [ ] Sözlükteki her terim metinde geçiyor ve linkli
- [ ] Print CSS ile makul bir PDF çıkıyor
