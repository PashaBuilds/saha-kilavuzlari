# Bölüm 0 — Bu Kılavuz ve Büyük Resim
::kisim 0 — Yön Bulma
::meta onkosul= acar=1,2,3,4 blok= rota=yazilimci,sayisal

Bir almaç kartının PS tarafında çalışıyorsan gün içinde şunları yapıyorsundur:
bir register'a eşik değeri yazmak, NCO frekansını ayarlamak, DMA ile PDW
çekmek, "false alarm neden patladı?" sorusuna cevap aramak. Her biri birkaç
satır C. Ama o birkaç satırın arkasında RF'ten sayısal işlemeye uzanan, on
yıllarda oturmuş bir düşünce zinciri var; ve o zinciri bütün olarak görmeden
yazılan kod, çalıştığında bile *neden* çalıştığını söyleyemez.

Bu kılavuz o zinciri **tek bir darbenin yolculuğu** üzerinden anlatır. Darbe
antene çarpar, yükseltilir, frekansı indirilir, sayıya çevrilir, FPGA'da
süzülür, tespit edilir, ölçülür ve bir **DTK** — Darbe Tanımlayıcı Kelime, İngilizce
literatürde **PDW** (Pulse Descriptor Word) — olarak senin `read()` çağrına düşer.
Türkiye'de ekip içi konuşmada DTK, standart ve kaynakçada PDW denir; bu kılavuz
başlıkta DTK'yı, teknik anlatımda PDW'yi kullanır — ikisi aynı şeydir. Her bölüm bu
yolculuğun bir durağıdır.

## Kimin için, ne vadediyor

Birincil okur, FPGA'lı bir almaç kartının yazılımcısı: register'ın arkasındaki
DSP'nin ne yaptığını, RF tarafın neden öyle tasarlandığını ve MATLAB modelinin
FPGA'ya nasıl indiğini bütün olarak görmek isteyen mühendis. İkincil okurlar,
DSP'ye yeni giren sayısal tasarımcı (RTL bilen, sinyal işleme teorisi zayıf) ve
RF/sistem tarafından gelip sayısal zinciri anlamak isteyen mühendis. Üç dünya —
RF, almaç/DSP, sayısal tasarım — tek anlatıda birleşir; hiçbirinde ön bilgi
varsayılmaz, hiçbirinde yüzeysel kalınmaz.

Bitirdiğinde şunları yapabiliyor olmalısın:

1. Antenden PDW FIFO'suna kadar zinciri tahtaya çizip her bloğun **neden**
   orada olduğunu söylemek.
2. RF / IF / baseband, örnekleme frekansı, Nyquist bölgesi, reel ve I/Q veri
   kavramlarını sayısal örnekle açıklamak.
3. Bir ADC datasheet'inden SNR, SFDR, ENOB, NSD, jitter değerlerini okuyup
   sisteme etkisini yorumlamak.
4. NCO → mixer → filtre → decimation zincirinde spektrumun, veri hızının ve bit
   genişliğinin nasıl değiştiğini izlemek.
5. FFT boyu, pencere, ölçekleme ve gürültü tabanı ilişkisini doğru kurmak;
   "FFT'de gürültü tabanı neden datasheet SNR'ından aşağıda?" sorusunu cevaplamak.
6. Eşik, gürültü tahmini, CFAR, Pfa/Pd ilişkisini hem sezgisel hem formülle
   anlatmak; "eşiği 3 dB indirirsem ne olur?" sorusunu cevaplamak.
7. PDW alanlarını, her alanın nasıl ölçüldüğünü ve ölçüm hatasının SNR'a
   bağlılığını bilmek; PDW'yi C'de parse etmek.
8. Almaç mimarilerini (kristal video'dan direct RF sampling'e) güçlü/zayıf
   yanlarıyla karşılaştırmak.
9. MATLAB modelinden FPGA gerçeklemesine giden akışı ve bit-true doğrulamayı
   anlamak.
10. Sahada gördüğün belirtiyi (beklenmeyen spur, patlayan yanlış alarm (false alarm) oranı, kısa
    ölçülen PW, aynalı spektrum) olası nedenlere bağlamak.

