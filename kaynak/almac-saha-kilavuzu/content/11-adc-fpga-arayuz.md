# Bölüm 11 — ADC'den FPGA'ya: Arayüz ve Saat
::meta onkosul=9,10,rf:link-parametreleri-harflerin-sozlugu acar=12,13,14,24,29 blok=arayuz rota=sayisal

:::neden-onemli
Sahadan soru: "JESD linki 'up' diyor, ILA'da veri akıyor ama spektrum
çöp; bir de her açılışta darbelerin TOA'sı 40 ns kayıyor." İki belirti, iki
katman: birincisi transport parametrelerinin ya da sözcük hizasının
uyuşmazlığı, ikincisi deterministik gecikmenin kurulmamış olması. ADC ile
FPGA arasındaki arayüz, kılavuzun en "elektriksel" konusu ama sonuçları
PDW'nin TOA alanına kadar gider. Bu bölüm, kardeş kılavuzun beş bölümde
anlattığı JESD204/SYSREF/saat dünyasını tek sayfada özetler, RFSoC'taki
halini gösterir ve almacın asıl ihtiyacına odaklanır: veri hangi formatta,
hangi saatle, kaç paralel şeritte geliyor?
:::

## Sezgi: nehir ve kanallar

ADC saniyede 2.4 milyar örnek üretir; FPGA kumaşı saniyede 300 milyon adım
atar. Nehri kanala sığdırmanın tek yolu, nehri **sekiz paralel kanala**
bölmektir: her adımda sekiz örnek birden gelir, FPGA sekizini aynı anda
işler. Bu, kılavuz boyunca **SSR** (super-sample rate) diye anacağımız
düzendir ve DSP'nin her bloğu ({{bolum:12}}'den itibaren) bu düzene göre
yazılır. Nehrin kaynağı ile kanallar arasında bir de köprü var: ayrı ADC
çipinde bu köprü yüksek hızlı seri hatlardır (JESD204), RFSoC'ta çip içi
bir veri yolu (AXI-Stream). Köprünün iki özelliği almacı doğrudan
ilgilendirir: veri **bit bit doğru** gelmeli ve **her açılışta aynı
gecikmeyle** gelmeli.

## Kavram: JESD204B/C tek sayfada

Ayrıntı için kardeş kılavuz; burada almacın ihtiyaç duyduğu kadar.

- **Lane ve link.** Bir *lane* tek bir diferansiyel seri çift (GT alıcı);
  bir *link*, aynı parametre setiyle çalışan L lane'in birlikte taşıdığı
  örnek akışıdır. Lane hızı 6–32 Gbps mertebesindedir.
- **Parametreler.** L (lane), M (converter — I ve Q ayrı sayılır), F
  (frame başına oktet), S (frame başına örnek), N (çözünürlük), N′ (hat
  üzerinde bit; 14 → 16), K (multiframe başına frame). Bunlar **iki uçta
  birebir aynı** yazılmalıdır; uyuşmazsa link kalkar, veri çorba olur
  ({{rf:link-parametreleri-harflerin-sozlugu|RF Örnekleme: link parametreleri}}).
- **Kodlama.** 204B 8b/10b (%25 ek yük), 204C 64b/66b (%3 ek yük) ve
  ileri hata düzeltme seçeneği; 204C aynı veri için daha az lane ya da daha
  düşük lane hızı demektir.
