# Bölüm 25 — Parametre Ölçümü
::meta onkosul=2,3,14,20,22,23,24 acar=26,27,29,30 blok=olcum rota=yazilimci

:::neden-onemli
Sahadan soru: "Aynı radarın darbeleri PDW'de bazen 1.00 µs, bazen 1.03 µs
görünüyor; güçlü darbelerin TOA'sı zayıflardan sistematik olarak erken.
Donanım mı bozuk?" Hayır — ölçüm tanımlarının ve SNR'ın kaçınılmaz sonucu.
PDW'deki her sayı bir **tanıma** (eşik geçişi mi, %50 noktası mı) ve bir
**belirsizliğe** (gürültü, kuantizasyon, kalibrasyon) sahiptir. Bunları
bilmeyen yazılımcı ya donanımı suçlar ya da yazılımda hatayı "düzeltmeye"
çalışıp yeni hatalar ekler. Bu bölüm PDW'nin beş ana alanının tek darbe
üzerinde nasıl ölçüldüğünü, hangi tanım farklarının hangi sapmayı yarattığını
ve hatanın SNR'la nasıl büyüdüğünü sayılarla verir.
:::

## Sezgi: bir cetvel, bir kronometre, bir terazi — hepsi titriyor

Darbeyi ölçmek, koşucunun süresini elle tutulan kronometreyle ölçmeye benzer.
Kronometreye ne zaman bastığın (eşik tanımı), elinin titremesi (gürültü) ve
kadranın en küçük çizgisi (örnek süresi) üç ayrı hata kaynağıdır. İlkini
tanımla sabitlersin ama sıfırlayamazsın — "koşucu çizgiyi geçince" demek,
göğsü mü ayağı mı sorusunu açık bırakır. İkincisi SNR'la küçülür. Üçüncüsü
kuantizasyondur ve {{bolum:9}}'daki gibi $Δ/√12$ kadar rms hata verir. PDW'deki
her alan bu üç hatanın toplamını taşır ve iyi bir ölçüm tasarımı üçünü
birbirinden ayırt edebilir.

{{svg:g-250-olcu-noktalari.svg|Tek darbe üzerinde bütün ölçü noktaları (hesaplanmış; SNR 20 dB, rise 50 ns, f_bb = +5 MHz). Üstte güç zarfı: T_on eşiği ve 3 dB altındaki T_off, TOA ve bitiş geçişleri, ikisi arasındaki PW oku, %50 genlik noktası, kenarların dışlandığı PA ölçüm bölgesi (taralı). Altta aynı darbenin anlık frekansı: darbe dışında rastgele, içinde 5 MHz etrafında; ölçüm penceresi ortalaması gerçek değerin birkaç kHz yakınında.}}

## TOA: eşik geçişi ve zaman damgası

TOA'nın donanım tanımı basittir: güç zarfı eşiği ilk aştığı örnekte serbest
koşan bir sayacın değeri **kilitlenir** (latch). Sayaç DDC saatiyle
({{s:ddc.cikis_fs_msps}} MSPS) sayar, dolayısıyla TOA'nın doğal çözünürlüğü
bir örnek, {{s:ddc.ornek_suresi_ns}} ns'dir ve kuantizasyon hatası
$3.333/√12 ≈ 0.96$ ns rms'dir. Sayaç açılışta sıfırdan başlar; mutlak zamana
bağlamak için ya bir **PPS** (pulse per second) girişinde sayaç değeri ayrı
bir register'a kilitlenir ve yazılım "sayaç N ↔ UTC saniyesi S" eşlemesini
tutar, ya da sayaç harici bir zaman referansından yüklenir. Çok almaçlı
sistemlerde (TDOA için) bu eşleme hayatidir; tek almaçta PRI ölçümü için
yalnızca sayaçın **sürekli ve atlamasız** olması yeterlidir.

Asıl soru "hangi örnek?"tir. Literatürde üç tanım dolaşır: **eşik geçişi**
(donanımın doğal yaptığı), **%50 genlik (−6 dB güç)** noktası ve **−3 dB**
noktası. Üçü aynı darbede farklı anlardır ve fark darbenin yükselme süresine
bağlıdır. Eşik geçişinin kötü huyu, geçiş anının darbenin **genliğine** bağlı
olmasıdır: sabit eşik, güçlü darbenin kenarını dipte, zayıf darbenin kenarını
tepeye yakın keser. Buna **time walk** (genliğe bağlı zaman kayması) denir.

