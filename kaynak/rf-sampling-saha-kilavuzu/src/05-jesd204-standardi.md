# Bölüm 5 — JESD204 Standardı: A'dan C'ye

{{sec:4}}'te bit'leri taşıyan makineyi gördük. Ama makine, yükün nasıl
paketleneceğini bilmez: hangi ADC örneği hangi lane'de, hangi bit sırasıyla,
hangi çerçevede gidecek? İki uç bu konuda harfiyen anlaşmazsa, link
elektriksel olarak kusursuz çalışır ve **tamamen anlamsız veri** taşır.
JESD204, JEDEC'in bu anlaşmayı standartlaştırmasıdır: converter'lar ile
lojik cihazlar (FPGA/ASIC) arasındaki seri linkin katmanlarını, çerçeve
yapısını ve senkronizasyon mekaniğini tanımlar. Bu bölüm ailenin haritasını
çıkarır, meşhur harf parametrelerini tek tek tanımlar ve bir link
konfigürasyonunu uçtan uca hesaplar. Bu bölümü sindirirsen {{sec:6}} ve
{{sec:7}} detay, {{sec:14}} ise uygulama olarak gelecek.

::: ogren
- JESD204 ailesinin soy ağacını ve hangi sürümün ne getirdiğini
- Katman modelini: transport / scrambling / data link / physical (D04)
- Link parametrelerini tek tek: L, M, F, S, N, N′, K, E, CS, CF, HD
- Lane rate formülünü türetmeyi ve uçtan uca örnek hesabı
- Subclass 0/1/2 ayrımını ve deterministic latency'nin nerede yaşadığını
:::

## Aile tarihçesi: neden dört harf var?

- **JESD204 (2006):** ilk adım — converter ile lojik arasında tek seri
  lane, 3.125 Gb/s'ye kadar. Çığır açıcı ama tek lane, tek converter.
- **JESD204A (2008):** çoklu lane ve lane hizalama geldi; çok converter'lı
  cihazlar tek linkte konuşabilir oldu. Hız tavanı aynı kaldı.
- **JESD204B (2011):** büyük sıçrama — 12.5 Gb/s, ve bu dokümanın kalbini
  oluşturan iki kavram: **deterministic latency** (linkin gecikmesinin her
  açılışta aynı olması) ve onu mümkün kılan **subclass/SYSREF** mekaniği.
  Endüstrinin bugün hâlâ en yaygın konuştuğu lehçe.
- **JESD204C (2017):** 64b/66b ile 32 Gb/s, CRC/FEC ile hata dayanıklılığı,
  daha temiz bir senkronizasyon modeli (SYNC~ pinine elveda). Yeni nesil
  RF AFE'lerin (AFE7900, AD9084 sınıfı) ana dili.

::: not
JESD204D (2023) 116 Gb/s'ye PAM4 ile çıkar; RF AFE dünyasına henüz inmedi
ama yönü gösteriyor. Bu doküman B ve C üzerine kurulu — sahadaki donanımın
dili bu ikisi.
:::

Hangisini *sen* kullanacaksın? Genelde bu seçim senin değil, AFE'nin ve
FPGA IP'nin destek matrisinin kararıdır; modern RF AFE'lerde pratik cevap
"mümkünse C, mecbursan B"dir. İkisini de bilmen gerekmesinin sebebi:
sahadaki kartların yarısı hâlâ B konuşur ve C'nin kavramları B'nin üstüne
kurulmuştur.

## Katman modeli

![JESD204 katman modeli. TX ve RX yığınları aynadır; parametre setleri iki uçta birebir eşleşmek zorundadır. Alt kısımdaki debug pusulası, hangi belirtinin hangi katmanı işaret ettiğini gösterir.](../diagrams/svg/d04.svg)

Dört katman, dört ayrı sorumluluk ({{fig:d04}}):

1. **Transport**: converter örneklerini oktetlere, oktetleri frame'lere
   yerleştirir. "M converter'ın S örneği, N′ bit'le, L lane'e nasıl
   dağılır" haritası burasıdır — birazdan tanımlayacağımız parametrelerin
   çoğu bu katmanda yaşar.
2. **Scrambling**: veriyi bir polinomla karıştırır; amaç spektral tepeleri
   yaymak ve veri desenine bağlı davranışı kırmak ({{sec:4}}'teki geçiş
   yoğunluğu/DC balance ihtiyacının müttefiki). 204B'de opsiyonel (ama
   pratikte hep açık; polinom 1+x¹⁴+x¹⁵), 204C'de zorunludur (Ethernet'le
   aynı x⁵⁸+x³⁹+1). İkisi de self-synchronous'tur: descrambler, akışın
   kendisinden senkronlanır, ayrıca hizalama istemez.
