# Bölüm 6 — PS Ayarları II: PS-PL Arayüzleri ve Interrupt'lar

## Neden umursamalısın

"PL'deki IP'me erişemiyorum" ve "interrupt'ım hiç gelmiyor" — PS-PL sınırında
yaşanan iki klasik arıza. İkisinin de konfigürasyon tarafı tek sayfada durur:
PS-PL Configuration. Bu sayfayı okuyabilen, arızanın yazılımda mı donanım
ayarında mı olduğunu beş dakikada ayırır.

## PS-PL Configuration: kapıların listesi

[[adim: ps_ultra çift tık → PS-PL Configuration → PS-PL Interfaces]]

PS ile PL arasındaki bütün AXI kapıları burada açılıp kapanır. Adlandırma
şifresi tek kuralla çözülür: ad **M_** ile başlıyorsa PS master'dır (PS
konuşur, PL dinler); **S_** ile başlıyorsa PS slave'dir (PL konuşur, PS
dinler).

[[sema: sema-07-ps-pl-arayuz | Şema 7 — PS-PL pencere haritası: HPM'lerde PS master (register erişimi), HP'lerde PL master (DMA), ACP'de cache-tutarlı özel yol.]]

| Kapı | Yön | Tipik iş |
|---|---|---|
| `M_AXI_HPM0/1_FPD` | PS → PL | Senin kodunun PL register erişimi |
| `M_AXI_HPM0_LPD` | PS → PL | Düşük güç adasından aynı iş (RPU ağırlıklı) |
| `S_AXI_HP0-3_FPD` | PL → PS | PL'den DDR'a DMA (cache'e uğramaz) |
| `S_AXI_HPC0/1_FPD` | PL → PS | Cache-tutarlı DMA varyantı |
| `S_AXI_ACP_FPD` / `ACE` | PL → PS | Cache'e doğrudan; nadir, bilinçli tercih |

Demo projenin gerçeği (rapordan): yalnızca **HPM0 FPD açık**
(`PSU__USE__M_AXI_GP0 = 1`), HPM1 ve bütün S_AXI kapıları kapalı,
veri genişliği 128 bit (`PSU__MAXIGP0__DATA_WIDTH = 128`). Yani bu
dizaynda PL'e tek kapıdan çıkılıyor ve PL'den DDR'a DMA yolu yok — dört
çevre birimimiz için doğru ölçü.

[[ekran: 15 | PS-PL Configuration — AXI kapı listesi
rozet 1: AXI HPM0 FPD — işaretli; SmartConnect'in beslendiği kapı.
rozet 2: AXI HPM1 FPD — kapalı; Address Editor'da ikinci uzay olmamasının nedeni.
rozet 3: S_AXI satırları — hepsi kapalı: bu dizaynda PL master yok.
]]

:::tuzak
Kapı sayısı ile SmartConnect dalları farklı şeylerdir. "HPM0 tek ama benim
dört IP'm var, nasıl?" — SmartConnect tek kapıyı dörde böler. Tersi de
önemli: HPM0 kapalıyken SmartConnect'e istediğin kadar IP bağla, PS o
dünyaya çıkamaz. Erişim teşhisinde sıra hep: kapı açık mı → SmartConnect
dalı var mı → adres atanmış mı (Bölüm 7).
:::

:::yazilima-yansimasi
HPM kapılarının yazılımdaki görünümü dolaylı ama nettir: kapı açık +
IP adreslenmiş ise `xparameters.h`'ta IP'nin `BASEADDR`'ı doğar ve
`Xil_Out32(XPAR_..._BASEADDR, ...)` fiziksel olarak HPM0 üzerinden akar.
Kapı kapalıysa IP'ye adres atanamaz, XPAR doğmaz — derleme hatası olarak
değil, "tanımsız sembol" ya da eksik driver instance olarak karşına çıkar.
S_AXI_HP kapıları ise senin dünyanda DMA buffer yönetimi demektir:
HP (non-coherent) kullanılıyorsa `Xil_DCacheFlushRange`/`Invalidate`
çağrıları zorunludur; HPC/ACP kullanılıyorsa donanımcıyla cache tutarlılığı
sözleşmesini netleştir.
:::

## Interrupt'lar: teller, demet, ID'ler

[[adim: ps_ultra çift tık → PS-PL Configuration → General → Interrupts → PL to PS]]

PL'den PS'e kesme taşıyan mekanizmanın konfig tarafı tek satır: **IRQ0[0-7]**
(ve istenirse IRQ1[0-7]) girişinin açık olması. Demo projede `PSU__USE__IRQ0
= 1` — 8 bitlik ilk grup açık, üç teli dolu.

[[ekran: 16 | PS-PL Configuration — Interrupts, PL to PS IRQ0
rozet 1: IRQ0[0-7] — açık; blok dizayndaki pl_ps_irq0 pini bu satırdan doğar.
rozet 2: IRQ1[0-7] — kapalı; ikinci 8'lik grup gerekmedi.
]]

Zincirin tamamını Bölüm 3'te seçip vurgulamıştık; şimdi anlamlandır:

[[sema: sema-08-interrupt-yolu | Şema 8 — Interrupt yolculuğu: IP'nin tek teli → concat demeti → pl_ps_irq0 → GIC → ISR. Alt tabloda demo projenin gerçek eşleşmesi.]]

Kritik bilgi **ID eşleşmesidir**: `pl_ps_irq0`'ın bitleri GIC'te sabit
ID bloğuna düşer — bit0'dan itibaren **121, 122, 123, ...** (UltraScale+
için ilk grup 121-128). Demo projede concat sırası:

| Concat girişi | Kaynak IP | GIC ID |
|---|---|---|
| In0 | `axi_timer_0/interrupt` | 121 |
| In1 | `axi_uartlite_dbg/interrupt` | 122 |
| In2 | `axi_gpio_led/ip2intc_irpt` | 123 |

Bu tabloyu her projede kendin çıkarmalısın; tek kaynağı blok dizayndaki
concat bağlantı sırasıdır.

:::tuzak
Concat'a yeni bir kaynak *araya* eklendiğinde (örn. In1'e yeni IP, eskiler
kayar) bütün ID'ler değişir. Donanımcı "sadece bir IP ekledim" der, senin
timer handler'ın artık UART kesmesine bağlıdır ve hiçbir derleyici bunu
görmez. .xsa güncellemesi aldığında ID tablosunu yeniden çıkarmak refleks
olmalı.
:::

:::yazilima-yansimasi
Baremetal tarafta bu zincir şöyle kapanır: `XScuGic_Connect(&Gic, 121,
TimerHandler, ...)` — 121 sayısı yukarıdaki tablodan gelir; BSP'de
`XPAR_FABRIC_AXI_TIMER_0_INTERRUPT_INTR` gibi türetilmiş bir sembol olarak
da bulunur (adı instance adından türediği için concat sırası değişse bile
sembol doğru ID'yi taşır — elle 121 yazmak yerine sembolü kullan).
Linux tarafında aynı bilgi device tree'de `interrupts = <0 89 4>` biçiminde
görünür; oradaki 89 = 121 − 32 (SPI numaralandırma ofseti). İki dünyada da
kaynak aynı: bu sayfa + concat sırası.
:::

## Reset sinyalleri: kısa ama zorunlu not

PS, PL'e yazılım kontrollü reset hatları da verir: `pl_resetn0-3`
(`PSU__NUM_FABRIC_RESETS = 1` — demo projede bir adet). Blok dizayndaki
`proc_sys_reset` bloğu bu ham sinyali alır, clock'a senkronlar ve IP'lere
dağıtır. Yazılım açısından bilmen gereken tek şey: PS yeniden başladığında
PL IP'lerinin register'ları da bu hat üzerinden temizlenir; "warm reset
sonrası IP ayarlarım niye uçtu" sorusunun cevabı budur.

:::deneme id=deneme-6-1
**Hedef:** ID tablosunu kendin çıkar.

[[adim: Open Block Design → irq_concat bloğuna odaklan (Ctrl+F → "concat")]]

Demo 1'de concat'ın In0/In1/In2 girişlerine tıklayıp her telin kaynağını
vurgula. Üç satırlık kendi ID tablonu yaz: kaynak IP → concat girişi →
GIC ID. Sonra yukarıdaki tabloyla karşılaştır.

::cozum::
In0 ← axi_timer_0 → 121; In1 ← axi_uartlite_dbg → 122; In2 ←
axi_gpio_led → 123. Tablon farklıysa iki ihtimal: ya teli yanlış izledin
ya da (gerçek projelerde) donanımcı sırayı senin varsaydığından farklı
bağladı — ikinci ihtimal tam da bu alışkanlığın var olma nedeni.
:::

:::ozet
- M_ = PS konuşur, S_ = PS dinler. Demo: yalnız HPM0 FPD açık, 128 bit.
- Erişim teşhis sırası: kapı → SmartConnect dalı → adres.
- Interrupt ID'leri concat sırasından doğar; ilk grup 121'den başlar.
  Elle ID yazma, XPAR_FABRIC_* sembolünü kullan.
- pl_resetn + proc_sys_reset ikilisi PL'in reset ağacıdır; PS resetinde
  PL register'ları da sıfırlanır.
:::