:::formul id=time-walk baslik="Time walk — eşik geçişinin genliğe bağlılığı (kosinüs kenar modeli)"
f: t_x = frac{t_r}{π} · acos(1 − 2a),      a = frac{A_{eşik}}{A_{tepe}} = sqrt{ frac{P_{eşik}}{P_{tepe}} }
f: Δt_{walk} = t_x(a_{zayıf}) − t_x(a_{güçlü})
s: t_x | darbe başlangıcından eşik geçişine kadar geçen süre | s
s: t_r | kenarın yükselme süresi (0 → %100, kosinüs kenar) | s
s: a | eşiğin tepeye oranı, genlik cinsinden (güç oranının karekökü) | —
o: t_r = {{s:sinyal.rise_time_ns}} ns, eşik {{s:turetilmis_beklenen.hassasiyet_dbm}} dBm sabit. {{s:sinyal.seviye_dbm_giris}} dBm'lik darbe: P_eşik/P_tepe = −8 dB → a = 0.398 → t_x = **21.7 ns**. −40 dBm'lik darbe: −28 dB → a = 0.040 → t_x = **6.4 ns**. Δt_walk = **15.3 ns ≈ 4.6 örnek**.
o: %50 genlik tanımında (a = 0.5) t_x = t_r/2 = 25 ns, genlikten bağımsız — bu yüzden "gerçek" TOA referansı olarak %50 noktası kullanılır; eşik geçişi ölçülür, %50'ye düzeltilir.
:::

{{svg:g-251-time-walk.svg|Time walk. Solda yükselen kenar yakınlaştırması: 0 dB ve −20 dB'lik iki darbe aynı −28 dB eşiğini 6.4 ns ve 21.7 ns'de keser. Sağda kosinüs kenar modelinden hesaplanan gecikme eğrisi: eşik tepeye yaklaştıkça gecikme t_r/2'ye gider; −28, −8 ve −6 dB noktaları işaretli, yatay kesikli çizgi bir örnek süresi. Alt satırlar PW'ye etkisini verir.}}

Düzeltmenin iki yolu var. **Yazılımda**: PDW'deki PA bilindiğine göre
$t_x(a)$ tablodan okunur ve TOA'dan çıkarılır; kenar şekli darbeye göre
değiştiğinden kusursuz değildir ama kaymanın büyük kısmını alır.
**Donanımda**: FSM, eşik geçişinden sonra tepe değeri belli olunca %50
noktasını geriye dönük arar (birkaç örnek geriye bakan küçük bir tampon) ve
iki komşu örnek arasında doğrusal aradeğerlemeyle **kesirli TOA** üretir;
bu, PDW'nin TOA alanına 2–3 kesir biti eklemeyi haklı çıkarır. Referans
tasarımda ilk yol seçilmiştir: TOA eşik geçişidir, düzeltme yazılımdadır ve
PDW belgesi bunu yazar.

## PW: kenar tanımı, SNR ve filtre bant genişliği

PW = bitiş geçişi − TOA. Bitiş, zarfın **T_off = T_on − histerezis**
seviyesinin altına düştüğü örnektir ({{bolum:23}}). Dolayısıyla PW üç şeye
bağlıdır: (1) eşiğin tepeye oranına — eşik dipteyse kenarların daha büyük kısmı
darbeye sayılır ve PW uzun okunur; (2) histerezise — T_off daha düşük olduğundan
düşen kenar daha geç kesilir, PW biraz daha uzar; (3) gürültüye — her iki
kenar kendi başına titrer ve PW hatası tek kenarınkinin $√2$ katıdır.

Kosinüs kenarlı simetrik darbe için eşik tanımlı PW, %50 tanımlı PW'den
$t_r − 2t_x$ kadar farklıdır: referans darbe için eşik tepenin −8 dB'sindeyse
50 − 43.4 = **+6.6 ns**, −28 dB'sindeyse **+37.2 ns** uzun. Aynı radarın
güçlü ve zayıf darbelerinin PW'si bu yüzden farklı okunur; deinterleaving
yazılımı PW toleransını buna göre açmalıdır ({{bolum:27}}).

**Video filtre** ({{bolum:22}}'deki kayan ortalama, uzunluk
{{s:tespit.video_filtre_uzunluk}}) gürültüyü yumuşatır ama kenarı da
$L$ örnek yayar ve $(L−1)/2 = 1.5$ örnek ≈ 5 ns grup gecikmesi ekler.
Gecikme TOA'ya sabit bir kayma olarak biner (PRI'yi etkilemez); yayılma ise
kısa darbelerde tepeyi düşürür: PW = L olan bir darbe tam tepeye ulaşamaz ve
eşiği hiç aşamayabilir. Bu, **min PW** register'ının doğal sınırıdır — filtre
uzunluğundan kısa darbeleri ölçmeye çalışma, tespit de edemezsin.

## PA: tepe mi, ortalama mı; log ölçek ve kalibrasyon