3. **Data link**: linkin "ayağa kalkma" protokolü ve çerçeve sınırlarının
   korunması. B'de CGS/ILAS ve 8b/10b ({{sec:6}}), C'de sync header ve
   multiblock hiyerarşisi ({{sec:7}}).
4. **Physical (PHY)**: {{sec:4}}'ün tamamı — SerDes, CDR, eşitleme.

{{fig:d04}}'ün altındaki *debug pusulası*nı şimdiden not al: belirtinin
hangi katmana ait olduğunu teşhis etmek, {{sec:16}}'daki tüm debug akışının
ilk adımıdır.

## Link parametreleri: harflerin sözlüğü

Bir JESD204 linkini tarif etmek, şu parametre setini iki uca da birebir
aynı yazmak demektir:

| Parametre | Tanım | Tipik aralık |
|---|---|---|
| **L** | Lane sayısı | 1–8 |
| **M** | Converter sayısı (mantıksal; I ve Q ayrı sayılır) | 1–256 |
| **F** | Lane başına, frame başına oktet sayısı | 1, 2, 4… |
| **S** | Converter başına, frame başına örnek sayısı | çoğunlukla 1 |
| **N** | Converter çözünürlüğü (bit) | 12–16 |
| **N′** | Örnek başına iletilen bit (N + dolgu/kontrol; 4'ün katı) | 16 |
| **K** | Multiframe başına frame sayısı (B) | bkz. kural |
| **E** | Extended multiblock başına multiblock sayısı (C) | çoğunlukla 1 |
| **CS** | Örnek başına kontrol biti | 0–3 |
| **CF** | Frame başına kontrol sözcüğü | 0–32 |
| **HD** | High-density: bir örneğin lane sınırını aşabilmesi | 0/1 |

Kavramları hikâyeleştirelim. **M**, linkin taşıdığı mantıksal converter
sayısıdır: {{sec:3}}'teki 4 kanallı senaryoda her kanal I+Q ürettiği için
M = 8'dir — fiziksel ADC sayısı değil, veri akışı sayısı. **N′**, örnek
başına *hat üzerinde* taşınan bit'tir: 14-bit ADC (N=14) tipik olarak 2 bit
dolguyla N′=16 taşınır, çünkü oktet hizası hayatı kolaylaştırır. **F**,
frame'in lane başına oktet cinsinden boyudur ve serbest değildir:

```text
F = (M × S × N′) / (8 × L)
```

— transport katmanının muhasebe denklemi: frame başına üretilen tüm bit'ler
(M·S·N′), L lane'in oktetlerine tam bölünmek zorunda.

**Frame ve multiframe/EMB**: bir frame, S örneklik bir zaman dilimidir;
frame clock = converter örnek hızı / S. Tek frame çok kısa olduğu için
(bizim örnekte ~2.7 ns) senkronizasyon için daha büyük bir birim gerekir:
B'de **multiframe** (K frame), C'de **extended multiblock** (E multiblock).
Bu büyük birimlerin sınırları, {{sec:9}}–{{sec:10}}'daki deterministic
latency mekanizmasının zaman cetvelidir — SYSREF'in hizaladığı sayaçlar
(LMFC/LEMC) tam olarak bu sınırları sayar. **K** serbest değildir (204B):

```text
ceil(17/F) ≤ K ≤ min(32, floor(1024/F))   ve   F×K, 4'ün katı
```

Alt sınır ILAS'ın konfigürasyon verisinin bir multiframe'e sığması, üst
sınır buffer boyutları içindir. 204C'de multiblock sabit 32 bloktur (lane
başına 256 oktet) ve K benzeri esneklik E ile sınırlı biçimde sürer.

**CS/CF**: örneklerin yanına iliştirilen kontrol bitleri (ör. ADC'nin
"bu örnekte taşma oldu" bayrağı). **HD**: bir örneğin iki lane'e bölünüp
bölünemeyeceği — F'yi küçültmek için kullanılan yoğun paketleme modu.
Çoğu RF AFE konfigürasyonunda CS=CF=0, HD=0 görürsün; varlıklarını bil,
datasheet'te görünce şaşırma.

::: dikkat
Parametreler **iki uçta birebir aynı olmak zorundadır** — biri register'a
F=4 yazıp öbürüne F=8 yazarsan link elektriksel olarak kalkar, CGS/ILAS
bile geçer, ama veri çorba olur. {{sec:16}}'daki "link geliyor ama veri
kayık" semptomunun bir numaralı şüphelisi parametre uyuşmazlığıdır.
Kontrol listesi: {{sec:17}}.
:::

## Uçtan uca hesap: lane rate formülünün türetimi

Formülü ezberlemek yerine türetelim. Link başına saniyede taşınacak payload:

```text
payload = M × N′ × (converter örnek hızı × S/S) = M × N′ × f_örnek   [bit/s]
```

