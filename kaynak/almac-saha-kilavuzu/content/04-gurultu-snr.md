# Bölüm 4 — Gürültü, SNR ve Hassasiyet
::meta onkosul=1,3 acar=5,9,21,23 blok=onuc rota=

:::neden-onemli
Sahadan soru: "Almacın hassasiyeti −68 dBm deniyor; bu sayı nereden çıktı ve
kartı soğutunca, kabloyu uzatınca, bandı açınca ne olur?" Eşik register'ına
yazdığın her değer bu sayının üstünde bir yerdedir; yanlış alarm (false alarm) oranı
({{bolum:21}}, {{bolum:23}}) bu sayının etrafındaki gürültünün
istatistiğine bağlıdır; ADC'nin kaç bit olması gerektiği ({{bolum:9}}) bu
sayı ile doyum arasındaki mesafeden çıkar. Gürültü, almacın "sıfır" çizgisi
değil, tabanıdır — ve o taban tasarımın her kararıyla oynar. Bu bölüm tabanı
fizikten (kTB) başlayıp zincir boyunca (Friis) izler ve hassasiyet denklemini
referans senaryonun sayılarıyla kurar.
:::

## Sezgi: sıcak olan her şey fısıldar

Sıcaklığı mutlak sıfırın üstünde olan her iletkende elektronlar rastgele
kıpırdar; bu kıpırtı uçlarda küçük, rastgele bir gerilim üretir. Buna
**termal gürültü** (Johnson–Nyquist gürültüsü) denir ve iki özelliği vardır:
gücü sıcaklıkla orantılıdır ve **frekansa göre düzdür** — 1 Hz'lik her
dilimde aynı güç. Yani ne kadar geniş bir bandı dinlersen o kadar çok gürültü
toplarsın: 300 MHz'lik bir pencere, 2 MHz'lik pencereden 150 kat (21.8 dB)
daha fazla gürültü içerir. Anten bu gürültüyü gökten ve yerden toplar, almacın
her kademesi üstüne kendi gürültüsünü ekler. Darbe bu fısıltının içinden
duyulabildiği kadar duyulur; "hassasiyet" tam olarak bu cümlenin sayıya
dökülmüş halidir.

:::analoji Kalabalık oda
Kalabalık bir odada bir fısıltıyı duymaya çalışıyorsun. Oda ne kadar
büyükse (bant genişliği) o kadar çok kişi konuşur ve uğultu artar. Kulağın
ne kadar iyi olursa olsun uğultunun altındakini duyamazsın; duyabildiğin en
sessiz fısıltı hassasiyetindir. Kulaklık takıp sesi açmak (kazanç) uğultuyu
da fısıltıyı da birlikte yükseltir, oranı değiştirmez. Odanın kapısını
kapatıp yalnızca bir köşeyi dinlemek (dar bant) uğultuyu azaltır — ama
fısıltı başka köşeden gelirse kaçırırsın (POI).
:::

## Kavram: kTB — gürültünün fiziği

Empedansı eşlenmiş (matched) bir yüke düşen termal gürültü gücü, Boltzmann sabiti,
sıcaklık ve bant genişliğinin çarpımıdır. Bu üçlünün en kullanışlı hali,
1 Hz'e düşen güçtür: oda sıcaklığında (290 K, sistem mühendisliğinin
standart T₀'ı) **−174 dBm/Hz**. Bu sayı, kılavuzun en sık geçen sabitidir;
her gürültü hesabı buradan başlar.

:::formul id=ktb baslik="Termal gürültü gücü (kTB)"
f: N = k · T · B      N_{dBm} = 10·log_{10}(k·T·1000) + 10·log_{10} B = **−174 + 10·log_{10} B**  (T = 290 K)
s: k | Boltzmann sabiti, 1.380649·10⁻²³ | J/K
s: T | gürültü sıcaklığı (referans T₀ = 290 K) | K
s: B | gürültü bant genişliği | Hz
s: N | eşleştirilmiş yükteki gürültü gücü | W (dBm)
o: k·T₀ = 4.00·10⁻²¹ W/Hz → **{{s:turetilmis_beklenen.ktb_dbm_hz}} dBm/Hz**. B = 1 Hz'te bir gürültü, 1 mW'ın 10¹⁷'de biri.
o: B = {{s:ddc.cikis_bant_mhz}}·2 = 300 MHz (DDC çıkış bandı) → −174 + 84.8 = **−89.2 dBm**; B = 2 MHz (1 µs darbenin ana lobu, {{bolum:3}}) → **−111 dBm**. Fark 10·log(150) = 21.8 dB.
:::

