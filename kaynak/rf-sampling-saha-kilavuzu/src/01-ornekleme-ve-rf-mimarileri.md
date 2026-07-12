# Bölüm 1 — Örnekleme Teorisi ve RF Mimarileri

Elindeki AFE'nin datasheet'i "RF sampling transceiver" diyor. Bunun anlamı
şu: kartında mixer yok, IF (intermediate frequency — ara frekans) katı yok;
anten sinyali birkaç analog bloktan geçip **doğrudan ADC'ye** giriyor. Bu,
on yıl önce çılgınlık sayılırdı. Bu bölümde önce bunun neden mümkün olduğunu
(örnekleme teorisi), sonra neden tercih edildiğini (mimari evrim) ve bedelini
(analog ön uç + clock kalitesi) anlayacağız. Buradaki kavramlar — özellikle
Nyquist bölgeleri ve folding — {{sec:2}}'deki spur analizinin ve
{{sec:8}}'deki jitter tartışmasının temelidir.

::: ogren
- Nyquist teoremi ve aliasing'in ne olduğunu, folding hesabını
- Nyquist bölgelerini ve undersampling'in (2./3. bölge örnekleme) mantığını
- Superheterodyne → zero-IF → direct RF sampling evriminin trade-off'larını
- Direct sampling'de bile LNA/filtre/DSA/balun'un neden yaşadığını
- Basit bir frekans planının nasıl yapıldığını
:::

## Örnekleme: sürekli dünyadan sayılara

ADC (analog-to-digital converter — analogdan sayısala çevirici), sürekli bir
gerilim dalgasını saniyede fs kez ölçüp sayıya çevirir; fs'e **örnekleme
hızı** denir. Nyquist teoremi der ki: bant genişliği B olan bir sinyali
kayıpsız temsil etmek için **fs > 2·B** olmalıdır. Dikkat: kural sinyalin
*en yüksek frekansı* değil, *bant genişliği* üzerinden yazılır — bu ayrım
birazdan undersampling'i mümkün kılacak.

Kurala uymazsan ne olur? Sinyal yok olmaz; **başka bir frekansta görünür**.
Buna aliasing (örtüşme/takma ad) denir. Sayısal örnek: fs = 100 MHz ile
örneklediğin 70 MHz'lik bir ton, ADC çıkışında **30 MHz'de** belirir
(100 − 70 = 30). ADC çıkışındaki hiçbir bilgi ona "aslında 70'tim" demez;
30 MHz'lik gerçek bir tondan ayırt edilemez. Genel kural: f frekanslı bir
ton, örnekleme sonrası

```text
f_görünen = | f − k·fs |        (k: f'e en yakın fs katı)
```

frekansına düşer. 70 MHz için k=1: |70 − 100| = 30 MHz. 230 MHz için k=2:
|230 − 200| = 30 MHz. Gördüğün gibi 30, 70, 130, 170, 230 MHz... hepsi aynı
yere iner: örnekleme, frekans eksenini **fs/2'nin katlarında akordeon gibi
katlar**. Bu yüzden aliasing'e folding (katlanma) da denir.

## Nyquist bölgeleri ve undersampling

Katlanan ekseni dilimlemek işleri kolaylaştırır: **n. Nyquist bölgesi**,
(n−1)·fs/2 ile n·fs/2 arasıdır. 1. bölge 0..fs/2, 2. bölge fs/2..fs, 3.
bölge fs..3fs/2... Her bölgenin içeriği, ADC çıkışında 1. bölgeye iner —
tek farkla: **çift numaralı bölgelerden gelenler aynalanır** (bandın alçak
ve yüksek kenarı yer değiştirir), tek numaralılar düz iner.

![Nyquist bölgeleri ve spektrum katlanması. 2. bölgedeki gerçek RF bandı, ADC çıkışında 1. bölgeye aynalanmış olarak düşer; A–B kenar işaretlerine dikkat.](../diagrams/svg/d10.svg)

