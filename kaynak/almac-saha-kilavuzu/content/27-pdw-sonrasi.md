# Bölüm 27 — PDW'den Sonrası: Ufuk Turu
::meta onkosul=24,25,26 acar=28 blok=ps rota=yazilimci

:::neden-onemli
Sahadan soru: "PDW'ler tampona düşüyor; peki bunlarla ne yapacağız?" Bu
kılavuz bir *almaç* kılavuzudur: darbeyi antenden alıp PDW olarak teslim
eder ve orada durur. Ama PDW'yi tüketen yazılımın ne beklediğini bilmeden
iyi bir PDW akışı tasarlanamaz — hangi alanın toleransı önemli, kayıp neden
sessiz kalmamalı, SEG ve POP bayrakları kimin işine yarıyor. Bu kısa bölüm
PDW'den sonraki üç adımı — deinterleaving, emiter takibi, tanımlama — kavram
düzeyinde tanıtır, almaç tasarımına geri dönen taleplerini çıkarır ve ileri
okumayı gösterir. Formül yok, tek şekil var; amaç yön göstermek.
:::

## Sezgi: karışık bir istasyonun ayak sesleri

Kalabalık bir koridorda gözün kapalı otur ve ayak seslerini dinle. Tek tek
adımlar (PDW) karışık gelir; ama bir süre sonra "şu düzenli, ağır adım aynı
kişi", "şu hızlı topuk sesi başka biri" dersin. Yaptığın şey iki ipucuyla
kümelemektir: adımın **karakteri** (ses tonu, sertliği — RF, PW, AOA) ve
**ritmi** (adım aralığı — PRI). Ritim en güçlü ipucudur, çünkü bir radar
darbelerini rastgele değil, bir zamanlama kuralına göre gönderir. Karakter
bazen yeterlidir (tek başına bir X-bant emiter), bazen değildir (aynı bantta
üç benzer radar); ritim ise darbe kaçırdığında bile tutar — dört adımın
üçünü duysan da aralığı bulursun.

## Deinterleaving: karışık akışı emiterlere ayırma

