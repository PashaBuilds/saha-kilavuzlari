# Bölüm 6 — Frekans Dönüştürme: RF, IF, Baseband
::meta onkosul=2,3,5 acar=7,8,14,15,25 blok=mixer,if rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "PDW'deki RF alanı 9 400 MHz yerine 9 396 gösteriyor ve LFM
darbelerin eğimi ters çıkıyor — hangisi bozuk?" İkisi de bozuk olmayabilir:
ilki LO'nun 4 MHz kaymış olmasıdır, ikincisi LO'nun sinyalin *üstüne*
konmasıdır. Mixer, yazılımcının hiç görmediği ama her frekans ölçümünün
içinden geçtiği bloktur: FPGA'nın ölçtüğü her frekans aslında bir IF
frekansıdır ve RF'e dönüş, LO'nun nerede olduğuna ve hangi tarafta olduğuna
bağlıdır. Bu bölüm çarpma işleminin spektruma ne yaptığını, "image" denen
kaçınılmaz kopyayı ve referans senaryonun 9.4 → 1.8 GHz planının neden öyle
seçildiğini anlatır.
:::

## Sezgi: iki tekerlek ve vuru

{{bolum:2}}'de bir sinüsü dönen bir fazör olarak gördün. İki fazörü çarpmak,
{{bolum:2}}'deki üstel gösterimde açıları toplamaktır: $e^{ja}·e^{jb} =
e^{j(a+b)}$. Reel bir kosinüs ise iki zıt yönde dönen fazörün toplamıdır
($cos a = ½e^{ja} + ½e^{−ja}$); iki kosinüsü çarpınca dört kombinasyon çıkar
ve bunlar iki reel kosinüse toplanır: biri açıların **farkında**, biri
**toplamında**. Frekans dilinde: 9.4 GHz'i 7.6 GHz ile çarparsan 1.8 GHz ve
17.0 GHz elde edersin. Mixer bir çarpıcıdır; IF filtresi de bu iki üründen
birini seçen elek.

Zaman domaininde aynı şey "vuru"dur (beat): iki yakın frekansı çarptığında
hızlı bir salınımın üstünde yavaş bir zarf görürsün; yavaş olan fark
frekansıdır. Akort ederken iki telin birbirine yaklaşınca duyulan "vuvv"
budur.

:::analoji Saat dilimi dönüşümü
Frekans dönüştürme bir saat dilimi değiştirmektir: İstanbul'daki 14:00,
Londra'da 11:00'dır; olay aynı, etiket değişti. LO, dilimler arasındaki
farktır (3 saat = 7.6 GHz). Dönüşümde bir şey kaybolmaz ama iki tuzak vardır.
Birincisi: "11:00" dediğinde hangi dilimde olduğunu söylemezsen bilgi
eksiktir — IF'te ölçülen 1.8 GHz, LO bilinmeden RF'e çevrilemez. İkincisi:
"Londra'dan 3 saat farklı" olan iki şehir vardır, biri doğuda biri batıda —
IF'ten 1.8 GHz uzaklıkta da iki RF frekansı vardır, biri LO'nun altında biri
üstünde. İkincisine *image* denir.
:::

## Kavram: mixer = çarpım; RF, IF, baseband

