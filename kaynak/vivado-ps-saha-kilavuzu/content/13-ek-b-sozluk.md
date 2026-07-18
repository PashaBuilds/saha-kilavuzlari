# Ek B — Sözlük

Alfabetik; teknik terimler İngilizce korunur, karşılığı Türkçe açıklanır.

:::sozluk
**ACP** — Accelerator Coherency Port. PL'den PS cache'ine tutarlı (coherent) erişim veren AXI slave portu. Bkz. [Bölüm 6](#06-ps-ayarlari-2).
**Address Editor** — Blok dizayndaki her master'ın hangi slave'i hangi adres aralığında gördüğünü listeleyen sekme. Adres haritasının kaynağı. Bkz. [Bölüm 7](#07-adres-haritasi).
**AXI** — Advanced eXtensible Interface. ARM AMBA veri yolu; blok dizaynda kalın tek çizgi olarak görünür, altında adres/veri/el sıkışma kanalları vardır.
**BD** — Block Design. Donanımcının IP bloklarını bağlayarak sistemi kurduğu `.bd` dosyası ve tuvali.
**bitstream** — PL'i (FPGA dokusunu) programlayan ikili dosya. UltraScale+'ta `.bit`; Versal'de yerini **PDI** alır.
**Board preset** — Kart üreticisinin yayınladığı, kartın şemasına uygun hazır PS ayar paketi. Donanımcı projeyi board part ile açınca tek hamlede uygulanır. Bkz. [Bölüm 4](#04-ps-ip).
**BSP** — Board Support Package. Donanıma özel sürücü + başlangıç kodu katmanı; `.xsa`'dan türetilir, `xparameters.h`'ı içerir.
**CIPS** — Control, Interfaces & Processing System. Versal'de MPSoC'un PS IP'sinin yerini alan blok: APU + RPU + PMC + çevre birimleri. Bkz. [Bölüm 8](#08-versal).
**concat** — `xlconcat` IP'si. Birden çok tek-bit interrupt telini tek demet (bus) yapar; giriş sırası GIC ID'sini belirler. Bkz. [Bölüm 6](#06-ps-ayarlari-2).
**DDRMC** — DDR Memory Controller. Versal'de DDR denetleyicisi; artık PS içinde değil, **NoC** içinde yaşar. Bkz. [Bölüm 8](#08-versal).
**EMIO** — Extended MIO. Bir PS çevre biriminin PL dokusu üzerinden dünyaya çıkması. MIO'nun aksine bitstream olmadan çalışmaz. Bkz. [Bölüm 5](#05-ps-ayarlari-1).
**Fabric clock (pl_clk)** — PS'ten PL'e ihraç edilen saat. PL'deki AXI IP'lerin çalışma saati. Bkz. [Bölüm 5](#05-ps-ayarlari-1).
**GIC** — Generic Interrupt Controller. APU'daki kesme denetleyicisi; pl_ps_irq bitleri buraya sabit ID bloğunda düşer (ilk PL grubu 121'den başlar).
**HP / HPC** — High Performance (Coherent) portları. `S_AXI_HP*`: PL master'ın DDR'a DMA'sı. HP cache'e uğramaz, HPC tutarlıdır. Bkz. [Bölüm 6](#06-ps-ayarlari-2).
**HPM** — High Performance Master. `M_AXI_HPM*`: PS master'ın PL slave'lerine (register) eriştiği kapı. Bkz. [Bölüm 6](#06-ps-ayarlari-2).
**ILMB / DLMB** — Instruction/Data Local Memory Bus. MicroBlaze'in yerel BRAM'ine giden ayrı komut ve veri yolları; Address Editor'da iki ayrı uzay olarak görünür. Bkz. [Bölüm 9](#09-microblaze).
**IP** — Intellectual Property. Blok dizayndaki hazır donanım bloğu (kutusu). Üstündeki instance adı xparameters türetmelerinin kökü.
**MDM** — MicroBlaze Debug Module. JTAG üzerinden MicroBlaze debug'ı (breakpoint, XSDB) sağlayan IP. Bkz. [Bölüm 9](#09-microblaze).
**MicroBlaze** — PL dokusuna sentezlenen 32/64-bit soft-core RISC işlemci; PS'siz kartlarda yazılımın evi. Bkz. [Bölüm 9](#09-microblaze).
**MIO** — Multiplexed I/O. PS'in kendine ait 78 pinlik havuzu; sabit çevre birimleri bu havuzdan pin alır. Versal'de PMC_MIO + PS_MIO olarak ikiye ayrılır. Bkz. [Bölüm 5](#05-ps-ayarlari-1).
**MMI** — Memory Map Info. Hangi adres aralığının hangi fiziksel BRAM hücresinde olduğunu tarif eden dosya (`write_mem_info`); updatemem'in haritası. Bkz. [Bölüm 9](#09-microblaze).
**NMU / NSU** — NoC Master/Slave Unit. NoC'a giriş turnikesi (NMU) ve çıkış kapısı (NSU). Bkz. [Bölüm 8](#08-versal).
**NoC** — Network on Chip. Versal'de yüksek bant AXI trafiğini taşıyan, silikonda hazır çip içi ağ. "AXI'nin şehir içi metrosu." Bkz. [Bölüm 8](#08-versal).
**PDI** — Programmable Device Image. Versal'de boot + PL + NoC konfigürasyonunu birlikte taşıyan tek imaj; bitstream'in yerini alır.
**PL** — Programmable Logic. FPGA dokusu; donanımcının IP'lerini yerleştirdiği kısım.
**PMC** — Platform Management Controller. Versal'de boot, güvenlik ve konfigürasyon yöneticisi; CIPS içindedir.
**PS** — Processing System. Çipin işlemci tarafı: APU/RPU, sabit çevre birimleri, DDR denetleyici, MIO/EMIO ve PS-PL kapıları.
**PSS_REF_CLK** — PS'e karttan giren referans kristal saati (demo: 33.330 MHz); tüm iç PLL'lerin kökü. Bkz. [Bölüm 5](#05-ps-ayarlari-1).
**Re-customize IP** — Bir IP'ye çift tıklayınca açılan yapılandırma diyaloğu. PS için dört durak: I/O, Clock, DDR, PS-PL. Çıkışta **Cancel**. Bkz. [Bölüm 4](#04-ps-ip).
**RPU** — Real-time Processing Unit. Cortex-R5F çekirdekleri; gerçek-zaman ve güvenlik-kritik görevler.
**SmartConnect (axi_smc)** — AXI trafik göbeği; PS'ten gelen tek yolu birden çok IP'ye adres çözerek dağıtır. Bkz. [Bölüm 3](#03-blok-dizayn).
**soft-core** — Çipin sabit silikonunda değil, PL dokusunda LUT/FF/BRAM ile gerçeklenen işlemci (ör. MicroBlaze). Karşıtı: hard-core (APU gibi). Bkz. [Bölüm 9](#09-microblaze).
**unmapped** — Bağlı ama adres atanmamış slave. Fiziksel var, yazılımdan erişilemez; xparameters'ta doğmaz. Bkz. [Bölüm 7](#07-adres-haritasi).
**updatemem** — ELF'i, MMI haritasını kullanarak bitstream'in BRAM init bitlerine işleyen araç; sentezsiz yazılım güncelleme. Bkz. [Bölüm 9](#09-microblaze).
**Validate Design** — Blok dizaynı doğrulayan işlem (F6); adres çakışması ve bağlantı hatalarını yakalar. Bkz. [Bölüm 7](#07-adres-haritasi).
**VLNV** — Vendor:Library:Name:Version. Bir IP'nin tam kimliği (ör. `xilinx.com:ip:axi_gpio:2.0`).
**.xpr** — Vivado proje giriş dosyası; etrafındaki dizin ailesiyle birlikte projeyi oluşturur.
**xparameters.h** — BSP'nin ürettiği, adres/ID/frekans tanımlarını içeren başlık dosyası. `.xsa`'dan türetilir; kaynağı Vivado projesidir. Bkz. [Bölüm 7](#07-adres-haritasi).
**.xsa** — Xilinx Support Archive. Vivado'nun "Export Hardware" ile ürettiği, donanım tarifini (adresler, clock'lar, IP listesi, init) taşıyan ZIP arşivi. Vivado ile Vitis arasındaki köprü. Bkz. [Bölüm 1](#01-el-sikisma), [Bölüm 7](#07-adres-haritasi).
:::
