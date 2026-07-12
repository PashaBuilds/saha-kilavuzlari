# Bölüm 19 — Kaynakça ve Okuma Yolu

Bu dokümandaki her sayısal değer, pin adı ve protokol ayrıntısı üretim
sırasında aşağıdaki public kaynaklardan doğrulanmıştır. Doküman
çevrimdışı kullanım için tasarlandığından adresler tıklanabilir link
değil düz metin olarak verilir. Bölüm sonundaki "okuma yolu", bu
kılavuzdan sonra nereye derinleşeceğini önerir.

## Standartlar

- JEDEC, **JESD204B** (2011) ve **JESD204C** (2017) — standart metinleri
  JEDEC sitesinden (ücretsiz üyelikle) indirilir: `jedec.org`.
  Tarihçe: JESD204 (2006), 204A (2008), 204B (2011), 204C (2017),
  204D (2023).

## Texas Instruments

- **SBAA517** — *JESD204B/C overview*: sürüm farkları, kodlama ek
  yükleri, parametreler. `ti.com/lit/pdf/sbaa517`
- **SLAP160** — *JESD204B Transport and Data Link Layers* (eğitim
  slaytları): CGS/ILAS, 4×/K/ kuralı, character replacement.
  `ti.com/lit/ml/slap160/slap160.pdf`
- **SBAA402** — sync header, CRC/FEC/komut kanalı, scrambler dereceleri.
  `ti.com/lit/pdf/sbaa402`
- **SBAA543** — *Determining Optimal Receive Buffer Delay*: RBD yöntemi.
  `ti.com/lit/pdf/SBAA543`
- **SLYT628** — çok converter'lı senkronizasyon: SYSREF şartları, tam
  bölen kuralı. `ti.com/lit/an/slyt628/slyt628.pdf`
- **SBAA221** — ADC32RF45 SYSREF uygulaması: düşük frekans + susturma
  politikası. `ti.com/lit/pdf/sbaa221`
- **SLYT379** — *Clock jitter analyzed in the time domain*: jitter–SNR.
  `ti.com/lit/pdf/slyt379`
- **SLAA824** — RF ADC spur analizi (interleaving aileleri).
  `ti.com/lit/pdf/slaa824`
- **SLAA523** — DAC temelleri: imajlar, sinc. `ti.com/lit/pdf/slaa523`
- **SLYY068** — *Direct RF conversion* beyaz bülteni: mimari evrim, ön
  uç. `ti.com/lit/pdf/slyy068`
- **SBAA625** — *Noise Spectral Density: A Better Way*: NSD/ENOB.
  `ti.com/lit/SBAA625`
- **SBAA677** — RF ADC ön uç mimarileri (balun). `ti.com/lit/pdf/sbaa677`
- **LMK04832 datasheet (SNAS688)** — `ti.com/lit/ds/symlink/lmk04832.pdf`
- **LMX1204 datasheet (SNAS800)** — `ti.com/lit/ds/symlink/lmx1204.pdf`
- **AFE7900 ürün sayfası + kısaltılmış datasheet (SBASA44)** —
  `ti.com/product/AFE7900`
- **TIDUEZ6 (TIDA-010230)** — iki AFE7950'nin <10 ps senkronu.
  `ti.com/lit/pdf/tiduez6`
- **SBAU338** — AFE79xxEVM kılavuzu. `ti.com/lit/pdf/sbau338`

## Analog Devices

- **MT-001 / MT-002 / MT-003 / MT-008** — Kester tutorial'ları:
  kuantalama, Nyquist bölgeleri, ENOB/SINAD, faz gürültüsü→jitter.
  `analog.com/media/en/training-seminars/tutorials/MT-00x.pdf`
- **JESD204C Primer (Analog Dialogue, 2 kısım)** — 204C yapısı: blok/
  multiblock/EMB, sync word, kilitlenme.
  `analog.com/en/resources/analog-dialogue/articles/jesd204c-primer-part1.html`