:::formul id=mixer-carpim baslik="Çarpımın frekansa etkisi"
f: cos(2π f_{RF} t) · cos(2π f_{LO} t) = frac{1}{2} cos(2π (f_{RF} − f_{LO}) t) + frac{1}{2} cos(2π (f_{RF} + f_{LO}) t)
s: f_{RF} | giriş (radyo) frekansı | Hz
s: f_{LO} | yerel osilatör frekansı | Hz
s: f_{RF} − f_{LO} | fark ürünü — istenen IF (low-side'da) | Hz
s: f_{RF} + f_{LO} | toplam ürünü — filtreyle atılır | Hz
o: f_RF = {{s:sinyal.rf_ghz}} GHz, f_LO = {{s:on_uc.lo_ghz}} GHz → fark **{{s:on_uc.if_ghz}} GHz**, toplam 17.0 GHz. Her ürün genliğin yarısı (−6 dB); pasif mixer'ın {{s:on_uc.kaskad.3.kazanc_db}} dB dönüşüm kaybının kaynağı budur (artı diyot kayıpları).
:::

{{svg:g-60-mixer-carpim.svg|Mixer çarpımı adım adım (hesaplanmış). Üstte zaman domaini: 9.4 GHz'lik RF, 7.6 GHz'lik LO ve çarpımları — hızlı salınımın (17 GHz) üstünde 1.8 GHz'lik yavaş zarf (kesikli). Altta üç spektrum: ① girişler; ② çarpım ürünleri, fark 1.8 ve toplam 17.0 GHz'te, gerçek mixer'da LO ve RF sızıntısı da çıkışta görünür (kırmızı); ③ IF filtresi fark ürününü seçer.}}

Üç ad, üç bölge: **RF** (radio frequency) sinyalin havada olduğu frekans,
9.4 GHz. **IF** (intermediate frequency — ara frekans) mixer'dan sonra
taşındığı sabit frekans, 1.8 GHz. **Baseband** (taban bant) sinyalin
taşıyıcısı sıfıra indirilmiş hali: darbenin zarfı ve içindeki modülasyon,
±BW/2 aralığında. Referans zincirde baseband'e iniş analogda değil FPGA'da
olur: ADC IF'i örnekler, NCO ve kompleks mixer ({{bolum:14}}, {{bolum:15}})
600 MHz'i sıfıra taşır. Yani zincirde **iki mixer** var — biri analog
(9.4 → 1.8), biri sayısal (0.6 → 0) — ve ikisi de bu bölümün matematiğine
uyar; sayısal olanın farkı kompleks çarpım yapabilmesidir, o yüzden
"toplam" ürünü ve image'ı kendiliğinden yoktur.

Neden IF'e inilir? Üç neden. (1) **Filtreleme:** 9.4 GHz'de %3 bant
genişliği (300 MHz) dik kenarlı bir filtre yapmak zordur; 1.8 GHz'de aynı 300
MHz, %17'dir ve kolaydır. Dar kanal seçiciliği hep IF'te yapılır. (2)
**Kazanç:** 40 dB'lik kazancı tek bir frekansta toplamak osilasyon riskidir
(çıkış girişe sızar); kazancı RF ve IF arasında bölmek kararlılığı kolaylaştırır.
(3) **ADC erişimi:** 1.8 GHz'i 2.4 GSPS ile örneklemek bugün olağan; 9.4 GHz'i
doğrudan örneklemek özel ADC ister ({{bolum:10}}). Sabit bir IF'in ek ödülü:
LO'yu değiştirerek bandı tararken IF zincirinin hiçbir parçası değişmez.

## Kavram: image — kaçınılmaz ikinci giriş

Fark ürünü $f_{RF} − f_{LO}$ ise, LO'nun **öbür yanındaki** bir sinyal de
aynı farkı verir: $f_{LO} − f_{img} = f_{IF}$. Mixer bu iki girişi ayırt
edemez; ikisi de 1.8 GHz'e düşer, üst üste biner. Bu ikinci frekansa
**image** (görüntü/ayna) frekansı denir ve mixer'dan *önce* bastırılması
gerekir; sonrasında iş işten geçmiştir.

:::formul id=image baslik="Image frekansı"
f: f_{img} = 2 · f_{LO} − f_{RF} = f_{RF} ∓ 2 · f_{IF}
s: f_{img} | image frekansı | Hz
s: f_{LO} | LO frekansı | Hz
s: f_{IF} | ara frekans | Hz
s: ∓ | low-side'da −, high-side'da + | —
o: Low-side (referans): f_img = 2·7.6 − 9.4 = **{{s:on_uc.image_ghz}} GHz** — RF'in 3.6 GHz altında. Preselector 8–11 GHz ise image bandın 2.2 GHz dışındadır: iyi bir filtre onu 60 dB'nin üstünde bastırır (kurgusal, filtreye bağlı).
o: High-side seçenek: f_LO = 11.2 GHz → f_img = 13.0 GHz. Bu da bandın dışındadır; seçim başka ölçütlere kalır (aşağıda).
:::

{{svg:g-61-image-problemi.svg|Image problemi. ① Low-side LO 7.6 GHz: RF 9.4 (mavi) ve image 5.8 GHz (kırmızı) LO'nun iki yanında, ikisi de 1.8 GHz uzakta; preselector bandı (altın kesikli) image'ı dışarıda bırakır. ② IF ekseninde ikisi de 1.8 GHz'e düşer; asimetrik rampa şekli spektrumun yönünü gösterir — low-side'da düz. ③ High-side LO 11.2 GHz: image 13.0 GHz'e gider ve IF'e inen spektrum evrilir (rampa ters).}}

Image'ın uzaklığı $2·f_{IF}$'tir: **IF ne kadar yüksekse image o kadar
uzakta**, preselector o kadar rahat. Bu, çift dönüşümlü almaçlarda ilk IF'in
yüksek seçilmesinin nedenidir: ilk dönüşüm image'ı uzağa atar (yüksek IF₁,
kolay preselector), ikinci dönüşüm dar kanal filtresini kolay yapar (düşük
IF₂). Referans zincir tek dönüşümdür ve IF'i 1.8 GHz gibi yüksek tutar,
çünkü ADC bunu doğrudan örnekleyebilir; kanal seçiciliğini de sayısal
filtreye ({{bolum:16}}) bırakır. Sayısal almaçların analog zinciri
kısaltmasının somut hali budur.

Image reddi (image rejection) toplam olarak iki katkıdan oluşur:
preselector'ın image frekansındaki zayıflatması ve, varsa, **image-reject
mixer**'ın kendi reddi. Image-reject mixer iki mixer'ı 90° fazlı LO ile
sürer ve çıkışları öyle toplar ki istenen bant güçlenir, image sönümlenir;
{{bolum:2}}'deki I/Q dengesizliği burada da geçerlidir: 0.5 dB / 5°'lik
dengesizlik reddi ~25–30 dB ile sınırlar. Tek başına yetmez, preselector'la
birlikte çalışır.

## Kavram: high-side, low-side ve spektral evrilme

LO'yu sinyalin altına koymak **low-side injection**, üstüne koymak
**high-side injection**'dır. Fark yalnızca image'ın yeri değildir; IF'e inen
spektrumun **yönü** değişir. Low-side'da $f_{IF} = f_{RF} − f_{LO}$: RF
artınca IF artar, spektrum düz iner. High-side'da $f_{IF} = f_{LO} − f_{RF}$:
RF artınca IF **azalır**, spektrum ayna görüntüsü olur. Buna **spektral
evrilme** (spectral inversion) denir. Bir CW ton için önemsizdir (tek çizgi
yer değiştirir), ama yönü olan her şey için önemlidir: LFM darbenin
"yukarı chirp"i "aşağı chirp" olur, kompleks temsilde $e^{+jθ}$ ile
$e^{−jθ}$ yer değiştirir, yani I/Q'nun işareti döner.

:::formul id=evrilme baslik="Evrilme: IF'in RF'e göre türevi"
f: low-side: f_{IF} = f_{RF} − f_{LO}  →  frac{df_{IF}}{df_{RF}} = +1
f: high-side: f_{IF} = f_{LO} − f_{RF}  →  frac{df_{IF}}{df_{RF}} = −1
s: f_{IF}, f_{RF}, f_{LO} | ara, radyo ve LO frekansı | Hz
s: df_{IF}/df_{RF} | RF'teki bir kaymanın IF'te görünen yönü | —
o: Varyant B (LFM {{s:sinyal.varyant_b.chirp_bw_mhz}} MHz / {{s:sinyal.pw_us}} µs, yukarı): low-side'da IF'te de yukarı (+10 MHz/µs); high-side olsaydı **−10 MHz/µs** ölçülürdü. Aynı emiter, ters işaret.
o: Evrilme sayaç gibi çalışır: her high-side dönüşüm ve her çift Nyquist bölgesinden örnekleme ({{bolum:8}}) bir kez daha evirir. Referansta analog kat evirmez, ADC (2. bölge) evirir → toplam **bir** evrilme → NCO işareti ile düzeltilir ({{bolum:14}}).
:::

Hangisini seçmeli? Ölçütler: image'ın nereye düştüğü (bantta güçlü
vericilerin olduğu yere düşmesin), LO'nun üretilebilirliği (high-side LO
daha yüksek frekans, daha zor sentezleyici; low-side LO'nun harmonikleri
banda düşebilir), ve bütün bant taranırken LO aralığının kaç oktav
gerektirdiği. Referans senaryo low-side seçti: 7.6 GHz'lik LO 11.2'den
kolaydır ve image 5.8 GHz'te, X-bant preselector'ın çok dışındadır.

