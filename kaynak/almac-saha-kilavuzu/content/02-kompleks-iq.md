# Bölüm 2 — Kompleks Sinyal ve I/Q
::meta onkosul=1 acar=14,15,20,22,25 blok= rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "Spektrumda sinyal +5 MHz'de olmalıydı, −5 MHz'de görünüyor;
donanım mı bozuk?" Ya da: "DMA'dan gelen 32 bitlik sözcüğün hangi yarısı I,
hangisi Q? Yanlış okursam ne olur?" İkisinin de cevabı aynı yerde: I ve Q'nun
bir kompleks sayının iki bileşeni olduğu, kompleks sinyalin yönü olan bir
frekansı temsil ettiği ve bu yönün I ile Q'nun sırasına bağlı olduğu. Sayısal
almaç zincirinin ADC'den sonraki her bloğu — NCO, mixer, filtre, zarf, FFT,
frekans ölçümü — kompleks örnekler üzerinde çalışır. Bu bölüm, "I/Q" deyince
gözünün önüne dönen bir vektör gelmesi için var.
:::

## Sezgi: bir sinüs, dönen bir vektörün gölgesidir

{{bolum:1}}'de sinüsü $A·cos(2πft + φ)$ diye yazdık. Şimdi aynı şeye başka
bir gözle bak: bir düzlemde, uzunluğu A olan bir ok, saniyede f tur hızında
dönüyor. Okun *yatay eksene düşen gölgesi* tam olarak $A·cos(2πft + φ)$'dir.
Ama okun bir de düşey gölgesi var: $A·sin(2πft + φ)$. Reel sinüs, dönen okun
yalnızca yarısını görür; öbür yarısı — düşey gölge — kaybolur. Kayıpla
birlikte iki bilgi gider: okun *o anki açısı* (faz) ve *hangi yöne döndüğü*.

Kompleks sinyal, iki gölgeyi birden saklamaktan ibarettir. Yatay gölgeye
**I** (in-phase, eş fazlı), düşey gölgeye **Q** (quadrature, dik fazlı)
denir. İkisi bir arada, okun kendisidir: $x = I + jQ$. Tek bir örnekten
genliği ($√(I²+Q²)$) ve fazı (atan2(Q, I)) okuyabilirsin; iki ardışık örnekten
de dönüş yönünü ve hızını, yani **işaretli frekansı**. Bu okun adı
**fazördür** (phasor).