- **JESD204B subclass makale serisi** — deterministic latency ve
  subclass'lar. `analog.com/en/resources/technical-articles/...`
- **MS-2374** — *What is JESD204...*: ailenin doğuşu.
- **MS-2448** — *Critical Design Issues...*: character replacement,
  0xFC/0x7C.
- **JESD204B vs Serial LVDS** — LVDS ~1 Gb/s pratik sınırı.
- **The ABCs of Interleaved ADCs** — interleaving spur'ları.
- **Where Zero-IF Wins** — zero-IF kusur/avantajları.
- **HMC7044 datasheet** —
  `analog.com/media/en/technical-documentation/data-sheets/hmc7044.pdf`
- **ADF4382 datasheet** — `analog.com/.../adf4382.pdf`
- **AD9084 ürün sayfası, datasheet ve AD9084/AD9088 Device UG** —
  `analog.com/en/products/ad9084.html`
- **UG-2326** — EVAL-AD9084 kılavuzu (clock ağacı Fig. 8).
- **Quad-MxFE MCS wiki** — one-shot sync + NCO master-slave.
  `wiki.analog.com/resources/eval/user-guides/quadmxfe/multichipsynchronization`
- **Power-Up Phase Determinism...** — DL ≠ faz koherensi.
- **Quad-Apollo MxFE Reference Design** — ADF4030/BSYNC yaklaşımı.

## AMD / Xilinx

- **AM002** — *Versal Adaptive SoC GTY and GTYP Transceivers Architecture
  Manual*: quad/HSCLK, refclk kuralları, loopback, eye scan.
  `docs.amd.com/r/en-US/am002-versal-gty-transceivers`
- **PG242** — *JESD204C LogiCORE IP Product Guide*: clocking, SYSREF,
  register arayüzü. `docs.amd.com/r/en-US/pg242-jesd204c`
- **PG331** — *Versal Adaptive SoC Transceivers Wizard*.
- **PG066 / PG198** — JESD204(B) IP + JESD204 PHY (UltraScale kuşağı).
- **UG908** — *Vivado Programming and Debugging*: IBERT / Serial I/O
  Analyzer.
- **PG269** — RF Data Converter (mix-mode/Nyquist bölgesi anlatımı).

## Diğer

- B. Razavi, *Design Considerations for Direct-Conversion Receivers*,
  IEEE TCAS-II, 1997 — zero-IF kusurlarının klasik analizi.
- chipinterfaces.com JESD204B/C özetleri; EDN *Understanding JESD204B
  link parameters*; DSPRelated ZOH yazısı (−3.92 dB); Wikipedia 8b/10b
  ve 64b/66b maddeleri (kod tabloları, scrambler polinomları).

## Okuma yolu: buradan sonra ne?

1. **Standardın kendisi**: bu kılavuz JESD204C'nin haritasını verdi;
   sıradaki adım, JEDEC metnini elinde bu haritayla okumaktır — artık
   hangi bölümün ne işe yaradığını bilerek gezinirsin.
2. **Kendi zincirinin dokümanları**: {{sec:11}}–{{sec:12}}'deki
   datasheet'leri ve (erişimin varsa) NDA'lı programlama kılavuzlarını,
   {{sec:15}}'teki akış sırasına paralel oku.
3. **AMD tarafında derinlik**: AM002'nin eşitleme/eye scan bölümleri ve
   PG242'nin register haritası; IBERT ile bir kartta pratik yap.
4. **Clocking ustalığı**: TI'ın clock eğitim serileri ve ADI'nin MT
   tutorial'ları; ardından kendi kartının faz gürültüsünü ölçüp bütçeyle
   karşılaştır — teori, ölçümle kapanır.
5. **Ufuk**: JESD204D (2023): 116 Gb/s'ye PAM4 ile — bir sonraki neslin
   dili şimdiden şekilleniyor.