## Kavram: mixer spur'ları, LO sızıntısı ve frekans planı

Gerçek mixer yalnızca $f_{RF} ± f_{LO}$ üretmez. Diyotların doğrusal
olmaması ({{bolum:5}}) her iki girişin harmoniklerini de çarpar; çıkışta
**tüm** $|m·f_{RF} ± n·f_{LO}|$ kombinasyonları vardır ($m, n = 0, 1, 2, …$).
$m = n = 1$ istenen üründür; ötekiler **spur**'dur ve mertebe arttıkça
zayıflar (tipik olarak her mertebe onlarca dB, mixer'ın "spur tablosu"
datasheet'te verilir). $m = 0, n = 1$ **LO sızıntısıdır**: LO gücü (genellikle
+10 dBm ve üstü) izolasyon kadar zayıflayarak IF portuna ve — daha kötüsü —
RF portuna, oradan antene sızar. $m = 1, n = 0$ RF sızıntısıdır.

:::formul id=spur baslik="Mixer ürünleri ve half-IF spur"
f: f_{out} = | m · f_{in} − n · f_{LO} |      m, n = 0, 1, 2, …
f: f_{in}(m×n → IF) = frac{n · f_{LO} ± f_{IF}}{m}
s: m | giriş sinyalinin harmonik mertebesi | —
s: n | LO'nun harmonik mertebesi | —
s: f_{in} | IF'e düşen bir ürün üreten giriş frekansı | Hz
o: 2×2 ürünü: f_in = (2·7.6 + 1.8)/2 = **8.5 GHz** — RF ile LO'nun tam ortası, "half-IF spur". 8.5 GHz'deki bir emiter 2·8.5 − 2·7.6 = 1.8 GHz'e, senin IF'ine düşer ve preselector (8–11 GHz) onu **geçirir**. Tek koruma mixer'ın 2×2 bastırmasıdır (tipik 50–70 dBc, doğrulanmadı).
o: 2×3 ürünü 10.5 GHz'de, o da bant içinde; 1×2 ürünü 13.4 GHz'de, bant dışında. Bu tablo W-05'te canlı üretilir.
:::