- **Subclass 1 ve SYSREF.** Deterministik gecikme için her iki cihazın
  multiframe sayaçları (LMFC/LEMC) ortak bir işaretle hizalanır; o işaret
  **SYSREF**'tir — bir saat değil, örnekleme saatiyle kaynak-senkron bir
  *hizalama emri* ({{rf:subclass-lar-determinizmin-uc-seviyesi|RF Örnekleme: subclass'lar}},
  {{rf:tanim-clock-degil-hizalama-emri|SYSREF tanımı}}).
- **Deterministik gecikme.** RX tarafındaki elastik tampon veriyi LMFC
  sınırı + RBD anında bırakır; böylece ADC girişinden FPGA'daki ilk
  register'a gecikme her açılışta ve her çipte aynı olur
  ({{rf:buffer-release-adim-adim|RF Örnekleme: buffer release}}). TOA
  ölçümünün ({{bolum:24}}) mutlak doğruluğu buna bağlıdır.
- **Çok çipli senkron.** Birden çok ADC'nin örnekleme anlarını hizalamak
  için hepsine aynı SYSREF ve aynı örnekleme saati, aynı bölücü zincirinden
  dağıtılır; yön bulma kartlarının ön şartı.

{{svg:g-110-jesd204-ozet.svg|JESD204B/C tek bakışta. Solda ADC (TX) ve FPGA (RX) tarafında aynalı dört katman — transport, scrambler, data link, PHY — ve aralarındaki L lane; parametre seti iki uçta aynı olmalı. Sağda subclass 1 zamanlaması: SYSREF kenarı iki cihazın LMFC sayaçlarını hizalar, RX SYNC~'i bırakır, TX ILAS ve veriyi LMFC sınırında başlatır, RX elastik tampon veriyi LMFC + RBD anında bırakır → deterministik gecikme. RFSoC'ta bu katmanlar yok; SYSREF yine çok tile hizası için gerekir.}}

:::formul id=veri-hizi baslik="Ham veri hızı ve lane hızı"
f: R_{ham} = f_s · N′ · M        R_{lane} = frac{R_{ham} · k}{L}        k = 10/8 (204B) · 66/64 (204C)
f: SSR genişliği  P = frac{f_s}{f_{fabric}}        bus genişliği = P · N′  (reel)  ·  2 · P · N′  (I/Q)
s: f_s | örnek hızı (converter başına) | Hz
s: N′ | hat üzerindeki örnek genişliği (14 bit → 16) | bit
s: M | converter sayısı (I/Q'da 2) | —
s: L | lane sayısı | —
s: P | fabric saati başına örnek sayısı (SSR) | —
o: f_s = {{s:adc.fs_msps}} MSPS, N = {{s:adc.bit}} bit → **{{s:adc.veri_hizi_gbps_14bit}} Gbps** ham; N′ = 16 ile **{{s:adc.veri_hizi_gbps_16bit_paket}} Gbps**. 204B, L = 8 → 38.4 · 1.25 / 8 = **6.0 Gbps/lane**; 204C, L = 4 → 38.4 · 1.031 / 4 ≈ **9.9 Gbps/lane**.
o: f_fabric = 300 MHz → P = 2400/300 = **8 örnek/saat**, bus 8 × 16 = **128 bit**. DDC çıkışında ({{s:ddc.cikis_fs_msps}} MSPS I/Q) P = 1, bus 32 bit, {{s:ddc.cikis_veri_hizi_gbps}} Gbps.
:::

## Kavram: RFSoC'ta durum — AXI-Stream

RFSoC'ta ADC ile PL aynı silikonda olduğu için seri hat, 8b/10b, CDR ve
link katmanları yoktur. RF-ADC tile'ı örnekleri **AXI-Stream** olarak verir:
`tdata` (P × 16 bit), `tvalid`, isteğe bağlı `tready`; saat, tile'ın
çıkış saatidir ve fs / P'ye eşittir. Reel modda tdata sekiz ardışık reel
örnek taşır; mixer (I/Q) modunda I ve Q ayrı akışlar ya da aynı sözcükte
dönüşümlü olarak gelir — hangisi olduğunu üreticinin kılavuzu söyler ve
**yanlış yorum, spektrumu fs/4 kaydırır ya da aynalar**. Deterministik
gecikme derdi ortadan kalkmaz: tile'ların FIFO'ları ve bölücüleri
hizalanmazsa kanallar arası gecikme açılıştan açılışa değişir; çözüm yine
SYSREF tabanlı çok tile senkron ({{bolum:10}}).

## Kavram: veri formatı

Örnek sözcüğü dört soruyu cevaplamalı:

1. **İşaret gösterimi.** İkinin tümleyeni (2's complement) mi, offset
   binary mi? Offset binary'de sıfır giriş 0x2000 (14 bit) kodunu verir;
   ikinin tümleyenine geçmek için MSB'yi ters çevirirsin. Çoğu JESD204 ADC
   ikinin tümleyenini varsayılan yapar; register'da seçilebilir.
2. **Hizalama.** 14 bitlik örnek 16 bitlik sözcüğün neresinde? **LSB
   hizalı + işaret uzatma** (`s s d13 … d0`) ya da **MSB hizalı**
   (`d13 … d0 0 0`). İkincisinde sayı 4 kat büyük görünür; dBFS hesabı
   ({{bolum:9}}) 12 dB kayar. Alt iki bit bazen kontrol bitidir (overrange,
   SYSREF yakalandı) — o zaman ne sıfır ne işaret.
3. **Reel mi I/Q mı.** Bypass modunda reel, çip içi DDC'de kompleks. Kompleks
   akışta I ve Q'nun sırası ve hangisinin "önde" olduğu, {{bolum:8}}'deki
   evrilme sorusunun bir parçasıdır.
4. **Örnek sırası (SSR).** 128 bitlik sözcükte hangi 16 bit en eski örnek?
   Yaygın sözleşme: bit [15:0] en eski, [127:112] en yeni. Ters kurulmuş
   bir sıra spektrumu aynalamaz ama zaman içinde örnekleri 8'li bloklar
   halinde ters çevirir: spektrum fs/2 etrafında bozulur, darbe kenarları
   tırtıklı olur.

Bunların dördü de birer register ya da IP parametresidir ve **belgeden
okunur, tahmin edilmez**. Doğrulama yöntemi tek: bilinen bir CW ton ver,
FFT'de tek bir temiz çizgi ve doğru genlik gör ({{bolum:29}}).

## Kavram: saat mimarisi

Almaç kartında dört saat vardır ve yalnızca ikisi birbirine akrabadır.

- **Örnekleme saati** ({{s:adc.fs_msps}} MHz): ADC'nin örnekle-tut devresine
  gider. Jitter'ı SNR'ı belirler ({{bolum:9}}); fs'in doğruluğu (ppm) NCO'nun
  ve her frekans ölçümünün doğruluğudur ({{bolum:14}}).
- **SYSREF**: örnekleme saatiyle aynı bölücü zincirinden, ADC'ye ve FPGA'ya
  çift olarak dağıtılır. Frekansı LMFC periyodunun tam böleni olmalıdır.
- **FPGA saatleri**: GT referans saati (SerDes PLL için), link/fabric saati
  (JESD çıkışından türetilir ya da saat çipinden gelir; SSR düzeninde
  fs / P), isteğe bağlı MMCM türevleri.
- **PS saati**: işlemcinin kendi kristali; örnekleme saatiyle ilişkisi yoktur
  ve olmamalıdır — zaman damgası için PS saati değil, örnek sayacı
  kullanılır ({{bolum:24}}).

Örnekleme saatini üreten zincir kardeş kılavuzda ayrıntılıdır: sistem
referansı → dar bantlı PLL1 (VCXO'ya kilitler, referansın kirini süzer) →
geniş bantlı PLL2 (GHz'e çarpar) → bölücüler
({{rf:zincir-referans-pll-dagitim|RF Örnekleme: referans → PLL → dağıtım}},
{{rf:dual-loop-mimari-jitter-cleaning|dual-loop jitter cleaning}}). Almaç
tasarımcısı için sonuç bir bütçedir: σ_saat² + σ_aperture² ≤ σ_hedef².
Senaryoda 100 fs toplam: ADC 55 fs alırsa saate 84 fs kalır.

{{svg:g-111-saat-agaci.svg|Almaç kartı saat ağacı. Sistem referansı (10/100 MHz OCXO ya da şasi) → çift döngülü jitter temizleyici (PLL1 dar bant + VCXO, PLL2 geniş bant + VCO) → bölücüler → ADC örnekleme saati 2400 MHz ve ADC SYSREF; FPGA GT referans saati, FPGA SYSREF ve isteğe bağlı fabric saati aynı zincirden. PS saati ayrı kristal. DCLK/SYSREF çiftleri aynı bölücüden çıkar; örnekleme saati asla FPGA'dan üretilmez.}}

## Kavram: SSR — tek hızlı akış, sekiz paralel şerit

fs = 2400 MHz, fabric 300 MHz: her fabric saatinde **P = 8** örnek gelir.
Bu, FPGA'daki her DSP bloğunun sekiz örneği aynı anda işlemesi demektir:
NCO sekiz faz üretir ({{bolum:14}}), FIR sekiz çıkış hesaplar
({{bolum:16}}), darbe FSM'i sekiz örneklik bir pencerede kenar arar
({{bolum:24}}). Kaynak sekiz kat artar, gecikme fabric saati cinsinden
sayılır ama örnek cinsinden aynı kalır. Verinin gelişinde iki kural: (1)
sözcük içindeki sıra sözleşmesi (yukarıda), (2) **saat geçişi (CDC)**: JESD
IP'sinin link saati ile senin DSP saatin aynı değilse arada asenkron FIFO
gerekir; aynı frekansta ama farklı fazda iseler bile. CDC'yi "aynı hızda,
sorun olmaz" diye atlayan tasarımlar sıcaklıkla bir örnek kaçırır ve bunu
kimse fark etmez — spektrumda küçük bir taban yükselmesi, PDW'lerde ara
sıra 3.3 ns'lik TOA sıçraması.

{{svg:g-112-ssr-paralel.svg|SSR düzeni. Üstte ADC'nin 2400 MSPS tek örnek akışı (örnek başına 417 ps). Altta 300 MHz fabric saatinin her vuruşunda 8 örneklik 128 bitlik sözcük: saat n'de lane k örneği x[8n + k] taşır; bit [15:0] en eski örnek. Veri hızı değişmez (38.4 Gbps), yalnızca genişlik × hız takası yapılır. 14 bitlik örnek 16 bitlik sözcüğe işaret uzatma ya da MSB hizalama ile yerleşir.}}

:::pasaport durak="FPGA girişi" alan=sayisal
Alan: sayısal (PL, fabric)
Frekans: {{s:adc.alias_mhz}} MHz merkez (450–750 MHz), evrik
Tip: reel
fs: {{s:adc.fs_msps}} MSPS (örnek hızı değişmedi)
!Düzen: SSR-8 × 300 MHz fabric saati, 128 bit sözcük, bit [15:0] en eski örnek
!Bit: {{s:adc.bit}} → 16 bit sözcük (ikinin tümleyeni, işaret uzatılmış)
!Veri hızı: {{s:adc.veri_hizi_gbps_16bit_paket}} Gbps (204B örneği: 8 lane × 6.0 Gbps; RFSoC: AXI-Stream)
!Gecikme: deterministik (subclass 1 / çok tile senkron) — TOA referansı burada başlar
SNR: ≈ 23 dB (300 MHz bantta), ADC çıkışıyla aynı
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
RF/donanım tasarımcısı için arayüz üç kabloyla özetlenir: örnekleme saati
(en temiz hat, en kısa yol, ADC'ye), SYSREF (aynı çipten, saatle uzunluk
eşlemeli, setup/hold penceresi doğrulanmış) ve GT lane'leri (empedans
kontrollü, uzunluk eşlemeli, 204C'de 10 Gbps üstü için kart malzemesi
seçilmiş). Saat çipinin çıkış çiftleri (DCLK/SYSREF) tasarımın en değerli
pinleridir; SYSREF'i başka bir kaynaktan "yavaş sinyal nasılsa" diye
vermek, sıcaklıkla kayan bir TOA üretir. RFSoC'ta lane yoktur ama ADC_CLK ve
SYSREF girişleri aynı özeni ister.
::fpga::
FPGA tasarımcısının işi: JESD204 RX IP'sini (ya da RFSoC RF Data Converter
IP'sini) doğru parametrelerle kurmak, SYSREF'i fabric'te güvenli yakalamak,
RBD'yi gecikme penceresinin ortasına koymak, çıkıştaki sözcüğü **açıkça
belgelenmiş** bir sıra ve hizayla DSP saatine geçirmek (asenkron FIFO ya da
aynı saatte doğrulanmış faz), overrange/kontrol bitlerini ayıklayıp örnekle
birlikte taşımak. İlk doğrulama: ILA'da tek bir CW ton için 8 ardışık
örneğin bilinen bir sinüsü izlediğini (sıra), genliğin beklenen kodda
olduğunu (hiza) ve link yeniden kurulduğunda bir sayaçla ölçülen
gecikmenin aynı kaldığını (determinizm) gör ({{bolum:13}}, {{bolum:29}}).
Referans gerçekleme: 128 bit AXI-Stream, 300 MHz, 8 × 16 bit işaret uzatılmış;
DSP zinciri bu formatı "sözleşme" olarak alır.
::yazilim::
Yazılımcının arayüzle üç teması: (1) **link durumu**: SYNC~ / CGS / ILAS /
data durum bitleri, hata sayaçları (8b/10b disparity, not-in-table, 204C
CRC/FEC), SYSREF yakalama sayacı — bunlar sağlık göstergesidir ve
{{bolum:30}}'daki durum register'larına girer; (2) **başlatma sırası**:
saat kilidi → ADC kalibrasyon → SYSREF ver → link kur → gecikme doğrula →
veri aç; (3) **format bilgisi**: sürücünün dBFS hesabı hizaya, TOA hesabı
gecikme sabitine bağlıdır; ikisi de yapılandırma tablosunda durur ve ADC
modu değişince (decimation, DDC açık/kapalı) güncellenir. "Link up" tek
başına hiçbir şeyin doğru olduğunu söylemez.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>

/* 16-bit sözcükten 14-bit ikinin tümleyeni örnek: hizaya göre iki farklı yol.
 * Yanlış seçim = 12 dB (4 kat) genlik hatası, dBFS ve PA yanlış. */
static int16_t ornek_lsb_hizali(uint16_t w)      /* [s s d13..d0]: işaret uzatılmış */
{
    return (int16_t)w;                           /* zaten 16-bit imzalı */
}
static int16_t ornek_msb_hizali(uint16_t w)      /* [d13..d0 c1 c0]: alt 2 bit kontrol */
{
    return (int16_t)w >> 2;                      /* aritmetik kaydırma: işaret korunur */
}
static int16_t offset_binary_to_2c(uint16_t w, int bit)
{
    return (int16_t)(w ^ (1u << (bit - 1))) ;    /* MSB'yi çevir (LSB hizalı, bit=14 → 0x2000) */
}

/* Kurgusal link durum register'ı (öğretici) */
#define JESD_STAT        0x0300
#define  JESD_SYNC_OK    (1u << 0)
#define  JESD_CGS_DONE   (1u << 1)
#define  JESD_ILAS_DONE  (1u << 2)
#define  JESD_DATA       (1u << 3)
#define  JESD_SYSREF_CNT_SHIFT 8    /* [15:8] yakalanan SYSREF sayısı */
#define JESD_ERR_CNT     0x0304     /* 8b10b / CRC hata sayacı, okununca sıfırlanır */

static int link_saglikli(uint32_t (*rd)(uint32_t))
{
    uint32_t st = rd(JESD_STAT);
    if ((st & 0xF) != 0xF) return 0;              /* dört aşama da tamam olmalı */
    if (((st >> JESD_SYSREF_CNT_SHIFT) & 0xFF) == 0) return 0;  /* SYSREF hiç gelmedi → gecikme belirsiz */
    return rd(JESD_ERR_CNT) == 0;                 /* sessiz link */
}
```

Üç tuzak: `>> 2` işaretli tipte aritmetik olmalı (`uint16_t` üzerinde
yaparsan işaret kaybolur); SYSREF sayacı sıfırsa link "up" olsa da TOA
güvenilmez; hata sayacı okununca sıfırlanıyorsa sağlık denetimi ile günlük
kaydı aynı okumayı paylaşmalı.

:::tuzak "Link up, veri geliyor — arayüz bitti"
Belirti: spektrumda ton var ama 12 dB düşük, ya da fs/4 kaymış, ya da
aynalı. Link katmanı yalnızca oktetlerin doğru geldiğini garanti eder;
sözcük hizası (MSB/LSB), işaret gösterimi, I/Q sırası ve SSR örnek sırası
transport ve senin yorumun arasındaki sözleşmedir. Teşhis: bilinen −6 dBFS
CW ton → FFT'de tek çizgi, tam −6 dBFS; 1 MHz yukarı al → çizgi doğru
yönde 1 MHz kaysın; ILA'da 8 örneklik sözcüğün içinde sinüsün *sürekli*
ilerlediğini gör. Üçü de geçmeden DSP'ye başlama.
:::

:::tuzak SYSREF'i "yavaş bir sinyal" sanmak
Belirti: her açılışta kanallar arası gecikme bir örnek (417 ps) oynar; TOA
farkları yön bulmada 30°'lik faz hatasına dönüşür. SYSREF, örnekleme
saatinin kenarında örneklenen bir giriştir; setup/hold penceresini ihlal
ederse cihaz onu bu kenarda mı sonraki kenarda mı gördüğüne kararsız
kalır. SYSREF'in örnekleme saatiyle aynı çipin aynı bölücüsünden gelmesi,
uzunluk eşlemeli çekilmesi ve faz kaydırma register'ıyla pencerenin
ortasına konması gerekir. FPGA GPIO'sundan üretilen SYSREF bir laboratuvar
kısayoludur, ürün değil.
:::

:::tuzak "Aynı frekans, CDC gerekmez"
Belirti: haftalarca temiz çalışan kart, kabin ısınınca ara sıra bir örnek
kaçırır; spektrum tabanı 1–2 dB yükselir, darbe uzunlukları nadiren 3.3 ns
kısa çıkar. JESD IP'sinin link saati ile DSP saati aynı frekansta olsa bile
farklı PLL'lerden geliyorsa fazları kayar; register-register geçiş bir gün
setup ihlal eder. Aradaki asenkron FIFO (birkaç yüz LUT) bu hatanın
sigortasıdır; ya da iki saat aynı MMCM'den, faz ilişkisi zamanlama
analizine dahil edilerek türetilir.
:::

:::ozet
- ADC → FPGA arayüzü ayrı çipte JESD204B/C (lane, link, L/M/F/S/N′/K parametreleri, 8b/10b vs 64b/66b), RFSoC'ta AXI-Stream; derin anlatım RF Örnekleme kılavuzunda.
- Subclass 1 + SYSREF deterministik gecikme sağlar: TOA'nın mutlak doğruluğu ve çok kanallı senkron buna dayanır. SYSREF saat değil, saatle kaynak-senkron hizalama emridir.
- Veri hızı: {{s:adc.fs_msps}} MSPS × {{s:adc.bit}} bit = {{s:adc.veri_hizi_gbps_14bit}} Gbps; 16-bit paketle {{s:adc.veri_hizi_gbps_16bit_paket}} Gbps → 204B 8 lane × 6 Gbps ya da 204C 4 lane × 9.9 Gbps.
- Veri formatı dört soru: işaret gösterimi (2's complement / offset binary), hizalama (LSB + işaret uzatma / MSB, 4 kat fark), reel / I/Q, SSR örnek sırası. Belgeden okunur, CW tonla doğrulanır.
- Saat mimarisi: örnekleme saati (jitter → SNR, ppm → frekans doğruluğu), SYSREF (aynı bölücüden), FPGA GT/fabric saatleri, ilişkisiz PS saati. Jitter bütçesi karesel toplanır.
- SSR: fs / f_fabric = 8 örnek/saat, 128 bit sözcük; her DSP bloğu 8 örneği paralel işler. Farklı saat alanları arasında CDC (asenkron FIFO) zorunludur.
- "Link up" yeterli değil: sıra, hiza, gecikme ve hata sayaçları doğrulanmadan DSP'ye başlanmaz.
:::

:::kendini-sina
S: 4 kanallı, 3 GSPS, 12 bit (N′ = 16) bir ADC'yi JESD204C ile 8 lane üzerinden bağlıyorsun. Lane hızı nedir? Aynı işi 204B ile kaç lane ister (lane başına ≤ 12.5 Gbps)?
C: R_ham = 3e9 × 16 × 4 = 192 Gbps; 204C: 192 × 66/64 / 8 = 24.75 Gbps/lane. 204B: 192 × 1.25 = 240 Gbps toplam; 12.5 Gbps/lane ile en az 20 lane — pratik değil; 204C'nin varlık nedeni.
S: Fabric saati 250 MHz olsaydı 2400 MSPS için SSR genişliği ne olurdu, ve neden sorun?
C: P = 2400/250 = 9.6 — tam sayı değil. JESD IP ya 8 örneklik sözcük verip 300 MHz link saati üretir (sen 250'ye asenkron FIFO ile geçer, ortalama 9.6 örnek/saat işlemek zorunda kalırsın: karmaşık), ya da fabric saati fs'in tam böleni seçilir (300, 240, 200 MHz). Kural: f_fabric = fs / P, P tam sayı ve tercihen 2'nin kuvveti.
S: MSB hizalı 16-bit sözcüğü LSB hizalı sanarak dBFS hesaplarsan tam ölçek sinüs kaç dBFS görünür?
C: Kod 4 kat büyük okunur: 20·log(4) = +12 dBFS. Aynı zamanda kontrol bitleri (alt 2 bit) "gürültü" olarak sayıya karışır. Belirti: tam ölçeğin üstünde görünen seviyeler ve açıklanamayan bir taban.
S: İki ADC'li bir yön bulma kartında SYSREF yalnızca birine bağlıysa ne olur?
C: İkinci ADC'nin LMFC'si hizalanmaz; linki kalkar ama gecikmesi her açılışta multiframe içinde rastgele bir yerde oturur. Kanallar arası gecikme, dolayısıyla faz farkı, açılıştan açılışa değişir; kalibrasyon tutmaz. Subclass 1 çok çipli senkron, her cihaza aynı SYSREF'i ister.
:::

:::kopru
Veri artık FPGA'nın içinde: her saatte sekiz adet 16 bitlik ikinin
tümleyeni sayı. Bu sayılarla çarpma, toplama ve filtreleme yapmadan önce
onların *ne olduğunu* — hangi ölçekte, kaç kesir biti, taşınca ne olacağı —
kararlaştırmak gerekir. Bölüm 12 sabit noktalı aritmetiği, Q formatını ve
"wrap felaketini" kurar; Kısım V'teki her blok o kurallarla yazılacak.
:::