Bu, henüz almaç yokken, antenin ucundaki gürültüdür. Almaç girişinde
gördüğün her şey bunun üstüne eklenir. Dikkat: formüldeki B *gürültü* bant
genişliğidir — filtrenin gücü geçirdiği eşdeğer dikdörtgen genişlik, −3 dB
genişliği değil (keskin filtrelerde ikisi yakındır, yumuşak filtrelerde
gürültü bandı belirgin daha geniştir). Birim ayrımı da önemli: −174 dBm/Hz
bir *yoğunluktur*, dBm değil; dBm'e çevirmek için bant genişliği gerekir
({{bolum:1}}'deki dBm/Hz satırı).

## Kavram: gürültü şekli — almaç fısıltıya ne ekler

İdeal bir yükselteç sinyali ve gelen gürültüyü aynı oranda büyütür; SNR
değişmez. Gerçek yükselteç kendi gürültüsünü de ekler; çıkıştaki SNR
giriştekinden düşüktür. Bu bozulmanın ölçüsü **gürültü faktörü** F (noise
factor, lineer) ve onun dB hali **gürültü şekli** NF'dir (noise figure).
Aynı bilgiyi sıcaklık diliyle söylemek de mümkün: kademe, girişine
T_e kelvinlik ek bir gürültü kaynağı eklenmiş idealmiş gibi davranır.

:::formul id=nf baslik="Gürültü faktörü, gürültü şekli ve eşdeğer sıcaklık"
f: F = frac{SNR_{giriş}}{SNR_{çıkış}}      NF = 10·log_{10} F      T_e = T_0 · (F − 1)
s: F | gürültü faktörü (lineer, ≥ 1); giriş gürültüsü T₀ = 290 K kabulüyle | —
s: NF | gürültü şekli | dB
s: T_e | kademenin girişine indirgenmiş eşdeğer gürültü sıcaklığı | K
o: LNA NF = {{s:on_uc.kaskad.1.nf_db}} dB → F = 1.585, T_e = 290·0.585 = **170 K**; sistem bütçesi NF = {{s:on_uc.nf_toplam_db}} dB → F = 3.98, T_e = **865 K**: almaç, antenin 290 K'lık gürültüsünün üstüne yaklaşık üç katını kendisi ekler.
o: Pasif kayıplı bir eleman (kablo, filtre, limiter) için NF = kayıp: {{s:on_uc.kaskad.3.nf_db}} dB kayıplı mixer NF = {{s:on_uc.kaskad.3.nf_db}} dB. Kayıp sinyali küçültür, çıkıştaki termal gürültü ise aynı kalır (eleman kendisi 290 K'dır).
:::

Kayıp = NF eşitliği, zincirin başındaki her şeyin neden bu kadar pahalı
olduğunu anlatır: LNA'dan önceki bir dB kablo kaybı, sistem NF'ine *doğrudan*
bir dB olarak biner. Bunu birazdan Friis ile sayıya dökeceğiz.

## Kavram: Friis — zincirde gürültü nasıl birikir

Kademeler art arda dizilince toplam gürültü faktörü basit bir kuralla
birikir: her kademenin gürültüsü, kendisinden önceki toplam kazanca
*bölünerek* girişe taşınır. İlk kademe tam ağırlığıyla sayılır; ikinci
kademenin katkısı birinci kazanca, üçüncününki ilk ikisinin kazancına
bölünür. Bir kez yüksek kazançlı ve düşük gürültülü bir kademe geçildi mi,
arkadan gelenler neredeyse görünmez olur. **LNA'nın en başta olmasının
nedeni budur.**

:::formul id=friis baslik="Friis kaskad formülü"
f: F_{toplam} = F_1 + frac{F_2 − 1}{G_1} + frac{F_3 − 1}{G_1 G_2} + frac{F_4 − 1}{G_1 G_2 G_3} + …
s: F_i | i. kademenin gürültü faktörü (lineer) | —
s: G_i | i. kademenin kazancı (lineer; kayıp için < 1) | —
o: KICKOFF'un bilinen-cevap örneği: LNA (G = 20 dB, NF = 2 dB) + mixer (NF = 10 dB) → F = 1.585 + (10 − 1)/100 = 1.675 → **{{s:turetilmis_beklenen.friis_ornek_db}} dB**. Mixer'ın 10 dB'si LNA'nın arkasında 0.24 dB'ye iner.
o: Referans zincir (limiter → LNA → preselector → mixer → IF filtre → IF yükselteç → AAF), scenario.json değerleriyle → **{{s:on_uc.nf_friis_db}} dB**, kazanç {{s:on_uc.kazanc_toplam_db}} dB. Aynı bloklar, LNA en sona alınırsa → **16.5 dB**; LNA hiç yoksa → yine **16.5 dB**: sondaki LNA'nın hiçbir katkısı yoktur.
:::

{{svg:g-40-seviye-diyagrami.svg|Referans ön uç kaskadının seviye diyagramı (hesaplanmış, B = 300 MHz). Üstte blok sembolleri ve her bloğun kazanç/NF'i; altta bloktan bloğa sinyal (mavi, −60 → −20 dBm) ve gürültü (gri). Girişte SNR 29.2 dB, çıkışta 25.8 dB; fark 3.45 dB = Friis NF. Kümülatif NF satırı LNA'dan sonra neredeyse değişmez; ADC tam ölçeği altın kesikli, headroom (tepe payı) 24 dB.|kaydir}}

Seviye diyagramı Friis'in resmidir. İki çizgiye bak: sinyal her blokta
kazanç kadar iner-çıkar; gürültü ise her blokta hem kazançla ölçeklenir hem
de bloğun kendi katkısıyla biraz daha yükselir. İki çizgi arasındaki mesafe
SNR'dır ve zincir boyunca yalnızca *daralabilir*; toplam daralma NF'tir.
Şeklin altındaki kümülatif NF satırı hikâyeyi anlatır: limiter 0.5 dB,
LNA'yla 2.5 dB, sonra beş blok boyunca yalnızca +0.95 dB. Mixer'ın 7 dB'lik
NF'i LNA'nın 20 dB'si sayesinde 0.17 dB'ye inmiştir. Aynı LNA sona
gitseydi mixer ve filtreler tam ağırlıklarıyla sayılır, NF 16.5 dB olurdu:
hassasiyet 13 dB, yani menzil olarak kabaca dört kat kaybedilirdi.

### Friis 3.45 dB diyor, bütçe 6 dB — fark nerede?

Kılavuz boyunca "sistem NF = 6 dB" kullanılıyor; oysa blokların Friis
toplamı 3.45 dB. Bu bir çelişki değil, **bütçe** ile **blok hesabı**
arasındaki farktır ve gerçek projelerde her zaman vardır:

| Kalem | Katkı | Nasıl girer |
|---|---|---|
| Blok zinciri (Friis) | 3.45 dB | yukarıdaki hesap |
| LNA öncesi kablo, konektör, anten anahtarı kaybı | ≈ +1.0 dB | kayıp = NF, **doğrudan eklenir** → 4.45 dB |
| ADC'nin eşdeğer gürültüsü (kuantizasyon + termal, {{bolum:9}}) | ≈ +1 dB | ADC girişindeki analog gürültüyle güç olarak toplanır |
| Sıcaklık, üretim toleransı, yaşlanma payı | ≈ +0.5 dB | tasarım marjı; en kötü durum kartı da bütçeyi tutsun |
| **Sistem bütçesi** | **6 dB** | hassasiyet hesabında kullanılan değer |

İlk satırın altındaki 1 dB'lik kablo kalemi Friis'in "LNA öncesi her şey
tam ağırlığıyla sayılır" kuralının doğrudan sonucudur. ADC kalemi, analog
zincirin gürültüsünün ADC'nin kendi gürültüsünü ne kadar aştığına bağlıdır;
IF kazancı bu yüzden "ADC'yi doyurmayacak kadar az, ADC gürültüsünü
gömecek kadar çok" seçilir — bu takas {{bolum:9}}'da sayıyla kurulur. Sayılar
öğreticidir; gerçek bir tasarımda her kalem ölçülür.

:::widget id=w04 ad="Kaskad NF / kazanç / hassasiyet hesaplayıcı"
- **Referans senaryo**: Friis NF 3.45 dB, kazanç 40 dB, gürültü tabanı −85.8 dBm (300 MHz, yalnızca bloklar), SNR giriş 29.2 → çıkış 25.8 dB. Katkı çubuklarında en büyük payın 0.5 dB'lik limiter'da (%51 — çünkü LNA'nın önünde), LNA'da %30, mixer'da yalnızca %3 olduğunu gör. **Sistem bütçesi (6 dB)** preset'i: 1 dB ön kayıp + 1.55 dB pay → sistem NF 6.00 dB, taban −83.2 dBm, MDS −68.2 dBm.
- **LNA'yı sona al** düğmesi: NF 3.45'ten 16.5 dB'ye fırlasın; seviye diyagramında gürültü çizgisinin mixer'dan itibaren sinyale yaklaştığını izle. **LNA'yı çıkar**: yine 16.5 dB — LNA sondayken zaten işe yaramıyordu. Referansa dön, LNA kazancını 20'den 10 dB'ye indir: NF 3.45 → 7.9 dB; LNA'nın kazancı, arkadakileri ne kadar bastırdığını belirler.
- LNA öncesi kaybı 0'dan 3 dB'ye çek: Friis NF tam 3 dB artsın (her dB doğrudan). Aynı 3 dB'lik kaybı zincirin sonuna bir blok olarak ekle: NF neredeyse değişmesin.
- Bant genişliğini 300 MHz'ten 2 MHz'e indir (**Dar bant** preset'i): taban −83.2'den −105.0 dBm'e, MDS −90.0 dBm'e insin — 21.8 dB hassasiyet, bedeli {{bolum:3}}'te ve aşağıda (POI). Gereken SNR'ı 15'ten 11 dB'ye çek: MDS 4 dB iyileşsin; bu 4 dB'nin Pfa ile ödendiğini {{bolum:21}}'de göreceksin.
:::

## Kavram: gürültü tabanı, SNR ve hassasiyet

Şimdi parçaları birleştir. Almacın **gürültü tabanı**, girişine indirgenmiş
toplam gürültü gücüdür: kTB'nin üstüne sistem NF'i. Bir darbe bu tabanın
tam üstünde değil, tespit için gereken SNR kadar üstünde olmalıdır; o
seviyeye **MDS** (minimum detectable signal — en küçük tespit edilebilir
sinyal) ya da hassasiyet denir.

:::formul id=hassasiyet baslik="Gürültü tabanı ve hassasiyet (MDS)"
f: N_{taban} = −174 + 10·log_{10} B + NF  [dBm]
f: MDS = N_{taban} + SNR_{gerekli} = −174 + 10·log_{10} B + NF + SNR_{gerekli}  [dBm]
s: B | almacın gürültü bant genişliği | Hz
s: NF | sistem gürültü şekli (bütçe) | dB
s: SNR_{gerekli} | istenen Pd/Pfa için gereken tek darbe SNR'ı ({{bolum:21}}) | dB
o: B = 300 MHz, NF = {{s:on_uc.nf_toplam_db}} dB → N_taban = −174 + 84.8 + 6 = **{{s:turetilmis_beklenen.gurultu_tabani_dbm}} dBm**. SNR_gerekli = {{s:tespit.tespit_snr_db}} dB → MDS = **{{s:turetilmis_beklenen.hassasiyet_dbm}} dBm**. Gelen darbe {{s:sinyal.seviye_dbm_giris}} dBm: MDS'in 8.2 dB üstünde — tespit edilir, ama bol payla değil.
o: Aynı almaç 2 MHz bantla: taban −105 dBm, MDS −90 dBm. Aynı 15 dB SNR ile 21.8 dB daha zayıf darbeyi duyar.
:::

Dört terimin her biri bir tasarım kararıdır. −174 fizik, pazarlık yok. B,
darbenin ve emiter belirsizliğinin dayattığı bant ({{bolum:3}}, aşağıda).
NF, ön ucun kalitesi ve parası. SNR_gerekli ise tespit istatistiğinin
bedeli: yanlış alarmı milyonda bire indirmek ve darbelerin %90'ını
yakalamak isteyince tek darbe için 13–15 dB civarı gerekir; sayının kökeni
{{bolum:21}}'de. Referans senaryoda 15 dB alındı.

Tabanın bir de tavanı var. ADC'nin tam ölçeği +{{s:adc.tam_olcek_dbm}} dBm,
zincir kazancı {{s:on_uc.kazanc_toplam_db}} dB; girişe indirgenmiş doyum
seviyesi 4 − 40 = **−36 dBm**. Gürültü tabanı −83.2 dBm ile doyum −36 dBm
arasındaki 47 dB, almacın 300 MHz banttaki **anlık dinamik aralığının**
(instantaneous dynamic range) kaba üst sınırıdır: aynı anda bundan daha farklı seviyeli iki darbe, biri
gürültüde biri doyumda olmadan işlenemez. Bu koridoru genişletmenin yolları
— daha çok bit, kazanç kontrolü, daha dar bant — {{bolum:5}} ve {{bolum:9}}'un
konusu; burada yalnızca koridorun iki duvarını göstermiş olduk.

## Kavram: bant genişliği ↔ hassasiyet ↔ POI — EH almacının ikilemi

{{svg:g-41-bant-gurultu-tabani.svg|Bant genişliği ile gürültü tabanı ve hassasiyet. Solda logaritmik bant genişliği ekseninde kTB·B, NF = 6 dB ile taban ve +15 dB ile MDS; 2 MHz, 300 MHz ve 1 GHz noktaları işaretli — her on kat bant tabanı 10 dB yükseltir. Sağda 1 µs darbenin spektrumu üstünde iki almaç bandı: dar bant az gürültü alır ama darbenin frekansını bilmeyi gerektirir; geniş bant darbeyi nerede olursa olsun yakalar, bedeli 21.8 dB daha yüksek taban.}}

Radar almacı kendi darbesinin frekansını bilir: bandı 1/PW'ye kadar
daraltır, gürültüyü en aza indirir. EH almacı bilmez. 2 MHz'lik bir pencereyle
gökyüzünü tararsa 300 MHz'i taramak 150 adım sürer; emiter darbesi o 150
adımın yalnızca birinde yakalanır. Darbenin almaç pencereye bakarken gelme
olasılığına **POI** (probability of intercept — yakalama olasılığı) denir
ve dar bant taramada düşüktür. 300 MHz'i tek seferde dinlemek POI'yi bire
yaklaştırır; bedeli, tabanın 21.8 dB yükselmesi ve hassasiyetin −90'dan
−68 dBm'e gerilemesidir. Bu, EH almaç tasarımının **temel ikilemidir**:
hassasiyet mi, yakalama mı?

Zincirin geri kalanı bu ikilemi yumuşatmanın yollarıyla dolu. Kristal video
almacı geniş bandı kabul edip hassasiyetten vazgeçer ({{bolum:7}}); süperheterodin
almaç dar bantla tarar; kanallaştırılmış almaç bandı aynı anda birçok dar
kanala böler ve ikisini birden alır — sayısal almaçta bu kanallaştırıcının
adı FFT'dir: 300 MHz'lik bant, {{s:fft.bin_khz}} kHz'lik binlere bölününce her
binin tabanı 300 MHz tabanının 30 dB altına iner ({{bolum:18}}). Yani
"geniş bantta topla, dar bantta tespit et" mümkündür; darbenin bant genişliği
({{bolum:3}}) bunun sınırını koyar.

## Kavram: gürültünün istatistiği — Gauss, beyaz, PSD

Buraya kadar gürültüyü tek sayıyla, gücüyle tarif ettik. Eşik koyarken
({{bolum:21}}) gücü değil *dağılımı* bilmek gerekir: gürültü ne sıklıkla
eşiği aşar? Termal gürültünün üç istatistiksel özelliği vardır:

- **Gauss dağılımlıdır.** Herhangi bir anda ölçülen gerilim, ortalaması
  sıfır, standart sapması σ olan çan eğrisini izler (çok sayıda bağımsız
  elektron hareketinin toplamı — merkezi limit teoremi). σ, gürültünün rms
  gerilimidir ve σ² = gücüdür: −83.2 dBm, 50 Ω'da σ = 15.5 µV rms. Gauss'un
  kuyruğu hızla iner ama sıfır olmaz: 3σ'yı aşma olasılığı %0.27, 5σ'yı
  aşma milyonda 0.6 — Pfa hesabı bu kuyruktur.
- **Beyazdır.** Güç spektral yoğunluğu (**PSD**, power spectral density)
  ilgilendiğimiz bant boyunca düzdür: her hertz'e aynı güç, N₀ = kT·F
  W/Hz (−174 + NF dBm/Hz). "Beyaz" ışık gibi: bütün frekanslar eşit.
  Toplam güç = N₀ · B; kTB formülünün istatistik dilindeki karşılığı budur.
  Filtre gürültüyü "renklendirir" — bant dışını atar, geçirdiğinin
  toplamı N₀·B_gürültü olur.
{{svg:g-42-gurultu-istatistigi.svg|Gürültünün üç istatistik yüzü (hesaplanmış). Solda tek kanalın Gauss yoğunluğu: σ = rms, ±3σ dışı %0.27. Ortada 600 kompleks gürültü örneğinin I/Q düzlemindeki yönsüz bulutu. Sağda zarfın Rayleigh dağılımı: sıfırda sıfır, tepe σ'da, kuyruk uzun; Pfa = 10⁻⁶ için 5.26σ eşiği işaretli — Bölüm 21 ve 22'nin eşik hesabı bu kuyruk üzerinedir.}}

- **I/Q'da bağımsız iki Gauss'tur.** Gürültü, kompleks banda ({{bolum:2}})
  indirildiğinde I ve Q bileşenleri birbirinden bağımsız, her biri σ²/2
  güçlü Gauss olur. Bunun sonucu: genlik ($√(I²+Q²)$) Gauss *değil*,
  **Rayleigh** dağılımlıdır; güç ($I²+Q²$) üstel dağılımlıdır. Eşiği
  zarf üzerine koyduğumuzda ({{bolum:22}}) Pfa'yı veren dağılım Rayleigh'dir;
  {{bolum:21}}'in 5.26σ'sı oradan çıkar.

Yazılımcı için pratik karşılığı: gürültü tabanını "tek bir sayı" olarak
ölçemezsin; ölçtüğün her değer bir rastgele değişkendir. N örnek üzerinden
alınan güç ortalamasının kendi standart sapması ortalamanın $1/√N$ katıdır;
16 örnekle taban ±1 dB oynar, 1024 örnekle ±0.13 dB. CFAR'ın referans hücre
sayısının ({{bolum:23}}) neden 16'dan küçük tutulmadığı burada saklıdır.

:::pasaport durak="Ön uç çıkışı (ADC girişi)" alan=analog
Alan: analog IF
!Frekans: {{s:on_uc.if_ghz}} GHz (IF, {{bolum:6}})
Tip: reel, bant geçiren
!Bant genişliği: ≈ 300 MHz (IF filtre / AAF geçirme bandı)
!Seviye: {{s:sinyal.seviye_dbm_giris}} + {{s:on_uc.kazanc_toplam_db}} = −20 dBm (tepe)
!Gürültü: −43.2 dBm (300 MHz, sistem NF {{s:on_uc.nf_toplam_db}} dB); yalnız Friis ile −45.8 dBm
!SNR: 23.2 dB (tek darbe, tepe; girişte 29.2 dB idi)
Headroom (tepe payı): ADC tam ölçeği +{{s:adc.tam_olcek_dbm}} dBm → 24 dB
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Gürültü şekli analog tasarımcının para birimidir: LNA seçimi (NF, kazanç,
P1dB üçgeni), LNA öncesi her milimetre iletim hattı, limiter'ın kaybı,
anten anahtarı. Zincir ölçülürken **Y-faktör** yöntemi kullanılır: girişe
sıcak/soğuk (açık/kapalı) bir gürültü kaynağı bağlanır, çıkış gücünün
oranından NF çözülür. Sıcaklık NF'i kaydırır (LNA'lar sıcakta kötüleşir);
bütçedeki payın bir kısmı budur. Analog tasarımcı IF kazancını da buradan
seçer: ADC'nin gürültüsünü gömecek kadar çok, en güçlü beklenen darbeyi
doyurmayacak kadar az ({{bolum:5}}, {{bolum:9}}).
::fpga::
FPGA gürültüyü *üretmez* ama *ölçer*: gürültü tabanı tahmini, CFAR'ın
({{bolum:23}}) ve eşiğin temelidir. Gerçekleme, $I²+Q²$ güç örneklerinin
kayan ortalamasıdır ({{s:tespit.n_ref}} referans hücre); toplayıcının bit
genişliği ortalama uzunluğuna göre büyür ({{bolum:12}}). Tabanın dBm
karşılığı FPGA'yı ilgilendirmez — o yalnızca sayılarla çalışır; kalibrasyon
sabiti (0 dBFS ↔ dBm) PS tarafında tutulur. Bir de kendi gürültüsü vardır:
kuantizasyon ve yuvarlama, tabana eklenen deterministik olmayan küçük bir
katkı; doğru ölçekleme ile analog tabanın çok altında tutulur ({{bolum:12}}).
::yazilim::
Yazılımcı için hassasiyet iki sabit ve bir ölçümdür: bant genişliği (DDC
ayarından bilinir), sistem NF (kalibrasyondan) ve FPGA'nın ölçtüğü anlık
taban. Eşik register'ı tabanın kaç dB üstüne konacaksa ({{bolum:21}}) bu
hesabın çıktısıdır; sıcaklık, kazanç ayarı (AGC/STC, {{bolum:5}}) ve bant
değiştikçe yeniden hesaplanır. Bir sağlık kontrolü olarak ölçülen tabanı
$−174 + 10·log B + NF + G$ ile karşılaştırmak, "LNA öldü mü, kablo mu
gevşedi" sorusunu saniyeler içinde cevaplar: taban beklenenden 3 dB
düştüyse muhtemelen zincirin başında bir şey koptu — sinyalle birlikte
gürültü de kaybolur.
:::

## Yazılımcıya dokunan yer

```c
#include <math.h>

#define KTB_DBM_HZ   (-173.975)          /* 10·log10(k·290·1000) */

/* Girişe indirgenmiş gürültü tabanı ve MDS (dBm). */
static double gurultu_tabani_dbm(double bw_hz, double nf_db)
{
    return KTB_DBM_HZ + 10.0 * log10(bw_hz) + nf_db;
}
static double mds_dbm(double bw_hz, double nf_db, double snr_gerekli_db)
{
    return gurultu_tabani_dbm(bw_hz, nf_db) + snr_gerekli_db;
}

/* Friis: bloklar sırayla {kazanc_db, nf_db}. Döner: toplam NF (dB). */
typedef struct { double kazanc_db, nf_db; } blok_t;
static double friis_nf_db(const blok_t *b, int n)
{
    double F = 0.0, G = 1.0;
    for (int i = 0; i < n; i++) {
        double f = pow(10.0, b[i].nf_db / 10.0), g = pow(10.0, b[i].kazanc_db / 10.0);
        F = (i == 0) ? f : F + (f - 1.0) / G;      /* önceki toplam kazanca böl */
        G *= g;
    }
    return 10.0 * log10(F);
}

/* Ölçülen tabandan NF'i geri çözme (sağlık kontrolü): taban_dbm ADC girişinde,
 * zincir kazancı g_db, DDC bandı bw_hz. Kalibrasyon sabiti: 0 dBFS = +4 dBm. */
static double olculen_nf_db(double taban_dbfs, double tam_olcek_dbm, double g_db, double bw_hz)
{
    double taban_dbm_giris = taban_dbfs + tam_olcek_dbm - g_db;
    return taban_dbm_giris - (KTB_DBM_HZ + 10.0 * log10(bw_hz));
}
/* referans senaryo: gurultu_tabani_dbm(300e6, 6) = -83.2; mds_dbm(300e6, 6, 15) = -68.2
 * friis_nf_db(scenario.on_uc.kaskad, 7) = 3.45 */
```

Üç not: (1) `pow(10, x/10)` güç için, gerilim oranına çevireceksen /20;
{{bolum:1}}'in tuzağı burada da geçerli. (2) Bant genişliği DDC'nin
*gürültü* bandıdır; decimation filtresinin geçirme bandı ile eşdeğer
gürültü bandı arasında birkaç yüzde fark olabilir ({{bolum:16}}). (3)
Ölçülen taban bir istatistiktir; `olculen_nf_db` için en az birkaç bin
örneğin ortalamasını kullan, tek FFT karesinden okuma ({{bolum:18}}).

:::tuzak "Kazancı artırdım, hassasiyet arttı"
IF yükseltecinin kazancını 32'den 42 dB'ye çıkarınca FFT ekranında darbe
10 dB yükselir ve "daha iyi görüyoruz" hissi doğar. Oysa gürültü tabanı da
10 dB yükselmiştir; SNR ve dolayısıyla MDS değişmemiştir (Friis'te IF
yükselteç LNA'nın 20 dB'sinin arkasındadır, katkısı zaten küçüktü). Değişen
tek şey headroom'dur (tam ölçeğe kalan pay): ADC tam ölçeğine 10 dB yaklaşıldı, güçlü darbeler
artık kırpılır ve harmonikler üretir ({{bolum:9}}). Hassasiyet zincirin
*başında*, dinamik aralık zincirin *sonunda* belirlenir; kazanç düğmesi
ikisini birbirine karşı takas eder, ikisini birden vermez.
:::

:::tuzak "Preselector'ı LNA'nın önüne aldım, image'dan kurtuldum"
Image ({{bolum:6}}) ve güçlü bant dışı sinyaller için filtreyi LNA'nın
önüne koymak cazip gelir. Ama {{s:on_uc.kaskad.2.kazanc_db}} dB kayıplı
bir filtre LNA'nın önündeyken NF'e tam 2 dB olarak biner; arkasındayken
0.02 dB. Referans zincirde bu, 3.45 → 5.1 dB, yani 1.7 dB hassasiyet
demektir. Doğru cevap çoğu zaman ikisidir: LNA'nın önüne yalnızca
limiter/koruma ve çok düşük kayıplı geniş bir ön filtre, asıl seçici filtre
LNA'nın arkasına. Ödün gerekiyorsa sayıyla verilir: image bastırma kaç dB
kazandırıyor, NF kaç dB kaybettiriyor — ikisi de aynı birimde, aynı
hassasiyet denkleminde.
:::

:::ozet
- Termal gürültü kTB: 290 K'da −174 dBm/Hz; toplam güç bant genişliğiyle ölçeklenir (×10 bant = +10 dB). 300 MHz → −89.2 dBm, 2 MHz → −111 dBm.
- Gürültü şekli NF = SNR kaybı (dB); pasif kayıp için NF = kayıp; T_e = 290·(F−1).
- Friis: her kademenin gürültüsü önceki toplam kazanca bölünür → LNA en başta, önündeki her dB kayıp doğrudan NF'e biner. Referans zincir 3.45 dB; LNA sonda 16.5 dB.
- Sistem NF bütçesi (6 dB) = Friis (3.45) + LNA öncesi kayıp (~1) + ADC eşdeğer gürültüsü + sıcaklık/üretim payı.
- Gürültü tabanı = −174 + 10·log B + NF = −83.2 dBm (300 MHz); MDS = taban + SNR_gerekli = −68.2 dBm (15 dB). Doyum girişe indirgenmiş −36 dBm; arası anlık dinamik aralık.
- EH ikilemi: geniş bant → yüksek POI ama yüksek taban (2 → 300 MHz: +21.8 dB). Kanallaştırma (FFT) ikisini birden vermeye çalışır.
- Gürültü Gauss ve beyazdır (PSD düz, N₀ = kTF); I/Q'da bağımsız iki Gauss → zarf Rayleigh. Taban ölçümü bir istatistiktir, ±1/√N ile oynar.
:::

:::kendini-sina
S: Bant genişliği 20 MHz, NF 8 dB olan bir almacın gürültü tabanı ve 13 dB SNR ile MDS'i nedir?
C: Taban = −174 + 73 + 8 = −93 dBm; MDS = −93 + 13 = −80 dBm. Referans almaçtan (300 MHz, 6 dB) 11.8 dB daha hassas: 15 kat dar bant −11.8 dB, 2 dB kötü NF +2 dB, 2 dB düşük SNR −2 dB.
S: Zincir: 1.5 dB kayıplı kablo → LNA (G = 25 dB, NF = 1.5 dB) → 8 dB NF'li mixer. Toplam NF? Kablo LNA'nın arkasına alınsa?
C: F = 1.413 + (1.413 − 1)/0.708 + (6.31 − 1)/(0.708·316) = 1.413 + 0.583 + 0.024 = 2.02 → 3.05 dB. Kablo arkada: F = 1.413 + (1.413 − 1)/316 + (6.31 − 1)/(316·0.708) = 1.413 + 0.0013 + 0.024 = 1.438 → 1.58 dB. 1.5 dB'lik kablo önde tam 1.5 dB, arkada 0.01 dB.
S: Almacı 300 MHz'ten 30 MHz banda kanallaştırdın (on paralel kanal). Her kanalın hassasiyeti ve POI'si ne olur?
C: Her kanalın tabanı 10 dB düşer: −93.2 dBm, MDS −78.2 dBm. On kanal aynı anda dinlendiği için POI değişmez; bedeli on kat işlem donanımı ve 30 MHz'i aşan bant genişliğine sahip (kısa PW ya da geniş LFM) darbelerin kanallar arasında bölünmesidir.
S: FPGA'dan okunan gürültü tabanı sabahtan öğlene 2 dB yükseldi; sinyal seviyeleri de 2 dB yükseldi. Ne olmuş olabilir?
C: Sinyal ve gürültü birlikte kaymışsa SNR değişmemiştir; muhtemelen zincirin LNA sonrası bir yerinde kazanç arttı (sıcaklıkla kazanç değişimi, AGC adımı) ya da kalibrasyon sabiti bayat. Yalnızca gürültü yükselseydi (sinyal sabit) LNA öncesi NF bozulması ya da harici girişim düşünülürdü. Teşhisin anahtarı iki sayıyı birlikte okumaktır.
:::

:::kopru
Gürültünün nereden geldiğini ve zincirin başının neden bu kadar önemli
olduğunu biliyorsun. Şimdi o zincirin başına bakma zamanı: anten, limiter,
LNA, preselector — Bölüm 5 RF ön ucun bloklarını tek tek açar, kazanç
kontrolü ve doyum sorunlarını bu bölümdeki koridorun iki duvarı arasına
yerleştirir ve Friis'te kullandığımız sayıların gerçek bir tasarımda nasıl
seçildiğini gösterir.
:::