{{svg:g-62-frekans-plani.svg|Referans senaryonun frekans planı. Üstte tek eksende her şey: preselector 8–11 GHz (altın), RF 9.4 (mavi), LO 7.6 (gri), image 5.8 ve half-IF 8.5 (kırmızı), IF bandı 1.8 ± 0.15 GHz, ilk dört Nyquist bölgesi (fs = 2.4 GSPS) ve IF'in 2. bölgeden 0.6 GHz'e evrik katlanması. Altta m, n ≤ 3 ürünlerinin IF'e düşürdüğü giriş frekansları: preselector içinde kalanlar kırmızı.}}

**Frekans planlama** bu tablonun üstünde oynanan bir oyundur: IF'i, LO'yu ve
preselector bandını öyle seç ki (a) image bandın dışında olsun, (b) düşük
mertebeli spur girişleri ($2×2$, $2×3$, $3×2$) ya bandın dışına ya da güçlü
verici olmayan yerlere düşsün, (c) LO ve harmonikleri banda düşmesin, (d) IF
ADC'nin uygun Nyquist bölgesine otursun ({{bolum:8}}). Bütün bunları aynı
anda sağlayan "temiz" bir IF her zaman yoktur; bu yüzden geniş bantlı
almaçlar birden çok IF/LO planı arasında bant bant geçiş yapar ve bu
geçişler yazılımın tuttuğu bir **tabloyla** yönetilir. Tablonun her satırında
LO frekansı, high/low-side bayrağı, preselector seçimi ve o plan için
"bilinen spur listesi" bulunur.

:::widget id=w05 ad="Mixer frekans planı ve image gezgini"
- **Referans senaryo** preset'inde LO = 7 600 MHz, IF = 1 800 MHz, image = 5 800 MHz ve "evrilme: hayır" satırlarını doğrula. Alt eksende 1×1 ürününün IF filtresi bandının (1 650–1 950 MHz) tam ortasında olduğunu, half-IF girişinin (8 500 MHz) preselector bandının **içinde** kırmızı işaretlendiğini gör.
- **High-side** preset'ine geç: LO 11 200 MHz'e, image 13 000 MHz'e sıçrasın; "evrilme: EVET" uyarısı yansın. IF aynı kalır — FPGA'nın gördüğü hiçbir şey değişmez, yalnızca RF'e dönüş formülü ve LFM işareti değişir.
- **Image içeride** preset'i: IF'i 200 MHz'e indir. Image 9 000 MHz'e gelir ve 3 000 MHz'lik preselector bandının içine düşer; uyarı satırı kırmızıya döner. IF'i yavaşça 1 800'e doğru artır ve image'ın banttan çıktığı IF'i bul (≈ 750 MHz'in üstünde: image = RF − 2·IF < 7 900 MHz).
- Spur mertebesini 3'ten 5'e çıkar: üst eksende preselector içine düşen spur girişi sayısı 3'ten 9'a çıksın, ama "IF filtresine düşen ürün" referans planda 0 kalsın — "temiz plan" tam olarak budur. Sonra IF'i 300 MHz, IF filtre bandını 1 200 MHz yap: 2×2 ürünü (2·RF − 2·LO = 600 MHz) filtreye girsin ve image (8 800 MHz) preselector'ın içine düşsün.
:::

## Kavram: tek ve çift dönüşüm; ilk IF neden yüksek

Tek dönüşüm (referans): bir mixer, bir IF, sonra ADC. Basit, az spur, az
blok; ama IF hem "image uzak olsun diye yüksek" hem "filtre kolay olsun diye
düşük" olamaz. Çözüm ADC ve sayısal filtre yeterince iyiyse tek dönüşümdür:
IF yüksek tutulur, seçicilik sayısala bırakılır.

Çift dönüşüm (klasik süperhet, {{bolum:7}}): ilk mixer yüksek bir IF₁'e
(örneğin bant 2–18 GHz için IF₁ ≈ 20 GHz'in üstü ya da bant ortasında
birkaç GHz), ikinci mixer düşük bir IF₂'ye (yüzlerce MHz ya da onlarca MHz)
indirir. İlk IF yüksek → image bandın çok dışında, tek bir sabit preselector
yeter; ikinci IF düşük → dar, dik kanal filtresi ucuz. Bedel: iki LO, iki
image (ikinci mixer'ın da image'ı vardır, IF₁ filtresi onu bastırmalı), iki
spur tablosu ve daha uzun bir zincir. Geniş bantlı EH almaçlarında hâlâ
yaygındır; sayısal IF'in yükselişi ikinci dönüşümü giderek FPGA'ya
taşımaktadır.

:::pasaport durak="IF çıkışı (ADC girişi)" alan=analog
Alan: analog (IF)
!Frekans: {{s:on_uc.if_ghz}} GHz = {{s:sinyal.rf_ghz}} − {{s:on_uc.lo_ghz}} (low-side) · IF filtre bandı ±{{s:ddc.cikis_bant_mhz}} MHz
Tip: reel IF gerilimi, 50 Ω, diferansiyel (balun sonrası)
!Seviye: −60 + {{s:on_uc.kazanc_toplam_db}} = **−20 dBm** (referans darbe) · ADC tam ölçeği {{s:adc.tam_olcek_dbm}} dBm → −24 dBFS
!Gürültü tabanı: −89.2 + {{s:on_uc.nf_friis_db}} + 40 = **−45.8 dBm** (B = 300 MHz) · SNR ≈ 25.8 dB
!Evrilme: hayır (INV_ANALOG = 0) — image {{s:on_uc.image_ghz}} GHz preselector'da bastırıldı
Bilinen spur girişleri: 8.5 GHz (2×2), 10.5 GHz (2×3) bant içinde
Bit / fs: — (bir sonraki durak ADC)
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Mixer'ın kalitesi üç sayıdır: dönüşüm kaybı (NF'e girer), IIP3 (spur ve
IMD), izolasyon (LO sızıntısı). LO'nun kalitesi faz gürültüsüdür
({{bolum:5}}). Frekans planı bu sayılarla preselector'ın ve IF filtresinin
şekli arasındaki pazarlıktır; iyi bir plan, en tehlikeli spur'u (half-IF)
mixer'ın en iyi bastırdığı yere değil, bandın en boş yerine koyar. Image
reddi mixer'dan **önce** bitmiş olmalıdır; sonradan telafi yoktur.
::fpga::
FPGA analog mixer'ı görmez; ama iki bilgiyi ondan **miras alır**: (1) IF'te
gördüğü frekansın RF'e dönüşü LO ve side'a bağlıdır — bu dönüşüm FPGA'da
değil yazılımda yapılır, FPGA yalnızca IF (ya da baseband) frekansı
ölçer; (2) evrilme sayacı. Referansta analog kat evirmez, ADC'nin 2. Nyquist
bölgesi evirir; toplam tek evrilme NCO'nun işareti (ya da I/Q swap) ile
düzeltilir ({{bolum:14}}). FPGA'daki kompleks mixer analog mixer'ın
ikizidir ama tek yanlıdır: image üretmez, toplam ürünü yoktur, spur'u NCO
tablosundan gelir.
::yazilim::
Senin tablonun satırı: `LO_FREQ`, `HIGH_SIDE`, `PRESEL_SEL`, "bilinen
spur listesi". Üç iş: (1) PDW'nin RF alanını hesapla: $f_{RF} = f_{LO} +
f_{IF}$ (low-side) ya da $f_{LO} − f_{IF}$ (high-side); IF'i FPGA'dan
baseband ofseti olarak alıyorsan ADC katlaması ve NCO'yu da zincire kat
({{bolum:8}}, {{bolum:25}}). (2) LFM eğiminin ve I/Q'nun işaretini toplam
evrilme sayısına göre düzelt. (3) LO yeniden ayarlanırken (PLL kilitlenme
süresi, onlarca µs–ms) üretilen PDW'leri geçersiz işaretle; kilit kaybı
kesmesini (lock-detect) izle.
:::

