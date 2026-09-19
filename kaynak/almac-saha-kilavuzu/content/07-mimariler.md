# Bölüm 7 — Almaç Mimarileri Kataloğu
::meta onkosul=3,4,5,6 acar=8,10,17,22,27,28 blok=onuc,mixer,if rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "Aynı kartta iki almaç var; biri her darbeyi görüyor ama
frekansı 50 MHz kaba veriyor, öteki 10 kHz doğru ölçüyor ama darbelerin
yarısını kaçırıyor. Neden ikisini birden yapamıyoruz?" Çünkü almaç
mimarisi, birbiriyle çelişen isteklerin (anlık bant, hassasiyet, eşzamanlı
sinyal, frekans doğruluğu, maliyet) arasında bir yerde durmaktır ve her
mimari o çelişkiyi farklı çözer. Yazılımcı için bunun somut karşılığı:
aynı PDW alanının (RF, PA, TOA) anlamı, güvenilirliği ve çözünürlüğü almaçtan
almaca değişir. Bu bölüm on mimariyi aynı sembol diliyle çizer, üç ölçütle
karşılaştırır ve senin zincirinin (sayısal IF) neden bugünün "orta yolu"
olduğunu gösterir.
:::

## Sezgi: geniş ağ mı, derin olta mı

Bir gölde balık arıyorsun. Geniş bir ağ atarsan gölün tamamını bir seferde
tararsın ama küçük balıklar deliklerden kaçar ve iki balık aynı anda
takılınca hangisi hangisi bilemezsin. İnce bir oltayla belli bir noktaya
inersen en küçük balığı bile yakalarsın ama gölün geri kalanında ne olduğunu
görmezsin; gölü noktadan noktaya taraman gerekir ve o sırada başka yerde
zıplayan balığı kaçırırsın.

Almaç mimarileri bu iki uç arasındaki tüm ara çözümlerdir. **Geniş açık
almaçlar** (kristal video, IFM) ağdır: anlık bant geniş, POI yüksek,
hassasiyet ve seçicilik zayıf. **Dar bant taramalı almaçlar** (süperhet)
oltadır: hassas ve seçici, ama POI düşük. **Kanallaştırılmış almaçlar** aynı
anda çok olta atmaktır; pahalıdır. Sayısal teknoloji bu takası kaldırmadı;
oltaların fiyatını düşürdü ve sayısını artırdı. Bugünün sayısal IF ve direct
RF almaçları, "ne kadar geniş bir bandı kaç kanalla dinleyeceğin" sorusunu
donanımdan register'a taşıdı — o yüzden bu bölüm senin bölümün.

:::analoji Radyo kadranı ve tarayıcı
Eski bir radyoda istasyonu bulmak için kadranı çevirirsin: o an yalnızca
bir frekansı duyarsın, ötekilerde konuşulanı kaçırırsın. Bu süperhettir.
"Tarayıcı" (scanner) telsizler kadranı otomatik çevirir: her kanala kısa
süre uğrar; birinin konuştuğu anda oradaysan duyarsın, değilsen kaçırırsın.
Bu POI (probability of intercept — yakalama olasılığı) kavramının ta
kendisidir. Bir radar darbesi 1 µs sürer ve saniyede bin kez gelir;
tarayıcın 100 kanalı 1 ms'de dolaşıyorsa her kanalda 10 µs kalır ve o
darbenin senin kanalındayken gelme olasılığı %1'dir. Geniş açık almaç ise
tüm kanalları aynı anda "duyar" — ama hangi kanaldan geldiğini söyleyemez.
:::

## Kavram: mimarileri ayıran yedi ölçüt

Her mimari kartında aynı yedi çubuk var; anlamlarını önce sabitleyelim.

1. **Anlık bant genişliği:** aynı anda bakılan spektrum dilimi. CVR için
   bütün bant (GHz'ler), süperhet için IF filtresi kadar (MHz'ler).
2. **Hassasiyet:** en zayıf tespit edilebilir sinyal. {{bolum:4}}'ten:
   $−174 + 10 log B + NF + SNR_{gerekli}$; **B ne kadar genişse hassasiyet o
   kadar kötü** — anlık bant ile hassasiyet doğrudan çelişir.
3. **Dinamik aralık:** {{bolum:5}}'teki anlık dinamik aralık; mimarinin en
   zayıf halkasıyla (dedektör, ADC biti, limiter) belirlenir.
4. **Eşzamanlı sinyal başarımı:** iki darbe üst üste gelince ne olur.
   Frekans ayrımı yapamayan mimariler ya karışık tek ölçüm verir (IFM) ya
   ikisini toplar (CVR).
5. **Frekans doğruluğu / çözünürlüğü:** ölçülen RF'in gerçeğe yakınlığı;
   CVR'de yok, IFM'de MHz, sayısalda kHz.
6. **POI:** darbe geldiğinde almacın ona bakıyor olma olasılığı; geniş açık
   ve kanallaştırılmış yapılarda ≈ %100, taramalıda dwell/tarama süresi oranı.
7. **Karmaşıklık / maliyet:** blok sayısı, güç, kalibrasyon yükü, FPGA
   kaynağı. Çubuk uzun = pahalı.

:::formul id=poi baslik="Taramalı almaçta yakalama olasılığı (kaba)"
f: POI ≈ frac{T_{dwell}}{T_{tarama}} = frac{B_{anlık}}{B_{toplam}}   (tek darbe için)
f: POI_N = 1 − (1 − POI)^N   (N darbe sonunda en az bir kez)
s: T_{dwell} | bir frekans penceresinde kalınan süre | s
s: T_{tarama} | tüm bandın taranma süresi | s
s: B_{anlık}, B_{toplam} | anlık ve toplam bant | Hz
s: N | emiterin gönderdiği darbe sayısı (gözlem süresi / PRI) | —
o: 300 MHz'lik anlık bantla 2–18 GHz'i (16 GHz) tarayan bir almaç: POI ≈ 300/16 000 ≈ **%1.9** darbe başına. PRI {{s:sinyal.pri_ms}} ms olan emiter 1 s'de 1000 darbe gönderir: POI₁₀₀₀ = 1 − 0.981^1000 ≈ **1.0** — 1 s içinde neredeyse kesin yakalarsın, ama kaç darbesini? Yaklaşık 19'unu. Tarama, "görmek" ile "her darbeyi görmek" arasındaki farktır.
o: Referans zincir 300 MHz'lik anlık bandı sabit bir IF'te tutar; bandı tarayan LO'dur. Bu yüzden ESM'de bant taraması yerine birden çok kanalı paralel açmak (M-9) tercih edilir.
:::

