# Bölüm 5 — PS Ayarları I: I/O, Clock, DDR

## Neden umursamalısın

Konsolun çalışması, baud hesabının tutması ve `malloc`'un elinin altında
gerçek bir bellek bulması — üçü de bu bölümdeki üç sayfanın doğru okunmasına
bakar. Buradaki her değeri demo projenin *gerçek* dökümünden aktarıyoruz
(`assets/reports/ultrascale-ps-config-secme.md`); kendi projende aynı
ekranlara bakıp aynı tabloyu kendin çıkarabilirsin.

## I/O Configuration: MIO tablosu

[[adim: ps_ultra çift tık → Page Navigator → I/O Configuration]]

MIO (Multiplexed I/O), PS'in kendine ait 78 pinlik havuzudur. Her sabit
çevre birimi bu havuzdan bir dilim ister; tablo hangi dilimin kime
verildiğini gösterir. Demo projede (ZCU102 preset'i) dağılım şöyle:

| Çevre birimi | Durum | Pin dilimi |
|---|---|---|
| QSPI | açık | MIO 0 .. 12 |
| I2C0 / I2C1 | açık | MIO 14 .. 15 / 16 .. 17 |
| **UART0** | **açık** | **MIO 18 .. 19** |
| UART1 | açık | MIO 20 .. 21 |
| CAN1 | açık | MIO 24 .. 25 |
| SD1 | açık | MIO 39 .. 51 |
| USB0 | açık | MIO 52 .. 63 |
| GEM3 (ENET3) | açık | MIO 64 .. 75 |
| SPI0/1, NAND, SD0, ENET0-2 | kapalı | — |

[[ekran: 09 | I/O Configuration — MIO tablosu
rozet 1: Peripheral ağacı — Low Speed / High Speed dalları; işaret kutusu = çevre birimi açık.
rozet 2: I/O sütunu — pin dilimi (MIO x .. y) ya da EMIO seçimi.
rozet 3: MIO Voltage — bank gerilimleri; donanımcının alanı ama uyumsuzluk kart hatası demektir.
]]

[[ekran: 10 | I/O Configuration — UART0 satırı yakın plan
rozet 1: UART0 açık ve MIO 18 .. 19'da — konsolunun fiziksel adresi.
rozet 2: Aynı ağaçta UART1: MIO 20 .. 21 — ikinci konsol/telemetri kanalı.
]]

:::yazilima-yansimasi
UART0'ın MIO 18-19'da açık olması BSP'de şöyle görünür: `xparameters.h`
içinde `XPAR_XUARTPS_0_BASEADDR 0xFF000000` (UART0'ın sabit PS adresi) ve
stdin/stdout'un `psu_uart_0`'a bağlanması. Linux tarafında karşılığı device
tree'deki `uart0` düğümü ve `console=ttyPS0,115200` satırıdır. Çevre birimi
burada *kapalıysa* xparameters'ta hiç doğmaz — "driver var, cihaz yok"
hatalarının kaynağı çoğu zaman bu tablodur.
:::

### EMIO: "UART'ım PL'den mi çıkıyor?"

I/O sütununda pin dilimi yerine **EMIO** yazıyorsa o çevre birimi PS
pinlerinden değil, PL dokusundan dünyaya çıkıyor demektir. Aynı denetleyici,
farklı kapı:

[[sema: sema-05-mio-emio | Şema 5 — Aynı UART'ın iki çıkış yolu: MIO doğrudan paket pinine (bitstream'siz yaşar), EMIO PL üzerinden donanımcının seçtiği pine (bitstream şart).]]

Yazılım açısından register'lar ve driver aynıdır; fiziksel yol farklıdır.
Kritik sonuç şu: EMIO'ya yönlenmiş çevre birimi, **bitstream PL'i
yapılandırmadan dünyaya çıkamaz.** "Kart açıldı ama konsol sessiz" vakasında
ilk bakılacak yer UART'ın MIO mu EMIO mu olduğudur.

:::tuzak
MIO tablosunda bir pin diliminin *dolu görünmesi*, o çevre biriminin senin
beklediğin konektöre gittiğini garanti etmez. MIO 18-19'un USB-UART köprüsüne
mi, pin header'a mı gittiği kartın şematiğinde yazar. Vivado sana "hangi PS
pini" sorusunu cevaplar; "o pin kartta nereye lehimli" sorusu şematik işidir.
İkisini karıştırma.
:::

## Clock Configuration: baud hesabının kaynağı

[[adim: ps_ultra çift tık → Clock Configuration → Input Clocks / Output Clocks]]

İki alt sekme var. **Input Clocks**: karttan PS'e giren referanslar — demo
projede `PSS_REF_CLK = 33.330 MHz` (kartın kristali). **Output Clocks**:
bu referanstan PLL'lerle türetilen tüm iç saatler.

[[sema: sema-06-clock-agaci | Şema 6 — Basitleştirilmiş clock ağacı: tek kristalden PLL'lere, oradan çevre birimi referanslarına ve PL fabric clock'larına. Sarı yol: pl_clk0; yeşil yol: UART referansı.]]

[[ekran: 11 | Clock Configuration — Input Clocks
rozet 1: PSS_REF_CLK — 33.330 MHz; ağacın kökü.
]]

[[ekran: 12 | Clock Configuration — Output Clocks, Low Power Domain
rozet 1: UART0/1 referans satırı — istenen 100 MHz.
rozet 2: Actual Frequency sütunu — 99.990005 MHz; hesapların gerçek girdisi.
]]

Tablonun en önemli sütunu **Actual Frequency**'dir. PLL'ler tam sayı
bölücülerle çalıştığından istenen değer her zaman tutturulamaz: demo
projede UART referansı "100 MHz" istenmiş, gerçekte **99.990005 MHz**
üretilmiştir.

| Saat | İstenen | Gerçek (Actual) |
|---|---|---|
| UART0_REF | 100 MHz | 99.990005 MHz |
| I2C0/1_REF | 100 MHz | 99.990005 MHz |
| QSPI_REF | 125 MHz | 124.987511 MHz |
| SD1 (SDIO1_REF) | 187.5 MHz | 187.481262 MHz |
| GEM3_REF | 125 MHz | 124.987511 MHz |

### PL Fabric Clocks: PL'deki IP'lerin kalbi

Output Clocks sayfasının alt kısmı PL'e ihraç edilen saatleri listeler:
`pl_clk0..3`. Demo projede yalnızca **PL0 açık: istenen 100 MHz, gerçek
99.990005 MHz** — blok dizayndaki bütün AXI IP'ler (SmartConnect dahil)
bu tek saatle çalışıyor.

[[ekran: 13 | Clock Configuration — PL Fabric Clocks
rozet 1: PL0 satırı — açık, kaynak PLL (IOPLL) ve 100 MHz istek.
rozet 2: PL1-3 — kapalı; dizaynda ikinci saat yok.
]]

:::yazilima-yansimasi
İki somut düşüm: (1) `XPAR_XUARTPS_0_UART_CLK_FREQ_HZ` gibi tanımlar
Actual değerden gelir — baud bölücüsünü BSP bu sayıyla hesaplar; elle
hesap yapacaksan 100 000 000 değil 99 990 005 kullan. (2) PL'deki
`axi_timer_0`'ın saymasını saniyeye çevirirken `XPAR_AXI_TIMER_0_CLOCK_FREQ_HZ`
kullanılır; bu da pl_clk0'ın gerçek değeridir. 100 MHz varsayımıyla yazılmış
gecikme döngüsü, %0.01 değil — PLL başka değere ayarlandığında %50 —
yanılabilir. Sabit yazma, XPAR'dan oku.
:::

## DDR Configuration: heap'inin fiziksel evi

[[adim: ps_ultra çift tık → DDR Configuration]]

Bu sayfanın onlarca zamanlama parametresi donanımcının ve preset'in işidir;
senin okuyacağın satırlar tabloda:

| Parametre | Demo projedeki değer | Sana anlamı |
|---|---|---|
| Memory Type | DDR4 | Denetleyici modu |
| Speed Bin | DDR4-2133P | Veri hızı sınıfı (2133 MT/s) |
| Bus Width | 64 Bit | Tam genişlik; bant genişliğinin çarpanı |
| Device Capacity | 4096 MBits | Yonga başına 512 MB; toplamı Address Editor doğrular |
| ECC | Disabled | Hata düzeltme yok — veri bütünlüğü sana kalmış |
| CL | 15 | Gecikme sınıfı; yazılıma dolaylı yansır |

[[ekran: 14 | DDR Configuration — genel görünüm
rozet 1: Memory Type / Speed Bin — DDR4, 2133P.
rozet 2: Data Bus Width — 64 bit; ECC seçimi hemen yanında.
rozet 3: Zamanlama alanları — preset'ten gelir; elle dokunulmaz.
]]

:::saha-notu
"DDR açık mı" sorusunun en hızlı cevabı bu sayfa bile değil, Address
Editor'dur (Bölüm 7): `DDR_LOW` segmenti listede yoksa ya da PS
konfigürasyonunda DDR devre dışıysa, linker script'in DDR'a koyduğu her
şey hayalete yazıyor demektir. DDR'sız PS konfigürasyonu meşru bir
tercihtir (küçük baremetal işler OCM'de yaşayabilir) ama bunun *bilinçli*
olduğunu donanımcıya teyit ettir.
:::

:::yazilima-yansimasi
DDR ayarlarının yazılım düşümleri: `XPAR_PSU_DDR_0_S_AXI_BASEADDR 0x0` ve
`HIGHADDR` (kapasitenin adres uzayındaki karşılığı) linker script'inin
bellek bölgesini tanımlar; Linux'ta `memory` düğümü aynı bilgiyi taşır.
ECC Disabled ise tek bit hataları sessizce veri bozar — kritik uygulamada
bu satır bir tasarım kararı olarak tartışılmalıdır. Speed bin ve bus width,
DMA throughput beklentilerinin üst sınırını çizer.
:::

:::deneme id=deneme-5-1
**Hedef:** MIO tablosundan konsol bilgisi çıkar, baud saatinin kaynağını yaz.

[[adim: ps_ultra çift tık → I/O Configuration → Low Speed → UART0]]

Demo 1'de: (a) UART0 hangi MIO pinlerinde? (b) Clock Configuration'da
UART referansının *gerçek* frekansı kaç? (c) 115200 baud için bölücü bu
frekanstan mı, istenen 100 MHz'den mi hesaplanmalı?

::cozum::
(a) MIO 18 .. 19. (b) 99.990005 MHz. (c) Gerçek değerden — BSP zaten öyle
yapar; `XPAR_XUARTPS_0_UART_CLK_FREQ_HZ` 99990005 olarak düşer ve
`XUartPs_SetBaudRate` bölücüyü bundan türetir. Fark bu örnekte ihmal
edilebilir; ama prensip değil: her zaman Actual sütununu oku.
:::

:::ozet
- MIO tablosu = hangi çevre birimi açık + hangi pinde; EMIO = PL üzerinden
  çıkış, bitstream şart.
- Clock sayfasında istenen değil **Actual** frekans okunur; XPAR'lar oradan
  türetilir.
- PL fabric clock'ları (pl_clk0-3) PL'deki bütün AXI IP'lerin saatidir.
- DDR sayfasından yazılımcıya dört satır yeter: tip, hız, genişlik, ECC.
  "Açık mı" sorusunun kesin cevabı Address Editor'da.
:::