## Yazılımcıya dokunan yer

LO bir PLL sentezleyicidir; register düzeyinde genellikle bir tam sayı
bölücü, bir kesirli bölücü ve referans frekansından oluşur. Çoğu kartta bu
ayrıntı bir sürücünün arkasındadır ve sana `lo_set_hz()` gibi bir arayüz
kalır. Asıl senin olan kısım, **frekans planı tablosu** ve IF → RF
dönüşümüdür:

```c
#include <stdint.h>

/* Kurgusal, öğretici frekans planı satırı */
typedef struct {
    uint64_t lo_hz;        /* LO frekansı */
    uint8_t  high_side;    /* 1: LO > RF → IF'te evrilme */
    uint8_t  presel_sel;   /* preselector bank seçimi */
    uint32_t if_merkez_hz; /* IF filtre merkezi (1.8 GHz) */
} plan_t;

/* FPGA'nın ölçtüğü IF frekansından RF'e dönüş.
 * if_hz: IF eksenindeki gerçek frekans (ADC katlaması ve NCO düzeltilmiş,
 *        bkz. Bölüm 8 ve 25). */
static uint64_t rf_hz_hesapla(const plan_t *p, uint32_t if_hz)
{
    return p->high_side ? p->lo_hz - if_hz : p->lo_hz + if_hz;
}

/* Toplam evrilme sayısı: analog high-side (0/1) + çift Nyquist bölgesi (0/1)
 * + NCO işareti düzeltmesi (0/1). Tek sayı → LFM eğimi ve I/Q işareti ters. */
static int evrilme_tek_mi(const plan_t *p, int nyquist_bolgesi, int nco_inv)
{
    int n = (p->high_side ? 1 : 0) + ((nyquist_bolgesi % 2 == 0) ? 1 : 0) + (nco_inv ? 1 : 0);
    return n & 1;
}

/* referans senaryo: lo 7.6 GHz, low-side, IF 1.8 GHz → RF 9.4 GHz
 *   plan_t ref = { 7600000000ull, 0, 2, 1800000000u };
 *   rf_hz_hesapla(&ref, 1800000000u) == 9400000000ull
 *   evrilme_tek_mi(&ref, 2, 1) == 0  → ADC evirdi, NCO düzeltti, net düz */
```

