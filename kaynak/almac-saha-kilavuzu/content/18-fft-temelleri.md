# Bölüm 18 — FFT'nin Temelleri
::kisim VI — Frekans Domaini: FFT
::meta onkosul=1,2,3,4,9,12,16 acar=19,20,23,25 blok=fft rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "FFT ekranında gürültü tabanı −120 dBFS görünüyor; ADC'nin
datasheet'i 86 dB SNR diyor. Hangisi doğru?" İkisi de. Aynı gürültüyü iki
farklı bant genişliğinde ölçüyorsun ve aradaki 30 dB'lik fark ne bir hata ne
de bir kazanç; bin genişliğinin bandın binde biri olmasıdır. Bu soruyu
cevaplayamayan bir ekip, FFT tabanına bakıp "ADC bozuk" der ya da tersine
tespit eşiğini FFT tabanının 10 dB üstüne koyup gerçek SNR'ın yarısını çöpe
atar. Bu bölüm FFT'nin ne hesapladığını, bin'in ne olduğunu, spektrumu
dBFS'e nasıl ölçekleyeceğini ve gürültü tabanının N ile neden aşağı indiğini
tek bir şemada bağlar. Frekans kolunun ({{bolum:0}}'daki poster) ilk durağıdır.
:::

## Sezgi: bir kutu akort çatalı

Odada bir ses var ve hangi notaların çaldığını bilmek istiyorsun. Elinde N
tane akort çatalı var; her biri farklı, eşit aralıklı bir frekansa ayarlı.
Hepsini aynı anda odaya tutarsın: sesle aynı frekanstaki çatal titreşmeye
başlar, diğerleri sessiz kalır. Titreşen çatalların hangileri olduğuna ve ne
kadar titreştiğine bakarak sesin *frekans içeriğini* okursun. Çatal sayısı
arttıkça frekans ekseni daha ince taranır; ama her çatalın "karar vermesi"
için sesi daha uzun dinlemesi gerekir.

DFT (Discrete Fourier Transform — ayrık Fourier dönüşümü) tam olarak budur:
N örneklik bir diziyi, N adet referans sinüzoidin her biriyle **korelasyona**
sokar. k'ıncı referans, N örnekte tam k periyot tamamlayan kompleks
üsteldir ($e^{−j2πkn/N}$); dizi ile nokta nokta çarpılıp toplanır. Toplam
büyükse sinyalde o frekans vardır; sıfırsa yoktur. **FFT** (Fast Fourier
Transform) aynı N toplamı $N^2$ yerine $N·log_2 N$ çarpımla hesaplayan
algoritmadır; sonucu DFT ile *bit bit aynıdır*, yalnızca hızlıdır. N = 1024
için 1 048 576 yerine 10 240 kompleks çarpım: FPGA'da 300 MSPS'te sürekli FFT
alabilmenin tek sebebi budur.

{{svg:g-180-dft-korelasyon.svg|DFT'nin korelasyon yorumu. Solda 32 örneklik giriş (iki ton: bin 5'te genlik 1, bin 11'de genlik 0.5). Ortada üç referans kosinüsle çarpım: k = 3'te çarpımların işareti değişip toplam sıfırlanır, k = 5'te hepsi aynı işaretli kalır ve toplam N/2 = 16 olur, k = 11'de toplam 8. Sağda tüm bin'ler için çubuklar: enerji yalnızca 5 ve 11'de. Gerçek DFT sinüsle de korelasyon alır (kompleks referans); çizilen yalnızca kosinüs kısmıdır.}}

:::analoji Çatalın dinleme süresi
Bir akort çatalı 440 Hz ile 441 Hz'i ayırt edecekse, iki frekansın bir tam
periyot fark biriktirmesini beklemesi gerekir: 1 saniye. Yarım saniye dinlerse
ikisini de "440 civarı" diye titreşir. DFT'de de öyle: komşu iki bin'i
ayıran şey gözlem süresidir. $Δf = 1/T$ bir tasarım tercihi değil, fiziğin
kendisidir; daha çok çatal (N) almak, süreyi (T = N/fs) uzatmadan çözünürlük
vermez.
:::

## Kavram: bin, bin genişliği ve gözlem süresi

N örneklik FFT, N tane çıkış üretir; her çıkışa **bin** denir. Bin'ler
frekans ekseninde eşit aralıklıdır ve aralık, örnekleme hızının N'e bölümüdür.
Aynı sayı başka bir yoldan da çıkar: N örnek fs hızında T = N/fs saniye
sürer; DFT'nin referansları T'de tam sayıda periyot tamamlayan sinüzoidler
olduğu için komşu referanslar arasındaki fark tam 1/T'dir.

:::formul id=fft-bin baslik="Bin genişliği ve gözlem süresi"
f: Δf = frac{f_s}{N} = frac{1}{T}      T = frac{N}{f_s}
s: Δf | bin genişliği (frekans çözünürlüğü) | Hz
s: f_s | FFT girişinin örnekleme hızı | Hz
s: N | FFT boyu (örnek ve bin sayısı) | —
s: T | çerçevenin (gözlem penceresinin) süresi | s
o: DDC çıkışı f_s = {{s:ddc.cikis_fs_msps}} MSPS, N = {{s:fft.n}} → Δf = **{{s:turetilmis_beklenen.fft_bin_khz}} kHz**, T = **{{s:fft.gozlem_suresi_us}} µs**
o: Aynı fs ile N = 4096 → Δf = 73.2 kHz ama T = 13.65 µs: {{s:sinyal.pw_us}} µs'lik darbe çerçevenin yalnızca %7'sini doldurur ({{bolum:20}}).
:::

Şu üçlüyü bir arada tut: **fs sabitken N'i artırmak** bin'i inceltir ama
çerçeveyi uzatır; **N sabitken fs'i düşürmek** (decimation, {{bolum:16}})
bin'i inceltir ve çerçeveyi yine uzatır. Frekans çözünürlüğünü bedavaya
veren hiçbir düğme yoktur; bedel her zaman zamandır. Darbeli sinyalde bu
bedelin ne demek olduğu Bölüm 20'nin ana konusudur; burada yalnızca sayıyı
kur: referans darbe 300 örnektir, 1024'lük çerçevenin üçte birinden azı.

## Kavram: reel giriş, kompleks giriş ve fftshift

FFT doğası gereği kompleks girişlidir; N kompleks örnek alır, N kompleks bin
verir. Bin'lerin frekansı k·fs/N'dir (k = 0 … N−1) ama bu eksenin *üst
yarısı* aslında **negatif frekanslardır**: bin k = N−1, −fs/N'e denk gelir
({{bolum:2}}'deki negatif frekans ve {{bolum:8}}'deki katlanma aynı şeyin iki
yüzü). Bu yüzden kompleks (I/Q) girişte spektrumu −fs/2 … +fs/2 olarak
görmek için ilk ve ikinci yarıyı yer değiştirirsin: **fftshift**. Referans
senaryoda DDC çıkışı ±150 MHz'lik kompleks banttır; fftshift'ten sonra bin
512 DC'ye (NCO frekansına), bin 0 −150 MHz'e, bin 1023 +149.7 MHz'e karşılık
gelir.

Reel girişte (ADC'nin ham çıkışı, {{bolum:9}}) durum farklıdır: reel sinyalin
spektrumu DC etrafında simetriktir, negatif frekanslar pozitiflerin
eşleniğidir. N reel örnekten alınan FFT'nin yalnızca **ilk N/2 + 1 bin'i
anlamlıdır** (0 … fs/2); üst yarı bilgi taşımaz. Bu, birazdan işlem kazancı
formülünde karşına çıkacak N/2'nin kökenidir. Pratikte iki kural: kompleks
veride N bin'in hepsi kullanılır ve fftshift yapılır; reel veride N/2 bin
kullanılır ve fftshift yapılmaz.

Bir bin numarasını frekansa çevirmek, yazılımcının en çok yaptığı FFT
işlemidir ve en çok hata da buradadır: fftshift yapılmış mı, giriş kompleks
mi, NCO ofseti eklenmiş mi, spektrum evrik mi ({{bolum:14}}, {{bolum:15}}).
Aşağıdaki "Yazılımcıya dokunan yer" bunu tek fonksiyonda toplar.

## Kavram: genlik, güç ve dBFS ölçekleme

Ham FFT çıkışı ölçeksizdir: tam ölçekli (genlik 1) bir kompleks ton, düştüğü
bin'de **N** büyüklüğünde bir değer üretir (N örneğin hepsi aynı fazda
toplanır — g-180'de bin 5'in 16 = N/2 çıkması, reel kosinüsün enerjisinin
yarısının negatif frekansa gitmesindendir). Spektrumu dBFS'e çevirmenin
kuralı bu yüzden basittir: büyüklüğü N'e böl (kompleks giriş) ya da N/2'ye
böl (reel giriş, tek taraflı), sonra 20·log10 al. Pencere kullanıyorsan N
yerine pencere katsayılarının toplamı $∑w$ kullanılır; bu, pencerenin tepe
genliğini düşürmesini (coherent gain, {{bolum:19}}) otomatik telafi eder.

:::formul id=fft-dbfs baslik="dBFS ölçekleme"
f: P_k = 20 · log_{10} ( frac{|X[k]|}{∑w} )      (kompleks giriş)
f: P_k = 20 · log_{10} ( frac{2 · |X[k]|}{∑w} )      (reel giriş, tek taraflı)
s: X[k] | k'ıncı bin'in kompleks FFT çıkışı | —
s: ∑w | pencere katsayılarının toplamı (dikdörtgen pencerede N) | —
s: P_k | bin gücü, tam ölçek ton = 0 dBFS | dBFS
o: N = {{s:fft.n}}, dikdörtgen, tam ölçek kompleks ton bin merkezinde → |X| = 1024 → P = 20·log10(1024/1024) = **0 dBFS**
o: Aynı ton −40 dBFS'te → |X| = 10.24; 16 bit I/Q girişte FFT çıkışı 26 bit taşımalı ki bu da temsil edilsin ({{bolum:20}}, ölçekleme takvimi).
:::

"Güç spektrumu" dediğimizde $|X[k]|^2$'yi kastederiz; dB'ye çevrilince
20·log|X| ile 10·log|X|² aynı sayıdır, karıştırma. Farklı olan, dB'ye
çevirmeden önce mi sonra mı ortalama aldığındır; birazdan Welch'te.

## Kavram: FFT işlem kazancı — taban neden N ile iniyor

Şimdi bölümün açılış sorusuna geliyoruz. Bir ADC'nin SNR'ı, tam ölçek tonun
gücünün **tüm Nyquist bandındaki** (0 … fs/2) toplam gürültü gücüne oranıdır
({{bolum:9}}). FFT aldığında o gürültü N/2 bin'e paylaştırılır (reel giriş);
her bin, toplamın yalnızca 1/(N/2)'sini görür. Ton ise tek bir bin'de kalır.
Sonuç: FFT'de tepe ile taban arasındaki fark SNR'dan 10·log10(N/2) kadar
**büyüktür**. Bu farka **FFT işlem kazancı** (processing gain) denir; N'i 4
katladığında taban 6 dB iner — ton yerinde durur. Gürültü azalmamıştır;
yalnızca daha ince dilimlere bölünmüştür.

:::formul id=fft-islem-kazanci baslik="FFT işlem kazancı ve taban"
f: G_{FFT} = 10 · log_{10} ( frac{N}{2} )      (reel giriş)      G_{FFT} = 10 · log_{10} N      (kompleks giriş)
f: Taban_{FFT} = −SNR − G_{FFT} + 10 · log_{10}(ENBW)
s: G_{FFT} | işlem kazancı: tepe−taban farkının SNR'ı aşan kısmı | dB
s: N | FFT boyu | —
s: SNR | tam ölçek tona göre, tüm bant üzerinden | dB
s: ENBW | pencerenin eşdeğer gürültü bant genişliği (dikdörtgen 1, Hann {{s:fft.hann_enbw_bin}}) | bin
s: Taban_{FFT} | bin başına ortalama gürültü seviyesi | dBFS/bin
o: {{s:adc.bit}}-bit ADC, SNR = {{s:turetilmis_beklenen.snr_ideal_14bit_db}} dB, N = {{s:fft.n}} reel → G = **{{s:fft.islem_kazanci_db}} dB**, taban = −86.0 − 27.1 = **−113.1 dBFS/bin**
o: DDC çıkışı (kompleks, {{s:ddc.cikis_fs_msps}} MSPS): bant içi SNR = 86.0 + {{s:ddc.islem_kazanci_db}} (decimation) = 92.1 dB; N = 1024 kompleks → G = 30.1 dB; Hann ENBW +1.76 → taban = **−120.4 dBFS/bin**. Açılıştaki "−120" budur.
:::

Aynı gürültünün üçüncü bir ifadesi daha var: **NSD** (Noise Spectral
Density — gürültü spektral yoğunluğu), 1 Hz'lik banttaki gürültü gücü,
dBFS/Hz. Datasheet'ler artık SNR yerine çoğunlukla bunu verir, çünkü fs'ten
bağımsızdır. Üç büyüklük aynı fiziksel gürültüyü üç bantta ölçer: SNR tüm
bantta, NSD 1 Hz'de, FFT tabanı bir bin'de. Dönüşüm yalnızca bant oranının
logaritmasıdır ve şu tek şemada durur.

{{svg:g-182-fft-tabani-snr-nsd.svg|FFT tabanı, SNR ve NSD tek şemada (hesaplanmış). Üstte 14-bit reel ADC çıkışının 1024 noktalı FFT'si: tek çekim taban −113 dBFS çevresinde ±10 dB saçılır (mavi); 64 ortalama aynı seviyede düz çizgi olur (altın). Kırmızı kesikli: −SNR − 10·log10(N/2) kestirimi; mor: N = 4096 olsaydı 6 dB aşağısı. Altta üç kutu ve dönüşüm okları: SNR → NSD için bandı 1 Hz'e böl; NSD → FFT tabanı için bin genişliğiyle (ve ENBW ile) çarp. Bin değişince yalnızca sağdaki kutu değişir.}}

:::formul id=nsd baslik="NSD ve FFT tabanı arasındaki köprü"
f: NSD = −SNR − 10 · log_{10} ( frac{f_s}{2} )
f: Taban_{FFT} = NSD + 10 · log_{10}( Δf · ENBW )
s: NSD | gürültü spektral yoğunluğu (tam ölçeğe göre) | dBFS/Hz
s: f_s / 2 | reel ADC'nin Nyquist bandı (kompleks veride tam f_s) | Hz
s: Δf | bin genişliği | Hz
o: SNR = {{s:turetilmis_beklenen.snr_ideal_14bit_db}} dB, f_s = {{s:adc.fs_msps}} MSPS → NSD = −86.0 − 90.8 = **−176.8 dBFS/Hz**
o: Δf = {{s:turetilmis_beklenen.fft_bin_khz}} kHz, Hann → taban = −176.8 + 10·log10(292 969 · 1.5) = −176.8 + 56.4 = **−120.4 dBFS/bin** — SNR yolu ile aynı sayı. NSD yolunun avantajı, reel/kompleks ve decimation ayrımlarını düşünmeden doğru çıkması.
:::

:::saha-notu Tespit eşiği hangi tabana göre?
Frekans ekseninde eşik koyacaksan ({{bolum:23}}) eşiğin referansı FFT
tabanıdır, datasheet SNR'ı değil. Ama tersine, "FFT'de 30 dB SNR gördüm"
diyen biri aslında tepe−taban farkını söylüyordur; gerçek bant içi SNR bundan
G_FFT kadar düşüktür. İki ekibin farklı "SNR" kullandığı toplantılarda önce
bandı sor: hangi bant genişliğinde?
:::

## Kavram: koherent örnekleme, sızıntı ve picket fence

DFT'nin referansları çerçevede *tam sayıda* periyot tamamlar. Girişteki ton
da tam sayıda periyot tamamlıyorsa (frekansı Δf'nin tam katıysa) tek bir
bin'e tam oturur ve diğer bin'ler sıfır okur: **koherent örnekleme** (coherent sampling). Ama
gerçek sinyaller bin ızgarasını bilmez. 10.000 MHz'lik bir ton 1024'lük
çerçevede 34.13 periyot tamamlar; DFT bu çerçeveyi periyodik varsaydığı için
çerçevenin sonu ile başı arasında bir **sıçrama** görür ve sıçrama geniş bant
enerji demektir. Enerji komşu bin'lere yayılır: **spektral sızıntı** (leakage).
Bu, dikdörtgen pencerenin sinc biçimli yan loblarından başka bir şey değildir
({{bolum:3}}'te 1 µs darbenin sinc spektrumu; burada 3.41 µs'lik "darbe" çerçevenin
kendisidir) ve çaresi Bölüm 19'un konusu olan pencerelerdir.

{{svg:g-181-bin-izgarasi-sizinti.svg|Bin ızgarası ve sızıntı (hesaplanmış, fs = 300 MSPS, N = 1024). Üstte çerçevenin sonu ve periyodik kopyasının başı: 9.961 MHz (34 tam periyot) kesintisiz devam eder; 10.000 MHz (34.13 periyot) çerçeve sınırında sıçrar. Altta bin 24–44 arası spektrum: gri çizgi sürekli DTFT, noktalar FFT'nin okuduğu bin'ler. Koherent tonda tek bin 0 dBFS ve diğerleri DTFT'nin sıfırlarına denk gelir; 10 MHz tonda enerji yanlara sızar, en yakın yan lob −13 dB, 10 bin ötede hâlâ −30 dB; tepe 0.26 dB düşer.}}

Sızıntının iki yan etkisi vardır. **Scalloping kaybı:** ton iki bin'in tam
ortasına düşerse en yakın bin tepeyi değil, ana lobun yamacını okur;
dikdörtgen pencerede en kötü kayıp 3.92 dB'dir. Genlik ölçümünde (PA,
{{bolum:25}}) bu 4 dB'lik belirsizlik kabul edilemez olabilir. **Picket
fence (çit) etkisi:** FFT, sürekli spektruma (DTFT) yalnızca bin
merkezlerinden bakar; iki bin arasında ne olduğunu göremezsin — çitin
tahtaları arasından bahçeye bakmak gibi. İki etki de sinyalin değil,
*örneklenmiş* spektrumun özelliğidir.

:::formul id=scalloping baslik="Scalloping kaybı (dikdörtgen pencere)"
f: L_{sc}(δ) = 20 · log_{10} | frac{sin(π δ)}{π δ} |
s: δ | tonun en yakın bin merkezine uzaklığı | bin
s: L_{sc} | okunan tepenin gerçek tepeye göre kaybı | dB
o: 10.000 MHz ton, bin 34.13 → δ = 0.13 → L = 0.24 dB. En kötü durum δ = 0.5 → **3.92 dB**; Hann ile 1.42 dB, flat-top ile 0.01 dB ({{ek:d}}).
:::

## Kavram: zero-padding ve ortalama — ne verir, ne vermez

**Zero-padding** (sıfır doldurma): N örneğin sonuna N örnek daha sıfır ekleyip
2N'lik FFT alırsan bin sayısı ikiye katlanır ve bin aralığı yarıya iner. Bu,
çözünürlük artışı *değildir*: gözlem süresi hâlâ T'dir, ana lob hâlâ 2/T
genişliğindedir, birbirine 1/T'den yakın iki ton hâlâ ayrılmaz. Kazandığın
şey, aynı DTFT'yi daha sık noktadan okumaktır — çitin tahtalarını
sıklaştırmak. Faydası gerçektir: scalloping kaybı düşer, tepe konumu
(frekans) daha iyi okunur ({{bolum:20}}'deki interpolasyona ucuz alternatif).
Bedeli FFT boyu; FPGA'da sıfırları beslemek 2N'lik çekirdek demektir, o yüzden
donanımda nadiren, yazılımda sıkça kullanılır.

**Ortalama alma** (Welch yöntemi): ardışık K çerçevenin güç spektrumlarını
(dB'ye çevirmeden, lineer güçte) toplayıp K'ya bölersen gürültü tabanının
*saçılımı* $√K$ kadar azalır — tek çekimde ±10 dB zıplayan taban 64 ortalamada
±1 dB'lik düz bir çizgi olur. Tabanın **seviyesi değişmez**; gürültü hâlâ
oradadır, yalnızca tahminin varyansı düşmüştür. Zayıf ama sürekli bir sinyali
ortalama ile tabanın altından çıkarabilirsin çünkü sinyal her çerçevede aynı
bin'de birikir, gürültü ise dalgalanmasını kaybeder; ama 1 µs'lik tek bir
darbe için ortalama alacak ikinci çerçeve yoktur. Bu yüzden darbe almacında
ortalama, sürekli emiterler ve gürültü tabanı kestirimi ({{bolum:23}}) için
kullanılır, tespit için değil.

:::widget id=w14 ad="FFT laboratuvarı"
- **Referans senaryo** preset'inde bin genişliğinin 293 kHz, gözlem süresinin 3.41 µs ve teorik tabanın −120.4 dBFS olduğunu doğrula. "Gerçek SNR" 92 dB iken "tepe − taban" ≈ 120 dB okunur: fark 30.1 − 1.76 = 28.3 dB'lik işlem kazancıdır, SNR değil.
- **N'i 4 katla** preset'ine geç (N = 4096): taban 6 dB inip −126.4 dBFS'e gitsin, tepe 0 dBFS'te dursun, "gerçek SNR" satırı değişmesin. Sonra N = 256 yap: taban 6 dB yükselsin.
- **Sızıntı (dikdörtgen)** preset'inde 10 MHz tonun bin 34.13'e düştüğünü, yakınlaştırma panelinde komşu bin'lerin −13, −18, −21 dB'lerde dolduğunu ve tepenin 0.24 dB düştüğünü gör. "Bin merkezine oturt" kutusunu işaretle: komşular −150 dB'ye çöksün (koherent). Pencereyi Hann yap: sızıntı 3 bin'e sıkışsın, taban 1.76 dB yükselsin.
- **Yakın iki ton** preset'inde 0.5 MHz (1.7 bin) uzaklıktaki −6 dBFS ton ana lobun içinde erisin; zero-padding'i 8× yapsan da ayrılmasın (çözünürlük gözlem süresidir). N = 4096 yap: bin 73 kHz, iki ton ayrılsın.
- **64 ortalama** preset'inde "taban saçılımı σ" 5.6 dB'den 0.7 dB'ye insin ama "FFT tabanı ölçülen" −120 dBFS'te kalsın: ortalama seviyeyi değil varyansı düşürür.
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
FFT, analog spektrum analizörünün sayısal ikizidir ama önemli bir farkla:
analizör dar bir filtreyi bant boyunca *tarar* ve her an tek frekansa bakar;
FFT, N tane filtreyi (her bin bir bant geçiren filtredir, genişliği ENBW·Δf)
aynı anda uygular. Bu yüzden 1 µs'lik tek bir darbeyi kaçırmaz — taramalı
analizör kaçırır. RF gözüyle bin genişliği, analizördeki RBW'dir (resolution
bandwidth) ve analizör ekranındaki "gürültü tabanı RBW ile iner" kuralı FFT
işlem kazancının aynısıdır: RBW'yi 10 katına çıkar, taban 10 dB yükselsin.
::fpga::
Radix-2 FFT, log₂N kademe kelebekten (butterfly) oluşur; her kelebek bir
kompleks çarpma (3–4 DSP slice) ve iki kompleks toplamadır. N = 1024 için 10
kademe; pipelined mimaride her kademe kendi kelebeği ve gecikme belleğiyle
sürekli akış işler, örnek başına bir saat. Her kademede genlik en fazla 2
katına (1 bit) çıkabildiği için 16 bitlik giriş 26 bite büyür; ölçekleme
takvimi (scaling schedule) ya da blok kayan nokta (block floating point) bunu yönetir. Twiddle katsayıları ($e^{−j2πk/N}$)
ROM'da durur; çeyrek dalga simetrisiyle N/4 giriş yeter ({{bolum:14}}'teki
LUT hilesinin aynısı). Mimari seçenekleri, gecikme ve bit takvimi
{{bolum:20}}'de.
::yazilim::
Yazılımcı FFT'yi üç yerde görür: bin → Hz dönüşümü (fftshift, NCO ofseti,
evriklik), büyüklük → dBFS dönüşümü (N ve pencere normalizasyonu, çekirdeğin
ölçekleme takvimi) ve "hangi N" kararı (register'a log₂N yazılır; 1024 için
10). En sık hata, çekirdeğin çıkışını "ölçekli" sanıp N'e bir kez daha
bölmek ya da tam tersi: 30 dB'lik sistematik seviye hatası, ADC kalibrasyonunu
suçlatır. İkinci hata, fftshift yapılmış diziye yapılmamış formülü uygulamak:
sinyal −140 MHz'de "görünür", oysa +10 MHz'dedir.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>
#include <math.h>

/* Kurgusal, öğretici: FFT bin numarasını RF frekansına çevirir.
 * k        : bin (0..N-1), fftshift UYGULANMAMIŞ ham çekirdek sırası
 * fs_ddc   : FFT girişinin örnekleme hızı (DDC çıkışı, 300e6)
 * f_nco    : NCO frekansı (600e6) — baseband'in ADC bandındaki merkezi
 * inv      : 1 ise donanım INV biti baseband'i zaten evirmiş demektir
 *            (Bölüm 14); dönüşümden önce geri alınır. Katlanmadan gelen
 *            evriklik ayrıca hesaba katılır (f_if = fs_adc − alias adımı).
 * f_lo     : analog LO (7.6e9), low-side */
static double fft_bin_to_rf(uint32_t k, uint32_t N, double fs_ddc,
                            double f_nco, int inv, double f_lo)
{
    /* 1) ham bin → işaretli baseband frekansı (kompleks giriş) */
    int32_t ks = (k < N / 2) ? (int32_t)k : (int32_t)k - (int32_t)N;   /* fftshift'in tam sayı hali */
    double f_bb = (double)ks * fs_ddc / (double)N;                       /* −fs/2 .. +fs/2 */
    /* 2) donanım INV biti ile evrilmiş baseband'i ham hâline döndür */
    if (inv) f_bb = -f_bb;
    /* 3) ADC bandındaki (alias) konum → IF → RF  (2. Nyquist bölgesi: IF = fs_adc − alias) */
    double f_alias = f_nco + f_bb;                 /* 0 .. 1200e6 */
    double f_if    = 2400e6 - f_alias;             /* bölge 2, evrik katlanma */
    return f_lo + f_if;                            /* low-side: RF = LO + IF */
}

/* Büyüklük → dBFS. mag: çekirdek çıkışı |X[k]| (tam sayı), olcek_kaydirma:
 * çekirdeğin toplam sağa kaydırması (ölçekleme takvimi), sum_w: pencere toplamı
 * (dikdörtgen: N). tam_olcek: giriş kelime tam ölçeği (16 bit → 32767). */
static double fft_mag_to_dbfs(uint32_t mag, int olcek_kaydirma, double sum_w, double tam_olcek)
{
    double x = ldexp((double)mag, olcek_kaydirma) / (sum_w * tam_olcek);   /* kaydırmayı geri al */
    return 20.0 * log10(x > 0 ? x : 1e-12);
}
/* referans: k = 34 (fftshift'siz), N = 1024 → f_bb = +9.96 MHz → RF = 9 390.04 MHz  (inv = 0) */
```

Dönüşümün her satırı bir tuzaktır: (1) `ks` hesabında `k − N` işaretsiz
aritmetikle yapılırsa 4 milyar çıkar; (2) evrikliği kim düzeltiyor — NCO'nun INV biti mi, yazılım mı — register
haritasında yazmalı; iki kez düzeltilen spektrum yine evriktir; (3) `f_if = fs − alias` yalnızca 2. Nyquist bölgesi
içindir, 1. bölgede `f_if = alias`, 3. bölgede `fs + alias` ({{bolum:8}});
(4) `ldexp` ile kaydırmayı geri almazsan spektrum 10·log10(N) = 30 dB aşağıda
görünür ve "hassasiyet kaybettik" alarmı çalar.

:::tuzak "FFT tabanı −120 dBFS, demek ki SNR 120 dB"
Bir ekip FFT ekranında tepe ile taban arasında 120 dB görüp ADC'nin 14 bit
olamayacağına karar verir; başka bir ekip aynı ekrana bakıp "datasheet 86 dB
diyor, bizim FFT 34 dB fazla gösteriyor, ölçekleme bozuk" der. İkisi de
aynı hatayı yapar: bant genişliğini sormaz. Tepe−taban = SNR_bant + G_FFT −
10·log10(ENBW). N = 1024 kompleks, Hann: 92.1 + 30.1 − 1.76 = 120.4. Kontrol:
N'i dört katla; taban 6 dB inerse okuduğun şey işlem kazancıdır ve SNR
değişmemiştir.
:::

:::tuzak Zero-padding ile "çözünürlük artırdım"
MATLAB'da `fft(x, 8*N)` yazan biri iki yakın tonun "ayrıldığını" sanır çünkü
tepe artık daha yuvarlak görünür. Ayrılmamıştır: ana lob genişliği hâlâ
1/T'dir, iki ton hâlâ tek tümsektir; zero-padding o tümseği daha çok
noktadan çizmiştir. Test: tonları 0.7 bin ayır ve 64× zero-padding uygula — tek tepe.
Çözünürlük istiyorsan T'yi uzat (N'i artır, sıfır değil örnek ekle).
Zero-padding'in meşru işi tepe konumunu ve genliğini daha iyi okumaktır.
:::

:::tuzak Ortalama alınca zayıf darbe çıkar sanmak
"Taban çok gürültülü, 16 çerçeve ortalama alalım" — sürekli bir emiter için
doğru refleks, 1 µs'lik darbe için felaket. Darbe 16 çerçevenin birinde var,
on beşinde yoktur; ortalama darbeyi 12 dB bastırır, gürültüyü bastırmaz
(seviyesi zaten değişmez, yalnızca düzleşir). Darbe almacında ortalama
gürültü *tabanını kestirmek* için alınır (eşik referansı, {{bolum:23}});
tespit kararı tek çerçeveden verilir.
:::

:::ozet
- DFT = N örneği N referans sinüzoidle korelasyon; FFT aynı sonucu N·log₂N işlemle verir. Bin k'nın frekansı k·fs/N.
- Bin genişliği Δf = fs/N = 1/T: frekans çözünürlüğü gözlem süresidir (300 MSPS, N = 1024 → 293 kHz, 3.41 µs). Bedava çözünürlük yok.
- Kompleks giriş: N bin, −fs/2…+fs/2, fftshift. Reel giriş: N/2 anlamlı bin, 0…fs/2.
- dBFS: |X| / ∑w (kompleks) ya da 2|X| / ∑w (reel). Çekirdeğin ölçekleme kaydırmasını geri almayı unutma.
- FFT tabanı = −SNR − 10·log10(N/2) [reel] ya da −SNR − 10·log10(N) [kompleks], + 10·log10(ENBW). N'i 4 katla → taban 6 dB iner, SNR değişmez. NSD üçünü bağlayan değişmezdir.
- Bin merkezine oturmayan ton sızar (dikdörtgen: −13 dB yan lob) ve scalloping kaybeder (en kötü 3.92 dB); FFT sürekli spektruma yalnızca bin merkezlerinden bakar.
- Zero-padding örnekleme sıklığı verir, çözünürlük vermez. Ortalama varyansı düşürür, seviyeyi değil; darbe için ortalama alınmaz.
:::

:::kendini-sina
S: fs = 300 MSPS, N = 2048 kompleks FFT. Bin genişliği, gözlem süresi ve 1 µs darbenin çerçeve doluluğu nedir?
C: Δf = 300e6/2048 = 146.5 kHz; T = 6.83 µs; darbe 300 örnek / 2048 = %14.6. Çözünürlük iki kat iyileşti ama darbe çerçevenin yedide birini dolduruyor — kalan kısım yalnızca gürültü toplar (Bölüm 20).
S: Bir 12-bit ADC datasheet'i SNR = 70 dB (fs = 1 GSPS, reel) veriyor. N = 8192 reel FFT'de taban nerede görünür? NSD kaçtır?
C: G = 10·log10(4096) = 36.1 dB → taban ≈ −70 − 36.1 = −106.1 dBFS/bin (dikdörtgen). NSD = −70 − 10·log10(500e6) = −157.0 dBFS/Hz. Kontrol: −157.0 + 10·log10(1e9/8192 = 122 kHz) = −157.0 + 50.9 = −106.1 ✓.
S: FFT çıkışında ton bin 990'da görünüyor (N = 1024, fftshift yapılmamış, kompleks giriş, fs = 300 MSPS). Baseband frekansı nedir?
C: 990 ≥ 512 olduğundan negatif frekans: ks = 990 − 1024 = −34 → f = −34 · 292.97 kHz = −9.96 MHz. fftshift yapılmış dizide bu ton indeks 512 − 34 = 478'de görünürdü. Spektrum evrikse gerçek ofset +9.96 MHz'dir.
S: Aynı sinyal, aynı N; bir mühendis 16 çerçeve Welch ortalaması alıyor, diğeri tek çerçeve. Gürültü tabanının seviyesi ve saçılımı nasıl değişir? Tek bir 1 µs darbe hangi ekranda daha iyi görünür?
C: Seviye ikisinde aynı (−SNR − G + ENBW); saçılım 16 ortalamada √16 = 4 kat (≈ 6 dB) azalır. Tek darbe ortalamada 16 çerçevenin birinde olduğundan 10·log10(16) = 12 dB bastırılır; tek çerçeve ekranında daha iyi görünür.
S: Bir ton iki bin'in tam ortasına düşüyor. Dikdörtgen pencerede okunan tepe kaç dB düşük çıkar ve bu PA ölçümü için ne demektir?
C: 3.92 dB (scalloping). PA'yı FFT tepe değerinden okuyan bir sistem ±4 dB belirsizlik taşır; çözüm pencere (Hann 1.42 dB, flat-top 0.01 dB), zero-padding ya da komşu bin'lerle interpolasyon (Bölüm 20).
:::

:::kopru
Sızıntının kaynağı çerçevenin keskin kenarlarıdır; DFT, çerçeveyi periyodik
tekrarlayınca o kenarlarda sıçrama görür. Kenarları yumuşatırsan — çerçeveyi
dikdörtgen yerine ortası dolu, uçları sıfıra inen bir eğriyle çarparsan —
yan loblar çöker, ama ana lob genişler ve taban ENBW kadar yükselir. Bölüm 19
bu takası pencere ailesi üzerinden, Ek D'nin sayılarıyla kurar.
:::