(f_örnek: link'e giren converter başına örnek hızı — DDC'li sistemde DDC
*çıkış* hızı.) Bunu L lane paylaşır; kodlama vergisi eklenir:

```text
lane rate (204B) = M × N′ × f_örnek × (10/8) / L
lane rate (204C) = M × N′ × f_örnek × (66/64) / L
```

{{sec:3}}'ün senaryosuyla: M=8, N′=16, f_örnek=368.64 MSPS, S=1, L=4.
Payload = 8×16×368.64M = 47.19 Gb/s.

- **204B denemesi**: 47.19 × 1.25 / 4 = **14.75 Gb/s/lane** → 204B'nin
  12.5 Gb/s tavanının *üstünde*. Bu konfigürasyon B'de yasadışı: ya L=8'e
  çık (7.37 Gb/s/lane — pin ve routing maliyeti) ya da hızdan feragat et.
- **204C ile**: 47.19 × 66/64 / 4 = **12.17 Gb/s/lane** → rahat. Aynı işi
  yarı lane ile yapabilmek, C'nin %3'lük vergisinin gücüdür.

Kalan parametreler: F = (8×1×16)/(8×4) = **4 oktet/frame**. Frame clock =
368.64 MHz. B'de K seçimi: ceil(17/4)=5 ≤ K ≤ min(32, 256)=32, F×K 4'ün
katı → K=32 seçilir; LMFC = 368.64/32 = **11.52 MHz**. C'de multiblock =
256 oktet = 64 frame; E=1 ile LEMC = 368.64/64 = **5.76 MHz**. Bu iki sayı
({{sec:9}}'da göreceğiz) SYSREF frekansının tam böleni olmak zorunda —
frekans planının senkronizasyon ayağı buradan doğar.

Aynı hesabı kendi sisteminde yapmak için sıra: (1) f_örnek'i DDC planından
al, (2) M'yi kanal×I/Q'dan çıkar, (3) N′'yi datasheet'ten oku, (4) hedef
lane rate'e göre L'yi seç, (5) F'yi denklemden hesapla, (6) K/E'yi kurala
göre seç. {{sec:14}}'te bu zinciri Versal IP konfigürasyonuna birebir
eşleyeceğiz.

## Subclass'lar: determinizmin üç seviyesi

JESD204B üç subclass tanımlar; fark, **deterministic latency** (DL —
linkin toplam gecikmesinin her power-up'ta ve her cihazda aynı olması)
garantisinin nasıl sağlandığıdır:

- **Subclass 0**: DL garantisi yok. Link kalkar, veri akar, gecikme "o
  günkü şansa" bağlıdır. Tek kanallı, senkronizasyon derdi olmayan işler
  için yeterli.
- **Subclass 1**: DL, harici **SYSREF** sinyaliyle sağlanır — tüm
  cihazların LMFC/LEMC sayaçları SYSREF kenarıyla aynı âna hizalanır.
  Yüksek hızlı (≥500 MSPS sınıfı) sistemlerin ve bu dokümandaki tüm
  donanımın yolu. SYSREF'in tüm hikâyesi: {{sec:9}}.
- **Subclass 2**: DL, SYNC~ sinyalinin bırakılma anının TX tarafından
  zamanlama referansı olarak kullanılmasıyla sağlanır. Düşük örnekleme
  hızlarında işler; hız arttıkça SYNC~'in gidiş-dönüş zamanlaması
  yönetilemez hale gelir ve mekanizma pratikte ölür.

Pratik özet: **RF-sampling dünyası = subclass 1 = SYSREF.** Bu cümle,
KISIM III'ün ({{sec:8}}–{{sec:10}}) neden bu dokümanın kalbi olduğunun da
özetidir. 204C, kavramsal olarak subclass 1'in yolunu sürdürür: SYSREF,
LEMC sayacını hizalar.

Harita elimizde. Şimdi mikroskobu 204B'nin üstüne koyup linkin gerçekte
nasıl ayağa kalktığını izleyeceğiz: SYNC~ düşer, K28.5 yağmuru başlar,
ILAS geçidi yürür ve veri akar.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- Analog Devices, MS-2374: *What is JESD204 and why should we pay
  attention to it?* — sürüm tarihçesi ve motivasyon.
- TI, SBAA517: *JESD204B/C overview* — hız tavanları, parametre tanımları,
  kodlama ek yükleri, K kuralları (204C K≤256).
- EDN, *Understanding JESD204B link parameters* — parametre tanımları ve
  lane rate örneği.
- Intel JESD204B IP User Guide — K aralığı kuralı (F×K kısıtları).
- Analog Devices, JESD204B subclass makale serisi — subclass 0/1/2 ve
  deterministic latency.
- ADI JESD204C Primer (Analog Dialogue, 2 kısım) — 204C yapısı, E/K,
  LEMC.
- Toplu ve linkli liste: {{sec:19}}.

</details>