`uint64_t` şart: 9.4 GHz, 32 bitte taşar (4.29 GHz sınırı). `if_hz`
ölçümünün hangi eksende olduğunu netleştir: FPGA sana baseband ofsetini
(±150 MHz) veriyorsa önce NCO frekansını ekleyip ADC katlamasını geri almak
gerekir; bu zinciri {{bolum:25}} tamamlar. `evrilme_tek_mi` her katmanın
kendi işaret bayrağıyla beslenir; en sık hata, katmanlardan birinin
unutulmasıdır — o zaman CW tonlar doğru, LFM eğimleri ters çıkar.

:::saha-notu LO'yu kaydırarak image'ı ayırt et
Bir emiterin gerçek mi image mi olduğunu üç saniyede anlarsın: LO'yu +δ
(örneğin 1 MHz) kaydır. Gerçek sinyal (low-side) IF'te **−δ** kayar, image
**+δ** kayar; high-side'da tersi. Yön beklediğinin tersiyse image'a (ya da
bir spur'a) bakıyorsun demektir. Aynı test half-IF spur'unu da yakalar: 2×2
ürünü LO kaymasına **2δ** ile tepki verir.
:::

:::tuzak "LFM eğimi ters çıkıyor, chirp'i yanlış ölçüyoruz"
Ölçüm doğru olabilir; işaret zinciri eksik. Analog high-side dönüşüm, ADC'nin
çift numaralı Nyquist bölgesi ({{bolum:8}}) ve NCO işareti ({{bolum:14}})
üç ayrı evirme kaynağıdır; tek sayıda evirme kaldıysa spektrum aynadır. Kurgusal
ama tipik: donanım ekibi ADC'nin evirdiğini bilir ve NCO'yu ters çevirir;
sonra biri frekans planını high-side bir satıra geçirir ve yazılım
`HIGH_SIDE` bayrağını okumaz. CW tonlarla yapılan tüm testler geçer (tek
çizgi doğru yerdedir), LFM'de eğim ters, faz kodlu darbede kod "eşlenik"
çıkar. Kontrol: bilinen yönde bir LFM üreteci ile uçtan uca test; eğimin
işaretini plan satırı değişince tekrar kontrol et.
:::

:::tuzak Tüm PDW'lerin RF'i birkaç MHz kaymış
Hepsi aynı yönde ve aynı miktarda kaymışsa suçlu FPGA değil LO'dur:
sentezleyicinin referansı (10 MHz OCXO vb.) kaymış ya da yanlış plan satırı
yüklenmiştir (LO 7 600 yerine 7 604 MHz). Frekans ölçümünün doğruluğu
({{bolum:25}}) LO'nun doğruluğundan iyi olamaz; 1 ppm'lik referans hatası
7.6 GHz'te 7.6 kHz, 100 ppm'lik bir kristal 760 kHz kaydırır. Teşhis: bilinen
frekansta CW ton ver, hatanın LO frekansıyla orantılı olup olmadığına bak
(iki farklı plan satırında ölç). Çözüm yazılımda değil, referansta ya da
tabloda.
:::

:::tuzak LO sızıntısı "sürekli emiter" olarak PDW üretir
LO'nun IF portuna sızıntısı IF bandının dışındadır (7.6 GHz), AAF onu
keser. Ama LO'nun RF portuna sızıp antenden yayılması komşu almacın işidir
— ve komşu almaç sensin, çünkü çok kanallı kartta kanal 1'in LO'su kanal 2'nin
preselector'ından girer. Belirti: tam LO frekansında (ya da onun bir
harmoniğinde) sabit genlikli, PW'si "sonsuz" ya da tuhaf bir CW emiter. Kontrol:
anteni sonlandırıcıyla değiştir; emiter kaybolmuyorsa içeriden geliyor.
Çözüm donanımda (izolasyon, ekranlama) ama yazılımda bilinen LO frekanslarını
"kendi sızıntım" listesine koymak ucuz bir savunmadır.
:::

