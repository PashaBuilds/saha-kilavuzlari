# Bölüm 28 — Uçtan Uca Referans Tasarım
::kisim IX — Sistem Bütünü ve Pratik
::meta onkosul=4,9,14,16,18,23,25,26 acar=29,30 blok=anten,onuc,mixer,if,adc,arayuz,nco,mixing,filtre,zarf,esik,fft,olcum,pdw,ps rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "fs neden 2400? Decimation neden 8? FFT neden 1024? Kim, neye
göre seçmiş?" Yirmi yedi bölüm boyunca darbeyi durak durak izledik; her
durakta bir sayı seçildi ve o sayı bir sonraki durağı belirledi. Bu bölüm
zinciri **tek seferde, baştan sona** kurar: her durakta zaman ve frekans
görünümü, sinyal pasaportunun büyük tablosu, dört bütçe (seviye/SNR, bit
genişliği, latency, kaynak) ve tasarım kararlarının geri izi. Sonunda, bütün
widget'ların çekirdeğini birleştiren zincir oyun alanında bir parametreyi
değiştirip etkisinin PDW'ye kadar nasıl yayıldığını izleyeceksin. Sayılar
kurgusaldır; mantık gerçektir.
:::

## Zincir tek bakışta, sayılarla

{{svg:g-280-poster-sayili.svg|Poster şemanın sayılarla dolu hali. Her durağın altında referans darbenin o noktadaki değerleri: frekans konumu, fs, bit, veri hızı, sinyal seviyesi ve SNR. Altın: analog, mavi: sayısal, yeşil: yazılım. Bölüm 0'daki posterle aynı yerleşim; oradaki her blok burada sayıya kavuşur.|kaydir}}

Darbenin yolculuğu (antenden DTK'ya), Bölüm 0'daki cümleyle: antene {{s:sinyal.rf_ghz}} GHz'de,
{{s:sinyal.seviye_dbm_giris}} dBm tepe güçle, {{s:sinyal.pw_us}} µs süren bir
darbe çarpar. LNA onu gürültü şeklini bozmadan yükseltir; mixer
{{s:on_uc.lo_ghz}} GHz LO ile {{s:on_uc.if_ghz}} GHz IF'e indirir; image olan
{{s:on_uc.image_ghz}} GHz'i preselector daha önce bastırmıştır. IF filtresi ve
kazanç kademeleri sinyali ADC'nin tam ölçeğine uygun seviyeye getirir; AAF
ikinci Nyquist bölgesi dışını temizler. ADC {{s:adc.fs_msps}} MSPS'te,
{{s:adc.bit}} bitle örnekler; 1.8 GHz ikinci bölgeden {{s:adc.alias_mhz}} MHz'e
**evrik** katlanır. NCO {{s:ddc.nco_mhz}} MHz'i baseband'e çeker, filtre ve
↓{{s:ddc.decimation_toplam}} decimation veri hızını {{s:ddc.cikis_fs_msps}} MSPS
kompleks I/Q'ya indirir. Zarf, CA-CFAR eşiği ve darbe FSM'i darbeyi
{{s:ddc.darbe_ornek_sayisi}} örneklik bir olay olarak yakalar; FFT aynı darbeye
{{s:fft.bin_khz}} kHz'lik bin'lerle bakar. Ölçümler 128 bitlik PDW'ye yazılır,
FIFO ve DMA üzerinden PS'e düşer.

## Sinyal pasaportu: büyük tablo

Her bölümdeki pasaport şeritleri burada tek tabloda. Değişen alanlar
**kalın**. Gürültü ve SNR sütunları tek darbe için, entegrasyon yok.

{{tablo: genis}}
| Durak | Alan | Frekans konumu | Tip | fs | Bit | Veri hızı | Sinyal | Gürültü | SNR |
|---|---|---|---|---|---|---|---|---|---|
| Anten girişi | analog RF | {{s:sinyal.rf_ghz}} GHz | reel | — | — | — | {{s:sinyal.seviye_dbm_giris}} dBm | −111 dBm (2 MHz, NF 0) | — |
| LNA çıkışı | analog RF | 9.4 GHz | reel | — | — | — | −40.5 dBm | −89 dBm (2 MHz, NF ≈ 2.5 dB, +19.5 dB kazanç) | 48 dB (2 MHz) |
| Mixer / IF çıkışı | analog IF | **{{s:on_uc.if_ghz}} GHz** (low-side, düz) | reel | — | — | — | −49.5 dBm | NF ≈ 3.4 dB | — |
| IF kazanç + AAF çıkışı | analog IF | 1.8 GHz, 1200–2400 MHz bandı | reel | — | — | — | **−20 dBm** (tam ölçek {{s:adc.tam_olcek_dbm}} dBm'in 24 dB altı) | sistem NF {{s:on_uc.nf_toplam_db}} dB → −43 dBm (300 MHz) | **23 dB** (300 MHz bandında) |
| ADC çıkışı | **sayısal** | **{{s:adc.alias_mhz}} MHz, evrik** | reel | **{{s:adc.fs_msps}} MSPS** | **{{s:adc.bit}}** | **{{s:adc.veri_hizi_gbps_14bit}} Gbps** | −24 dBFS | ADC tabanı −86 dBFS (1200 MHz); termal taban −41 dBFS baskın | 23 dB (300 MHz) |
| FPGA girişi (SSR-8) | sayısal | 600 MHz | reel, 8 örnek/saat | 300 MHz saat | 8 × 16 | 38.4 Gbps | −24 dBFS | — | 23 dB |
| NCO / mixer çıkışı | sayısal | **0 Hz (baseband)** + image −1200 MHz | **kompleks** | 2400 MSPS | 2 × 16 | 76.8 Gbps | −24 dBFS | — | 23 dB |
| Filtre + ↓8 çıkışı | sayısal | ±150 MHz | kompleks I/Q | **{{s:ddc.cikis_fs_msps}} MSPS** | 16+16 | **{{s:ddc.cikis_veri_hizi_gbps}} Gbps** | −24 dBFS | taban −47 dBFS (işlem kazancıyla −{{s:ddc.islem_kazanci_db}} dB indi) | 23 dB |
| Zarf çıkışı | sayısal | — | güç (reel) | 300 MSPS | 32 → 20 | 6 Gbps | tepe −24 dBFS | Rayleigh/üstel | 23 dB |
| CFAR / tespit | sayısal | — | **bayrak + güç** | 300 MSPS | 1 + 20 | — | eşik = α·ort, α = {{s:tespit.alfa_ca}} | Pfa 10⁻⁶ → 300 FA/s | Pd ≈ 1 (23 dB ≫ 13 dB) |
| FFT çıkışı | sayısal | bin {{s:fft.bin_khz}} kHz | büyüklük | 1024 nokta / {{s:fft.gozlem_suresi_us}} µs | 18 | ≈ 5.3 Gbps (%50 overlap) | tepe | taban −{{s:fft.islem_kazanci_db}} dB indi | 23 + 27 − 5.3 (pencere kaybı) ≈ 45 dB |
| Ölçüm | sayısal | RF geri hesap 9.4 GHz | alanlar | darbe/s | — | — | TOA ±1 ns · PW ±3 ns · PA ±0.3 dB · RF ±20 kHz | — | — |
| PDW FIFO → PS | **yazılım** | — | **128-bit sözcük** | 1000 PDW/s | 128 | **128 kbps** | — | — | indirgeme 75 000 : 1 |

İki satır dikkat ister. **Hassasiyet:** referans darbenin çıkış SNR'ı 23 dB;
giriş −60 dBm'den {{s:turetilmis_beklenen.hassasiyet_dbm}} dBm'e düşürüldüğünde
15 dB'ye iner ve Pd ≈ 0.97 olur; −72 dBm'de Pd ≈ 0.5'e düşer. Referans darbe
"rahat"tır (13 dB'lik sınırın 10 dB üstünde); sistem tasarımı rahat darbeye değil, hassasiyet sınırındaki
darbeye göre yapılır. **ADC tabanı:** sistem kazancı termal tabanı ADC'nin
kuantizasyon+jitter tabanının 10 dB üstüne taşır; bu yüzden ADC'nin 86 dB'lik
SNR'ı çıkış SNR'ında görünmez — ({{bolum:9}}) kazanç planının amacı tam olarak
buydu.

## Dört bütçe

### Seviye ve SNR bütçesi

{{svg:g-281-seviye-merdiveni.svg|Seviye merdiveni (hesaplanmış): referans darbenin sinyal seviyesi (mavi) ve gürültü tabanı (gri) antenden DDC çıkışına. Bant genişliği 2 MHz'den 300 MHz'e geçince gürültü 21.8 dB yükselir, kazanç ikisini birlikte kaldırır; ADC'nin kendi tabanı (kırmızı kesikli) termal tabanın 10 dB altında kalır. Aradaki mesafe SNR'dır: 300 MHz bandında 23 dB.}}

:::formul id="butce-snr" baslik="Tek darbe SNR bütçesi (DDC çıkışında)"
f: SNR_{çıkış} = P_{giriş} − ( −174 + 10·log_{10}(B_{DDC}) + NF_{sistem} ) − L_{ADC}
s: P_{giriş} | darbe tepe gücü antende | dBm
s: B_{DDC} | DDC çıkış bandı (kompleks fs) | Hz
s: NF_{sistem} | ön uç + kayıplar + ADC katkısı bütçesi | dB
s: L_{ADC} | ADC tabanının termal tabana eklediği kayıp (10 dB üstteyse ≈ 0.4 dB) | dB
o: −60 − (−174 + 84.8 + 6) − 0.4 = **22.8 dB** (tabloda 23 dB)
o: Hassasiyet sınırı: SNR = 13.2 dB (Pd 0.9, Pfa 10⁻⁶) → P_giriş = **−70 dBm**; 15 dB kabulüyle {{s:turetilmis_beklenen.hassasiyet_dbm}} dBm.
:::

### Bit genişliği bütçesi

| Kademe | Giriş | İşlem | Çıkış (tam) | Yuvarlama sonrası | Not |
|---|---|---|---|---|---|
| ADC | — | 14-bit örnek | 14 | 16 (MSB hizalı, 2 bit sıfır) | JESD 16-bit sözcük |
| NCO çarpımı | 16 × 16 | çarpma | 32 | 18 (round, sat) | NCO genliği 16 bit |
| CIC (R=4, N=4) | 18 | 4 kademe integratör | 18 + 8 = 26 | 26 (kırpma yok) | bit büyümesi N·log₂R |
| CIC ölçekleme | 26 | ≫ 8 + round | 18 | 18 | droop kompanzasyonu sonra |
| Kompanzasyon FIR (31 tap, Q1.17) | 18 × 18 | çarp-topla | 36 + 5 | 18 | akümülatör 41 bit |
| Halfband (↓2) | 18 | 15 tap simetrik | 36 + 4 | **16** | DDC çıkışı: I/Q 16+16 |
| Güç I²+Q² | 16 × 16 × 2 | kare-topla | 33 | 20 (kayan nokta değil, kaydırmalı) | dB eşik için log-zarf 12 bit |
| CFAR toplamı | 20 × 16 hücre | topla | 24 | 24 | bölmesiz karşılaştırma x·N > α·Σ |
| FFT (1024, Hann) | 16+16 | 10 kademe, ölçek takvimi (scaling schedule) 1 bit/kademe (ilk 5) | 21 | 18 büyüklük | scaling: 2⁻⁵ |

Bütçenin kritik noktası CIC çıkışıdır: 26 bitten 18'e inerken hangi 18'in
alındığı, zayıf sinyalde gürültü tabanını, güçlü sinyalde doyumu belirler
({{bolum:12}}, {{bolum:16}}).

### Latency bütçesi

{{svg:g-282-latency-zaman-cizgisi.svg|Latency zaman çizgisi: darbe antene çarptıktan sonra her bloğun çıkış verdiği an. Zaman kolu darbe bitiminden ≈ 0.45 µs sonra (ADC + JESD ve DDC gecikmeleri dahil, t ≈ 1.45 µs) hazırdır; frekans kolu FFT çerçevesini ≈ 4 µs'de tamamlar; PDW birleştirme iki kolu hizalamak için zaman kolunu bekletir. PS'in görmesi kesme politikasına bağlıdır.}}

| Blok | Gecikme (örnek @ kendi fs) | Süre |
|---|---|---|
| ADC + JESD204B link | ≈ 60 ADC saati + link | ≈ 0.3 µs (deterministik) |
| SSR hizalama + NCO + mixer | 5 + 3 fabric saati | 27 ns |
| CIC + kompanzasyon + halfband | ≈ 4 + 31/2 + 15/2 | ≈ 27 örnek @ 300–600 MSPS ≈ 60 ns |
| Zarf + video filtre | 3 + 4 | 23 ns |
| CFAR penceresi (N=16 + 2 guard, ileriye bakış) | 10 | 33 ns |
| Darbe FSM + ölçüm (darbe bitince) | PW + 4 | 1.0 µs + 13 ns |
| FFT 1024 streaming | 1024 + ≈ 40 | 3.5 µs |
| **PDW birleştirme hizalama** | frekans kolu − zaman kolu ≈ 2.5 µs | zaman kolu 2.5 µs geciktirilir |
| FIFO → DMA → PS kesme | tampon dolumu (yarım: {{s:pdw.fifo_yarim_esik}} PDW) | 512 ms @ 1 kHz PRF, ya da zaman aşımı |

Toplam "darbe bitti → PDW yazıldı" gecikmesi ≈ 4 µs; PS'te görünmesi
ise **kesme politikasına** bağlıdır (bkz. {{bolum:26}}): tek darbede kesme
istiyorsan FIFO eşiğini 1 yap ve kesme yükünü kabul et.

### Kaynak bütçesi (kaba, SSR-8 @ 300 MHz fabric)

| Blok | DSP slice | BRAM (36 kb) | LUT (bin) | Not |
|---|---|---|---|---|
| NCO (SSR-8, tablo) | 0 | 4–8 | 2 | 8 faz paralel |
| Kompleks mixer (8 örnek × 2) | 16–24 | 0 | 1 | 16×16 çarpma |
| CIC ↓4 (8 → 2 örnek/saat) | 0 | 0 | 6 | yalnızca toplayıcı |
| Kompanzasyon FIR + halfband | 24–40 | 1 | 4 | simetri yarıya indirir |
| Zarf + video + CFAR | 8 | 2 | 5 | OS-CFAR sıralama ağı ek ~4 bin LUT |
| FFT 1024 streaming | 24–48 | 12–20 | 8 | IP çekirdeği |
| Darbe FSM + ölçüm + PDW paketleyici | 6 | 4 | 6 | anlık frekans için CORDIC |
| FIFO + DMA + AXI | 0 | 4 | 4 | {{s:pdw.fifo_derinlik}} PDW derinlik (16 KB) |
| Snapshot tamponları (4 × 8 k örnek) | 0 | 32 | 1 | teşhis için |
| **Toplam** | **≈ 100** | **≈ 70** | **≈ 40 bin** | orta boy bir UltraScale+ parçasının küçük bir kesri |

Bu sayılar kurgusal ve mertebe (order-of-magnitude) düzeyindedir; gerçek tasarımda
sentez raporu konuşur ({{bolum:13}}). Öğretici sonuç: **sayısal almacın
darboğazı hesap gücü değil, veri taşıma ve saat alanı disiplinidir.**

## Tasarım kararlarının geri izi

Sorular sırasıyla; her cevap bir önceki cevaba yaslanır.

- **fs neden 2400 MSPS?** IF'i 1.8 GHz'de tutmak istedik (image ve filtre
  için yüksek IF, {{bolum:6}}). 1.8 GHz'in ikinci Nyquist bölgesinde
  ortalanması ve 300 MHz'lik anlık bandın harmonik katlanmasından uzak
  kalması için fs 2400 seçildi: bölge 1200–2400, IF tam ortada, HD2 (3.6 GHz)
  1200 MHz'e katlanır — bandın kenarına, içine değil ({{bolum:8}}). 2400,
  300 MHz fabric saatinin tam 8 katı: SSR-8 tam sayı ({{bolum:11}}).
- **Neden 14 bit?** Anlık dinamik aralık hedefi ~70 dB (zayıf darbe ile güçlü
  darbe yan yana). 14 bit ideal 86 dB verir; jitter ve termal katkıyla
  ~70 dB'lik SFDR/SNR bütçesi kalır. 12 bit sınırda kalır, 16 bit bu fs'te
  güç/maliyet ({{bolum:9}}, {{bolum:10}}).
- **Jitter bütçesi neden 100 fs?** 1.8 GHz IF'te 100 fs → 65 dB jitter SNR'ı;
  14 bitin 86 dB'siyle birleşince 65 dB'ye yakın toplam. 200 fs olsaydı
  59 dB: ADC'nin çözünürlüğünü boşa harcardık ({{bolum:9}}).
- **NCO neden 600 MHz?** Çünkü alias oraya düştü; NCO'nun işi katlanmış
  bandı sıfıra taşımak. 600/2400 = 1/4 olması bonus: FTW tam, faz kırpma
  hatası sıfır, hatta fs/4 hilesiyle çarpansız mixing mümkün ({{bolum:14}},
  {{bolum:15}}).
- **Decimation neden 8?** 300 MHz anlık bant istedik (EH almacı geniş bakar,
  {{bolum:4}}); kompleks çıkışta fs = bant → 300 MSPS; 2400/300 = 8. CIC ↓4
  + halfband ↓2 bölünmesi: CIC ucuz ama droop'lu, halfband son adımda keskin
  ({{bolum:16}}).
- **FFT neden 1024?** Gözlem süresi 3.4 µs: 1 µs darbe için pencere kaybı
  −5.3 dB (kabul edilebilir, 44 dB'lik SNR var), bin 293 kHz frekans ölçüm
  çözünürlüğü için yeterli, interpolasyonla ~20 kHz'e iner; 4096 olsaydı
  13.6 µs pencerede darbe boğulurdu ({{bolum:18}}, {{bolum:20}}).
- **CFAR N neden 16, Pfa neden 10⁻⁶?** N=16 CFAR kaybı ~2 dB (N=8'de 3.5 dB);
  daha büyük N yoğun darbe ortamında maskeleme riskini artırır. Pfa 10⁻⁶,
  300 MSPS'te 300 yanlış alarm/s demek; min PW ve M-of-N ile PDW düzeyinde
  saniyede <1'e iner ({{bolum:21}}, {{bolum:23}}).
- **PDW neden 128 bit?** TOA 48 bit (3.3 ns çözünürlükte 10 gün), PW 20, PA 10,
  RF 20, AOA 12, bayraklar/kanal/SNR/sıra 18 → 128; DMA ve önbellek satırı
  için 2'nin kuvveti ({{bolum:24}}).

:::widget id=w20 ad="Uçtan uca zincir oyun alanı"
- **Referans senaryo**: pasaport tablosunda çıkış SNR'ının ≈ 23 dB, Pd'nin ≈ %100 ve PDW'deki geri hesaplanan RF'in 9.4 GHz olduğunu doğrula. Giriş seviyesini −70 dBm'e indir: çıkış SNR 13 dB'ye, Pd %90'a düşsün; −75'te Pd çöksün, PDW satırı çoğu zaman "tespit yok"a dönsün.
- **Kısa darbe + uzun FFT** preset'i: darbe 0.2 µs, FFT 2048 → zaman kolunda darbe hâlâ tespit edilirken frekans kolunda "pencere kaybı −15 dB" belirsin. FFT N'i 256'ya indir: kayıp azalsın ama bin 1.2 MHz'e büyüsün.
- **Kötü saat (800 fs)**: giriş güçlü (−40 dBm) olmasına rağmen jitter SNR'ı ≈ 41 dB'ye düşsün; ADC tabanı termal tabanın üstüne çıkıp çıkış SNR'ını sınırlasın. Jitter'ı 100 fs'e çekince farkı gör.
- **Doyum**: kazancı 58 dB yap → ADC girişi 0 dBFS'i aşsın, "KIRPMA" uyarısı çıksın; gerçek sistemde bu AGC/STC'nin devreye girdiği andır ({{bolum:5}}).
- NF bütçesini 6'dan 12'ye çıkar: gürültü tabanı ve hassasiyet 6 dB kötüleşsin; sonra CFAR Pfa'sını 10⁻³'e çekerek Pd'yi geri kazanmaya çalış ve FA/s'nin 300'den 300 000'e fırladığını gör — hassasiyet Pfa ile satın alınamaz.
- **İki emiter + LFM**: spektrumda ikinci darbenin tepesi +30 MHz'de −20 dB'de belirsin; zaman kolunda iki ayrı tespit bandı ve PDW sayısı 2 olsun. NCO ofsetini +5 MHz yap: her iki tepe 5 MHz kaysın — ve "RF geri hesap" satırı yine 9.405 GHz versin (giriş ofseti 5 MHz'di), çünkü NCO ofseti geri toplanır ({{bolum:25}}).
:::

:::tuzak Bütçeleri ayrı ayrı doğru, birlikte yanlış
SNR bütçesi ADC'yi tam ölçeğe yakın sürmek ister; doğrusallık bütçesi
(IP3, {{bolum:5}}) sinyali tam ölçekten uzak tutmak ister; bit bütçesi CIC
çıkışında kırpmayı zayıf sinyale göre ayarlamak ister; latency bütçesi FFT'yi
küçük ister, frekans çözünürlüğü büyük. Referans tasarımdaki her sayı bu
çekişmenin bir uzlaşmasıdır. Tek bir bütçeyi "iyileştiren" değişiklik
(ör. kazancı 6 dB artırmak) diğer üçünü bozar; bu yüzden değişiklik önce
Bölüm 28'in tablolarında, sonra W-20'de, en son kartta denenir.
:::

:::tuzak Referans senaryoyu gerçek sanmak
Bu kılavuzun sayıları öğretici: 2400 MSPS, 14 bit, 6 dB NF, 1 µs darbe.
Gerçek bir sistem bambaşka olabilir ve olmalıdır; ama hangi sayı olursa
olsun aynı on soruyu sorman gerekir. Kendi kartının sayılarını bu bölümün
tablolarına yerleştir; boş kalan hücre, henüz anlamadığın kararın adresidir.
:::

:::ozet
- Zincir tek bakışta: −60 dBm, 9.4 GHz, 1 µs darbe → 1.8 GHz IF → 2400 MSPS/14 bit → 600 MHz evrik → NCO 600 → ↓8 → 300 MSPS I/Q (SNR 23 dB) → CFAR N=16 α=21.9 → FFT 1024 Hann → 128-bit PDW.
- Tek darbe çıkış SNR'ı ≈ 23 dB; hassasiyet sınırı (Pd 0.9) ≈ −70 dBm; ADC tabanı termal tabanın 10 dB altında tutulur.
- Bit bütçesinde kritik nokta CIC çıkışı (26 → 18); latency bütçesinde kritik nokta iki kolun hizalanması (≈ 2.5 µs); kaynak bütçesinde darboğaz hesap değil veri taşıma.
- Her tasarım sayısı bir önceki karara yaslanır: IF → fs → bölge → NCO → decimation → FFT → CFAR → PDW.
- Bütçeler birbirine karşı çalışır; değişiklik önce tabloda ve widget'ta denenir.
- PDW indirgeme oranı 75 000:1 — almacın işi veri üretmek değil, veri azaltmaktır.
:::

:::kendini-sina
S: Giriş seviyesi −60 dBm'den −70 dBm'e düştüğünde Pd yaklaşık nereye iner ve neden "yaklaşık"?
C: Çıkış SNR 23'ten 13 dB'ye: −70 − (−83.2) − 0.4 ≈ 12.8 dB; Pd (Pfa 10⁻⁶) ≈ 0.87–0.9. "Yaklaşık", çünkü Pd eğrisi bu bölgede çok diktir: 1 dB'lik kalibrasyon hatası Pd'yi 0.8 ile 0.95 arasında oynatır.
S: Decimation 8 yerine 16 seçilseydi pasaportta hangi satırlar değişirdi, hangileri değişmezdi?
C: DDC çıkışı fs 150 MSPS, bant ±75 MHz, veri hızı 4.8 Gbps, taban 3 dB daha aşağı (işlem kazancı 9 dB), darbe 150 örnek; FFT bin 146 kHz, gözlem 6.8 µs (1 µs darbe için pencere kaybı −8.3 dB). Değişmeyenler: ADC satırına kadar her şey, PDW formatı, CFAR α (N ve Pfa aynı).
S: Latency bütçesinde zaman kolu neden kasıtlı olarak geciktirilir?
C: Frekans kolu (1024 noktalık streaming FFT) ≈ 3.5 µs sürerken zaman kolu ≈ 1 µs'de sonuç verir; aynı darbenin TOA/PW/PA'sı ile frekansının tek PDW'de birleşmesi için zaman kolu ≈ 2.5 µs bekletilir. Bekletilmezse PDW'ye bir önceki darbenin frekansı yazılabilir.
S: "fs neden 2400" sorusunun cevabında hangi iki kısıt birleşir?
C: (1) IF 1.8 GHz'in bir Nyquist bölgesinin ortasında durması ve harmoniklerin (HD2 3.6 GHz → 1200 MHz) anlık bandın içine katlanmaması; (2) fabric saatinin (300 MHz) tam sayı katı olması, böylece SSR-8 ile kesirsiz paralelleştirme.
:::

:::kopru
Referans tasarım kâğıt üstünde tutarlı; sahada ise hiçbir şey ilk açılışta
tabloya uymaz. Bölüm 29, belirtiden bloğa giden hata ayıklama disiplinini
kurar: test sinyalleri, ölçüm noktaları ve on sekiz satırlık belirti–neden
tablosu.
:::
