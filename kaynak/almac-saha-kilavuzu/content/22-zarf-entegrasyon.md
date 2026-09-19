# Bölüm 22 — Zarf Çıkarımı ve Entegrasyon
::meta onkosul=2,12,16,21 acar=23,25,26 blok=zarf rota=sayisal

:::neden-onemli
Sahadan soru: "Karekök IP'si 18 saat gecikme ve iki DSP slice yiyor; zarf
için gerçekten gerekli mi?" Çoğu zaman hayır — ve bunu bilmek yalnızca kaynak
tasarrufu değildir. Tespit kararı, PA ölçümü ve eşik birimi, zarfı *nasıl*
hesapladığına bağlıdır: güç mü, genlik mi, dB mi? Sonra ikinci soru gelir:
"Zarfın üstüne kaç örneklik kayan ortalama koyalım?" Bu sayı gürültüyü
sakinleştirir, eşiği aşağı çeker, hassasiyeti artırır — ve aynı anda
darbenin kenarını yayar, TOA'yı geciktirir, kısa darbeleri yutar. Bu bölüm
I/Q çiftinden tek bir "ne kadar enerji var" sayısına giden yolu, ucuz
yaklaşımları ve "kaç örneği bir karara sığdırmalı" pazarlığını anlatır.
:::

## Sezgi: dönen okun uzunluğu

{{bolum:2}}'de kompleks örneği dönen bir ok (fazör) olarak görmüştük: I yatay
izdüşüm, Q düşey izdüşüm. Darbenin taşıyıcısı NCO'nun frekansından biraz
farklıysa ok her örnekte biraz döner; I ve Q tek tek sinüs gibi salınır ve
"darbe" I'ya ya da Q'ya bakarak görünmez bile. Ama okun **uzunluğu** dönüşten
etkilenmez: darbe boyunca sabittir, darbe yokken gürültünün küçük rastgele
uzunluğuna düşer. Zarf çıkarımı, oku unutup uzunluğunu almaktır. Tespit ve
PA ölçümü uzunluğa bakar; frekans ve faz ölçümü ({{bolum:25}}) okun *yönüne*
bakar — ikisi aynı I/Q'dan beslenir, biri diğerini bozmaz.

:::analoji Pozometre
Fotoğraf makinesinin pozometresi ışığın dalga yapısını, fazını, rengini
ölçmez; yalnızca gelen enerjiyi toplar ve "ne kadar parlak" der. Zarf
dedektörü almacın pozometresidir: taşıyıcının nerede olduğunu, fazının ne
yaptığını bilmeden "burada enerji var mı" sorusuna cevap verir. Kayan
ortalama ise pozlama süresidir: uzun pozlama gürültüyü (kumlanmayı) azaltır
ama hareket eden şeyi (darbenin kenarını) bulanıklaştırır.
:::

## Kavram: genlik, güç, log — üç zarf, tek bilgi

Kompleks örneğin büyüklüğünü üç eşdeğer ölçekte yazabilirsin ve her biri
zincirde başka bir yerde işine yarar:

:::formul id=zarf-uc-olcek baslik="Zarfın üç ölçeği"
f: P = I^2 + Q^2        (güç, kare-yasa)
f: r = sqrt{I^2 + Q^2} = sqrt{P}        (genlik / doğrusal zarf)
f: L = 10 · log_{10} P = 20 · log_{10} r        (log-zarf, dB)
s: I, Q | DDC çıkışı örnek çifti | LSB (16 bit işaretli)
s: P | anlık güç | LSB² (31 bit tam, kırpılarak 20 bit)
s: r | genlik | LSB (17 bit)
s: L | dB cinsinden güç; referans tam ölçek → dBFS | dB
o: I, Q 16 bit → I² ve Q² 30'ar bit, toplam 31 bit (işaretsiz); tam ölçek ton (genlik 32767) P = 2^30 ≈ 0 dBFS. Referans senaryoda üst **20 bit** tutulur (bit 29…10; alt 10 bit atılır, en üst bit yalnızca kırpılmış girişte set olur → doyurulur): en küçük adım 2^10 LSB² = −60 dBFS. Gürültü tabanı ADC girişinde {{s:turetilmis_beklenen.gurultu_tabani_dbm}} + {{s:on_uc.kazanc_toplam_db}} − {{s:adc.tam_olcek_dbm}} ≈ −47 dBFS'tir, adımın 13 dB üstünde: gürültü ≈ 20 seviyeyle temsil edilir, yeterli.
o: Pfa = 10⁻⁶ eşiği güç ölçeğinde ortalama gürültünün **13.8 katı** (11.4 dB üstü), genlik ölçeğinde σ'nın 5.26 katı — aynı karar, farklı sayı ({{bolum:21}}).
:::