:::ozet
- Mixer bir çarpıcıdır: iki kosinüsün çarpımı fark ve toplam frekansı üretir; IF filtresi farkı seçer. Her ürün −6 dB, dönüşüm kaybının kaynağı.
- RF havadaki frekans, IF sabit ara durak, baseband taşıyıcısı sıfırlanmış hal. IF'e inmenin nedenleri: kolay filtre, bölünmüş kazanç, ADC erişimi; sabit IF tarama sırasında zinciri değiştirmez.
- Image = 2·f_LO − f_RF, IF'ten eşit uzaklıktaki öbür giriş; mixer'dan önce preselector (ve varsa image-reject mixer) ile bastırılır. IF yüksek → image uzak.
- Low-side'da spektrum düz iner, high-side'da evrilir (LFM eğimi, I/Q işareti ters). Evrilme bir sayaçtır: her high-side ve her çift Nyquist bölgesi bir kez evirir.
- Mixer tüm |m·f_in − n·f_LO| ürünlerini üretir; half-IF (2×2) spur'u RF ile LO'nun ortasında ve preselector'ın içindedir. LO sızıntısı 0×1 ürünüdür.
- Frekans planı: IF, LO, preselector ve Nyquist bölgesinin image ve spur'ları boş yerlere düşürecek biçimde seçilmesi; yazılımda bir tablo olarak yaşar.
- Yazılım için: f_RF = f_LO ± f_IF (64 bit), toplam evrilme sayısı, LO kilitlenme süresinde PDW'leri geçersiz say, LO kaydırma testi ile image/spur ayrımı.
:::

