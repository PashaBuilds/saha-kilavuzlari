# Bölüm 29 — Doğrulama ve Hata Ayıklama
::meta onkosul=8,9,13,14,16,18,23,25,26 acar=30 blok=adc,nco,esik,pdw rota=sayisal

:::neden-onemli
Sahadan soru: "Spektrumda olmaması gereken yerde bir çivi var; ADC mi, saat
mi, NCO mu, benim yazılımım mı?" Kılavuzun önceki yirmi sekiz bölümü her
bloğun ne yaptığını anlattı; bu bölüm ters yönde çalışır: **belirtiden
bloğa**. Sayısal almaçta hata ayıklamanın iyi tarafı, her durakta sinyalin
sayı olarak yakalanabilmesi; kötü tarafı, o sayıların bir ekrana düştüğünde
yirmi farklı nedenin aynı görüntüyü verebilmesi. Bu yüzden iki şey lazım:
sorunun hangi durakta doğduğunu ayıracak **test sinyalleri ve ölçüm
noktaları**, ve belirti → olası neden → kontrol üçlüsünü ezbere bilen bir
**tablo**. Bu bölüm ikisini de verir.
:::

## Sezgi: zinciri ikiye böl, tekrarla

Hata ayıklamanın en eski yöntemi ikiye bölmektir: zincirin ortasına bilinen
bir sinyal ver, çıkışa bak; doğruysa hata ilk yarıda değil, ikinci yarıdadır.
Sayısal almaçta "ortaya sinyal vermek" gerçek anlamda mümkündür: ADC yerine
FPGA içindeki **dahili test üreteci** (bir NCO + darbe zarfı) DDC'yi
besleyebilir; DDC çıkışı yerine bilinen bir I/Q dizisi tespit zincirine
enjekte edilebilir. Her ara noktada da bir **snapshot tamponu** ya da ILA ile
örnekler yakalanıp MATLAB/Python'da incelenebilir ({{bolum:13}}). Yani zincir
yalnızca ikiye değil, istediğin yerden bölünebilir. Marifet, hangi test
sinyalinin hangi hatayı görünür kıldığını bilmektir.

{{svg:g-290-karar-agaci.svg|Hata ayıklama karar ağacı. Kök soru "PDW akıyor mu?"; her dal bir test sinyali ve bir ölçüm noktasıyla ilerler, yaprakta olası neden ve ilgili bölüm yazar. Sol kol donanım/saat/arayüz, orta kol DDC/spektrum, sağ kol tespit/PDW arızaları.|kaydir}}

## Test sinyalleri: ne, neyi gösterir

{{svg:g-291-test-noktalari.svg|Enjeksiyon ve ölçüm noktaları. Üstte (altın) bilinen sinyalin zincire girebileceği dört nokta: anten, IF, DDC girişi (sayısal loopback) ve tespit zinciri (bilinen I/Q). Altta (yeşil) snapshot tamponlarının yakaladığı noktalar. Soldan sağa ilerleyerek analog nedenler dışlanır.|kaydir}}

| Sinyal | Kaynak | Neyi görünür kılar |
|---|---|---|
| **CW ton** (tek frekans, bilinen seviye) | RF üreteci antene ya da IF girişine; dahili NCO üreteci DDC'ye | Frekans zinciri (LO, NCO, bölge evrikliği, bin→Hz), kazanç/kalibrasyon (dBm↔dBFS), spur ailesi (harmonik, interleaving, NCO) |
| **Çift ton** (f₁, f₂ yakın, eşit seviye) | RF üreteci + birleştirici | Doğrusallık: IMD3 çizgileri 2f₁−f₂, 2f₂−f₁ ({{bolum:5}}); ADC ve sürücü doyumu; FFT'de iki tonu ayırma (pencere) |
| **Darbe katarı** (PW, PRI, seviye bilinen) | Darbe modülatörlü üreteç; dahili üreteç | Tespit ve ölçüm zinciri: TOA/PW/PA doğruluğu, histerezis, min PW, FIFO hızı, latency hizalaması ({{bolum:25}}, {{bolum:26}}) |
| **Gürültü** (yalnızca sonlandırıcı, 50 Ω) | Anten girişi sonlandırılır | Gürültü tabanı ve NF doğrulaması ({{bolum:4}}), Pfa ölçümü (sayaç/saniye), CFAR α doğrulaması ({{bolum:23}}) |
| **Sayısal loopback** | Test üreteci → DDC girişi, ADC devre dışı | Analog/saat sorunlarını dışlar; DDC–FFT–CFAR–PDW zincirini bit-true doğrular |
| **Bilinen I/Q dizisi** | MATLAB'dan üretilip snapshot tamponu üzerinden geri enjekte | Bit-true karşılaştırma: FPGA çıkışı = golden referans ({{bolum:13}}) |

