# Bölüm 3 — Dijital Sinyal Yolu

{{sec:2}}'nin sonunda bir sayı bırakmıştık: 2.94912 GS/s'de 16 bit üreten
tek bir ADC kanalı, saniyede ~47 gigabit ham veri demektir. Dört kanallı bir
AFE'de bu ~189 Gb/s eder. Bu sel, ne FPGA'ya taşınabilir ne de çoğu
uygulamada gereklidir: radar alıcın 200 MHz'lik bir bantla ilgileniyorsa,
geri kalan spektrum çöptür. Modern AFE'nin cevabı, veriyi **çip içinde,
daha ADC'nin dibindeyken eritmektir**: DDC ilgilendiğin bandı seçer, hızı
düşürür; kalan makul akışı da JESD204 seri linki taşır. Bu bölüm o dijital
yolu — DDC/DUC, NCO, I/Q kavramı — ve bölümün sonunda "neden seri link,
neden JESD?" sorusunun cevabını verir.

::: ogren
- I/Q (kompleks) verinin ne olduğunu ve neden gerektiğini
- DDC/DUC bloklarını: NCO + mixer + decimation/interpolation
- NCO'nun mekaniğini ve faz koherensi sorusunun nereden çıktığını
- Kanal başına veri hızının uçtan uca hesabını (4 kanallı senaryo)
- LVDS'in neden duvara tosladığını ve JESD204'ün neden doğduğunu
:::

## Neden kompleks (I/Q) veri?

ADC'den çıkan örnekler **gerçek** (real) sayılardır ve gerçek bir sinyalin
spektrumu DC etrafında simetriktir: +f'teki her bileşenin −f'te aynası
vardır. Bu simetri yüzünden gerçek veride "pozitif ve negatif frekansı ayırt
etmek" diye bir şey yoktur — gerek de yoktur, spektrum zaten yarıya kadar
anlamlıdır.

Ama bandı DC etrafına çektiğinde iş değişir. 2.8 GHz merkezli 200 MHz'lik
bandı "sıfıra indirdiğinde", bandın alt yarısı negatif frekanslara (−100..0),
üst yarısı pozitife (0..+100) düşer ve bunlar **farklı bilgidir** — artık
ayırt etmek zorundasın. Tek gerçek sayı dizisi bunu yapamaz; çözüm, her
örneği iki bileşenle taşımak: I (in-phase) ve Q (quadrature), yani kompleks
örnek x = I + jQ. Kompleks veride spektrum simetrik olmak zorunda değildir;
fs_kompleks örnek/saniye, tam fs_kompleks genişliğinde bir bandı temsil eder
(gerçek verinin fs/2'sine karşılık). {{sec:1}}'deki zero-IF mimarisinin I/Q
mixer'la yaptığı tam buydu — birazdan aynısını dijitalde, kusursuz yapacağız.

## DDC: bandı seç, hızı düşür

DDC (digital downconverter) üç işi ardışık yapar ({{fig:d05}}):

![ADC yolu: ADC core'dan SerDes lane'lerine. DDC'nin veri hacmini nasıl erittiğine ve hız etiketlerine dikkat; transport/link katmanları §5–7'nin konusu.](../diagrams/svg/d05.svg)

1. **NCO + mixer**: NCO (numerically controlled oscillator — sayısal
   kontrollü osilatör) istediğin merkez frekansında dijital bir kompleks
   sinüs üretir; mixer (çarpıcı) gelen örnekleri bununla çarpar. Bu,
   spektrumu kaydırır: NCO frekansındaki bant DC'ye gelir. Zero-IF'in analog
   LO+mixer'ının dijital ikizi — ama burada 90° *tam* 90°'dir, DC offset
   yoktur, LO kaçağı yoktur. Zero-IF'in tüm analog dertleri, işi dijitale
   taşıyınca tanım gereği yok olur.
2. **Decimation filtreleri**: bant artık DC etrafında; bandın dışını keskin
   dijital filtreler atar. Tipik zincir, kaba ama ucuz bir ilk kat (CIC
   sınıfı) + keskin FIR katlarıdır; sen genelde yalnız toplam **decimation
   oranı D**'yi seçersin.
3. **Seyreltme (÷D)**: filtrelenmiş sinyalin bant genişliği artık düşük;
   Nyquist gereği her D örnekten birini tutmak yeterlidir. Kritik sıra:
   **önce filtrele, sonra seyrelt** — tersini yaparsan bant dışı her şey
   {{sec:1}}'deki katlanmayla bandının içine iner.

Bedava hediye: {{sec:2}}'deki process gain. Gürültü tabanının bant dışı
kısmını decimation filtresi attığı için, D oranında seyreltme SNR'a
10·log10(D/2)'ye varan katkı yapar (kompleks çıkışta).

**Yazılıma dokunduğu yer:** DDC konfigürasyonu — NCO frekansı, D oranı,
hangi DDC'nin hangi ADC'ye bağlı olduğu — init'te senin yazdığın
register'lardır. Ve dikkat: D ve çıkış hızı, {{sec:5}}'te göreceğin JESD
link parametreleriyle **kilitli bir denklem** oluşturur; DDC oranını "sonra
değiştiririm" diyemezsin, link konfigürasyonu da değişir.

## DUC: aynanın verici hali

Verici yolda aynı mantık ters akar ({{fig:d06}}): FPGA'dan gelen düşük hızlı
I/Q akışını **interpolation** filtreleri fs'e çıkarır (araya örnek doldurup
imajları filtreleyerek), NCO + mixer bandı hedef merkez frekansına taşır,
DAC analog dünyaya döndürür. DDC için söylenen her şey simetrik geçerlidir —
seçtiğin interpolation oranı link parametrelerine kilitlidir, NCO frekansı
senin register'ındır.