:::kendini-sina
S: RF = 9.4 GHz, IF = 1.8 GHz. Low-side ve high-side için LO ve image frekanslarını yaz; hangisinde IF spektrumu evriktir?
C: Low-side: LO = 7.6 GHz, image = 5.8 GHz, düz. High-side: LO = 11.2 GHz, image = 13.0 GHz, evrik. IF her ikisinde 1.8 GHz — FPGA fark görmez, yalnızca yazılımın dönüşümü ve işareti değişir.
S: Preselector 8–11 GHz. Aynı zincirde IF'i 1.8 yerine 0.4 GHz seçseydin image nerede olurdu ve ne olurdu?
C: Low-side LO = 9.0 GHz, image = 8.6 GHz: preselector bandının **içinde**. Filtre onu bastıramaz; 8.6 GHz'deki her emiter 9.4 GHz'de görünür. Image'ı uzağa atmak için IF'i yükseltmen (ya da image-reject mixer ve dar ayarlı bir preselector kullanman) gerekir.
S: Half-IF spur'u nedir ve referans planda hangi giriş frekansından gelir? Preselector bunu neden çözemez?
C: 2·f_in − 2·f_LO = f_IF olan giriş, f_in = (f_RF + f_LO)/2 = 8.5 GHz. RF ile LO'nun tam ortasında, preselector bandının (8–11) içinde olduğu için filtre geçirir; yalnızca mixer'ın 2×2 bastırması ve girişteki seviye korur.
S: LO'yu 1 MHz yukarı kaydırdın; IF'te bir çizgi 1 MHz yukarı, öteki 1 MHz aşağı kaydı. Low-side plandasın. Hangisi gerçek?
C: Low-side'da f_IF = f_RF − f_LO: gerçek sinyal LO artınca **aşağı** kayar. Yukarı kayan, image (f_IF = f_LO − f_img) ya da benzer davranan bir spur'dur.
:::

:::kopru
Mixer ve IF'i kurduk; artık aynı yapıtaşlarını farklı sıralarla dizmenin ne
kadar farklı almaçlar doğurduğuna bakabiliriz. Bölüm 7, kristal video
almaçtan sayısal kanallaştırıcıya on mimariyi aynı sembol diliyle çizer,
"analog–sayısal sınır nereye kaydı" sorusunu sorar ve referans zincirimizin
bu haritada nerede durduğunu gösterir.
:::