## Katalog: on mimari

Sıra kabaca tarihsel ve "analog → sayısal" yönündedir. Her kartın blok
şeması {{bolum:5}}'teki sembollerle çizilmiştir; altın analog, mavi sayısal,
yeşil kontrol, gri kesikli LO/saat. Puanlar 0–5, göreli ve kurgusal-
öğreticidir; W-06'da aynı sayılar yan yana getirilir.

:::mimari no=1 ad="Kristal video almaç (CVR) ve TRF" sema=g-70-cvr.svg
::ilke::
RF doğrudan bir kare-yasa dedektöre (kristal diyot) verilir; çıkış, sinyalin
güç zarfıdır ("video"). Logaritmik video yükselteç 60–70 dB'lik giriş
aralığını birkaç voltluk çıkışa sığdırır; eşik darbe var/yok kararı verir.
Frekans dönüşümü yok, LO yok, frekans bilgisi yok. **TRF** (tuned radio
frequency) aynı iskelette ayarlanabilir dar bir RF filtresi kullanır: biraz
seçicilik, hâlâ mixer yok.
::arti::
- En basit, en ucuz, en küçük; birkaç blok.
- Tüm bant aynı anda açık: POI ≈ %100, darbe geldiği anda görünür.
- TOA, PW ve PA ölçümü doğrudan zarftan; hızlı tepki (RWR uyarısı için).
::eksi::
- Hassasiyet düşük: B = GHz'ler → gürültü tabanı yüksek; dedektörün "tangential sensitivity"si tipik −40 … −50 dBm mertebesinde (kurgusal aralık).
- Frekans bilgisi yok (en fazla bant seçici filtrelerle "hangi alt bant").
- Eşzamanlı darbeler toplanır; güçlü CW bütün almacı doldurur.
::kullanim::
Radar uyarı almaçlarının (RWR) omurgası: birkaç anten + birkaç CVR ile
yön ve varlık; frekans için yanına IFM eklenir. Bugün de üretilir; ucuzluğu
ve POI'si yerini korur.
::ozellik::
Anlık BW: 5
Hassasiyet: 1
Dinamik aralık: 2
Eşzamanlı sinyal: 0
Frekans doğruluğu: 0
POI: 5
Karmaşıklık: 0
:::

:::mimari no=2 ad="Süperheterodin (dar bant, taramalı; tek/çift dönüşüm)" sema=g-71-superheterodin.svg
::ilke::
{{bolum:6}}'nın mimarisi: ayarlı preselector, LNA, mixer ve sabit IF; dar
IF filtresi kanalı seçer, IF yükselteci kazancı verir, dedektör zarfı çıkarır.
Bandı taramak için LO süpürülür ya da adım adım atlatılır. Çift dönüşümde
yüksek IF₁ image'ı uzağa atar, düşük IF₂ dar filtreyi kolaylaştırır.
::arti::
- En iyi hassasiyet ve seçicilik: dar B, temiz gürültü tabanı, komşu kanal bastırma.
- Geniş ve temiz dinamik aralık (IF'te kazanç kontrolü kolay).
- Frekans doğruluğu LO kadar iyi (sentezleyici + IF filtre merkezi).
::eksi::
- POI düşük: anlık bant dar, tarama gerekir; kısa süreli ve düşük PRF'li emiterleri kaçırır.
- Image ve spur yönetimi (preselector takibi, frekans planı tablosu).
- Eşzamanlı sinyal yalnızca IF bandı içinde ve orada da ayrım yok (analog dedektör toplar).
::kullanim::
Yüksek hassasiyet isteyen ELINT ve "doğrulama" almaçları; geniş açık bir
almacın (CVR/IFM) bulduğu emitere "derin bakış". Radarın kendi almacı da
süperhettir ama taramaz: hedef frekansı bellidir.
::ozellik::
Anlık BW: 1
Hassasiyet: 5
Dinamik aralık: 4
Eşzamanlı sinyal: 1
Frekans doğruluğu: 4
POI: 1
Karmaşıklık: 2
:::

:::mimari no=3 ad="Zero-IF / homodyne / direct conversion" sema=g-72-zero-if.svg
::ilke::
LO tam RF'e konur; IF sıfırdır, mixer çıkışı doğrudan baseband'dir. Tek
mixer'la pozitif ve negatif frekanslar üst üste bineceğinden (image = sinyalin
kendisi) iki mixer 0° ve 90° LO ile sürülür ve I/Q çifti üretilir
({{bolum:2}}); her kol alçak geçiren filtreden ve düşük hızlı bir ADC'den geçer.
::arti::
- IF filtresi, IF yükselteci yok; image filtresi yok → tek çipe sığar, ucuz ve küçük.
- ADC hızı yalnızca sinyal bandı kadar (I ve Q ayrı ayrı B/2).
- Kanal seçimi baseband'de (analog LPF + sayısal filtre), esnek.
::eksi::
- **DC ofset:** LO kendi mixer'ına sızar ve kendisiyle çarpılır → baseband'de sıfır frekansta sabit bileşen; güçlü sinyalde zamanla değişir.
- **I/Q dengesizliği:** genlik/faz hatası, sinyalin frekans eksenine göre aynadaki kopyasını ("iç image") üretir; 0.5 dB / 5° → ~25–30 dB image reddi ({{bolum:2}}).
- 1/f gürültüsü ve IMD2 ($f_1 − f_2$) tam sinyalin üstüne, baseband'e düşer; LO sızıntısı antene çıkar.
::kullanim::
Ticari haberleşme alıcılarının standardı; EH'de sayısal I/Q düzeltme
(kalibrasyon) ile geniş bantlı, küçük hacimli almaçlarda ve bazı RFSoC
yardımcı yollarında görülür. Referans zincirin sayısal DDC'si aslında bir
"sayısal zero-IF"tir: aynı iş, dengesizlik problemi olmadan.
::ozellik::
Anlık BW: 3
Hassasiyet: 3
Dinamik aralık: 3
Eşzamanlı sinyal: 2
Frekans doğruluğu: 3
POI: 3
Karmaşıklık: 2
:::

