# Bölüm 9 — Kuantizasyon ve ADC Performans Metrikleri
::meta onkosul=1,4,8 acar=10,11,12,18,21 blok=adc rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "ADC 14 bit; 6.02 · 14 + 1.76 = 86 dB olması lazım. Neden
FFT'de 57 dB görüyoruz?" Bu sorunun cevabı tek bir sayı değil, dört ayrı
mekanizmadır: kuantizasyon gürültüsü gerçekten 86 dB'dir ama termal gürültü,
saat titremesi (jitter) ve doğrusalsızlık onun çok üstüne çıkar; üstelik
FFT'nin gösterdiği "taban" SNR'ın kendisi bile değildir. Tespit eşiğini
({{bolum:21}}) gürültü tabanına göre kuran, kazancı ADC doymasın diye ayarlayan
ve datasheet'ten "bu ADC bize yeter mi" diyecek olan sensin. Bu bölüm o
datasheet'in ilk sayfasını, satır satır, referans senaryonun sayılarıyla
okur.
:::

## Sezgi: milimetrik cetvelle ölçmek

Bir masanın boyunu milimetre bölmeli cetvelle ölçüyorsun. Gerçek boy
1234.37 mm ise sen 1234 yazarsın; 0.37 mm'lik farkı cetvel *görmez*. Her
ölçümde en fazla yarım milimetre hata yaparsın ve bu hata, masadan masaya
rastgele dağılır: bazen +0.4, bazen −0.2. Çok masa ölçersen hatalar
"gürültü" gibi davranır; ortalaması sıfır, yayılımı bölme aralığına bağlı.
ADC de budur: giriş gerilimini $2^N$ eşit basamağa bölen bir cetvel. Basamak
**LSB**'dir (least significant bit — en anlamsız bit), yarım basamaklık
hata **kuantizasyon gürültüsüdür** ve bit sayısını artırmak cetvele daha
ince bölme çizmektir.

Ama cetvel benzetmesinin bir sınırı var: gerçek ADC'nin bölmeleri eşit
aralıklı değildir (INL/DNL), cetveli tam o anda tutamazsın (jitter) ve
masanın kendisi titrer (termal gürültü). 14 bitlik cetvelin son üç-dört
bölmesi bu yüzden pratikte okunmaz. "14 bit" etikettir; **ENOB** gerçektir.

## Kavram: LSB, tam ölçek ve dBFS

ADC'nin kabul ettiği en büyük gerilim aralığı **tam ölçektir** (full scale,
FS); referans senaryoda {{s:adc.tam_olcek_vpp}} Vpp, 50 Ω'da
{{s:adc.tam_olcek_dbm}} dBm'e karşılık gelir ({{bolum:1}}). Tam ölçek
genlikli bir sinüs **0 dBFS**'tir; her şey ona göre ölçülür. dBFS, dBm'in
ADC dünyasındaki karşılığıdır ve iki dünya arasında geçiş tek bir sabittir:
dBFS = dBm − FS_dBm.

:::formul id=lsb-dbfs baslik="LSB ve dBFS"
f: LSB = frac{V_{FS}}{2^N}        P_{dBFS} = P_{dBm} − P_{FS,dBm}
f: 1 LSB genlikli sinüs = 20·log_{10}( frac{1}{2^{N−1}} ) dBFS
s: V_{FS} | tam ölçek tepe-tepe giriş aralığı | V
s: N | çözünürlük | bit
s: P_{FS,dBm} | tam ölçek sinüsün gücü (50 Ω) | dBm
o: V_FS = {{s:adc.tam_olcek_vpp}} Vpp, N = {{s:adc.bit}} → LSB = 1 V / 16 384 ≈ **61 µV**; 1 LSB genlikli sinüs ≈ **−78.3 dBFS**.
o: Darbe ADC girişinde −20 dBm, tam ölçek {{s:adc.tam_olcek_dbm}} dBm → **−24 dBFS**; gürültü tabanı −43.2 dBm (300 MHz) → **−47.2 dBFS**.
:::

Sinyal seviyesini dBFS'te düşünmeye alış: register'daki eşik, PDW'deki PA
alanı, "overrange" bayrağı — hepsi dBFS'te yaşar; dBm'e çevirmek için
zincirin kazancını ve FS'i bilmek gerekir ve o bilgi kalibrasyon tablosunda
durur ({{bolum:26}}).

## Kavram: kuantizasyon gürültüsü ve 6.02N + 1.76

Kuantizasyon hatası e[n] = y[n] − x[n], −LSB/2 ile +LSB/2 arasındadır. Sinyal
"yeterince karmaşık" olduğunda — birkaç LSB'den büyük ve örnekleme
frekansıyla basit bir oranda olmayan bir frekansta — hata bu aralıkta
tekdüze dağılır, ardışık örnekler arasında bağıntı taşımaz ve **beyaz
gürültü** gibi davranır. Tekdüze dağılımın varyansı LSB²/12'dir; tam ölçek
sinüsün gücü (FS/2)²/2'dir; oranı alıp dB'ye çevirince meşhur formül çıkar.

{{svg:g-90-kuantizasyon-merdiveni.svg|Kuantizasyon merdiveni ve hata sinyali (3 bit, öğretici). Solda sürekli sinüs (altın) ve 8 basamaklı kuantizör çıkışı (mavi merdiven); 1 LSB oku. Altta hata e[n]: ±½ LSB arasında, sinyale bağlı ama gürültü gibi. Sağda modelin varsayımı: hata tekdüze dağılır, varyansı LSB²/12; tam ölçek sinüse oranı 1.5 · 2^(2N) → SNR = 6.02·N + 1.76 dB.}}

