# Bölüm 1 — İki Dünyanın El Sıkışması

## Neden umursamalısın

Kartın açılmıyor, konsol sessiz, DMA veri getirmiyor. Bu belirtilerin her
birinin kök nedeni yazılımda olabileceği gibi donanım *konfigürasyonunda* da
olabilir — yani Vivado projesindeki bir ayarda. O ayarı okuyamıyorsan iki
seçeneğin kalır: donanımcıyı her seferinde masana çağırmak ya da körlemesine
denemek. Bu bölüm üçüncü seçeneği açar: teslimat zincirini tanı, hangi
sorunun cevabının hangi dünyada yaşadığını bil.

## İş bölümü: kim neyi üretir

Donanımcı Vivado'da çalışır: blok dizaynı kurar, PS'i (Processing System —
çipin işlemci tarafı) yapılandırır, PL'e (Programmable Logic — FPGA dokusu)
IP'leri yerleştirir, sentez ve implementasyonu koşturur, bitstream üretir.
Sen Vitis'te (ya da Yocto/PetaLinux hattında) çalışırsın: BSP, driver,
uygulama.

İki dünyanın buluşma noktası tek bir dosyadır: **.xsa** (Xilinx Support
Archive). Donanımcı Vivado'dan "Export Hardware" ile bu dosyayı üretir;
sen onu Vitis'e verip platformunu kurarsın. O an, Vivado'daki yüzlerce
ekranın içeriği senin dünyana akar: adres haritası `xparameters.h`
tanımlarına, aktif çevre birimleri BSP driver listesine, clock frekansları
driver başlangıç parametrelerine dönüşür.

[[sema: sema-01-el-sikisma | Şema 1 — Teslimat zinciri: Vivado projesi → .xsa → Vitis platformu → uygulama. Sol tarafta üretilen her ayar, sağ tarafta bir #define ya da BSP davranışı olarak karşına çıkar.]]

:::analoji
.xsa dosyası, donanımcıyla aranızdaki API sözleşmesidir. REST servisinin
OpenAPI şeması neyse, .xsa da odur: karşı tarafın ne sunduğunu, hangi
adreste sunduğunu, hangi parametrelerle çalıştığını beyan eder. Şemayı
okuyabilen entegrasyonu tartışabilir; okuyamayan her pull request'te
servis sahibini masasına çağırır.
:::

## Vivado'da ne arıyorsun: dört soru

Bir yazılımcının Vivado projesinde aradığı şeylerin neredeyse tamamı dört
soruya iner:

1. **Hangi IP'ler var?** Blok dizayndaki kutular — hangi çevre birimleri,
   hangi hızlandırıcılar sana görünür olacak? (Bölüm 3)
2. **Adresleri ne?** Her IP'nin register bloğu işlemcinin adres uzayının
   neresine haritalanmış? (Bölüm 7)
3. **Clock'ları ne?** İşlemci, çevre birimleri ve PL IP'leri hangi
   frekanslarda çalışıyor; baud/timer hesapların hangi değere dayanacak?
   (Bölüm 5)
4. **Interrupt'ları nereye bağlı?** PL'deki hangi kesme hangi ID ile
   GIC'e (Generic Interrupt Controller) düşüyor? (Bölüm 6)

Kılavuzun geri kalanı, bu dört sorunun cevabını Vivado ekranlarından okuma
pratiğidir. Dördünü de cevaplayabildiğin gün "Vivado bilmiyorum" cümlesini
bırakabilirsin — donanım tasarlamayı bilmiyorsun, ama donanımı *okumayı*
biliyorsun.

## Donanımcıya doğru soru sormak

Vivado okur-yazarlığının görünmeyen faydası iletişimdir. "Kart çalışmıyor"
ile "PS-PL Configuration'da HPM0 açık görünüyor ama Address Editor'da GPIO
segmenti unmapped — bilerek mi?" cümleleri, donanımcıda iki farklı öncelik
sınıfına düşer. İkincisi beş dakikada cevap bulur.

:::ekip-notu
Donanımcının projesine dokunmadan sorularını topla. En verimli format,
ekran adı + gözlem + beklenti üçlüsüdür: "Clock Configuration'da PL0
100 MHz görünüyor; IP'lerin timing'i 150 MHz'e göre konuşulmuştu —
hangisi doğru?" Bu format hem senin okuduğunu kanıtlar hem donanımcının
Vivado'yu açmadan cevap vermesini sağlar.
:::

:::yazilima-yansimasi
Bu bölümün tek cümlelik özeti: `xparameters.h`, device tree ve BSP
konfigürasyonun **türetilmiş** dosyalardır — kaynakları Vivado projesidir.
Elle düzelttiğin her değer, bir sonraki .xsa güncellemesinde ezilir. Yanlış
görünen bir adres ya da frekansın düzeltileceği yer kod değil, donanımcının
Vivado projesidir.
:::

:::deneme id=deneme-1-1
**Hedef:** Teslimat zincirini kendi gözünle gör.

Repo'daki demo projeyi kur ve üretilen .xsa dosyasını bul:

```tcl
vivado -mode batch -source vivado/rfsoc/create_bd.tcl
vivado -mode batch -source vivado/export_visuals.tcl -tclargs ultrascale
```

Soru: `vivado/work/demo_ultrascale/` altında oluşan `.xsa` dosyasının adı ne
ve boyutu kaç MB civarında?

::cozum::
`ultrascale-demo.xsa`, tipik olarak birkaç MB (bitstream içermediği için
küçüktür — pre-synthesis export). Dosya aslında bir ZIP arşividir;
`unzip -l ultrascale-demo.xsa` ile içindeki `sistem.hwh` donanım tarif
dosyasını ve `psu_init.*` başlangıç scriptlerini görebilirsin. Bölüm 7'de
bu içeriği tek tek okuyacağız.
:::

:::ozet
- Donanımcı Vivado'da üretir, sen Vitis'te tüketirsin; köprü .xsa dosyasıdır.
- Yazılımı ilgilendiren her Vivado ayarı dört sorudan birine hizmet eder:
  IP'ler, adresler, clock'lar, interrupt'lar.
- xparameters.h türetilmiş dosyadır; gerçeğin kaynağı Vivado projesidir.
- Vivado okur-yazarlığı donanımcıyla konuşma dilini değiştirir: ekran adı +
  gözlem + beklenti.
:::
