# Bölüm 10 — Vaka Analizleri

## Neden umursamalısın

Önceki bölümler her ekranı ayrı ayrı okumayı öğretti. Sahada ise soru
ekran adıyla değil, belirtiyle gelir: "konsol niye sessiz", "bu IP'ye niye
erişemiyorum", "DDR gerçekten NoC'ta mı". Bu bölüm üç kısa vakada, demo
projeler üzerinde uçtan uca iz sürmeyi gösterir — her adım gerçek bir
ekrana/rapora dayanır.

## Vaka A — "Debug UART hangi pinde ve kaç baud?"

**Senaryo:** Kart geldi, seri konsol bağlayacaksın. Terminal ayarı için iki
şey lazım: fiziksel pin (kabloyu nereye) ve baud (terminal hızı). Demo 1
üzerinde iz sürelim.

**Adım 1 — hangi UART konsol?** PS'in iki sabit UART'ı var (UART0, UART1) ve
bir de PL'de `axi_uartlite_dbg`. "Debug konsol" tipik olarak PS UART0'dır.

[[adim: ps_ultra çift tık → I/O Configuration → Low Speed → I/O Peripherals → UART0]]

**Adım 2 — pin.** MIO tablosunda UART0 satırı: **MIO 18 .. 19**
(gerçek rapor: `PSU__UART0__PERIPHERAL__IO = MIO 18 .. 19`). TX/RX bu iki
pinde; kartın şematiğinde MIO 18-19'un USB-UART köprüsüne gittiğini teyit et.

**Adım 3 — baud saati.** Baud, UART referans saatinden bölünür.

[[adim: ps_ultra çift tık → Clock Configuration → Output Clocks → UART0 ref]]

Gerçek değer: **99.990005 MHz** (`UART0_REF_CTRL__ACT_FREQMHZ`). Baud'ı
donanım değil driver ayarlar; sen sadece 115200 istersin, bölücüyü BSP bu
saatten hesaplar.

