# Bölüm 23 — Gürültü Tahmini, Adaptif Eşik ve CFAR
::meta onkosul=4,21,22 acar=24,25,26,28 blok=esik rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "Sabah kalibre ettiğimiz eşik öğlen neden yanlış alarm
yağdırıyor?" Çünkü eşik sabit kaldı, gürültü kalmadı: kart ısındı, LNA'nın
kazancı yarım dB kaydı, operatör bandı değiştirdi, yan lobdan bir verici
girdi. {{bolum:21}}'de gördük — Pfa eşiğin *üstel* fonksiyonudur; gürültü
tabanının 3 dB yükselmesi 10⁻⁶'yı 10⁻³ yapar, saniyede 300 sahte darbe
300 000 olur. Tersine 3 dB düşmesi almacı sessizce 3 dB sağırlaştırır ve
kimse fark etmez. Çözüm, eşiği gürültünün *kendisinden* türetmektir: her an,
her hücrede, o anki gürültüyü ölçüp katını almak. Bu bölüm o mekanizmanın —
**CFAR** (Constant False Alarm Rate — sabit yanlış alarm oranı) — ailesini,
α = {{s:turetilmis_beklenen.ca_cfar_alfa}}'un nereden geldiğini, nerede
kırıldığını ve etrafına örülen pratikleri anlatır. Kısmın en uzun bölümüdür;
tespit almacının kalitesi büyük ölçüde burada belirlenir.
:::

## Sezgi: kütüphanede fısıltı, stadyumda çığlık

Kütüphanede biri fısıldasa duyarsın; stadyumda yanındaki bağırsa zor
duyarsın. Kulağın "ses var mı" kararını mutlak bir desibel değerine göre
değil, **ortamın o anki uğultusuna göre** verir; eşiği arka plana göre
sürekli yeniden kurar. Sabit eşikli almaç, kütüphane ayarıyla stadyuma
giren biri gibidir: her şeyi ses sanır. Stadyum ayarıyla kütüphaneye giren
ise hiçbir şey duymaz.

CFAR kulağın yaptığını yapar: karar vereceği hücrenin **komşularına** bakar,
onların ortalamasını "arka plan" sayar ve eşiği bunun sabit bir katına kurar.
Arka plan yükselirse eşik yükselir, düşerse düşer; yanlış alarm oranı sabit
kalır — adı buradan gelir. Bedeli iki türlüdür: komşulardan alınan kestirim
sonlu sayıda örnekten geldiği için gürültülüdür (bu, sabit eşiğe göre birkaç
dB kayıp demektir) ve komşuların "arka plan" olmadığı durumlarda — yanında
başka bir darbe varken, gürültünün basamak yaptığı kenarda — kestirim yalan
söyler. Bölümün geri kalanı bu iki bedeli yönetmektir.

:::analoji Otomatik pozlama
Fotoğraf makinesinin otomatik pozlaması sahnenin ortalama parlaklığını
ölçer ve pozlamayı ona göre kurar: karanlıkta uzun, aydınlıkta kısa. Kar
manzarasında insanların yüzü karanlık çıkar — çünkü ortalama, sahnenin
"arka planı" değil, sahnenin kendisi tarafından şişirilmiştir. CFAR'ın
maskeleme arızası tam olarak budur: komşu darbeler ortalamaya girer, eşik
şişer, asıl darbe karanlıkta kalır. Fotoğrafçının çaresi "nokta ölçüm"
(daha küçük pencere) ya da "en parlak noktaları yok say"dır; CFAR'ın çaresi
guard hücreleri, küçük yarıyı seçen SO (smallest-of) ve sıra istatistiği
kullanan OS (order-statistic) — hepsi aşağıda.
:::

## Kavram: sabit eşik neden yetmez

Gürültü tabanı sabit bir sayı değildir. Kazanç sıcaklıkla kayar (tipik
0.01–0.03 dB/°C, 40 °C'lik gün içi fark ≈ 1 dB), kazanç kontrol ayarı
değişir, bant değiştirilince ön uçtaki filtre kaybı değişir, komşu bir
verici ya da geniş bantlı bir karıştırıcı tabanı fiilen yükseltir. Referans
senaryonun eşiği gürültü ortalamasının 13.8 katındaydı; bu oranın
gürültüyle nasıl bozulduğuna bak:

:::formul id=sabit-esik-duyarlilik baslik="Sabit eşiğin gürültü değişimine duyarlılığı"
f: Pfa' = exp( − frac{−ln Pfa}{g} ) = Pfa^{1/g}
s: Pfa | eşiğin tasarlandığı yanlış alarm olasılığı | —
s: g | gürültü gücünün tasarım değerine oranı (doğrusal; +3 dB → g = 2) | —
s: Pfa' | gerçekleşen yanlış alarm olasılığı | —
o: Tasarım Pfa = 10⁻⁶. Taban +1 dB → Pfa' = 1.7×10⁻⁵ (17 kat); +3 dB → **10⁻³** (bin kat; 300 MSPS'te saniyede 300 000 yanlış alarm); +6 dB → 0.03 (her 30 örnekten biri).
o: Taban −3 dB → Pfa' = 10⁻¹² — yanlış alarm yok ama eşik artık gürültünün 14.4 dB üstünde: Pd = 0.9 için 13.2 yerine 16.2 dB SNR gerekir, almaç sessizce 3 dB sağırlaşır.
:::

{{svg:g-231-sabit-vs-adaptif.svg|Sabit eşik ile CA-CFAR eşiği, gürültü tabanı 600. hücrede 6 dB yükselen bir sahnede (hesaplanmış; N = 16, G = 2, α = 21.94). Üstte: ilk yarının gürültüsüne göre kurulmuş sabit eşik, ikinci yarıda 24 yanlış alarm (kırmızı) üretir. Altta: CFAR eşiği (altın kesikli) tabanı izler, sıfır yanlış alarm, dört darbe de tespit (mavi); basamağı N/2 + G = 10 hücrede öğrenir, darbe komşuluğunda bir miktar yükselir.}}

Asimetriye dikkat: gürültü yükselince yanlış alarm *seli* gelir ve herkes
görür; gürültü düşünce almaç *sessizce* sağırlaşır ve kimse görmez. İkincisi
sahada daha tehlikelidir. Sabit eşik yalnızca iki yerde meşrudur: laboratuvar
ölçümünde (gürültü kontrol altında) ve CFAR'ın altına konan bir **taban
eşiği** olarak (aşağıda "eşik pratikleri").

## Kavram: gürültü tabanını kestirmek

