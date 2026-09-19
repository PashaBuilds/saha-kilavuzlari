# Bölüm 21 — Tespit Teorisinin Temeli
::kisim VII — Tespit: Eşik, Gürültü Tahmini, Yanlış Alarm
::meta onkosul=1,2,4,9 acar=22,23,25,26 blok=esik rota=yazilimci

:::neden-onemli
Sahadan soru: "Eşiği kaç dB'ye koyalım?" Bu soruya "gürültünün 10 dB üstüne"
diye cevap veren herkes bir hafta sonra ikinci soruyu sorar: "Sistem boşta
dururken saniyede yüzlerce darbe raporluyor, neden?" Cevap eşiğin değerinde
değil, eşiğin *ne anlama geldiğinde* saklıdır. Bir eşik iki olasılığı aynı
anda belirler: gürültünün tek başına onu aşma olasılığı (yanlış alarm) ve
sinyal varken aşılma olasılığı (tespit). Bu ikisi arasında bedava bir bölge
yoktur; birini iyileştiren her hamle diğerini bozar. Bu bölüm, o pazarlığın
matematiğini — Rayleigh, Rician, Pfa, Pd, ROC — bir yazılımcının register'a
yazacağı sayıya kadar indirir ve "10⁻⁶ küçük bir sayı mı?" sorusuna 300 MSPS'te
şaşırtıcı bir cevap verir.
:::

## Sezgi: iki torba, bir çizgi

İki torba düşün. Birinde yalnızca gürültü örnekleri var; genlikleri çoğunlukla
küçük ama arada sırada büyük bir tane çıkıyor. Diğerinde gürültünün üstüne
sabit bir sinyal binmiş örnekler var; genlikleri daha büyük ama onların da
küçükleri var. Sana tek bir örnek veriyorlar ve soruyorlar: hangi torbadan?
Elindeki tek araç bir çizgi çekmek: çizginin üstündekilere "sinyal", altındakilere
"gürültü" diyeceksin.

Çizgiyi nereye çekersen çek iki tür hata yaparsın. Gürültü torbasının büyük
örnekleri çizgiyi aşar: **yanlış alarm** (false alarm). Sinyal torbasının
küçük örnekleri çizginin altında kalır: **kaçırma** (miss). Çizgiyi yukarı
çekersen yanlış alarm azalır ama kaçırma artar; aşağı çekersen tersi. Torbaların
içeriğini değiştirmeden bu ikisini aynı anda iyileştiremezsin. İçeriği değiştiren
tek şey SNR'dır: sinyal ne kadar güçlüyse iki torba o kadar az örtüşür.
Tespit teorisinin tamamı bu iki torbanın *şeklini* (dağılımını) bilmek ve çizgiyi
bilinçli bir yere çekmektir.

:::analoji Duman dedektörü
Mutfaktaki duman dedektörü de aynı pazarlığı yapar. Hassas ayarlarsan kızartma
yaparken çalar (yanlış alarm); az hassas ayarlarsan gerçek bir yangında geç
kalır (kaçırma). Üretici hassasiyeti "yılda bir yanlış alarm" gibi bir hedefe
göre seçer — Pfa hedefi — ve sonra o ayarla "ne kadar duman gerekir" sorusu
kendiliğinden cevaplanır. Almaçta da sıra budur: önce kabul edilebilir yanlış
alarm oranı, sonra ondan türeyen eşik, en sonda "bu eşikle hangi sinyali görürüm".
:::

## Kavram: iki hipotez, dört sonuç

Resmî dil iki **hipotez** kurar: **H0** — yalnız gürültü var; **H1** — sinyal
artı gürültü var. Her örnekte (ya da her hücrede) almaç bir karar verir: "var"
ya da "yok". Gerçek ile karar çaprazlanınca dört sonuç çıkar:

| | Karar: "yok" | Karar: "var" |
|---|---|---|
| **H0 gerçek** (yalnız gürültü) | doğru ret (1 − Pfa) | **yanlış alarm** — olasılığı **Pfa** |
| **H1 gerçek** (sinyal var) | **kaçırma** — olasılığı 1 − Pd | **tespit** — olasılığı **Pd** |

