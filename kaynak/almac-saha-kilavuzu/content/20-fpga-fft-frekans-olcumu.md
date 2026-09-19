# Bölüm 20 — FPGA'da FFT ve Darbeli Sinyalde Frekans Ölçümü
::meta onkosul=3,4,12,13,16,18,19 acar=23,25,26,28 blok=fft,olcum rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "PDW'deki RF alanının LSB'si 10 kHz; ama FFT bin'imiz 293 kHz.
Bu 10 kHz'i nereden buluyoruz, yoksa uyduruyor muyuz?" Uydurmuyoruz — ama
bedavaya da bulmuyoruz. Bin genişliği FFT'nin *ızgarasıdır*, ölçümün
*doğruluğu* değil; komşu bin'lerden interpolasyonla ya da darbe içindeki faz
farkından bin'in otuzda birine inilir ve inilebilecek sınır SNR ile darbe
süresinin çarpımıyla belirlenir. Bu bölüm FFT'yi FPGA'ya indirir (mimari,
ölçekleme takvimi, gecikme), spektrogramı kurar, sonra kılavuzun en sık
yaşanan takasını açar: 3.41 µs'lik çerçeveye 1 µs'lik darbe koyduğunda SNR
kaybedersin, çerçeveyi kısaltınca çözünürlük. Sonunda PDW'nin RF alanının
kaç Hz güvenilir olduğunu söyleyebiliyor olacaksın.
:::

## Sezgi: pozlama süresi

Bir fotoğraf makinesinde pozlama süresini uzatırsan karanlıkta daha çok ışık
toplarsın (hassasiyet), ama hareket eden şey bulanıklaşır (zaman
çözünürlüğü). Kısa pozlamada hareket donar, ama görüntü gürültülü olur. FFT
çerçevesi bir pozlamadır: N örnek boyunca enerji biriktirir. Uzun çerçeve
zayıf, sürekli bir tonu gürültüden çıkarır; ama 1 µs'lik darbe o çerçevenin
içinde "hareket eden şey"dir — çerçevenin büyük kısmı darbenin olmadığı
zamanı, yani yalnızca gürültüyü pozlar. Spektrogram, kısa pozlamaların
ardışık kareleridir: her kare bir FFT, karelerin sıklığı overlap, karenin
süresi N/fs.

## Kavram: FFT çekirdeğinin mimarisi

FPGA'da FFT genellikle hazır bir çekirdek (IP) olarak gelir ve senin
kararların onun ayarlarıdır. İlk ayar mimaridir:

- **Pipelined / streaming:** log₂N kademe kelebek arka arkaya dizilir, her
  kademenin kendi gecikme belleği vardır; veri kesintisiz akar, örnek başına
  bir saat, giriş hızı = çıkış hızı. Kaynak: kademe başına 3–4 DSP + BRAM;
  N = 1024 için ~40 DSP ve ~10 BRAM mertebesi (üreticiye göre değişir).
  Gecikme ≈ N + birkaç yüz saat. %50 overlap istiyorsan çekirdeğin örnek
  hızının iki katında beslenmesi gerekir: iki çekirdek ya da SSR-2.