Tepe güç FSM'de bir karşılaştırıcı ve register'la bedavaya gelir ama gürültüye
karşı **yukarı yanlıdır**: 300 örneğin en büyüğü, gürültünün en şanslı anını
seçer. 15 dB SNR'da tepe, ortalamanın 1–2 dB üstünde çıkar. **Kenarlar hariç
ortalama** (darbenin ilk ve son %10'u atılır, kalan güç toplanıp örnek
sayısına bölünür) yansızdır ve varyansı $1/√N$ ile küçülür; bedeli bir
toplayıcı ve bir bölme (ya da kaydırma için 2'nin kuvveti sayıda örnek). Şu
ayrımı bil: ortalama güç, gürültü gücünü de içerir — sinyal + gürültü. 15 dB
SNR'da bu +0.14 dB'lik bir sapmadır; 5 dB SNR'da +1.2 dB. Titiz ölçüm
gürültü tahminini ({{bolum:23}}, `NOISE_EST`) çıkarır.

PA PDW'ye **dBFS** olarak, 0.25 dB adımla yazılır ({{bolum:24}}). dBm'e
dönüşüm bir toplamadır: $PA_{dBm} = PA_{dBFS} + K_{cal}(f, T)$. Referans
senaryoda $K_{cal}$ ön uç kazancı ({{s:on_uc.kazanc_toplam_db}} dB) ve ADC
tam ölçeğinden (+{{s:adc.tam_olcek_dbm}} dBm) çıkar: {{s:sinyal.seviye_dbm_giris}}
dBm'lik darbe ADC girişinde −20 dBm, yani −24 dBFS'tir; $K_{cal}$ = −36 dB.
Bu sabit frekansa (preselector kenarı, IF filtre dalgalanması) ve sıcaklığa
(LNA kazancı ~0.01 dB/°C) bağlı olduğundan tek sayı değil bir tablodur;
{{bolum:30}}'daki `CAL_GAIN_DB` register'ı tablodan seçilen güncel değeri
taşır. Kalibrasyonsuz PA yalnızca *göreli* bir büyüklüktür; iki almaçın PA'sını
karşılaştırmak (AOA için genlik karşılaştırma) mutlaka kalibrasyon ister.

## Frekans: darbe içi ölçüm ve RF'e geri dönüş

İki yol var. **FFT tepesi** ({{bolum:18}}–{{bolum:20}}): darbeyi kapsayan
çerçevede en büyük bin, üç noktalı aradeğerlemeyle inceltilir. Çözünürlük bin
genişliğiyle ({{s:fft.bin_khz}} kHz) sınırlıdır; aradeğerleme iyi SNR'da onda
birine iner. Birden çok darbe aynı anda varsa ya da MOP genişse FFT
yolunun **bant genişliği** ölçümü ve çoklu tepe ayrımı vazgeçilmezdir; ama
gecikmesi büyüktür ({{bolum:26}}).

**Darbe içi anlık frekans**: ardışık iki kompleks örneğin faz farkı
$Δφ = arg(x[n] · x^*[n−1])$, frekans $f = Δφ · f_s / 2π$'dir ({{bolum:2}}).
Darbe boyunca (kenarlar hariç) ortalanınca tek bir sayı çıkar. Bu ölçümün
hatası bin genişliğine değil SNR'a ve darbe içindeki örnek sayısına bağlıdır
ve iyi bir kestiriciyle çok daha incedir:

:::formul id=frekans-crlb baslik="Darbe içi frekans ölçümünün alt sınırı (CRLB, tek ton)"
f: σ_f ≥ sqrt{ frac{12}{(2π)^2 · SNR · N · (N^2 − 1)} } · f_s
s: σ_f | frekans hatasının rms alt sınırı | Hz
s: SNR | örnek başına sinyal/gürültü oranı (lineer) | —
s: N | ölçüme giren örnek sayısı | —
s: f_s | örnekleme hızı | Hz
o: N = {{s:ddc.darbe_ornek_sayisi}}, f_s = {{s:ddc.cikis_fs_msps}} MHz, SNR = {{s:tespit.tespit_snr_db}} dB → σ_f ≈ **5.7 kHz**; 30 dB'de ≈ **1.0 kHz**. FFT bin'inin ({{s:fft.bin_khz}} kHz) elli katı daha ince — PDW'deki 10 kHz'lik RF LSB'si bu alt sınıra göre seçildi.
o: Dikkat: faz farklarının **basit ortalaması** bu sınıra ulaşmaz — ardışık farkların toplamı uçlardaki iki fazın farkına iner ve σ_f ≈ √2·σ_φ / (2π·T_ölçüm) olur (σ_φ = 1/√(2·SNR) örnek başına faz rms'i). 15 dB, 0.8 µs pencere: **≈ 35 kHz** (w19'daki sayı). Ağırlıklı faz kestiricisi (Kay) ya da faza doğrusal uydurma CRLB'ye yaklaşır; FPGA'da ikinci biriktirici (Σ k·Δφ_k) bunun için de kullanılır.
o: 100 ns'lik darbede (N = 30) aynı SNR'da CRLB ≈ **180 kHz**: kısa darbe, kaba frekans. N³ bağımlılığı acımasızdır.
:::

Ölçülen $f_{bb}$ DDC çıkışındaki **baseband ofsetidir**; PDW'ye mutlak RF
yazmak için zincir geri sarılır: NCO frekansı eklenir, Nyquist bölgesi
açılır, LO eklenir. Referans senaryoda her adımın işareti önemlidir:

:::formul id=rf-geri-olcum baslik="Baseband ölçümünden mutlak RF'e (referans zincir, Bölüm 30'daki kart ile aynı)"
f: f_{alias} = f_{bb} + f_{NCO}
f: f_{IF} = f_s − f_{alias}      (2. Nyquist bölgesi: evrik)
f: f_{RF} = f_{LO} + f_{IF}      (low-side LO)
s: f_{bb} | darbe içi anlık frekans ortalaması ya da FFT tepesi (DDC çıkışı) | Hz
s: f_{NCO} | NCO frekansı, FTW'den ({{bolum:14}}) | Hz
s: f_s | ADC örnekleme hızı ({{bolum:8}}) | Hz
s: f_{LO} | yerel osilatör ({{bolum:6}}) | Hz
o: f_bb = 0 → f_alias = {{s:ddc.nco_mhz}} MHz → f_IF = {{s:adc.fs_msps}} − 600 = 1800 MHz → f_RF = {{s:on_uc.lo_ghz}} GHz + 1.8 GHz = **{{s:sinyal.rf_ghz}} GHz** ✓
o: f_bb = **+5 MHz** ölçüldü → f_alias = 605 MHz → f_IF = 1795 MHz → f_RF = **9.395 GHz**. Evrik bölge işareti çevirir: baseband'de yukarı görünen, RF'te aşağıdadır. Evrikliği unutan 9.405 GHz yazar — 10 MHz hata.
o: PDW'ye: 9 395 000 000 / 10 000 = 939 500 → RF alanı = 0xE55EC.
:::

Bu zincirin PL'de mi yazılımda mı kapatıldığı bir tasarım kararıdır; referans
tasarımda PL kapatır (PDW mutlak RF taşır), ama üç sabit — FTW, bölge/inversion
biti, LO — yazılımın yazdığı register'lardan gelir. NCO inversion biti
({{bolum:14}}, `NCO_CTRL` bit0) açıksa DDC çıkışı zaten evrilmiş demektir; o
zaman $f_{bb}$'nin işareti orada çevrilmiştir ve "bölgeyi aç" adımı **tekrar
uygulanmaz**. İki kez düzeltmek, hiç düzeltmemekle aynı hatayı verir.

## MOP: darbe içi profil

Anlık frekansı ortalamak yerine **profiline** bakarsan darbe içi modülasyonu
(MOP — Modulation on Pulse) görürsün. Sabit taşıyıcıda profil düz bir
çizgidir. **LFM**'de doğrusal bir rampadır; en küçük kareler eğimi chirp
hızını verir: referans varyant B'de {{s:sinyal.varyant_b.chirp_bw_mhz}} MHz /
{{s:sinyal.pw_us}} µs = **10 MHz/µs**, örnek başına 33.3 kHz artış. Rampanın
uçları arasındaki fark BW'yi, işareti yukarı/aşağı chirp'i verir. **Faz kodlu**
darbede (Barker, {{bolum:3}}) taşıyıcı sabittir ama kod geçişlerinde 180°'lik
faz atlamaları olur; anlık frekans o örneklerde $±f_s/2$'ye varan tek örneklik
sivri uçlar üretir. Sivri uçların sayısı ve aralığı kodu ele verir; FSM
düzeyinde "pencere içinde eşikten büyük k adet sıçrama" sayacı MOP tipini 2
bite indirger ({{bolum:24}}'teki `MOP` alanı).

{{svg:g-252-anlik-frekans-profili.svg|Darbe içi anlık frekans profili — üç MOP imzası (hesaplanmış, SNR 25 dB). Üstte sabit taşıyıcılı ve LFM darbenin I(t)'si; LFM'de salınım kenarlara doğru sıklaşır. Altta anlık frekans: sabit taşıyıcı 5 MHz'de düz, LFM 0'dan 10 MHz'e doğrusal rampa (eğim 10 MHz/µs), 13-bit Barker kod geçişlerinde sivri uçlar. Ölçüm penceresi ortalaması üçünde de ≈ 5 MHz — ortalama tek başına MOP'u göstermez, profil gösterir.}}

Dikkat: LFM darbenin **ortalama** frekansı da 5 MHz'dir. PDW'de yalnız
ortalamayı taşırsan LFM ile sabit taşıyıcıyı ayırt edemezsin; bu yüzden MOP
tipi ve (uzantı sözcüğünde) eğim/BW ayrı alanlardır.

## AOA: üç ilke

Yön ölçümü çok kanallı bir konudur ve bu kılavuzun tek kanallı zincirinin
dışında kalır; ama PDW'de bir alanı olduğu için ilkeleri bil.
**Genlik karşılaştırma**: birbirine açılı bakan iki antenin (kanalın) PA
farkı, anten desenlerinin kesişim bölgesinde yönle yaklaşık doğrusaldır;
ucuzdur, kabadır (derece mertebesi) ve iki kanalın **kalibre** PA'sını ister.
**Faz interferometresi**: aralığı $d$ olan iki anten arasındaki faz farkı
$Δφ = 2π d sinθ / λ$'dır; {{s:sinyal.rf_ghz}} GHz'de λ ≈ 3.19 cm, $d = λ/2$
için $Δφ = π sinθ$. Faz hatası 5° rms ise yön hatası borda ≈ 1.6°; daha uzun
taban daha hassas ama belirsiz (birden çok θ aynı fazı verir), bu yüzden
birden çok taban birlikte kullanılır. İki kanalın NCO'larının **aynı fazdan
başlaması** ({{bolum:14}}'teki senkron reset) burada şarttır. **TDOA**: iki
ayrı almaçın TOA farkı $Δt = L sinθ / c$; 1 m'lik tabanda azami 3.3 ns — tek
örnek — bu yüzden TDOA uzun tabanlar (yüz metreler, ayrı platformlar) ve
mutlak zaman eşlemesi (PPS) ister; 100 m tabanda 6 ns'lik TOA hatası ≈ 1°
verir. Üçünde de AOA'nın kalitesi PDW'deki PA/TOA kalitesinden gelir; SNR
düşükse AOA da kabalaşır.

## Ölçüm hatası ↔ SNR ve tekrarlanabilirlik

Bütün alanlar için aynı şekil geçerlidir: hata $1/√SNR$ ile küçülür, ölçüme
giren örnek sayısıyla küçülür, kuantizasyon tabanının altına inemez.

:::formul id=toa-hata baslik="TOA hatası ve SNR"
f: σ_{TOA} ≈ frac{t_r}{sqrt{2 · SNR}}      σ_{PW} ≈ sqrt{2} · σ_{TOA}
f: σ_{toplam} = sqrt{ σ_{TOA}^2 + frac{T_s^2}{12} }
s: t_r | kenar yükselme süresi | s
s: SNR | eşik civarındaki örnek başına SNR (lineer) | —
s: T_s | örnek süresi (TOA sayacının LSB'si) | s
o: t_r = {{s:sinyal.rise_time_ns}} ns, SNR = {{s:tespit.tespit_snr_db}} dB → σ_TOA ≈ **6.3 ns** (≈ 2 örnek); SNR = 30 dB → 1.1 ns, artık kuantizasyon (0.96 ns) eşit ağırlıkta. σ_PW ≈ 8.9 ns (15 dB).
o: SNR = 10 dB → σ_TOA ≈ 11.2 ns. Eşik civarında SNR zaten düşüktür; bu yüzden zayıf darbelerin PRI'si "titrek" görünür — radarın değil, ölçümün jitter'ıdır.
:::

Sayıların pratik sonucu: PDW'nin çözünürlüğü (TOA 3.3 ns, RF 10 kHz, PA 0.25
dB) ile **doğruluğu** aynı şey değildir. 15 dB'lik bir darbede TOA ±6 ns,
PW ±9 ns, RF ±6 kHz (iyi kestirici) ile ±35 kHz (basit ortalama) arası, PA ±0.5 dB dolaylarında titrer; 25 dB'de üçte birine
iner. **Tekrarlanabilirlik** (aynı radarın ardışık darbelerinde ölçümün ne
kadar sabit kaldığı) deinterleaving için doğruluktan bile önemlidir: PRI
histogramı ({{bolum:27}}) TOA'nın rastgele hatasını görür, sabit kaymasını
görmez. Kalibrasyon kaymayı, SNR ve N ise rastgele hatayı belirler.

:::widget id=w19 ad="PDW üreteci — darbeden PDW tablosuna"
- **Referans senaryo** preset'inde (SNR 15 dB, PW 1 µs, eşik gürültünün 11.4 dB üstü = Pfa 10⁻⁶, histerezis 3 dB, min PW 4, video filtre 4) dört darbenin dördü tek PDW olsun. Tabloda ΔTOA'nın **hep pozitif ~10–15 ns** olduğunu gör: bu rastgele değil, time walk (eşik tepenin −3.6 dB'sinde kesiyor) + filtre gecikmesi (~5 ns) sapmasıdır; sonuç şeridinde "sapma" ve "rms" ayrı satırlardır. Δf sütununu sonuç şeridindeki iki teoriyle karşılaştır: basit Δφ ortalaması ≈ 35 kHz'i tutturur, CRLB (≈ 5.7 kHz) ancak daha iyi bir kestiriciyle ulaşılır.
- SNR'ı 15'ten 30 dB'ye çıkar: TOA rms'i ~6 ns'den ~1 ns'ye, Δf ~45 kHz'den ~8 kHz'e insin (basit Δφ ortalaması; CRLB satırı hep ~6 kat daha iyidir); sapma ise küçülse de kalsın (time walk hâlâ var). Sonra SNR'ı 10 dB'ye indir: darbeler eşiğin altında kalıp **kaçmaya** başlasın ("kaçan" sayacı).
- **Düşük SNR, eşik indirilmiş** preset'i: 10 dB'lik darbeleri yakalamak için eşik 8.5 dB'ye çekildi; Pfa 10⁻³ mertebesine çıkar ve tabloda **SAHTE** bayraklı kısa PDW'ler belirir — min PW'yi 4'ten 12'ye çıkararak çoğunu ele; PW'si gerçekten kısa bir darbeyi de kaybettiğini fark et.
- **Histerezis yok, eşik düşük** preset'i: tek darbe **onlarca** PDW'ye parçalanır (PARÇA bayrağı, PW sütunu 3–200 ns; "parça" sayacı 30'u aşar). Histerezisi 3 dB'ye, video filtreyi 4'e çıkar; parçalanma dursun. Bu, {{bolum:23}}'teki "kenarda gürültü çentiği" sorununun PDW tarafındaki görüntüsüdür.
- **Varyant B: LFM** preset'i: alt panelde rampa, tabloda "LFM 9.7–9.8 MHz/µs" (gerçek 10; kenar dışlama rampanın uçlarını kırpar) ve ortalama f hâlâ ≈ 5 MHz. MOP'u Barker-13 yap: FAZ↕ bayrağı ve alt panelde sivri uçlar.
- **Uzun darbe (SEG)** preset'i: 4 µs'lik darbe 3 µs'lik DET_MAX_PW'de parçalanır; ilk PDW SEG bayraklı, ikincisi SEG→ ile devam parçası. Yazılım ikisini birleştirmelidir ({{bolum:26}}).
:::

:::pasaport durak="Ölçüm çıkışı" alan=sayisal
Alan: sayısal (FPGA) — darbe başına ölçüm demeti
!Tip: örnek akışı değil, darbe başına 5 ölçüm + bayraklar (PDW'ye paketlenmeden önce)
!TOA: eşik geçişi, sayaç LSB = {{s:ddc.ornek_suresi_ns}} ns; σ ≈ 6.3 ns @ 15 dB, time walk düzeltmesi yazılımda
!PW: T_on/T_off tanımlı; referans darbe ≈ 300 örnek (+2 örnek eşik uzaması); σ ≈ 8.9 ns @ 15 dB
!PA: kenarlar hariç ortalama, dBFS 0.25 dB adım; −24 dBFS ≙ {{s:sinyal.seviye_dbm_giris}} dBm (K_cal = −36 dB)
!RF: darbe içi faz farkı kestirimi → NCO + bölge + LO ile mutlak; {{s:sinyal.rf_ghz}} GHz; σ ≈ 5.7 kHz (CRLB) … 35 kHz (basit ortalama) @ 15 dB
!MOP: profilden tip (yok / LFM 10 MHz/µs / faz kodlu); AOA: tek kanal → geçersiz
SNR: {{s:tespit.tespit_snr_db}} dB (kenar civarı) — bütün hataların ölçeği
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
RF gözüyle ölçüm hataları iki sınıftır: **rastgele** (gürültü — SNR ile
küçülür) ve **sistematik** (time walk, kalibrasyon, filtre gecikmesi —
tanımla ve tabloyla düzeltilir). PDW belgesinde her alanın yanında "tanım +
tipik σ @ SNR" satırı olmalı; olmayan belgeyle çalışan yazılımcı 1.03 µs'lik
PW'yi hata sanır. RF ekibinin katkısı kalibrasyon tablolarıdır: genlik
(frekans × sıcaklık), frekans (ppm), kanal eşleme; ölçüm çekirdeği bu
tablolar olmadan yalnızca *göreli* doğrudur.
::fpga::
Ölçüm çekirdeği FSM'in yanında bir avuç register'dır: TOA latch (48 bit),
örnek sayacı (PW), tepe tutucu (karşılaştırıcı + register), güç toplayıcı
(kenar dışlama için başlangıç/bitiş örneklerini atan iki sayaçla; bölme
yerine örnek sayısı 2'nin kuvvetine yuvarlanıp kaydırma), faz farkı
biriktirici (CORDIC `atan2` ya da küçük LUT ile $arg(x[n]·x^*[n−1])$, 16 bit
yeter; toplamı örnek sayısına bölünür), eğim için $Σ k·Δφ_k$ ikinci
biriktirici. Toplam ~300 LUT + 2–3 DSP slice; latency darbe bitiminden 8–10
saat. RF'e geri dönüş (NCO + bölge + LO) 64-bit toplama/çıkarma ve 10 kHz'e
bölme (sabit çarpan) ile PDW paketleyicide yapılır.
::yazilim::
Yazılımcının üç görevi: (1) tanımları bilmek ve tüketen katmana taşımak —
TOA eşik geçişidir, PW T_on/T_off ile, PA kenarlar hariç ortalama; (2)
düzeltmeleri uygulamak — time walk tablosu (PA → Δt), K_cal (dBFS → dBm),
gerekiyorsa evriklik; (3) belirsizliği yaymak — deinterleaving toleransları
PDW'nin SNR/kalite alanından türetilir: 15 dB'lik darbe için PRI toleransı
±20 ns, 25 dB için ±6 ns. Bu üçü yapılmadan yazılan "PRI = 1000.00 µs"
satırı, dört anlamlı basamağı olmayan bir sayıdır.
:::

## Yazılımcıya dokunan yer

```c
/* PDW ölçümlerini fiziksel birime taşıma ve düzeltme (kurgusal format, B24) */
#include <math.h>

#define FS_DDC_HZ   300e6
#define T_RISE_S    50e-9          /* kalibrasyonda ölçülen tipik kenar; darbe tipine göre tablo olabilir */

/* time walk: eşik/tepe genlik oranından geçiş gecikmesi (kosinüs kenar) */
static double time_walk_s(double esik_dbfs, double pa_dbfs)
{
    double a = pow(10.0, (esik_dbfs - pa_dbfs) / 20.0);   /* genlik oranı */
    if (a < 0.001) a = 0.001; if (a > 0.999) a = 0.999;
    return T_RISE_S / M_PI * acos(1.0 - 2.0 * a);
}

/* TOA'yı %50 genlik noktasına düzelt: t50 = t_esik - t_x(a) + t_r/2 */
static double toa_50_s(const pdw_t *p, double esik_dbfs)
{
    return p->toa_s - time_walk_s(esik_dbfs, p->pa_dbfs) + T_RISE_S / 2.0;
}

/* frekans: PDW zaten mutlak RF taşır; PL kapatmıyorsa Bölüm 30'daki
 * baseband_to_rf(f_bb, ftw) kullanılır — evrikliği yalnızca BİR yerde uygula. */

/* güç: dBFS → dBm, CAL_GAIN_DB (Q8.8) ile */
static double pa_dbm(const pdw_t *p, int16_t cal_q8_8) { return p->pa_dbfs + cal_q8_8 / 256.0; }

/* belirsizlik: tolerans hesabı için */
static double toa_sigma_s(double snr_db) { return T_RISE_S / sqrt(2.0 * pow(10.0, snr_db / 10.0)); }
/* referans: toa_sigma_s(15) ≈ 6.3e-9 ; time_walk_s(-68+36, -60+36) ≈ 21.7e-9 (dBFS'e çevrilmiş) */
```

Dikkat: `time_walk_s` eşiği **dBFS** ister; eşik register'ı güç biriminde
(Q4.16) ise önce {{bolum:30}}'daki `pow_reg_to_dbfs` ile çevir. Eşik CFAR ise
darbe anındaki eşik PDW'de yoktur — kalite alanından (SNR) yaklaşık olarak
$esik ≈ PA − SNR$ türetilir.

:::tuzak "PW'yi %50'ye göre ölçüyoruz" sanmak
Kurgusal vaka: sistem belgesi PW'yi %50 noktaları arası tanımlar, donanım
eşik geçişleri arasını ölçer. Yazılım radar kütüphanesindeki 1.00 µs ile
PDW'deki 1.04 µs'yi eşleyemez; tolerans sıkıysa emiter tanınmaz, gevşetilirse
komşu emiterle karışır. Belirti: PW farkının PA ile korelasyonu (güçlü
darbe daha uzun). Kontrol: kalibre darbe üreteciyle iki farklı genlikte
ölçüm; farkın $t_r − 2t_x$ modeline uyup uymadığına bak; belgeyi ya da
düzeltmeyi düzelt.
:::

:::tuzak Evrikliği iki kez düzeltmek
NCO inversion biti açıkken ({{bolum:14}}) DDC çıkışı zaten düz spektrumludur.
Yazılımcı yine de "2. bölge evrik" diye $f_s − f$ uygular: +5 MHz'lik darbe
9.395 GHz yerine 9.405 GHz yazılır — 10 MHz, yani darbenin spektral
genişliğinin beş katı hata. Belirti: tüm RF'ler bir merkez etrafında
aynalanmış; test üretecinin tonunu ({{bolum:29}}) 1 MHz yukarı kaydır, PDW'de
aşağı kayıyorsa bir düzeltme fazladır. Kural: evriklik zincirde **tek** yerde
düzeltilir ve o yer belgeye yazılır.
:::

:::tuzak Kalibrasyonsuz PA ile genlik karşılaştırma
İki kanalın PA farkından yön çıkarmaya çalışan bir ekip, kanallardan birinin
IF yükseltecinin 1.5 dB daha az kazançlı olduğunu bilmez; tüm hedefler 5°
kaymış görünür ve sıcaklıkla gezinir. PA'nın dBFS hali almaçın iç
ölçeğidir; kanal karşılaştırması ancak `CAL_GAIN_DB` ile dBm'e çevrildikten
ve kanal eşleme tablosu uygulandıktan sonra anlamlıdır ({{bolum:30}}).
:::

:::ozet
- TOA = eşik geçişinde kilitlenen serbest koşan sayaç (LSB 3.33 ns, kuantizasyon 0.96 ns rms); mutlak zamana PPS ile bağlanır. Üç tanım: eşik geçişi, %50 (−6 dB), −3 dB.
- Time walk: sabit eşik, güçlü darbeyi dipte, zayıfı tepeye yakın keser; referans senaryoda −60 ve −40 dBm darbeler arasında 15.3 ns. Düzeltme PA tablosuyla yazılımda ya da kesirli %50 TOA ile donanımda.
- PW = T_off geçişi − TOA; eşik oranına ($t_r − 2t_x$), histerezise ve gürültüye ($√2·σ_TOA$) bağlı; video filtre kenarı L örnek yayar, (L−1)/2 örnek geciktirir.
- PA: tepe gürültüye karşı yukarı yanlı; kenarlar hariç ortalama yansız. dBFS'te 0.25 dB adım; dBm'e K_cal(f, T) ile (−36 dB referans senaryoda).
- Frekans: darbe içi faz farkından; CRLB ≈ 5.7 kHz @ 15 dB, N = 300 (basit Δφ ortalaması ≈ 35 kHz, ağırlıklı/uydurmalı kestirici CRLB'ye yaklaşır) — FFT bin'inden çok ince. RF'e dönüş: + NCO, bölgeyi aç (f_s − f), + LO; f_bb = +5 MHz → 9.395 GHz. Evriklik tek yerde düzeltilir.
- MOP: profilden — LFM doğrusal rampa (10 MHz/µs), faz kodu sivri uçlar; ortalama frekans MOP'u göstermez.
- AOA: genlik karşılaştırma / faz interferometresi ($Δφ = 2πd sinθ/λ$) / TDOA; hepsi PA/TOA kalitesine ve kanal kalibrasyonuna dayanır.
- Bütün hatalar $1/√SNR$ ile küçülür: σ_TOA ≈ t_r/√(2·SNR) ≈ 6.3 ns @ 15 dB. Çözünürlük ≠ doğruluk; tekrarlanabilirlik deinterleaving için belirleyicidir.
:::

:::kendini-sina
S: Eşik sabit −68 dBm; −50 dBm'lik bir darbenin TOA'sı %50 noktasına göre kaç ns erken/geç okunur?
C: P_eşik/P_tepe = −18 dB → a = 0.126 → t_x = 50/π · acos(1 − 0.252) = 50/π · 0.723 = 11.5 ns. %50 noktası 25 ns'de olduğundan eşik geçişi 13.5 ns **erken**dir; yazılım TOA'ya +13.5 ns ekler.
S: FFT tepe bin'i 532 (N = 1024, fftshift'li) ve darbe içi ölçüm +5.90 MHz verdi. Hangisine güvenirsin, RF nedir?
C: Bin 532 → (532 − 512) · 293 kHz = +5.86 MHz; bin çözünürlüğü 293 kHz, aradeğerlemesiz ±146 kHz belirsiz. Darbe içi ölçüm 15 dB'de ±6–35 kHz (kestiriciye göre). İkisi tutarlı; PDW'ye darbe içi ölçüm gider: f_alias = 605.90 → f_IF = 1794.10 → f_RF = 9394.10 MHz.
S: Video filtre uzunluğu 4'ten 16'ya çıkarılırsa PW ve TOA ölçümüne ne olur?
C: Gürültü varyansı 4 kat düşer (kenar civarında TOA rastgele hatası azalır), ama kenar 16 örnek (53 ns) yayılır: filtre gecikmesi 7.5 örnek = 25 ns sabit kayma, 16 örnekten kısa darbeler tepeye ulaşamaz ve kaçar, PW'nin eşik tanımına bağımlılığı artar. Min PW register'ı en az 16 yapılmalıdır.
S: LFM darbenin PDW'sinde RF alanı 9.400 GHz yazıyor; bu değer neyi temsil eder?
C: Darbe içi anlık frekansın ortalamasını, yani chirp'in **merkez** frekansını. Süpürme ±5 MHz'dir; başlangıç frekansı 9.395, bitiş 9.405 GHz'dir. MOP tipi ve eğim/BW olmadan RF alanı tek başına LFM'i sabit taşıyıcıdan ayırt etmez.
S: Aynı radarın 20 dB ve 10 dB SNR'lı darbelerinde PRI histogramının genişliği neden farklıdır?
C: PRI = iki TOA farkı; σ_PRI = √2 · σ_TOA. 20 dB'de σ_TOA ≈ 3.5 ns → σ_PRI ≈ 5 ns; 10 dB'de 11.2 ns → 16 ns. Histogram üç kat genişler. Radarın PRI'si değişmemiştir, ölçüm belirsizliği artmıştır; deinterleaving toleransı SNR'a göre ölçeklenmelidir.
:::

:::kopru
Ölçümlerin nasıl yapıldığını biliyorsun; ama kim karar veriyor "darbe şimdi
başladı, şimdi bitti, şimdi PDW'yi yaz" diye? Eşik geçişini bir olaya çeviren
şey küçük bir durum makinesidir ve gerçek dünyanın bütün pisliği — kenarda
gürültü çentiği, üst üste binen darbeler, hiç bitmeyen CW — onun
kapısına gelir. Bölüm 26 o makineyi, iki kolun zaman hizalamasını ve PDW'nin
FIFO'dan DMA ile PS tamponuna yolculuğunu anlatır.
:::