:::formul id=snr-q baslik="İdeal kuantizasyon SNR'ı"
f: SNR_q = 6.02 · N + 1.76  dB        (tam ölçek sinüs, Nyquist bandı)
f: SNR_q(A) = 6.02 · N + 1.76 + A_{dBFS}        (A_{dBFS} ≤ 0: sinyal küçüldükçe SNR düşer)
s: N | çözünürlük | bit
s: A_{dBFS} | sinyal genliği tam ölçeğe göre | dBFS
o: N = {{s:adc.bit}} → **{{s:turetilmis_beklenen.snr_ideal_14bit_db}} dB**. N = 12 → 74.0 dB, N = 16 → 98.1 dB: bit başına 6.02 dB.
o: Darbe −24 dBFS'te → kuantizasyona göre SNR = 86.0 − 24 = **62 dB**. Gürültü sabit, sinyal küçüldü; oran da küçüldü.
:::

Formülün üç ince noktası var. **Birincisi**, 1.76 dB sinüs içindir; gürültü
benzeri ya da darbeli sinyaller için tepe/ortalama oranı farklıdır, sabit
değişir ama 6.02·N gövdesi kalır. **İkincisi**, gürültü gücü fs/2'lik
Nyquist bandına yayılmıştır; dar banda bakınca payına düşen azalır (işlem
kazancı, birazdan). **Üçüncüsü**, model küçük sinyalde çöker: sinyal birkaç
LSB'ye inince hata artık gürültü değil, sinyale kilitli periyodik bir
örüntüdür ve spektrumda **çizgi** olarak görünür. Bunu kıran hile
**dither**'dır: girişe kasıtlı, küçük (≈ 1 LSB rms) bir gürültü eklemek.
Hata rastgeleleşir, çizgiler tabana dağılır; karşılığında toplam gürültü
gücü artar — ±½ LSB tekdüze dither ile tam iki kat, yani **3 dB**. Tespit
almacında bu kötü bir takas değildir: tespit eşiğini periyodik bir çizginin
aşması, tabanın 3 dB yükselmesinden çok daha pahalıdır. Modern RF ADC'lerde
dither çip içindedir ve genellikle sayısal olarak çıkarılır; register'da bir
"dither enable" biti görürsen ne yaptığını artık biliyorsun.

:::widget id=w08 ad="Kuantizasyon laboratuvarı"
- **Referans senaryo** (14 bit, −1 dBFS): ölçülen SNR'ın teorik 85.0 dB'ye (86.0 − 1) birkaç onda bir dB içinde oturduğunu, hata RMS'inin 1/√12 ≈ 0.289 LSB çıktığını gör. Bit sayısını 14'ten 12'ye indir: SNR tam 12 dB düşsün, spektrumdaki taban 12 dB yükselsin.
- **Kaba kuantizör (4 bit)** preset'i: hata sinyali artık gürültüye değil sinyale benziyor; spektrumda harmonik çizgileri belirsin, SFDR 35 dBc civarına insin. **4 bit + dither**'a geç: çizgiler dağılsın, SFDR yükselsin, ama ölçülen SNR yaklaşık 3 dB düşsün (24.8 → ~22).
- Giriş seviyesini −1'den −40 dBFS'e indir (14 bit): SNR 46 dB'ye düşsün — gürültü değişmedi, sinyal küçüldü. Spektrum tabanının yerinde durduğunu doğrula.
- **Aşırı sürme (+3 dBFS)**: dalga şekli tepelerinde düzleşsin (clipping), hata sinyali ±½ LSB penceresinin dışına fırlasın, "clipping" satırı örnek saysın ve SFDR 20 dBc'ye çöksün — overrange bayrağının neden kritik olduğu.
- **Analog gürültü baskın** (−60 dBFS ek gürültü): ölçülen SNR 59 dB'de takılsın; bit sayısını 14'ten 16'ya çıkarmak hiçbir şeyi değiştirmesin. Gerçek RF ADC'nin hikâyesi budur.
:::

## Kavram: metrik ormanı — SNR, SINAD, ENOB, THD, SFDR, IMD, NSD

Datasheet'in ilk sayfası aynı FFT grafiğinden türetilmiş yarım düzine
sayıdır. Aşağıdaki şekil o grafiği, kurgusal bir 14-bit ADC için, referans
senaryonun fs'inde çizer ve her sayının grafikte *neresi* olduğunu
işaretler. Kardeş kılavuzun metrik tablosuna ({{rf:metrik-ormaninda-yol-bulmak|RF Örnekleme: metrik ormanı}})
buradan bakabilirsin; biz almacın sorularına odaklanıyoruz.