Sıra önemlidir: önce **gürültü** (sonlandırıcı ile) — tabanı doğrula; sonra
**CW** — frekans ve seviye zincirini doğrula; sonra **darbe** — tespit ve
ölçümü doğrula; en son **çift ton** ve gerçek anten. Tabanı doğrulamadan
CW'ye geçersen "sinyal geliyor, çalışıyor" yanılgısına düşersin: sinyal 40 dB
üstte olduğu için gürültü tabanındaki 10 dB'lik hatayı göremezsin, o hata
sahada hassasiyet olarak geri döner.

## Ölçüm noktaları ve araçlar

:::uc-goz
::rf::
RF tarafında üç ölçüm noktası: anten girişi (spektrum analizörü ile ortam),
LNA çıkışı (kazanç ve NF; gürültü şekli ölçer ya da Y-faktör), ADC girişi
(IF spektrumu: image, LO sızıntısı, AAF'nin bastırması). Spektrum
analizöründe çözünürlük bant genişliğini (RBW) almacın FFT bin'ine yakın seç;
yoksa gürültü tabanları karşılaştırılamaz (taban RBW ile 10·log(RBW₁/RBW₂)
kayar — {{bolum:18}}'deki işlem kazancının analog karşılığı).
::fpga::
Sayısal tarafta ölçüm noktası demek **snapshot tamponu** demektir: ADC ham
çıkışı (SSR sözcükleri), DDC çıkışı (I/Q), zarf/güç, CFAR eşiği, FFT
büyüklükleri. Her birine bir BRAM tamponu ve tetik (yazılım ya da ilk tespit)
bağlanır; DMA ile PS'e alınır. ILA aynı işi yapar ama derinliği sınırlıdır ve
bitstream'e gömülüdür; snapshot tamponu ürün tasarımının parçasıdır ve
sahada da çalışır. Kural: **her tampona örnek sayacı ve zaman damgası ekle**,
yoksa iki tamponun aynı darbeye ait olup olmadığını anlayamazsın.
::yazilim::
PS tarafında araç zinciri: snapshot'ı dosyaya yaz (ham int16, başlığında fs,
bit biçimi, NCO, bölge bayrağı), Python/MATLAB'da oku, FFT'le, dBFS
ölçekle ({{bolum:18}}), beklenen frekansı `baseband_to_rf` ile karşılaştır
({{bolum:30}}). Şu üç betik her projede olur: `spektrum.py` (bir snapshot'ın
spektrumu + en büyük 5 tepe), `pdw_dok.py` (PDW akışını CSV'ye çöz, sıra
numarası boşluklarını say), `bit_true.py` (golden referansla fark).
:::

```python
# spektrum.py — snapshot'tan hızlı spektrum (yalnızca standart kütüphane + numpy)
import numpy as np, sys
fs, ncoHz, evrik, loHz = 300e6, 600e6, True, 7.6e9
x = np.fromfile(sys.argv[1], dtype=np.int16).astype(float).reshape(-1, 2)
z = (x[:, 0] + 1j * x[:, 1]) / 32768.0                     # Q1.15 → ±1
N = 1024; w = np.hanning(N); cg = w.mean()
X = np.fft.fftshift(np.fft.fft(z[:N] * w)) / (N * cg)       # tam ölçek ton = 0 dBFS
P = 20 * np.log10(np.abs(X) + 1e-12)
f_bb = (np.arange(N) - N // 2) * fs / N
for k in np.argsort(P)[-5:][::-1]:
    f_alias = f_bb[k] + ncoHz
    f_if = (2400e6 - f_alias) if evrik else f_alias
    print(f"{P[k]:7.1f} dBFS  bb {f_bb[k]/1e6:8.3f} MHz  →  RF {(loHz + f_if)/1e9:.6f} GHz")
```

## Belirti → neden → kontrol

Tablo, sahada en sık görülen belirtileri toplar. Her satırda en olası
nedenler sıklık sırasıyla, kontrol sütununda ise nedeni **kanıtlayan ya da
dışlayan** tek bir işlem var. Nedeni tahmin etme; kontrolü yap.

{{tablo: genis belirti-neden}}
| Belirti | Olası nedenler | Nasıl kontrol edilir |
|---|---|---|
| Spektrum aynalı: ton beklenen frekansın simetriğinde | Evrik Nyquist bölgesi düzeltilmemiş; I/Q yer değişmiş; NCO işareti ters | CW tonu +5 MHz kaydır: ölçülen ters yöne giderse evriklik. `NCO_CTRL` inversion bitini çevir ({{bolum:8}}, {{bolum:14}}) |
| DC'de (0 Hz) çivi | ADC ofseti; LO sızıntısı (zero-IF'te); NCO tam fs/4'te ADC ofsetini DC'ye taşımaz ama f_NCO = 0 taşır | Anteni sonlandır: çivi kalıyorsa sayısal/ADC ofseti; DDC öncesi ortalama çıkarma bloğunu aç ({{bolum:9}}) |
| fs/2 − f_in ve fs/4 ± f_in'de spur | Time-interleaving offset/gain/timing hatası; ADC kalibrasyonu çalışmamış | f_in'i kaydır: spur ters yöne kayıyorsa interleaving; ADC'nin ön plan kalibrasyonunu yeniden tetikle ({{bolum:9}}) |
| f_in'in katlarında (katlanmış) çiviler | Harmonik bozulma: ADC sürücü/LNA doyumu, clipping | Giriş seviyesini 6 dB düşür: harmonik 12 dB (HD2) / 18 dB (HD3) düşerse doğrusallık; `ADC_OVR_CNT`'ye bak ({{bolum:5}}, {{bolum:8}}) |
| Periyodik, düzenli aralıklı küçük çiviler; FTW değişince yer değiştiriyor | NCO faz kırpma spur'ları; dither kapalı | FTW'yi 1 LSB değiştir: çiviler kayıyorsa NCO; dither aç, P'yi artır ({{bolum:14}}) |
| Gürültü tabanı beklenenden 3–10 dB yüksek | Saat jitter'ı (f_in yüksekken); kazanç planı yanlış (ADC tabanı termal tabanı örtüyor); yanlış pencere/ENBW telafisi | Giriş frekansını düşür: taban düşüyorsa jitter. Anteni sonlandırıp tabanı hesapla ({{bolum:4}}, {{bolum:9}}, {{bolum:19}}) |
| Gürültü tabanı beklenenden düşük, hassasiyet kötü | Kazanç eksik: ADC kuantizasyon tabanı termal tabanın üstünde | ADC girişinde termal gürültü ≥ ADC tabanı + 10 dB kuralını kontrol et; kazanç ekle ({{bolum:9}}) |
| False alarm patlaması, FIFO taşıyor | Eşik birimi yanlış (dBm↔dBFS); gürültü kestirimi donmuş/sıfır; CFAR α'nın sabit nokta biçimi yanlış; histerezis 0 | `NOISE_EST`'i oku ve tabanla karşılaştır; α register'ını geri okuyup Q formatıyla çöz; anten sonlandırılmışken Pfa'yı sayaçla ölç ({{bolum:23}}, {{bolum:30}}) |
| Hiç tespit yok, sinyal spektrumda görünüyor | Eşik çok yüksek; min PW koşulu darbeden uzun; tespit bloğu etkin değil; latency hizalaması bozuk (frekans kolu PDW'yi engelliyor) | Sabit eşiği tabanın 10 dB üstüne çek, CFAR'ı kapat: tespit gelirse CFAR ayarı; `DET_MIN_PW`'yi oku ({{bolum:23}}, {{bolum:26}}) |
| PW kısa ölçülüyor | Histerezis yok ve gürültü kenarı parçalıyor; eşik tepeye yakın (−3 dB yerine −0.5 dB'de kesiyor); filtre BW'si darbeyi yumuşatmış | Aynı darbeyi 10 dB güçlü ver: PW değişiyorsa eşik/histerezis; değişmiyorsa filtre ({{bolum:16}}, {{bolum:25}}) |
| PW uzun ölçülüyor ya da darbeler birleşiyor | Video filtre çok uzun; histerezis çok geniş; iki darbe pulse-on-pulse | Video filtre uzunluğunu yarıya indir; zarf snapshot'ında kenarı incele ({{bolum:22}}, {{bolum:26}}) |
| PA dalgalı, aynı darbede ±2 dB | FFT scalloping (bin arası); kanal kenarı; AGC adım değişimi darbe içinde | Frekansı bin merkezine kaydır: dalgalanma kaybolursa scalloping; flat-top pencere ya da zaman kolu PA'sı kullan ({{bolum:19}}, {{bolum:25}}) |
| TOA genliğe göre kayıyor (güçlü darbe erken) | Time walk: sabit eşik yükselen kenarı farklı noktada kesiyor | Aynı darbeyi 20 dB farkla ver, TOA farkını ölç; %50 kesişim ya da CFD kullan ({{bolum:25}}) |
| PDW kaybı: sıra numarası atlıyor | FIFO taşması (darbe yoğunluğu > DMA hızı); PS okuma döngüsü yavaş; kesme kaçırılıyor | `PDW_DROP_CNT` artıyor mu? FIFO seviye kesmesini yarıya çek, DMA tampon boyutunu artır ({{bolum:26}}) |
| RF frekansı sabit ofsetle yanlış | LO frekansı ya da NCO FTW yanlış girildi; bölge evrikliği; referans osilatör ppm hatası | Bilinen CW ver; hata sabitse LO/NCO register'ı, frekansla orantılıysa ppm ({{bolum:6}}, {{bolum:30}}) |
| Çok kanallı faz farkı her açılışta değişiyor | NCO senkron reset kanallara farklı saatte ulaşıyor; SYSREF hizalaması yok | Aynı tonu iki kanala böl, faz farkını ölç, yeniden başlat, tekrar ölç ({{bolum:14}}, {{bolum:11}}) |
| Her şey doğru ama saniyede bir "tık" (geniş bant darbe) | Kalibrasyon/PLL yeniden kilitlenmesi; saat alanı geçişinde kayıp örnek; DMA tampon sınırı | Snapshot'ı tık anında tetikle: örnek sayacında atlama varsa CDC/FIFO ({{bolum:11}}) |
| JESD link kuruluyor, veri hep 0 ya da sabit desen | ADC test deseni açık kalmış; lane sırası yanlış; veri biçimi (offset binary / 2's complement) yanlış çözülüyor | ADC'ye rampa deseni ver, FPGA'da ardışıklığı kontrol et ({{bolum:11}}) |

{{svg:g-292-spur-kimligi.svg|Bir spur'un kimliğini üç hamlede çıkarma. Sol: giriş frekansını kaydır ve spur'un kaymasını sinyalinkiyle oranla. Orta: giriş seviyesini 6 dB düşür ve spur'un kaç dB düştüğüne bak. Sağ: FTW'yi 1 LSB değiştir; yer değiştiren çiviler NCO kaynaklıdır.}}

:::saha-notu Bir spur'un kimliğini üç hamlede çıkar
(1) **Giriş frekansını** 1 MHz kaydır: spur kaymıyorsa saat/NCO/DC kaynaklı;
aynı yönde k·1 MHz kayıyorsa k'ıncı harmonik; ters yöne kayıyorsa
katlanmış/interleaving. (2) **Giriş seviyesini** 6 dB düşür: spur 6 dB
düşerse doğrusal kaçak (LO/saat sızıntısı, crosstalk); 12/18 dB düşerse
HD2/HD3; hiç düşmezse sinyalden bağımsız (NCO, saat). (3) **FTW'yi** 1 LSB
değiştir: kayıyorsa NCO. Üç hamle, kağıt üstünde tabloya bakmadan çoğu spur'u
teşhis eder.
:::

## Bit-true doğrulama döngüsü

Saha teşhisinin ötesinde, tasarımın doğruluğunu kanıtlayan tek yöntem
{{bolum:13}}'te tanımlanan **bit-true karşılaştırma**dır: aynı giriş dizisi
hem MATLAB/Python modeline hem FPGA'ya verilir, ara nokta çıkışları örnek
örnek karşılaştırılır. Uygulamada üç zorluk çıkar ve üçünün de çözümü
bellidir:

- **Hizalama.** FPGA çıkışı model çıkışına göre zincirin latency'si kadar
  gecikir; ayrıca decimation fazı (hangi örneğin atıldığı) farklı olabilir.
  Çözüm: bilinen bir dürtü ya da kenar ile gecikmeyi ölç, decimation fazını
  parametre yap, karşılaştırmayı çapraz korelasyon tepesinden başlat.
- **Yuvarlama farkı.** Model `round`, RTL `floor` yapıyorsa ±1 LSB farklar
  birikir. Çözüm: modeli RTL'in yuvarlama moduna **birebir** uydur
  ({{bolum:12}}); "yaklaşık eşit" kabul etme, fark sıfır olmalı.
- **Gürültü.** Dither ve gürültü üreteçleri tohumluysa model ile FPGA aynı
  diziyi üretebilir; değilse bu blokları test modunda kapat.

:::matlab-fpga
::matlab::
```matlab
% bit_true.m — snapshot ile golden karşılaştırma
x   = read_snapshot('adc_raw.bin');          % int16, ADC çıkışı
ref = ddc_bit_true(x, ftw, katsayi, 'floor'); % RTL ile aynı yuvarlama
y   = read_snapshot('ddc_out.bin');           % int16 I/Q, FPGA çıkışı
[~, gecikme] = max(abs(xcorr(real(y), real(ref))));
gecikme = gecikme - numel(ref);
fark = y(gecikme+1:end) - ref(1:end-gecikme);
assert(all(fark == 0), 'bit-true değil: %d farklı örnek', nnz(fark));
```
::fpga::
```verilog
// snapshot tamponu: tetikte N örnek + örnek sayacı + zaman damgası
always @(posedge clk) begin
  if (kol && tetik)              yaz_aktif <= 1'b1;
  if (yaz_aktif) begin
    bram[adr] <= {sayac[15:0], i_q_veri};   // sayaç boşluk teşhisi için
    adr <= adr + 1;
    if (adr == SNAP_LEN-1) begin yaz_aktif <= 1'b0; hazir <= 1'b1; end
  end
  if (temizle) begin hazir <= 1'b0; adr <= 0; end
end
```
:::

:::tuzak "Simülasyonda çalışıyordu"
Simülasyon kısa, temiz ve tohumlu; donanım uzun, gürültülü ve asenkron. En
sık kaçan üç hata: (1) simülasyonda hiç taşmayan bir akümülatör donanımda
saatler sonra taşar (sayaç genişliği); (2) simülasyonda hep aynı fazda
başlayan iki blok donanımda reset'e farklı saatte çıkar (senkron reset
disiplini, {{bolum:14}}); (3) simülasyonda CFAR referans penceresi hep dolu,
donanımda akışın başında yarım (kenar etkisi, {{bolum:23}}). Simülasyona
**uzun rastgele koşu**, **rastgele reset zamanlaması** ve **akış başlangıcı**
senaryolarını ekle.
:::

:::tuzak Snapshot'ı yanlış birimle okumak
Tampon int16 I/Q tutuyor; Python'da `np.int16` yerine `np.uint16` ile
okursan negatif örnekler 65 535'e sarar, spektrumda devasa bir DC çivisi ve
gürültü tabanı yükselmesi görürsün — ve saatlerce ADC ofseti ararsın. Aynı
tuzağın kardeşleri: I/Q sırası (I mi önce Q mu), MSB hizalaması (14 bit 16'ya
sola mı sağa mı yaslı), offset binary. Tampon başlığına biçimi yaz; okuma
betiği başlığı doğrulasın.
:::

:::ozet
- Hata ayıklama belirtiden bloğa gider: zinciri bilinen bir sinyalle istediğin yerden böl, ara noktayı snapshot'la yakala, modelle karşılaştır.
- Test sinyali sırası: gürültü (taban) → CW (frekans/seviye) → darbe (tespit/ölçüm) → çift ton (doğrusallık) → gerçek anten.
- Her belirti için nedeni tahmin etme, kanıtlayan tek kontrolü yap; tablo 18 belirti için kontrolü verir.
- Spur kimliği üç hamlede: giriş frekansını kaydır, giriş seviyesini düşür, FTW'yi değiştir.
- Snapshot tamponlarına örnek sayacı ve zaman damgası ekle; biçimi başlığa yaz.
- Bit-true karşılaştırmada hizalama, yuvarlama modu ve tohumlu gürültü üç zorluktur; fark sıfır olmalı, "yaklaşık" yok.
- Simülasyona uzun koşu, rastgele reset zamanlaması ve akış başlangıcı senaryolarını ekle.
:::

:::kendini-sina
S: CW tonu 1 MHz yukarı kaydırdın; spur 2 MHz yukarı kaydı. Kaynak nedir?
C: İkinci harmonik (HD2): f_in'in katlarında olan bileşenler giriş kaymasının katı kadar kayar. Seviyeyi 6 dB düşürüp spur'un 12 dB düşmesiyle doğrula; doyum noktasını (ADC sürücü, LNA) ara.
S: Anten sonlandırılmışken PDW sayacı saniyede 3 000 artıyor; hedef Pfa 10⁻⁶, karar hızı 300 MSPS. Ne söylenebilir?
C: Beklenen yanlış alarm oranı 300/s; ölçülen 10 katı → gerçek Pfa ≈ 10⁻⁵. Eşik yaklaşık 1 dB düşük (Rayleigh: 10⁻⁵ için 4.8σ, 10⁻⁶ için 5.26σ). α register'ının sabit nokta biçimini ve gürültü kestiriminin doğru çalıştığını kontrol et.
S: Bit-true karşılaştırmada FPGA çıkışı ile model arasında her örnekte 0 ya da −1 LSB fark var. Neden ve çözüm?
C: Yuvarlama modu farkı: model round, RTL floor (truncation) yapıyor. Modeli RTL'in moduna uydur; farkın tam sıfıra inmesi beklenir.
S: Spektrumda ton doğru yerde ama gürültü tabanı hesaplanandan 8 dB yüksek; giriş frekansını yarıya indirince taban 6 dB düşüyor. Kaynak?
C: Örnekleme saati jitter'ı: jitter kaynaklı gürültü giriş frekansıyla 20·log orantılı artar (frekans yarıya → 6 dB). Saat kaynağını, PLL döngü bant genişliğini ve saat yolundaki gürültüyü incele.
:::

:::kopru
Belirtileri okumayı öğrendin; şimdi sıra o belirtilerin doğduğu register'ları
düzgün yazmaya geldi. Bölüm 30, kılavuzun yazılımcı için son durağı: kurgusal
bir register haritası, birim dönüşüm kütüphanesi, kalibrasyon ve açılış sırası.
:::