## Büyük resim: Antenden PDW'ye

Aşağıdaki poster, kılavuzun haritasıdır. Dört dünya bandı var: **RF dünyası**
(analog, altın), **veri dönüştürme** (ADC ve arayüzü), **sayısal dünya** (FPGA,
mavi) ve **yazılım dünyası** (PS, yeşil). Sayısal dünyada zincir ikiye ayrılır:
*zaman kolu* darbeyi zarfından yakalar ve ölçer; *frekans kolu* aynı darbeye
FFT ile bakar. İki kol PDW'de birleşir. Her bloğa tıklayınca ilgili bölüme
gidersin; bu şemanın küçük hali her bölümün başında "zincirdeki yerim" olarak
tekrar karşına çıkacak.

{{svg:g-00-poster.svg|Poster şema — "Antenden PDW'ye". Üstte dört dünya bandı; ortada tek bir darbenin geçtiği bloklar. Sayısal dünyada zaman kolu (zarf → gürültü tahmini → eşik → darbe FSM → ölçüm) ve frekans kolu (pencere → FFT → tepe bulma) PDW birleştirmede buluşur. Bloklar tıklanabilir.|kaydir}}

Bu zincirin hiçbir bloğu keyfî değil. LNA en başta, çünkü gürültü şekli
zincirin başında belirlenir ({{bolum:4}}). Mixer var, çünkü 9.4 GHz'i
doğrudan örneklemek yerine 1.8 GHz'e indirmek filtreleme ve ADC seçimini
kolaylaştırır ({{bolum:6}}) — ama aynı işi mixer'sız yapan direct RF-sampling
almaçlar da var ({{bolum:10}}). ADC'nin ardından NCO ve kompleks mixer gelir,
çünkü reel örnekler geniş bir bandı taşır ve bizi yalnızca içindeki dar bir
dilim ilgilendirir ({{bolum:15}}). Filtre ve decimation, veri hızını
FPGA'nın işleyebileceği ölçüye indirirken gürültüyü de azaltır ({{bolum:16}}).
Zarf ve CFAR, "darbe var mı?" sorusuna sabit bir yanlış alarm oranıyla cevap
verir ({{bolum:23}}). FFT, "hangi frekansta?" sorusunu cevaplar ({{bolum:18}}).
PDW, bütün bu ölçümlerin sabit formatlı kaydıdır ({{bolum:24}}). Kılavuz
boyunca her "neden" için bir bölüm var.

## Referans senaryo: bir darbenin pasaportu

Bütün bölümler sayısal örneklerini aynı kurgusal senaryodan alır; böylece
Bölüm 4'te hesapladığın gürültü tabanı Bölüm 23'teki eşiğe, Bölüm 8'deki alias
frekansı Bölüm 14'teki NCO ayarına dönüşür. **Sayılar öğreticidir; gerçek bir
sistemi, platformu veya tehdidi temsil etmez.**

| Parametre | Değer |
|---|---|
| Gelen sinyal | {{s:sinyal.bant}}, RF = {{s:sinyal.rf_ghz}} GHz, darbeli |
| Darbe | PW = {{s:sinyal.pw_us}} µs, PRI = {{s:sinyal.pri_ms}} ms (duty %{{s:sinyal.duty_yuzde}}); varyant B: darbe içi {{s:sinyal.varyant_b.chirp_bw_mhz}} MHz LFM |
| LO (low-side) | {{s:on_uc.lo_ghz}} GHz → IF = {{s:on_uc.if_ghz}} GHz; image = {{s:on_uc.image_ghz}} GHz |
| Ön uç (front end) | sistem gürültü şekli bütçesi NF = {{s:on_uc.nf_toplam_db}} dB, kazanç ≈ {{s:on_uc.kazanc_toplam_db}} dB |
| ADC | direct IF sampling, fs = {{s:adc.fs_msps}} MSPS, {{s:adc.bit}} bit, reel çıkış |
| Nyquist bölgesi | IF {{s:on_uc.if_ghz}} GHz → {{s:adc.nyquist_bolgesi}}. bölge ({{s:adc.bolge_alt_mhz}}–{{s:adc.bolge_ust_mhz}} MHz) → alias = {{s:adc.alias_mhz}} MHz, **spektrum evrik** (spectral inversion) |
| DDC | NCO = {{s:ddc.nco_mhz}} MHz, kompleks mixing, toplam decimation = {{s:ddc.decimation_toplam}} |
| DDC çıkışı | {{s:ddc.cikis_fs_msps}} MSPS kompleks I/Q ({{s:ddc.cikis_bit_i}}+{{s:ddc.cikis_bit_q}} bit), ±{{s:ddc.cikis_bant_mhz}} MHz |
| Zaman çözünürlüğü | {{s:ddc.ornek_suresi_ns}} ns/örnek; 1 µs darbe = {{s:ddc.darbe_ornek_sayisi}} örnek |
| Tespit | güç zarfı (I²+Q²), CA-CFAR, N = {{s:tespit.n_ref}} referans hücre, Pfa = 10⁻⁶ |
| FFT yolu | N = {{s:fft.n}}, {{s:fft.pencere}}, %{{s:fft.overlap_yuzde}} overlap → bin ≈ {{s:fft.bin_khz}} kHz |