Şimdi kilit fikir: madem 2. bölgedeki bir bant, 1. bölgeye *temiz bir
şekilde* katlanıyor, o zaman sinyali taşımak zorunda değilim — **ADC'yi
sinyalin bulunduğu bölgede çalıştırırım, katlanma benim mixer'ım olur.**
Buna undersampling (alt-örnekleme) veya harmonic/IF sampling denir ve direct
RF sampling'in sırrı budur.

Sayısal örnek ({{fig:d10}}'daki senaryo): S-band radar alıcısı, bant
2.7–2.9 GHz, ADC fs = 3 GS/s. Bölge sınırı fs/2 = 1.5 GHz; 2.7/1.5 = 1.8 →
bant **2. bölgede** ve tamamı tek bölge içinde kalıyor (2.7 ve 2.9, ikisi de
1.5–3.0 aralığında). ADC çıkışında bant |2.7 − 3.0| = 0.3 GHz ile
|2.9 − 3.0| = 0.1 GHz arasına, yani **100–300 MHz'e aynalanmış olarak**
düşer. 200 MHz'lik bant genişliği için 3 GS/s fazlasıyla yeterli — Nyquist'i
bant genişliği üzerinden okumanın anlamı bu.

::: dikkat
Undersampling bedava değildir. İki bedeli var: (1) ADC'nin **analog giriş
bant genişliği** sinyal frekansını görebilmeli — fs değil, giriş katının
analog bant genişliği sınırlar; datasheet'te ayrı bir satırdır. (2) Aynı
jitter, giriş frekansı yükseldikçe **orantılı olarak daha çok SNR yer** —
2.9 GHz'te örnekleme anındaki pikosaltı titreme, 100 MHz'tekinden ~29 kat
daha yıkıcıdır. Formülü ve sayıları {{sec:2}}'de göreceğiz; clocking'in
neden ayrı bir kısım ({{sec:8}}–{{sec:10}}) hak ettiğinin cevabı da budur.
:::

## Mimari evrim: superheterodyne → zero-IF → direct sampling

RF alıcı tasarımının yüz yıllık sorusu şu: GHz'lerdeki sinyali, işlenebilir
bir forma nasıl indiririm? Üç cevap, üç mimari:

![Üç alıcı mimarisi. Turuncu bloklar LO/clock üretimini gösterir; direct sampling'de mixer ve LO'nun yokluğuna, DDC'nin çip içine taşınmasına dikkat.](../diagrams/svg/d09.svg)

**Superheterodyne** (süperheterodin): sinyali bir mixer ve LO (local
oscillator — yerel osilatör) ile sabit bir IF'e indir, seçiciliği IF
filtresinde (genelde SAW) yap, ADC'yi IF'te çalıştır. Artısı: mükemmel
seçicilik, on yıllarca rafine edilmiş, öngörülebilir performans. Eksisi:
mixer istemeden **imaj frekansını** da indirir (LO'nun öbür yakasındaki bant
IF'e üst üste biner), bu yüzden mixer'dan önce imaj-reddetme filtresi
şarttır; her bant için ayrı filtre/LO planı gerekir; parça sayısı ve kart
alanı büyüktür; "bandı değiştir" demek donanımı değiştirmek demektir.

**Zero-IF** (direct conversion): IF'i sıfıra indir — LO'yu tam sinyal
merkezine koy, çıkan I/Q (in-phase/quadrature — eşfaz/dördün) çiftini iki
yavaş ADC ile örnekle. Artısı: IF filtresi ve imaj problemi yok (imaj,
sinyalin kendisidir), parça az, entegrasyona çok uygun — cep telefonlarının
mimarisi. Eksisi: sinyal DC etrafına indiği için analog kusurlar bandın tam
ortasına oturur: **DC offset**, **LO kaçağı** (LO'nun antene sızıp geri
dönmesi), **I/Q dengesizliği** (iki koldaki kazanç/faz farkı imaj spur'u
üretir), düşük frekans 1/f gürültüsü. Bunların hepsi kalibrasyonla
bastırılır ama hiç bitmez.

**Direct RF sampling**: mixer'ı ve LO'yu tamamen at; GS/s sınıfı ADC ile
sinyali RF'te (gerekirse 2./3. Nyquist bölgesinde) doğrudan örnekle;
"indirme" işini çip içindeki DDC yapsın ({{sec:3}}). Artısı: **esneklik** —
bant, merkez frekansı, kanal sayısı yazılımla değişir; analog imaj/IF
problemleri yok; çok kanallı sistemlerde kanallar aynı clock'tan örneklediği
için **faz koherensi** (beamforming'in ön şartı, {{sec:10}}) çok daha kolay.
Eksisi: ADC güç tüketimi ve maliyeti; devasa örnek selini taşıma problemi
(JESD204'ün varlık sebebi, {{sec:3}}–{{sec:5}}); ve en kritiği, **clock
kalitesine vahşi bir bağımlılık** — jitter bütçesi femtosaniyelerle konuşulur.

| | Superheterodyne | Zero-IF | Direct RF |
|---|---|---|---|
| Seçicilik | Mükemmel (IF filtre) | Orta (LPF + dijital) | Dijitalde (DDC) |
| İmaj problemi | Var, filtreyle | Yapısal olarak az | Yok (bölge planıyla) |
| Parça sayısı | Yüksek | Düşük | En düşük (RF'te) |
| Esneklik | Düşük | Orta | Yüksek |
| Çok kanal koherens | Zor | Orta | Doğal |
| ADC talebi | Düşük (IF) | Düşük (baseband) | Çok yüksek (GS/s) |
| Clock talebi | LO kalitesi | LO kalitesi | fs jitter'ı kritik |

::: not
Evrim "eskisi öldü" demek değil. Dar bantlı, çok yüksek dinamik aralıklı
sistemlerde superheterodyne hâlâ yaşıyor; zero-IF, güç/maliyet baskısı olan
her yerde. Direct sampling, esneklik ve kanal sayısının kazandığı yerde —
faz dizili radar, elektronik harp, çok bantlı baz istasyonu — standart
haline geldi.
:::

## Analog ön uç neden ölmedi?

"Doğrudan örnekleme" pazarlaması, anteni ADC bacağına lehimleyebileceğin
hissi verir. Veremezsin. {{fig:d09}}'un üçüncü satırındaki dört blok orada
kalır ve her birinin nedeni senin işini etkiler:

- **LNA**: ADC'ler görece gürültülüdür. Zincirin gürültü figürünü (NF) ilk
  kat belirler; anten sinyalini önce düşük gürültüyle yükseltmezsen, ADC
  gürültü tabanı zayıf sinyalleri yutar. LNA kazancı sabittir; sistemin
  hassasiyeti büyük ölçüde burada doğar.
- **Ön seçici filtre**: Aliasing bölümünün pratik sonucu — ADC, seçtiğin
  Nyquist bölgesinin *dışındaki her şeyi de* bandına katlar. 2. bölgede
  çalışıyorsan, 1. ve 3. bölgedeki her sinyal (komşu banttaki bir verici,
  kendi kartındaki bir clock harmoniği) senin bandına iner. Klasik
  "anti-alias alçak geçiren filtre" burada **bant geçiren** olur: görevi,
  hedef bölge dışını bastırmak. Filtre yazılımla değişmez; frekans planın
  filtreyle uyumlu olmak zorundadır.
- **DSA** (digital step attenuator — sayısal adımlı zayıflatıcı): ADC'nin
  tam ölçeği (full scale) sabittir. Sinyal çok güçlüyse ADC doyar (clipping
  — spektrumda her yere spur saçar), çok zayıfsa kuantalama gürültüsüne
  gömülür. DSA, kazancı senin kontrolüne verir. **Bu senin register'ın**:
  init sırasında ve çalışma anında AGC/güç yönetimi politikasını yazılım
  kurar; yanlış DSA ayarı, sahada "SNR kötü" şikâyetlerinin klasik
  sebebidir ({{sec:15}}).
- **Balun** (balanced-unbalanced dönüştürücü): anten ve kablo dünyası
  single-ended, GS/s ADC girişleri gürültü bağışıklığı için
  **diferansiyeldir**. Balun bu köprüyü kurar; pasif ve görünmezdir ama
  bant dışına çıktığında kazanç/faz dengesizliğiyle performansı o da bozar.

::: saha
Kart açılışında ADC'den anlamsız, geniş bantlı "çimen" görüyorsan ilk
şüphelin RF zinciri değil, DSA init değeri olsun: reset sonrası bazı
AFE'lerde DSA maksimum zayıflatmada, bazılarında sıfırda uyanır. İki uçta da
spektrum "bozuk" görünür — biri gürültüye gömer, öbürü doyurur. Datasheet'in
reset-değeri tablosunu init kodunla karşılaştırmak beş dakikanı alır.
:::

## Frekans planlama ve folding

Direct sampling sisteminde fs seçimi bir mühendislik kararıdır ve yanlışı
pahalıdır, çünkü katlanma yalnızca sinyaline değil, **bozulmalara da**
uygulanır. ADC'nin ürettiği ikinci ve üçüncü harmonikler (HD2, HD3) sinyal
bandının 2 ve 3 katında doğar, sonra fs etrafında katlanıp *herhangi bir
yere* — en kötü ihtimalle bandının içine — düşebilir.

Mini örnek, yukarıdaki radar senaryosuyla: bant 2.7–2.9 GHz, fs = 3 GS/s.
HD2 5.4–5.8 GHz'te doğar. 5.4/1.5 = 3.6 → 4. bölge; katlama: |5.4 − 2·3.0| =
0.6 GHz, |5.8 − 6.0| = 0.2 GHz → HD2, çıkışta 200–600 MHz'e iner. Sinyalin
100–300 MHz'e indiğini hesaplamıştık: **200–300 MHz aralığında üst üste
binerler.** Bu plan kusurlu; fs'i veya bandı kaydırmak gerekir (örneğin
fs = 2.6 GS/s ile aynı hesabı yapmayı okura egzersiz bırakıyorum — bu
dokümanda tek egzersiz bu olsun). Gerçek projede bu analiz, üreticilerin
frekans planlama araçlarıyla tüm spur aileleri (HD2–HD5, interleaving
spur'ları — {{sec:2}}) için otomatik yapılır; ama aracın ne aradığını bilmek
zorundasın, çünkü çıktısındaki "bu plan temiz" cümlesinin geçerlilik şartı
senin filtre ve DSA seçimlerindir.

::: not
Aynı katlama mantığı verici (DAC) tarafında da işler ama ters yönde: DAC,
istediğin sinyalin **imajlarını** fs'in katları etrafında üretir ve bunları
analog filtreyle bastırman gerekir. DAC'ye {{sec:2}}'nin sonunda geleceğiz.
:::

Artık sinyalin *neden* GS/s hızında sayılara dönüştüğünü biliyorsun. Sıradaki
soru: bu sayılara ne kadar güvenebilirsin? ADC ve DAC datasheet'lerindeki
o metrik ormanı — SNR, ENOB, SFDR, NSD — tam olarak bu sorunun cevabıdır.

<details class="kaynaklar">
<summary>Bu bölümün kaynakları</summary>

- Analog Devices, MT-002: *What the Nyquist Criterion Means to Your Sampled
  Data System Design* — Nyquist bölgeleri ve undersampling.
- Analog Devices, zero-IF mimarisi teknik makaleleri — direct conversion
  kusurları (DC offset, LO kaçağı, I/Q dengesizliği).
- TI, RF-sampling mimari uygulama notları ve TI Precision Labs ADC serisi —
  direct sampling ön ucu, DSA, frekans planlama.
- Toplu ve linkli liste: {{sec:19}}.

</details>
