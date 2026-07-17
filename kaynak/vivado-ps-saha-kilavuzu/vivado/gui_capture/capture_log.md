# capture_log.md — GUI yakalama tekrar üretim reçetesi

Her kare, aşağıdaki döngüyle alındı ve alındıktan sonra Claude Code
tarafından **görsel olarak doğrulandı** (doğru sekme/diyalog açık mı,
beklenen değer görünüyor mu, beklenmedik popup var mı):

```
Tcl ile sahnele → computer use ile son adımı at → gör-doğrula → yakala
```

**Ortak araçlar:**
- `capture_shot.ps1 -Out shot-NN.png [-Title "..."] [-Ekran]` — Claude
  penceresini küçültür, `PrintWindow` ile pencere yüzeyini alır (üstteki
  pencereler görüntüyü kirletemez), `kucult.py` ile indirger.
  - `-Title "Re-customize IP"` / `"Configure PS PMC"`: **diyalog penceresinin
    kendisini** yakalar (tam pencere yerine yalnız diyalog → daha büyük,
    daha okunur kare). Re-customize/CIPS/NoC diyalog kareleri böyle alındı.
  - `-Ekran`: geçici popup'ları da (örn. Diagram arama kutusu) içeren
    ekran-kopyası yolu.
- Kaydetme soran her popup'ta **kaydetme / Cancel / Don't Save** seçildi;
  hiçbir proje değişikliği diske yazılmadı.

**Görsel son-işlem** (`build/gorsel_hatti.py`): yakalamadan sonra
`duzelt_bd` (BD SVG'lerinin 90° yan yatmasını düzeltir), `crop_bd`
(PS/CIPS kırpımları), `annotate` (numaralı rozet katmanları) sırayla koşar.
Rozet yerleşimi `build/qc_shots.py` ile üretilen kompozitlerde gözle
doğrulandı.

**Oturum 1 — demo_ultrascale (ZCU102):**
`vivado -mode tcl -source vivado/gui_capture/stage_us_open.tcl`

| Kare | Sahne / eylem | Doğrulanan içerik |
|---|---|---|
| shot-01 | Proje+BD açık, ana pencere | Flow Navigator + Sources + Diagram, 9 IP |
| shot-02 | Sources sekmesi öne | sistem_wrapper → sistem.bd hiyerarşisi |
| shot-04 | Diagram, Zoom Fit | Tüm BD tek karede |
| shot-05 | irq_concat→pl_ps_irq0 netine tık | `irq_concat_dout` neti seçili (turuncu) |
| shot-06 | Ctrl+F (Diagram) → "uart" | 7 eşleşme, arama kutusu |
| shot-07 | axi_gpio_led bloğuna tık | Block Properties: axi_gpio_led |
| shot-08 | ps_ultra çift tık | Re-customize IP, Page Navigator |
| shot-09 | I/O Configuration | MIO tablosu, bank gerilimleri (LVCMOS18) |
| shot-10 | Low Speed→I/O Periph→UART | UART0=MIO18, UART1=MIO20 |
| shot-11 | Clock→Input Clocks | PSS_REF_CLK 33.330 MHz |
| shot-12 | Clock→Output→LPD→Periph/IO | UART0/1 Actual 99.990005 MHz |
| shot-13 | Clock→Output→PL Fabric | PL0 açık, IOPLL, 99.990005 MHz |
| shot-14 | DDR Configuration | DDR4, 64bit, ECC Disabled, 2133P, 4GB |
| shot-15 | PS-PL→Master Interface | HPM0 FPD açık, HPM1/LPD kapalı |
| shot-16 | PS-PL→General→Interrupts→PL to PS | IRQ0=1, IRQ1=0 |
| shot-17 | Address Editor sekmesi | 4 segment: GPIO/Timer/Uartlite/BRAM |
| shot-18 | F6 → Rerun Validate | "Validation successful" diyaloğu |
| shot-19 | File→Export→Export Hardware | Export Hardware Platform sihirbazı |
| shot-20 | Sihirbaz Next → Output | Pre-synthesis / Include bitstream |
| shot-29 | close_project → Start Page | Quick Start / Recent Projects |

BD layout SVG/PDF export'u da bu oturumda GUI Tcl konsolundan alındı
(`write_bd_layout` batch modda çalışmaz):
`assets/bd-exports/ultrascale-bd-full.{svg,pdf}`.

**Oturum 2 — demo_versal (VCK190):**
Aynı GUI'de `source ~/vopen.tcl` ile proje değiştirildi
(`open_project demo_versal + open_bd_design`).

| Kare | Sahne / eylem | Doğrulanan içerik |
|---|---|---|
| shot-21 | Diagram, Zoom Fit | CIPS + NoC + DDR4 + GPIO/Timer yolları |
| shot-22 | versal_cips_0 çift tık | CIPS Re-customize, Board/Clock/IO satırları |
| shot-25 | axi_noc_0 çift tık → General | 6 slave (NMU), 1 master (NSU), Single MC |
| shot-26 | NoC → DDR Basic | DDR4 SDRAM, 625ps=1600MHz, differential |
| shot-27 | Address Editor sekmesi | DDR NoC arkasında, timer 0x201_0000_0000 |
| shot-28 | FPD_CCI_NOC_0 netine tık | CIPS→NoC S00_AXI bağlantısı seçili |

BD layout SVG/PDF: `assets/bd-exports/versal-bd-full.{svg,pdf}`
(GUI konsolundan `source ~/vlay2.tcl`).

**Alınamayan kareler:** shot-23, shot-24 → `SHOT-LIST.md`.
Her ikisinin de sayısal verisi `assets/reports/versal-ps-pmc-config.txt`'te
mevcut ve Bölüm 8'de işlendi.

**Katman A kırpımları** (`build/crop_bd.py`): tam BD SVG'leri viewBox ile
kırpılarak `ultrascale-bd-ps.svg` (PS-yakın) ve `versal-bd-cips.svg`
(CIPS/NoC-yakın) üretildi.