{{svg:g-91-adc-fft-aciklamali.svg|Açıklamalı ADC FFT grafiği — kurgusal 14-bit cihaz, fs = 2400 MSPS, N = 4096, Blackman-Harris pencere, tek ton testi. Temel ton −1 dBFS; HD3 en kötü spur (SFDR oku, yeşil); HD2 ve 2-yollu interleaving image kırmızı; fs/2 yakınında ofset spur'u. Altın çizgiler: toplam gürültü gücü (tek sayı, SNR ≈ 57 dB) ile bin başına FFT tabanı (≈ −89 dBFS) arasındaki fark FFT işlem kazancı 10·log(N/2) = 33.1 dB'dir (pencere ENBW'si ≈ 3 dB geri alır). NSD ≈ −149 dBFS/Hz.}}

- **SNR** (signal-to-noise ratio): sinyal gücü / *gürültü* gücü; harmonikler
  ve spur'lar dışarıda bırakılır. Gürültü tabanının yüksekliğini, dolayısıyla
  hassasiyeti anlatır. Datasheet'te "SNR = 60 dBFS @ f_in = 900 MHz, −1 dBFS"
  gibi koşullu verilir; f_in yükseldikçe düşer (jitter).
- **SINAD** (signal-to-noise-and-distortion): payda gürültü + tüm bozulma.
  "Her şey dahil" kalite. **ENOB** onun bit cinsinden çevirisidir.
- **THD** (total harmonic distortion): ilk birkaç harmoniğin (tipik HD2–HD6)
  toplam gücü, dBc. SINAD = SNR ⊕ THD (güç toplamı).
- **SFDR** (spurious-free dynamic range): temel ton ile en büyük spur
  arasındaki mesafe — harmonik, interleaving spur'u ya da başka bir çizgi,
  hangisi en büyükse. **dBc** olarak (tona göre) ya da **dBFS** olarak (tam
  ölçeğe göre) verilir; −1 dBFS tonda ikisi 1 dB farklıdır, −20 dBFS tonda
  20 dB. Hangisinin yazıldığına bak. Almaçta SFDR, "güçlü bir emiterin
  yanındaki zayıf emiteri spur sanmadan görebilir miyim" sorusudur.
- **İki tonlu IMD3**: iki eşit ton f1, f2 girince 2f1 − f2 ve 2f2 − f1'de
  doğan ürünler, dBc. Yoğun ortamda (aynı anda birçok emiter) sahte darbe
  üreten mekanizma budur; ölçüm koşulu (ton seviyesi, aralık) mutlaka
  belirtilir.
- **NSD** (noise spectral density): 1 Hz'e düşen gürültü, dBFS/Hz. SNR'ın
  bant genişliğinden bağımsız hali; geniş bantlı ADC'leri karşılaştırmanın
  doğru yolu.

:::formul id=enob-nsd baslik="ENOB, SINAD ve NSD"
f: ENOB = frac{SINAD − 1.76}{6.02}        SINAD = −10·log_{10}( 10^{−SNR/10} + 10^{−THD/10} )
f: NSD = −( SNR + 10·log_{10}( f_s / 2 ) )  dBFS/Hz
s: SNR, THD | gürültü ve harmonik oranları (pozitif dB, dBc) | dB
s: ENOB | etkin bit sayısı | bit
s: f_s | örnekleme frekansı | Hz
o: Kurgusal ADC: SNR = 57 dB, THD ≈ −71 dBc → SINAD ≈ 56.8 dB → ENOB ≈ **9.1 bit**. 14 bitlik etiketten ~5 bit gürültü ve bozulmaya gitti; RF frekansında 9 etkin bit iyi bir sayıdır.
o: NSD = −(57 + 10·log(1.2 GHz)) = −(57 + 90.8) ≈ **−148 dBFS/Hz**. Şekildeki −89 dBFS'lik "taban" NSD değildir: bin genişliği 586 kHz (57.7 dB) ve pencere ENBW'si (+3 dB) eklidir.
:::

:::saha-notu FFT tabanı ≠ SNR ≠ NSD
Aynı gürültünün üç farklı sayısı vardır ve üçü de doğrudur: **SNR** tüm
Nyquist bandındaki toplam gürültü (tek sayı, −58 dBFS), **FFT tabanı** bir
bin'e düşen pay (−89 dBFS; N büyüdükçe iner, pencereyle oynar), **NSD**
1 Hz'e düşen pay (−148 dBFS/Hz; hiçbir şeye bağlı değil). Sahada "FFT'de
taban −89'da ama datasheet SNR 57 diyor, hangisi doğru?" tartışması bu üç
sayının karıştırılmasıdır. Aralarındaki köprüler 10·log(N/2) ve 10·log(bin);
{{bolum:18}} bunu FFT tarafından yeniden kurar.
:::

## Kavram: işlem kazancı — dar banda inince gürültü neden azalır

ADC'nin gürültüsü fs/2'lik banda yayılmıştır. Senin sinyalin o bandın
küçük bir dilimindedir: DDC ({{bolum:15}}, {{bolum:16}}) o dilimi kesip
gerisini atınca, gürültünün de yalnızca dilime düşen kısmı kalır. Sinyal
gücü aynı, gürültü gücü bant oranı kadar azalmış: SNR artar. Buna **işlem
kazancı** (processing gain) denir ve bedavadır — yeter ki dilimin dışındaki
gürültüyü gerçekten atan bir filtren olsun.

:::formul id=islem-kazanci baslik="Oversampling işlem kazancı"
f: PG = 10·log_{10}( frac{f_s / 2}{B} )        SNR_{bant} = SNR_{Nyquist} + PG
s: B | ilgilenilen bant genişliği (reel: tek taraflı; kompleks I/Q: toplam) | Hz
s: f_s / 2 | Nyquist bandı | Hz
o: f_s = {{s:adc.fs_msps}} MSPS, DDC çıkışı ±{{s:ddc.cikis_bant_mhz}} MHz = 300 MHz → PG = 10·log(1200/300) = **{{s:turetilmis_beklenen.islem_kazanci_1200_300_db}} dB**. ADC'nin 57 dB'si DDC çıkışında 63 dB olur.
o: Aynı ADC 2 MHz'lik bir darbe bandına indirilseydi PG = 10·log(1200/2) ≈ **27.8 dB** — bu yüzden dar bantlı kanal, geniş bantlı EH almacından çok daha hassastır ({{bolum:4}}, {{bolum:17}}).
:::

Dikkat: işlem kazancı yalnızca *beyaz* gürültü için geçerlidir. Spur'lar
bandın içindeyse olduğu gibi kalır; jitter gürültüsü de sinyalin etrafına
yığıldığı için dar banda inince beklediğin kadar azalmaz. Bu yüzden
datasheet SNR'ını değil, **bandındaki NSD'yi** düşün.

## Kavram: aperture jitter — GHz girişte saat her şeydir

ADC, örneği saatin söylediği anda alır. Saat kenarı σ_j kadar titriyorsa
örnek yanlış anda alınır ve sinyal o anda dV/dt hızıyla değişiyorsa zaman
hatası gerilim hatasına dönüşür. Sinüsün eğimi frekansıyla orantılıdır;
dolayısıyla aynı jitter, **giriş frekansı** yükseldikçe daha çok gürültü
üretir — fs ile değil, f_in ile. Bant geçiren örneklemenin ({{bolum:8}})
gizli faturası budur: 1.8 GHz'lik IF'i örneklerken jitter cezası 1.8 GHz
üzerinden kesilir, alias'ın düştüğü 600 MHz üzerinden değil.

:::formul id=jitter baslik="Jitter SNR tavanı"
f: SNR_j = −20·log_{10}( 2π · f_{in} · σ_j )
s: f_{in} | sinyalin ADC girişindeki gerçek frekansı (alias değil) | Hz
s: σ_j | toplam rms jitter: √(σ_{saat}² + σ_{aperture}²) | s
o: f_in = {{s:on_uc.if_ghz}} GHz, σ_j = {{s:adc.jitter_fs}} fs → SNR_j = −20·log(2π · 1.8e9 · 1e−13) = **58.9 dB**. 14 bitin 86 dB'si burada 59 dB'ye kilitlenir.
o: Bilinen-cevap: f_in = 1 GHz, σ_j = 100 fs → **{{s:turetilmis_beklenen.jitter_snr_1ghz_100fs_db}} dB**. Direct RF örneklemede f_in = {{s:sinyal.rf_ghz}} GHz → **44.6 dB**; 86 dB'yi 1.8 GHz'te görmek için σ_j ≈ 4.4 fs gerekirdi.
:::

{{svg:g-92-jitter-snr.svg|Jitter SNR tavanı eğri ailesi. Yatay eksen giriş frekansı (log), düşey eksen SNR. σ = 50, 100, 200, 500 fs doğruları: frekans ya da jitter iki katına çıkınca 6 dB düşer. Altın kesikli çizgiler 14 ve 12 bit ideal kuantizasyon SNR'ı. Çalışma noktaları: referans senaryo (1.8 GHz, 100 fs → 58.9 dB), direct RF (9.4 GHz → 44.6 dB), kötü saat (500 fs → 45 dB).}}

σ_j iki kaynağın karesel toplamıdır: ADC'nin kendi **aperture jitter**'ı
(datasheet'te sabit, tipik 50–100 fs; senin elinde değil) ve dışarıdan
verdiğin **örnekleme saatinin** jitter'ı (tamamen senin — saat çipinin —
elinde). Saatin jitter'ı, faz gürültüsü eğrisinin belirli bir ofset
aralığında entegre edilmesiyle bulunur; o hesabı ve "hangi ofsetten hangi
ofsete" sorusunu kardeş kılavuz işler
({{rf:jitter-snr-in-sessiz-katili|RF Örnekleme: jitter, SNR'ın sessiz katili}}).
Almaç tasarımcısı için sonuç şudur: **örnekleme saati, RF zincirinin bir
parçasıdır** ve LO için gösterilen özen ona da gösterilir ({{bolum:11}}).

## Kavram: toplam SNR — üç gürültü, bir sayı

Kuantizasyon, termal ve jitter gürültüleri bağımsızdır; güçleri toplanır.
dB'de bu "en küçüğü kazanır"a yakın bir davranıştır: birbirinden 10 dB
uzak iki terimden büyüğü sonucu yalnızca 0.4 dB etkiler.

:::formul id=snr-toplam baslik="Toplam SNR (güç domeninde birleşim)"
f: SNR_{toplam} = −10·log_{10}( 10^{−SNR_q/10} + 10^{−SNR_{termal}/10} + 10^{−SNR_j/10} )
s: SNR_q | kuantizasyon (6.02N + 1.76) | dB
s: SNR_{termal} | ADC'nin iç termal gürültüsü (datasheet, düşük f_in) | dB
s: SNR_j | jitter tavanı (f_in'de) | dB
o: Kurgusal ADC: SNR_q = 86.0, SNR_termal = 62, SNR_j(1.8 GHz) = 58.9 → **57.2 dB**; ENOB ≈ 9.2 bit. Jitter baskın: saati 2× iyileştir → 60.3 dB; bit sayısını 16'ya çıkar → 57.2 dB (değişmez).
o: Aynı ADC 100 MHz IF'te: SNR_j = 84 dB → toplam ≈ **62 dB**, termal baskın. Baskın terimi bilmeden "daha iyi ADC" almak paranın yanlış yere gitmesidir.
:::

:::widget id=w09 ad="Jitter–SNR hesaplayıcı"
- **Referans senaryo**: üç çubuğun en kısası jitter (58.9 dB); toplam 57.2 dB, ENOB ≈ 9.2. Eğri panelinde çalışma noktası "jitter köşesinin" (≈ 1.27 GHz) sağında — bu f_in'de saat baskın. Bit sayısını 14'ten 16'ya çıkar: hiçbir çubuk hariç kuantizasyon değişmesin, toplam aynı kalsın.
- Jitter'ı 100 fs'ten 50 fs'e indir: jitter çubuğu 6 dB uzasın, toplam ≈ 60.3 dB'ye çıksın; 25 fs'te termal baskın hale gelsin (toplam 61.8). "Bu f_in'de jitter'ın görünmez kalması için σ ≤ 70 fs" satırını oku.
- **Direct RF 9.4 GHz** preset'i: toplam 44.5 dB, ENOB 7.1 — aynı saat, aynı ADC, yalnızca giriş frekansı 5.2 kat yüksek. **Düşük IF (100 MHz)** ile karşılaştır: 62 dB, jitter görünmez.
- Bandı 300 MHz'den 2 MHz'e daralt: işlem kazancı 6 → 27.8 dB, bant içi SNR 85 dB'ye çıksın — ama bunun spur'lar ve jitter'ın yakın gürültüsü için geçerli olmadığını hatırla.
:::

## Kavram: doğrusalsızlık, interleaving, clipping

**INL/DNL.** İdeal cetvelin bölmeleri eşittir; gerçek ADC'de her kodun
genişliği ideal LSB'den sapar (**DNL**, differential nonlinearity) ve
sapmalar birikerek transfer eğrisini düz çizgiden uzaklaştırır (**INL**,
integral nonlinearity). DNL büyükse bazı kodlar hiç çıkmaz (missing code)
ve küçük sinyalde gürültü tabanı bozulur; INL, transfer eğrisinin
eğriliğidir ve **harmonik** üretir — HD2/HD3'ün bir kaynağı budur, diğeri
giriş tamponunun doğrusalsızlığıdır. INL periyodik yapıdaysa (pipeline'ın
kademe sınırları) spektrumda harmonik olmayan düzenli spur'lar da çıkar.
Kaba kural: 14-bit ADC'de 1 LSB'lik INL ≈ −84 dBc mertebesinde spur demektir.

**Time-interleaving.** GSPS sınıfı ADC'lerin hemen hepsi içeride M çekirdeği
sırayla çalıştırır; her çekirdek fs/M hızındadır. Çekirdekler birebir aynı
olmadığından üç imza bırakırlar: ofset farkı → k·fs/M'de sinyalden bağımsız
tonlar; kazanç farkı → k·fs/M ± f_in'de image'lar; örnekleme anı farkı
(skew) → yine k·fs/M ± f_in'de, f_in ile büyüyen image'lar. Konumlarını
{{bolum:8}}'de hesapladık; mekanizma aşağıda. Seviyeleri için kaba kurallar:
%0.5 kazanç farkı ≈ −52 dBc image; 1 ps skew 600 MHz'de ≈ −55 dBc. Modern
cihazlar bunları **çip içi kalibrasyonla** −75 … −85 dBc'ye bastırır; o
kalibrasyonu başlatan, tamamlanmasını bekleyen ve sıcaklık değişince
yenileyen senin sürücündür ({{rf:interleaved-adc-hiz-hilesi-ve-bedeli|RF Örnekleme: interleaved ADC}}).

{{svg:g-93-interleaving-spur.svg|Time-interleaving spur mekanizması. Solda zaman: dört çekirdek (A, B, C, D) sırayla örnekler; B'nin ofseti ve kazancı farklı, D'nin örnekleme anı kaymış — hata dizisi fs/4 periyotlu. Sağda hesaplanmış spektrum (fs = 2400 MSPS, f_in = 450 MHz): ofset spur'ları 600 ve 1200 MHz'de sinyalden bağımsız; kazanç/zamanlama image'ları fs/4 ± f_in ve fs/2 − f_in konumlarında (150, 750, 1050 MHz). Referans senaryoda f_in = fs/4 olduğu için bu ailenin iki üyesi sinyalin tam üstüne düşer.}}

**Clipping ve overrange.** Tam ölçeği aşan giriş, kodun tavanına yapışır;
sinüsün tepesi kesilir ve spektrum harmoniklerle dolar — 3 dB aşımda SFDR
20 dBc'ye çöker (widget'ta gör). Bu bir "biraz daha gürültü" durumu değil,
**ölçümün geçersiz olduğu** durumdur: PA yanlış (doyma seviyesinde takılı),
frekans ölçümü harmoniklerle kirlenmiş, yanındaki zayıf darbe intermod
ürünlerinin altında kaybolmuş. Bu yüzden her RF ADC bir **overrange
bayrağı** üretir (örnek başına bir kontrol biti, JESD204'te CS biti ya da
ayrı bir pin/register) ve PDW'ye "doydu" bayrağı olarak taşınır
({{bolum:24}}). Almaçta çözüm ADC'de değil, öncesindeki kazanç kontrolündedir
({{bolum:5}}).

## Kavram: ADC'nin eşdeğer gürültü şekli ve önündeki kazanç

ADC'yi zincirin son bloğu gibi düşünüp ona bir **gürültü şekli (NF)**
atayabilirsin: ADC'nin kendi gürültüsünü, girişindeki kTB'ye göre ölçersin.
Sonuç şaşırtıcı derecede kötü bir sayıdır — 30 dB civarı — ve tam da bu
yüzden ADC'nin önünde 40 dB kazanç vardır: Friis ({{bolum:4}}) ADC'nin
gürültüsünü önündeki kazanca böler.

:::formul id=adc-nf baslik="ADC eşdeğer gürültü şekli ve zincire katkısı"
f: N_{ADC} = P_{FS,dBm} − SNR_{toplam} − 10·log_{10}(f_s / 2)  dBm/Hz        NF_{ADC} = N_{ADC} − (−174)
f: NF_{zincir} = 10·log_{10}( F_{önuç} + frac{F_{ADC} − 1}{G_{önuç}} )
s: P_{FS,dBm} | tam ölçek sinüs gücü | dBm
s: SNR_{toplam} | ADC'nin Nyquist bandındaki SNR'ı | dB
s: F_{önuç}, G_{önuç} | ADC öncesi zincirin gürültü faktörü ve kazancı (lineer) | —
o: FS = {{s:adc.tam_olcek_dbm}} dBm, SNR = 57 dB, f_s/2 = 1.2 GHz → N_ADC = 4 − 57 − 90.8 = **−143.8 dBm/Hz** → NF_ADC ≈ **30.2 dB**.
o: Ön uç Friis NF'i {{s:on_uc.nf_friis_db}} dB, kazanç {{s:on_uc.kazanc_toplam_db}} dB → ADC ile zincir NF'i ≈ **3.65 dB**; ADC yalnızca 0.2 dB ekler. LNA öncesi ≈ 1 dB kayıp ve pay ile bütçe **{{s:on_uc.nf_toplam_db}} dB** — Bölüm 4'teki "6 dB"nin hesabı budur.
:::

Kazancı ayarlamanın iki ucu vardır ve arada durursun. **Az kazanç**: analog
gürültü ADC'nin tabanının altında kalır, ADC baskın gürültü kaynağı olur,
sistem NF'i bozulur. Kural: analog gürültü tabanı ADC'nin tabanının en az
10 dB üstünde olsun (senaryoda 15.8 dB; ADC katkısı 0.1 dB). **Çok kazanç**:
güçlü emiterler ADC'yi doyurur, overrange, intermod, komşu darbeler
maskelenir. Senaryoda −60 dBm'lik darbe ADC girişinde −24 dBFS'tir; tam
ölçeğe 24 dB pay var, yani −36 dBm'den güçlü bir emiter doyurur. EH
almacında bu pay bilinçli tutulur: dinamik aralık, hassasiyetten daha
değerli olabilir; STC/AGC ({{bolum:5}}) bu payı sahneye göre oynatır.

## Datasheet okuma rehberi

Aşağıdaki tablo, kurgusal bir RF ADC'nin ("XADC-14G", **öğretici, gerçek
bir ürün değil**) datasheet ilk sayfasıdır. Sağ sütun her satırın almaç
için ne anlama geldiğini söyler.

{{tablo: genis}}
| Satır (datasheet ilk sayfa) | Kurgusal değer | Ne okumalısın |
|---|---|---|
| Resolution | 14 bit | Etiket. ENOB satırına bak. |
| Max sample rate | 3.0 GSPS | Senaryoda 2.4 GSPS ile çalışıyoruz; fs düşükken güç ve NSD biraz iyileşir. |
| Analog input bandwidth (−3 dB) | 6 GHz | Bant geçiren örnekleme için üst sınır; 1.95 GHz rahat, 9.4 GHz direct RF için yetersiz ({{bolum:10}}). |
| Full-scale input | 1.0 Vpp diff (+4 dBm, 50 Ω) | dBFS ↔ dBm sabiti: −4 dB. |
| SNR @ 900 MHz, −1 dBFS | 60 dBFS | Düşük f_in'de termal baskın; 1.8 GHz'te jitter ile 57'ye iner (grafik sayfasındaki SNR-vs-f_in eğrisine bak). |
| NSD @ 900 MHz | −151 dBFS/Hz | Bandına çevir: 300 MHz'te −151 + 84.8 = −66 dBFS gürültü. |
| SFDR @ 900 MHz | 72 dBc (HD3) | En kötü spur HD3; bandın içine katlanır ({{bolum:8}}). dBc olduğuna dikkat: −20 dBFS sinyalde spur −92 dBFS. |
| HD2 / HD3 | −78 / −72 dBc | Giriş seviyesiyle 2:1 ve 3:1 ölçeklenir; girişi 6 dB kıs, HD3 12 dB dBc kazan. |
| Interleaving spurs (kalibrasyon sonrası) | −78 dBc | Kalibrasyon şartlı; sıcaklıkla bozulur, sürücü yeniler. |
| Aperture jitter | 55 fs rms | Bütçenin ADC payı; saat çipinden gelen ile karesel toplanır. 100 fs toplam için saat ≤ 84 fs. |
| ENOB @ 900 MHz | 9.6 bit | Gerçek çözünürlük. 14 değil. |
| IMD3, iki ton −7 dBFS | −75 dBc | Yoğun ortamda sahte darbe seviyesi. |
| Input impedance | 100 Ω diff | Sürücü ve AAF tasarımının girdisi. |
| Interface | JESD204B, 8 lane, 12.5 Gbps/lane maks | 2.4 GSPS × 16 bit = 38.4 Gbps → 8 lane × 6 Gbps ({{bolum:11}}). |
| Integrated DDC | 4 kanal, NCO 32 bit, decimation 2–32 | Çip içi DDC; FPGA'daki ile aynı matematik ({{bolum:15}}). |
| Power | ≈ 3 W | Soğutma ve kart bütçesi; fs ile ölçeklenir. |

Okuma sırası: (1) giriş bant genişliği ve fs — frekans planına sığıyor mu;
(2) NSD — bandındaki gürültü, hassasiyet; (3) SFDR ve IMD3 — dinamik aralık,
yoğun ortam; (4) jitter — saat bütçesi; (5) ENOB — gerçek çözünürlük; (6)
arayüz ve DDC — FPGA tarafı. Grafik sayfalarında mutlaka **SNR/SFDR-vs-f_in**
eğrisine bak; ilk sayfadaki sayı o eğrinin en iyi noktasıdır.

:::pasaport durak="ADC çıkışı" alan=sayisal
!Alan: sayısal (ADC → arayüz)
!Frekans: {{s:adc.alias_mhz}} MHz merkez (450–750 MHz), evrik
Tip: reel
!fs: {{s:adc.fs_msps}} MSPS
!Bit: {{s:adc.bit}} bit (ENOB ≈ 9)
!Veri hızı: {{s:adc.fs_msps}} × {{s:adc.bit}} = {{s:adc.veri_hizi_gbps_14bit}} Gbps ({{s:adc.veri_hizi_gbps_16bit_paket}} Gbps 16-bit paketle)
Seviye: −24 dBFS tepe (darbe), tam ölçeğe 24 dB pay
!Gürültü: analog −47.2 dBFS ⊕ ADC −63 dBFS ≈ −47.1 dBFS (300 MHz'te) — analog baskın
SNR: ≈ 23 dB (300 MHz bantta), ADC katkısı < 0.2 dB
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
RF tasarımcı için ADC, NF'i 30 dB olan ve tam ölçeği +4 dBm'de biten bir
"son kat"tır. Önündeki kazanç bu iki sayı arasında seçilir: gürültü tabanını
ADC tabanının 10–15 dB üstüne çıkar, en güçlü beklenen emitere 10–20 dB pay
bırak; ikisi aynı anda olmuyorsa STC/AGC ya da iki kazanç kademeli mimari.
Jitter bütçesi RF tasarımcının işidir: ADC aperture 55 fs + saat 80 fs →
toplam ≈ 100 fs; saat çipinin faz gürültüsü maskesi buna göre yazılır
({{bolum:11}}). AAF'nin bant dışı bastırması ve sürücünün doğrusallığı
datasheet SFDR'ını sahada tutmanın şartıdır.
::fpga::
FPGA tarafında ADC'nin gürültüsü "doğal" gürültü tabanıdır; ilk kural, onun
altına inen bir bit budamamaktır. 14 bit ENOB 9 demek, alt 4–5 bitin
gürültü olduğu demektir — ama o bitler DDC'nin işlem kazancı için gereklidir
(300 MHz'e inince 6 dB, yani 1 bit geri gelir; {{bolum:12}} ve
{{bolum:16}}). Overrange bitini örnekle birlikte taşı: JESD204'te CS biti
olarak gelir ya da ayrı bir pin'den yakalanır; darbe FSM'i ({{bolum:24}})
bu biti PDW bayrağına yazar. Interleaving spur'larının bant içinde
olduğunu biliyorsan ({{bolum:8}}) tespit eşiğinin ({{bolum:23}}) o
frekanslarda maskelenmesi gerekebilir — bu, PS'in yazdığı bir "spur
maskesi" tablosudur.
::yazilim::
Yazılımcının ADC ile üç teması: (1) **başlatma**: kalibrasyonu tetikle,
"done" bitini bekle, sıcaklık eşiği aşılınca yenile; (2) **seviye**:
overrange sayaçlarını periyodik oku, kazanç kademesini ona göre ayarla
({{bolum:30}}); (3) **birim**: dBFS ↔ dBm çevirisini FS ve zincir kazancıyla
yap, kalibrasyon tablosundan oku. "ADC değeri × sabit = dBm" yazan sürücü,
kazanç kademesi değişince yanlış PA raporlar. ENOB'u aklında tut: PDW'deki
PA alanına 0.01 dB çözünürlük koymak (10 bit, 0.25 dB LSB yeter,
{{bolum:24}}) 9 bitlik bir ölçümü süslemektir.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>
#include <math.h>

/* dBFS <-> dBm: tam ölçek ve zincir kazancı kalibrasyon tablosundan gelir.
 * Referans senaryo: fs_dbm = +4, kazanc_db = 40 → -24 dBFS ↔ -60 dBm anten girişi */
static double dbfs_to_dbm_giris(double dbfs, double fs_dbm, double kazanc_db)
{
    return dbfs + fs_dbm - kazanc_db;
}

/* Ham 14-bit örnek (ikinin tümleyeni, 16-bit sözcükte işaret uzatılmış) → dBFS.
 * Tek örnek için tepe değer; güç için I²+Q² ortalaması kullanılır (Bölüm 22). */
static double ornek_dbfs(int16_t kod, int bit)
{
    double tam = (double)(1 << (bit - 1));            /* 8192 (14 bit) */
    double v = fabs((double)kod) / tam;               /* 0 … 1 */
    return v > 0 ? 20.0 * log10(v) : -200.0;
}

/* Overrange politikası (kurgusal register): sayaç eşiği aşarsa kazancı bir kademe kıs */
#define ADC_OVR_CNT   0x0040   /* 1 ms'de doyan örnek sayısı, okununca sıfırlanır */
#define GAIN_STEP_REG 0x0100

static void ovr_denetle(uint32_t (*rd)(uint32_t), void (*wr)(uint32_t, uint32_t))
{
    uint32_t ovr = rd(ADC_OVR_CNT);
    if (ovr > 1000)               /* 2.4e6 örnekte 1000 → %0.04; eşik sahaya göre */
        wr(GAIN_STEP_REG, rd(GAIN_STEP_REG) + 1);   /* +1 kademe = -6 dB */
}
```

İki tuzak: `ornek_dbfs` içindeki `bit`, ADC'nin biti değil, sözcüğün
hizalamasıdır — MSB hizalı 16-bit sözcükte 14 bitlik kod 4 kat büyük
görünür ({{bolum:11}}). Ve overrange sayacı "okununca sıfırlanan"
türdense iki yerden okuma; ikinci okuyan hep sıfır görür.

:::tuzak "14 bit, 86 dB dinamik aralık demek"
Belirti: sistem gereksinimine "ADC 14 bit → 86 dB" yazılır, zayıf emiter
güçlü emiterin yanında görünmez. Gerçek üç sayıdır: gürültü tabanı için
**NSD** (bandına çevrilmiş), spur için **SFDR** (dBc, seviyeyle değişir),
komşu için **IMD3**. Kurgusal ADC'de 1.8 GHz'te SNR 57, SFDR 72; 300 MHz'lik
bantta anlık dinamik aralık gürültüye karşı ≈ 63 dB, spur'a karşı 72 dBc'dir
— 86 değil. Teklif dokümanına bit değil, bu üç sayı yazılır.
:::

:::tuzak "Gürültü tabanı yükseldi, ADC bozuldu"
Belirti: FFT tabanı bir günde 3–6 dB yükselir. ADC nadiren bozulur;
şüpheliler sırayla: (1) saat — jitter arttı mı (saat çipi kilidi, referans
kablosu, PLL bant genişliği register'ı yanlış yüklendi)? f_in'i düşürüp
taban düzeliyorsa jitter'dır. (2) Kazanç — bir kademe arttıysa analog
gürültü de artar; bu *doğru* davranıştır, dBm'e çevirince taban aynı çıkar.
(3) FFT ayarı — N ya da pencere değişti mi (taban N ile 10·log oynar). (4)
Sıcaklık — interleaving kalibrasyonu bayatladı, spur'lar yükseldi (taban
değil, çizgiler). Sıra önemlidir; en ucuz testler önce.
:::

:::tuzak Overrange bayrağını yok saymak
Belirti: güçlü bir emiter göründüğünde PDW'lerde PA sabit bir değere
yapışır, frekans ölçümleri saçılır, olmayan darbeler belirir. ADC doymuştur;
o andaki *bütün* ölçümler geçersizdir, yalnızca güçlü emiterinki değil.
Doyma örnekleri darbe FSM'inden PDW'ye bayrak olarak taşınmalı, üst katman
bayraklı PDW'leri "güvenilmez" işaretlemeli ve kazanç kontrolü sayaçtan
beslenmelidir. "Doyan darbeyi at, gerisi sağlam" düşüncesi yanlıştır:
intermod ürünleri diğer darbelerin içindedir.
:::

:::ozet
- LSB = FS / 2^N; seviyeler dBFS'te ölçülür, dBm'e geçiş FS ve zincir kazancıyla yapılır (senaryo: −24 dBFS ↔ −60 dBm girişte).
- Kuantizasyon gürültüsü ±½ LSB tekdüze → SNR_q = 6.02·N + 1.76 dB ({{s:adc.bit}} bit: {{s:turetilmis_beklenen.snr_ideal_14bit_db}} dB); küçük sinyalde çizgilere dönüşür, dither dağıtır (+3 dB gürültü).
- SNR gürültü, SINAD gürültü + bozulma, ENOB SINAD'ın bit hali, SFDR en büyük spur (dBc mi dBFS mi, bak), NSD 1 Hz'e düşen gürültü; FFT tabanı bunların hiçbiri değildir.
- İşlem kazancı 10·log(fs/2B): 1200 → 300 MHz'de {{s:turetilmis_beklenen.islem_kazanci_1200_300_db}} dB; yalnızca beyaz gürültü için.
- Jitter tavanı −20·log(2π f_in σ): 1.8 GHz, 100 fs → 58.9 dB; f_in ya da σ 2× → −6 dB. GHz girişte saat, bit sayısından önemlidir.
- Toplam SNR güç domeninde birleşir; kurgusal ADC 1.8 GHz'te ≈ 57 dB, ENOB ≈ 9. Baskın terimi bul, parayı oraya harca.
- ADC eşdeğer NF ≈ 30 dB; önündeki 40 dB kazanç bunu 0.2 dB'ye indirir. Analog gürültüyü ADC tabanının ≥ 10 dB üstünde tut, güçlü emitere pay bırak; overrange bayrağını PDW'ye taşı.
:::

:::kendini-sina
S: 12-bit bir ADC, −30 dBFS'lik bir tona kuantizasyon açısından kaç dB SNR verir? Aynı ADC'nin datasheet SNR'ı 58 dBFS ise gerçek SNR ne olur?
C: Kuantizasyon: 74.0 − 30 = 44 dB. Datasheet SNR'ı tam ölçek sinüse göredir: −30 dBFS'te 58 − 30 = 28 dB. Toplam ≈ 28 dB (kuantizasyon 16 dB üstte, görünmez). Zayıf sinyalde gürültü tabanı sabit, SNR sinyalle birlikte düşer.
S: fs = 2400 MSPS, N = 4096, dikdörtgen pencere. Datasheet SNR 57 dB ise FFT'de bin başına taban yaklaşık kaç dBFS'te görünür? Blackman-Harris ile?
C: −57 − 10·log(2048) = −57 − 33.1 ≈ −90 dBFS (dikdörtgen, ENBW 1 bin). Blackman-Harris ENBW ≈ 2 bin → +3 dB → ≈ −87 dBFS. Taban SNR değildir; N 4 katına çıkınca 6 dB daha iner.
S: Toplam jitter bütçesi 100 fs, ADC aperture jitter'ı 55 fs. Saat çipi en fazla kaç fs verebilir? 9.4 GHz'lik direct RF için aynı 57 dB'yi tutmak isteseydin toplam jitter ne olmalıydı?
C: √(100² − 55²) ≈ 84 fs. 9.4 GHz'te 58.9 dB için σ = 10^(−58.9/20)/(2π · 9.4e9) ≈ 19 fs toplam; aperture 55 fs tek başına bunu aşar — bu ADC ile o frekansta 57 dB alınamaz, ADC ve saat birlikte değişmeli ({{bolum:10}}).
S: Ön uç kazancını 40'tan 20 dB'ye düşürürsen sistem NF'i ne olur (ADC NF 30.2 dB, ön uç Friis 3.45 dB)?
C: F = 10^0.345 + (10^3.02 − 1)/10^2 = 2.21 + 10.46 = 12.7 → 11.0 dB. ADC baskın gürültü kaynağı olur; hassasiyet 7.5 dB kötüleşir. Karşılığında tam ölçeğe pay 44 dB'ye çıkar — kazanç ayarı bu iki sayı arasındaki pazarlıktır.
S: SFDR datasheet'te 72 dBc, ölçüm −1 dBFS'te. −25 dBFS'lik bir sinyal için HD3 spur'u kaç dBFS'te beklenir?
C: HD3 seviyesi sinyalin küpüyle gider: sinyal 24 dB düşünce HD3 72 dB düşer, dBc olarak 48 dB kazanır → 120 dBc; mutlak −145 dBFS — pratikte gürültü tabanının altında, görünmez. Bu yüzden SFDR'ın hangi seviyede ölçüldüğü yazılır; küçük sinyalde spur derdi harmonik değil, sinyalden bağımsız ofset spur'larıdır.
:::

:::kopru
Metrikleri okuyabiliyoruz; şimdi onları üreten silikona bakalım. Flash,
pipeline, SAR, sigma-delta ve time-interleaved mimariler hız–çözünürlük
haritasının farklı köşelerinde yaşar; "direct RF-sampling ADC" denen şey o
haritanın GSPS köşesine yerleşmiş, içine DDC ve JESD204 gömülmüş bir
pipeline/SAR ailesidir. Bölüm 10 bu aileyi ve mixer'sız almacı anlatır.
:::