:::yazilima-yansimasi
Terminal ayarın: **115200 8N1**, port = kartın USB-UART'ı. Kod tarafında
`XPAR_XUARTPS_0_BASEADDR` (0xFF000000, PS UART0'ın sabit adresi) ve
`XPAR_XUARTPS_0_UART_CLK_FREQ_HZ = 99990005`. Linux'ta
`console=ttyPS0,115200`. Cevap: **MIO 18-19, 115200 baud, ref 99.99 MHz.**
Not: PL'deki `axi_uartlite_dbg` ayrı bir UART'tır (adresi 0xA0020000,
Bölüm 7); onu konsol sanıp yanlış pine kablo takmak klasik hatadır.
:::

## Vaka B — "PL timer'ının adresi ve interrupt ID'si ne?"

**Senaryo:** PL'deki `axi_timer_0`'ı süreceksin: register'a yazmak için
adres, ISR bağlamak için IRQ ID lazım. İkisini uçtan uca çıkaralım.

**Adım 1 — adres.** Address Editor tek durak:

[[adim: Open Block Design → Window → Address Editor]]

`axi_timer_0/S_AXI` satırı: base **0xA0010000**, aralık 64K, high 0xA001FFFF
(gerçek rapor: `SEG_axi_timer_0_Reg`). Kodda `XPAR_AXI_TIMER_0_BASEADDR
0xA0010000`.

**Adım 2 — interrupt yolu.** Timer'ın `interrupt` teli concat'a girer.
Blok dizaynda izle (Bölüm 6):

- `axi_timer_0/interrupt` → `irq_concat/In0` → `pl_ps_irq0[0]` → **GIC ID 121**.

Concat In0 en düşük bit olduğu için ilk PL IRQ ID'sine (121) düşer.

**Adım 3 — doğrulama refleksi.** Concat sırasını gözünle teyit et:
donanımcı araya bir IP eklerse timer In1'e kayar ve ID 122 olur — kod
sessizce yanlış kaynağa bağlanır.

:::yazilima-yansimasi
İki satır kod, iki farklı ekrandan:
`XTmrCtr_Initialize(&Timer, XPAR_AXI_TIMER_0_DEVICE_ID);` — taban adres
0xA0010000 (Address Editor); `XScuGic_Connect(&Gic,
XPAR_FABRIC_AXI_TIMER_0_INTERRUPT_INTR, Handler, &Timer);` — ID 121
(concat sırası). Elle 121 yazmak yerine `XPAR_FABRIC_*` sembolünü kullan:
concat sırası değişse bile sembol doğru ID'yi taşır. Cevap: **adres
0xA0010000, IRQ ID 121.**
:::

## Vaka C — "Donanımcı 'DDR'ı NoC'a aldık' dedi; Versal projesinde doğrula"

**Senaryo:** MPSoC alışkanlığınla DDR'ı PS/CIPS'in içinde ararsın ama orada
yok. İddiayı Demo 2 üzerinde doğrulayalım.

**Adım 1 — CIPS'te DDR arama.** CIPS'i aç, DDR ayarı ara — bulamazsın; tek iz
`DDR_MEMORY_MODE = Connectivity to DDR via NOC` beyanıdır.

[[adim: versal_cips_0 çift tık → PS PMC → (DDR ayarı yok, sadece "via NoC" beyanı)]]

**Adım 2 — NoC'a bak.** Asıl denetleyici NoC'un içinde:

[[adim: axi_noc_0 çift tık → General → Memory Controller / DDR Basic]]

NoC General: **Single Memory Controller**, DDR Address Region 0 = DDR LOW0
(0x0–0x7FFFFFFF, 2G), Region 1 = DDR LOW1 (0x8_0000_0000, 32G kapasiteye
kadar). DDR Basic: **DDR4 SDRAM, 1600 MHz**. Kart arayüzü `ddr4_dimm1`
(gerçek rapor: `CH0_DDR4_0_BOARD_INTERFACE = ddr4_dimm1`).

**Adım 3 — adres haritasında doğrula.** Address Editor'da CIPS'in NoC
kapılarından (`FPD_CCI_NOC_*`) DDR_LOW0/LOW1 segmentleri görünür; PL timer'ı
ise NoC arkasında **0x201_0000_0000** gibi 40-bit üstü bir adrese düşer.

:::yazilima-yansimasi
Donanımcının iddiası **doğru**. Yazılım faturası: (1) DDR iki bölgeli —
linker script ve device tree `memory` düğümü 0x0'daki 2 GB ve
0x8_0000_0000'daki üst bölgeyi ayrı tanımlar; (2) NoC arkasındaki PL IP'leri
32-bit üstü adres alabilir, `u32` adres taşıyan eski kod kırılır. Cevap:
**DDR gerçekten NoC/DDRMC arkasında, DDR4-1600, iki adres bölgeli.**
:::

:::deneme id=deneme-10-1
**Hedef:** Üç vakayı kendi Vivado'nda uçtan uca yürü.

Demo 1'i aç ve Vaka A + B'yi tekrar üret: UART0 pinini, UART ref frekansını,
timer adresini ve concat sırasından timer'ın IRQ ID'sini kendi gözünle
çıkar. Sonra Demo 2'yi aç, Vaka C'yi yürü: NoC'ta DDR denetleyicisini bul.

::cozum::
UART0 = MIO 18..19, ref 99.990005 MHz; timer = 0xA0010000, IRQ ID 121
(concat In0); Demo 2'de DDR = NoC axi_noc_0 içinde DDR Basic sekmesi,
DDR4-1600, ddr4_dimm1. Üçünü de kendi projende bulduysan, bu kılavuzun
asıl becerisini kazandın: belirtiden ekrana, ekrandan yazılım karşılığına
iz sürmek.
:::

:::ozet
- Vaka A: konsol izi = MIO tablosu (pin) + clock sayfası (ref) → terminal
  ayarı.
- Vaka B: PL IP izi = Address Editor (adres) + concat sırası (IRQ ID) →
  iki satır sürücü kodu.
- Vaka C: Versal DDR izi = CIPS'te "via NoC" beyanı → NoC'ta gerçek DDRMC →
  Address Editor'da iki bölge.
- Ortak kalıp: belirti → ekran → `yazilima-yansimasi`.
:::
