# Bölüm 10 — Sentez: Bring-up Öncesi PS Kontrol Listesi

## Neden umursamalısın

Yeni bir proje teslim aldın ve kartı ayağa kaldıracaksın. Bu bölüm, tüm
kılavuzu tek bir yürütülebilir listeye damıtıyor: sırayla yürü, her maddeyi
işaretle, sonunda "bring-up'a hazır" de. Liste tek başına paylaşılabilir —
ekibe "yeni proje geldiğinde bunu koştur" diye verilebilir.

## Karar akışı

[[sema: sema-12-bringup-akis | Şema 12 — Bring-up öncesi PS kontrol akışı: proje açılışından konsol/clock/DDR/adres/interrupt kontrollerine ve "hazır" durumuna. Her adımın "hata yolu" kırmızıyla işaretli.]]

## Kontrol listesi

Aşağıdaki kutucuklar tarayıcında saklanır; kaldığın yerden devam edersin.
Her madde ilgili bölüme bağlıdır.

:::kontrol id=kontrol-bringup
### 0 — Hazırlık
- Projeyi **kaydetmeden** aç; git'teki kopyaya dokunma ([Bölüm 2](#02-ilk-giris))
- `.xsa`'nın tarihini kontrol et — bayat mı? ([Bölüm 7](#07-adres-haritasi))
### 1 — Konsol
- Debug UART hangi (PS UART0 mı, PL uartlite mı)? ([Bölüm 5](#05-ps-ayarlari-1))
- UART MIO'da mı EMIO'da mı? EMIO ise bitstream şart ([Bölüm 5](#05-ps-ayarlari-1))
- Fiziksel pin kartın şematiğinde konektöre gidiyor mu?
### 2 — Clock
- UART referans saatinin **Actual** değeri kaç? ([Bölüm 5](#05-ps-ayarlari-1))
- PL fabric clock (pl_clk0) açık ve beklenen frekansta mı?
### 3 — DDR
- DDR açık mı; tip/hız/genişlik doğru mu? ([Bölüm 5](#05-ps-ayarlari-1))
- Versal ise: DDR NoC/DDRMC'de mi (CIPS'te değil)? ([Bölüm 8](#08-versal))
- Address Editor'da DDR segmenti var mı?
### 4 — Adres
- Address Editor'da **unmapped** satır var mı? ([Bölüm 7](#07-adres-haritasi))
- Her PL IP'nin base adresi xparameters ile eşleşiyor mu?
- Validate Design temiz geçti mi (çakışma yok)? ([Bölüm 7](#07-adres-haritasi))
### 5 — Interrupt
- pl_ps_irq açık mı; concat sırası → IRQ ID tablosu çıkarıldı mı? ([Bölüm 6](#06-ps-ayarlari-2))
- Kodda `XPAR_FABRIC_*` sembolü kullanılıyor mu (elle ID değil)?
### 6 — PS-PL
- PL IP'ye giden master kapı (HPM0) açık mı? ([Bölüm 6](#06-ps-ayarlari-2))
- PL→DDR DMA gerekiyorsa S_AXI_HP açık mı; cache tutarlılığı sözleşmesi net mi?
:::

## Kapanış: bu kılavuz sana ne kazandırdı

Başlangıçtaki dört soruyu ([Bölüm 1](#01-el-sikisma)) artık tek başına
cevaplayabiliyorsun:

| Soru | Nereden | Bölüm |
|---|---|---|
| Hangi IP'ler var? | Blok dizayn | 3 |
| Adresleri ne? | Address Editor | 7 |
| Clock'ları ne? | Clock Configuration | 5 |
| Interrupt'ları nereye? | PS-PL + concat | 6 |

Donanım tasarlamayı öğrenmedin — buna gerek de yoktu. Donanımı *okumayı*
öğrendin: teslim aldığın projeyi açıp yolunu bulmayı, ayarları yazılım
karşılığına çevirmeyi, doğru soruyu doğru ekrandan sormayı. "Vivado
bilmiyorum" cümlesini artık bırakabilirsin.

:::yazilima-yansimasi
Bu kontrol listesinin çıktısı bir belgedir: her yeni proje için doldurulmuş
hâlini `bring-up-notlari.md` olarak sakla. Bir sonraki kart geldiğinde
karşılaştırma yaparsın; "bu projede UART neden EMIO'da, öncekinde MIO'daydı"
gibi sorular böyle hızlı cevap bulur. Kontrol listesi tek seferlik değil,
projeler arası kurumsal hafızadır.
:::

:::deneme id=deneme-10-1
**Hedef:** Kontrol listesini gerçek bir demo üzerinde uçtan uca doldur.

Demo 1'i (ya da Demo 2'yi) aç ve yukarıdaki listeyi baştan sona işaretle.
Takıldığın her maddede ilgili bölüme dön. Sonuna geldiğinde tüm kutucuklar
işaretliyse: bu projeyi bring-up'a hazır okudun demektir.

::cozum::
Demo 1 için beklenen sonuçlar: konsol = PS UART0, MIO 18-19, MIO yolu
(bitstream'siz çalışır); UART ref 99.99 MHz; DDR4 açık, 4GB; unmapped yok,
validate temiz; IRQ0 açık, timer/uartlite/gpio → ID 121/122/123; HPM0 açık.
Hepsini işaretlediysen liste seninle çalışıyor demektir.
:::

:::ozet
- Bring-up kontrol listesi: 0-hazırlık, 1-konsol, 2-clock, 3-DDR, 4-adres,
  5-interrupt, 6-PS-PL.
- Her madde bir bölüme ve bir gerçek ekrana bağlı.
- Çıktısı paylaşılabilir bir belge; projeler arası hafıza.
- Dört başlangıç sorusunu artık tek başına cevaplıyorsun.
:::