{{svg:g-20-fazor-iq.svg|Dönen fazör ve I/Q izdüşümleri. Solda birim çember üzerinde saat yönünün tersine dönen vektör; yatay izdüşüm I = cos θ, düşey izdüşüm Q = sin θ; ilk sekiz örnek 30° aralıklarla noktalanmış. Sağda aynı örnekler zamanda: Q, I'yı çeyrek periyot geriden izler. Altta reel kosinüsün iki ters dönen fazörün toplamı olduğu gösterilir; Q bileşenleri birbirini götürür, spektrumda +f ve −f birlikte görünür.}}

:::analoji Saat kolu
Saat ibresinin yalnızca duvardaki gölgesine bakarsan ibrenin ne zaman saat
üçü ne zaman dokuzu gösterdiğini ayırt edemezsin: iki durumda da gölge aynı
uzunluktadır. İbrenin ileri mi geri mi döndüğünü de anlayamazsın. Yan
duvardaki ikinci gölge her iki belirsizliği kaldırır. I/Q'nun ikinci kanalı
o yan duvardır; onsuz frekansın işareti yoktur.
:::

## Kavram: Euler, negatif frekans ve reel sinyalin simetrisi

Dönen oku matematiksel olarak yazmanın kompakt yolu Euler formülüdür:

:::formul id=euler baslik="Euler formülü ve kompleks üstel"
f: e^{jθ} = cos θ + j · sin θ      x(t) = A · e^{j(2πft + φ)} = I(t) + j · Q(t)
f: cos θ = frac{e^{jθ} + e^{−jθ}}{2}
s: θ | anlık açı (faz) | rad
s: j | sanal birim, j² = −1 (elektrikte i akım olduğundan j) | —
s: f | frekans; işareti dönüş yönü: + saat yönünün tersi, − saat yönü | Hz
o: DDC çıkışında ({{bolum:15}}) darbe, {{s:ddc.cikis_fs_msps}} MSPS'te I/Q çifti olarak gelir: 20 MHz'lik bir ton, örnek başına 360°·20/300 = **24°** döner; −20 MHz'lik ton aynı hızla ters yönde.
o: cos formülü: reel sinüs = biri +f'te, biri −f'te, her biri yarım genlikte iki fazörün toplamı → reel spektrum **iki çizgili ve simetrik**.
:::

İkinci satır bu bölümün kilit cümlesidir. Reel bir kosinüs, biri ileri biri
geri dönen iki fazörün toplamıdır; düşey gölgeleri her an birbirini götürür,
yatay gölgeleri toplanır. Bunun spektrumdaki sonucu: reel bir sinyalin
spektrumu **sıfır etrafında simetriktir** — +f'te ne varsa −f'te de aynası
vardır. Negatif frekans, gizemli bir şey değil, ters yönde dönen fazörün
adıdır. Reel sinyalde negatif yarı hiç yeni bilgi taşımaz; kompleks sinyalde
ise pozitif ve negatif yarılar bağımsızdır, spektrum **tek taraflı**
olabilir.

{{svg:g-21-reel-kompleks-spektrum.svg|Reel ve kompleks sinyalin spektrumu (hesaplanmış, 300 MSPS, 0.4 µs darbe, taşıyıcı 20 MHz). Üstte reel darbeli ton: zamanda tek iz, frekansta +20 ve −20 MHz'de simetrik iki kopya, her biri kompleks tepenin 6 dB altında. Altta kompleks darbeli ton: zamanda I ve Q izleri, frekansta yalnızca +20 MHz. Negatif taraf boş; işaret ve yön bilgisi korunur.}}

Bunun almaç için iki pratik sonucu var. Birincisi, bant genişliği: reel bir
örnek dizisi fs/2'ye kadar frekans taşır; kompleks bir dizi ise −fs/2'den
+fs/2'ye, yani **fs kadar** bant taşır — aynı örnek hızında iki kat bant, ya
da aynı bant için yarı örnek hızı. {{bolum:15}}'teki decimation kazancının
kökeni budur. İkincisi, ADC'nin çıkışı reeldir ve simetriktir; o simetrik
spektrumdan istediğimiz yarıyı seçip diğerini atmak, sayısal almacın ilk işi
olacaktır ({{bolum:15}}).

## Kavram: I ve Q'dan genlik, faz ve anlık frekans

I/Q örneği elimizdeyken fazörün üç özelliği doğrudan hesaplanır:

:::formul id=iq-genlik-faz baslik="Genlik, faz ve anlık frekans"
f: |x| = sqrt{I^2 + Q^2}      φ = atan2(Q, I)      f_{anlık} = frac{1}{2π} · frac{dφ}{dt} ≈ frac{Δφ}{2π} · f_s
s: |x| | anlık genlik (zarf) | lineer, tam ölçek = 1
s: φ | anlık faz, atan2 dört bölgeyi ayırt eder (−π … +π) | rad
s: Δφ | ardışık iki örnek arasındaki faz farkı (±180° wrap'i — sarması — düzeltilmiş) | rad
s: f_s | örnekleme hızı (kompleks) | Hz
o: Referans darbe {{s:sinyal.pw_us}} µs = {{s:ddc.darbe_ornek_sayisi}} örnek boyunca |x| sabittir (zarf, {{bolum:22}}); faz her örnekte Δφ kadar ilerler. Δφ = 24° → f = 24/360 · 300 MHz = **20 MHz**.
o: Δφ = 180° sınırdır: fs/2 = ±{{s:ddc.cikis_bant_mhz}} MHz. Daha hızlı dönen fazörün yönü ayırt edilemez; Δφ wrap eder, yani ±180°'de sarar (aliasing'in kompleks hali, {{bolum:8}}).
:::

Bu üç formül, kılavuzun ikinci yarısının iskeletidir: zarf ($I²+Q²$)
tespitin girişidir ({{bolum:22}}); faz farkı iki anten arasında yön verir
({{bolum:25}}); ardışık faz farkı ise FFT'siz, tek darbe içinde **anlık
frekans** ölçmenin yoludur ve LFM bir chirp'in eğimini bile verir
({{bolum:20}}, {{bolum:25}}). `atan2`'nin iki argümanlı olması önemli:
tek argümanlı `atan(Q/I)` yalnızca 180°'lik aralığı ayırt eder, fazörün
sol yarıdaki konumlarını sağ yarıya katlar.

## Kavram: I/Q nereden gelir — analitik sinyal ve Hilbert

Antenden gelen sinyal reeldir; I/Q'yu almaç üretir. İki yol var. **Analog
yol:** sinyali, aralarında 90° faz farkı olan iki LO ile iki ayrı mixer'da
çarp, iki ayrı alçak geçiren filtreden geçir, iki ADC ile örnekle. Bu
"kuadratür demodülatör"dür ve zero-IF mimarisinin kalbidir ({{bolum:7}}).
**Sayısal yol:** reel sinyali tek ADC ile örnekle, FPGA içinde kompleks bir
NCO ile çarp ({{bolum:14}}, {{bolum:15}}). Referans senaryo ikinci yolu
izler; I ve Q, ADC'den değil DDC'den çıkar.

Matematiksel olarak her ikisi de aynı şeyi yapar: reel sinyalin negatif
frekans yarısını atıp pozitif yarısını tutar. Negatif yarısı atılmış sinyale
**analitik sinyal** denir; onu üreten ideal işlem **Hilbert dönüşümüdür**:
her frekans bileşenini 90° kaydıran bir filtre. Sezgisi şu: cos'un 90°
kaydırılmışı sin'dir; reel sinyalin kendisini I, Hilbert'inden geçmiş halini
Q yaparsan $I + jQ = cos + j·sin = e^{jθ}$ elde edersin — tek yönde dönen
fazör. Pratikte ideal Hilbert filtresi sonsuz uzundur; gerçek almaçlar ya
kuadratür mixer ya da NCO çarpımı + filtre ile aynı sonuca yaklaşır. Bu
kılavuzda Hilbert bir daha nadiren geçecek; ama "I/Q = reel sinyalin negatif
frekansı atılmış hali" cümlesi her yerde geçerli.

## Kavram: I/Q dengesizliği ve image

İki gölgenin gerçekten 90° ayrık ve eşit ölçekli olması gerekir. Analog
kuadratür demodülatörde iki mixer'ın kazancı birebir aynı olmaz (**kazanç
hatası**, g) ve iki LO tam 90° ayrık olmaz (**faz hatası**, φ_e). Sayısal
NCO'da bu hatalar yoktur (sin ve cos aynı tablodan okunur); ama zero-IF ya
da çift ADC'li tasarımlarda her zaman vardır. Sonuç: fazörün yörüngesi çember
yerine elips olur ve tek yönde dönmesi gereken sinyalin bir kısmı ters yönde
döner. Spektrumda bu, sinyalin −f'te beliren zayıf kopyasıdır: **image**.

:::formul id=iq-image baslik="I/Q dengesizliğinden image seviyesi"
f: frac{P_{image}}{P_{sinyal}} = frac{1 − 2g·cos φ_e + g^2}{1 + 2g·cos φ_e + g^2}      IRR = 10 · log_{10} frac{P_{sinyal}}{P_{image}}
s: g | Q/I kazanç oranı (lineer; 1 dB hata → 1.122) | —
s: φ_e | Q kanalının 90°'den sapması | rad (metinde °)
s: IRR | image bastırma oranı (image rejection ratio) | dB
o: g = 1 dB, φ_e = 10° → image **−19.6 dBc** (g-22'de hesaplanan değer). Böyle bir almaçta −20 dBc'lik "sahte emiter" her güçlü darbenin aynasında belirir.
o: g = 0.1 dB, φ_e = 1° → −39.6 dBc. Analog I/Q'da kalibrasyonsuz 25–35 dB, sayısal kalibrasyonla 50–60 dB tipiktir (yaklaşık değerler).
:::

{{svg:g-22-iq-dengesizlik-image.svg|I/Q dengesizliği ve image (hesaplanmış). Solda ideal çember ile 1 dB kazanç, 10° faz hatalı elips. Ortada +20 MHz tonunun spektrumunda −20 MHz'de beliren image, 19.6 dB aşağıda. Sağda I ve Q yer değiştirince spektrumun tamamının aynalanması: ton −20 MHz'e taşınır, image +20 MHz'e.}}

Şeklin sağ paneli ikinci ve daha kaba hatayı gösterir: I ile Q **yer
değiştirirse** fazör ters yönde döner ve *bütün spektrum aynalanır*; +5
MHz'deki sinyal −5 MHz'de görünür. Matematiği tek satırdır: $Q + jI = j·(I − jQ) = j·x^*$ —
kompleks eşlenik (conjugate) alma frekansın işaretini çevirir, $j$ çarpanı yalnızca 90° sabit faz
ekler. Aynı etkiyi Q'nun işaretini değiştirmek de yapar. Sahada bu, NCO
işaret bitinin ({{bolum:14}}) ya da veri yolunda I/Q sırasının yanlış
olmasıdır; belirtisi "her şey doğru ama frekanslar eksi" hissidir.

:::widget id=w02 ad="Fazör laboratuvarı"
- **Referans senaryo** (20 MHz, fs = 300 MSPS): çemberde örneklerin 24°'lik adımlarla saat yönünün tersine ilerlediğini, zaman çiziminde Q'nun I'yı çeyrek periyot (3.75 örnek) geriden izlediğini, spektrumda tek çizginin +20 MHz'de olduğunu gör. Frekansı −20 MHz yap: örnekler ters yöne dönsün, Q öne geçsin, çizgi −20 MHz'e taşınsın.
- Frekansı +140 MHz'e çek: örnek başına 168°; çember üzerinde noktalar neredeyse karşılıklı sıçrar, yön hâlâ okunur. +150 MHz'de 180° — yön belirsiz; bu fs/2 sınırıdır.
- **I/Q dengesizliği** preset'i (1 dB, 10°): yörünge elips, |x| örnekten örneğe dalgalanıyor; spektrumda −20 MHz'de image −19.6 dBc. Hataları 0.1 dB ve 1°'ye indir: image −39.6 dBc'ye düşsün. Yalnızca kazanç hatasını 1 dB bırak (faz 0): −24.8 dBc.
- **I/Q swap**'ı aç: image değil, tonun kendisi −20 MHz'e atlasın. Dengesizlik image'ı tona göre zayıf bir kopyadır; swap ise bütün ekseni çevirir — iki belirtiyi karıştırma.
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Analog dünyada I/Q, kuadratür demodülatörle üretilir: 0° ve 90° LO, iki
mixer, iki LPF, iki ADC. Her analog fark (mixer kazancı, filtre grup
gecikmesi, LO faz bölücüsünün doğruluğu, ADC'ler arası kazanç) doğrudan
image olur; sıcaklıkla ve frekansla kayar, bu yüzden fabrika kalibrasyonu
ve çoğu zaman çalışma sırasında adaptif I/Q düzeltme gerekir ({{bolum:7}}).
Reel-IF örnekleyip I/Q'yu FPGA'da üreten mimari ({{bolum:10}}) bu sorunu
tamamen ortadan kaldırır: sin ve cos aynı tablodan gelir, kazanç hatası
sıfırdır, faz hatası tablo çözünürlüğü kadardır. Referans senaryonun bu
mimariyi seçmesinin nedenlerinden biri budur.
::fpga::
Kompleks örnek, iki paralel işaretli sözcüktür: referans senaryoda
{{s:ddc.cikis_bit_i}} + {{s:ddc.cikis_bit_q}} bit, aynı saatte, aynı geçerli
(valid) işaretiyle. Kompleks çarpma dört reel çarpma ve iki toplamadır
(ya da üç çarpmalı Gauss hilesi): $(a + jb)(c + jd) = (ac − bd) + j(ad + bc)$;
NCO ile mixing ({{bolum:15}}) tam olarak budur ve iki-dört DSP slice yer.
Genlik için karekök yerine $I² + Q²$ (güç) kullanılır ya da
alpha-max-beta-min yaklaşımı ({{bolum:22}}); faz için atan2, iteratif
CORDIC ile ({{bolum:25}}). Bit genişliği kararlarında I ve Q her zaman
birlikte büyür; birinin taşması diğerini de bozar ({{bolum:12}}).
::yazilim::
Yazılımcı için I/Q bir bellek düzenidir: tipik olarak 32 bitlik sözcükte
iki 16 bitlik işaretli tam sayı. Hangi yarının I olduğu, bayt sırası
(little/big endian), işaretin ikinin tümleyeni (two's complement) olup olmadığı ve I/Q'nun
mu yoksa Q/I'nın mı geldiği register haritasında yazar; yazmıyorsa
bilinen bir tonla test edilir. DMA tamponunu `int16_t` çiftleri olarak
okuyup $I² + Q²$ ile zarf, `atan2f` ile faz hesaplamak PS tarafında
test ve teşhis için en sık yazılan on satırdır. "Spektrum aynalı" belirtisi
görüldüğünde ilk kontrol edilecek şey bu on satırdaki I/Q sırasıdır.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>
#include <math.h>

/* DDC çıkışı: 32 bitlik sözcükte I alt yarı, Q üst yarı (KURGUSAL düzen —
 * gerçek kartta register haritasına bak). İşaretli 16 bit, ikinin tümleyeni. */
typedef struct { int16_t i, q; } iq16_t;

static inline iq16_t iq_ac(uint32_t sozcuk)
{
    iq16_t s;
    s.i = (int16_t)(sozcuk & 0xFFFFu);        /* önce uint16'ya kırp, sonra işaretli yorumla */
    s.q = (int16_t)(sozcuk >> 16);
    return s;
}

/* Genlik ve faz: tam sayı güç taşmaz (2·32767² < 2^31), karekök float'ta. */
static inline uint32_t iq_guc(iq16_t s)  { return (uint32_t)((int32_t)s.i * s.i + (int32_t)s.q * s.q); }
static inline float    iq_genlik(iq16_t s) { return sqrtf((float)iq_guc(s)); }
static inline float    iq_faz_deg(iq16_t s) { return atan2f((float)s.q, (float)s.i) * 57.2957795f; }

/* Ardışık iki örnekten anlık frekans (Hz). Faz farkı çarpım/eşlenikle alınır:
 * x[n]·conj(x[n-1]) → açısı Δφ; sarma sorunu yok, ayrı ayrı atan2 gerekmez. */
static float iq_anlik_frekans(iq16_t a /* x[n-1] */, iq16_t b /* x[n] */, float fs_hz)
{
    float re = (float)b.i * a.i + (float)b.q * a.q;     /* Re{b·conj(a)} */
    float im = (float)b.q * a.i - (float)b.i * a.q;     /* Im{b·conj(a)} */
    return atan2f(im, re) / (2.0f * 3.14159265f) * fs_hz;
}
/* referans senaryo: 20 MHz ton, fs = 300e6 → ardışık Δφ = 24°, iq_anlik_frekans ≈ 20e6 */
```

İki incelik: `(int16_t)(sozcuk >> 16)` işaretli yorumu doğru yapar ama
`(int16_t)sozcuk >> 16` yapmaz (önce işaretli genişler, sonra kayar).
Anlık frekans için iki ayrı `atan2f` alıp çıkarmak yerine
$x[n]·x^*[n−1]$ çarpımının açısını almak, ±180° wrap (sarma) sorununu kendiliğinden
çözer; FPGA'daki frekans ölçüm bloğu da aynısını yapar ({{bolum:25}}).

:::tuzak "Q kanalını kapattım, test daha kolay olur"
Test sırasında Q'yu sıfırlayıp yalnızca I ile çalışmak masum görünür. Ama
Q = 0 demek sinyali reel yapmak demektir: fazör artık iki ters dönen
fazörün toplamıdır, spektrum simetrik olur ve her sinyalin −f'te *eşit
güçte* bir kopyası belirir. FFT'de "image" sanılan bu kopya, tespit
zincirinde çift sayım, frekans ölçümünde işaret belirsizliği yaratır.
Tek kanalla test edeceksen bunu bilerek yap ve yalnızca pozitif yarıya bak.
:::

:::tuzak "Spektrum aynalı, mixer'ı değiştirelim"
Sinyal beklenen frekansın eksi işaretlisinde görünüyorsa üç olası neden var
ve üçü de yazılımdan görülür: (1) I/Q sırası ters okunuyor (DMA tamponu),
(2) NCO işaret / spectral inversion biti yanlış ({{bolum:14}}), (3) IF
çift Nyquist bölgesinden katlanmış ve düzeltilmemiş ({{bolum:8}}). Teşhis
tek deneydir: bilinen bir tonun frekansını *artır*; spektrumda çizgi sola
gidiyorsa eksen aynalıdır. Düzeltme donanım değil, bir bit ya da bir swap'tır.
İkiden fazla aynalama katmanı üst üste gelebilir; her birini ayrı ayrı
doğrula, ikisi birden yanlışsa sonuç "doğru" görünür ve bir gün patlar.
:::

:::ozet
- Reel sinüs, dönen bir vektörün (fazörün) tek gölgesidir; I ve Q iki gölgedir ve fazörün kendisini verir: x = I + jQ = A·e^{jθ}.
- Euler: cos θ = (e^{jθ} + e^{−jθ})/2 → reel sinyalin spektrumu simetriktir; negatif frekans ters dönen fazördür; kompleks sinyal tek taraflı olabilir.
- Kompleks örnek dizisi fs kadar bant taşır (−fs/2 … +fs/2), reel dizi fs/2 kadar.
- |x| = √(I²+Q²), φ = atan2(Q, I), anlık frekans = Δφ/(2π)·fs; Δφ = 180° sınırı fs/2'dir.
- I/Q, reel sinyalin negatif frekansı atılmış halidir (analitik sinyal); analogda kuadratür demodülatör, sayısalda NCO çarpımı üretir.
- Kazanç/faz dengesizliği −f'te zayıf bir image üretir (1 dB, 10° → −19.6 dBc); I/Q swap ise bütün spektrumu aynalar.
- Yazılımda I/Q bir bellek düzenidir: sıra, işaret ve bayt düzenini doğrula; anlık frekansı x[n]·x*[n−1] açısıyla al.
:::

:::kendini-sina
S: fs = 300 MSPS'lik kompleks bir akışta ardışık örnekler arasındaki faz farkı sürekli −36° ölçülüyor. Sinyalin frekansı nedir?
C: f = Δφ/360° · fs = −36/360 · 300 MHz = −30 MHz. İşaret, fazörün saat yönünde döndüğünü söyler; reel bir sinyalde bu bilgi yoktu.
S: Reel bir 1.8 GHz IF sinyalini 2400 MSPS ile örnekleyen ADC'nin çıkışı neden "kompleks" değildir ve bundan ne kaybederiz?
C: Tek ADC tek reel dizi verir; spektrumu fs/2 = 1200 MHz etrafında simetriktir ve yalnızca 0–1200 MHz'lik tek taraflı bant taşır. İşaretli frekans bilgisi yoktur; onu kazanmak için sinyal FPGA'da kompleks NCO ile çarpılıp tek yarı seçilir (Bölüm 15).
S: Zero-IF bir almaçta kazanç hatası 0.5 dB, faz hatası 5°. Image kaç dBc? Bu, −60 dBm'lik güçlü bir emiterin aynasında ne yaratır?
C: g = 1.059; formülden image ≈ −25.6 dBc. −60 dBm'lik darbenin aynasında −85.6 dBm'lik sahte bir darbe belirir; 300 MHz bantta gürültü tabanı −83.2 dBm olduğundan bu image tabanın hemen altındadır, ama daha güçlü bir emiterde tespit eşiğini aşar ve "ikinci emiter" olarak PDW üretir.
S: DMA tamponunda I ve Q'nun yer değiştiğinden şüpheleniyorsun. Kodla nasıl doğrularsın?
C: Bilinen pozitif frekanslı bir ton ver; x[n]·x*[n−1] açısı pozitif çıkmalı. Negatif çıkıyorsa ya I/Q ters okunuyor ya da NCO işareti ters. Tonun frekansını artırıp ölçülen frekansın hangi yöne gittiğine bakarak hangisi olduğunu ayırt et: her iki hata da işareti çevirir ama yalnızca biri register'dan düzeltilir.
:::

:::kopru
Artık sinyalin dilini ve onun kompleks halini biliyorsun. Sıradaki soru:
bir radar darbesi bu dilde nasıl görünür? Bir mikrosaniyelik dikdörtgen bir
darbe zaman ekseninde basittir, ama frekans ekseninde 2 MHz'lik bir ana lob
ve sonsuza uzanan yan loblardır; darbe kısaldıkça bu lob genişler, içine
modülasyon konunca daha da genişler. Bölüm 3, darbeyi ölçü ölçü söker ve
almacın neden bant genişliğini darbeye göre seçmek zorunda olduğunu gösterir.
:::