Adaptif eşiğin kalbi, gürültü gücünün kestirimidir. Dört klasik kestirici,
dört farklı sağlamlık düzeyi:

| Kestirici | Ne yapar | Güçlü yanı | Zayıf yanı |
|---|---|---|---|
| **Ortalama** (mean) | K örneğin aritmetik ortalaması | En az varyans (gürültü Gauss ise en iyi) | Darbeler ortalamaya girer, kestirim şişer (maskeleme) |
| **Medyan** | K örneğin ortanca değeri | Örneklerin yarısından azı darbe olduğu sürece etkilenmez | Üstel dağılımda medyan = ln 2 × ortalama → ×1.44 (1.6 dB) düzeltme gerekir; sıralama ister |
| **Minimum istatistiği** (minimum statistics) | K bloğun her birinin ortalamasını al, en küçüğünü seç | Darbe yoğunluğu çok yüksekken bile "en sessiz anı" bulur | Sistematik olarak düşük kestirir (K'ye bağlı düzeltme çarpanı); yavaş |
| **Histogram / mod** | Güç histogramının tepesi | Darbelerden ve uç değerlerden bağımsız | Bellek, yavaş güncelleme; düşük çözünürlük |

Hepsinin ortak sorunu **darbenin kendisidir**: gürültüyü kestirmek istiyorsun
ama akışta darbeler de var. İki savunma vardır. Birincisi **dondurma**
(gating): tespit bayrağı yüksekken (ve birkaç örnek sonrasına kadar)
kestiriciyi güncelleme. Bu, darbenin kendi kestirimini şişirmesini önler
ama ilk tespit için kestirimin *zaten* doğru olmasını ister — döngüsel
görünen bu bağımlılık pratikte sorun çıkarmaz, çünkü darbe olmayan zaman
darbe olan zamandan çok daha uzundur (referans senaryoda duty %{{s:sinyal.duty_yuzde}}).
İkincisi **zaman sabiti**: kestirici yavaş güncellenir, tek bir darbe onu
kıpırdatamaz.

:::formul id=iir-kestirici baslik="Üstel ortalamalı (IIR) gürültü kestiricisi ve zaman sabiti"
f: P_{est}[n] = P_{est}[n−1] + ( P[n] − P_{est}[n−1] ) · 2^{−k}      (tespit bayrağı 0 iken)
f: τ ≈ 2^k örnek = frac{2^k}{f_s}
s: P[n] | anlık güç (video filtre çıkışı) | LSB²
s: P_{est} | gürültü gücü kestirimi | LSB²
s: k | güncelleme kaydırması (register); adım 2⁻ᵏ | —
s: τ | kestiricinin zaman sabiti | s
o: k = 16, f_s = {{s:ddc.cikis_fs_msps}} MSPS → τ = 65 536 örnek ≈ **218 µs**: 1 µs'lik bir darbe (dondurma unutulsa bile) kestirimi en fazla 300/65 536 ≈ %0.5 oynatır; gün içi 1 dB'lik kazanç kaymasını saniyeler içinde izler.
o: k = 20 → τ ≈ 3.5 ms: daha sakin kestirim (varyans 16 kat düşük) ama band değişiminden sonra 3–4 τ ≈ 12 ms süreyle eşik yanlış — bant atlama komutundan sonra kestiriciyi **yeniden başlatmak** (reset ya da hızlı k) standart pratiktir.
:::

Bu tür bir **yavaş kestirici + sabit çarpan** düzeni, CFAR'ın en basit
halidir: gürültüyü zamanda uzun bir pencereden kestirir, eşiği α katına kurar.
Hızlı değişen gürültüye (darbeli girişim, tarama sırasında bant değişimi,
FFT ekseninde filtre kenarı) yetişemez; bunun için kestirimi karar hücresinin
*hemen komşuluğundan* alan kayan pencereli (sliding window) CFAR gerekir.

## Kavram: CFAR penceresi — referans, guard, test hücresi

{{svg:g-230-cfar-penceresi.svg|CFAR penceresinin anatomisi. Üstte: kayan pencere içinde N/2 = 8 öncü referans hücresi, G = 2 guard, test hücresi (CUT — cell under test), 2 guard, 8 ardıl referans hücresi; referans hücrelerinin ortalaması Z gürültü kestirimi, eşik T = α·Z. Guard hücreleri darbenin yumuşak kenarlarının referansa sızmasını önler. Altta: darbe pencereden uzunsa (300 örneklik darbe, 21 hücrelik pencere) kenarlar referansa taşar, Z şişer ve darbe kendini maskeler — dondurma ya da darbeden uzun pencere gerekir.}}

Pencerenin üç bölgesi vardır. **CUT** (cell under test — test hücresi) o anda
karar verilen örnektir; bundan sonra kısaca CUT diyeceğiz. İki yanındaki **guard** (koruma) hücreleri, darbenin
yükselme/düşme kenarlarının ve video filtrenin yaydığı enerjinin referansa
sızmasını önlemek için *hesaba katılmaz*; sayısı, beklenen kenar
yayılmasından büyük seçilir (video filtre L = {{s:tespit.video_filtre_uzunluk}}
için 3 örnek yayılma → G = {{s:tespit.guard}}). Guard'ların dışındaki **referans
hücreleri** gürültü kestirimini verir; toplam sayısı N'dir, iki yarıya
bölünmüştür (öncü/ardıl — zaman ekseninde "önce gelen / sonra gelen", FFT
ekseninde "alt/üst komşu bin'ler"). Kestirim Z bu N hücreden nasıl
türetiliyorsa CFAR'ın adı odur:

| Tip | Z (gürültü kestirimi) | İyi olduğu yer | Kötü olduğu yer |
|---|---|---|---|
| **CA** (cell averaging) | tüm N hücrenin ortalaması | Homojen gürültü; en düşük kayıp | Yakın darbe (maskeleme), gürültü basamağı (kenar etkisi) |
| **GO** (greatest of) | iki yarının ortalamasından *büyüğü* | Gürültü basamağı kenarında yanlış alarmı bastırır | Maskelemeyi ağırlaştırır; ≈ 0.3 dB ek kayıp |
| **SO** (smallest of) | iki yarının ortalamasından *küçüğü* | Yakın iki darbeyi çözer | Basamak kenarında yanlış alarm patlaması; ek kayıp |
| **OS** (order statistic) | N hücre sıralanır, k'ıncı en küçüğü alınır (k ≈ 3N/4) | N−k kadar yabancı darbeye ve kenara dayanıklı | Sıralama ağı maliyeti; CA'dan ≈ 1–2 dB fazla kayıp |

Hepsinde karar aynıdır: $x_{CUT} > α · Z$. Farkı yaratan yalnızca Z ve ona
uygun α'dır.

## Kavram: α nereden gelir — CA-CFAR çarpanı ve CFAR kaybı

Sabit eşikte ortalama gürültü gücünü *tam* bildiğimizi varsaymıştık: eşik
= 13.8 × P_ort. CFAR'da P_ort'u N hücreden *kestiriyoruz*; kestirim kendisi
rastgeledir ve arada sırada düşük çıkar. Düşük çıktığı anlarda eşik düşer ve
yanlış alarm olasılığı artar. Aynı ortalama Pfa'yı korumak için çarpanı
13.8'in üstüne çıkarmak gerekir; ne kadar üstüne çıktığı, kestirimin ne
kadar gürültülü olduğuna — yani N'e — bağlıdır. Üstel dağılımlı N hücrenin
ortalaması için sonuç kapalı formdur:

:::formul id=ca-cfar-alfa baslik="CA-CFAR çarpanı ve CFAR kaybı"
f: Pfa = ( 1 + frac{α}{N} )^{−N}   ⟺   α = N · ( Pfa^{−1/N} − 1 )
f: kayıp_{CFAR} = 10 · log_{10} frac{α(N)}{−ln Pfa}        (N → ∞ iken α → −ln Pfa, kayıp → 0)
s: N | referans hücre sayısı (iki yarının toplamı) | —
s: α | eşik çarpanı: T = α · Z, Z = referans ortalaması (güç) | —
s: Pfa | hücre başına hedef yanlış alarm olasılığı | —
o: N = {{s:tespit.n_ref}}, Pfa = 10⁻⁶ → α = 16 · (10^{6/16} − 1) = 16 · (2.371 − 1) = **{{s:turetilmis_beklenen.ca_cfar_alfa}}** (13.4 dB). Sabit eşiğin 13.8'ine (11.4 dB) göre **2.0 dB CFAR kaybı** — 15 dB bütçesindeki "kalan 2 dB" budur.
o: N = 8 → α = 37.0, kayıp 4.3 dB · N = 32 → α = 17.3, kayıp 1.0 dB · N = 64 → α = 15.4, kayıp 0.5 dB. N'i iki katlamak kaybı kabaca yarıya indirir ama pencereyi uzatır.
:::

α'nın **N'e ve Pfa'ya birlikte** bağlı olduğunu unutma: `CFAR_N` register'ını
16'dan 32'ye çeken ama α'yı 21.9'da bırakan yazılımcı Pfa'yı 10⁻⁶'dan
≈ 10⁻⁸'e çeker (1.0 dB gereksiz kayıp); tersini yapan (N = 8, α = 21.9)
Pfa'yı ≈ 3×10⁻⁵'e çıkarır. İkisi tek bir fonksiyonda, birlikte yazılır
(aşağıda C kodu). Bir de α'nın **güç domaininde ve tek örneklik üstel gürültü
için** olduğunu hatırla: girişte L örneklik video filtre varsa hücreler gama
dağılımlıdır ({{bolum:22}}), aynı Pfa için α küçülür; kapalı form yoktur,
sayısal çözülür ya da ölçülür.

**N seçimi** iki baskı arasındadır. Büyük N kaybı düşürür (N = 16'da 2 dB, 64'te
0.5 dB). Küçük N pencereyi kısa tutar: pencere, gürültünün *homojen* kaldığı
uzunluktan kısa olmalıdır (FFT ekseninde filtre kenarının, zaman ekseninde
girişim değişiminin ölçeğinden) ve içine düşen yabancı darbe sayısını azaltır.
Referans senaryo N = 16, G = 2: pencere 21 hücre = 70 ns; 1 ms PRI'de iki
darbenin aynı pencereye düşme ihtimali yok denecek kadar azdır, ama yoğun bir
ortamda (birden çok emiter, µs mertebesinde aralıklar) bu pencere sık sık
kirlenir — OS ya da SO'ya geçiş nedeni.

OS-CFAR için çarpan başka bir formülden gelir (k'ıncı sıra istatistiğinin
dağılımı): N = 16, k = 12, Pfa = 10⁻⁶ için α ≈ 21.0 — sayı CA'nınkine
yakın görünür ama k'ıncı istatistik ortalamadan büyük olduğu için efektif
eşik daha yüksektir; OS'nin CA'ya göre ek kaybı N = 16'da ≈ 1–1.5 dB'dir.
Karşılığında referans penceresindeki N − k = 4 hücreye kadar yabancı darbe
kestirimi hiç etkilemez.

{{svg:g-232-cfar-ailesi-sahne.svg|Dört CFAR'ın aynı sahnedeki davranışı (hesaplanmış; N = 16, G = 2, Pfa = 10⁻⁶). Sahne: 6 hücre arayla iki yakın 3 hücrelik darbe (20 dB), yalnız bir darbe, 420. hücrede +8 dB gürültü basamağı ve basamağın içinde bir darbe. CA ve GO yakın çifti tamamen maskeler (0/3, 0/3) ama basamakta temizdir; SO çifti çözer ama basamağın hemen sağında (420–421. hücreler) 2 yanlış alarm üretir; OS (k = 12) çifti de çözer, basamakta da temiz kalır. Güç gri, eşik altın kesikli, tespit mavi, yanlış alarm kırmızı.}}

:::widget id=w18 ad="CFAR laboratuvarı"
- **Referans senaryo** preset'i (CA, N = 16, G = 2, Pfa = 10⁻⁶, düz gürültü, seyrek darbeler): α satırında 21.9'u, kayıp satırında 2.0 dB'yi oku; sağ paneldeki sabit eşik ile sol paneldeki CFAR eşiğinin düz gürültüde aynı yükseklikte (13.4 dB'ye karşı 11.4 dB — 2 dB fark) durduğunu gör; ikisi de tüm darbeleri yakalar.
- Gürültü profilini **basamak** (+6 dB) yap: sabit eşik ikinci yarıda onlarca yanlış alarm üretsin, CA-CFAR eşiği basamağı ≈ 10 hücrede öğrensin ve yanlış alarm saymasın. Sonra **rampa** seç: sabit eşik önce sağır, sonra alarm yağmuru; CFAR ikisini de yapmaz.
- Darbe yoğunluğunu **yoğun** yap (yakın çiftler): CA'da kaçırma sayacı yükselsin (maskeleme); tipi **SO**'ya çevir, kaçırma düşsün ama basamaklı profilde yanlış alarm belirsin; **OS** ile ikisinin de düzeldiğini, kaybın ≈ 1 dB arttığını gör.
- Guard'ı 2'den 0'a indir: 3 hücrelik darbenin kenar hücreleri artık referans penceresine girer, darbe *kendini* maskeler — kaçırma sayacı sıfırdan onlarca hücreye çıksın; G = 1'de yalnızca uçlar kaybolsun. Guard, beklenen kenar yayılmasından büyük seçilir.
- N'i 16'dan 64'e çıkar: α 21.9'dan 15.4'e, kayıp 2.0'dan 0.5 dB'ye insin; ama yoğun ortamda pencereye daha çok yabancı darbe düştüğü için maskeleme *artsın*. N = 8'e in: kayıp 4.3 dB, eşik eğrisi "sinirli", yanlış alarm sayacı değişmesin (Pfa sabit) ama kaçırma artsın.
- Pfa'yı 10⁻⁶'dan 10⁻³'e çek: α 21.9'dan 8.6'ya insin, 4000 hücrelik çizimde ≈ 4 yanlış alarm belirsin; Monte Carlo satırı (uzun gürültü, sabit tohum) ölçülen Pfa'yı teorik değere karşı göstersin.
:::

## Kavram: CFAR'ın kırıldığı yerler

Yukarıdaki sahne üç arıza modunu birden gösteriyor; sahada karşına çıkma
sırasıyla:

**1. Maskeleme (masking).** Referans penceresine ikinci bir darbe düşerse Z
şişer ve CUT'taki darbe eşiğin altında kalır — iki darbe *birbirini*
maskeler (yoğun ortamda çok yaygın: ardışık iki emiterin darbeleri, çok yollu
yansımalar, darbe içi ve darbe dışı yan loblar). Uzun bir darbe pencereden
uzunsa kendi kenarlarıyla *kendini* maskeler (g-230 alt panel). Belirti:
güçlü bir emiter varken zayıf emiterin PDW'leri kesilir; tek başına
göründüğünde normal. Çare sırasıyla: guard'ı büyütmek (yalnızca kenar
sızıntısı için), SO ya da OS'ye geçmek, darbe süresince kestirimi dondurmak,
uzun darbeler için ayrı bir yavaş kestirici.

**2. Kenar etkisi (clutter edge).** Gürültü tabanı basamak yaparsa (bant
değişimi, girişimin başlaması, FFT ekseninde filtre kenarı), pencerenin bir
yarısı düşük diğeri yüksek gürültüde kalır. CA ikisinin ortalamasını alır: yüksek
tarafa giren ilk N/2 hücrede eşik gerçek gürültünün altındadır → yanlış alarm
patlaması; düşük tarafa çıkarken de tersi → geçici sağırlık. GO bunu büyük
yarıyı seçerek çözer; SO ağırlaştırır. Bedel: GO maskelemeyi ağırlaştırır.
Basamağın nerede olduğunu biliyorsan (bant değişimi komutu senin elinde)
CFAR'a "kenar geliyor" demek — kestiriciyi sıfırlamak ya da geçişte kararı
birkaç pencere süresince askıya almak — en ucuz çözümdür.

**3. Uzun darbe / CW tabanı şişirir.** Sürekli dalga (CW) ya da pencereden çok
uzun bir darbe geldiğinde, referans hücrelerinin *hepsi* o sinyalle dolar:
CFAR onu "yeni gürültü tabanı" sayar, eşiği onun 13.4 dB üstüne çıkarır ve
CW'nin altında kalan her şeye kör olur — CW'nin kendisini de tespit etmez,
çünkü CUT ile referans aynı seviyededir. Zaman ekseninde CFAR bu duruma
yapısal olarak kördür; çare CW'yi başka yerden yakalamaktır: yavaş
kestiricinin ani sıçramasını izlemek ("taban 20 dB yükseldi" bayrağı), FFT
ekseninde CFAR (CW dar bantlıdır, komşu bin'ler gerçek gürültüdür — orada
kolayca çıkar) ve CW bayrağı ile PDW üretmek ({{bolum:24}}).

**4. Yoğun ortamda kayıp.** Darbe yoğunluğu arttıkça referans pencereleri
sürekli kısmen doludur; OS bile N − k sınırını aşınca kestirim şişer. Sonuç,
Pfa sabit kalırken **hassasiyetin ortama bağlı düşmesidir** — CFAR'ın adının
söylediği tam olarak budur: sabit tuttuğu Pfa'dır, Pd değil. Sistem
tasarımcısı bunu bilir ve yoğun ortam için hassasiyet bütçesine 2–4 dB
ek pay koyar.

## Kavram: zaman ekseninde mi, FFT bin'leri üzerinde mi?

Aynı pencere iki eksende gezdirilebilir. **Zaman ekseninde** hücreler ardışık
örneklerdir (300 MSPS'te 3.33 ns); pencere 21 hücre = 70 ns; darbe, zamanda
yerelleşmiş bir enerji olarak yakalanır, geniş bantlı ve modülasyonlu
darbeler için doğal yoldur — ama "gürültü" olarak gördüğü şey 300 MHz'lik
bandın *tamamının* gürültüsüdür ve dar bantlı bir sinyalin 300 MHz gürültüyle
yarışması gerekir. **FFT ekseninde** ({{bolum:18}}) hücreler aynı anın
frekans bin'leridir ({{s:fft.bin_khz}} kHz); pencere 16 bin = 4.7 MHz; dar
bantlı bir sinyal tek bin'e toplanır ve yalnızca *o bin'in* gürültüsüyle
yarışır (işlem kazancı {{s:fft.islem_kazanci_db}} dB), CW burada sıradan bir
"hedef"tir, komşu bin'ler temiz gürültüdür. Bedel: zaman çözünürlüğü FFT
boyuna düşer ({{s:fft.gozlem_suresi_us}} µs) ve kısa darbeler enerjisini
bin'lere yayar. FFT ekseninde gürültü tabanı düz değildir — DDC filtresinin
kenarları ({{bolum:16}}) bandın uçlarında tabanı düşürür — bu bir "rampa"
profilidir ve GO/OS'nin ya da bin başına kalibre edilmiş bir taban
tablosunun konusudur. Modern tespit almaçları ikisini birlikte çalıştırır:
zaman kolu hızlı ve geniş, FFT kolu yavaş ve hassas; PDW ikisinden beslenir
({{bolum:26}}).

## Kavram: eşik pratikleri — tek karşılaştırmadan sağlam karara

CFAR bayrağı tek örneklik bir karardır; darbe değildir. Bayraktan darbeye
giden yolda dört pratik vardır ve dördü de FAR'ı, Pfa'ya dokunmadan düşürür:

**Histerezis** (hysteresis — açma/kapama çift eşiği). Darbe başlangıcı üst eşikle (T) açılır, bitişi
alt eşikle (T − {{s:tespit.histerezis_db}} dB) kapanır. Platodaki gürültü
dalgalanması (video filtre sonrası ±1.5 dB) tek eşiği defalarca kesip bir
darbeyi üçe böler; 3 dB'lik boşluk bunu önler. Alt eşik, PW ölçümünün
düşme kenarını belirler; {{bolum:25}} bunun PW tanımıyla (−3 dB / −6 dB)
ilişkisini kurar.

**Minimum darbe genişliği** (min-PW; glitch reddi). Ardışık en az M örnek eşik
üstünde kalmayan aşımlar reddedilir (referans senaryo M = {{s:tespit.min_pw_ornek}}
örnek = 13 ns). Bağımsız örneklerde M ardışık yanlış alarm olasılığı Pfaᴹ'dir:

:::formul id=min-pw-mofn baslik="Minimum PW ve M-of-N doğrulamanın FAR'a etkisi"
f: FAR_{M/M} ≈ f_s · Pfa^M        (M ardışık aşım; örnekler bağımsızsa)
f: FAR_{M/N} ≈ f_s · ∑_{j=M}^{N} C(N, j) · Pfa^j · (1 − Pfa)^{N−j}
s: M, N | gereken aşım sayısı / bakılan pencere | örnek
s: Pfa | örnek başına yanlış alarm olasılığı | —
s: f_s | karar hızı | Hz
o: Pfa = 10⁻³ (N = 16 için α = 8.6, eşik yalnızca 9.4 dB!) ve M = 4/4 → FAR ≈ 3×10⁸ · 10⁻¹² = **3×10⁻⁴ /s**; aynı Pfa ile 3-of-4 → ≈ 1.2 /s. Tek örnekte 10⁻³, saniyede 300 000 yanlış alarm olurdu.
o: Uyarı: video filtre (L = 4) komşu örnekleri ilişkilendirir; gerçek kazanç bağımsız varsayımdan azdır (kabaca M yerine M/L etkin). Hedef Pfa'yı buna göre ölç, hesaplama.
:::

Bu formül CFAR ile min-PW arasındaki iş bölümünü gösterir: **min-PW, örnek
başına Pfa'yı gevşetmene izin verir** (10⁻⁶ yerine 10⁻³–10⁻⁴), bu da eşiği
3–4 dB indirir ve CFAR kaybının çoğunu geri alır. Bedeli, M örnekten kısa
darbelere körlüktür — M, görmek istediğin en kısa darbeden kısa seçilir.

**M-of-N doğrulama**, min-PW'nin toleranslı halidir: N örneğin M'si yetsin.
Plato içindeki tek bir gürültü çukurunun darbeyi kesmesini önler; darbe FSM'i
({{bolum:26}}) genellikle "3-of-4 açar, 4 ardışık alt eşik altı kapatır" gibi
asimetrik kurulur.

**Maksimum PW / CW bayrağı.** Aşım belirli bir süreyi (örneğin 100 µs) geçerse
darbe değil CW'dir; FSM darbeyi "kırpılmış" bayrağıyla kapatır, CW bayrağı
kaldırır ve kestiriciyi dondurmayı bırakır (yoksa CW süresince taban asla
güncellenmez).

**Taban eşiği ve tavan.** CFAR eşiğinin altına sabit bir **taban** konur
(`max(α·Z, T_min)`): kestirim bir arızayla sıfıra düşerse (giriş kopunca,
dondurma takılı kalınca) almaç her örneği tespit etmesin. Tavan da faydalıdır:
CFAR eşiği ADC tam ölçeğinin üstüne çıkamaz; çıkıyorsa CW/doyma durumu var
demektir, bayrak kaldır.

**Eşiğin dBFS/dBm karşılığı ve kalibrasyon.** Register'daki eşik LSB²'dir;
operatör dBm ister. Zincir: LSB² → dBFS (tam ölçek gücüne oran, {{bolum:22}})
→ dBm (ADC tam ölçek dBm − ön uç kazancı: {{s:adc.tam_olcek_dbm}} −
{{s:on_uc.kazanc_toplam_db}} = −36 dBm'lik ofset, kart başına ölçülür). Ofset
ısıyla ve bantla kayar; kalibrasyon, bilinen seviyede bir CW verip ölçülen
PA'yı beklenene eşitleyen tek bir sayıdır ve periyodik yenilenir. CFAR'ın
güzelliği, bu ofset kaysa bile Pfa'nın kaymamasıdır — kayan yalnızca
raporlanan dBm'dir.

:::pasaport durak="Tespit çıkışı" alan=sayisal
Alan: sayısal (FPGA)
!Büyüklük: tespit bayrağı (1 bit) + hizalanmış güç (20 bit) + eşik (20 bit, isteğe bağlı)
Tip: reel, işaretsiz + bayrak
fs: {{s:ddc.cikis_fs_msps}} MSPS (hücre = örnek; FFT kolunda hücre = bin, {{s:fft.bin_khz}} kHz)
!Eşik: CA-CFAR, N = {{s:tespit.n_ref}}, G = {{s:tespit.guard}}, α = {{s:turetilmis_beklenen.ca_cfar_alfa}} (13.4 dB), Pfa = 10⁻⁶ hücre başına; taban eşiği −55 dBFS
!Yanlış alarm: 300/s ham bayrak → min-PW {{s:tespit.min_pw_ornek}} + histerezis {{s:tespit.histerezis_db}} dB sonrası ≪ 1/s (ölçülür)
SNR: Pd = 0.9 için 13.2 + 2.0 (CFAR kaybı) ≈ 15.2 dB; bütçe {{s:tespit.tespit_snr_db}} dB → hassasiyet ≈ {{s:turetilmis_beklenen.hassasiyet_dbm}} dBm
Gecikme: pencere yarısı N/2 + G = 10 hücre + pipeline ≈ 4 saat (TOA düzeltmesi sabit)
:::

## FPGA'da nasıl gerçeklenir

{{svg:g-233-ca-cfar-blok.svg|CA-CFAR donanım blok şeması (referans gerçekleme). Güç örnekleri 21 hücrelik gecikme hattına girer; ardıl ve öncü referans pencereleri için iki kayan toplam tutulur (her saatte yeni hücre eklenir, pencereden çıkan çıkarılır — 16 toplama yerine 4). İki toplam Σ'da birleşir, PS'in yazdığı α (Q6.10) ile çarpılır; CUT log₂N kadar kaydırılarak N ile çarpılır ve bölmesiz karşılaştırma x_CUT·N > α·Σ bayrağı üretir. Bayrak tespit sayacına da gider; giriş sonlandırıldığında bu sayaç yanlış alarm sayacıdır. Register'lar yeşil.|kaydir}}

:::uc-goz
::rf::
CFAR, RF tasarımcının en iyi dostudur: kazanç kaymasını, sıcaklık etkisini,
bant değişimini ve AGC adımlarını affeder — hepsi "yavaş değişen taban"dır
ve eşik onları izler. Affetmediği şeyler *hızlı* ve *dar bantlı*
bozulmalardır: CW girişim, güçlü spur'lar, komşu kanaldan darbeli sızıntı.
Bunlar zaman ekseninde CFAR için "taban" gibi görünür ve hassasiyeti çalar.
RF tarafında ön seçici filtre, iyi LO temizliği ve limiter buradaki en etkili
"CFAR yardımcılarıdır". Bir de kayıp bütçesi: 15 dB tespit SNR'ının 2 dB'si
CFAR'a gider; N'i büyütmek (kayıp 0.5 dB'ye iner) 1.5 dB hassasiyet demektir
ve bu, LNA'da 1.5 dB NF kazanmaktan çok daha ucuzdur — ama yalnızca gürültü
homojense.
::fpga::
Referans gerçekleme g-233'teki gibidir: 21 derinlikli, 20 bit genişlikli
gecikme hattı (bir SRL zinciri ya da küçük bir BRAM); iki kayan toplam
(20 + 3 = 23 bit; her biri saatte bir toplama bir çıkarma); Σ 24 bit; α
çarpımı bir DSP slice (24 × 16 bit Q6.10 → 40 bit, üst bitler alınır); CUT
için 4 bit sola kaydırma (N = 16); 40 bitlik bir karşılaştırıcı. Kayan
toplamın (running sum) güzelliği N'den bağımsız maliyetidir; N ve G register'dan
değişecekse gecikme hattının uçları bir mux ile seçilir — bu yüzden çoğu
tasarım N ve G'yi yalnızca birkaç 2ⁿ değerle sınırlar. GO/SO, iki yarı
toplamı arasında bir karşılaştırma ve mux daha. **OS** pahalı olandır:
N = 16 hücreyi her saatte sıralamak bitonic sıralama ağıyla (sorting network) 10 kademe × 8 = 80
karşılaştır-değiştir birimi (20 bit); alternatif **sayma yöntemi**: yeni
hücre geldiğinde onu 15 hücreyle karşılaştırıp "kaç tanesinden büyük"
sayısını hesapla, k'ıncı sırayı bu sayılardan seç — 16 karşılaştırıcı, ama
her saatte güncellenen bir sıra tablosu. Pipeline gecikmesi 3–5 saat; bayrak,
güce göre N/2 + G + gecikme kadar geride çıkar, TOA bu sabitle düzeltilir.
300 MSPS SSR'da ({{bolum:12}}) 8 paralel hücre için kayan toplam 8 girişli
toplayıcı ağacına dönüşür.
::yazilim::
Yazılımcının gördüğü register'lar (kurgusal): `CFAR_MODE` (CA/GO/SO/OS + OS
için k), `CFAR_N`, `CFAR_G`, `CFAR_ALPHA` (Q6.10), `THR_MIN` (taban, LSB²),
`HYST` (alt/üst eşik oranı, Q1.15), `MIN_PW`, `MAX_PW`, `DET_CNT` (okununca
sıfırlanan 32 bit sayaç). Üç disiplin: (1) `CFAR_N` ile `CFAR_ALPHA` **tek
fonksiyonla, birlikte** yazılır; (2) Pfa hedefi FAR'dan türetilir (saniyede
kaç, hangi karar hızında), α ondan; (3) `DET_CNT` giriş sonlandırılmışken
periyodik okunur ve `Pfa · f_s · süre` ile karşılaştırılır — bu, CFAR'ın
"gerçekten sabit yanlış alarm oranı" verip vermediğinin tek kanıtıdır.
Aşağıda hepsi.
:::

:::matlab-fpga
::matlab::
Model tarafında CA-CFAR bir konvolüsyondur; α kapalı formdan gelir:

```matlab
N = 16; G = 2; Pfa = 1e-6;
alfa = N * (Pfa^(-1/N) - 1);                 % 21.94
h = [ones(1,N/2) zeros(1,2*G+1) ones(1,N/2)];% referans maskesi
Z = conv(P, h, 'same') / N;                  % referans ortalaması
tespit = P > alfa * Z;                       % karar
% bit-true: alfa_q = round(alfa*1024)/1024 (Q6.10), Z yerine Σ = Z*N,
% karar: P*N > alfa_q*Σ  (bölme yok) — FPGA ile aynı sıra ve kırpma.
```
::fpga::
Aynı kararın RTL çekirdeği (kayan toplam + bölmesiz karşılaştırma):

```verilog
// p: 20 bit güç; hat[0..20]: gecikme hattı; N=16, G=2 sabit örnek
always @(posedge clk) begin
  sum_ardil <= sum_ardil + p        - hat[7];    // x[n]     .. x[n-7]
  sum_oncu  <= sum_oncu  + hat[12]  - hat[20];   // x[n-13]  .. x[n-20]
end
wire [24:0] sigma   = sum_ardil + sum_oncu;      // 16 hücre toplamı
wire [40:0] esik_xN = sigma * alfa_q;            // Q6.10 → sonuç Q?.10
wire [40:0] cut_xN  = {hat[10], 4'b0} << 10;     // x_CUT · 16, aynı ölçek (·1024)
assign tespit = (cut_xN > esik_xN) && (hat[10] > thr_min);
```

Bit-true doğrulama ({{bolum:13}}): MATLAB `P*N > alfa_q*Σ` ile ILA'dan okunan
`tespit` bayrağı bit bit eşit olmalı; bayrağın 10 + pipeline hücre gecikmesi
hizalanır. Eşik kenarındaki tek-LSB farkları, `alfa_q` yuvarlaması modelde
de aynı yapılmadıysa ortaya çıkar.
:::

## Yazılımcıya dokunan yer

Register haritası kurgusaldır; birim ve sıra gerçektir.

```c
#include <stdint.h>
#include <math.h>

/* Pfa ve N'den CA-CFAR çarpanı; Q6.10 sabit noktaya (16 bit) çevirir.
 * α = N·(Pfa^(-1/N) − 1). N=16, Pfa=1e-6 → 21.942 → 22469 = 0x57C5. */
static uint16_t cfar_alpha_q610(unsigned N, double pfa)
{
    double alpha = N * (pow(pfa, -1.0 / N) - 1.0);
    if (alpha > 63.999) alpha = 63.999;          /* Q6.10 üst sınırı */
    return (uint16_t)lround(alpha * 1024.0);
}

/* FAR hedefinden Pfa: saniyede kaç yanlış alarm, hangi karar hızında. */
static double pfa_from_far(double far_hz, double f_karar_hz) { return far_hz / f_karar_hz; }

/* N ve α BİRLİKTE yazılır; ayrı yazılırsa Pfa mertebelerce kayar. */
static void cfar_kur(volatile uint32_t *reg, unsigned N, unsigned G, double pfa)
{
    reg[CFAR_N]     = N;                          /* yalnızca 8/16/32/64 */
    reg[CFAR_G]     = G;
    reg[CFAR_ALPHA] = cfar_alpha_q610(N, pfa);
    reg[HYST]       = (uint32_t)lround(pow(10.0, -3.0 / 10.0) * 32768.0); /* 3 dB → 0.501 → Q1.15 = 0x4027 */
    reg[MIN_PW]     = 4;                          /* örnek (13 ns) */
    reg[THR_MIN]    = 3;                          /* taban: −55 dBFS, 20 bitlik güç ölçeğinde (2^20·10^(−5.5) ≈ 3.3) */
}

/* Yanlış alarm oranı sağlık kontrolü: giriş sonlandırılmışken çağır. */
static int cfar_far_kontrol(uint32_t det_cnt, double sure_s, double pfa, double f_karar_hz)
{
    double olculen = det_cnt / sure_s, beklenen = pfa * f_karar_hz;   /* 1e-6 × 300e6 = 300/s */
    return olculen < 3 * beklenen && olculen > beklenen / 3;          /* ±3 kat dışına çıkarsa arıza */
}
```

Sabit nokta ayrıntısı: Q6.10'un 1 LSB'si 0.001'dir; α'daki 0.001'lik hata
Pfa'yı yalnızca %0.04 değiştirir — 10 bit kesir fazlasıyla yeter, 6 bit tam
sayı ise α ≤ 64'ü, yani N = 8, Pfa = 10⁻⁶'ya kadar (α = 37) her makul
ayarı kapsar. `THR_MIN` tabanı, 20 bitlik güç ölçeğinde (tam ölçek 2^20 = 0 dBFS)
−55 dBFS ≈ 3 LSB'dir; gürültü tabanı ≈ −47 dBFS ≈ 21 LSB, CFAR eşiği
≈ 21 × 21.9 ≈ 460 LSB (−34 dBFS). Taban, CFAR eşiğinin 20 dB altındadır ve
normalde hiç devreye girmez — yalnızca kestirim çökerse. (Gürültünün 21
LSB ile temsil edilmesi kaba görünür; kestirim 16 hücreden alındığı için
yeterlidir, ama daha düşük gürültü tabanlı bir kartta kırpma kaydırması
10 yerine 8 bit seçilir.)

:::tuzak "CFAR'ı taktık, hassasiyet 2 dB düştü — kırık mı?"
Hayır, hesapta. N = 16 için CFAR kaybı 2.0 dB'dir: α = 21.9, sabit eşiğin
13.8'inin 2 dB üstü. Bu kayıp, gürültüyü 16 örnekten kestirmenin bedelidir
ve laboratuvarda (gürültü sabitken) sabit eşik gerçekten 2 dB daha
hassastır. Sahada ise sabit eşik ya yanlış alarm seli ya da 3 dB sessiz
sağırlıktır. Kaybı azaltmanın yolu N'i büyütmektir (64 → 0.5 dB), ama pencere
homojen kaldığı sürece; ya da min-PW ile örnek başına Pfa'yı gevşetip eşiği
3 dB indirmek. Hassasiyet raporuna "CFAR, N = 16" yazılmadan sayı
karşılaştırılamaz.
:::

:::tuzak CW geldi, her şey kayboldu
Yakında güçlü bir CW verici açılır; o andan itibaren zaman ekseninde CFAR'ın
referans hücreleri CW ile doludur, taban kestirimi CW gücüne çıkar, eşik onun
13.4 dB üstüne kurulur. CW'nin kendisi tespit edilmez (CUT = referans),
CW'den 13 dB zayıf her darbe de kaybolur. Belirti: PDW akışı aniden kesilir,
`DET_CNT` sıfıra düşer, yavaş kestirici register'ı 20–30 dB yükselmiştir.
Teşhis: yavaş kestiricinin ani sıçramasına bir "taban sıçradı" bayrağı bağla.
Çare: CW'yi FFT ekseninde yakala (orada dar bir "hedef"tir), CW bayrağıyla
PDW üret ve mümkünse bir çentik (notch) ile bastır; zaman ekseninde CFAR'ın
CW'ye yapısal olarak kör olduğunu kabul et.
:::

:::tuzak N'i değiştirdim, α'yı unuttum
`CFAR_N` 16'dan 32'ye alınır ("kaybı düşürelim"), `CFAR_ALPHA` 21.9'da
kalır. Yeni Pfa = (1 + 21.9/32)^−32 ≈ 6×10⁻⁸: yanlış alarm 17 kat azalır, hassasiyet
1 dB *düşer* — tam tersi amaçlanmıştı. Tersi (N = 8, α = 21.9) Pfa'yı
≈ 3×10⁻⁵'e çıkarır: yanlış alarm 30 kat artar. α yalnız başına anlamsızdır;
N ve Pfa ile birlikte tek fonksiyondan yazılır. Kontrol: register'ları geri
oku, `(1 + α/N)^−N`'i hesapla, hedef Pfa ile karşılaştır.
:::

:::tuzak Histerezisi sıfırladım, PW ölçümleri ikiye bölündü
"Alt eşik neden farklı olsun" diye histerezis 0 dB yapılır. Video filtre
sonrası platodaki gürültü ±1.5 dB dalgalanır; eşiğe 1–2 dB mesafeli bir
darbenin platosu tek eşiği birkaç kez keser ve bir darbe yerine iki-üç kısa
PDW üretilir; PW yarıya iner, PRI yanlış ölçülür, emiter tanıma bozulur.
Belirti: aynı emiter için PW histogramında iki tepe (tam ve yarım). Çare:
histerezis 3 dB, M-of-N ile kapatma, min-PW. Yan etki: alt eşik PW'nin
düşme kenarını belirler; PW tanımı ({{bolum:25}}) bununla tutarlı seçilir.
:::

:::ozet
- Sabit eşik gürültüyle birlikte kayar: taban +3 dB → Pfa 10⁻⁶'dan 10⁻³'e (bin kat); −3 dB → sessiz 3 dB sağırlık. Eşik gürültüden türetilmelidir.
- Gürültü kestiricileri: ortalama (en az varyans, darbelere duyarlı), medyan (×1.44 düzeltme), minimum istatistiği, histogram; tespit sırasında **dondurma** ve darbeden çok uzun **zaman sabiti** (k = 16 → 218 µs) şarttır.
- CFAR penceresi: N referans (iki yarı), G guard, CUT; karar $x_{CUT} > α·Z$. CA ortalama, GO büyük yarı (kenar), SO küçük yarı (yakın darbe), OS k'ıncı sıra (her ikisine dayanıklı, pahalı).
- CA-CFAR: α = N·(Pfa^(−1/N) − 1); N = 16, Pfa = 10⁻⁶ → **α = 21.9** (13.4 dB), CFAR kaybı **2.0 dB**; N = 64 → 0.5 dB. α, N ve Pfa ile birlikte yazılır.
- Arıza modları: maskeleme (yakın/uzun darbe), kenar etkisi (basamak), CW/uzun darbenin tabanı şişirmesi (zaman-CFAR yapısal olarak kör; FFT ekseninde yakala), yoğun ortamda Pd kaybı (CFAR Pfa'yı sabitler, Pd'yi değil).
- Eşik pratikleri: histerezis 3 dB, min-PW (M ardışık → FAR ≈ f_s·Pfaᴹ; Pfa'yı gevşetip eşiği 3–4 dB indirmenin yolu), M-of-N, max-PW/CW bayrağı, taban ve tavan eşiği, LSB² ↔ dBFS ↔ dBm kalibrasyonu.
- FPGA: gecikme hattı + iki kayan toplam + α çarpımı (Q6.10) + bölmesiz karşılaştırma x_CUT·N > α·Σ; OS için sıralama ağı ya da sayma; `DET_CNT` giriş sonlandırılmışken FAR'ı ölçer — CFAR'ın tek kanıtı.
:::

:::kendini-sina
S: N = 32, Pfa = 10⁻⁶ için α ve CFAR kaybı nedir; Q6.10 register değeri kaç?
C: α = 32·(10^{6/32} − 1) = 32·(1.540 − 1) = 17.28 (12.4 dB); kayıp = 10·log10(17.28/13.82) = 0.97 dB. Q6.10: round(17.28 × 1024) = 17 694 = 0x451E.
S: Referans pencere 21 hücre (70 ns) iken 1 µs'lik darbe geldiğinde CA-CFAR ne yapar, nasıl düzeltilir?
C: Darbenin ilk ~10 hücresi tespit edilir (referans henüz gürültü), sonra referans hücreleri darbeyle dolar, Z ≈ darbe gücü, eşik darbenin 13.4 dB üstüne çıkar ve darbenin geri kalanı "kaybolur" (kendini maskeleme) — PW yanlış ölçülür. Düzeltme: tespit bayrağı yükselince kestirimi dondurmak (Z'yi son gürültü değerinde tutmak), ya da darbe FSM'inin kapanışını CFAR eşiğine değil dondurulmuş eşiğe bağlamak; uzun darbeler için yavaş kestirici.
S: Gürültü tabanı 420. hücrede +8 dB basamak yapıyor. CA, GO, SO basamağın hemen sağındaki hücrelerde ne yapar?
C: CA: pencerenin yarısı düşük gürültüde olduğundan Z gerçek tabanın altında kalır (≈ ortalama), eşik yetersiz → N/2 hücre boyunca yanlış alarm patlaması olasılığı yüksek. GO: büyük yarıyı (yüksek taban) seçer, eşik doğru, temiz. SO: küçük yarıyı seçer, eşik 8 dB düşük, yanlış alarm patlaması (şekilde basamağın hemen sağında 2 alarm). Basamağın solunda ise CA/GO geçici sağırlık gösterir.
S: Yazılımcı min-PW'yi 4 yapıp örnek başına Pfa'yı 10⁻³'e gevşetti. Eşik kaç dB indi ve FAR ne olur (bağımsız örnek varsayımıyla)? Bu varsayım neden iyimser?
C: α = 16·(1000^{1/16} − 1) = 8.7 → 9.4 dB; 10⁻⁶'nın 13.4 dB'sine göre 4 dB daha düşük eşik. FAR ≈ 3×10⁸ · (10⁻³)⁴ = 3×10⁻⁴ /s. İyimser, çünkü L = 4 video filtre komşu örnekleri ilişkilendirir: bir aşımı 4 örnek sürdürmek bağımsız 4 aşımdan çok daha olasıdır; gerçek FAR ölçülmeli (giriş sonlandırılmış, DET_CNT).
S: Giriş sonlandırılmış, `DET_CNT` 10 saniyede 2900 sayıyor (CA, N = 16, α = 21.9, 300 MSPS, min-PW kapalı). CFAR sağlıklı mı?
C: Beklenen 10⁻⁶ × 3×10⁸ × 10 = 3000 ± 55; 2900 bunun içinde sayılır (2 σ'nın biraz dışında ama ±3 kat sağlık bandında rahat). CFAR ve gürültü modeli tutarlı. 30 000 çıksaydı gürültü Gauss değil (spur/girişim) ya da α/N uyumsuz; 300 çıksaydı taban eşiği (THR_MIN) devrede olabilir.
:::

:::kopru
Tespit bayrağı artık güvenilir: gürültüye göre kurulmuş, histerezisle
temizlenmiş, kısa aşımlardan arındırılmış. Ama bayrak yalnızca "bu örnekte
darbe var" der; ne zaman başladığını, ne kadar sürdüğünü, kaç dBm olduğunu,
hangi frekansta olduğunu söylemez. Kısım VIII bu soruların cevabını tek bir
sabit formatlı kayda — PDW'ye — sığdırır. Bölüm 24 önce o kaydın ne
olduğunu, hangi alanları kaç bitle taşıdığını ve ham örnekten PDW'ye
kaç binde birlik indirgemenin nasıl yapıldığını anlatır.
:::