:::mimari no=4 ad="IFM — anlık frekans ölçer" sema=g-73-ifm.svg
::ilke::
Sinyal limiter'la sabit genliğe getirilir, ikiye bölünür; bir kol
$τ$ kadar geciktirilir. İki kol bir faz korelatöründe çarpılır: çıkış
$cos(2π f τ)$ ve $sin(2π f τ)$ (I/Q). Faz farkı frekansla orantılıdır;
$f = φ / (2π τ)$. Tek bir darbe içinde, onlarca ns'de frekans okunur.
::arti::
- Geniş açık: tüm bant aynı anda, POI ≈ %100.
- Tek darbeden frekans; yanıt süresi çok kısa (limiter + korelatör + tablo).
- Basit, ucuz, küçük; CVR ile birlikte RWR'nin klasik ikilisi.
::eksi::
- Eşzamanlı iki sinyalde tek ve **yanlış** bir frekans (güçlü olan kazanır, zayıf "çeker").
- Genlik bilgisi limiter'da kaybolur (PA için ayrı CVR kanalı gerekir).
- Belirsizlik aralığı $1/τ$: kaba/ince birkaç korelatör ve çözümleme mantığı gerekir; hassasiyet B ile sınırlı.
::kullanim::
RWR ve hızlı ESM ön ucu; yüksek darbe yoğunluğunda ilk kaba frekans etiketi.
Sayısal ikizi, DDC çıkışında ardışık örneklerin faz farkından anlık frekans
hesabıdır ({{bolum:25}}); aynı güçlü ve zayıf yanları taşır.
::ozellik::
Anlık BW: 5
Hassasiyet: 2
Dinamik aralık: 3
Eşzamanlı sinyal: 0
Frekans doğruluğu: 4
POI: 5
Karmaşıklık: 2
:::

:::formul id=ifm baslik="IFM: faz farkından frekans"
f: φ = 2π · f · τ      f = frac{φ}{2π τ}      f_{belirsiz} = frac{1}{τ}
s: φ | gecikmeli ve gecikmesiz kol arasındaki faz farkı | rad
s: τ | gecikme hattı süresi | s
s: f_{belirsiz} | φ'nin 2π'yi sarmadan kapsadığı frekans aralığı | Hz
o: τ = 5 ns → belirsizlik aralığı 200 MHz; 9.4 GHz'i tek başına çözemez. τ = 0.0625 ns'lik kaba bir hat 16 GHz'i kapsar ama çözünürlüğü kabadır; kaba → ince zincir (0.0625, 0.5, 4, 32 ns gibi) hem aralığı hem çözünürlüğü verir. Aynı "kaba-ince" fikri Bölüm 25'teki sayısal frekans ölçümünde tekrar karşına çıkar.
:::