{{svg:g-220-iq-zarf.svg|I/Q'dan zarfa üç panel (hesaplanmış, SNR = 15 dB, artık taşıyıcı 4 MHz). 1) I ve Q örnekleri: darbe içinde ikisi de salınır, tek başına anlamsız. 2) Güç zarfı I²+Q²: darbe düz bir platoya dönüşür (≈ 31.6 × gürültü gücü), eşik gürültü ortalamasının 13.8 katında (Pfa = 10⁻⁶). 3) Log-zarf: aynı şey dB ekseninde; eşik gürültünün 11.4 dB üstünde sabit bir çizgi. Üstel dağılımlı gürültünün log'u aşağı doğru uzun kuyrukludur — derin çukurlar normaldir, arıza değil.}}

**Karekök çoğu zaman gereksizdir.** Karekök tekdüze artan bir fonksiyondur:
$r > T$ ile $P > T^2$ *aynı* karardır. Eşiği güç biriminde yazarsan
karşılaştırıcı doğrudan $I^2+Q^2$ ile beslenir; iki çarpma, bir toplama, sıfır
gecikme fazlası. Karekök yalnızca genliğin *doğrusal* halinin gerektiği
yerlerde lazımdır — örneğin AM modülasyon derinliği ölçmek ya da genliği
doğrusal ölçekte raporlamak istiyorsan. PA ölçümü için de gerekmez, çünkü PA
dB cinsinden raporlanır ({{bolum:25}}, PDW'de {{s:pdw.pa_lsb_db}} dB LSB) ve
dB'ye giden yol güçten geçer: $10·log_{10}P$.

**Log-zarf** iki iş görür. Birincisi, eşiği *sabit bir ofset* yapar: gürültü
tabanı dB'de nerede olursa olsun, "tabanın 11.4 dB üstü" bir toplamadır; güç
domaininde aynı şey bir çarpmadır (α × kestirim, {{bolum:23}}). İkincisi,
dinamik aralığı sıkıştırır: 20 bitlik güç 60 dB'lik aralığı 2^20 seviyeyle
temsil ederken, 0.25 dB adımlı 10 bit aynı aralığı 256 seviyeyle temsil eder
ve PDW'ye doğrudan yazılır. FPGA'da log, karekökten daha ucuzdur: baştaki
birlerin sayısını bulan bir öncelik kodlayıcı (tam sayı kısmı, 3 dB adımlı)
artı mantis için küçük bir LUT ya da doğrusal enterpolasyon (kesir kısmı);
0.1 dB doğruluk 8–9 bitlik bir tabloyla gelir. Bedeli: log domaininde
*ortalama almak* tehlikelidir — aşağıdaki tuzağa bak.

## Kavram: ucuz genlik — alpha-max + beta-min ve CORDIC

Yine de bazen $r$ gerekir ve karekök istemezsin. İki klasik yol var.

**alpha-max + beta-min** tek satırlık bir yaklaşımdır: büyük bileşenin bir
katı artı küçük bileşenin bir katı.

:::formul id=alpha-max-beta-min baslik="alpha-max + beta-min zarf yaklaşımı"
f: r ≈ α · max(|I|, |Q|) + β · min(|I|, |Q|)
s: α, β | sabit katsayılar; ikinin kuvveti kesirleri seçilir (kaydırma ile çarpma) | —
s: |I|, |Q| | bileşenlerin mutlak değeri | LSB
o: (α, β) = (1, 1/4): en kötü hata +3.1 % / −11.6 %, ≈ 0.95 dB tepe-tepe dalgalanma; (1, 1/2): +11.8 % / 0 %; (15/16, 15/32): +4.8 % / −6.2 %, ≈ 0.53 dB; max(|I|,|Q|) tek başına: −29.3 % (45°'de, ≈ 3 dB).
o: Hata sinyalin fazına bağlıdır ve fazör döndükçe periyodik olarak tekrar eder; sabit tonlu bir darbenin PA'sı bu yüzden yaklaşım kadar "titrer".
:::

{{svg:g-221-zarf-yaklasim-hatasi.svg|alpha-max + beta-min yaklaşımlarının bağıl hatası faz açısına karşı (hesaplanmış). Hata θ = 45°'de (|I| = |Q|) simetrik olarak tekrar eder; her yöntemin en kötü ve ortalama hatası sağda. (1, 1/4) ve (15/16, 15/32) sahada en yaygın seçimlerdir: ilki iki kaydırma bir toplamadır, ikincisi 0.5 dB'nin altında kalır. CORDIC'in hatası faza bağlı değildir ama 16 pipeline kademesi ve ×1.647 kazanç düzeltmesi ister.}}

Bu yaklaşım tespit için fazlasıyla yeterlidir: 1 dB'lik dalgalanma eşik
üstündeki 13 dB'lik sinyali kaçırtmaz. Ama **PA ölçümünü** bozar — darbe
boyunca fazör döndüğü için ölçülen genlik ±0.5 dB salınır, bu da ham bir
AM modülasyonu gibi görünür. PA'yı 0.25 dB çözünürlükle raporlayacaksan
zarfı güçten ve log'dan üret, alpha-max-beta-min'i yalnızca hızlı ön kararda kullan.

**CORDIC** ({{bolum:14}}'te NCO'nun öteki yolu olarak görmüştük) burada ters
yönde çalışır: vektörü yalnızca kaydırma ve toplama ile yatay eksene döndürür;
kaç derece döndürdüğü fazı, döndürme bittiğinde kalan uzunluk genliği verir.
Genlik ve faz aynı anda çıkar — {{bolum:25}}'teki frekans ölçümü bu fazı
kullanır. 16 kademe ≈ 16 bit doğruluk; her kademe bir pipeline saati.
Çıkış sabit bir **kazanç** taşır (≈ 1.647, kademe sayısına bağlı) ve ya
katsayıyla düzeltilir ya da eşik aynı kazançla çarpılarak yutulur. Kaynak:
DSP slice yok, kademe başına iki toplayıcı ve bir kaydırıcı; 300 MSPS'te
fabric saatine rahat sığar.

## Kavram: video filtre — gürültüyü sakinleştirmek, kenarı yaymak

Zarf çıkışındaki her örnek ayrı bir gürültü çekilişidir; üstel dağılımın
standart sapması ortalamasına eşittir (bu yüzden log-zarf o kadar
"kıllı"dır). Tespit kararı tek örneğe bakınca her örnek bir yanlış alarm
fırsatıdır ({{bolum:21}}: 300 MSPS'te 300/s). Klasik çare **video filtre**:
zarfı L örneklik bir **kayan ortalama** (moving average) ile yumuşatmak.
Analog almaçta bu, diyot dedektörünün ardındaki RC alçak geçirendir; sayısal
almaçta L uzunluğunda bir kutu filtre.

:::formul id=video-filtre baslik="Kayan ortalama: varyans, kenar, gecikme"
f: y[n] = frac{1}{L} · ∑_{k=0}^{L−1} x[n−k]
f: σ_y^2 = frac{σ_x^2}{L}   (bağımsız örnekler)      kenar yayılması = L − 1 örnek      gecikme = frac{L − 1}{2} örnek
s: L | filtre uzunluğu (örnek) | —
s: σ_x, σ_y | giriş ve çıkış gürültü standart sapması (güç ölçeğinde) | LSB²
o: L = {{s:tespit.video_filtre_uzunluk}} (referans senaryo): gürültü std yarıya iner (−3 dB dalgalanma), kenar 3 örnek = 10 ns yayılır, gecikme 1.5 örnek = 5 ns. 1 µs'lik (300 örnek) darbe için ihmal edilebilir; 20 ns'lik (6 örnek) bir darbe için değil.
o: L = 64: std 8 kat düşer ama 15 örneklik (50 ns) gerçek yükseliş kenarı ≈ 79 örneğe (260 ns) uzar; PW ölçümü −3 dB tanımına göre onlarca ns kayar.
:::

{{svg:g-222-video-filtre.svg|Video filtre uzunluğunun etkisi (hesaplanmış; 300 örneklik, 15 örnek yükselişli, 15 dB darbe; gürültü gücü ortalaması 1). Solda ön kenar: L = 1, 4, 16, 64 için kenar hem yayılır hem gecikir; eşik çizgisi L = 1 için 13.8. Sağda bütün darbe: L = 16'da plato ve taban sakinleşir. Lejantta ölçülen gürültü std'si teorik 1/√L ile yan yana. Referans senaryonun L = 4'ü kenara yalnızca 3 örnek ekler.}}

Filtrenin görünmeyen ikinci etkisi, **eşik matematiğini değiştirmesidir.**
Tek örnekte güç üstel dağılımlıydı ve Pfa = 10⁻⁶ için eşik ortalamanın 13.8
katıydı. L bağımsız üstel örneğin ortalaması artık üstel değil, **gama**
(ki-kare, 2L serbestlik dereceli) dağılımlıdır; kuyruğu çok daha hızlı söner.
Aynı 10⁻⁶ için eşik çarpanı L = 2'de 8.3, L = 4'te **5.3** (7.3 dB), L = 8'de
3.7, L = 16'da 2.7'ye iner. Yani 4 örneklik filtre eşiği 11.4 dB'den 7.3
dB'ye, 4 dB aşağı çeker; darbe platosu ortalama alınca değişmediğinden bu 4
dB doğrudan hassasiyete yazılır — bir sonraki başlıktaki "entegrasyon
kazancı"nın somut hali. Bedel, kenar ve gecikme. Yazılımcı için sonuç: **eşik
çarpanı L'ye bağlıdır**; L register'ını değiştirip eşiği aynı bırakırsan Pfa
mertebelerce oynar (L'yi artırınca yanlış alarm biter ama Pd düşer, azaltınca
tersi).

## Kavram: koherent ve non-koherent entegrasyon

Video filtre bir **non-koherent entegrasyon** örneğidir: zarf alındıktan
*sonra*, faz bilgisi atıldıktan sonra örnekler toplanır. Alternatifi
**koherent entegrasyon**: I/Q örneklerini faz bilgisi *korunarak* toplamak
(kompleks toplama). Fark büyüktür:

:::formul id=entegrasyon-kazanci baslik="Entegrasyon kazancı"
f: G_{koh} = 10 · log_{10} N        (kompleks toplam; sinyal fazörleri hizalıysa)
f: G_{nonkoh} ≈ 10 · log_{10} N − kayıp(N, Pd, Pfa)      (zarf sonrası toplam; kabaca 5–8 · log_{10} N)
s: N | toplanan örnek (ya da darbe) sayısı | —
s: G | aynı Pd/Pfa için gereken tek-örnek SNR'ındaki azalma | dB
o: Koherent, N = 300 (1 µs darbenin tüm örnekleri, taşıyıcı biliniyorsa): 10·log10(300) = **24.8 dB**. Radarın eşlenik filtresi budur.
o: Non-koherent, N = 4 (video filtre), Pd = 0.9, Pfa = 10⁻⁶ (Albersheim): gereken SNR 13.1 → 8.0 dB, kazanç **≈ 5.2 dB** (koherent 6.0 dB olurdu). N = 16 için ≈ 9.5 dB (koherent 12.0). Fark N büyüdükçe açılır.
:::

Koherent toplama neden daha çok kazandırır? Gürültü fazörleri rastgele
yönlüdür, N tanesini toplarsan güçleri toplanır (N kat); sinyal fazörleri
aynı yöndeyse *genlikleri* toplanır, gücü N² kat artar; oran N kat, yani
10·log N. Non-koherent toplamda sinyal de gürültü de güç olarak toplanır;
kazanç yalnızca gürültünün *dalgalanmasının* azalmasından gelir, daha
mütevazıdır ve N büyüdükçe verimi düşer.

Koherent toplamanın şartı, sinyal fazörlerinin "aynı yönde" olmasıdır — yani
sinyalin taşıyıcı frekansını ve faz yapısını *önceden bilmen*. Bu, radar ile
EH almacı arasındaki temel ayrımdır ({{bolum:0}}): **radar kendi gönderdiği
dalga şeklini bilir**, gelen ekoyu onun eşleniğiyle süzer (matched filter)
ve darbe içindeki bütün örnekleri koherent toplar; 1 µs'lik darbeden 24.8 dB
alır. **EH almacı bilmez**; taşıyıcı ±150 MHz içinde herhangi bir yerde
olabilir. Bu yüzden zarf çıkarır, fazı atar ve non-koherent toplamakla
yetinir. Ara yol vardır: FFT ({{bolum:18}}) aslında her bin için ayrı bir
koherent entegratördür — 1024 noktalık FFT, o bin'e düşen tona
{{s:fft.islem_kazanci_db}} dB işlem kazancı verir; frekansı bilmeden, tüm
frekansları aynı anda deneyerek. Zaman kolundaki zarf dedektörü ile frekans
kolundaki FFT'nin PDW'de neden birleştiği burada anlaşılır: biri hızlı ve
geniş, diğeri yavaş ve hassastır.

:::pasaport durak="Zarf çıkışı" alan=sayisal
Alan: sayısal (FPGA)
!Büyüklük: güç, $I^2+Q^2$ (karekök yok); log-zarf opsiyonel çıkış
!Tip: reel, işaretsiz
fs: {{s:ddc.cikis_fs_msps}} MSPS (DDC çıkış hızı; video filtre L = {{s:tespit.video_filtre_uzunluk}}, decimation yok)
!Bit: 32 → 20 bit güç (üst bitler; ≈ 60 dB aralık) · log çıkışı 10 bit, {{s:pdw.pa_lsb_db}} dB/LSB
!Veri hızı: 300 M × 20 bit = 6.0 Gbps (I/Q'nun 9.6 Gbps'inden az; I/Q ölçüm için paralel devam eder)
SNR: darbe platosu / gürültü ortalaması = {{s:tespit.tespit_snr_db}} dB (bütçe); video filtre sonrası gürültü dalgalanması −3 dB
Gecikme: zarf 2–3 saat + video filtre (L−1)/2 = 1.5 örnek
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Analog almaçta zarf dedektörü bir diyot ve RC'dir: diyot kare-yasa
bölgesinde çalışırsa çıkış güçle orantılıdır (aynı $I^2+Q^2$), RC video
filtredir ve "video bant genişliği" darbenin en kısa yükseliş süresini
belirler. Sayısal zincir bu iki bloğu aynen kopyalar; fark, video filtrenin
kesin ve ayarlanabilir olması, dedektörün kırpma ve sıcaklık kayması
taşımamasıdır. Log-zarf da analog dünyadan gelir: DLVA (detector log video
amplifier) 60–70 dB'lik dinamik aralığı doğrusal bir gerilime sıkıştırır; sayısal
log-zarf aynı işi bir LUT ile yapar. RF tarafında dikkat edilecek şey, zarf
dedektörünün gördüğü "gürültünün" DDC bandının tamamı olmasıdır: 300 MHz bant,
{{s:turetilmis_beklenen.gurultu_tabani_dbm}} dBm taban. Bant daraltılmadan
zarf alınıyorsa hassasiyet bu taban tarafından belirlenir.
::fpga::
Güç: iki 16×16 çarpma (DSP slice, ya da tek slice'ta ardışık iki çarpım) ve
bir toplama; 300 MSPS'te fabric saati yetiyorsa örnek başına bir saat, aksi
halde SSR ({{bolum:12}}). Çıkış 31 bit; bit 29…10 alınır (10 bit sağa
kaydırma, yuvarlamalı; bit 30 set ise doyur). Kayan ortalama, bölme olmadan **kayan toplam** olarak
yazılır: toplam += yeni − (L örnek önceki); L ikinin kuvvetiyse ortalama bir
kaydırmadır, değilse kimse bölmez — eşik L ile çarpılır. Gecikme hattı L
derinliğinde bir SRL; toplam 20 + log2(L) bit. Log-zarf: 20 bitlik güçte
baştaki bir konumunu bulan öncelik kodlayıcı (5 bit tam sayı, 3.01 dB adım)
+ izleyen 7 bitin adreslediği 128 girişli LUT (kesir, 0.024 dB adım) → 12 bit
dB değeri; 1 BRAM'in küçük bir köşesi. alpha-max-beta-min (1, 1/4): iki
mutlak değer, bir karşılaştırma, bir kaydırma, bir toplama; 1 saat.
CORDIC vectoring 16 kademe: ≈ 16 × (2 toplayıcı + kaydırıcı), 16 saat gecikme,
DSP slice yok. Toplam zarf + video filtre gecikmesi tipik 4–6 saat + (L−1)/2 örnek;
TOA düzeltmesi için sabittir ve register'a yazılır.
::yazilim::
Yazılımcının bu durakta gördüğü register'lar: `ZARF_MODE` (güç / log / genlik
yaklaşımı), `VIDEO_LEN` (L, genellikle 1–64, çoğu tasarımda yalnız 2ⁿ),
`ZARF_SHIFT` (31 → 20 bit kırpma konumu) ve log çıkışının ölçeği (dB/LSB).
Üç iş: (1) PA'yı LSB²'den dBFS'e, oradan kalibrasyonla dBm'e çevirmek —
kırpma kaydırmasını unutmadan; (2) L'yi değiştirdiğinde eşik çarpanını
yeniden hesaplamak (gama kuyruğu, aşağıdaki tablo); (3) L'nin PW ve TOA'ya
eklediği sabit sapmayı ({{bolum:25}}) düzeltmek. En sık hata, log çıkışından
ortalama alıp güce çevirmek: −2.5 dB sistematik hata (tuzak).
:::

:::matlab-fpga
::matlab::
Model tarafında zarf ve video filtre iki satırdır; eşik çarpanı L'ye göre
gama dağılımından gelir:

```matlab
P   = abs(iq).^2;                       % güç, kare-yasa
L   = 4;
Pv  = filter(ones(1,L)/L, 1, P);        % kayan ortalama (video filtre)
% Pfa = 1e-6 için eşik / ortalama gürültü gücü (gama kuyruğu, 2L s.d.)
k   = gaminv(1 - 1e-6, L, 1/L);         % L=1: 13.8, L=4: 5.34
esik = k * mean(Pv(gurultu_bolgesi));
```
::fpga::
Aynı şeyin RTL iskeleti: bölmesiz kayan toplam, eşik L ile çarpılmış olarak gelir.

```verilog
wire [30:0] p_tam = i*i + q*q;             // 2 DSP, 1-2 saat
wire [19:0] p     = p_tam[30] ? 20'hFFFFF : p_tam[29:10]; // 20 bit, doyurmalı
reg  [21:0] top;                           // 20 + log2(L=4) bit kayan toplam
reg  [19:0] hat [0:3];                     // L derinlikli gecikme hattı (SRL)
always @(posedge clk) begin
  top    <= top + p - hat[3];              // += yeni − çıkan
  hat[0] <= p; hat[1] <= hat[0]; hat[2] <= hat[1]; hat[3] <= hat[2];
end
// karar: top > esik_x_L   (esik_x_L = k · P_ort · L, PS yazar; bölme yok)
```

Bit-true karşılaştırma ({{bolum:13}}): MATLAB `Pv*L` ile ILA'dan okunan `top`
bit bit eşit olmalı; kırpma (`[29:10]`) modelde de aynı yerde yapılmalı, yoksa
0.5 LSB'lik farklar birikip eşik kenarında farklı kararlara yol açar.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>
#include <math.h>

/* Güç yolundan PA: 20 bitlik güç register'ı, 10 bit sağa kaydırılmış.
 * Tam ölçek kompleks ton (genlik 32767) → P_fs = 32767² ≈ 2^30 LSB² (kaydırmadan önce). */
#define ZARF_SHIFT   10
#define P_FS_LSB2    1073741824.0     /* 2^30 */

static double guc_dbfs(uint32_t p_reg)
{
    double p = (double)p_reg * (1u << ZARF_SHIFT);        /* kırpmayı geri al */
    return 10.0 * log10(p / P_FS_LSB2);                    /* dBFS */
}
/* dBm = dBFS + kalibrasyon ofseti (ADC tam ölçek dBm − kazanç); kart başına ölçülür. */

/* Video filtre uzunluğuna göre eşik / ortalama gürültü gücü çarpanı, Pfa = 1e-6.
 * Gama kuyruğu (2L serbestlik derecesi) — gaminv ile üretilmiş tablo. */
static const double ESIK_KAT_1E6[] = { 13.82, 8.34, 5.34, 3.65, 2.66, 2.0, 1.71 }; /* L = 1,2,4,8,16,32,64 */

static uint32_t esik_video(uint32_t video_len_log2, double p_ort_lsb2)
{
    double k = ESIK_KAT_1E6[video_len_log2 > 6 ? 6 : video_len_log2];
    return (uint32_t)llround(k * p_ort_lsb2);   /* register bölmesiz karşılaştırıyorsa × L */
}

/* TOA / PW düzeltmesi: video filtre kenarı (L−1)/2 örnek geciktirir. */
static double video_gecikme_ns(uint32_t L, double ornek_ns) { return (L - 1) * 0.5 * ornek_ns; }
```

Tablo değerlerinden L = 32 için 2.0 yaklaşık okumadır (gama kuyruğu ile
≈ 2.1); kendi tablonu `gaminv` ile üret, elle yuvarlama. Asıl mesaj: **`VIDEO_LEN`
ile eşik register'ı bir çift olarak yazılır**; birini değiştirip diğerini
unutan yazılımcı ya yanlış alarm seline ya da sağır bir almaca uyanır.

:::tuzak Log çıkışından ortalama gürültü tabanı
Log-zarf ekranda güzel görünür, yazılımcı gürültü tabanını kestirmek için
log değerlerinin ortalamasını alır ve dB'ye çevirir. Üstel dağılımlı gücün
log'unun ortalaması, ortalamanın log'undan **2.5 dB düşüktür** (Euler
sabitinden gelen −γ·10·log10(e) = −2.51 dB). Taban 2.5 dB düşük kestirilir,
güç domaininde eşik 2.5 dB gevşek kurulur, Pfa 10⁻⁶ yerine ≈ 3×10⁻⁴ çıkar —
saniyede 100 000 yanlış alarm. Çare: ortalamayı güç domaininde al, sonra
log'a çevir; ya da log domaininde çalışacaksan medyanı kullan ve medyanın
ortalamadan 1.6 dB düşük olduğunu bilerek düzelt (üstel dağılımda medyan =
ln 2 × ortalama).
:::

:::tuzak "Video filtreyi 64'e çektim, hassasiyet 8 dB arttı"
Bir yarısı doğru: gürültü dalgalanması 8 kat düşer, eşik 11.4 dB'den 2.3
dB'ye iner. Ama üç şey birlikte olur: (1) 64 örnekten kısa darbeler (< 213
ns) platoya hiç ulaşamaz, genlikleri PW/L oranında ezilir — 30 ns'lik darbe
7 kat (8.5 dB) zayıflar, "hassasiyet artışı" kısa darbeler için kayba döner;
(2) kenar 63 örnek yayılır, TOA 105 ns gecikir, PW ölçümü onlarca ns şişer;
(3) ardışık iki yakın darbe tek darbeye yapışır. L, beklenen en kısa darbeden
kısa tutulur; referans senaryoda 4. Kısa ve uzun darbeleri birlikte görmek
istiyorsan iki paralel L ile iki dedektör çalıştırmak (kısa/uzun kanal) klasik
çözümdür.
:::

:::tuzak alpha-max-beta-min "AM modülasyonu" üretir
Taşıyıcısı NCO'dan 4 MHz uzak bir darbenin fazörü 300 MSPS'te her 75 örnekte
bir tur döner; (1, 1/4) yaklaşımı her turda ±0.5 dB'lik, 45°'de tekrar eden
bir hata çizer. Zarfa bakan biri bunu "darbe içinde 16 MHz'lik AM modülasyonu"
diye raporlar (4 MHz × dört tekrar/tur). Teşhis: NCO'yu 1 MHz kaydır —
"modülasyon frekansı" da 4 MHz kayarsa yaklaşım hatasıdır. Çare: PA ve MOP
analizini güç yolundan yap; yaklaşımı yalnızca ön karar için kullan.
:::

:::ozet
- Zarfın üç ölçeği aynı bilgidir: güç $I^2+Q^2$, genlik $√P$, log $10·log_{10}P$. Tespit için karekök gereksizdir: $r > T$ ⟺ $P > T^2$.
- Referans zincir: 16+16 bit I/Q → 32 bit güç → üst 20 bit; log çıkışı öncelik kodlayıcı + küçük LUT ile ucuzdur ve PDW'nin dB'li PA'sını doğrudan besler.
- Genlik gerekiyorsa alpha-max + beta-min ((1, 1/4) ≈ 1 dB, (15/16, 15/32) ≈ 0.5 dB, faza bağlı dalgalanma) ya da CORDIC (16 kademe, ×1.647 kazanç, faz da çıkar).
- Video filtre (L örnek kayan ortalama) gürültü varyansını L kat düşürür, kenarı L−1 örnek yayar, (L−1)/2 örnek geciktirir; L en kısa beklenen darbeden kısa seçilir (referans L = 4).
- L, eşik matematiğini değiştirir: güç artık üstel değil gama dağılımlı; Pfa = 10⁻⁶ çarpanı L = 1'de 13.8, L = 4'te 5.3, L = 16'da 2.7. `VIDEO_LEN` ile eşik birlikte yazılır.
- Koherent entegrasyon 10·log N kazandırır ama dalga şeklini bilmek ister (radar); EH almacı fazı atar, non-koherent toplar (≈ 5 dB / 4 örnek); FFT, frekansı bilmeden bin başına koherent toplamanın yoludur.
- Log domaininde ortalama alma: −2.5 dB sistematik hata; ortalamayı güçte al, sonra dB'ye çevir.
:::

:::kendini-sina
S: I = −1200, Q = 900 LSB. Güç, gerçek genlik ve (1, 1/4) yaklaşımı nedir; hata kaç dB?
C: P = 1 440 000 + 810 000 = 2 250 000 LSB²; r = 1500 LSB. Yaklaşım: 1200 + 900/4 = 1425 → −5.0 %, 20·log10(1425/1500) = −0.44 dB. Faz 36.9°'de olduğumuz için hata ne en kötü (−11.6 %, 45°'de) ne sıfır.
S: Video filtre L = 1'den 4'e çıkarıldı ama eşik register'ı değişmedi (13.8 × P_ort). Pfa ne olur?
C: L = 4'te güç gama dağılımlıdır; ortalamanın 13.8 katını aşma olasılığı 10⁻⁶'nın çok altına iner (≈ 10⁻²⁰ mertebesi) — yanlış alarm biter ama eşik gereğinden 4.1 dB yüksektir: doğru eşikle (5.3 × P_ort) Pd = 0.9 için ≈ 8 dB yeterken, eski eşikle ≈ 12 dB gerekir; video filtrenin kazancı çöpe gider. Doğrusu eşiği 5.3 × P_ort'a çekmektir.
S: Radar 1 µs'lik darbesinden 24.8 dB entegrasyon kazancı alıyor; aynı darbeyi dinleyen EH almacı neden alamıyor?
C: Kazanç koherent toplamadan gelir ve darbenin taşıyıcı frekansı ile faz yapısını önceden bilmeyi gerektirir (eşlenik filtre). EH almacı bunları bilmez; zarf alıp fazı attıktan sonra ancak non-koherent toplayabilir (4 örnekte ≈ 5 dB) ya da FFT ile her bin'de ayrı koherent toplama yapar (1024 nokta → ≈ 27 dB, ama 3.4 µs gözlem süresi ve bin başına).
S: Log-zarfın 10 000 örneklik ortalaması −45.0 dBFS çıktı. Gerçek ortalama gürültü gücü kaç dBFS?
C: ≈ −42.5 dBFS. Üstel dağılımlı gücün log ortalaması, gücün ortalamasının log'undan 2.51 dB düşüktür.
:::

:::kopru
Zarfı ve üstündeki kayan ortalamayı aldık; eşiği "gürültü ortalamasının k
katı" diye yazdık. Ama gürültü ortalaması nedir, kim ölçer, ne sıklıkla?
Kazanç, sıcaklık, bant ve ortam değiştikçe taban kayar; sabit bir sayı ya
yanlış alarm seli ya da sağırlıkla biter. Bölüm 23, tabanı sinyalin kendi
komşuluğundan kestiren CFAR ailesini, α = 21.9'un nereden geldiğini,
maskeleme ve kenar arızalarını ve eşiğin etrafına örülen pratikleri
— histerezis, minimum darbe genişliği, M-of-N — anlatır.
:::