![DAC yolu: lane'lerden analog çıkışa; D05'in aynası. Rekonstrüksiyon filtresi ve NRZ/mix-mode seçimi §2.6'da anlatıldı.](../diagrams/svg/d06.svg)

## NCO: mekanik ve ilk koherens sorusu

NCO'nun kalbi bir **faz akümülatörüdür**: her clock'ta sabit bir artış (FTW,
frequency tuning word) eklenen W bitlik bir sayaç. Sayacın üst bitleri bir
sinüs tablosunu (veya CORDIC'i) adresler. Frekans çözünürlüğü:

```text
Δf = fs / 2^W
```

Örnek: fs = 2.94912 GS/s, W = 32 bit → Δf = 2.94912×10⁹ / 2³² ≈ **0.69 Hz**.
GHz'ler dünyasında hertz-altı adım — dijital sentezin gücü.

Şimdi kritik gözlem: iki kanalın NCO'su aynı frekansa ayarlandığında,
çıkışlarının **fazları** akümülatörlerin *ne zaman sıfırlandığına* bağlıdır.
Kanal A'nın NCO'su kanal B'ninkinden bir clock sonra başladıysa, aralarında
sabit ama rastgele bir faz farkı olur — ve beamforming yapan bir sistemde bu
felakettir. "Tüm NCO'ları aynı anda, bilinen bir anda sıfırla" ihtiyacı,
{{sec:9}}'daki SYSREF'in ve {{sec:10}}'daki multi-chip senkronizasyonun ana
müşterilerinden biridir. Şimdilik not et: **hız problemini çözen her blok,
bir senkronizasyon problemi doğurur.**

## Uçtan uca hesap: 4 kanallı AFE senaryosu

Somutlaştıralım. Senaryo: 4 alıcı kanallı bir RF-sampling AFE; her ADC
2.94912 GS/s, 16-bit taşıma (N′ = 16); her kanalda DDC, D = 8, çıkış
kompleks.

| Adım | Hesap | Kanal başına | 4 kanal |
|---|---|---|---|
| Ham ADC çıkışı | 2.94912 G × 16 bit | 47.19 Gb/s | 188.7 Gb/s |
| DDC sonrası örnek hızı | 2.94912 G ÷ 8 | 368.64 MSPS (kompleks) | — |
| DDC sonrası veri | 368.64 M × 32 bit (I+Q) | 11.80 Gb/s | 47.19 Gb/s |
| JESD204C payload | ×(66/64) kodlama | 12.17 Gb/s | 48.67 Gb/s |
| L = 4 lane'e bölünce | 48.67 ÷ 4 | — | **12.17 Gb/s / lane** |

Okuma: DDC, ham 188.7 Gb/s'yi 47.2 Gb/s'ye indirdi (D=8 ama kompleks çıkış
veriyi ikilediği için net kazanç D/2 = 4×). Kalan akış, 64b/66b kodlamanın
%3.1'lik vergisiyle 4 lane üzerinden lane başına ~12.17 Gb/s ile taşınıyor —
modern bir FPGA transceiver'ı için rahat bir hız. Buradaki "M converter,
N′ bit, L lane" ilişkisinin resmî formülünü {{sec:5}}'te türeteceğiz; bu
tablo, o formülün etten kemiğe bürünmüş hali.

## LVDS duvarı ve JESD204'ün doğuşu

Peki bu 47 Gb/s'yi neden *seri* taşıyoruz? On beş yıl önce cevap paralel
arayüzdü: her biti kendi LVDS (low-voltage differential signaling) çiftinde,
yanında bir clock çiftiyle göndermek. LVDS çiftinin pratik tavanı ~1 Gb/s'dir
(standardın önerisi daha da muhafazakârdır). Hesap acımasız:

- 47.19 Gb/s ÷ ~1 Gb/s ≈ **48 diferansiyel çift = 96 pin** — yalnız veri
  için; clock ve frame sinyalleri hariç.
- Aynı yük, JESD204C ile: **4 lane = 8 pin.**

12 kat pin farkı; ama asıl katil pin sayısı bile değil, **skew**'dur:
paralel bus'ta her bit ayrı iz üzerinden gider ve hepsinin aynı clock
kenarında geçerli olması gerekir. 96 izin uzunluğunu picosaniye hassasiyetle
eşlemek, hız arttıkça imkânsızlaşır. Seri linkte ise clock veriye gömülüdür
(embedded clock — {{sec:4}}'ün ana konusu); tek çiftin içinde skew diye bir
şey yoktur, lane'ler arası kayıklığı da alıcı tarafta elastic buffer'lar
({{sec:6}}) çözer.

JEDEC bu ihtiyaç için JESD204 ailesini standartlaştırdı: ilk sürüm 2006'da
çıktı, 204A (2008) çoklu lane hizalamayı, 204B (2011) 12.5 Gb/s'ye ölçek ve
deterministic latency'yi, 204C (2017 sonu) 64b/66b kodlamayla 32 Gb/s'yi
getirdi. Ailenin soy ağacını ve "hangi harf sana ne verir" sorusunu
{{sec:5}}'te ayrıntısıyla ele alacağız.

::: not
Seri linkin bedeli karmaşıklıktır: artık bir CDR'ın kilitlenmesi, lane'lerin
hizalanması, link'in "ayağa kalkması" gerekir — yani bu dokümanın geri
kalanının konusu. Pin ve skew problemini protokol karmaşıklığıyla takas
ettik; senin işin o karmaşıklığı yönetmek.
:::

Buraya kadar sinyal işleme dünyasındaydık. Şimdi vites değişiyor: önümüzdeki
iki kısım ({{sec:4}}–{{sec:7}}) o "4 lane"in içinde bit'lerin fiziksel ve
mantıksal olarak nasıl yaşadığını anlatıyor. Fizikten başlıyoruz: bir çift
bakır iz üzerinde 12 Gb/s nasıl hayatta kalır?

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- Analog Devices, *JESD204B vs. Serial LVDS Interface Considerations for
  Wideband Data Converter Applications* — LVDS ~1 Gb/s pratik sınırı ve
  pin/skew karşılaştırması.
- Analog Devices, MS-2374: *What is JESD204 and why should we pay
  attention to it?* — JESD204'ün doğuş gerekçesi ve sürüm tarihçesi.
- TI, SBAA517: *JESD204B/C overview* — kodlama ek yükleri, sürüm farkları.
- ADI/TI DDC-DUC ve NCO dokümantasyonu (MxFE / AFE79xx fonksiyonel
  açıklamaları) — DDC zinciri ve NCO mekaniği.
- Toplu ve linkli liste: {{sec:19}}.

</details>
