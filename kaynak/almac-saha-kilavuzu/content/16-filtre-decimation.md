# Bölüm 16 — Filtreleme ve Decimation
::meta onkosul=3,8,12,15 acar=17,18,22,25 blok=filtre rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "Filtre bandını daralttık, gürültü tabanı düştü, hassasiyet
arttı — ama artık 1 µs'lik darbeleri 1.3 µs ölçüyoruz ve TOA 100 ns kayıyor;
neden?" Çünkü filtre yalnızca spektrumu değil darbenin **kenarını** da
şekillendirir: bant genişliği ile yükselme süresi aynı sayının iki yüzüdür.
Sayısal almaçta filtre iki iş yapar: mixer'ın bıraktığı image'ı ve bant dışı
gürültüyü atar, sonra da örnek hızını düşürmenin (decimation) önünü açar.
İkisi de zincirin en çok DSP slice yakan, en çok register taşıyan (katsayılar)
ve en çok "neden böyle ölçtük" sorusu üreten bloğudur. Bu bölüm FIR'ı, onun
ucuz akrabaları halfband ve CIC'i, decimation'ın alias'ı nasıl geri katladığını
ve referans senaryonun 2400 → 600 → 300 MSPS zincirini açar; sonunda filtreye
bir darbenin gözüyle bakar.
:::

## Sezgi: kayan pencere ve fısıltı

En basit sayısal filtre, son K örneğin ortalamasıdır: hızlı değişen bileşenler
(yüksek frekans) ortalamada birbirini götürür, yavaş olanlar kalır. Bu bir
**FIR** filtredir (Finite Impulse Response — sonlu dürtü yanıtı): çıkış, son K
girişin ağırlıklı toplamıdır, ağırlıkların hepsi 1/K. Ağırlıkları
değiştirirsen filtrenin şekli değişir; sinc biçimli ağırlıklar keskin bir
alçak geçiren verir. Hepsi bu: **gecikme hattı, çarpıcılar, toplayıcı**. Zorluk
filtrenin ilkesinde değil, "hangi ağırlıklar, kaç tane, kaç bit" sorusundadır.

:::analoji Kalabalıkta fısıltı
Gürültülü bir odada karşındakinin fısıltısını duymak için kulağını yaklaştırır
ve odanın gerisini "dinlememeye" çalışırsın: bant genişliğini daraltırsın.
İşe yarar — ta ki karşındaki hızlı konuşana kadar: dar dinleme, hızlı heceleri
birbirine bulaştırır. Filtre için de aynı: bant daraldıkça gürültü azalır ama
darbenin kenarı yumuşar, kısa darbeler birbirine karışır. Doğru bant genişliği,
"en dar" değil, "sinyalin hızına yetişen en dar"dır.
:::

## Kavram: FIR — tap, katsayı, konvolüsyon, lineer faz