**Pfa** (probability of false alarm — yanlış alarm olasılığı) ve **Pd**
(probability of detection — tespit olasılığı) bu tablonun iki bağımsız sayısıdır;
diğer ikisi bunların tümleyenidir. Eşik tek bir düğmedir ve bu iki sayıyı
*birlikte* hareket ettirir. Şekle bakalım.

{{svg:g-210-iki-pdf-esik.svg|İki hipotezin zarf dağılımları ve eşik. Üstte lineer eksende: H0 yalnız gürültü (gri, Rayleigh) ve H1 sinyal + gürültü (mavi, Rician, SNR = 13.2 dB); altın kesikli eşik T = 5.257σ. Eşiğin sağındaki mavi alan Pd = 0.90; gri kuyruk Pfa = 10⁻⁶ lineer eksende görünmez bile. Altta aynı dağılımlar logaritmik eksende: 10⁻⁶'lık kuyruk artık görünür. Sağ üstte dört sonuç matrisi.}}

Şeklin söylediği ilk şey şu: **eşik iki dağılımı keser** ve kestiği yerin
sağında kalan iki alan Pfa ile Pd'dir. İkinci şey: Pfa = 10⁻⁶ gibi bir değer
lineer eksende *görünmez*. Gürültü dağılımının o kadar uzağındaki kuyruğu
ancak logaritmik eksende görürsün; bu yüzden tespit hesapları hep log
eksende, hep kuyrukla ilgilidir. Gürültü dağılımının **şekli** — özellikle
kuyruğun ne kadar hızlı söndüğü — Pfa'yı belirler. O şekli bilmemiz gerekiyor.

## Kavram: gürültünün şekli — Gauss'tan Rayleigh'e

{{bolum:9}}'da ADC çıkışındaki termal gürültünün Gauss dağılımlı olduğunu,
{{bolum:15}} ve {{bolum:16}}'da DDC'nin bu gürültüyü kompleks I/Q'ya taşıdığını
görmüştük. Sonuç: I ve Q'nun her biri sıfır ortalamalı, aynı **σ** standart
sapmalı, birbirinden bağımsız Gauss gürültüsüdür. Tespit için I ile Q'ya ayrı
ayrı bakılmaz; **zarf** (envelope) $r = sqrt{I^2 + Q^2}$ ya da **güç** $r^2 = I^2 + Q^2$
kullanılır ({{bolum:22}} nedenini anlatır). İki bağımsız Gauss'un karekök-kareler
toplamı **Rayleigh** dağılımıdır; karesi (güç) **üstel** (exponential)
dağılımdır. Üstel dağılımın güzelliği, kuyruk olasılığının tek satırlık kapalı
formu olmasıdır: gücün bir eşiği aşma olasılığı $e^{−P_T / P_{ort}}$.

:::formul id=rayleigh-pfa baslik="Rayleigh zarf, üstel güç ve Pfa"
f: p(r) = frac{r}{σ^2} · e^{−r^2 / 2σ^2}        (zarf, H0)
f: Pfa = P(r > T) = e^{−T^2 / 2σ^2}   ⟺   T = σ · sqrt{−2 · ln Pfa}
f: güç ile: Pfa = e^{−P_T / P_{ort}}   ⟺   P_T = −ln(Pfa) · P_{ort},  P_{ort} = 2σ^2
s: σ | I (ve Q) bileşeninin gürültü standart sapması | V ya da LSB
s: r | zarf, $sqrt{I^2+Q^2}$ | V ya da LSB
s: T | zarf eşiği | σ'nın katı
s: P_T, P_{ort} | güç eşiği ve ortalama gürültü gücü (I²+Q² ortalaması) | LSB²
o: Pfa = 10⁻⁶ → T = σ·√(−2·ln 10⁻⁶) = σ·√27.63 = **{{s:turetilmis_beklenen.rayleigh_esik_sigma}} σ**. Güç ekseninde P_T = 13.8 × ortalama gürültü gücü, yani gürültü ortalamasının **11.4 dB** üstü.
o: Pfa = 10⁻³ için T = 3.72σ (8.4 dB üst); Pfa = 10⁻⁹ için T = 6.44σ (13.2 dB üst). 10⁻⁶'dan 10⁻⁹'a üç mertebe Pfa yalnızca 1.8 dB eşik demektir — kuyruk çok dik.
:::

Bu formülün üç sonucu sahada her gün karşına çıkar. Birincisi, eşik *σ'nın
katı* olarak anlamlıdır: σ'yı bilmeden "eşik = 1200 LSB" cümlesi boştur; σ
kazançla, sıcaklıkla, bantla değişir ({{bolum:23}} bu yüzden vardır). İkincisi,
Pfa'yı 10⁻⁶'dan 10⁻⁹'a bin kat küçültmek eşiği yalnızca 1.8 dB yukarı taşır — Rayleigh kuyruğu
o kadar hızlı söner. Üçüncüsü ve en tehlikelisi: bu kapalı form **yalnız Gauss
gürültü için** doğrudur. Spur'lar, ADC kırpması, komşu kanaldan sızan sinyal
ya da darbeli girişim kuyruğu kalınlaştırır; o zaman gerçek Pfa formülün
verdiğinden mertebelerce büyük olur.

Sinyal varken (H1) I ve Q'nun ortalaması sıfır değil, sinyalin genliği
kadar kaymıştır; zarf bu kez **Rician** dağılımını izler. Rician'ın kapalı
formu Marcum Q fonksiyonu içerir ve elle hesaplanmaz; ama davranışı sezgiseldir:
SNR büyüdükçe Rician, tepesi sinyal genliği A = σ·√(2·SNR) civarında olan
neredeyse Gauss bir tümseğe dönüşür ve Rayleigh'den uzaklaşır (üstteki şekilde
mavi eğri). Pd, bu tümseğin eşiğin sağında kalan kısmıdır.

## Kavram: Pfa–Pd pazarlığı, ROC ve Neyman-Pearson

Eşiği kaydırdıkça Pfa ile Pd birlikte değişir. Bu çifti bir grafiğe koyarsan
— yatayda Pfa (log), düşeyde Pd — bir eğri çıkar: **ROC** (Receiver Operating
Characteristic — almaç çalışma karakteristiği). Eğri üzerindeki her nokta
farklı bir eşiktir; eğrinin kendisi SNR'a bağlıdır.

{{svg:g-211-roc-ailesi.svg|ROC eğri ailesi: tek darbe, bilinmeyen fazlı sinyal (Swerling 0), square-law / zarf dedektörü. Her eğri bir SNR; eğri üzerinde ilerlemek eşiği değiştirmektir. Altın nokta referans senaryo: Pfa = 10⁻⁶, SNR = 13.2 dB → Pd = 0.90; aynı Pfa'da 11.2 dB yalnızca Pd = 0.50 verir. Köşegen Pd = Pfa, "yazı-tura" çizgisidir.}}

ROC'un öğrettiği disiplin **Neyman-Pearson** ölçütüdür: *önce* kabul
edilebilir Pfa'yı seç, *sonra* o Pfa'yı veren eşiği hesapla, Pd ne çıkarsa
kabul et — yetmiyorsa SNR'ı artır (anten, LNA, entegrasyon), eşiği oynatma.
Neden Pfa önce gelir? Çünkü yanlış alarmın maliyeti sistem düzeyinde
ölçülebilir ve sabittir: her yanlış alarm bir PDW'dir, işlemciyi meşgul
eder, izleyicileri kirletir, operatörü yorar. Kaçırmanın maliyeti ise
sinyale bağlıdır ve zaten zayıf sinyal için kaçınılmazdır. Neyman-Pearson
dedektörü, verilen Pfa için Pd'yi en büyükleyen dedektördür ve Gauss
gürültüde bu dedektörün "zarfı sabit bir eşikle karşılaştır"a indirgendiği
gösterilebilir — yani yaptığımız şey keyfî değil, en iyisidir.

## Kavram: hedef Pd için gereken SNR

Pratik soru genellikle ters yönden gelir: "Pfa = 10⁻⁶ ve Pd = 0.9 istiyorum,
kaç dB SNR gerekir?" Kesin cevap Rician dağılımının eşik üstü alanı, yani
Marcum Q fonksiyonudur; `dsp-core`'daki `pdSwerling0` bunu sayısal integralle
hesaplar. Elle hesap için **Albersheim** yaklaşımı yeterince iyidir (0.1 <
Pd < 0.9, 10⁻⁷ < Pfa < 10⁻³ aralığında ≈ 0.2 dB içinde):

:::formul id=albersheim baslik="Albersheim yaklaşımı — tek darbe (N = 1)"
f: A = ln frac{0.62}{Pfa}        B = ln frac{Pd}{1 − Pd}
f: SNR_{dB} ≈ −5 · log_{10} N + (6.2 + frac{4.54}{sqrt{N + 0.44}}) · log_{10}(A + 0.12·A·B + 1.7·B)
s: Pfa, Pd | hedef yanlış alarm ve tespit olasılıkları | —
s: N | non-koherent entegre edilen darbe (örnek) sayısı; tek karar için 1 | —
s: SNR_{dB} | tek darbe (örnek) SNR'ı, zarf dedektörü girişinde | dB
o: Pfa = 10⁻⁶, Pd = 0.5, N = 1 → A = 13.34, B = 0 → SNR ≈ 11.2 dB (kesin Marcum Q: **{{s:tespit.snr_pd05_db}} dB**).
o: Pfa = 10⁻⁶, Pd = 0.9, N = 1 → B = 2.20 → SNR ≈ 13.1 dB (kesin: **{{s:tespit.snr_pd09_db}} dB**). Referans senaryonun {{s:tespit.tespit_snr_db}} dB bütçesi Pd ≈ 0.997 verir; aradaki ≈ 2 dB, Bölüm 23'teki CFAR kaybı ve gerçek gürültünün ideal olmayışı için paydır.
:::

{{svg:g-212-pd-snr.svg|Pd–SNR eğrileri (tek darbe, Swerling 0, zarf dedektörü); parametre Pfa. Pfa = 10⁻⁶ eğrisinde iki altın nokta: 11.2 dB → Pd = 0.5 ve 13.2 dB → Pd = 0.9. Mavi nokta 15 dB bütçe noktası. "Diz" bölgesi diktir: Pd'yi 0.5'ten 0.9'a çıkarmak 2 dB, 0.9'dan 0.99'a çıkarmak 1.3 dB daha ister; Pfa'yı 10⁻³'ten 10⁻⁹'a çekmek aynı Pd için ≈ 4 dB'ye mal olur.}}

Bu eğrilerden aklında kalması gereken iki sayı: **Pd = 0.5 için ≈ 11 dB, Pd =
0.9 için ≈ 13 dB** (Pfa = 10⁻⁶, tek örnek). {{bolum:4}}'te hassasiyeti hesaplarken
kullandığımız "15 dB tespit SNR'ı" işte buradan gelir: 13.2 dB'nin üstüne
CFAR kaybı ve güvenlik payı. Bir tasarımcı sana "hassasiyet −68 dBm" dediğinde
bunun *hangi Pd ve hangi Pfa için* olduğunu sormazsan sayı anlamsızdır;
aynı almaç Pd = 0.5 için 2 dB daha hassas, Pfa = 10⁻⁹ için 1.8 dB daha
sağır görünür.

:::widget id=w17 ad="Tespit laboratuvarı"
- **Referans senaryo** preset'i: SNR = 13.2 dB, Pfa = 10⁻⁶. Eşiğin 5.26σ'da durduğunu, Pd'nin 0.90 çıktığını ve ROC üzerindeki noktanın altın işaretle çakıştığını doğrula. Log-eksen panelinde gri kuyruğun eşiğin sağında 10⁻⁶ seviyesine indiğini gör.
- Eşiği 5.26σ'dan 4σ'ya indir: Pfa 10⁻⁶'dan ≈ 3×10⁻⁴'e fırlasın (300 kat), Pd yalnızca 0.90'dan ≈ 0.99'a çıksın. "Saniyede yanlış alarm" satırında 300 MSPS için 300/s'nin ≈ 100 000/s olduğunu oku.
- Eşiği sabit tut, SNR'ı 13.2'den 11.2 dB'ye düşür: Pd 0.90 → 0.50. Sonra 15 dB yap: Pd ≈ 0.997. Diz bölgesinin ne kadar dar olduğunu gör: 4 dB'lik aralık Pd'yi 0.5'ten 0.997'ye taşıyor.
- **Monte Carlo** sayacını Pfa = 10⁻³ ile çalıştır (200 000 deneme): ölçülen Pfa teorik değerin ±%10'u içinde kalmalı. Pfa = 10⁻⁶'ya dön: 200 000 denemede beklenen yanlış alarm sayısı 0.2'dir; sayaç çoğunlukla 0 gösterir — 10⁻⁶'yı laboratuvarda *ölçmenin* neden saatler sürdüğünü buradan hisset.
:::

## Kavram: Pfa'dan yanlış alarm oranına — 10⁻⁶ küçük müdür?

Pfa bir *olasılıktır*: tek bir kararın yanlış alarm olma olasılığı. Sahada
kimse olasılık saymaz, saniyede kaç yanlış alarm geldiğini sayar. İkisini
bağlayan şey saniyedeki **bağımsız karar sayısıdır**:

:::formul id=far baslik="Yanlış alarm oranı (FAR)"
f: FAR = Pfa · f_{karar}        (1/s)
f: f_{karar} ≈ f_s (her örnekte karar)   ya da   frac{f_s}{L} (L örneklik video filtre / hücre başına bir karar)
s: FAR | saniyedeki ortalama yanlış alarm sayısı (false alarm rate) | 1/s
s: f_{karar} | saniyede verilen bağımsız karar sayısı | 1/s
s: f_s | karar verilen akışın örnek hızı | Hz
s: L | bir karara giren bağımsız örnek sayısı | —
o: Pfa = 10⁻⁶, f_s = {{s:ddc.cikis_fs_msps}} MSPS, her örnekte karar → FAR = 10⁻⁶ × 3×10⁸ = **300 yanlış alarm/s**. Günde 26 milyon.
o: "Saniyede 1 yanlış alarm" istersen Pfa = 1/(3×10⁸) ≈ 3.3×10⁻⁹ gerekir → T = 6.25σ, gürültünün 12.9 dB üstü; Pd = 0.9 için SNR ≈ 14.4 dB'ye çıkar (1.2 dB daha sağır almaç).
:::

Bu, kısmın en önemli sayısıdır: **10⁻⁶ küçük bir Pfa değildir; 300 MSPS'te
saniyede 300 sahte darbe demektir.** Radar ders kitaplarındaki 10⁻⁶ alışkanlığı
menzil hücresi başına saniyede birkaç bin karar veren darbeli radarlardan
gelir; geniş bantlı bir EH almacı her 3.33 ns'de bir karar verir, yani
kararı 10⁵ kat daha sık alır. Aynı "kabul edilebilir yanlış alarm/s" için EH
almacının Pfa'sı beş mertebe daha küçük olmak zorundadır — ya da kararı
seyreltmelisin. Seyreltmenin yolları sonraki bölümlerde geliyor: video
filtre ile L örneği tek karara indirmek ({{bolum:22}}), minimum darbe genişliği
ve histerezis (hysteresis — açma/kapama çift eşiği) ile tek örneklik aşımları
reddetmek ({{bolum:23}}), M-of-N doğrulama. Her biri f_karar'ı düşürür ve aynı Pfa'da FAR'ı azaltır; hepsinin
bedeli zaman çözünürlüğü ya da kısa darbelere körlüktür.

Bir de "bağımsız" sözcüğüne dikkat: DDC filtresi ({{bolum:16}}) çıkışta
komşu örnekleri ilişkilendirir; 300 MSPS akışta gerçekten bağımsız karar
sayısı, gürültü bant genişliği kadar, yani biraz daha azdır. Bu ayrıntı
FAR'ı en fazla 2 kat değiştirir; 10⁵ katlık mertebeyi değiştirmez.

:::saha-notu Pfa'yı ölçmek
Kartın girişini 50 Ω ile sonlandır (sinyal yok, yalnız gürültü) ve tespit
sayacını 10 saniye say. 300 MSPS'te 10⁻⁶ için 3000 ± 55 sayı beklersin.
Ölçülen sayı 30 000 ise eşiğin bir mertebe gevşek (≈ 0.8 dB) *ya da*
gürültü Gauss değil (spur, kırpma, girişim). Ayrım için eşiği 1 dB yükselt:
Gauss gürültüde sayı ≈ 35 kat düşer (kuyruk dik); spur baskınsa neredeyse
hiç düşmez. Bu üç dakikalık ölçüm, yanlış alarm şikâyetlerinin çoğunu
"eşik mi, gürültü mü" diye ikiye ayırır.
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Tespit teorisinin varsayımları RF ön uçta kurulur ya da bozulur. Gauss
gürültü varsayımı, ADC'ye ulaşan gürültünün termal kaynaklı olmasını ister;
LO faz gürültüsü, güç kaynağı spur'ları ve komşu vericilerin sızıntısı kuyruğu
kalınlaştırır ve gerçek Pfa'yı teorinin üstüne çıkarır. SNR'ın kendisi
{{bolum:4}}'teki kaskad hesabından gelir: −{{s:turetilmis_beklenen.gurultu_tabani_dbm}}
dBm'lik tabanın 13.2 dB üstündeki sinyal Pd = 0.9 ile görülür. RF tasarımcı
"1 dB daha az NF" dediğinde bu, Pd–SNR eğrisinde 1 dB sağa kaymak, diz
bölgesindeysen Pd'nin 0.5'ten 0.72'ye çıkması demektir.
::fpga::
Bu bölümün donanımı bir karşılaştırıcıdır: güç örneği ile eşik register'ı,
her saatte bir bit. Asıl iş eşiğin *nereden geldiğidir* — bu Bölüm 23'ün
konusu. Ama bir tasarım kararı buradan verilir: karşılaştırma **güç**
domaininde yapılır (karekök yok, {{bolum:22}}), eşik de güç birimindedir:
$P_T = −ln(Pfa) · P_{ort}$. 20 bitlik güç örneği için eşik de 20 bittir. Pfa
hesabı FPGA'da yapılmaz; yazılım Pfa'dan eşiği (ya da CFAR çarpanını) hesaplar
ve register'a yazar. FPGA'nın katkısı bir **tespit sayacıdır**: her saatte
karşılaştırıcı çıkışını sayan 32 bitlik bir sayaç ve PS'in okuduğu bir
"yakala ve sıfırla" register'ı. Bu sayaç, girişte sinyal yokken FAR
ölçer; kalibrasyonun ve saha teşhisinin temel aracıdır.
::yazilim::
Yazılımcının üç işi var. (1) Pfa'dan eşiğe dönüşüm: $T = σ√(−2 ln Pfa)$ ya da
güçte $P_T = −ln(Pfa) · P_{ort}$; σ ya da P_ort kalibrasyonla ya da Bölüm 23'teki
kestiriciden gelir. (2) Birim disiplini: register LSB² cinsinden güç ister,
sen dBm düşünürsün; dönüşüm zinciri dBm → dBFS → LSB² her kartta farklıdır ve
tek bir yerde, tek bir fonksiyonda yaşamalıdır. (3) FAR'ı **beklenen** değere
karşı izlemek: `det_cnt / süre` ile `Pfa · f_karar`'ı karşılaştır; 3 kat sapma
alarm nedenidir. Aşağıdaki kod bu üçünü toplar.
:::

## Yazılımcıya dokunan yer

Register haritası kurgusal ve öğreticidir; birimlere bak, adreslere değil.

```c
#include <stdint.h>
#include <math.h>

/* Square-law (güç) dedektörü için eşik. Pfa → eşik / ortalama gürültü gücü
 * oranı: -ln(Pfa). p_ort_lsb2: gürültü gücü kestirimi (I²+Q² ortalaması), LSB². */
static uint32_t esik_lsb2(double pfa, double p_ort_lsb2)
{
    double oran = -log(pfa);                 /* 1e-6 → 13.82 (11.4 dB) */
    double p_t  = oran * p_ort_lsb2;
    if (p_t > 1048575.0) p_t = 1048575.0;    /* 20 bitlik güç yolu: doyur */
    return (uint32_t)llround(p_t);
}

/* Zarf (genlik) dedektörü kullanan bir kartta: T = sigma * sqrt(-2 ln Pfa). */
static double esik_zarf(double pfa, double sigma_lsb)
{
    return sigma_lsb * sqrt(-2.0 * log(pfa));   /* 1e-6 → 5.257 sigma */
}

/* Beklenen FAR ve ölçülenle karşılaştırma. det_cnt: DET_CNT register'ı,
 * sure_s: sayaç sıfırlandığından beri geçen süre. */
static double far_beklenen(double pfa, double f_karar_hz) { return pfa * f_karar_hz; }

static int far_saglikli(uint32_t det_cnt, double sure_s, double pfa, double f_karar_hz)
{
    double olculen = det_cnt / sure_s;
    double beklenen = far_beklenen(pfa, f_karar_hz);     /* 1e-6 × 300e6 = 300/s */
    return olculen < 3.0 * beklenen && olculen > beklenen / 3.0;
}
```

İki tuzak bu kodun içinde. `log` doğal logaritmadır; `log10` yazarsan eşik
2.3 kat düşer ve Pfa 10⁻⁶ yerine ≈ 2.5×10⁻³ olur (saniyede 750 000 yanlış
alarm). İkincisi, `p_ort_lsb2` **güç** ortalamasıdır; birisi sana zarfın
(genliğin) ortalamasını verirse Rayleigh ortalaması σ·√(π/2) ≈ 1.25σ'dır,
karesi 2σ² değil 1.57σ²'dir; karıştırırsan eşik 1 dB kayar ve Pfa 20 kat
değişir.

:::tuzak "Pfa = 10⁻⁶ yeterince küçük"
Radar kitabından gelen refleks. 300 MSPS'te 10⁻⁶, saniyede 300 sahte PDW'dir;
PDW FIFO'su darbe yokken bile dolar, izleme yazılımı "300 Hz PRI'lı emiter"
üretir. Belirti: giriş sonlandırılmışken bile sabit bir PDW akışı. Teşhis:
`DET_CNT`'yi say ve `Pfa · f_s` ile karşılaştır — eşleşiyorsa eşik doğru,
*hedef* yanlış. Çare: hedefi FAR olarak koy ("saniyede en fazla 1"), Pfa'yı
ondan türet (3×10⁻⁹) ve kaybettiğin 1.3 dB'yi min-PW / M-of-N ile geri al
({{bolum:23}}).
:::

:::tuzak "Eşiği 3 dB yükselttim, yanlış alarm yarıya inmedi — 50 kat düştü"
Ters yönde bir şaşkınlık: Gauss gürültüde Pfa eşiğin *üssel* fonksiyonudur,
doğrusal değil. Güç eşiğini 3 dB (2 kat) artırmak −ln(Pfa)'yı 13.8'den 27.6'ya
çıkarır: Pfa 10⁻⁶'dan 10⁻¹²'ye iner. Bu "iyi haber" gibi görünür ama iki
yüzü vardır: (1) 3 dB'lik gevşeme de aynı hızla ters çalışır — eşiği "biraz
düşürüp" Pd kazanmaya çalışan yazılımcı FAR'ı bir milyon kat artırır; (2)
eşiği 1 dB yükseltince yanlış alarm *azalmıyorsa* gürültü Gauss değildir;
o 1 dB'yi spur ya da girişim yiyor demektir, eşikle oynamayı bırak ve
spektruma bak.
:::

:::tuzak Hassasiyet sayısının Pd'si yok
"Hassasiyet −68 dBm" cümlesi, yanına Pd ve Pfa yazılmadan karşılaştırılamaz.
Aynı almaç Pd = 0.5 için 2 dB, Pfa = 10⁻³ için 2.4 dB daha "hassas" görünür;
iki tedarikçinin sayısını kıyaslarken 4 dB'lik fark yalnızca tanım farkı
olabilir. Ölçüm raporuna hep üçlü yaz: seviye, Pd, Pfa (ve karar hızı).
:::

:::ozet
- İki hipotez (H0 gürültü / H1 sinyal + gürültü), tek eşik, dört sonuç; eşik Pfa ve Pd'yi *birlikte* kaydırır — bedava bölge yok.
- Gauss I/Q gürültüsü → Rayleigh zarf, üstel güç; sinyal varken Rician. Pfa kapalı form: $Pfa = e^{−T^2/2σ^2}$, $T = σ√(−2 ln Pfa)$; güçte $P_T = −ln(Pfa)·P_{ort}$.
- Pfa = 10⁻⁶ → T = 5.26σ (gürültü gücünün 11.4 dB üstü). Üç mertebe Pfa ≈ 1.8 dB eşik: kuyruk dik, eşik hassas.
- Neyman-Pearson: önce Pfa'yı seç, eşiği ondan türet, Pd'yi SNR belirler. ROC eğrisini yalnız SNR yukarı taşır.
- Pd = 0.5 için ≈ 11.2 dB, Pd = 0.9 için ≈ 13.2 dB (Pfa = 10⁻⁶, tek örnek); 15 dB bütçesinin kalan 2 dB'si CFAR kaybı ve pay.
- FAR = Pfa × karar hızı: 300 MSPS'te 10⁻⁶ = **300 yanlış alarm/s**. Saniyede 1 için Pfa ≈ 3×10⁻⁹ ya da kararı seyrelt (video filtre, min-PW, M-of-N).
- Kapalı formlar yalnız Gauss gürültü için geçerlidir; spur ve girişim kuyruğu kalınlaştırır — Pfa'yı hesaplama, **ölç** (giriş sonlandırılmış, tespit sayacı).
:::

:::kendini-sina
S: Güç dedektörlü bir kartta gürültü gücü ortalaması 400 LSB² ölçüldü. Pfa = 10⁻⁶ için eşik register'ına ne yazarsın; Pfa = 10⁻⁹ için ne değişir?
C: P_T = −ln(10⁻⁶) × 400 = 13.82 × 400 ≈ 5526 LSB². 10⁻⁹ için −ln = 20.72 → ≈ 8290 LSB²; yalnızca 1.76 dB daha yüksek bir eşik, Pfa'yı bin kat düşürür.
S: Bir almaç 300 MSPS'te her örnekte karar veriyor ve boşta saniyede 30 000 tespit sayıyor. Pfa kaçtır; eşik 5.26σ'ya göre kaç dB gevşek?
C: Pfa = 30 000 / 3×10⁸ = 10⁻⁴. T = σ√(−2 ln 10⁻⁴) = 4.29σ; 5.26σ'ya göre 20·log10(4.29/5.26) ≈ −1.8 dB gevşek (güçte −1.8 dB). Ya da eşik doğru, gürültü Gauss değil — eşiği 1 dB yükseltip sayının ≈ 35 kat düşüp düşmediğine bak.
S: SNR 11.2 dB'den 13.2 dB'ye çıktı; Pd neden 0.50'den 0.90'a "sıçradı" ama 13.2'den 15.2'ye çıkınca yalnızca 0.997'ye geldi?
C: Rician dağılımın tümseği eşiğin üstünden geçerken Pd hızla değişir (diz bölgesi); tümsek tamamen eşiğin sağına geçince artık kazanılacak alan kalmaz. Pd–SNR eğrisi S biçimlidir: ortası dik, uçları yatık.
S: Pfa = 10⁻⁶ hedeflenen bir sistemde yazılımcı `log10` kullanmış. Gerçek Pfa nedir?
C: Eşik/gürültü oranı 13.82 yerine 6.0 olur; Pfa = e^{−6} ≈ 2.5×10⁻³, hedefin 2500 katı. 300 MSPS'te saniyede ≈ 750 000 yanlış alarm.
:::

:::kopru
Bu bölümde eşiği zarfa karşılaştırdık ama zarfın kendisini nasıl elde
ettiğimizi sormadık. $sqrt{I^2+Q^2}$ FPGA'da pahalıdır, karekök çoğu zaman
gereksizdir ve ardından gelen küçük bir kayan ortalama gürültüyü sakinleştirirken
darbenin kenarını yumuşatır. Bölüm 22 I/Q'dan zarfa giden yolu, ucuz
yaklaşımları ve "kaç örneği bir karara sığdırmalı" sorusunu ele alır.
:::