- **Burst (radix-2 / radix-4 tek bellekli):** tek kelebek, N örneği belleğe
  alır, log₂N geçişte yerinde hesaplar, sonra boşaltır. Çok az kaynak (~4–8
  DSP), ama N örnek yükleme + ~N·log₂N/2 hesap + N boşaltma saati boyunca
  yeni veri kabul etmez: 1024'te ~7000 saatte bir FFT. 300 MSPS akışa
  yetişmez; tetiklenmiş (darbe FSM'i "başladı" dediğinde bir kez) analiz için
  uygundur.

Referans tasarım pipelined'dır çünkü frekans kolu her an bakmak zorundadır:
darbenin ne zaman geleceğini bilmiyoruz. İkinci ayar grubu: N (register'dan
değiştirilebilir, `log2N`), ölçekleme (aşağıda), çıkış sırası (bit-reversed
ya da doğal — doğal sıra bir N'lik tampon daha demektir) ve twiddle katsayı
genişliği (16–18 bit; 14-bit ADC için 16 yeter, sızıntı tabanı katsayı
kuantizasyonuyla −96 dB civarında sınırlanır).

{{svg:g-200-streaming-fft-akis.svg|Streaming FFT veri akışı (kurgusal referans tasarım). DDC çıkışı 300 MSPS 16+16 bit → overlap tamponu (ping-pong BRAM; her 512 örnekte 1024'lük yeni çerçeve) → pencere çarpımı (Hann ROM, 512 katsayı simetrik, tek DSP) → pipelined FFT (N = 1024, 10 kademe, ölçekleme takvimi register'dan) → bit-reversed → doğal sıra ve fftshift → |X|² = I²+Q² (36 bit) → log₂ LUT ile 20 bit dB → tepe bulma / eşik → FIFO → PS. Yeşil: PS register'ları. Alt şerit zamanlama: 586 k çerçeve/s, gecikme ≈ N + pipeline, ham spektrum 12 Gbps olduğu için PS'e yalnızca tepe listesi gider.|kaydir}}

## Kavram: bit büyümesi ve ölçekleme takvimi

Her radix-2 kademesi iki sayıyı toplar: genlik en fazla ikiye katlanır, yani
**kademe başına 1 bit** büyür. log₂N = 10 kademe sonunda 16 bitlik giriş
26 bit olur; tam ölçek ton için çıkış tam N katıdır ({{bolum:18}}). Bu
büyümeyi üç yoldan yönetirsin ve seçimin tespit hassasiyetini doğrudan
belirler:

1. **Ölçeksiz (bit büyümesine izin ver):** çıkış 16 + 10 = 26 bit. Hiçbir şey
   kaybolmaz; ama |X|² için 52 bit, BRAM ve veri yolu genişler.
2. **Ölçekleme takvimi (scaling schedule):** her kademede çıkışı 1 (ya da
   radix-4'te 2) bit sağa kaydır. Toplam kaydırma log₂N ise çıkış = X/N,
   16 bitte kalır, taşma olmaz. Ama her kaydırma bir yuvarlama gürültüsü
   ekler ve sinyal henüz büyümemişken atılan LSB'ler geri gelmez.
3. **Blok kayan nokta (block floating point):** çekirdek her kademede
   taşma riskine göre kaydırıp kaç bit kaydırdığını bir **blok üssü**
   olarak çıkışa ekler. Sinyal küçükken kaydırmaz, büyükken kaydırır;
   yazılım |X|'i 2^üs ile çarparak geri alır. En iyi taban, biraz daha
   kaynak ve "üssü unutan yazılım" tuzağı.

:::formul id=fft-bit-buyumesi baslik="Bit büyümesi ve ölçekleme"
f: B_{çıkış} = B_{giriş} + log_2 N − ∑ s_i
f: |X_{ölçekli}[k]| = frac{|X[k]|}{2^{∑ s_i}}      →   dBFS için 2^{∑ s_i} ile geri çarp
s: B_{giriş}, B_{çıkış} | giriş / çıkış kelime genişliği (I ve Q ayrı ayrı) | bit
s: N | FFT boyu | —
s: s_i | i'inci kademedeki sağa kaydırma (ölçekleme takvimi) | bit
o: B_giriş = {{s:ddc.cikis_bit_i}}, N = {{s:fft.n}}: ölçeksiz → **26 bit**; her kademede 1 kaydırma (∑s = 10) → 16 bit, çıkış = X/1024.
o: Bit-true benzetim (kılavuz çekirdeği, −92 dBFS bant içi gürültü): ölçeksiz 26 bit taban −121 dBFS/bin (ideal); 16 bit + her kademede kaydırma **−99 dBFS/bin** (22 dB hassasiyet kaybı!); 20 bit veri yolu + kaydırmalar yalnızca son 6 kademede → **−118 dBFS/bin**. Kaydırmayı sinyal büyüdükten sonra yap.
:::

Kural basittir: veri yolu genişliği = giriş genişliği + kaydırmasız kademe
sayısı. 20 bitlik bir veri yolunda ilk 4 kademe kaydırmasız geçer (16 → 20),
sonraki 6 kademe birer bit kaydırır; taban idealin 3 dB yakınında kalır.
Aynı toplam kaydırmayı ilk kademelere koyarsan gürültü tabanının 20 dB
üstünde bir "sayısal taban" yaratırsın ve 14 bitlik ADC'yi 10 bitlik gibi
kullanırsın. Ölçekleme takvimi register'ı (`FFT_SCALE_SCH`) bu yüzden bir
"taşma önleme" ayarı değil, bir **hassasiyet ayarıdır**; değeri sistem
mühendisinin bit-true modelinden gelir ({{bolum:13}}) ve yazılım onu değiştirmez,
yalnızca dBFS dönüşümünde hesaba katar.

## Kavram: STFT, spektrogram ve gerçek zamanlılık

Akan veri üzerinde ardışık çerçevelerle FFT almak **STFT**'dir (Short-Time
Fourier Transform — kısa zamanlı Fourier dönüşümü); sonucu zaman–frekans
düzleminde renk (ya da koyuluk) olarak çizersen **spektrogram** olur. Üç
parametresi vardır ve üçü de {{bolum:18}} ile {{bolum:19}}'dan tanıdıktır: N
(frekans çözünürlüğü fs/N ↔ zaman çözünürlüğü N/fs, çarpımları 1), pencere
(sızıntı ve kenar davranışı) ve overlap (çerçeve sıklığı; kenar kaybının
telafisi). Aşağıda referans darbe ve LFM varyantı, aynı STFT ayarıyla.

{{svg:g-202-spektrogram.svg|Referans darbenin (solda, 1 µs CW, +10 MHz) ve LFM varyantının (sağda, 10 MHz süpürme) hesaplanmış spektrogramı: N = 128 (bin 2.34 MHz, çerçeve 0.43 µs), adım 32 örnek (%75 overlap), Hann. Üstte darbe zarfı. CW darbe yatay bir çizgidir (genişlik ≈ Hann ana lobu, 2 bin); LFM darbe 10 MHz/µs eğimli çaprazdır: 5 MHz'den 15 MHz'e. Darbe kenarlarında çerçeve kısmen dolu olduğundan çizgi soluklaşır. Koyuluk −50…0 dB.}}

Spektrogram, darbe içi modülasyonu ({{bolum:3}}) gözle görünür kılar: CW yatay
çizgi, LFM eğik çizgi, faz kodlu darbe ise kod geçişlerinde kısa genişlemeler.
LFM'nin eğimi (MHz/µs) doğrudan okunur; bu, {{bolum:25}}'te MOP sınıflandırması
için bir ölçüttür. Ama dikkat: N = 1024 ile aynı darbe tek bir sütuna sığar
ve eğim görünmez; N = 32 ile bin 9.4 MHz olur ve 10 MHz'lik süpürme bir
bin'in içinde kalır. Spektrogramın N'i, darbe süresi ve modülasyon bant
genişliğine göre seçilir — sürekli emiter için seçilen 1024 değil.

Gerçek zamanlılık iki sayıyla ölçülür. **İş yükü:** %50 overlap'te 586 k
çerçeve/s × 1024 bin, pipelined çekirdek için sorun değil; ama ham spektrumu
PS'e taşımak 12 Gbps'tir — taşınmaz. PS'e tepe listesi (bin, dB, çerçeve no)
ya da eşik üstü bin'ler gider; ham spektrum yalnızca hata ayıklamada,
snapshot tamponuyla ({{bolum:13}}). **Gecikme:** çerçevenin son örneğinden
tepe listesinin FIFO'ya düşmesine ≈ N (çekirdek) + ~150 (pipeline) + N
(doğal sıraya çevirme) saat ≈ 7 µs. Zaman kolu ({{bolum:22}}, {{bolum:26}})
darbeyi çok daha erken görür; frekans kolu PDW'ye "geç ama doğru" bilgi
ekler ve iki kol zaman damgasıyla eşlenir.

## Kavram: kısa darbe problemi — zaman–frekans takası

Şimdi kılavuzun en sık karşılaşılan takası. Çerçeve N örnek, darbe L örnek
(referansta 300). FFT tepesinde sinyal *koherent* toplanır: genlik L ile
orantılı, güç $L^2$ ile. Gürültü ise çerçevenin tamamından gelir: güç N ile
orantılı. Tepe−taban oranı $SNR_{örnek} · L^2 / N$'dir ve L sabitken N
arttıkça **düşer**. En iyi durum N = L: çerçeve darbeyle çakışık, kayıp
sıfır. N > L olduğunda kayıp 10·log10(N/L); N < L olduğunda tepe−taban
artmaz (N örnek toplanır, N'e bölünür: $N^2/N = N$), ama bin genişler ve
frekans doğruluğu düşer.

:::formul id=darbe-cerceve baslik="Çerçeve–darbe uyumsuzluğunun SNR kaybı"
f: Tepe − Taban = SNR_{örnek} + 10 · log_{10} ( frac{min(L, N)^2}{N} )      Kayıp_{N>L} = 10 · log_{10} ( frac{N}{L} )
s: SNR_{örnek} | darbe içindeki örnek başına SNR (bant içi) | dB
s: L | darbenin örnek sayısı = PW · f_s | örnek
s: N | FFT çerçevesi | örnek
o: L = {{s:ddc.darbe_ornek_sayisi}} ({{s:sinyal.pw_us}} µs × {{s:ddc.cikis_fs_msps}} MSPS), N = {{s:fft.n}} → kayıp = 10·log10(1024/300) = **5.3 dB**. Tespit SNR'ı {{s:tespit.tespit_snr_db}} dB olan darbe, frekans kolunda 9.7 dB'ye düşer.
o: N = 256 → kayıp 0, ama bin 1.17 MHz. N = 4096 → kayıp 11.4 dB. 0.1 µs'lik darbe (30 örnek) için N = 1024 → **15.3 dB** kayıp: kısa darbeler frekans kolunda kaybolur, zaman kolu bulur.
:::

{{svg:g-201-darbe-pencere-hizalama.svg|Darbe ile FFT çerçevesinin hizalanması (hesaplanmış, örnek başına SNR 10 dB). (a) N = 1024 çerçeve 1 µs darbeyi kapsar ama yalnızca %29 doludur: tepe−taban 29.4 dB (teori 29.4), 5.3 dB kayıp. (b) Overlap'siz ardışık çerçevelerde sınıra düşen darbe ikiye bölünür (0.4 + 0.6 µs, iki zayıf tepe); %50 overlap'li ara çerçeve darbeyi bütün yakalar. (c) N = 256 çerçeve darbenin içinde: tepe−taban 34.2 dB (teori 34.1), kayıp yok, ama bin 1.17 MHz. Sağda aynı gürültülü darbenin iki N ile spektrumu.}}

Bir incelik: formül dikdörtgen çerçeve içindir. Hann gibi bir pencere,
çerçevenin ortasındaki darbeyi kayırır ve kenarlardaki gürültüyü bastırır —
darbe tam ortadaysa N = 1024'teki kayıp 5.3 yerine ≈ 1.7 dB'dir; ama darbe
çerçevenin kenarına düşerse pencere onu da söndürür ve kayıp 10 dB'yi aşar.
Overlap'in ({{bolum:19}}) darbeli sinyaldeki asıl işi budur: her darbeye
"ortada olduğu" bir çerçeve sağlamak.

Pratik çözümler: (1) **darbe FSM'i tetikli çerçeve seçimi** — zaman kolu
({{bolum:26}}) darbenin başlangıç ve bitişini verir, frekans kolu tamponundan
darbeyi tam kapsayan en kısa 2^k çerçeve seçilir; (2) **iki paralel N** —
kısa çerçeve (tespit/kaba frekans) ve uzun çerçeve (sürekli emiter, ince
frekans) aynı anda; (3) **çerçeve içinde sıfırlama** — darbe dışındaki
örnekleri sıfırla (zaman kapısı, time gating), gürültü yalnızca darbe süresinden gelsin;
N uzun kalır (ince bin), kayıp yok, ama darbe sınırlarını bilmek gerekir.
Referans tasarım (1) + (3)'ü birleştirir: FSM'in verdiği sınırlar hem kapı
hem çerçeve seçimidir.

:::widget id=w16 ad="Spektrogram / zaman–frekans takası"
- **Referans senaryo** preset'inde (N = 128, %75 overlap, Hann, 1 µs CW) yatay çizgiyi gör; "çerçeve / darbe" satırı darbenin içinde 6 tam çerçeve olduğunu, bin'in 2.34 MHz olduğunu söylesin. Tepe−taban ≈ SNR + 10·log10(128) − 1.76 (Hann ENBW) = 29.3 dB.
- **LFM varyantı**: çizgi eğilsin; 1 µs'de 10 MHz tırmanış. N'i 32 yap: bin 9.4 MHz, eğim kaybolsun (süpürme bir bin içinde). N'i 512 yap: çerçeve 1.7 µs > darbe; "SNR kaybı" satırı 2.3 dB desin ve eğim tek sütuna bulaşsın.
- **N = 1024: darbe kaybolur** preset'inde (SNR 0 dB) çerçeve 3.41 µs, doluluk %29; dikdörtgen çerçevede kayıp 5.3 dB olurdu (19.4 dB). Hann darbeyi *ortalarsa* zaman kapısı gibi davranır ve teori 23 dB'dir; ama %50 overlap'te en iyi çerçeve darbeyi ortalamaz — ölçülen değeri teoriyle karşılaştır, sonra overlap'i %87.5 yap ve farkın kapandığını gör. Darbe başlangıcını 0.3 µs'ye çek: darbe Hann'ın kenarına düşsün, tepe 10 dB'den fazla çöksün. N'i 256 yap: ≈ 22 dB ve hizalamaya çok daha az duyarlı.
- **Overlap'siz sınır** preset'inde 0.5 µs darbe iki çerçeveye bölünmüş, tepe zayıf; overlap'i %50, sonra %75 yap: altın çerçeve darbeyi bütün yakalasın ve tepe−taban 3–6 dB artsın.
- **Zayıf darbe (SNR −5 dB)**: N = 256'da hâlâ görünür (tepe−taban ≈ 17 dB); N = 1024'e geç ve overlap %50 iken tepenin gürültü zıplamalarından ayırt edilemez hâle gelişini izle. PW'yi 0.3 µs'ye indir: kısa darbe için uzun N felakettir, N = 64 kurtarır.
:::

## Kavram: tepe bulma, eşikleme ve eşzamanlı sinyaller

Spektrumdan PDW'ye giden yolun ilk adımı **tepe bulma**dır (peak search): her çerçevede
en büyük bin ve komşuları (interpolasyon için ±1) alınır. Tek tepe yetmez;
aynı çerçevede birden çok emiter olabilir, bu yüzden pratikte "yerel
maksimum + eşik üstü" bin'ler listelenir: bir bin, iki komşusundan büyükse
ve eşiği aşıyorsa tepedir. Eşik, tabanın kestirimine göre konur; gürültü
tabanı frekansla değişebildiğinden (DDC filtresinin kenarları, {{bolum:16}};
komşu güçlü emiterin sızıntısı) sabit eşik yerine frekans ekseninde
**komşu bin'lerden kestirilen adaptif eşik** kullanılır — bu, {{bolum:23}}'teki
CFAR'ın frekans ekseni versiyonudur ve orada ayrıntılı kurulur; burada
yalnızca şunu tut: zaman kolundaki CFAR'ın referans hücreleri zaman
örnekleriyken, frekans kolunda referans hücreler komşu bin'lerdir.

Frekans kolunun zaman koluna karşı en büyük üstünlüğü **eşzamanlı sinyal
ayrımı**dır. Aynı anda gelen iki darbe zaman kolunda tek bir zarf, tek bir
(bozuk) PDW üretir; frekansları ana lobdan (Hann ile ~2 bin, 600 kHz) fazla
ayrıksa FFT'de iki ayrı tepe, iki ayrı PDW olur. Ayrım sınırı pencerenin
ana lobu, dinamik aralık sınırı yan lobudur ({{bolum:19}}). Bu yüzden yoğun
ortamlarda frekans kolu yalnızca "RF alanını doldurmaz", PDW *sayısını*
belirler.

## Kavram: frekans kestirimi — bin'den Hz'e

Bin, ızgaradır; frekans kestirimi ızgaranın arasını okumaktır. Üç yöntem,
üç maliyet:

**1. FFT tepesi + interpolasyon.** Tepe bin'i k ve iki komşusunun
büyüklüğünden tepenin gerçek konumu kestirilir. **Parabolik** yöntem üç
dB değerine parabol uydurur; Hann pencerede (ana lob parabolden az sapar)
hata 0.02 bin'in altındadır, dikdörtgende 0.15 bin'e çıkar (sinc parabol
değildir). **Jacobsen** kestirimi kompleks bin'leri kullanır ve dikdörtgen
pencerede tam sonuç verir; pencereli veride bir düzeltme katsayısı gerekir.
Maliyet: tepe başına birkaç çarpma, FPGA'da ya da PS'te önemsiz.

:::formul id=tepe-interpolasyon baslik="Tepe interpolasyonu"
f: δ_{par} = frac{1}{2} · frac{P_{k−1} − P_{k+1}}{P_{k−1} − 2 P_k + P_{k+1}}      f = (k + δ) · Δf
f: δ_{Jac} = −Re[ frac{X_{k+1} − X_{k−1}}{2 X_k − X_{k−1} − X_{k+1}} ]      (dikdörtgen; Hann için × 2)
s: P_k | k'ıncı bin'in dB (ya da lineer) gücü | dB
s: X_k | k'ıncı bin'in kompleks değeri | —
s: δ | tepenin bin merkezine göre kesirli konumu | bin (−0.5 … 0.5)
s: Δf | bin genişliği | Hz
o: Hann, N = {{s:fft.n}}, ton bin 34.25'te (10.033 MHz): P = (−9.9, −0.4, −3.3) dB → δ_par = 0.266 → hata 0.016 bin = **4.6 kHz**. Dikdörtgende aynı ton için 0.156 bin = 45.6 kHz hata (kılavuz çekirdeğiyle doğrulanmış).
o: Jacobsen dikdörtgen: δ = 0.250 (tam). Kılavuzun periyodik Hann tanımıyla aynı ifade δ/2 verir; 2 ile çarpılır.
:::

**2. Anlık frekans (instantaneous frequency; faz farkı).** Kompleks örneklerde ardışık iki örneğin
faz farkı frekansı verir: $f = Δφ · f_s / 2π$ ({{bolum:2}}). Darbe boyunca bu
değerlerin ortalaması (kenarlar hariç) tek bir frekans kestirimidir; FFT
gerekmez, zaman kolunda darbe FSM'i açıkken hesaplanır. Avantajı çözünürlük
sınırının olmaması ve LFM'de eğimi doğrudan vermesi; dezavantajı düşük
SNR'da atan2 gürültüsünün hızla büyümesi (faz gürültüsü SNR ile ölçeklenir,
bin'ler gibi "toplamaz") ve aynı anda iki sinyal varsa anlamsız bir karışım
vermesi. Kılavuz çekirdeğinde `DSP.anlikFrekans`.

**3. Sıfır geçişi (zero crossing).** Reel IF sinyalinde sıfır geçişleri sayılır: T sürede M
geçiş → f ≈ M/(2T). Anlık frekansın reel, kaba hâli; IFM (instantaneous
frequency measurement) almaçlarının ({{bolum:7}}) sayısal karşılığıdır.
Sayısal almaçta I/Q varsa faz farkı her zaman daha iyidir; sıfır geçişi,
kompleks mixing öncesi ucuz bir "kaba RF" tahmini olarak yaşar.

Üç yöntemin de ortak sınırı vardır: hiçbiri SNR'ın ve gözlem süresinin izin
verdiğinden daha iyi olamaz. Bu sınır **CRLB**'dir (Cramér-Rao Lower Bound —
Cramér-Rao alt sınırı): yansız bir frekans kestiricisinin standart sapması
$1/(T·√SNR_{toplam})$ mertebesindedir. Sezgisi basit: frekans, fazın zamanla
değişim hızıdır; fazı ne kadar uzun izlersen (T) ve her ölçüm ne kadar az
gürültülüyse (SNR) eğimi o kadar iyi bilirsin. Darbe süresi T'yi
sınırlar — 1 µs'lik darbe için sınır 1 µs'tir, çerçeveni uzatman fayda
etmez.

:::formul id=crlb-frekans baslik="Frekans kestirimi için CRLB"
f: σ_f ≥ frac{f_s}{2π} · sqrt{ frac{12}{SNR · L · (L^2 − 1)} }  ≈  frac{√3}{π · T · sqrt{SNR · L}}
s: σ_f | frekans kestiriminin standart sapması (alt sınır) | Hz
s: SNR | örnek başına SNR, lineer (dB değil) | —
s: L | darbedeki örnek sayısı | örnek
s: T = L / f_s | darbe süresi | s
o: SNR = {{s:tespit.tespit_snr_db}} dB, L = {{s:ddc.darbe_ornek_sayisi}}, f_s = {{s:ddc.cikis_fs_msps}} MSPS → σ_f ≈ **5.7 kHz** (kılavuz çekirdeği `DSP.crlbFrekans`). Bin 293 kHz'in 1/50'si; PDW'nin 10 kHz LSB'si bu sınırın hemen üstündedir — makul.
o: SNR = 5 dB → 17.9 kHz; L = 100 (0.33 µs darbe), 15 dB → 29.4 kHz. Kısa ve zayıf darbede 10 kHz LSB anlamsızdır; PDW'nin RF alanı yanına **SNR alanı** bunun için konur ({{bolum:24}}).
:::

:::pasaport durak="FFT çıkışı (frekans kolu)" alan=sayisal
Alan: sayısal (FPGA)
!Frekans: {{s:fft.n}} bin × {{s:turetilmis_beklenen.fft_bin_khz}} kHz, −150 … +150 MHz (fftshift'li), bin 512 = NCO
!Tip: |X|² → dB (20 bit), tepe listesi (bin, δ, dB, çerçeve no)
!fs: 586 k çerçeve/s (N = {{s:fft.n}}, %{{s:fft.overlap_yuzde}} overlap); çerçeve 3.41 µs
!Bit: I/Q 16 → çekirdek 20 (takvim: son 6 kademe) → |X|² 40 → dB 20 bit
!Veri hızı: ham 12 Gbps (PS'e gitmez) → tepe listesi ≤ 8 × 64 bit / çerçeve ≈ 300 Mbps
SNR: bant içi 92 dB → tepe−taban 120 dB (CW, tam ölçek); 1 µs darbede −5.3 dB çerçeve kaybı
Gecikme: ≈ 2 N + 150 saat ≈ 7 µs (çerçeve sonundan tepe listesine)
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
RF gözüyle frekans kolu, süperheterodin almaçtaki "IF spektrum analizörü" ya
da kanallaştırılmış almaçtaki filtre bankasıdır ({{bolum:7}}, {{bolum:17}}):
N bin = N paralel dar bant kanal. Farkı, kanalların anlık kurulması ve
pencereyle şekillendirilebilmesidir. Frekans doğruluğu RF tarafında LO'nun
ve örnekleme saatinin doğruluğuyla sınırlanır: 10 ppm'lik referans 9.4 GHz'de
94 kHz hata demektir — CRLB'nin verdiği 5.7 kHz'in on katından fazla.
Sayısal kestirimin doğruluğu, saat referansının (OCXO/GPSDO, {{bolum:11}})
doğruluğundan iyi olamaz; PDW RF alanının mutlak doğruluğu çoğu zaman
saatle, göreli doğruluğu (aynı emiterin darbeleri arası) CRLB ile sınırlıdır.
::fpga::
Referans gerçekleme: ping-pong tampon 2 × 1024 × 32 bit (2 BRAM), Hann ROM
512 × 16 (dağıtık RAM), pipelined radix-2² çekirdek N = 1024, 20 bit veri
yolu, takvim 0x2AA'nın son altı kademeye uygulanmış hâli (register), twiddle
16 bit; çıkış doğal sırada ve fftshift, `k ^ 512` ile bedava (en üst adres
bitini tersle). |X|² için iki 20×20 çarpma (2 DSP), 40 bit; dB dönüşümü için
öncü sıfır sayacı + 256 girişli log₂ mantis LUT'u → 20 bit (Q12.8 dB). Tepe
bulucu: üç bin'lik kayan pencere, yerel maksimum ∧ eşik üstü, tepe başına
(k, P_{k−1}, P_k, P_{k+1}) → parabolik δ PS'te ya da küçük bir bölme
çekirdeğiyle FPGA'da. Kaynak toplamı ~50 DSP, ~14 BRAM, ~6 k LUT (mertebe;
üreticiye göre değişir, doğrulanmadı). Gecikme çerçeve sonundan tepe
listesine ≈ 1024 (çekirdek) + 1024 (doğal sıra tamponu) + ~150 ≈ 7.3 µs.
%50 overlap için çekirdek 600 MHz'de çalışamayacağından iki çekirdek
dönüşümlü (çift/tek çerçeve) kullanılır ({{bolum:12}} SSR mantığı).
::yazilim::
Yazılımcının gördüğü register'lar: `FFT_LOG2N` (10), `FFT_SCALE_SCH`
(takvim; yazılım *okur*, değiştirmez), `FFT_WIN_SEL`, `FFT_THR` (dB, Q8.4),
`FFT_MAXPK` (çerçeve başına tepe sayısı sınırı) ve tepe FIFO'su. Her tepe
kaydında bin numarası, üç komşu dB değeri ve çerçeve sayacı gelir; yazılım
δ'yı hesaplar, bin → Hz → RF dönüşümünü ({{bolum:18}}'deki fonksiyon) uygular
ve çerçeve sayacını zaman kolunun TOA'sıyla eşler (çerçeve merkezi = sayaç ×
512 / 300 MHz). En sık hata: blok kayan nokta açıkken üssü okumamak (tüm
seviyeler 6·üs dB kayar) ve fftshift'li bin ile fftshift'siz bin
formüllerini karıştırmak.
:::

:::matlab-fpga
::matlab::
Modelde tepe bulma ve interpolasyon üç satırdır; bit-true karşılığı tepe
FIFO'sundaki üçlüyle aynı sonucu vermelidir:

```matlab
X  = fftshift(fft(x .* hann(N, 'periodic')));      % kompleks çerçeve
P  = 20*log10(abs(X) / sum(hann(N,'periodic')));   % dBFS
[~, k] = max(P);                                     % tepe bin (1 tabanlı)
d  = 0.5 * (P(k-1) - P(k+1)) / (P(k-1) - 2*P(k) + P(k+1));   % parabolik
f  = (k - 1 - N/2 + d) * fs / N;                     % Hz, baseband
```
::fpga::
Tepe bulucunun RTL iskeleti (doğal sıralı akış üzerinde üç bin'lik pencere):

```verilog
// p_dm1, p_d0, p_dp1: ardışık üç bin'in dB değeri (20 bit), k: orta bin
wire yerel_maks = (p_d0 >= p_dm1) && (p_d0 > p_dp1);
wire esik_ustu  = (p_d0 > thr_db);
always @(posedge clk)
  if (yerel_maks && esik_ustu && pk_say < maxpk) begin
    fifo_din <= {cerceve_no[15:0], k[9:0], p_dm1, p_d0, p_dp1};  // 76 bit
    fifo_wr  <= 1'b1; pk_say <= pk_say + 1;
  end
// δ (parabol) PS'te: tek bölme; FPGA'da istenirse 16 girişli LUT ile yaklaşık
```

Bit-true karşılaştırma ({{bolum:13}}): MATLAB'ın `P(k−1:k+1)` üçlüsü ile
FIFO'daki üç dB değeri, log₂ LUT'un çözünürlüğü (1/256 dB) içinde eşit
olmalı; δ farkı 0.01 bin'i (3 kHz) aşıyorsa LUT ya da ölçekleme takviminde
sorun vardır.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>
#include <math.h>

/* Kurgusal, öğretici: tepe FIFO kaydı (76 bit, donanım 2 x 64 bit'e paketler) */
typedef struct { uint16_t cerceve; uint16_t bin; int32_t p_m1, p_0, p_p1; /* Q12.8 dB */ } fft_tepe_t;

#define FFT_SCALE_SCH  0x48   /* RO: 2 bit x 5 kademe çifti, MSB = ilk kademe çifti  */
#define FFT_BFP_EXP    0x4C   /* RO: blok kayan nokta üssü (son çerçeve), BFP modunda */

/* Toplam kaydırmayı takvimden çıkar (dBFS ölçeğini geri almak için) */
static int fft_toplam_kaydirma(uint32_t sch) { int s = 0; for (int i = 0; i < 5; i++) s += (sch >> (2 * i)) & 3; return s; }

/* dB (Q12.8, donanım |X|² üzerinden 10log10 aldı) → dBFS: kaydırma ve pencere telafisi */
static double fft_db_to_dbfs(int32_t q128, int toplam_kaydirma, double sum_w, double tam_olcek)
{
    double db = q128 / 256.0;
    db += 20.0 * log10(ldexp(1.0, toplam_kaydirma));      /* takvimi geri al: +6.02 dB / bit */
    db -= 20.0 * log10(sum_w * tam_olcek);                  /* ∑w (Hann: 512) ve 16-bit tam ölçek */
    return db;
}

/* Parabolik interpolasyon → baseband frekans (Hz). bin: doğal sıralı, fftshift'li (512 = DC) */
static double fft_tepe_frekans(const fft_tepe_t *t, uint32_t N, double fs)
{
    double ym = t->p_m1 / 256.0, y0 = t->p_0 / 256.0, yp = t->p_p1 / 256.0;
    double payda = ym - 2.0 * y0 + yp;
    double d = (payda == 0.0) ? 0.0 : 0.5 * (ym - yp) / payda;   /* −0.5 .. +0.5 bin */
    if (d > 0.5) d = 0.5; if (d < -0.5) d = -0.5;                /* gürültüde taşmayı kırp */
    return ((double)t->bin - (double)N / 2 + d) * fs / (double)N;
}
/* referans: bin = 546, üçlü (−9.9, −0.4, −3.3) dB → d = 0.266 → f_bb = 34.27 · 292 969 Hz = 10.038 MHz */
```

Üç not: (1) `d` gürültülü tepe komşularında ±0.5'i aşabilir; kırpmazsan
frekans komşu bin'e "zıplar". (2) İki tepe bitişikse (ana lob içinde iki
emiter) parabol anlamsızdır — `p_m1` ve `p_p1`'den biri de yerel maksimumsa
interpolasyonu atla ve PDW'ye "çözünürlük altı" bayrağı koy. (3) dB'den
interpolasyon Hann için iyidir; dikdörtgen pencerede lineer güçle ya da
Jacobsen ile yap, yoksa 45 kHz'lik sistematik hata PDW'ye gömülür.

:::tuzak "N = 1024 seçtik çünkü çözünürlük iyi"
Sürekli sinyaller için doğru, darbeler için yanlış karar. 1 µs'lik darbe
1024'lük çerçevede 5.3 dB, 0.3 µs'lik darbe 10.5 dB SNR kaybeder;
zaman kolunun 15 dB ile gördüğü darbeyi frekans kolu 4.5 dB ile arar ve
bulamaz. PDW'lerde "RF alanı boş" oranı artınca ekip FFT'nin eşiğini
düşürür, bu kez yanlış alarm patlar. Doğru çözüm N'i darbe süresine
uydurmak (FSM tetikli çerçeve seçimi ya da zaman kapısı) ve ince frekansı
interpolasyon / faz farkıyla almaktır; ızgara inceliği doğruluk değildir.
:::

:::tuzak Ölçekleme takvimini "taşma olmasın" diye en başa yığmak
Sayısal tasarımcı taşma korkusuyla ilk kademelerde kaydırır: 16 bitlik
çekirdek, tam ölçek girişte asla taşmaz, herkes mutludur. Sonra hassasiyet
ölçümünde frekans kolu zaman kolundan 20 dB geride çıkar. Neden: kaydırma
sinyal henüz LSB'nin altındayken yapılmıştır, o LSB'ler yuvarlanıp gitmiştir.
Bit-true model bunu ilk günden gösterir ({{bolum:13}}); göstermiyorsa modelde
kaydırma yoktur. Kural: kaydırmalar sona, veri yolu giriş + kaydırmasız
kademe sayısı kadar geniş, ya da blok kayan nokta.
:::

:::tuzak Anlık frekansı LFM darbede "ortalamak"
Faz farkından frekans ölçen bir tasarım, 10 MHz süpüren LFM darbede darbe
boyunca ortalama alır ve merkez frekansı doğru bulur — ama bir CW darbe
sanır, MOP alanı boş kalır ve iki farklı emiterin (CW 9.400 GHz ve LFM
9.395–9.405 GHz) PDW'leri aynı görünür. Ortalamadan önce anlık frekansın
darbe içindeki *eğimini* ve yayılımını (standart sapma) ölç: eğim → LFM ve
bant genişliği; yayılım gürültüden beklenen değerin (CRLB'den) üstündeyse
darbe içi modülasyon vardır ({{bolum:25}}).
:::

:::ozet
- Pipelined FFT sürekli akışta örnek başına bir saat, gecikme ≈ N + pipeline; burst FFT az kaynak ama akışa yetişmez. %50 overlap çekirdeği 2× hızda ister → iki çekirdek dönüşümlü.
- Bit büyümesi log₂N: 16 → 26 bit. Ölçekleme takvimi hassasiyet ayarıdır: kaydırmayı son kademelere koy (20 bit, son 6 kademe → taban idealin 3 dB içinde); her kademede kaydıran 16 bit çekirdek 22 dB kaybeder. Blok kayan nokta en iyi taban, üssü okumayı unutma.
- STFT/spektrogram: N ↔ zaman çözünürlüğü, pencere, overlap. CW yatay çizgi, LFM eğik çizgi; N darbe süresine ve modülasyon BW'sine göre seçilir. Ham spektrum PS'e gitmez (12 Gbps); tepe listesi gider.
- Kısa darbe: tepe−taban = SNR + 10·log10(min(L,N)²/N); N > L kaybı 10·log10(N/L) (1 µs, N = 1024 → 5.3 dB). Çözüm: FSM tetikli çerçeve, zaman kapısı, paralel N.
- Tepe bulma = yerel maksimum ∧ eşik; eşik komşu bin'lerden adaptif (frekans ekseninde CFAR, Bölüm 23). Frekans kolu eşzamanlı emiterleri ayırır: sınır ana lob ve yan lob.
- Frekans kestirimi: parabolik/Jacobsen interpolasyon (Hann'da < 0.02 bin ≈ 5 kHz), anlık frekans (faz farkı; LFM eğimini verir; düşük SNR'da kötü), sıfır geçişi (kaba). Hepsinin sınırı CRLB: 15 dB, 1 µs → ≈ 5.7 kHz; mutlak doğruluk saat referansıyla sınırlı.
- FFT çıkışı pasaportu: 1024 bin × 293 kHz, 20 bit dB, 586 k çerçeve/s, tepe listesi ≈ 300 Mbps, gecikme ≈ 7 µs.
:::

:::kendini-sina
S: 16 bitlik I/Q ile N = 4096 pipelined FFT: ölçeksiz çıkış kaç bit? 20 bitlik veri yolunda kaç kademe kaydırmasız geçebilir ve toplam kaç bit kaydırılır?
C: 16 + 12 = 28 bit. 20 bit veri yolunda 4 kademe kaydırmasız (16 → 20), kalan 8 kademe birer bit kaydırır: toplam 8. Yazılım dBFS için 2^8 = +48.2 dB geri ekler.
S: 0.2 µs'lik bir darbe (60 örnek) için N = 1024 çerçevede SNR kaybı nedir? Aynı darbe N = 64 ile alınırsa bin genişliği ve kayıp?
C: 10·log10(1024/60) = 12.3 dB kayıp. N = 64: 4.69 MHz bin, kayıp 10·log10(64/60) = 0.3 dB. 15 dB'lik darbe ilkinde 2.7 dB'ye düşer (görünmez), ikincisinde 14.7 dB kalır ama frekans yalnızca ±2 MHz mertebesinde bilinir; interpolasyonla ve CRLB'ye göre (15 dB, 60 örnek) ≈ 63 kHz'e inilebilir.
S: Tepe FIFO'sundan (−9.0, −2.0, −4.0) dB üçlüsü geldi (Hann). δ ve baseband frekansı (bin 600, N = 1024, fs = 300 MSPS)?
C: δ = 0.5·(−9 − (−4)) / (−9 − 2·(−2) − 4) = 0.5·(−5)/(−9) = 0.278 bin. f = (600 − 512 + 0.278) · 292.97 kHz = 25.86 MHz. Hann'da bu kestirimin hatası 0.02 bin (6 kHz) içindedir.
S: Frekans kolu tepe listesini çerçeve sonundan 7 µs sonra üretiyor; zaman kolu darbeyi 0.3 µs'te tespit ediyor. PDW nasıl birleştirilir ve hangi alan geç dolar?
C: Zaman kolu TOA/PW/PA'yı üretip PDW'yi tamponda tutar; frekans kolu çerçeve sayacını TOA'ya eşleyerek (çerçeve merkezi = sayaç × 1.71 µs) RF/δ/MOP alanlarını sonradan doldurur. RF alanı geç dolar; PDW FIFO'ya yazma 7–10 µs gecikir ya da RF ayrı bir güncelleme kaydıyla gönderilir (Bölüm 26).
S: Aynı emiterin ardışık darbelerinde RF ölçümü 4 kHz sapıyor, ama başka bir almaçla karşılaştırınca 80 kHz sistematik fark var. Hangisi CRLB, hangisi ne?
C: 4 kHz göreli saçılım CRLB mertebesidir (15 dB, 1 µs → 5.7 kHz sınırı). 80 kHz sistematik fark saat/LO referansının ppm hatasıdır (9.4 GHz'de 8.5 ppm) ya da bin → RF dönüşümündeki bir ofset (NCO frekansı, evriklik). Kestirici değil, referans kalibre edilir.
:::

:::kopru
Frekans kolu artık tepe listesi üretiyor; zaman kolu da darbe zarfı. İkisinde
de aynı soru bekliyor: "bu tepe gerçekten sinyal mi, yoksa gürültünün bir
zıplaması mı?" Eşik nereye konur, gürültü nasıl kestirilir, saniyede kaç
yanlış alarm kabul edilir? Kısım VII bu soruyu tespit teorisinin temelinden
başlayarak kurar: iki olasılık dağılımı, aralarında bir çizgi ve o çizginin
her milimetresinin bedeli.
:::