{{svg:g-160-fir-yapisi.svg|FIR yapısı: tapped delay line (kademeli gecikme hattı). Giriş örnekleri $z^{−1}$ gecikme elemanlarından geçer; her düğümden alınan örnek ("tap") bir katsayı $h_k$ ile çarpılır ve toplayıcı ağacında toplanır. Katsayılar simetrikse ($h_k = h_{N−1−k}$) filtre lineer fazlıdır ve simetrik tap çiftleri çarpımdan önce toplanarak çarpıcı sayısı yarıya iner (kesikli). Altta: dürtü yanıtı katsayıların kendisidir; grup gecikmesi (N − 1)/2 örnek. Yeşil: katsayı RAM'i PS tarafından yazılabilir.|kaydir}}

FIR'ın çıkışı girişle katsayıların **konvolüsyonudur**: $y[n] = ∑_{k=0}^{N−1} h_k · x[n−k]$.
N tap sayısı, $h_k$ katsayılar; dürtü yanıtı katsayıların kendisidir (girişe
tek bir 1 verirsen çıkıştan sırayla $h_0, h_1, …$ çıkar). Frekans yanıtı
katsayıların Fourier dönüşümüdür ({{bolum:3}}): keskin bir geçiş bandı uzun bir
dürtü yanıtı, yani çok tap ister.

Katsayılar **simetrikse** filtre **lineer fazlıdır**: her frekans bileşeni
aynı süre gecikir, dalga şekli bozulmaz. Gecikme sabittir ve tam
**(N − 1)/2 örnektir** — buna **grup gecikmesi** denir. Darbe ölçen bir almaç
için bu iki özellik hayatidir: kenar şekli korunur (PW doğru ölçülür) ve TOA
ofseti sabit bir sayıdır (kalibre edilir). Simetri ayrıca donanımı yarıya
böler: $h_k = h_{N−1−k}$ olduğundan iki tap önce toplanıp bir kez çarpılır.

:::formul id=fir baslik="FIR konvolüsyonu ve grup gecikmesi"
f: y[n] = ∑_{k=0}^{N−1} h_k · x[n−k]      τ_g = frac{N − 1}{2} · frac{1}{f_s}
f: H(f) = ∑_{k=0}^{N−1} h_k · e^{−j2πfk/f_s}      ∑ h_k = 1  (DC kazancı 1)
s: h_k | katsayılar (dürtü yanıtı) | —
s: N | tap sayısı | —
s: τ_g | grup gecikmesi (simetrik katsayı) | s
s: H(f) | frekans yanıtı | —
o: Halfband, N = 23, f_s = 600 MSPS: τ_g = 11 örnek = **18.3 ns**. Kompanzasyon FIR'ı N = {{s:ddc.kompanzasyon_fir_tap}}, 600 MSPS: 15 örnek = 25 ns. CIC R = 4, N = 4: (4·3)/2 = 6 giriş örneği = 2.5 ns. Toplam ≈ 46 ns ≈ 14 çıkış örneği; TOA'ya sabit ofset olarak girer ({{bolum:25}}).
:::

**IIR neden nadir?** Sonsuz dürtü yanıtlı filtreler (geri beslemeli) aynı
keskinliği çok daha az katsayıyla verir; ses ve kontrol dünyasında standarttır.
Almaçta üç nedenle nadirdir: (1) lineer faz vermezler — darbe kenarı frekansa
bağlı gecikir, biçim bozulur; (2) geri besleme sabit noktada kararlılık ve
limit cycle sorunları çıkarır ({{bolum:12}}), 16 bitlik yollarda katsayı
kuantizasyonu kutupları kaydırabilir; (3) geri besleme döngüsü pipeline'ı
kırar — SSR-8'de 8 örneği paralel işleyen bir IIR yazmak zordur, FIR ise
doğal olarak paralelleşir. Kural: veri yolunda FIR; IIR'ı yalnızca yavaş,
tek örnek/saat kollarında (video filtresi, {{bolum:22}}; AGC döngüsü) görürsün.

## Kavram: tasarım parametreleri ve yöntemler

Bir alçak geçiren FIR dört sayıyla tanımlanır: **geçirme bandı** kenarı $f_p$
ve içindeki dalgalanma (**passband ripple**, dB), **durdurma bandı** kenarı
$f_s$' ve içindeki zayıflatma (**stopband attenuation**, dB), ikisi arasındaki
**geçiş bandı** $Δf = f_s' − f_p$. Tap sayısı esas olarak geçiş bandının
darlığı ve zayıflatmanın büyüklüğüyle belirlenir; ripple ikincildir. Kaiser'in
kestirimi tasarımın ilk dakikasında kullanılır:

:::formul id=fir-tap baslik="Tap sayısı kestirimi (Kaiser)"
f: N ≈ frac{A − 8}{2.285 · Δω} + 1      Δω = 2π · frac{Δf}{f_s}
s: A | stopband zayıflatması | dB
s: Δf | geçiş bandı genişliği | Hz
s: f_s | filtrenin çalıştığı örnek hızı | Hz
o: 600 MSPS'te 150 MHz'e kadar geçir, 200 MHz'den sonra 80 dB bastır: Δf = 50 MHz, Δω = 0.524 → N ≈ 72/1.197 + 1 ≈ **61 tap**. Aynı filtre 2400 MSPS'te yapılsaydı Δω dört kat küçük → ≈ 240 tap: **decimation'ı erken yapmanın nedeni** budur.
o: Geçiş bandını 25 MHz'e daraltırsan N ≈ 121; zayıflatmayı 100 dB'ye çıkarırsan N ≈ 77. Tap sayısı geçiş bandıyla ters, zayıflatmayla doğru orantılı.
:::

İki tasarım yöntemi görürsün. **Pencereli sinc**: ideal alçak geçirenin dürtü
yanıtı sinc'tir; sonsuz uzunluktadır, bir pencereyle (Hamming, Kaiser,
{{bolum:19}}'un pencereleriyle aynı aile) kesilir. Basit, kapalı formlü,
Kaiser penceresinin β'sı ile zayıflatma doğrudan ayarlanır; ama passband ve
stopband ripple'ı eşit dağıtmaz, biraz fazla tap harcar. **Parks-McClellan**
(Remez, equiripple): verilen tap sayısı için ripple'ı hem geçirme hem durdurma
bandında eşit dalgalı yapan optimum çözüm; aynı spesifikasyonu %10–20 daha az
tap'le karşılar ve MATLAB `firpm` / SciPy `remez` ile bir satırdır. Üretim
filtreleri genellikle Parks-McClellan'dır; bu kılavuzun widget'ları ve
şekilleri pencereli sinc kullanır çünkü hesap açıktır.

**Katsayı kuantizasyonu** üçüncü tasarım parametresidir ve sabit noktada
kaçınılmazdır ({{bolum:12}}): katsayı B bit ile temsil edilince yanıt bozulur
ve en çok **stopband** zarar görür — kuantizasyon hatası küçük ama rastgele bir
ek filtredir ve onun yanıtı her yerde ≈ −(6·B + 10 log₁₀ N) dB civarındadır.
Somut: 63 tap'lik, kayan noktada 93 dB stopband veren bir Kaiser tasarımı
16 bit katsayıyla 87 dB, 12 bit ile 61 dB verir (widget'ta dene). Bu yüzden
katsayılar 16–18 bit tutulur (DSP48'in 18 bitlik girişine tam oturur) ve
stopband hedefi 80 dB'yi aşacaksa özel önlem gerekir.

## Kavram: decimation — neden, nasıl, alias geri katlanması

**Neden.** Üç sebep: veri hızı ({{bolum:15}}: 76.8 Gbps'i 9.6'ya indirmek),
kaynak (aynı filtre düşük hızda dört kat az tap ister; sonraki her blok sekiz
kat az işlem yapar) ve **işlem kazancı** (bant dışı gürültü atılınca SNR
artar). **Nasıl.** Önce filtre, sonra her M. örneği tut, aradakileri at. Sıra
değişmez; çünkü atma işlemi spektrumu **katlar**.

{{svg:g-161-decimation-katlanma.svg|Decimation'da alias'ın geri katlanması (fs_in = 600 MSPS → M = 2 → 300 MSPS). Üstte: filtre öncesi spektrum; yeni Nyquist sınırı ±150 MHz kesikli. ±150 MHz dışındaki her bileşen (kırmızı) M'ye bölünmüş yeni fs'in katları kadar kaydırılarak bandın içine düşer: 170 MHz'deki bir ton 170 − 300 = −130 MHz'e, 250 MHz'deki gürültü −50 MHz'e katlanır. Ortada: filtre (altın kesikli) katlanacak bölgeleri önceden bastırır; halfband'in −6 dB noktası tam 150 MHz'dedir, geçiş bandı 150 MHz etrafında simetrik katlanır. Altta: decimation sonrası spektrum, yeni eksen ±150 MHz; katlanan kalıntılar filtrenin stopband seviyesinde (−70 dB) kalır.|kaydir}}

:::formul id=decimation baslik="Decimation: yeni fs, katlanma ve işlem kazancı"
f: f_{s,out} = frac{f_{s,in}}{M}      f_{alias} = f − k · f_{s,out}   (f_{alias} ∈ [−f_{s,out}/2, +f_{s,out}/2] olacak k ile)
f: G_{işlem} = 10 · log10( frac{f_{s,in}/2}{B} )      (reel giriş f_s/2 bandından B bandına)
s: M | decimation oranı (tam sayı) | —
s: f | decimation öncesi frekans (kompleks, işaretli) | Hz
s: B | decimation sonrası tutulan bant (kompleks: çift taraflı toplam) | Hz
o: Referans: 2400 → M = {{s:ddc.decimation_toplam}} → **{{s:ddc.cikis_fs_msps}} MSPS**, yeni Nyquist ±{{s:ddc.cikis_bant_mhz}} MHz. İşlem kazancı 10·log10(1200/300) = **{{s:turetilmis_beklenen.islem_kazanci_1200_300_db}} dB**: gürültü tabanı −83.2 dBm'e bu bantla gelinir ({{bolum:4}}).
o: 600 MSPS'te 170 MHz'deki bir kalıntı, M = 2 sonrası 170 − 300 = **−130 MHz**'e katlanır; filtre 170 MHz'de yalnızca −15 dB veriyorsa (halfband geçiş bandı) o kalıntı −130 MHz'de −15 dB'de görünür. Bu yüzden halfband'in "temiz" bandı ±150 değil ≈ ±120 MHz'dir.
:::

Katlanma formülünün pratik anlamı şudur: decimation sonrası bandın her
noktasına, decimation öncesi bandın **M ayrı noktası** düşer. Filtre bu M − 1
"yabancı" noktayı yeterince bastırmak zorundadır; ne kadar bastıracağı,
almaçta kabul ettiğin spur seviyesidir (ADC'nin SFDR'ı ile aynı mertebe,
{{bolum:9}}: 70–80 dB). Yeni Nyquist sınırı ±fs_out/2'dir; bundan sonraki her
blok (FFT, zarf, ölçüm) frekansları bu yeni eksende görür ve ADC'nin
±1200 MHz'ini unutur.

## Kavram: verimli yapılar — halfband, CIC, polyphase

**Halfband.** Kesim frekansı tam fs/4 olan, M = 2 için biçilmiş FIR: merkez
katsayı 0.5, merkez dışındaki **çift indisli katsayıların tamamı sıfır**.
23 tap'lik bir halfband'de yalnızca 13 katsayı sıfırdan farklıdır, simetriyle
7 çarpıcı. Bedeli, yanıtın fs/4 etrafında simetrik olmasıdır: tam fs/4'te
−6 dB, geçiş bandı fs/4'ün iki yanına eşit yayılır; passband ripple ile
stopband zayıflatması da birbirine bağlıdır. Referans zincirin son kademesi
23 tap Kaiser (β = 6) halfband'dir: 120 MHz'de −0.7 dB, 150 MHz'de −6 dB,
200 MHz'de −53 dB, 210 MHz'den sonra −62 dB'nin altında.

**CIC** (Cascaded Integrator-Comb — Hogenauer filtresi). Çarpıcısız
decimator: N adet **integratör** (akümülatör) yüksek hızda, ardından ↓R,
ardından N adet **comb** (M örnek geriden fark) düşük hızda. Her kademe bir
toplayıcı ve bir register'dır; SSR-8'de bile ucuzdur. Yanıtı $(sin(πRf)/(R·sin(πf)))^N$ —
sinc benzeri: R·fs_out'un katlarında sıfırlar (alias bantlarının tam ortası),
aralarda yükselen yan loblar. İki bedeli vardır: (1) **bit büyümesi** tam
N·log₂R bit — integratörler bilerek taşar ve comb'lar taşmayı geri alır,
bu yüzden akümülatörün N·log₂R + B_in bit olması **şarttır**, doyurma
yasaktır ({{bolum:12}}: burada wrap istenen davranıştır); (2) **droop**:
geçirme bandı düz değildir, kenara doğru düşer. Referans CIC (R = 4, N = 4):
kazanç $4^4$ = 256 = 8 bit, 100 MHz'de −1.5 dB, **150 MHz'de −3.4 dB** droop;
alias bandının kenarı olan 450 MHz'de −40 dB, 600 MHz'de sıfır.

{{svg:g-162-cic-yanit.svg|CIC R = 4, N = 4 yanıtı (fs_in = 2400 MSPS, hesaplanmış). Solda 0–1200 MHz: sinc⁴ biçimli yanıt (mavi), 600 ve 1200 MHz'de sıfırlar; ↓4 sonrası (600 MSPS) ±150 MHz'in içine katlanacak alias bantları kırmızı taralı (450–750 ve 1050–1200 MHz); bu bantlarda en zayıf bastırma 450 MHz'de −40 dB. Sağda geçirme bandı büyüteci 0–150 MHz: CIC droop'u 150 MHz'de −3.4 dB (mavi), 31 tap kompanzasyon FIR'ının ters-sinc yanıtı (altın), ikisinin toplamı (yeşil) ±0.1 dB içinde düz. Kompanzasyon FIR'ı 600 MSPS'te çalışır.|kaydir}}

Droop'u **kompanzasyon FIR'ı** düzeltir: geçirme bandında CIC'in tersi
(yükselen), durdurma bandında düşen kısa bir FIR (referans: 31 tap, 600 MSPS'te,
CIC'in hemen arkasında). CIC + kompanzasyon + halfband üçlüsü, yüksek hızlı
decimation'ın standart reçetesidir: CIC kaba işi çarpıcısız yapar ve hızı
düşürür, FIR'lar düşük hızda inceliği sağlar.

**Polyphase.** Decimation'da çıkışın atılacak M − 1 örneğini hesaplamak
israftır. FIR katsayılarını M alt-diziye böl ($h_0, h_M, h_{2M}, …$ birinci;
$h_1, h_{M+1}, …$ ikinci; …), girişi bir **komütatörle** M yola dağıt, her yol
kendi alt-filtresini **çıkış hızında** çalıştırsın, sonuçları topla. Hesap
yükü tam M kat düşer ve yapı SSR ile örtüşür ({{bolum:12}}): SSR-8 girişte 8
örnek zaten yan yanadır, M = 8 polyphase decimator'ün komütatörü kablodan
ibarettir. Halfband'in sıfır katsayıları polyphase yapıda özellikle güzel
oturur: iki yoldan biri yalnızca merkez katsayının gecikmesidir.

{{svg:g-163-cok-kademeli-zincir.svg|Referans senaryonun çok kademeli decimation zinciri (hesaplanmış spektrumlar). Üst şerit bloklar: mixer çıkışı 2400 MSPS kompleks → CIC R = 4, N = 4 (çarpıcısız, +8 bit) → 600 MSPS → kompanzasyon FIR 31 tap → halfband 23 tap ↓2 → 300 MSPS, 16 + 16 bit. Alt şeritte her kademe çıkışının spektrumu (aynı 600 MHz'e katlanmış darbe + gürültü girişi): (a) 2400 MSPS, ±1200 MHz, image −1200'de; (b) CIC sonrası 600 MSPS, ±300 MHz, kenarlarda droop, alias kalıntıları −40 dB altında; (c) kompanzasyon sonrası düz geçirme bandı; (d) halfband + ↓2 sonrası 300 MSPS, ±150 MHz. Her panelde gürültü tabanı ve toplam gürültü gücü (dBFS) yazılıdır: toplam gürültü gücü kademelerde 9 dB düşer, işlem kazancı 6 dB.|kaydir}}

Neden tek kademede 8'e bölmüyoruz? Çünkü tek kademeli bir FIR 2400 MSPS'te
150 MHz geçirip 300 MHz'den sonra 80 dB bastırmak zorunda kalır: Δω çok küçük,
≈ 240 tap, SSR-8'de yaklaşık 1000 çarpıcı. Çok kademeli zincirde toplam
çarpıcı sayısı birkaç düzinedir. **Kural:** kaba decimation'ı ucuz yapılarla
(CIC, halfband) erken yap, keskin filtreyi en düşük hızda uygula.

:::pasaport durak="DDC çıkışı" alan=sayisal
Alan: sayısal (FPGA)
!Frekans: baseband, kompleks; Nyquist ±{{s:ddc.cikis_bant_mhz}} MHz (düz geçirme bandı ≈ ±120 MHz)
Tip: kompleks I/Q
!fs: {{s:ddc.cikis_fs_msps}} MSPS (2400 / {{s:ddc.decimation_toplam}}); örnek süresi {{s:ddc.ornek_suresi_ns}} ns; 1 µs darbe = {{s:ddc.darbe_ornek_sayisi}} örnek
Bit: 16 + 16 bit (Q1.15), yuvarlama + doyurma
!Veri hızı: 300 · 32 = **{{s:ddc.cikis_veri_hizi_gbps}} Gbps** (mixer çıkışının sekizde biri)
!SNR: ADC'ye göre **+{{s:ddc.islem_kazanci_db}} dB** işlem kazancı (1200 → 300 MHz bant); gürültü tabanı B = 300 MHz ile {{s:turetilmis_beklenen.gurultu_tabani_dbm}} dBm
Gecikme: ≈ 46 ns grup gecikmesi + pipeline (latency tablosu)
:::

## Kavram: darbe gözüyle filtre

Spektrum diliyle anlatılan her şey, darbe diliyle de söylenebilir ve almaç
için ikincisi daha önemlidir. Dikdörtgen bir darbenin spektrumu sinc'tir
({{bolum:3}}); {{s:sinyal.pw_us}} µs için ana lob null-to-null
{{s:turetilmis_beklenen.ana_lob_null_null_mhz}} MHz. Filtre bu spektrumdan
ne kadarını geçirirse darbenin kenarı o kadar keskin kalır: **bant genişliği
ile yükselme süresi ters orantılıdır**. Filtre bandı darbenin kendi bandından
genişse (referans: ±150 MHz'e karşı 2 MHz'lik ana lob) kenarı filtre değil,
darbenin kendi rise time'ı ({{s:sinyal.rise_time_ns}} ns) belirler. Filtre
bandı 1 MHz'e inerse kenar ≈ 350 ns'ye yayılır, 1 µs'lik darbe "yuvarlak" bir
tepeye döner, PW ölçümü tanıma göre ({{bolum:25}}: −3 dB / −6 dB / %50) onlarca
ns kayar ve ardışık iki kısa darbe birbirine karışır.

:::formul id=bw-rise baslik="Bant genişliği, yükselme süresi ve TOA doğruluğu"
f: t_r ≈ frac{0.35}{B_{3dB}}      σ_{TOA} ≈ frac{t_r}{sqrt{2 · SNR}}
s: t_r | %10–%90 yükselme süresi (filtre ya da darbenin, hangisi yavaşsa) | s
s: B_{3dB} | filtrenin tek taraflı −3 dB bant genişliği (kompleks baseband'de: ±B) | Hz
s: SNR | zarf üzerinde sinyal/gürültü oranı (doğrusal) | —
o: DDC çıkışı B ≈ 150 MHz → t_r,filtre ≈ 2.3 ns; darbenin kendi kenarı {{s:sinyal.rise_time_ns}} ns baskındır. SNR = {{s:tespit.tespit_snr_db}} dB (31.6) → σ_TOA ≈ 50 / √63.2 ≈ **6.3 ns** ≈ 2 örnek.
o: Filtre bandı 1 MHz'e daraltılırsa t_r ≈ 350 ns; aynı SNR'da σ_TOA ≈ 44 ns — gürültü tabanı 22 dB düştüğü için SNR artar, ama kenar 7 kat yavaşladığı için TOA hatası net olarak **kötüleşir**. Dar bant hassasiyeti artırır, zamanlamayı bozar.
:::

Bir de **geçici rejim** vardır: filtre, dürtü yanıtı uzunluğunca (N örnek)
"ısınır". Darbe başladığında çıkış hemen tepeye çıkmaz; N tap'lik filtrenin
çıkışı N örnek boyunca darbenin ve öncesindeki gürültünün karışımıdır. Uzun
filtre (yüzlerce tap) + kısa darbe (onlarca örnek) birleşimi, darbenin hiç
tepeye ulaşamaması demektir: ölçülen PA düşük, PW kısa çıkar. Referans zincirde
en uzun filtre 31 tap (600 MSPS'te 52 ns), darbe 1 µs; sorun yok. 50 ns'lik
darbeler ölçecek bir almaçta aynı zincir sınırda kalır.

**Interpolation** (kısa not): decimation'ın simetriği. Araya M − 1 sıfır
ekle (↑M), sonra filtreyle ara değerleri doldur; polyphase yapı burada da
geçerlidir ve verici (DUC) tarafının temel bloğudur. Almaçta nadiren, TOA'yı
örnek altı çözünürlükte bulmak için darbe kenarını yerel olarak interpolate
etmek amacıyla karşına çıkar ({{bolum:25}}).

:::widget id=w13 ad="Filtre ve decimation laboratuvarı"
- **Referans senaryo** preset'i (halfband, 23 tap, 600 MSPS, M = 2): frekans yanıtında 150 MHz'de tam −6.0 dB, 120 MHz'de ≈ −0.7 dB, 200 MHz'den sonra −53 dB'nin altını gör; taralı bölge (150–300 MHz) decimation sonrası ±150 MHz'in içine katlanan kısımdır. Grup gecikmesi 11 örnek = 18.3 ns.
- Tipi **CIC + kompanzasyon** yap (R = 4, N = 4): sinc⁴ yanıtında 600 MHz'de sıfır, 150 MHz'de −3.4 dB droop; kompanzasyonu aç, geçirme bandı ±0.1 dB'ye düzlensin. Bit büyümesi satırında **+8 bit** oku.
- Genel **FIR**'da tap sayısını 63, kesimi 150 MHz yap ve katsayı bitini 16'dan 12'ye, sonra 8'e indir: "stopband" satırı ≈ −81 dB'den ≈ −61'e, sonra ≈ −40 dB'ye yükselsin; geçirme bandı ripple'ı neredeyse değişmesin. Kaiser kestirimiyle (61 tap, 80 dB) karşılaştır.
- **Darbe yanıtı** panelinde "Dar bant: 1 MHz" preset'ine geç: 1 µs darbenin kenarı, girişin kendi ≈ 30 ns'sinden ≈ 330 ns'ye yayılsın, tepe 400 ns geç gelsin; "rise time" ve "σ_TOA" satırlarındaki sayıların formülle (0.35/B ≈ 350 ns, t_r/√(2·SNR) ≈ 41 ns) uyuştuğunu gör.
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Analog dünyada bu bloğun karşılığı IF filtresi ve AAF'tir ({{bolum:6}},
{{bolum:9}}): oradaki "shape factor" (−60 dB bandı / −3 dB bandı) burada geçiş
bandı, oradaki grup gecikmesi dalgalanması burada sıfırdır (lineer faz).
Sayısal filtrenin RF mühendisine sunduğu lüks tekrarlanabilirliktir: iki kanal
bit bit aynı yanıta sahiptir, sıcaklıkla kaymaz — yön bulma için kanal
eşleme sorunu analogdan sayısala geçince büyük ölçüde biter. Tek dikkat:
sayısal filtre ADC'nin **önündeki** alias'ı kurtaramaz; AAF'in görevi
devredilemez.
::fpga::
Referans zincir SSR-8 girişte: CIC integratörleri SSR'da özel yapı ister
(8 örneklik ön-toplam + akümülatör), ama çarpıcısızdır; 4 integratör × 24
bit × I/Q. ↓4 sonrası 600 MSPS = SSR-2 (300 MHz saatte 2 örnek). Kompanzasyon
FIR 31 tap simetrik → 16 çarpıcı × SSR-2 × I/Q = **64 DSP**; halfband 23 tap
polyphase ↓2, 7 çarpıcı × I/Q = 14 DSP (çıkış 300 MSPS = SSR-1). Toplam ≈ 80
DSP, ~10 BRAM (gecikme hatları), katsayı RAM'i PS'ten yazılabilir. Latency:
CIC 12 + comp FIR 20 + HB 16 ≈ 48 saat @300 MHz = 160 ns + grup gecikmeleri
46 ns; latency tablosuna toplam ≈ 206 ns yazılır. Kesme noktaları: CIC
çıkışı 24 → 16 (kaydırma 8, yuvarlama), her FIR çıkışı 35 → 16 (yuvarlama +
doyurma). Kompanzasyon FIR'ın ∑|h| ≈ 2.5 olduğuna dikkat: tam ölçek girişte
2.5 kat taşabilir — doyurma şart ya da katsayılar 1/4 ölçekli.
::yazilim::
Yazılımcı iki şeyle karşılaşır. (1) **Katsayı register'ları**: 18 bit Q2.16
(∑|h| > 1 olabildiği için 2 tam bit), sıralı yazılır, çift bankalıysa
"aktif banka" bitiyle atomik geçiş yapılır; yeni katsayı seti yüklerken eski
set çalışmaya devam eder, geçiş bir örnek sınırında olur. Katsayıların
toplamı DC kazancıdır: 1.0'dan farklıysa seviye kalibrasyonu kayar. (2)
**Grup gecikmesi ve latency**: TOA'dan çıkarılacak sabit; katsayı seti
değişince tap sayısı değişmediği için grup gecikmesi değişmez, ama bypass
bitleri (CIC bypass, HB bypass) değişirse **değişir** — TOA düzeltme tablosu
mod bitlerine bağlı olmalı.
:::

:::matlab-fpga baslik="CIC R = 4, N = 4: model ve RTL"
::matlab::
```matlab
% CIC decimator: N integrator @fs_in, ↓R, N comb @fs_out. Kazanc R^N.
R = 4; N = 4;
h1 = ones(R,1);  h = 1;
for k = 1:N, h = conv(h, h1); end       % esdeger FIR: (1+z^-1+..)^N
y  = filter(h, 1, x);                   % kayan nokta model
y  = y(1:R:end) / R^N;                  % ↓R, kazanci geri al

% bit-true: akumulator 16 + N*log2(R) = 24 bit, wrap (mod 2^24)
acc = int64(round(x*2^15));
for k = 1:N, acc = mod(cumsum(acc) + 2^23, 2^24) - 2^23; end   % integrator, wrap
acc = acc(1:R:end);
for k = 1:N, acc = [acc(1); diff(acc)]; end                      % comb (M=1)
acc = mod(acc + 2^23, 2^24) - 2^23;                              % wrap
yq  = floor((acc + 2^7) / 2^8);          % /256: 8 bit kaydir, yuvarla -> Q1.15
```
::fpga::
```verilog
// integrator kademeleri: fs_in hizinda, 24 bit, dogal wrap (doyurma YOK)
reg signed [23:0] i1, i2, i3, i4;
always @(posedge clk_in) begin
  i1 <= i1 + {{8{x[15]}}, x};   // isaret genislet 16 -> 24
  i2 <= i2 + i1;
  i3 <= i3 + i2;
  i4 <= i4 + i3;
end
// ↓R: her 4. ornekte comb'a aktar
reg [1:0] cnt;  reg signed [23:0] d0, c1, c2, c3, c4, d1, d2, d3, d4;
always @(posedge clk_in) begin
  cnt <= cnt + 2'd1;
  if (cnt == 2'd3) begin
    d0 <= i4;  c1 <= i4 - d0;                 // comb 1
    d1 <= c1;  c2 <= c1 - d1;                 // comb 2
    d2 <= c2;  c3 <= c2 - d2;                 // comb 3
    d3 <= c3;  c4 <= c3 - d3;                 // comb 4
  end
end
// cikis: 24 -> 16 bit, 8 bit sağa kaydir + yuvarla (R^N = 256 = 2^8)
wire signed [23:0] r = c4 + 24'sd128;
assign y = r[23:8];
```

Integratörlerin taşması **hatadır sanılır** — değildir: modulo aritmetiği comb
kademelerinde geri alınır; yeter ki genişlik 24 bit olsun ve hiçbir yerde
doyurma bulunmasın. Bit-true karşılaştırmada ({{bolum:13}}) integratör ara
değerleri eşleşmez görünebilir (farklı wrap fazı), çıkış eşleşir.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>
#include <math.h>

/* Kurgusal katsayı arayüzü: 31 tap, 18 bit Q2.16, çift banka. */
#define FIR_COEF_BASE   0x0200   /* 31 × 32 bit; alt 18 bit anlamlı */
#define FIR_CTRL        0x0280   /* [0] aktif banka, [1] yükleme bankası, [4] bypass */
#define FIR_NTAP        31

extern void reg_wr(uint32_t off, uint32_t v);
extern uint32_t reg_rd(uint32_t off);

/* Katsayıları Q2.16'ya çevirip yükleme bankasına yaz, sonra atomik geçiş.
 * Dönüş: DC kazancı (∑h) — 1.0'dan sapma seviye kalibrasyonuna girer. */
double fir_yukle(const double *h)
{
    double toplam = 0.0;
    uint32_t ctrl = reg_rd(FIR_CTRL);
    uint32_t hedef = (ctrl & 1u) ? 0u : 1u;          /* aktif olmayan banka */
    reg_wr(FIR_CTRL, (ctrl & ~2u) | (hedef << 1));
    for (int k = 0; k < FIR_NTAP; k++) {
        long v = lround(h[k] * 65536.0);              /* 2^16 */
        if (v >  131071) v =  131071;                 /* Q2.16 doyurma */
        if (v < -131072) v = -131072;
        reg_wr(FIR_COEF_BASE + 4 * k, (uint32_t)v & 0x3FFFFu);
        toplam += (double)v / 65536.0;
    }
    reg_wr(FIR_CTRL, (ctrl & ~1u) | hedef);           /* aktif banka = hedef */
    return toplam;
}

/* TOA düzeltmesi: grup gecikmesi + pipeline, mod bitlerine bağlı (ns). */
static double toa_ofset_ns(int cic_bypass, int hb_bypass)
{
    double ns = 160.0;                                /* pipeline (latency tablosu) */
    if (!cic_bypass) ns += 2.5;                       /* CIC grup gecikmesi        */
    ns += 25.0;                                       /* kompanzasyon FIR 15 örnek */
    if (!hb_bypass)  ns += 18.3;                      /* halfband 11 örnek @600    */
    return ns;
}
```

:::tuzak Bandı daralttım, PW uzadı, TOA kaydı
Zayıf sinyaller için "gürültüyü azaltalım" diye DDC çıkışına 2 MHz'lik bir
ek filtre konur. Gürültü tabanı 19 dB düşer, hassasiyet artar; ama darbe
kenarı ≈ 175 ns'ye yayılır, eşiği geçme anı seviyeye bağlı kayar (**time
walk**, {{bolum:25}}), PW tanıma göre onlarca ns değişir, 200 ns'den kısa
darbeler hiç tepeye ulaşamaz ve PA düşük ölçülür. Teşhis: PW hatası sinyal
seviyesiyle birlikte değişiyorsa filtre kaynaklı time walk'tur. Çözüm: tespit
kolunda bant genişliğini **en kısa beklenen darbenin** bandına göre seç
(≈ 1/PW_min), hassasiyeti FFT kolundan ({{bolum:18}}) al; iki kol farklı
filtre kullanabilir.
:::

:::tuzak CIC droop'u kalibrasyon hatası sanılır
Bant kenarına yakın (130–150 MHz) emiterlerin PA'sı sistematik olarak 2–3 dB
düşük ölçülür; merkezdekiler doğru. Ekip RF ön ucun frekans yanıtını
suçlar ve kalibrasyon tablosuna frekansa bağlı düzeltme koyar. Gerçek neden
kompanzasyon FIR'ının bypass'ta kalması (ya da yanlış katsayı seti) ve CIC
droop'unun (150 MHz'de −3.4 dB) düzeltilmemesidir. Teşhis: tonu bantta
süpür, DDC çıkışında seviyeyi ölç; sinc⁴ biçiminde bir eğri görüyorsan
CIC'tir. Düzeltme kalibrasyon tablosunda değil, katsayılardadır — tablo
yalnızca sabit bir donanımı düzeltir, bypass biti değişince yanlış olur.
:::

:::tuzak Katsayıları "yeterince yakın" yuvarladım
Yeni katsayı seti MATLAB'dan alınır, 12 bite yuvarlanıp register'a yazılır;
geçirme bandı mükemmeldir. Ama stopband 90 dB'den 60 dB'ye çıkmıştır ve güçlü
bir emiter geldiğinde decimation onun kalıntısını bandın içine katlar:
"hayalet" darbeler, gerçek emiterin frekansının aynasında, 60 dB aşağıda —
yani güçlü emiterler için tespit eşiğinin üstünde. Teşhis: hayalet, gerçek
darbe ile aynı TOA ve PW'ye sahiptir, PA'sı sabit bir oranda düşüktür.
Çözüm: katsayıları donanımın tam genişliğinde (18 bit) yaz, yuvarlamadan sonra
yanıtı **yeniden hesapla** ve stopband'i doğrula; bit-true model bunu zaten
yapıyor olmalı ({{bolum:13}}).
:::

:::ozet
- FIR = gecikme hattı + katsayılar + toplam; simetrik katsayı → lineer faz, sabit grup gecikmesi (N − 1)/2 örnek; IIR lineer faz vermediği, sabit noktada kararsız olabildiği ve pipeline'ı kırdığı için veri yolunda nadirdir.
- Tap sayısı geçiş bandıyla ters, zayıflatmayla doğru orantılı (Kaiser: N ≈ (A − 8)/(2.285·Δω)); Parks-McClellan aynı işi %10–20 az tap'le yapar; katsayı kuantizasyonu stopband'i bozar (63 tap: 16 bit 87 dB, 12 bit 61 dB).
- Decimation: önce filtre, sonra her M. örnek; dışarıda kalan her şey yeni ±fs_out/2 bandının içine katlanır; yeni Nyquist ±150 MHz; işlem kazancı 10·log(1200/300) = 6 dB.
- Halfband (fc = fs/4, çift katsayılar sıfır, −6 dB tam fs/4'te) M = 2 için; CIC çarpıcısız, bit büyümesi N·log₂R (+8), droop (150 MHz'de −3.4 dB) kompanzasyon FIR'ıyla düzeltilir; polyphase hesap yükünü M'ye böler ve SSR ile örtüşür.
- Referans zincir: 2400 → CIC R = 4 → 600 → komp. FIR 31 tap → halfband ↓2 → 300 MSPS, ≈ 80 DSP; tek kademeli eşdeğeri ≈ 1000 çarpıcı.
- Darbe gözüyle: t_r ≈ 0.35/B, σ_TOA ≈ t_r/√(2·SNR); dar bant hassasiyeti artırır, zamanlamayı bozar; filtre uzunluğu geçici rejimi (ısınma) belirler.
- Yazılımcı: katsayı register'ları Q2.16, çift banka, ∑h = DC kazancı; grup gecikmesi + latency = TOA ofseti, bypass bitlerine bağlı.
:::

:::kendini-sina
S: 600 MSPS'te çalışan halfband'i ↓2 ile 300 MSPS'e indiriyorsun. 180 MHz'de −23 dB'lik bir kalıntı decimation sonrası nerede ve hangi seviyede görünür?
C: 180 − 300 = −120 MHz'de, −23 dB seviyesinde (halfband'in geçiş bandı içinde olduğu için zayıf bastırılmıştır). Bu yüzden halfband'in temiz bandı ±120 MHz civarıdır; ±150'nin kenarına yakın her şeye şüpheyle bakılır.
S: CIC R = 4, N = 4'ün integratörleri neden bilerek taşırılır; akümülatör 20 bit yapılsa ne olur?
C: Integratörlerin DC kazancı sonsuzdur; modulo 2^B aritmetiğinde taşma comb kademelerinde geri alınır, yeter ki B ≥ B_in + N·log₂R = 16 + 8 = 24 olsun. 20 bitte comb'un çıkarması taşmayı geri alamaz: çıkış periyodik olarak yanlış olur (büyük sıçramalar). Doyurma eklemek de aynı biçimde bozar; CIC'te wrap zorunludur.
S: Tek kademede 2400 → 300 decimation yapan bir FIR ile üç kademeli zincir arasındaki kaynak farkını kabaca hesapla.
C: Tek kademe: 150 MHz geçir, 300 MHz'den sonra 80 dB: Δω = 2π·150/2400 = 0.393 → N ≈ 72/0.898 ≈ 81… ama geçiş bandının 150'de bitmesi gerektiği (alias 150'ye katlanır) için 150–150 aralığı yok, gerçekçi spesifikasyon 130 → 170 MHz: Δω = 0.105, N ≈ 300 tap; SSR-8'de polyphase ile ≈ 300 çarpıcı, polyphase'siz 2400. Üç kademeli zincir ≈ 80 DSP. Kural: kaba işi ucuz yapılarla erken yap.
S: Filtre bandı 150 MHz'den 5 MHz'e indirildi. Gürültü tabanı ne kadar düşer, 1 µs darbenin kenarı ne olur, TOA hatası (SNR sabit 15 dB kabulüyle) nasıl değişir?
C: Gürültü gücü 30 kat (14.8 dB) düşer. Kenar t_r ≈ 0.35/5 MHz = 70 ns olur (darbenin kendi 50 ns'sinden yavaş → filtre baskın). σ_TOA ≈ 70/√63.2 ≈ 8.8 ns, 6.3 ns'den kötü. SNR gerçekte 14.8 dB artar, bu σ_TOA'yı 5.5 kat iyileştirir; net etki iyileşme — ama darbe 5 MHz'in dışında bir LFM taşıyorsa ({{bolum:3}}) enerjisinin çoğu filtre dışında kalır ve hesap tersine döner.
:::

:::kopru
Bir DDC, bir bandı seçer ve onu temiz, düşük hızlı bir I/Q akışına çevirir. Ama
EH almacı hangi bantta sinyal geleceğini bilmez; aynı anda birçok bant izlemek
zorundadır. Onlarca DDC'yi yan yana koymak yerine hepsini tek bir yapıda,
polyphase filtre bankası ve bir FFT ile yapmanın yolu var — ve o yapının
darbelerle tuhaf bir ilişkisi ("tavşan kulakları"). Bölüm 17 kanallaştırmayı
anlatır.
:::
