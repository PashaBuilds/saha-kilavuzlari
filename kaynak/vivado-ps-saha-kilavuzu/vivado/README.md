# vivado/ — Demo Proje Üretim Hattı

Bu dizin, kılavuzdaki TÜM gerçek görsellerin ve raporların tek kaynağıdır.
Projeler yalnızca Tcl ile kurulur; GUI'de elle kurulum ve **kayıt yoktur**.
`vivado/work/` altındaki her şey türetilmiş çıktıdır, silinip yeniden
üretilebilir.

## Gereksinimler

- Vivado **2022.2** (bu repo bu sürümle koşulup doğrulanmıştır; KICKOFF'un
  baz aldığı 2023.2 makinede yoksa kavramsal fark yoktur, sürüm notu
  dokümanda düşülüdür).
- Board part'lar: `ZCU111` (yoksa script `ZCU102`'ye düşer) ve `VPK120`
  (yoksa `VCK190`'a düşer). Bu makinede ZCU102 + VCK190 kullanılmıştır.

### Board file eksikse (air-gap kurulumu)

1. İnternetli bir makinede <https://github.com/Xilinx/XilinxBoardStore>
   deposundan ilgili kartın klasörünü indirin
   (`boards/Xilinx/<kart>/`).
2. Klasörü hedef makinede şu yola kopyalayın:
   `<Vivado>\data\boards\board_files\<kart>\<sürüm>\`
3. Vivado'yu yeniden başlatın; `get_board_parts *<kart>*` ile doğrulayın.

Hiçbir board file yoksa: `create_bd.tcl` içindeki board seçim bloğunu
part-only kuruluma çevirin (`create_project ... -part xczu9eg-ffvb1156-2-e`
ve `apply_board_preset` satırını kaldırın); PS preset'i elle vermek
gerekir, kılavuzun board preset anlatımı yine geçerli kalır.

## Koşum sırası

```bat
:: 1) Demo 1 — UltraScale+ PS (ZCU111 -> ZCU102 yedekli)
vivado -mode batch -source vivado\rfsoc\create_bd.tcl

:: 2) Demo 2 — Versal CIPS + NoC + DDRMC (VPK120 -> VCK190 yedekli)
vivado -mode batch -source vivado\versal\create_bd.tcl

:: 3) Demo 3 — MicroBlaze soft-core (AC701; WebPACK lisansiyla kosar)
vivado -mode batch -source vivado\microblaze\create_bd.tcl

:: 4) Katman A exportlari: BD SVG/PDF + raporlar + pre-synth XSA
vivado -mode batch -source vivado\export_visuals.tcl

:: 5) (yalniz Demo 3) implementasyon + bitstream + MMI + kaynak raporu
vivado -mode batch -source vivado\microblaze\impl_bitstream.tcl
```

Çıktılar:

| Yol | İçerik |
|---|---|
| `vivado/work/demo_ultrascale/` | Demo 1 projesi (`sistem` BD) + `ultrascale-demo.xsa` |
| `vivado/work/demo_versal/` | Demo 2 projesi (`sistem` BD) + `versal-demo.xsa` |
| `assets/bd-exports/*.svg` | `write_bd_layout` BD görselleri |
| `assets/reports/*-adres-haritasi.md` | Gerçek adres haritaları |
| `assets/reports/*-ps-config-*.{txt,md}` | PS/CIPS gerçek CONFIG dökümleri |
| `assets/reports/*-hucreler.md` | IP envanterleri |

## GUI yakalama (gui_capture/)

- `shots.yaml` — kare manifesti: her karenin Tcl sahneleme durumu,
  GUI eylemi, doğrulama kriteri.
- `stage_*.tcl` — `vivado -mode tcl` oturumunda `source` edilen sahneleme
  scriptleri; GUI'de gezinmeyi minimuma indirir.
- `capture_log.md` — alınan her karenin tekrar üretim reçetesi.

Prensip: *Tcl ile duruma getir, GUI'de yalnızca son adımı at, her karede
gör-doğrula.* Kaydetme soran her popup'ta **kaydetme** seçilir; projeler
scriptten yeniden üretilebilir kalır.