{{svg:g-270-pdw-sonrasi.svg|Karışık PDW akışından emiter izlerine (üç kurgusal emiter, 10 ms). Üstte almaçtan çıkan haliyle TOA–RF saçılımı: kimin darbesi olduğu bilinmez. Sol altta ardışık TOA farklarının (1.–3. mertebe) histogramı; tepeler PRI adaylarıdır (0.31 ms, 0.62/0.78 ms stagger çifti, 1.00 ms). Sağ altta aday PRI'lerle çıkarılmış üç darbe dizisi. Sayılar kurgusaldır.}}

Almaçtan çıkan PDW akışı zaman sıralıdır ama emiter sıralı değildir;
**deinterleaving** (darbe ayrıştırma) bu akışı emiter başına birer diziye
böler. Klasik yaklaşım iki aşamalıdır. Önce **ön kümeleme**: PDW'ler TOA
dışındaki alanlarla — RF, PW, AOA, varsa MOP tipi — kaba kümelere ayrılır.
Bu adımın toleransları doğrudan {{bolum:25}}'ten gelir: 15 dB'lik darbede RF
±10 kHz değil ±50 kHz, PW ±30 ns; SNR düştükçe pencere açılır. AOA, iki
emiteri RF ve PW aynı olsa bile ayırabildiği için en değerli kümeleme
alanıdır; olmayan sistemde kümeler daha çok karışır.

Sonra her küme içinde **PRI analizi**. En eski ve en anlaşılır yöntem TOA
farkı histogramıdır: küme içindeki PDW çiftlerinin TOA farkları toplanır,
histogramda tepe veren fark bir PRI adayıdır; aday PRI ile dizi çıkarılır
(TOA₀ + k·PRI'ye tolerans içinde düşen PDW'ler alınır), kalan PDW'lerle
işlem tekrarlanır. Literatürde iki isim görürsün: **CDIF** (Cumulative
Difference Histogram — ardışık farkların birikimli histogramı) ve **SDIF**
(Sequential Difference Histogram — mertebe mertebe, alt harmonikleri ve
kaçırılan darbeleri hesaba katan eşikli sürüm). İkisi de "tekrarlayan aralığı
bul" fikrinin mühendislik halleridir; ayrıntı ileri okumada. Modern sistemler
buna PRI dönüşümü, izleme filtreleri ve öğrenmeye dayalı sınıflandırıcılar
ekler; fikir değişmez.

PRI'nin kendisi de bir imzadır: **sabit**, **kademeli** (stagger: birkaç
PRI'nin sabit sırayla dönmesi), **titreşimli** (jitter: kasıtlı rastgele
sapma), **anahtarlamalı** (dwell & switch) ve **kayan** (sliding). Histogram
sabit PRI'de tek tepe, stagger'da birkaç tepe ve toplamlarında bir tepe,
jitter'da yayvan bir tümsek verir. Almaç tasarımına dönen talep şudur: TOA'nın
**tekrarlanabilirliği** ({{bolum:25}}) PRI çözünürlüğünü belirler; 6 ns'lik
TOA jitter'ı, %0.001'lik PRI titreşimini bile görünür kılar; 100 ns'lik jitter
ise kasıtlı jitter'la ölçüm gürültüsünü birbirine karıştırır. Ve **kayıp**
({{bolum:26}}): FIFO taşmasında kaybolan PDW'ler histogramda "kaçırılan darbe"
gibi görünür; `DROP_CNT` sıfır değilse yazılım kaçırma toleransını açar,
sıfırsa kaçırmayı emiterin özelliği (örneğin anten tarama) sayar. Bu yüzden
kayıp sayılmalı, sessiz kalmamalıdır.

## Emiter takibi ve tanımlama

Ayrıştırılmış bir darbe dizisi bir **emiter kaydına** (track) dönüşür: RF
(merkez ve varsa çeviklik örüntüsü), PW, PRI tipi ve değerleri, MOP, AOA,
PA'nın zamanla değişimi. Kayıt yaşayan bir nesnedir: yeni PDW'ler eklenir,
belli süre darbe gelmezse (anten taraması bittiğinde, ya da emiter sustuğunda)
"kayıp" durumuna düşer, geri gelirse birleştirilir. PA'nın zaman içindeki
periyodik inip çıkması emiterin **anten tarama periyodunu** verir — PDW'nin
0.25 dB'lik PA adımı bunun için yeter, ama kalibrasyon kayması bunu bozmaz
(göreli ölçüm). AOA'nın zamanla değişimi platform hareketiyle birleşince
emiterin **konumunu** verir (yön kesiştirme — triangulation); bu noktada PDW'nin TOA'sı
mutlak zamana bağlı olmalıdır ({{bolum:25}}, PPS).

**Tanımlama**, kaydı bir **kütüphaneyle** eşlemektir: bilinen emiter
tiplerinin parametre aralıkları (RF bandı, PW, PRI türü ve değerleri, tarama)
ile kaydın parametreleri karşılaştırılır; her alan için bir uyum puanı,
toplamda bir güven değeri çıkar. Eşleme belirsiz olabilir — birden çok tip
aynı aralığa düşer — ve MOP, tarama periyodu, stagger deseni gibi ince alanlar
belirsizliği kırar. Bu kılavuzun tek katkısı şudur: kütüphanedeki her alanın
toleransı almaçın ölçüm belirsizliğinden **geniş** olmalıdır, yoksa doğru
emiter yanlış diye elenir; ve PDW'nin kalite alanı olmadan bu tolerans
ayarlanamaz. Kütüphane içeriği ve tehdit değerlendirme bu kılavuzun kapsamı
dışındadır ve açık literatürde de yalnızca ilke düzeyinde bulunur.

## Yazılım PDW'yi nasıl tüketir

PS tarafında tipik bir yapı üç katmandır. **Alma katmanı** ({{bolum:26}}'daki
döngü): DMA ring buffer'ından blok kopya, SEQ/DROP kontrolü, parse; PDW'ler zaman
sıralı bir kuyruğa girer. **Ayrıştırma katmanı**: kısa bir pencere (onlarca
ms) üzerinde kümeleme ve PRI analizi; mevcut kayıtlara eşleşen PDW'ler
doğrudan kayda eklenir (öngörü: bir sonraki darbe TOA + PRI'de beklenir — bu,
histogramdan çok daha ucuzdur), eşleşmeyenler yeni kayıt adayı olur.
**Kayıt/tanımlama katmanı**: kayıtların yaşam döngüsü, kütüphane eşleme,
kullanıcı arayüzü ya da üst sisteme rapor. Zaman bütçesi ters orantılıdır:
alma katmanı PDW başına yüz nanosaniyeler, ayrıştırma mikrosaniyeler,
tanımlama milisaniyeler; bu yüzden katmanlar ayrı iş parçacıklarında ve
aralarında kuyruklarla çalışır. Almaçtan gelen her bayrak burada bir karar
olur: SEG'ler birleşip CW kaydına, POP'lar düşük güvenli PDW'ye, SAT'lar PA
kullanılmayan PDW'ye, EXT'ler MOP ayrıntısına dönüşür.

## Kılavuzun bıraktığı yer ve ileri okuma

Bu kılavuz sinyal işlemenin bittiği, bilgi işlemenin başladığı çizgide durur:
PDW üretildi, doğru birimlerde, belirsizliği bilinerek, kayıpsız ya da kaybı
sayılmış olarak PS tamponuna ulaştı. Bundan sonrası ELINT/ESM yazılımının
alanıdır. İki kaynak bu çizgiden devam eder ({{ek:e}}): **Wiley, *ELINT: The
Interception and Analysis of Radar Signals*** — PRI türleri, deinterleaving,
tarama analizi ve parametre ölçümünün ELINT gözüyle bütünü; **Tsui, *Digital
Techniques for Wideband Receivers*** — bu kılavuzun almaç tarafını çok daha
derin ve matematiksel anlatır (özellikle anlık frekans ölçümü ve çok sinyalli
ortam). Radar tarafının kendi işlemesi (eşlenik filtre — matched filter, Doppler) için
**Richards**; LPI radarlar ve onları yakalamanın zorluğu için **Pace**.
Sonraki iki bölüm bu kılavuzun içinde kalır: {{bolum:28}} bütün zinciri tek
tabloda toplar, {{bolum:29}} bozulduğunda nereden bakılacağını gösterir.

:::tuzak "PDW toleranslarını kütüphaneden alırız"
Kurgusal ama yaygın: deinterleaving toleransları kütüphanedeki parametre
aralıklarından (örneğin "PW 0.9–1.1 µs") kopyalanır; almaçın kendi
belirsizliği hesaba katılmaz. Düşük SNR'da PW 1.15 µs okunan darbeler
kümenin dışında kalır, emiter iki kayda bölünür, PRI histogramı yarıya
iner ve "PRI 2 ms" diye yanlış tanımlanır. Tolerans = kütüphane aralığı ⊕
ölçüm belirsizliği (SNR'a bağlı, {{bolum:25}}); PDW'nin kalite alanı bunun
için var.
:::

:::tuzak Kaybı kaçırmayla karıştırmak
`PDW_DROP_CNT` okunmayan bir sistemde FIFO taşması sırasında kaybolan darbeler
PRI analizinde "emiter darbe atladı" olarak yorumlanır; stagger'lı ya da
taramalı emiter sanılır. Tersine, kayıp sayacı yüksekken her boşluğu
kayba bağlamak da gerçek tarama davranışını gizler. Kural: ayrıştırma
katmanı her PDW penceresiyle birlikte o pencerenin kayıp sayısını alır;
kayıp sıfırsa boşluk emiterin, değilse almaçındır.
:::

:::ozet
- Deinterleaving karışık PDW akışını emiter dizilerine böler: önce RF/PW/AOA ile kümele, sonra küme içinde PRI bul (TOA farkı histogramı; CDIF/SDIF adları), diziyi çıkar, kalanla tekrarla.
- PRI türleri (sabit, stagger, jitter, dwell & switch, sliding) histogramda farklı imzalar bırakır; TOA tekrarlanabilirliği PRI çözünürlüğünü belirler.
- Emiter kaydı yaşayan bir nesnedir: RF, PW, PRI, MOP, AOA, PA(t) → tarama periyodu; AOA(t) → konum. Tanımlama kütüphane eşlemedir ve toleransı ölçüm belirsizliğinden geniş olmalıdır.
- Yazılım üç katmandır: alma (kopyala, SEQ/DROP), ayrıştırma (öngörü ile ucuz eşleme, histogram yeni kayıt için), kayıt/tanımlama; zaman bütçeleri ns → µs → ms.
- Almaçtan gelen bayraklar (SEG, POP, SAT, EXT) ve kayıp sayaçları yazılımın hipotezlerini belirler; kayıp sessiz kalmamalıdır.
- Kılavuz PDW'de durur; devamı Wiley (ELINT) ve Tsui'dedir.
:::

:::kendini-sina
S: Aynı X-bant kümesinde iki emiter var: PRI 1.00 ms ve 0.50 ms. TOA farkı histogramında ne görürsün ve dizi çıkarma sırası neden önemlidir?
C: 0.50 ms'de büyük tepe (ikinci emiterin ardışık farkları + birincinin yarım katları değil — birincinin ardışık farkı 1.00'dır ama 0.50'lik emiterle çapraz farklar da 0.50 civarına düşer), 1.00 ms'de tepe (birinci emiter + ikincinin 2. mertebe farkı). Önce en yüksek tepeden (0.50) dizi çıkarılır; 1.00 ms'lik tepenin ikinci emiterin alt harmoniği olan kısmı böylece kaybolur ve kalan PDW'lerle 1.00 ms'lik gerçek emiter bulunur. Ters sırada çıkarsan 1.00 ms dizisi ikinci emiterin her ikinci darbesini çalar.
S: TOA jitter'ı 6 ns'den 60 ns'ye çıksa (SNR 15 → 5 dB) deinterleaving'de ne değişir?
C: PRI toleransı ~10 kat açılmalıdır; kasıtlı %0.01'lik PRI jitter'ı (100 ns @ 1 ms) artık ölçüm gürültüsünden ayırt edilemez, stagger'ın yakın PRI değerleri birleşir ve yakın PRI'li emiterler karışır. Almaç tarafında çözüm hassasiyet (NF, kazanç) ya da entegrasyon değil — darbe kısa — daha iyi TOA kestirimidir (kesirli %50 TOA).
S: Deinterleaving yazılımı neden her PDW için histogram kurmaz da önce mevcut kayıtlara "öngörüyle" eşler?
C: Histogram O(N²) fark hesabı ister ve pencere başına milisaniyeler sürer; öngörü ise "bir sonraki darbe TOA + PRI ± tolerans'ta beklenir" karşılaştırmasıdır, PDW başına nanosaniyeler. Sabit ortamda PDW'lerin büyük çoğunluğu mevcut kayıtlara düşer; histogram yalnızca eşleşmeyen artıklar için çalışır.
:::

:::kopru
Yolculuk bitti: darbe antene 9.4 GHz'de −60 dBm ile girdi, 128 bitlik bir
kayıt olarak PS tamponuna düştü ve yazılım onu bir emiter kaydına yazdı. Şimdi
geri dönüp bütün zinciri tek bakışta görme zamanı: her durakta sinyal
pasaportu nasıl değişti, seviye/SNR/bit/latency bütçeleri nasıl kapandı,
"fs neden 2400, decimation neden 8, FFT neden 1024" soruları birbirine nasıl
bağlı? Bölüm 28 uçtan uca referans tasarımı tek tabloda ve tek widget'ta
toplar.
:::
