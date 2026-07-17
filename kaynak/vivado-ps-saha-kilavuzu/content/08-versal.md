# Bölüm 8 — Versal: Yeni Dünya, Yeni Sözlük

## Neden umursamalısın

Masana bir Versal projesi geldiğinde MPSoC refleksierin seni iki yerde
yanıltır: PS IP'si diye bir kutu arayacaksın (adı değişti) ve DDR ayarını
onun içinde arayacaksın (yeri değişti). Bu bölüm sözlüğü günceller; demo
olarak VCK190 üzerine kurduğumuz gerçek projeyi (CIPS + NoC + DDRMC + iki
PL IP'si) okuyarak ilerler.

## Mimari fark: tek kutudan üç aktöre

[[sema: sema-10-versal-fark | Şema 10 — Solda MPSoC: DDR denetleyicili tek PS kutusu. Sağda Versal: CIPS + NoC omurgası + NoC'a taşınmış DDRMC; AI Engine ayrı bölge.]]

Üç isim değişikliğini sindirdiğinde gerisi tanıdıktır:

| MPSoC dünyası | Versal dünyası | Ne değişti |
|---|---|---|
| `zynq_ultra_ps_e` (PS IP) | **CIPS** (`versal_cips`) | İşlemciler + PMC (Platform Management Controller — boot/güvenlik yöneticisi) tek IP'de |
| PS içindeki DDR denetleyici | **DDRMC** (NoC içinde) | DDR artık PS'in değil, çipin ortak kaynağı |
| AXI Interconnect/SmartConnect omurgası | **NoC** (`axi_noc`) | Yüksek bant trafiği silikonda hazır ağa taşındı |
| bitstream | **PDI** (Programmable Device Image) | Tek imaj: boot + PL + NoC konfigürasyonu birlikte |

## Demo dizaynda rehberli tur

[[bd: versal-bd-full | Demo 2 blok dizaynı (VCK190, gerçek `write_bd_layout` export'u). CIPS'ten NoC'a giden çoklu arayüzler, NoC'un DDR4 çıkışı, GPIO'nun doğrudan (M_AXI_FPD → axi_smc), timer'ın NoC üzerinden (M00_AXI → smc_noc) yolu.]]

CIPS/NoC-yakın kırpım — dersin can alıcı bölgesi: CIPS'in altı arayüzü
(`FPD_CCI_NOC_0..3`, `LPD_AXI_NOC_0`, `PMC_NOC_AXI_0`) NoC'a girer, NoC'un
`CH0_DDR4_0` çıkışı DDR'a gider:

[[bd: versal-bd-cips | CIPS/NoC-yakın kırpım: versal_cips_0'ın NoC'a giden yüksek bant kapıları ve axi_noc_0. DDR artık bu ağın arkasında.]]

Aynı dizayn Vivado penceresinde:

[[ekran: 21 | Versal Diagram — sistem BD tam görünüm (GUI çerçevesiyle)
rozet 1: versal_cips_0 — CIPS bloğu; NoC'a giden altı yüksek bant kapısı sağ kenarında.
rozet 2: axi_noc_0 — NoC; S00..S05 girişleri CIPS'ten, M00_AXI çıkışı timer'a.
rozet 3: CH0_DDR4_0 → ddr4_dimm1 — DDR'ın NoC arkasındaki fiziksel çıkış yolu.
]]

Dizaynın hücre envanteri (rapordan): `versal_cips_0`, `axi_noc_0`,
`axi_smc`, `smc_noc`, `axi_gpio_led`, `axi_timer_0`, `rst_versal_cips_0_333M`.
Okuma sırası MPSoC'takiyle aynı dört adım; farklar şunlar:

1. **CIPS'i bul** — en büyük kutu yine o; ama kenarındaki arayüz sayısı
   şaşırtabilir: `FPD_CCI_NOC_0..3`, `LPD_AXI_NOC_0`, `PMC_NOC_AXI_0` —
   hepsi NoC'a giden yüksek bant kapıları.
2. **NoC'u bul** — `axi_noc_0`. DDR4 arayüzü (`CH0_DDR4_0`) ve kartın
   DIMM saat girişi (`ddr4_dimm1_sma_clk`) doğrudan bu kutudan çıkar:
   **DDR'ın yeni evi.**
3. **PL IP'lerine giden iki yolu ayırt et** — bu dizaynı bilerek iki farklı
   yolla kabloladık:
   - `axi_gpio_led`: CIPS `M_AXI_FPD` → `axi_smc` → GPIO (MPSoC'tan tanıdık
     doğrudan yol).
   - `axi_timer_0`: CIPS → NoC (`S00_AXI`) → NoC `M00_AXI` (NSU) →
     `smc_noc` → Timer (**NoC üzerinden PL erişimi**).
4. **İnce teller** — `pl0_ref_clk` (333.333 MHz — MPSoC'taki 100 MHz
   alışkanlığına dikkat) ve timer'ın interrupt'ı doğrudan CIPS `pl_ps_irq0`
   girişinde.

## Adres haritasında NoC'un izi

Gerçek harita (rapordan, kısaltılmış):

| Master uzayı | Segment | Base | Aralık |
|---|---|---|---|
| `/versal_cips_0/M_AXI_FPD` | `SEG_axi_gpio_led_Reg` | `0xA400_0000` | 64K |
| `/versal_cips_0/FPD_CCI_NOC_0` | `SEG_axi_timer_0_Reg` | `0x201_0000_0000` | 64K |
| `/versal_cips_0/FPD_CCI_NOC_0` | `SEG..._DDR_LOW0` | `0x0000_0000` | 2G |
| `/versal_cips_0/FPD_CCI_NOC_0` | `SEG..._DDR_LOW1` | `0x8_0000_0000` | 6G |

İki ders: (1) doğrudan yoldaki GPIO, MPSoC'takine benzer bir bölgede
(0xA400_0000) otururken NoC arkasındaki timer 44-bit bölgeye
(0x201_0000_0000) düştü — NoC'a taşınan PL slave'leri fiziksel adres
uzayının yukarısında yaşayabilir; 32-bit adres varsayımı yapan eski kod
kalıpları burada kırılır. (2) VCK190'ın 8 GB DIMM'i tek parça değildir:
2 GB `DDR_LOW0` (0x0) + 6 GB `DDR_LOW1` (0x8_0000_0000) — linker script
ve device tree bu iki bölgeyi ayrı tanır.

## CIPS'in içi: yazılımcının sayfaları

[[adim: versal_cips_0 çift tık → PS PMC bölümü]]

CIPS diyaloğu MPSoC PS'inden daha katmanlıdır (ve daha yavaş açılır —
sabır). Yazılımcının durakları aynı mantıkla adlanır:

- **I/O peripherals** — MIO'nun Versal hâli: pinler `PMC_MIO 0-51` ve
  `PS_MIO 0-25` diye iki havuza bölündü. Demo projede (VCK190 preset):
  UART0 **PMC_MIO 42..43**, I2C1 44..45, SD1 26..36, QSPI 0..12 (dual
  parallel), ENET0/1 PS_MIO 0..11 / 12..23.
- **Clocking** — kaynak `PMC_REF_CLK = 33.3333 MHz`; PL'e giden
  `pl0_ref_clk` demo projede **333.333 MHz**.
- **Interrupts** — `PS_IRQ_USAGE` altında CH0..CH15; demo projede yalnız
  CH0 açık (timer'ın teli).

[[ekran: 22 | CIPS Re-customize — açılış (Presets sayfası)
rozet 1: Board Interface — "ps pmc fixed io": kartın hazır ayar paketi (board preset'in Versal hâli).
rozet 2: Clock Settings / Connectivity to MC via NoC / I/O Peripherals — yazılımcıyı ilgilendiren preset satırları; ayrıntıya Next ile PS PMC yapılandırmasından inilir.
]]

[[ekran: 23 | CIPS — I/O peripherals, UART0 satırı
rozet 1: UART0 etkin, PMC MIO 42..43 — Versal'de konsolun fiziksel adresi.
rozet 2: PMC_MIO / PS_MIO ayrımı — iki pin havuzu tek tabloda.
]]

[[ekran: 24 | CIPS — Clocking, PL clock
rozet 1: PL CLK 0 — etkin PL fabric saati (kaynak NPLL, istek 350 MHz); PL1-3 kapalı.
rozet 2: Actual Frequency — 333.333008 MHz: timer ve PL IP hesaplarının gerçek girdisi; istekle karıştırma.
]]

## NoC ekranı: connectivity ve DDRMC

[[adim: axi_noc_0 çift tık → General / Connectivity / DDR Basic]]

NoC diyaloğunun yazılımcıya konuşan üç sekmesi:

- **General** — kaç AXI slave (NMU: NoC Master Unit — ağa *giriş*
  turnikesi), kaç AXI master (NSU: NoC Slave Unit — ağdan *çıkış* kapısı)
  ve kaç DDR denetleyicisi (MC) yapılandırılmış.
- **Connectivity** — hangi girişin hangi çıkışa sefer yapabildiği matrisi.
  Timer'a giden yolun "var olması", bu matriste S00→M00 kesişiminin işaretli
  olması demek.
- **DDR Basic/Advanced** — DDRMC parametreleri; MPSoC'un DDR Configuration
  sayfasının taşındığı yer. Demo projede denetleyici kartın `ddr4_dimm1`
  arayüzüne bağlı.

[[ekran: 25 | NoC — General sekmesi
rozet 1: AXI slave/master port sayıları — NMU/NSU envanteri.
rozet 2: Memory Controllers — Single Memory Controller: DDRMC burada yaşıyor.
]]

[[ekran: 26 | NoC — DDR yapılandırması
rozet 1: Controller Type — DDR4 SDRAM: MPSoC'ta PS içinde duran ayar artık NoC'un DDR Basic sekmesinde.
rozet 2: Clocking — Memory Clock 625 ps = 1600 MHz; kartın 200 MHz differential sistem saatiyle beslenir.
]]

[[ekran: 27 | Versal Address Editor — NoC'un izi
rozet 1: DDR_LOW0/LOW1 segmentleri — 2G + 6G, NoC üzerinden.
rozet 2: axi_timer satırı — 0x201_0000_0000: NoC arkasındaki PL slave'in yüksek adresi.
]]

Blok dizaynda CIPS'in NoC'a giden altı kapısını seçip vurgulayabilirsin —
bu, "CIPS ile NoC nasıl konuşuyor" sorusunun görsel cevabıdır:

[[ekran: 28 | Versal — CIPS↔NoC bağlantısı seçili
rozet 1: FPD_CCI_NOC_0 arayüz neti — CIPS'ten NoC S00_AXI'ye giden yol, seçim renginde.
rozet 2: Interface Connection listesi — FPD_CCI_NOC_0..3, LPD_AXI_NOC_0, PMC_NOC_AXI_0: CIPS'in tüm NoC kapıları.
]]

[[sema: sema-11-noc-sezgisi | Şema 11 — NoC'un metro benzetmesi: hatlar silikonda döşeli; NMU turnikeden girer, NSU kapısından çıkarsın. Hangi seferin var olduğunu connectivity matrisi belirler.]]

:::analoji
SmartConnect kiralık minibüstür: donanımcı PL dokusundan istediği kadar
kurar, esnek ama PL kaynağı harcar. NoC şehir metrosudur: hatlar silikonda
hazır döşelidir, PL harcamaz, yüksek bant taşır; ama sefer tarifesini
(connectivity + QoS) önceden yazmak zorundasın. Demo dizaynda ikisi yan
yana: GPIO minibüsle, timer metroyla gidiyor.
:::

## PDI ve AI Engine'e pencere

Versal'de "bitstream yükledim" cümlesi teknik olarak eksiktir: PL
konfigürasyonu, boot bileşenleri ve NoC ayarlarıyla birlikte **PDI** adlı
tek imajın içinde taşınır; PMC bu imajı aşama aşama yükler. Yazılımcıya
düşen fark: boot zinciri tartışmalarında `BOOT.BIN`'in içinde artık PDI
konuştuğunu bilmek. AI Engine dizileri ise bu kılavuzun tamamen dışında —
blok dizaynda `ai_engine` kutusu görürsen bil ki o dünyanın kendi derleyicisi
ve kendi kılavuzu var; PS analizini değiştirmez.

:::yazilima-yansimasi
Versal'e geçişin yazılım faturası üç kalemdir: (1) UART driver'ın PS değil
PMC MIO'dan çıktığını device tree/BSP zaten bilir ama senin şematik-pin
eşleştirme reflekslerin PMC_MIO tablosuna güncellenmelidir; (2) NoC
arkasındaki IP'ler 32-bit üstü adres alabilir — `uintptr_t` kullanmayan,
`u32` adres taşıyan eski yardımcı fonksiyonlar derlenip yanlış çalışır;
(3) timer/PL IP clock'u artık 100 MHz varsayılamaz — demo projede
`XPAR_AXI_TIMER_0_CLOCK_FREQ_HZ` 333333008'dir; sabit yazılmış her
gecikme hesabı 3.3 kat şaşar.
:::

:::deneme id=deneme-8-1
**Hedef:** "DDR'ı CIPS'te arama" refleksini kır.

[[adim: Open Block Design → axi_noc_0 çift tık → DDR sekmeleri]]

Demo 2'de önce CIPS diyaloğunu aç ve DDR ayarı ara (bulamayacaksın —
`DDR_MEMORY_MODE = Connectivity to DDR via NOC` satırı dışında). Sonra
NoC diyaloğunu aç: DDR denetleyicisi hangi sekmede ve kartın hangi board
arayüzüne bağlı?

::cozum::
NoC diyaloğunda DDR Basic (ve Advanced) sekmeleri; denetleyici `ddr4_dimm1`
board arayüzüne bağlı (raporda `CH0_DDR4_0_BOARD_INTERFACE = ddr4_dimm1`).
CIPS yalnızca "DDR'a NoC üzerinden bağlanılacak" beyanını taşır. Refleks
güncellendi: Versal'de bellek sorusu = NoC sorusu.
:::

:::ozet
- Sözlük: PS IP → CIPS, DDR denetleyici → NoC içindeki DDRMC,
  bitstream → PDI.
- PL IP'ye iki yol var: M_AXI_FPD (doğrudan) ve NoC NSU (yüksek adres
  bölgesine düşebilir — demo'da 0x201_0000_0000).
- MIO artık iki havuz: PMC_MIO ve PS_MIO; UART0 demo'da PMC_MIO 42..43.
- pl0_ref_clk 100 MHz değil 333.333 MHz — sabit clock varsayımlarını gömdük.
- DDR sorusu NoC sorusudur; connectivity matrisi "yol var mı"nın cevabıdır.
:::