Bu senaryodan türeyen ve kılavuz boyunca tekrar tekrar karşına çıkacak birkaç
sayı: gürültü tabanı ≈ **{{s:turetilmis_beklenen.gurultu_tabani_dbm}} dBm** (300 MHz bantta), hassasiyet
≈ **{{s:turetilmis_beklenen.hassasiyet_dbm}} dBm** (15 dB tespit SNR'ı ile), ideal 14-bit kuantizasyon SNR'ı
**{{s:turetilmis_beklenen.snr_ideal_14bit_db}} dB**, Pfa = 10⁻⁶ için Rayleigh zarf eşiği
**{{s:turetilmis_beklenen.rayleigh_esik_sigma}} σ**, CA-CFAR çarpanı **α ≈ {{s:turetilmis_beklenen.ca_cfar_alfa}}**.
Her biri ilgili bölümde adım adım türetilir.

### Sinyal pasaportu

Zincirin her durağında aynı formatta küçük bir bilgi şeridi göreceksin: sinyal
hangi alanda (analog / sayısal), frekans konumu nerede, reel mi kompleks mi,
örnekleme hızı, bit genişliği, veri hızı ve SNR. Bir duraktan diğerine
**değişen alan altınla işaretlenir**. Pasaportu durak durak izleyerek bütünü
kurarsın; {{bolum:28}} hepsini tek tabloda toplar. İlk pasaport, darbenin
antene çarptığı andaki hali:

:::pasaport durak="Anten girişi" alan=analog
Alan: analog RF
Frekans: {{s:sinyal.rf_ghz}} GHz (X-bant)
Tip: reel, bant geçiren
Bant genişliği: ≈ 2 MHz (1 µs darbe)
Seviye: {{s:sinyal.seviye_dbm_giris}} dBm (tepe)
Gürültü: kTB · B → −111 dBm (2 MHz)
SNR: henüz almaç bandına bağlı
:::

## Şema renk dili

Kılavuzdaki bütün şemalar ve widget çizimleri aynı renk dilini kullanır. Bir
kez öğren, her yerde oku:

{{svg:g-02-renk-dili.svg|Şema renk dili lejantı. Yol renkleri bloklar arası bağlantıları, spektrum renkleri frekans çizimlerini kodlar. Bu dil tema değişse de (koyu/açık) korunur.}}

| Öğe | Renk | Çizgi |
|---|---|---|
| Analog RF / IF yolu | altın | düz, kalın |
| Sayısal veri yolu (örnekler) | mavi vurgu | düz |
| Kontrol / PS / register | yeşil | ince |
| Saat / LO / referans | nötr gri | kesikli |
| Gürültü / istenmeyen bileşen | kırmızımsı | noktalı, yarı saydam |
| Spektrumda istenen sinyal | mavi | dolgu |
| Spektrumda image / alias / spur | kırmızımsı | dolgu |
| Gürültü tabanı | gri dolgu | — |
| Filtre yanıtı | altın | kesikli |

## Bölümler birbirine nasıl yaslanır

Temel ilke: **hiçbir kavram, kendisinden önce anlatılmamış bir kavrama
yaslanmaz.** Her bölümün başındaki şerit ön koşullarını ve açtığı bölümleri
listeler. Aşağıdaki harita bütün bağımlılıkları tek bakışta gösterir; bir
bölüme atlamak istiyorsan hangi düğümlerden geçmen gerektiğini buradan oku.

{{svg:g-01-bagimlilik.svg|Kavram bağımlılık haritası. Oklar "önce bunu oku" ilişkisidir; kalın düğümler birden çok kısmın yaslandığı temel bölümlerdir (1, 2, 4, 9, 12, 14, 18, 21). Renk, bölümün ait olduğu dünyayı gösterir.|kaydir}}

## Okuma rotaları

Sol menünün üstündeki üç düğme içindekileri filtreler; seçim tarayıcında
saklanır.

- **Tam yolculuk** — baştan sona, önerilen yol. Toplam okuma süresi kaba
  hesapla sekiz-on saat; laboratuvar widget'larıyla oynayarak iki katı.
- **Yazılımcı hızlı rotası** — 2, 3, 8, 9, 14–16, 18–19, 21, 23–26, 30.
  Register'a yazdığın her büyüklüğün arkasındaki teori, PDW parse ve kontrol
  yüzeyi. Ön uç ve mimari kataloğu atlanır; ama Bölüm 4'ü (gürültü) atlama, kısa
  tutulmuş ve her şey ona yaslanıyor.
- **Sayısal tasarımcı rotası** — 2, 8–9, 11–20, 22–23, 26, 29. Sabit nokta, DDC
  zinciri, FFT, CFAR ve PDW veri yolunun gerçeklemesi.

Her bölüm aynı iskeleti izler: başlık şeridi (okuma süresi, ön koşul, açtığı
bölümler) · zincirdeki yerim · neden önemli · sezgi ve analoji · kavram ·
matematik (formül kartları) · referans senaryoda sayısal örnek + pasaport ·
FPGA'da nasıl gerçeklenir · yazılımcıya dokunan yer · tuzaklar · özet kartı ·
kendini sına · köprü. Bir madde o bölüm için anlamsızsa atlanır.

:::saha-notu Widget'lar nasıl kullanılır
Kılavuzda yirmi interaktif laboratuvar var. Her birinin sol panelinde
kaydırıcılar (yanlarında aynı değeri gösteren sayı kutuları), altında
**preset** düğmeleri ("Referans senaryo" her zaman ilk sırada) ve "Ne
gözlemlemeliyim?" kutusu bulunur. Kutudaki deneyleri sırayla yap: her deney
"bu parametreyi değiştirirsem sonuca ne olur?" sorusunun cevabını gösterir.
Gürültü tohumludur (sabit seed); aynı ayar hep aynı görüntüyü verir. Widget'lar
JavaScript kapalıyken çalışmaz, yazdırırken son çizilen kare statik görüntü
olarak kalır.
:::

## Radar almacı ile EH almacı

Bu kılavuz "radar ve EH" diyor; ikisi aynı fiziği paylaşır ama farklı
sorular sorar. **Radar almacı** kendi vericisinin gönderdiği dalga biçimini
bilir: dalga biçimine uyarlanmış **matched filtre** (eşlenik filtre) kurabilir, darbeleri
koherent toplayabilir, Doppler işleyebilir. Bandı dar tutabilir çünkü nerede
bakacağını bilir. **EH almacı** (RWR, ESM, ELINT) ise sinyali *bilmez*:
frekansı, darbe genişliği, modülasyonu, geliş zamanı önceden belli değildir.
Bu yüzden geniş banda bakmak, her darbeyi tek başına yakalamak ve
parametrelerini ölçmek zorundadır; bedeli, geniş bantla gelen daha yüksek
gürültü tabanı ve daha düşük hassasiyettir ({{bolum:4}}).

| | Radar almacı | EH almacı |
|---|---|---|
| Sinyal bilgisi | Bilinen dalga biçimi (kendi vericisi) | Bilinmeyen: frekans, PW, PRI, MOP hepsi ölçülecek |
| Anlık bant genişliği | Dar (dalga biçimi kadar) | Geniş (GHz mertebesi olabilir) |
| Temel işlem | Matched filtre, koherent entegrasyon, Doppler | Tespit, parametre ölçümü, PDW üretimi |
| Öncelik | Menzil/hız doğruluğu, zayıf hedef | POI (yakalama olasılığı), tepki süresi, çok emiter |
| Hassasiyet | Yüksek (işlem kazancı büyük) | Düşük (geniş bant, tek darbe) |
| Bu kılavuzda | Farkı anlatıldığı kadar (Bölüm 7, 22, 27) | Ana eksen |

Sayısal zincir — ADC, DDC, FFT, tespit — her ikisinde de aynı yapıtaşlarından
kurulur; farkı, yapıtaşlarının nasıl ayarlandığındadır. Bu yüzden kılavuzun
büyük kısmı her iki tarafa da hizmet eder.

:::tuzak "Zaten register haritasını biliyorum"
En sık görülen yanılgı, register haritasını bilmenin sistemi bilmek olduğu.
Eşik register'ına 0x0C80 yazmak kolay; o değerin gürültü tabanının kaç dB
üstünde durduğunu, gürültü tabanının sıcaklıkla ve kazanç ayarıyla nasıl
kaydığını, Pfa'nın buna nasıl üstel bağlı olduğunu bilmeden yazılan 0x0C80
bir gün 0x0C7F olduğunda false alarm patlar ve teşhis günler sürer. Bu
kılavuz o günün maliyetini şimdiden ödemen için.
:::

:::ozet
- Kılavuz tek bir darbenin antenden PDW'ye yolculuğunu anlatır; her bölüm bir duraktır.
- Dört dünya: RF (analog, altın) → veri dönüştürme → sayısal (FPGA, mavi) → yazılım (PS, yeşil).
- Sayısal dünyada zaman kolu (zarf, CFAR, FSM, ölçüm) ve frekans kolu (FFT) PDW'de birleşir.
- Tüm sayılar tek bir kurgusal referans senaryodan gelir; sinyal pasaportu durak durak değişimi izler.
- Şema renk dili sabittir: altın analog, mavi sayısal, yeşil kontrol, gri saat, kırmızı istenmeyen.
- Hiçbir kavram anlatılmadan kullanılmaz; bağımlılık haritası ve ön koşul satırları rehberindir.
- Üç okuma rotası: tam yolculuk, yazılımcı, sayısal tasarımcı.
:::

:::kendini-sina
S: Sayısal dünyadaki iki kol hangileridir ve nerede birleşirler?
C: Zaman kolu (zarf → gürültü tahmini → eşik → darbe FSM → parametre ölçümü) ve frekans kolu (pencere → FFT → tepe bulma). PDW birleştirme bloğunda buluşurlar; her ikisinin gecikmesi hizalanarak aynı darbenin ölçümleri tek PDW'ye yazılır.
S: EH almacının radar almacına göre hassasiyetinin düşük olmasının temel nedeni nedir?
C: Sinyali bilmediği için geniş banda bakmak zorundadır; gürültü gücü bant genişliğiyle orantılı olduğundan gürültü tabanı yükselir. Ayrıca dalga biçimini bilmediğinden eşlenik filtre ve koherent entegrasyon kazancından yararlanamaz.
S: Referans senaryoda IF neden 1.8 GHz ama NCO 600 MHz'e ayarlı?
C: ADC 2400 MSPS ile örneklediğinde 1.8 GHz ikinci Nyquist bölgesine düşer ve 600 MHz'e katlanır (alias: 2400 − 1800). NCO, katlanmış konumu baseband'e taşır. Ayrıntı Bölüm 8 ve 14'te.
:::

:::kopru
Yolculuk sinyalin dilini öğrenmekle başlar: genlik, frekans, faz ve her şeyi
ölçtüğümüz birim olan dB. Bölüm 1, "−83 dBm" ifadesini okuyabilmen için
gereken her şeyi kurar.
:::
