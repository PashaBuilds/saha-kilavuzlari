# Bölüm 9 — MicroBlaze: İşlemcinin Kendisi de PL'deyse

## Neden umursamalısın

Her kartta bir PS yok. Saf FPGA'lı bir tasarım teslim aldığında (Artix,
Kintex, Spartan…) yazılımın koşacağı işlemci de blok dizaynın içinde bir
IP olarak durur: **MicroBlaze**. Bu dünyada alışkanlıkların iki yerde
kırılır: işlemcinin özellikleri bile birer konfigürasyon ayarıdır ve
yazılımın "diske" değil, **bitstream'in içindeki BRAM'e** gömülür. Bu
bölüm, PS bölümlerinde (4-7) kurduğun okuma refleksinin PL'deki işlemciye
uyarlanmış hâlidir.

## Soft-core fikri: sentezlenen işlemci

MicroBlaze, LUT + FF + BRAM'den örülen 32-bit RISC bir **soft-core**'dur.
Zynq'ta APU silikonda hazırdı; burada işlemci, donanımcı onu dizayna
koyduğu İÇİN vardır — bitstream yüklenmeden ne işlemci ne UART çalışır.

[[sema: sema-13-microblaze-sistem | Şema 13 — MicroBlaze sistemi kuşbakışı: soft-core çekirdek, ILMB/DLMB üzerinden yerel BRAM, AXI interconnect'ten çevre birimleri, axi_intc'den tek interrupt girişi, MDM'den JTAG debug.]]

Demo 3, **AC701** (Artix-7 xc7a200t) üzerine kuruludur ve maliyet gerçeği
şudur: işlemci + tüm çevre birimleri dahil sistemin tamamı çipin yalnızca
**%2.2'sini** kullanır (3004 LUT; gerçek rapor:
`assets/reports/microblaze-utilization.txt`). Kılavuzun scripti:

```tcl
vivado -mode batch -source vivado/microblaze/create_bd.tcl
```

[[bd: microblaze-bd-full | Demo 3 blok dizaynı (AC701, gerçek `write_bd_layout` export'u). Ortada MicroBlaze + yerel bellek + MDM + axi_intc çekirdeği; sağ sütunda AXI çevre birimleri ve kart portları (rs232_uart, iic_main, led_4bits, spi_flash); solda clk_wiz + reset altyapısı.]]

Çekirdek bölgenin yakın kırpımı — bu dörtlü her MicroBlaze dizaynında
birlikte gezer:

[[bd: microblaze-bd-cekirdek | MB çekirdeği: axi_intc'nin interrupt çıkışı MicroBlaze'in INTERRUPT girişine; DLMB/ILMB çift yolu yerel belleğe; MDM DEBUG kapısına bağlı.]]

[[ekran: 30 | MicroBlaze Diagram — sistem BD tam görünüm
rozet 1: microblaze_0 + local_memory + mdm + axi_intc — işlemci çekirdeği ve yaşam destek üniteleri.
rozet 2: AXI çevre birimleri sütunu — uartlite, iic, quad_spi, gpio, timer, bram_ctrl.
rozet 3: Kart portları — rs232_uart, iic_main, led_4bits, spi_flash: board preset PS'siz dünyada da işliyor.
]]

## İşlemcinin ayar ekranı: çekirdek özellikleri konfigürasyondur

[[adim: Open Block Design → microblaze_0 çift tık → MicroBlaze Configuration Wizard]]

PS'te Re-customize bir "okuma" ekranıydı; MicroBlaze'de aynı pencere
işlemcinin VAR OLUŞUNU tanımlar. Sihirbazın 4 sayfasından yazılımcıyı
ilgilendiren ayarlar:

[[ekran: 31 | MicroBlaze Wizard — Sayfa 1: genel yapı
rozet 1: Predefined Configurations + 32/64 bit seçimi — çekirdeğin sınıfı.
rozet 2: General Settings — optimizasyon (PERFORMANCE/AREA/FREQUENCY), Debug Module, Cache, Exceptions, MMU anahtarları.
rozet 3: Resource Estimates — her işaretin LUT/BRAM faturası anında görünür.
]]

[[ekran: 32 | MicroBlaze Wizard — Sayfa 2: komut seti
rozet 1: Instructions — Barrel Shifter, FPU (NONE), Integer Multiplier (NONE), Divider: her biri donanımda VAR/YOK anahtarı.
rozet 2: Optimization / Fault Tolerance — implementasyon tercihi ve hata toleransı.
]]

Demo projenin gerçek konfigürasyonu (rapor:
`microblaze-ps-config-secme.md`): 100 MHz, **çarpıcı yok, bölücü yok,
FPU yok, barrel shifter yok, cache yok**, debug açık
(`C_DEBUG_ENABLED=1`, 1 donanım breakpoint).

:::yazilima-yansimasi
Bu ekran senin derleyici bayraklarını ve performans beklentini belirler:
donanımda çarpıcı yokken `a*b` yazmak yasak değildir ama derleyici onu
yazılım döngüsüne açar — `xparameters.h`'taki
`XPAR_MICROBLAZE_USE_HW_MUL 0`, `XPAR_MICROBLAZE_USE_DIV 0`,
`XPAR_MICROBLAZE_USE_FPU 0` tanımları BSP derlenirken doğru `-mno-xl-soft-mul`
/ `-mhard-float` kararlarının otomatik verilmesini sağlar. Cache açılırsa
(`C_USE_DCACHE=1`) DMA'lı her akışta `Xil_DCacheFlushRange` sorumluluğu
doğar; bizim dizaynda cache yok, dert de yok. `XPAR_CPU_CORE_CLOCK_FREQ_HZ
100000000` ise bütün gecikme/timer hesaplarının tek gerçeğidir.
:::

## Bellek: kodun evi bitstream'in içindeki BRAM

MicroBlaze'in yerel belleği **LMB** (Local Memory Bus) üzerinden bağlanan
**64KB BRAM**'dir; komut (ILMB) ve veri (DLMB) ayrı yollardan aynı
BRAM'e ulaşır. Address Editor bu yüzden PS'tekinden farklı görünür —
**iki adres uzayı** vardır:

[[ekran: 33 | Address Editor — MicroBlaze'in çift uzayı
rozet 1: /microblaze_0/Data — 64K yerel bellek (0x0000_0000) + tüm AXI çevre birimleri + intc + AXI BRAM.
rozet 2: /microblaze_0/Instruction — yalnız ILMB'nin gördüğü 64K (0x0000_0000): kod buradan çekilir.
]]

Gerçek harita (rapordan):

| Segment | Base | Aralık | Not |
|---|---|---|---|
| `dlmb/ilmb Mem` | `0x0000_0000` | 64K | Kod + veri: linker script'in ana bölgesi |
| `axi_gpio_led` | `0x4000_0000` | 64K | LED'ler |
| `axi_uartlite_0` | `0x4060_0000` | 64K | Konsol |
| `axi_iic_0` | `0x4080_0000` | 64K | I2C |
| `microblaze_0_axi_intc` | `0x4120_0000` | 64K | Kesme denetleyici (kendisi de adreslenir!) |
| `axi_timer_0` | `0x41C0_0000` | 64K | Timer/PWM |
| `axi_quad_spi_0` | `0x44A0_0000` | 64K | SPI flash |
| `axi_bram_ctrl_0` | `0xC000_0000` | 8K | Ek veri BRAM'i |

:::yazilima-yansimasi
64KB, linker script'inin (`lscript.ld`) bütün dünyasıdır: `.text`,
`.data`, `.bss`, stack ve heap bu tek bölgeye sığmak zorunda. Vitis
varsayılanı stack+heap için 1KB'ler önerir; `printf` gibi obur
fonksiyonlar yerine `xil_printf` kullanılmasının sebebi budur. Kod
büyürse iki yol var: BRAM'i büyütmek (donanımcıdan `local_mem` ayarı —
sentez gerekir) ya da 0xC000_0000'daki ek AXI BRAM'i linker'da veri
bölgesi olarak kullanmak. DDR'lı MicroBlaze sistemlerinde (MIG'li) aynı
mantık DDR bölgesine genişler — bizim demoda bilinçli olarak yok:
"bellek = BRAM" senaryosunun saf hâlini görüyorsun.
:::

## MMI ve updatemem: yazılımı sentezsiz güncellemek

Kodun BRAM'de yaşıyorsa şu soru hayatidir: *her yazılım değişikliğinde
sentez mi koşacağız?* Hayır — bunun için **MMI** (Memory Map Info)
dosyası ve **updatemem** aracı var:

[[sema: sema-15-mmi-updatemem | Şema 15 — MMI + updatemem akışı: ELF + MMI + bitstream girer, yazılım gömülü download.bit çıkar. Sentez ve implementasyon bu döngünün DIŞINDADIR.]]

MMI, implementasyon sonrası `write_mem_info` ile üretilir ve "hangi adres
aralığı hangi FİZİKSEL BRAM hücresinde" bilgisini taşır. Demo projenin
gerçek MMI'sinden bir kesit (`assets/reports/microblaze-sistem.mmi`):

```xml
<MemInfo Version="1" Minor="9">
  <Processor Endianness="Little" InstPath="sistem_i/microblaze_0">
    <AddressSpace Name="...dlmb_bram_if_cntlr" Begin="0" End="65535">
      <BusBlock>
        <BitLane MemType="RAMB36" Placement="X1Y25">
          <DataWidth MSB="7" LSB="6"/>
          <AddressRange Begin="0" End="16383"/>
```

Oku: 64KB'lik bellek, çip üzerinde X1Y25 gibi koordinatlarda oturan
RAMB36'lara, her birine 2'şer bit dilimiyle dağıtılmış. ELF'ini bu
haritaya göre bitstream'e işleyen komut:

```bash
updatemem -meminfo sistem.mmi -data app.elf \
          -bit sistem_wrapper.bit -proc sistem_i/microblaze_0 \
          -out download.bit
```

:::tuzak
`-proc` argümanı MMI içindeki `InstPath` ile birebir aynı olmalıdır
(bizde `sistem_i/microblaze_0`). Ayrıca MMI, implementasyonun O KOŞUSUNA
aittir: donanımcı yeniden implement ettiyse BRAM yerleşimi değişmiş
olabilir — eski MMI + yeni bitstream sessizce bozuk bellek içeriği üretir.
MMI ile bitstream'i her zaman aynı koşudan al.
:::

:::yazilima-yansimasi
Pratikte bu akış sana iki şekilde dokunur: (1) Vitis "Program FPGA"
düğmesi perde arkasında updatemem'dir — .xsa içindeki MMI'yi kullanır ve
ELF'ini seçtiğinde bitstream'e gömer; (2) üretim hattında yazılım
güncellemesi, donanım ekibine gitmeden `updatemem` ile saniyeler içinde
yeni `download.bit` üretmektir. "Yazılımcı bitstream'e dokunmaz" kuralının
tek istisnası budur ve tamamen güvenlidir: updatemem yalnız BRAM init
bitlerini değiştirir, lojik dokunulmaz kalır.
:::

## Çevre birimleri: her ayar sentezde donar

PS'te çevre birimleri silikondaydı, ayarları boot'ta yazılırdı.
MicroBlaze dünyasında çevre birimi IP'lerinin config ekranındaki her
değer **sentezde donar** — çalışma zamanında değiştirilemez. En çarpıcı
örneği UART'tır:

[[ekran: 35 | AXI Uartlite — IP Configuration
rozet 1: Baud Rate 115200 — DONANIMDA SABİT: PS UART'ının aksine runtime'da değiştirilemez; yanlışsa sentez gerekir.
rozet 2: AXI CLK Frequency 100.0 (AUTO) — bölücü bu saate göre sentezlenir; saat değişirse baud da bozulur.
]]

[[ekran: 37 | AXI IIC — IP Configuration
rozet 1: SCL frekansı (100 kHz) ve adres modu — I2C zamanlaması da config'te; yavaş sensör için 400k'ya çıkarmak donanım işi.
]]

[[ekran: 36 | AXI Quad SPI — IP Configuration
rozet 1: Mode Quad · Transaction Width 8 · Frequency Ratio 2 — SCK = AXI/2 = 50 MHz; oran değişmeden hız değişmez.
rozet 2: Slave sayısı, Micron cihaz seçimi, FIFO 16, STARTUP primitive — konfigürasyon flash'ıyla pin paylaşımının anahtarı.
]]

[[ekran: 38 | AXI GPIO — IP Configuration
rozet 1: GPIO Width 4 + All Outputs — kart LED arayüzü genişliği kilitledi; 5. LED yazmak sessizce boşa gider.
rozet 2: Enable Interrupt — kesme çıkışının var olma şartı; kapalıysa XGpio_InterruptEnable çağrın hiçbir şey yapmaz.
]]

[[ekran: 39 | AXI Timer — yapılandırma
rozet 1: 32-bit sayaç + Timer 2 etkin — çift kanal; XPAR'da tek base, iki alt timer olarak görünür.
rozet 2: Generate/PWM uçları — pwm0 çıkışı: PWM üretimi bu IP'nin işi, ayrı IP arama.
]]

:::yazilima-yansimasi
Sabitlenen her değer `xparameters.h`'a düşer ve driver'lar oradan okur:
`XPAR_AXI_UARTLITE_0_BAUDRATE 115200` (XUartLite'ta SetBaudRate diye bir
fonksiyon YOKTUR — arama, çünkü donanımda yok), `XPAR_AXI_TIMER_0_CLOCK_FREQ_HZ
100000000` (timer tık→saniye çevirisi), `XPAR_AXI_GPIO_LED_GPIO_WIDTH? →
tasarımda 4`. SPI'da `C_USE_STARTUP=1` özel dikkat ister: SPI flash,
FPGA'nın kendi konfigürasyon pinlerini paylaşır — erişim STARTUPE2
primitivi üzerinden gider; kartta "flash'a yazamıyorum" vakalarının
klasik kökeni bu ayarın kapalı olmasıdır.
:::

## Kesmeler: GIC yok, axi_intc var

MicroBlaze'in **tek bir interrupt girişi** vardır. Birden çok kaynağı
oraya taşıyan yapı, PS'teki GIC'in PL'de sentezlenen küçük kardeşidir:
**axi_intc** (+ önünde xlconcat).

[[sema: sema-14-mb-interrupt | Şema 14 — Beş kaynak → concat → axi_intc → MB INTERRUPT. Alt tabloda GIC-intc farkları: ID'nin kaynağı, driver API'si, ortak refleks.]]

[[ekran: 34 | AXI Interrupt Controller — yapılandırma
rozet 1: Number of Peripheral Interrupts (Auto) = 5 — concat'tan gelen demet genişliği.
rozet 2: Edge/Level maskeleri (0xFFFFFFEA) + Fast Interrupt Mode — her girişin tetikleme tipi ve düşük gecikmeli mod.
]]

Demo projedeki sıra (concat girişleri) → kesme ID'leri:

| Concat girişi | Kaynak | intc ID |
|---|---|---|
| In0 | `axi_timer_0/interrupt` | 0 |
| In1 | `axi_uartlite_0/interrupt` | 1 |
| In2 | `axi_iic_0/iic2intc_irpt` | 2 |
| In3 | `axi_quad_spi_0/ip2intc_irpt` | 3 |
| In4 | `axi_gpio_led/ip2intc_irpt` | 4 |

:::yazilima-yansimasi
GIC'te `XScuGic` vardı; burada `XIntc` var ve ID'ler 121'den değil
0'dan başlar — kaynağı yine concat SIRASIDIR. `xparameters.h` örneği:
`XPAR_MICROBLAZE_0_AXI_INTC_AXI_TIMER_0_INTERRUPT_INTR 0U`,
`..._AXI_UARTLITE_0_INTERRUPT_INTR 1U`. Kod kalıbı:

```c
XIntc_Initialize(&Intc, XPAR_INTC_0_DEVICE_ID);
XIntc_Connect(&Intc,
    XPAR_MICROBLAZE_0_AXI_INTC_AXI_TIMER_0_INTERRUPT_INTR,
    TimerHandler, &TimerInst);
XIntc_Enable(&Intc,
    XPAR_MICROBLAZE_0_AXI_INTC_AXI_TIMER_0_INTERRUPT_INTR);
XIntc_Start(&Intc, XIN_REAL_MODE);
microblaze_enable_interrupts();
```

İki fark daha: intc'nin kendisi AXI'de adreslenir (0x4120_0000 — kesme
onayı/maskeleme register yazmalarıdır) ve `Fast Interrupt Mode` açıksa
vektör adresleri doğrudan donanımdan beslenir — BSP bunu senin yerine
kurar, ama "neden ISR'ım hızlı giriyor" sorusunun cevabı bu kutudur.
Donanımcı concat'a kaynak eklerse/araya sokarsa ID'ler kayar: PS'teki
refleks aynen geçerli — .xsa güncellendiğinde bu tabloyu yeniden çıkar.
:::

:::deneme id=deneme-9-1
**Hedef:** Çift adres uzayını ve sabit baud'u kendi gözünle gör.

```tcl
vivado -mode batch -source vivado/microblaze/create_bd.tcl
vivado vivado\work\demo_microblaze\demo_microblaze.xpr
```

[[adim: Open Block Design → Window → Address Editor]]

(a) Address Editor'da kaç Network var ve Instruction uzayında kaç satır
görüyorsun? (b) `axi_uartlite_0`'a çift tıkla: baud'u 9600 yapmak istesen
hangi süreç gerekir? (c) `updatemem` komutunda `-proc` için ne yazacağını
MMI dosyasından bul (`assets/reports/microblaze-sistem.mmi`).

::cozum::
(a) 2 network: Data (8 segment) + Instruction (yalnız ilmb, 1 satır) —
Harvard tarzı ayrım. (b) IP config'te C_BAUDRATE değişir → çıkışta OK
gerekir → IP yeniden üretilir → SENTEZ + implementasyon + yeni bitstream:
yani donanımcı işi; PS UART'taki gibi `SetBaudRate` yok. (c)
`InstPath="sistem_i/microblaze_0"` → `-proc sistem_i/microblaze_0`.
:::

:::ozet
- Soft-core = sentezlenen işlemci; bitstream yoksa sistem yok. Fatura
  şaşırtıcı derecede küçük: bu demo xc7a200t'nin %2.2'si.
- Çekirdek özellikleri (çarpıcı/FPU/cache/debug) konfigürasyondur;
  XPAR_MICROBLAZE_* tanımları derleyici ve driver davranışını yönetir.
- Kod 64KB LMB BRAM'de yaşar; Address Editor'da Data + Instruction diye
  İKİ uzay görürsün. Linker script bu haritanın kopyasıdır.
- MMI + updatemem = sentezsiz yazılım güncelleme; MMI ile bitstream aynı
  implementasyon koşusundan olmalı.
- Çevre birimi ayarları sentezde donar: uartlite baud'u sabittir, SPI
  hızı orandır, GPIO genişliği karta kilitlidir.
- Kesmeler axi_intc'den geçer: ID = concat sırası (0'dan), API = XIntc.
:::