:::mimari no=5 ad="Analog kanallaştırılmış almaç (filtre bankası)" sema=g-74-analog-kanallastirilmis.svg
::ilke::
Bant, bir güç bölücüyle N kola ayrılır; her kolda bitişik bir bant geçiren
filtre, dedektör, video yükselteç ve eşik vardır — her kanal küçük bir CVR.
Bir kodlayıcı hangi kanal(lar)ın tetiklendiğini frekans etiketine çevirir.
Süperhetle birleştirilip IF'te kanallaştırma da yapılır.
::arti::
- Tüm kanallar aynı anda açık: POI ≈ %100, eşzamanlı sinyaller farklı kanallardaysa ayrılır.
- Hassasiyet kanal bandına göre (N kat dar → 10·log N dB kazanç CVR'ye göre).
- Dinamik aralık kanal başına iyi; güçlü sinyal yalnızca kendi kanalını doldurur.
::eksi::
- N filtre + N dedektör: hacim, güç, maliyet N ile büyür; filtrelerin birbirine uydurulması (kalibrasyon) zordur.
- Kanal kenarındaki sinyal iki kanalda birden görünür ("rabbit ears"); frekans çözünürlüğü kanal genişliğiyle sınırlı.
- Kanal içinde iki sinyal yine ayrılamaz.
::kullanim::
1970–90'ların yüksek performanslı ESM almaçları; bugün büyük ölçüde sayısal
kanallaştırıcıya (M-9) bıraktı, ama çok geniş bant ilk kademe bölmede
(bant seçimi) hâlâ karşına çıkar.
::ozellik::
Anlık BW: 5
Hassasiyet: 3
Dinamik aralık: 3
Eşzamanlı sinyal: 4
Frekans doğruluğu: 2
POI: 5
Karmaşıklık: 4
:::

:::mimari no=6 ad="Compressive (microscan) almaç ve akusto-optik — kısa tarih" sema=g-75-compressive.svg
::ilke::
Süperhetin LO'su darbe süresinden çok hızlı süpürülür (microscan); her
giriş frekansı IF'te bir chirp'e dönüşür. Dispersif bir gecikme hattı (SAW
chirp filtresi) bu chirp'i sıkıştırıp dar bir darbe yapar: darbenin **zaman
konumu** giriş frekansını verir. Yani analog bir Fourier dönüşümü. Akusto-
optik (Bragg cell) almaçta ise RF bir kristalde ses dalgasına çevrilir, lazer
bu "kırınım ağı"ndan frekansa orantılı açıyla sapar ve bir fotodedektör dizisi
üstüne düşer: her piksel bir frekans kanalı.
::arti::
- Geniş anlık bant ile yüksek frekans çözünürlüğünü tek kanalda birleştirir.
- Eşzamanlı sinyalleri ayırır (zaman ya da açı ekseninde ayrı tepeler).
- Kanallaştırıcının N kolu yerine tek bir dispersif hat.
::eksi::
- Dinamik aralık sınırlı (SAW hattı ve dedektörler; akusto-optikte ~30–40 dB, doğrulanmadı).
- Darbe süresi tarama süresinden kısaysa sinyal tam süpürülmez (kısa darbe zaafı); tarama tekrar oranı POI'yi sınırlar.
- Kalibrasyon ve sıcaklık kararlılığı güç; sayısal FFT ile aynı işi daha iyi yapmak mümkün hale gelince terk edildi.
::kullanim::
Tarihî ilgi: 1970–80'lerde geniş bant + çok sinyal problemi için analog
çözümler. Bugün ikisinin de işlevi M-9'un içindeki FFT'dir; kavramsal mirası
("frekansı zamana ya da uzaya haritalamak") pulse compression'da yaşar.
::ozellik::
Anlık BW: 4
Hassasiyet: 3
Dinamik aralık: 2
Eşzamanlı sinyal: 4
Frekans doğruluğu: 3
POI: 4
Karmaşıklık: 4
:::

:::mimari no=7 ad="Sayısal IF almaç (digital IF) — referans zincir" sema=g-76-sayisal-if.svg
::ilke::
Süperhet ön uç sinyali sabit ve görece yüksek bir IF'e indirir; hızlı bir
ADC IF'i doğrudan (genellikle 2. Nyquist bölgesinden, {{bolum:8}})
örnekler; kanal seçimi, baseband'e iniş, zarf, tespit ve ölçüm tamamen
FPGA'da yapılır (NCO + kompleks mixer + FIR/CIC + decimation, Kısım V).
Analog–sayısal sınır IF'tedir.
::arti::
- IF filtresi geniş tutulur (300 MHz), seçicilik sayısal → filtre şekli tekrarlanabilir, yeniden yapılandırılabilir.
- Aynı IF örneğinden birden çok NCO ile birden çok kanal; anında yeniden ayar (register).
- Frekans doğruluğu NCO/FFT sınıfında (kHz); dinamik aralık ADC'nin (14 bit, ~70–75 dB SFDR).
::eksi::
- Analog ön uç ve frekans planı hâlâ var (image, spur, LO faz gürültüsü).
- Anlık bant ADC'nin Nyquist bölgesiyle sınırlı (1.2 GHz); bantı taramak için LO gerekir.
- Veri hızı yüksek (33.6 Gbps), FPGA arayüzü ve saat dağıtımı kritik ({{bolum:11}}).
::kullanim::
Bugünün ESM/ELINT ve radar almaçlarının en yaygın biçimi; bu kılavuzun
referans zinciri. Analog ve sayısalın "makul" paylaşımı: analog seçicilik
ve kazanç, sayısal her şey.
::ozellik::
Anlık BW: 3
Hassasiyet: 4
Dinamik aralık: 4
Eşzamanlı sinyal: 3
Frekans doğruluğu: 5
POI: 3
Karmaşıklık: 3
:::

:::mimari no=8 ad="Direct RF sampling almaç" sema=g-77-direct-rf.svg
::ilke::
Mixer ve IF katı yoktur: LNA'dan (ve Nyquist bandı seçici bir filtreden)
sonra RF doğrudan çok GSPS'lik bir ADC'ye girer; 9.4 GHz gibi bir sinyal
yüksek bir Nyquist bölgesinden (undersampling) örneklenir ya da ADC'nin
ilk bölgesi yeterince genişse doğrudan. Frekans dönüşümü NCO ile sayısaldır.
Analog–sayısal sınır LNA'nın hemen arkasındadır.
::arti::
- Image yok, LO sızıntısı yok, analog frekans planı yok; LO faz gürültüsünün yerini saat jitter'ı alır — tek bir temiz saat.
- Aynı ADC'den bütün bant: çok kanal, anında yeniden ayar, tamamen yazılım tanımlı bant planı.
- Blok sayısı en az; RFSoC sınıfı çiplerle tek yonga.
::eksi::
- ADC'nin dinamik aralığı **tüm bantla paylaşılır**: bant içindeki en güçlü sinyal ADC'yi doyurursa herkes kaybeder (analog seçicilik yalnızca Nyquist filtresi kadar).
- Frekans planı kaybolmaz, ADC'ye taşınır: harmonikler, interleaving spur'ları, bölge katlanmaları ({{bolum:8}}, {{bolum:10}}).
- Jitter: 9.4 GHz'te 100 fs jitter SNR'ı ~44 dB'ye sınırlar ({{bolum:9}}); saat dağıtımı en kritik analog problem olur. Yüksek frekansta ADC giriş bandı, NF ve güç tüketimi.
::kullanim::
Yeni nesil geniş bantlı ESM, çok kanallı yön bulma, faz dizili radar
almaçları (eleman başına ADC). Referans zincirle farkı: mixer/IF yok;
bu kılavuzda {{bolum:10}} tümüyle ona ayrılmıştır.
::ozellik::
Anlık BW: 4
Hassasiyet: 3
Dinamik aralık: 3
Eşzamanlı sinyal: 4
Frekans doğruluğu: 5
POI: 4
Karmaşıklık: 3
:::

:::mimari no=9 ad="Sayısal kanallaştırılmış almaç (polyphase / FFT filtre bankası)" sema=g-78-sayisal-kanallastirilmis.svg
::ilke::
Geniş bant ADC (IF'te ya da RF'te) örneklerini bir polyphase FIR bankası ve
M noktalı FFT, M eşit kanala böler; her FFT çıkışı, kendi decimation
oranında örneklenmiş bir kanal akışıdır. Her kanalda zarf, CFAR ve ölçüm
bağımsız çalışır. M-5'in sayısal ikizi; polyphase yapı, düz FFT'nin yaprak
sızıntısını ve kanal kenarı sorununu FIR prototipiyle düzeltir ({{bolum:17}},
{{bolum:18}}).
::arti::
- M kanal bir kez tasarlanır, hepsi bit bit özdeştir (analogda imkânsız); kanal şekli, örtüşme ve geçiş bandı yazılımla değişir.
- Geniş anlık bant + kanal başına dar bant hassasiyeti + POI ≈ %100 + eşzamanlı sinyal M'ye kadar.
- Frekans doğruluğu kanal içi interpolasyon ile kHz sınıfı.
::eksi::
- En yüksek FPGA yükü: M × FIR fazı, FFT, M kanal tespit zinciri; bellek ve DSP slice bütçesi.
- Kanal sınırındaki darbe komşu kanallarda birden görünür; "aynı darbe mi" kararı için kanal-arası mantık gerekir (yazılıma yansır).
- Kanal geçiş süreleri, decimation nedeniyle zaman çözünürlüğü kaybı; geniş bantlı LFM birden çok kanalı sırayla dolaşır.
::kullanim::
Yüksek darbe yoğunluklu ortamda çalışan modern ESM; geniş bantlı radar
almaçlarında alt bant işleme. Referans zincirin tek kanallı DDC'si bunun
M = 1 halidir; kılavuzun {{bolum:17}}'si kanallaştırmayı açar.
::ozellik::
Anlık BW: 5
Hassasiyet: 4
Dinamik aralık: 4
Eşzamanlı sinyal: 5
Frekans doğruluğu: 5
POI: 5
Karmaşıklık: 5
:::

:::mimari no=10 ad="Monobit almaç (kavram düzeyi)" sema=g-79-monobit.svg
::ilke::
Giriş limiter'dan geçirilir ve yalnızca **işareti** çok yüksek hızda
örneklenir (1 bit). Ardından bir FFT alınır; ama twiddle çarpanları da
±1, ±j'ye yuvarlandığı için hiç çarpma yoktur — yalnızca toplama. Sonuç,
çok küçük mantıkla çok geniş bantta kaba frekans ölçümüdür: IFM'in FFT
tabanlı akrabası.
::arti::
- En küçük mantık, en yüksek örnekleme hızı; ucuz ve az güç.
- Tek sinyalde frekans doğruluğu şaşırtıcı iyi (FFT bin'i kadar), tek darbede.
- Geniş açık, POI ≈ %100.
::eksi::
- Dinamik aralık çok düşük (~20 dB anlık, doğrulanmadı): güçlü sinyal zayıfı tamamen yutar; eşzamanlı sinyalde güçlü olan kazanır.
- Genlik bilgisi yok; kuantizasyon spur'ları yüksek (1 bit).
- Zayıf sinyalde SNR kaybı (~2 dB kuantizasyon kaybı ideal, pratikte fazlası).
::kullanim::
Araştırma ve düşük maliyetli geniş bant frekans etiketleme; kavramsal
önemi, "bit sayısı ↔ bant genişliği" takasının en uç noktasını göstermesidir.
Çok bitli sayısal kanallaştırıcı ile 1 bitlik monobit aynı eksenin iki ucudur.
::ozellik::
Anlık BW: 5
Hassasiyet: 2
Dinamik aralık: 1
Eşzamanlı sinyal: 1
Frekans doğruluğu: 4
POI: 5
Karmaşıklık: 1
:::

:::widget id=w06 ad="Mimari karşılaştırıcı"
- **Referans senaryo** preset'i sayısal IF (M-7) ile direct RF (M-8) yan yana: yedi çubuktan beşi eşit ya da bir puan farklı; farkın "anlık BW" (3 → 4) ve karmaşıklığın *türünde* (mixer/IF yerine saat/jitter) olduğunu blok listesinden gör.
- Öncelik seçicisini **hassasiyet** yap: öneri sıralamasında süperhet (M-2) başa çıkar, CVR (M-1) sona düşer. Şimdi **POI / anlık BW** yap: sıralama neredeyse tersine döner — aynı tablo, farklı ağırlık.
- **RWR: POI + maliyet** preset'i CVR (M-1) ile IFM'i (M-4) karşılaştırır; ikisinin de "eşzamanlı sinyal" çubuğu sıfırdır. Bu ikilinin RWR'de neden hep birlikte kullanıldığını çubuklardan oku: biri genlik/zaman, öteki frekans.
- Sayısal kanallaştırılmış (M-9) ile monobit'i (M-10) seç: anlık BW ve POI'de eşit (5/5), dinamik aralıkta 4'e karşı 1. Bu fark tam olarak ADC bit sayısıdır.
:::

{{svg:g-7a-evrim-haritasi.svg|Mimarilerin evrim haritası (on yıllar yaklaşıktır). Dört soy: zarf (CVR), anlık frekans (IFM → monobit), süperhet (→ zero-IF, → sayısal IF → direct RF) ve kanallaştırma (analog filtre bankası ve compressive/akusto-optik → sayısal kanallaştırılmış). 1990 sonrası hızlı ADC + FPGA çağı: sayısal çekirdekli mimariler (mavi) analog olanları (altın) tek tek devralır.}}

{{svg:g-7b-analog-sayisal-sinir.svg|"Analog–sayısal sınır nereye kaydı" şeridi. Aynı sekiz durak beş mimari için: CVR ve klasik süperhette ADC zarftan sonra (video), sayısal IF'te IF'te, direct RF ve sayısal kanallaştırılmışta LNA'nın hemen arkasında. Sınır sola kaydıkça analog problem (filtre, mixer, dedektör) DSP problemine dönüşür — bu kılavuzun Kısım III–VIII'inin konusu tam da o problemlerdir.}}

## Kavram: radar almacına özgü notlar

Radar almacı ile EH almacı aynı yapıtaşlarını kullanır ama üç yerde
ayrılır. Birincisi **koherenttir**: radar kendi gönderdiği darbenin
fazını bilir ve ekonun fazını onunla karşılaştırır. Bunun için verici ve
alıcı aynı referanstan türetilir: **STALO** (stable local oscillator — kararlı
yerel osilatör) RF↔IF dönüşümünü, **COHO** (coherent oscillator) IF↔baseband
dönüşümünü yapar ve darbeden darbeye fazı korur. Faz korunduğu için ardışık
ekolardan Doppler (hız) çıkarılabilir; EH almacında böyle bir referans
yoktur, bu yüzden EH'de "faz" yalnızca aynı darbe içinde (LFM eğimi, faz
kodu) ya da kanallar arasında (yön bulma) anlamlıdır.

İkincisi **eşlenik filtredir** (matched filter): radar, gönderdiği dalga
şeklini bildiğinden alıcıda o dalga şeklinin zaman-tersine çevrilmiş
eşleniğiyle korelasyon alır; SNR'ı $2E/N_0$ ile en iyileyen filtre budur ve
LFM darbelerde **darbe sıkıştırması** (pulse compression) olarak karşına
çıkar: 10 µs'lik 10 MHz'lik chirp, 0.1 µs'lik bir tepeye sıkışır ve menzil
çözünürlüğü 100 kat iyileşir. EH almacı dalga şeklini bilmez; onun "eşlenik
filtresi" olsa olsa darbe genişliğine uydurulmuş bir video filtresidir
({{bolum:22}}). Bu tek fark, aynı SNR'da radarın EH'den neden çok daha
zayıf sinyalle çalışabildiğini açıklar.

Üçüncüsü **monopulse kanallarıdır**: yön ölçmek için radar anteni tek
darbede iki (ya da dört) huzme örneği alır — toplam (Σ) ve fark (Δ)
kanalları — ve Δ/Σ oranı hedefin huzme merkezinden açısal sapmasını verir.
Almaç bu yüzden iki ya da üç **eşleşmiş** kanaldır: aynı kazanç, aynı faz,
aynı gecikme; kalibrasyon almacın parçasıdır. EH tarafında karşılığı,
genlik karşılaştırmalı (birden çok CVR) ya da faz karşılaştırmalı
(interferometre) yön bulmadır ({{bolum:25}}); orada da kanal eşleşmesi
ölçümün sınırıdır.

## Kavram: EH bağlamı — RWR, ESM, ELINT öncelikleri

Aynı mimari kataloğundan üç farklı EH almacı çıkar; fark **öncelik
sırasındadır.**

{{tablo: genis}}
| Almaç | Birinci öncelik | İkinci | Feda edilen | Tipik mimari seçimi |
|---|---|---|---|---|
| **RWR** (radar warning receiver) | POI ve tepki süresi (ms içinde uyarı) | Kaba yön ve kaba frekans, yüksek darbe yoğunluğuna dayanma | Hassasiyet (yakın tehdit zaten güçlü), frekans doğruluğu | CVR (birden çok anten) + IFM; giderek sayısal geniş açık ön uçlar |
| **ESM** (electronic support measures) | Geniş bant durumsal farkındalık: çok emiteri aynı anda ayırma, güvenilir PDW | Hassasiyet (menzil), frekans/PW/PRI doğruluğu (emiter tanıma) | Anlık bant ile hassasiyet arasında sürekli pazarlık | Sayısal IF, sayısal kanallaştırılmış, direct RF; kanal sayısı ile POI alınır |
| **ELINT** (electronic intelligence) | Hassasiyet ve ölçüm doğruluğu (darbe içi modülasyon, kHz frekans, ns TOA) | Uzun kayıt, sonradan analiz; dinamik aralık | POI (emiter biliniyor, ona bakılır), tepki süresi | Süperhet + sayısal IF, geniş dinamik aralıklı ADC; yüksek çözünürlüklü kayıt |

Yazılımcı için sonuç: **PDW alanlarının anlamı almaca göre değişir.** RWR'nin
"RF" alanı 25 MHz'lik bir IFM bölmesi olabilir; ESM'ninki 100 kHz'lik bir
kanal içi interpolasyon; ELINT'inki 1 kHz'lik uzun FFT ölçümü. Aynı alan adı,
üç farklı güven aralığı. PDW formatına bir "çözünürlük/güven" alanı koymak
({{bolum:24}}) bu yüzden lükstür değil, gerekliliktir.

## Karşılaştırma tablosu

Puanlar kartlardaki çubuklarla aynıdır (0 en düşük, 5 en yüksek; karmaşıklıkta
5 en pahalı). Göreli ve öğreticidir; belirli bir ürünü temsil etmez.

{{tablo: genis}}
| # | Mimari | Anlık BW | Hassasiyet | Dinamik aralık | Eşzamanlı sinyal | Frekans doğruluğu | POI | Karmaşıklık / maliyet |
|---|---|---|---|---|---|---|---|---|
| 1 | CVR / TRF | 5 | 1 | 2 | 0 | 0 | 5 | 0 |
| 2 | Süperheterodin (taramalı) | 1 | 5 | 4 | 1 | 4 | 1 | 2 |
| 3 | Zero-IF / homodyne | 3 | 3 | 3 | 2 | 3 | 3 | 2 |
| 4 | IFM | 5 | 2 | 3 | 0 | 4 | 5 | 2 |
| 5 | Analog kanallaştırılmış | 5 | 3 | 3 | 4 | 2 | 5 | 4 |
| 6 | Compressive / akusto-optik | 4 | 3 | 2 | 4 | 3 | 4 | 4 |
| 7 | **Sayısal IF (referans)** | 3 | 4 | 4 | 3 | 5 | 3 | 3 |
| 8 | Direct RF sampling | 4 | 3 | 3 | 4 | 5 | 4 | 3 |
| 9 | Sayısal kanallaştırılmış | 5 | 4 | 4 | 5 | 5 | 5 | 5 |
| 10 | Monobit | 5 | 2 | 1 | 1 | 4 | 5 | 1 |

Tabloyu okumanın yolu satır satır değil sütun sütun: "anlık BW" ve
"hassasiyet" sütunları neredeyse birbirinin tersidir (fizik: $10 log B$);
"eşzamanlı sinyal" sütunu kanallaştırmayla, "frekans doğruluğu" sayısal
işlemeyle birlikte yükselir; "karmaşıklık" ise ikisinin toplamı gibi davranır.
Sayısal IF'in her sütunda 3–5 alması onun hiçbir şeyde en iyi, hiçbir şeyde
kötü olmayan "orta yol" konumunu gösterir — referans zincir bu yüzden odur.

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Mimari seçimi RF gözüyle bir **filtreleme ve kazanç dağıtımı** kararıdır:
seçiciliği analogda mı (preselector, IF filtre, filtre bankası) yoksa
sayısalda mı (DDC, kanallaştırıcı) yapacaksın? Analog seçicilik ADC'yi
güçlü bant dışı sinyallerden korur ve dinamik aralığı kanal başına verir;
sayısal seçicilik esneklik ve tekrarlanabilirlik verir ama ADC'nin dinamik
aralığını bütün bantla paylaştırır. Direct RF'te bu pazarlık tek bir Nyquist
filtresine ve saat jitter'ına indirgenir; RF tasarımcısının işi azalmaz,
yer değiştirir: LO yerine saat, image yerine bölge katlanması.
::fpga::
FPGA gözüyle mimari, **kanal sayısı × örnek hızı × bit** çarpımıdır.
Sayısal IF: 1 kanal × 2.4 GSPS × 14 bit girer, bir DDC ile 300 MSPS I/Q'ya
iner; kaynak birkaç bin LUT, birkaç on DSP slice ({{bolum:15}},
{{bolum:16}}). Sayısal kanallaştırılmış: aynı giriş, M = 8–64 kanal;
polyphase FIR + FFT + M tespit zinciri, kaynak M ile neredeyse doğrusal
büyür ve SSR mimarisi ({{bolum:12}}) kaçınılmazdır. Direct RF: giriş hızı
5–10 GSPS'ye çıkar, JESD204 hattı ve saat ağı tasarımın merkezine oturur
({{bolum:11}}). Monobit: neredeyse hiç kaynak. Mimari, FPGA'da "kaç DSP
slice" sorusundan önce "kaç paralel örnek yolu" sorusudur.
::yazilim::
Yazılımcı gözüyle her mimari farklı bir **register yüzeyi ve farklı bir
PDW anlamı** getirir. Süperhet/sayısal IF: LO tablosu, tarama listesi, dwell
süresi; PDW'de RF = LO ± IF. Kanallaştırılmış: kanal başına eşik/CFAR
register'ı, kanal-arası birleştirme kuralı (aynı darbe komşu kanallarda);
PDW'de "kanal no + kanal içi ofset". Direct RF: Nyquist bölgesi ve NCO
tablosu; RF = katlama düzeltmesi + NCO. IFM/CVR: neredeyse register yok,
ama PDW'nin RF alanı kaba ve eşzamanlı darbede güvenilmez. Aynı sürücü
API'sini iki mimaride kullanmak istiyorsan, "bu PDW'nin RF'i ne kadar
güvenilir" bilgisini PDW'nin içine koy.
:::

## Yazılımcıya dokunan yer

Mimari seçimi yazılımın kontrolünde değildir; ama yazılım mimarinin
sınırlarını **bilmek** zorundadır. Somut olarak üç şey değişir:

**1. RF alanının türetilme zinciri.** Sayısal IF'te $f_{RF} = f_{LO} +
f_{IF}$, $f_{IF}$ ise ADC katlaması + NCO + baseband ölçümünden gelir
({{bolum:6}}, {{bolum:8}}, {{bolum:25}}). Direct RF'te LO terimi yoktur ama
Nyquist bölgesi terimi vardır. Kanallaştırılmışta kanal numarası × kanal
aralığı + kanal içi ofset. Her mimarinin kendi `rf_hesapla()` fonksiyonu
vardır ve hepsi aynı imzayı taşımalıdır ki PDW tüketicisi farkı görmesin.

**2. Eşzamanlılık bayrağı.** IFM ve monobit gibi tek ölçüm veren yapılarda
iki darbe üst üste binerse ölçüm bozuktur; donanım genellikle bir "çakışma"
biti verir (IFM'de genlik/faz tutarsızlığı, sayısalda aynı anda iki kanal).
O biti PDW'ye taşımayan yazılım, deinterleaving'e ({{bolum:27}}) zehirli
PDW gönderir.

**3. Tarama ve dwell yönetimi.** Taramalı mimaride (süperhet, ya da LO ile
bant değiştiren sayısal IF) hangi anda hangi banda bakıldığı yazılımın
tuttuğu bir zaman çizelgesidir; PDW'nin TOA'sı ile o çizelge birleştirilmeden
"bu emiter neden 100 ms göründü sonra kayboldu" sorusuna cevap verilemez.
Görünmemesi emiterin sustuğu anlamına gelmez, senin başka yere baktığın
anlamına gelir.

```c
/* Kurgusal, öğretici: mimariye göre RF türetme — tek imza, farklı gövde */
typedef enum { MIM_SAYISAL_IF, MIM_DIRECT_RF, MIM_KANALLASTIRILMIS } mimari_t;

typedef struct {
    mimari_t tip;
    uint64_t lo_hz;          /* sayısal IF: LO; direct RF: 0 */
    uint8_t  high_side;      /* sayısal IF */
    uint32_t fs_hz;          /* ADC örnekleme hızı */
    uint8_t  nyquist_bolge;  /* IF/RF'in düştüğü bölge (1, 2, ...) */
    int64_t  nco_hz;         /* DDC NCO (işaretli) */
    uint32_t kanal_aralik_hz;/* kanallaştırılmış: kanal genişliği */
} almac_cfg_t;

/* olcum_hz: FPGA'nın verdiği baseband ofseti (±B/2) ya da kanal içi ofset.
 * kanal   : kanallaştırılmışta kanal numarası, ötekilerde 0.
 * Bölge katlamasının açılması Bölüm 8'de; burada yalnızca iskelet. */
static uint64_t rf_hesapla(const almac_cfg_t *c, int32_t olcum_hz, uint16_t kanal)
{
    int64_t if_hz;
    switch (c->tip) {
    case MIM_SAYISAL_IF:
        if_hz = bolge_ac(c->fs_hz, c->nyquist_bolge, c->nco_hz + olcum_hz);
        return c->high_side ? c->lo_hz - if_hz : c->lo_hz + if_hz;
    case MIM_DIRECT_RF:
        return (uint64_t)bolge_ac(c->fs_hz, c->nyquist_bolge, c->nco_hz + olcum_hz);
    case MIM_KANALLASTIRILMIS:
        return (uint64_t)kanal * c->kanal_aralik_hz + (int64_t)olcum_hz + rf_taban(c);
    }
    return 0;
}
```

`bolge_ac()` ve `rf_taban()` bu bölümde yazılmaz; ilki {{bolum:8}}'in,
ikincisi {{bolum:17}}'nin konusudur. Buradaki nokta yapısaldır: **mimari,
PDW üreticisinin içinde bir `switch`tir**, tüketicisinde değil.

:::saha-notu "Hangi almaçtayım" testi
Elinde belgesi olmayan bir kartın mimarisini üç ölçümle anlarsın. (1) Bilinen
bir CW ton ver, register'lara dokunmadan frekansı 500 MHz kaydır: hâlâ
görüyorsan geniş açık ya da geniş kanallaştırılmış (anlık bant geniş);
kaybolduysa taramalı/dar bant. (2) İki ton aynı anda ver: iki ayrı PDW
geliyorsa kanallaştırılmış ya da FFT tabanlı; tek ve frekansı ikisinin
arasında kayan bir PDW geliyorsa IFM sınıfı. (3) Tonu 40 dB zayıflat: hâlâ
görüyorsan hassas (süperhet/sayısal IF); kaybolduysa CVR/monobit sınıfı.
:::

:::tuzak "Direct RF'e geçince frekans planı problemi bitti"
Mixer gidince image ve LO sızıntısı gider; ama ADC harmonikleri, interleaving
spur'ları ve Nyquist bölgesi katlanması ({{bolum:8}}) tam olarak "frekans
planı" problemidir, yalnızca adı değişmiştir. Üstelik analog seçicilik
kalmadığı için bant içindeki en güçlü sinyal ADC'nin tüm dinamik aralığını
tüketir: 9.4 GHz'deki −68 dBm'lik darbeyi ararken 6 GHz'deki −20 dBm'lik bir
verici ADC'yi doyurur ve sen hiçbir şey görmezsin — sayısal IF'te preselector
onu 60 dB bastırırdı. Belirti: "almaç bazen kör oluyor", zarfta görünür bir
şey yok. Kontrol: ADC kırpma sayacı ve tam bant FFT; çözüm Nyquist filtresini
daraltmak ya da bant seçici bir ön filtre bankası eklemek — yani M-5'in bir
parçasını geri getirmek.
:::

:::tuzak Kanallaştırılmış almaçta aynı darbe üç PDW üretir
Kanal sınırına düşen bir darbe (ya da geniş bantlı bir LFM) iki-üç komşu
kanalda birden eşiği aşar; her kanalın kendi CFAR'ı bağımsız çalıştığı
için üç PDW çıkar: aynı TOA, aynı PW, birer kanal arayla RF. Deinterleaving
bunları üç emiter sanır ya da PRI'ı üçe böler. Çözüm donanımda (kanal-arası
"aynı darbe" birleştirici, {{bolum:17}}) ya da yazılımda (TOA ± birkaç
örnek ve komşu kanal → birleştir, en güçlü kanalı RF olarak al, genişliği
"BW" alanına yaz). Yazılımın bunu bilmediği kurulumlarda emiter sayısı üç
katına çıkar ve kimse RF'i suçlamaz.
:::

:::tuzak Taramalı almaçta "emiter kayboldu" alarmı
Süperhet ya da LO ile bant değiştiren sayısal IF, bir anda yalnızca bir
pencereye bakar. Emiterin PDW akışı kesildiğinde ilk soru "emiter sustu mu"
değil "biz başka yere mi baktık" olmalıdır. Kurgusal ama tipik: takip
yazılımı 200 ms PDW gelmeyince emiteri "kayıp" ilan eder; oysa tarama
çizelgesinde o bant 250 ms'de bir ziyaret edilmektedir. Çözüm: takip
mantığına tarama çizelgesini (hangi bant, ne zaman, ne kadar) girdi olarak
vermek; "kayıp" sayacını yalnızca o banda bakılan sürede ilerletmek.
:::

:::ozet
- Mimariler, çelişen istekler (anlık BW ↔ hassasiyet, eşzamanlı sinyal ↔ maliyet, POI ↔ seçicilik) arasında farklı noktalardır; hiçbiri her sütunda en iyi değildir.
- Geniş açık (CVR, IFM): POI ≈ %100, ucuz, hassasiyet ve eşzamanlı sinyal zayıf; RWR'nin omurgası. Taramalı süperhet: en hassas ve seçici, POI düşük; ELINT'in aracı.
- Kanallaştırma (analog → sayısal polyphase/FFT) hem geniş bandı hem kanal başına hassasiyeti hem eşzamanlı sinyali verir; bedeli karmaşıklıktır.
- Sayısal IF (referans zincir) analog seçicilik + sayısal her şey: her sütunda 3–5, bugünün orta yolu. Direct RF sınırı LNA'ya çeker; frekans planı ADC'ye taşınır, jitter LO faz gürültüsünün yerini alır.
- Analog–sayısal sınır tarihsel olarak sola kaydı (video → IF → RF); her adım bir analog problemi DSP problemine çevirdi.
- Radar almacı koherenttir (STALO/COHO), eşlenik filtre kullanır ve monopulse için eşleşmiş kanallar taşır; EH almacı dalga şeklini bilmez.
- RWR/ESM/ELINT aynı katalogdan farklı öncelikle seçer; yazılımcı için PDW alanlarının anlamı ve güveni mimariye bağlıdır — `rf_hesapla()` mimariye göre değişir, eşzamanlılık bayrağı ve tarama çizelgesi PDW'nin parçası olmalıdır.
:::

:::kendini-sina
S: Anlık bant genişliği ile hassasiyet neden aynı mimaride birlikte en yüksek olamaz? Kanallaştırma bu çelişkiyi nasıl "kırar"?
C: Gürültü tabanı $10 log B$ ile büyür: bant 10 kat genişleyince hassasiyet 10 dB kötüleşir. Kanallaştırma toplam bandı geniş tutarken her kanalın B'sini dar tutar; hassasiyet kanal bandına göre belirlenir. Bedel, N kanalın donanımıdır (analogda N filtre, sayısalda N kat FPGA yükü).
S: IFM'de iki darbe üst üste gelince ne olur ve sayısal IF almaç aynı durumda neden daha iyi?
C: IFM tek bir faz farkı ölçer; iki sinyalin vektör toplamının fazı, güçlünün frekansına yakın ama zayıf tarafından "çekilmiş" tek ve yanlış bir değer verir. Sayısal IF'te FFT ya da kanallaştırıcı iki tonu ayrı bin'lerde gösterir (frekans farkı çözünürlükten büyükse); zaman-domain zarf yolu ise IFM gibi karışır — bu yüzden ölçüm FFT'ye de bakar ({{bolum:25}}).
S: Referans zincir (sayısal IF) yerine direct RF sampling seçilseydi hangi bloklar kalkar, hangi yeni problemler gelirdi?
C: Mixer, LO/PLL, IF filtre ve IF yükselteç kalkar; image ve LO sızıntısı yok olur. Gelenler: 9.4 GHz'i örnekleyecek ADC (giriş bandı, NF, güç), saat jitter'ı (100 fs'de ~44 dB SNR sınırı), Nyquist bölgesi seçici filtre ve bölge katlanması/harmonik planı, ADC dinamik aralığının tüm bantla paylaşılması (güçlü bant dışı sinyal herkesi kör eder).
S: RWR ile ELINT almacı aynı emitere baksa PDW'lerinin RF alanı neden farklı "anlama" gelir?
C: RWR (CVR + IFM) frekansı tek darbede, kaba (MHz–on MHz) ve eşzamanlı darbede güvenilmez ölçer; önceliği POI ve tepki süresidir. ELINT (süperhet + sayısal IF) uzun gözlem ve dar bantla kHz doğruluğunda ölçer; önceliği doğruluktur, POI'yi feda eder. Aynı alan adı, iki farklı güven aralığı; PDW'ye çözünürlük/güven bilgisi koymak bu yüzden gerekir.
S: Radar almacında STALO ve COHO ne işe yarar; EH almacında neden yoktur?
C: STALO RF↔IF, COHO IF↔baseband dönüşümünde verici ile alıcıya aynı faz referansını verir; böylece ekonun fazı gönderilen darbeye göre ölçülür ve darbeden darbeye Doppler çıkarılır. EH almacı emiterin vericisine bağlı değildir, ortak referans yoktur; faz yalnızca aynı darbe içinde ya da kendi kanalları arasında anlamlıdır.
:::

:::kopru
Katalogda hangi mimariyi seçersen seç, sayısal olanların hepsi aynı kapıdan
geçer: ADC. Bir sonraki kısım o kapıyı açar — önce örnekleme ve Nyquist
bölgelerinin bu kılavuza özgü hatırlatması (referans senaryonun 1.8 GHz'inin
neden 600 MHz'e ve neden evrik katlandığı), sonra ADC'nin gerçek dünyadaki
kusurları (bit, jitter, SFDR) ve direct RF sampling'in kendine özgü
problemleri. Bölüm 8 ile analog dünyadan çıkıyoruz.
:::
