# Bölüm 26 — Darbe Durum Makinesi ve PDW Veri Yolu
::meta onkosul=12,13,22,23,24,25 acar=27,28,29,30 blok=pdw,ps rota=yazilimci,sayisal

:::neden-onemli
Sahadan soru: "Yoğun ortamda `PDW_DROP_CNT` artıyor, sıra numaraları
atlıyor, ara sıra 3 ms'lik 'darbe' geliyor ve bir CW verici açılınca FIFO
saniyeler içinde doluyor. Hangisi donanım hatası, hangisi tasarım gereği?"
Hepsi tasarım gereği — ve hepsinin bir register'ı var. Eşik karşılaştırıcısının
"var/yok" bitini bir PDW'ye çeviren şey, gürültü çentiğini darbeden, biten
darbeyi süren darbeden, CW'yi uzun darbeden ayırmak zorunda olan küçük bir
durum makinesidir. Onun ürettiği PDW'nin PS'teki tamponuna ulaşması ise bir
FIFO, bir DMA ve bir okuma döngüsü ister; her birinin taşma davranışı, kesme
politikası ve kayıp sayacı vardır. Bu bölüm o mekanizmayı FSM'den C
iskeletine kadar açar.
:::

## Sezgi: kapıdaki görevli

Bir konser salonunun kapısındaki görevli sayım tutuyor: kapı açıldı — biri
giriyor mu, yoksa rüzgâr mı? Kapı kapandı — çıktı mı, yoksa eşikte durup
konuşuyor mu? Görevli iki kural koyar: "kapı en az iki saniye açık kalırsa
giriş sayarım" (**min PW**) ve "kapandıktan sonra bir saniye içinde yeniden
açılırsa aynı kişidir" (**histerezis / kenar çentiği toleransı**). Bir de
"beş dakikadır açıksa kapı bozuk demektir, not düşüp saymaya devam ederim"
(**zaman aşımı**). Darbe FSM'i tam bu görevlidir; kuralları register'lardır ve
her kural bir tür hatayı önlerken başka bir tür darbeyi kaçırma riskini
taşır. Görevlinin defteri FIFO'dur; defter dolarsa ya yeni gelenler ya da en
eski satırlar kaybolur — ikisi de bir politikadır.

## Kavram: darbe FSM'i

{{svg:g-260-darbe-fsm.svg|Darbe durum makinesi. IDLE'da güç eşiği (T_on) aşınca RISING'e geçilir ve TOA sayacı kilitlenir; k_r ardışık örnek üstte kalırsa IN_PULSE (tepe, güç toplamı, faz farkı toplamı biriktirilir), kalmazsa gürültü sivrisi sayılıp IDLE'a dönülür. Güç T_off altına inince FALLING; k_f örnek altta kalırsa EMIT (PW hesaplanır, PDW paketlenip FIFO'ya yazılır), k_f dolmadan yeniden T_on aşılırsa kenar çentiği sayılıp IN_PULSE'a dönülür. IN_PULSE'ta örnek sayacı DET_MAX_PW'ye ulaşırsa SEG bayraklı parça PDW yayımlanır ve darbe izlenmeye devam edilir. Öğretici şema.|kaydir}}

Beş durum, dört register. **IDLE**: güç zarfı ($I^2+Q^2$, video filtreli —
{{bolum:22}}) eşiğin altındadır; eşik sabit ya da CFAR'dan gelir ({{bolum:23}}).
İlk aşımda **RISING**'e geçilir ve serbest koşan sayaç TOA olarak kilitlenir.
RISING geçici bir doğrulama durumudur: $k_r$ ardışık örnek (tipik 1–4) üstte
kalmazsa bu bir gürültü sivrisiydi, IDLE'a dönülür ve hiçbir şey yazılmaz.
**IN_PULSE** asıl ölçüm durumudur: tepe tutucu, güç toplayıcı, faz farkı
biriktirici ve örnek sayacı çalışır ({{bolum:25}}). Güç $T_{off} = T_{on} −$
histerezis altına düşünce **FALLING**; burada da $k_f$ örnek beklenir — bu
sürede güç yeniden $T_{on}$'u aşarsa darbe bitmemiş, kenarda bir gürültü
çentiği görülmüştür; IN_PULSE'a dönülür ve sayaçlar sıfırlanmaz. $k_f$
dolunca **EMIT**: PW = bitiş − TOA, PA ve frekans son değerlerini alır, 128
bit paketlenir, `wr_en` ile FIFO'ya yazılır, sıra sayacı artar; tek saat
sürer ve IDLE'a dönülür. PW `DET_MIN_PW`'den küçükse EMIT yazmaz, atar.

Histerezis ve $k_r/k_f$ aynı sorunu iki açıdan çözer: gürültü, eşik civarında
gezinen bir zarfın eşiği bir örnekte on kez kesmesine yol açar. Histerezis
"çıkış eşiğini" düşürerek, doğrulama sayaçları "kararı geciktirerek" bu
titreşimi yutar. Bedel: TOA doğrulama kadar geç kesinleşir (ama kilitlenen
değer ilk geçiştir, gecikme yalnızca kararda) ve PW, $k_f$ kadar değil,
$T_{off}$ geçişine kadar sayılır. Referans senaryoda histerezis
{{s:tespit.histerezis_db}} dB, min PW {{s:tespit.min_pw_ornek}} örnek,
$k_r = k_f = 2$'dir.

### Zaman aşımı: uzun darbe ve CW

Bir CW verici ya da 3 ms'lik uzun darbe IN_PULSE'ta sonsuza kadar kalır; PW
sayacı 20 biti aşar, FIFO'ya hiçbir şey yazılmaz ve yazılım "almaç sustu"
sanır. **DET_MAX_PW** bunun için vardır: örnek sayacı bu değere ulaşınca FSM
bir **parça PDW** yayımlar — `SEG` bayrağı kalkık, PW = MAX_PW, PA ve frekans
o parçanın ölçümü — ve IN_PULSE'ta kalır; sayaçlar sıfırlanır, bir sonraki
parçanın TOA'sı bu parçanın bitişidir. CW böylece periyodik PDW dizisine
dönüşür: PW = MAX_PW, PRI = MAX_PW, hepsi SEG bayraklı. Yazılım bunu tanır
ve tek bir "CW emiter" kaydına indirger. MAX_PW seçimi bir dengedir:
kısa (100 µs) seçersen CW 10 000 PDW/s üretip FIFO'yu boğar; uzun (3 ms)
seçersen PW alanı sınırına ({{bolum:24}}, 3.5 ms) yaklaşırsın ve gerçek uzun
darbeler geç raporlanır. Referans tasarımda 1 ms; kurgusal.

### Çakışan ve çok yakın darbeler

**Pulse-on-pulse** (POP): bir darbe sürerken ikinci, daha güçlü bir darbe
başlar. Zarf tek bir uzun darbe gibi görünür; PW ikisinin birleşimidir, PA
güçlü olanın, frekans ikisinin karışımıdır. FSM'in tek başına ayrıştırması
beklenmez; görevi **bayrak kaldırmaktır**: IN_PULSE içinde tepe birden
sıçrarsa (≥ 6 dB) ya da anlık frekans pencere ortalamasından koparsa (birkaç
ardışık örnek, bir eşikten büyük sapma) `POP` biti kalkar ve yazılım bu PDW'yi
güvenilmez sayar; snapshot varsa ham veriye döner. **Çok yakın darbeler**
(aralık < $k_f$ + histerezis toparlanma süresi): iki darbe tek PDW'ye
birleşir. Bu FSM'in çözünürlük sınırıdır — referans ayarlarla yaklaşık 10
örnek, 33 ns; daha yakın darbeleri ayırmak için ya $k_f$ küçültülür (çentik
toleransı düşer) ya da frekans kolu iki tepe gösterdiğinde POP bayrağı
kaldırılır.

## Kavram: iki kolun hizalanması

{{bolum:0}}'daki posterde iki kol vardı: **zaman kolu** (zarf → eşik → FSM →
ölçüm) ve **frekans kolu** (pencere → FFT → tepe). Aynı darbenin iki koldan
gelen sonuçları tek PDW'de buluşmalıdır; ama gecikmeleri çok farklıdır.

{{svg:g-262-latency-hizalama.svg|İki kolun gecikmesi (referans darbe 1 µs, t = 1.0 µs'de başlar). Zaman kolu zarf + filtre + CFAR penceresiyle ≈ 0.1 µs gecikir; FSM darbe bitiminden ≈ 0.2 µs sonra EMIT'e ulaşır ve faz tabanlı frekans o anda hazırdır. Frekans kolu %50 örtüşen 3.41 µs'lik FFT çerçeveleriyle çalışır; darbeyi kapsayan çerçevenin bitişi ve ≈ 1124 saatlik boru hattından sonra (t ≈ 7.2 µs) tepe hazır olur. PDW birleştirici zaman kolunun sonucunu TOA anahtarıyla bekletir ve FFT sonucu gelince FIFO'ya yazar.}}

Zaman kolunun gecikmesi küçüktür: zarf ve kayan ortalama birkaç örnek, CFAR
penceresi ($N/2$ + guard + CUT ≈ 11 örnek tek tarafta) ve FSM'in $k_f$
doğrulaması. Toplam ≈ 30–40 örnek, 100–130 ns; darbe bittikten ≈ 0.2 µs
sonra PDW'nin zaman alanları hazırdır. Frekans kolu **çerçeve** bazlıdır:
N = {{s:fft.n}} noktalık FFT {{s:fft.gozlem_suresi_us}} µs'lik çerçeve
doldurulmadan başlayamaz, ardından boru hattı (yaklaşık $N$ + ~100 saat)
ve tepe arama gelir. Darbeyi tam kapsayan çerçevenin sonucu, darbe bitiminden
3–5 µs sonra gelir; darbe iki çerçeveye bölünmüşse ({{bolum:20}}'deki
darbe–pencere hizalama sorunu) hangi çerçevenin sonucu kullanılacağı da bir
karardır (en büyük tepe olan).

Hizalamanın iki yolu var. **Sabit gecikme**: zaman kolunun sonucu, frekans
kolunun azami gecikmesi kadar (birkaç µs, birkaç yüz 128-bit sözcük) bir
gecikme hattında bekletilir ve iki kol sabit bir ofsetle birleştirilir; basit,
ama her PDW en kötü gecikmeyi öder ve darbe yoğunluğu arttıkça gecikme hattı
dolar. **TOA anahtarıyla eşleştirme**: zaman kolu PDW'yi küçük bir "bekleyen"
tablosuna TOA ile yazar; frekans kolu her tepeyi ait olduğu çerçevenin zaman
aralığıyla etiketler; birleştirici, çerçeve aralığı TOA'yı kapsayan tepeyi
PDW'ye yazar ve yayımlar. Eşleşme bulunamazsa (darbe çerçeve sınırında
kaybolmuş, ya da FFT kolu aynı çerçevede iki darbe görmüş) PDW yine
yayımlanır: RF alanı faz tabanlı ölçümden, BW alanı "bilinmiyor", kalite
düşük. Referans tasarım bu ikinci yolu izler; zaten frekansın ana kaynağı
FSM içindeki faz tabanlı ölçümdür ({{bolum:25}}), FFT kolu BW, MOP
doğrulaması ve çoklu sinyal için yardımcıdır. Her iki yolda da **latency
eşitleme** kelimesi tek bir şeyi anlatır: iki kolun *aynı örneğe* ait
sonuçlarının aynı anda bir araya gelmesi; bunun için her kolun gecikmesi
örnek cinsinden bilinmeli ve register'a değil, tasarım belgesine yazılmalıdır.

## Kavram: PDW FIFO, paketleme, AXI-Stream → DMA → PS

{{svg:g-261-pdw-veri-yolu.svg|PDW veri yolu. DDC çıkışı üç dala ayrılır: zaman kolu (I²+Q² + kayan ortalama → eşik → darbe FSM → ölçüm), frekans kolu (FFT 1024 → tepe bulma → TOA eşleme) ve ön-tetikli snapshot RAM. PDW birleştirici iki kolu eşler, paketleyici 4 × 32 bit üretir, 1024 derinlikli 128-bit FIFO tamponlar, AXI-Stream DMA'ya (S2MM) akar, DMA PS'teki halka tampona yazar. Yeşil register'lar FIFO seviyesi/kontrolü, drop ve PDW sayaçları, kesme durumu/maskesi. FIFO dolunca gelen PDW atılır, DROP_CNT artar ve IRQ bit1 kalkar. Snapshot ikinci DMA kanalıyla okunur.|kaydir}}

EMIT'te paketlenen 128 bit önce bir **FIFO**'ya yazılır; çünkü darbeler
düzensiz, DMA ise bloklar halinde çalışır. FIFO'nun derinliği (referans:
1024 × 128 bit = 16 KB, bir avuç BRAM) ve PS'in okuma hızı birlikte bir
**bant genişliği bütçesi** kurar. Her PDW için tüketilen kaynak üç kalemdir:
AXI-Stream/DMA bant genişliği (önemsiz: 128 bit × 1 M PDW/s = 128 Mbps,
150 MHz'lik 128-bit AXI-Stream 19.2 Gbps taşır), DDR yazma (aynı), ve **PS
işlem süresi** — asıl darboğaz. Yazılım PDW başına 200 ns harcıyorsa 1 M
PDW/s bir çekirdeğin %20'sidir; 5 M PDW/s'de çekirdek dolar ve FIFO taşar.
Bu yüzden PDW okuma döngüsü parse etmez, **kopyalar**: DMA tamponundan
uygulama kuyruğuna 16 baytlık blok kopya, parse ve deinterleaving ayrı
iş parçacığında.

FIFO'dan çıkan sözcükler **AXI-Stream** olarak DMA motoruna (S2MM: stream'den
belleğe) akar. DMA, PS'in hazırladığı **tanımlayıcı** (descriptor)
zincirini izler: her tanımlayıcı bir DDR adresi ve uzunluk (referans: 4 KB =
256 PDW… hayır — 4 KB / 16 B = **256 PDW**) tutar; tanımlayıcı dolunca DMA
sonrakine geçer ve isteğe bağlı bir kesme üretir. Tanımlayıcılar bir **halka**
oluşturur: 64 tanımlayıcı × 4 KB = 256 KB = 16 384 PDW; 1 M PDW/s'de 16 ms'lik
tampon. Tanımlayıcı **paket sonu** (TLAST) beklerse ve darbe seyrekse tampon
hiç dolmaz: bu yüzden ya PL belli aralıkla TLAST üretir (zaman aşımı) ya da
DMA "kısmi tanımlayıcı" ile çalışır ve PS dolu bayt sayısını okur.

### Kesme mi, polling mi?

**Kesme** (IRQ): `IRQ_STATUS` bit0 "FIFO yarım dolu", bit1 "taşma", bit4
"snapshot hazır" ({{bolum:30}}). Seyrek darbede verimlidir: CPU boşta uyur,
PDW gelince uyanır. Yoğun ortamda felakettir: 1 M PDW/s'de her 512 PDW'de bir
kesme = saniyede 2 000 kesme; kabul edilebilir, ama tanımlayıcı başına kesme
(saniyede 4 000) ve PDW başına kesme (1 000 000) değildir. **Polling**: PS
periyodik olarak (ör. her 1 ms) DMA'nın yazdığı son adresi ya da
`PDW_FIFO_LEVEL`'i okur ve gelen bloğu işler. Gecikme periyot kadardır,
yük sabittir ve yoğunlukla artmaz. Pratik çözüm **melez**: normalde polling
(sabit yük, öngörülebilir gecikme), FIFO yarım ve taşma kesmeleri açık
(acil durum). Kesme işleyicisi yalnızca bir bayrak kaldırır; işi döngü
yapar. `IRQ_STATUS` yapışkandır (sticky) ve W1C ile temizlenir — temizlemeden
dönen işleyici sonsuza kadar tekrar tetiklenir.

### Taşma politikası ve drop sayaçları

FIFO dolduğunda iki seçenek vardır ve `PDW_FIFO_CTRL` bit1 seçer: **yeniyi at**
(varsayılan; en eski veri korunur, akış tutarlı kalır) ya da **en eskiyi at**
(en güncel durum korunur; gerçek zamanlı uyarı sistemlerinde tercih edilir).
Hangisi seçilirse seçilsin atılan her PDW `PDW_DROP_CNT`'yi artırır ve
`IRQ_STATUS` bit1 kalkar. PDW içindeki 8 bitlik **SEQ** alanı bağımsız bir
kayıp dedektörüdür: yazılım her PDW'de `seq == (önceki + 1) mod 256`
bekler; fark 1'den büyükse arada `fark − 1` PDW kaybolmuştur. 8 bit yalnızca
255'e kadar boşluğu güvenle sayar; daha büyük kayıp `PDW_COUNT` (toplam
üretilen) ile `DROP_CNT` karşılaştırılarak çözülür. Kayıp asla sessiz
kalmamalıdır: deinterleaving için "bir darbe gelmedi" ile "bir darbe
kaybedildi" tamamen farklı hipotezlerdir ({{bolum:27}}).

### Darbe yoğunluğu bütçesi

:::formul id=pdw-butce baslik="PDW bant genişliği ve FIFO dolum süresi"
f: R_{PDW} = b_{PDW} · λ
f: t_{dolum} = frac{D_{FIFO}}{λ − r_{PS}}      (λ > r_{PS} iken)
s: λ | darbe (PDW) yoğunluğu | PDW/s
s: b_{PDW} | PDW uzunluğu | bit
s: D_{FIFO} | FIFO derinliği | PDW
s: r_{PS} | PS'in sürekli tüketebildiği hız (0 = PS duraklamış) | PDW/s
o: Referans: λ = {{s:sinyal.prf_hz}} → R_PDW = **128 kbps**; PS 1 ms'lik polling'de dursa bile FIFO'da yalnızca 1 PDW birikir.
o: Yoğun ortam λ = 10⁶: R_PDW = **128 Mbps** (AXI-Stream'in 19.2 Gbps'sinin binde yedisi); PS duraklarsa D = 1024 ile t_dolum = **1.02 ms** — polling periyodu ve en uzun kesme gecikmesi bunun altında kalmalı. DMA halkası (16 384 PDW) 16 ms ek pay verir.
:::

Bir almaçın "kaç darbe/s kaldırdığı" tek bir sayı değil, bir zincirdir:
FSM saniyede en fazla $f_s / (min PW + k_f + 1)$ PDW üretebilir
(referans ayarlarla ≈ 43 M/s — pratikte hiç ulaşılmaz); FIFO derinliği
PS'in yanıt süresini belirler (1024 PDW, 1 M PDW/s'de **1 ms**: polling
periyodu bundan kısa olmalı); DMA halkası PS'in işlem dalgalanmasını yutar
(16 ms); PS işlem hızı ortalamayı sınırlar. Yoğunluk tasarım sınırını aşınca
FSM'e "ön filtre" konur: yalnızca belirli RF/PW aralığındaki darbeler PDW
olur (**PDW filtresi** register'ları — kurgusal haritada yok, gerçek
tasarımlarda yaygın), gerisi yalnızca sayılır. Atmak zorundaysan, ne
attığını sayarak at.

## Kavram: tetiklemeli ham I/Q snapshot

PDW kayıplı bir özettir ({{bolum:24}}); POP bayraklı, MOP'u "bilinmiyor" ya
da RF'i şüpheli bir darbede ham örneğe dönmek istersin. **Snapshot** yolu
bunun için var: DDC çıkışı sürekli olarak küçük bir halka RAM'e yazılır
(`SNAP_PRETRIG` kadar ön-tetik derinliği), tetik gelince `SNAP_LEN` örnek
daha yazılıp durdurulur ve `SNAP_CTRL` bit2 "hazır" kalkar; PS ikinci bir DMA
kanalıyla ya da AXI-Lite ile okur, sonra yeniden **kurar** (bit1). Tetik
kaynağı yazılım (test) ya da "ilk tespit" (FSM'in RISING → IN_PULSE geçişi)
olabilir. Referans: 4096 örnek × 32 bit = 16 KB, 13.65 µs; 256 örneklik
ön-tetik darbenin öncesini ve yükselen kenarını tam gösterir. Snapshot bir
**doğrulama aracıdır** ({{bolum:29}}): PDW'deki PW ile snapshot'tan
MATLAB/Python'da ölçtüğün PW aynı mı; RF geri dönüş zinciri doğru mu; time
walk modeli kenar şekline uyuyor mu. Sürekli çalışan bir kanal değildir;
darbe başına yakalama sistemin PDW bütçesini değil, PS'in analiz süresini
tüketir.

:::pasaport durak="PDW FIFO çıkışı" alan=yazilim
Alan: PL → PS sınırı (AXI-Stream / DMA)
!Tip: 128-bit PDW kayıtları (4 × 32 bit, little-endian), darbe başına bir; örnek akışı bitti
!Frekans: alan olarak taşınır (RF, mutlak, 10 kHz LSB) — sinyalin kendisi artık yok
!Hız: 128 bit × {{s:sinyal.prf_hz}} PDW/s = **128 kbps** (referans); yoğun ortamda 1 M PDW/s → 128 Mbps
!Bit: 128 / PDW; FIFO 1024 derinlik = 16 KB; DMA tanımlayıcısı 4 KB = 256 PDW
!Gecikme: darbe bitiminden FIFO'ya ≈ 0.2 µs (yalnız zaman kolu) / ≈ 5 µs (FFT kolu eşlenince)
SNR: PDW alanı (kalite) — ölçüm belirsizliğinin ölçeği, {{bolum:25}}
Register: PDW_FIFO_LEVEL · PDW_FIFO_CTRL · PDW_DROP_CNT · PDW_COUNT · IRQ_STATUS[1:0]
:::

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
RF gözüyle FSM'in register'ları bir **hassasiyet–seçicilik** düğmesidir.
Min PW'yi yükseltmek gürültü sivrilerini eler ama kısa darbeli emiterleri
kaçırır; MAX_PW'yi kısaltmak CW'yi kontrol altında tutar ama uzun darbeleri
parçalar; histerezisi büyütmek çentiği yutar ama zayıf darbenin PW'sini
uzatır. Bu ayarların doğru değeri ortama bağlıdır; RF ekibi "beklenen darbe
sözlüğünü" (PW aralığı, yoğunluk, CW var mı) verir, yazılım register'a
çevirir ve **sayaçlarla** doğrular: atılan çentik sayısı, SEG oranı, POP
oranı birer sağlık göstergesidir.
::fpga::
FSM 5 durumlu, one-hot kodlu birkaç yüz LUT'luk bir bloktur; kritik yol
tepe karşılaştırıcısı ve 48-bit sayaçtır (300 MHz'de sorunsuz; SSR
gerekmez çünkü DDC çıkışı zaten 300 MSPS). PDW FIFO: 128 bit genişlik,
1024 derinlik, **bağımsız saatli** (CDC: DDC saati → AXI saati,
{{bolum:13}}), `prog_full` çıkışı IRQ "yarım" için, `overflow` bayrağı
sayaç için. Paketleyici bir saatte 128 biti sabit konumlara yerleştirir;
ardından AXI-Stream (TVALID/TREADY/TLAST, 128-bit TDATA) ve standart bir
S2MM DMA IP'si. Snapshot: 4096 × 32 bit basit çift portlu BRAM (4 adet 36
kb), yazma adresi serbest döner, tetikte "kalan örnek" sayacı başlar.
Latency eşitleme için bekleyen-PDW tablosu 16 girişli küçük bir CAM/RAM'dir;
16'dan çok darbe FFT sonucunu beklerken gelirse en eskisi frekanssız yayımlanır.
::yazilim::
Yazılımcının yüzeyi: `PDW_FIFO_CTRL` (etkin, taşma politikası, sıfırla),
`PDW_FIFO_LEVEL`, `PDW_DROP_CNT` (W1C), `PDW_COUNT`, `IRQ_STATUS`/`IRQ_MASK`,
DMA tanımlayıcı halkası, `SNAP_*`. Açılış sırası {{bolum:30}}'da: DMA halkası
kurulmadan FIFO **etkinleştirilmez**, yoksa ilk milisaniyede taşar ve
DROP_CNT'nin ilk değeri anlamsız olur. Okuma döngüsü aşağıda; ilkeleri:
kopyala-parse-etme, SEQ ile boşluk say, DROP_CNT ile karşılaştır, taşma
kesmesinde önce oku sonra temizle, EXT bayraklı PDW'de bir sözcük daha al.
:::

## Yazılımcıya dokunan yer

```c
/* PDW okuma döngüsü iskeleti — RTOS/bare-metal bağımsız, kurgusal harita (B30) */
#include <stdint.h>
#include <string.h>

#define PDW_BYTES        16u
#define DESC_BYTES       4096u                 /* 256 PDW / tanımlayıcı */
#define DESC_COUNT       64u                   /* halka: 256 KB, 16 384 PDW */
#define PDW_FLAG_EXT     (1u << 5)

typedef struct { uint32_t w[4]; } pdw_raw_t;

typedef struct {
    uint8_t  *halka;            /* DMA'nın yazdığı, önbelleğe alınmayan (uncached) bellek */
    uint32_t  okuma_ofs;        /* bizim kaldığımız bayt ofseti */
    uint8_t   son_seq;          /* son görülen sıra numarası */
    int       seq_gecerli;
    uint64_t  alinan, kayip_seq, kayip_fifo;
} pdw_okuyucu_t;

extern uint32_t reg_read32(uint32_t ofs);
extern void     reg_write32(uint32_t ofs, uint32_t v);
extern uint32_t dma_yazma_ofseti(void);     /* DMA'nın halkada geldiği bayt (tanımlayıcı durumundan) */
extern void     kuyruga_kopyala(const pdw_raw_t *p, int uzanti_var);
#define REG_PDW_DROP_CNT 0x068u
#define REG_IRQ_STATUS   0x080u
#define IRQ_FIFO_TASMA   (1u << 1)

/* Tek geçiş: DMA'nın yazdığı yere kadar olan PDW'leri tüket. Polling'den ya da
 * "FIFO yarım" kesmesinin kaldırdığı bayraktan çağrılır; kesme içinden değil. */
void pdw_isle(pdw_okuyucu_t *r)
{
    uint32_t yazma = dma_yazma_ofseti();
    uint32_t toplam = DESC_BYTES * DESC_COUNT;
    while (r->okuma_ofs != yazma) {
        pdw_raw_t p;
        memcpy(&p, r->halka + r->okuma_ofs, PDW_BYTES);        /* hizasız erişim güvenli */
        r->okuma_ofs = (r->okuma_ofs + PDW_BYTES) % toplam;

        uint8_t seq = (uint8_t)((p.w[3] >> 20) & 0xFFu);
        if (r->seq_gecerli) {
            uint8_t beklenen = (uint8_t)(r->son_seq + 1u);
            if (seq != beklenen)                                /* mod 256 boşluk */
                r->kayip_seq += (uint8_t)(seq - beklenen);
        }
        r->son_seq = seq; r->seq_gecerli = 1;

        int ext = (p.w[1] >> 26) & PDW_FLAG_EXT ? 1 : 0;        /* uzantı sözcüğü izliyor mu */
        if (ext) {
            if (r->okuma_ofs == yazma) { r->okuma_ofs = (r->okuma_ofs - PDW_BYTES + toplam) % toplam; break; } /* yarım geldi; sonraki geçişte */
            r->okuma_ofs = (r->okuma_ofs + PDW_BYTES) % toplam; /* uzantıyı da aldık */
        }
        kuyruga_kopyala(&p, ext);                               /* parse burada DEĞİL: başka iş parçacığında */
        r->alinan++;
    }
    /* donanım tarafı kayıp: taşma bayrağı ve sayaç — önce oku, sonra temizle */
    uint32_t irq = reg_read32(REG_IRQ_STATUS);
    if (irq & IRQ_FIFO_TASMA) {
        r->kayip_fifo += reg_read32(REG_PDW_DROP_CNT);
        reg_write32(REG_PDW_DROP_CNT, 1u);                      /* W1C */
        reg_write32(REG_IRQ_STATUS, IRQ_FIFO_TASMA);            /* W1C */
        /* SEQ boşluğu ile DROP_CNT tutarlı olmalı; değilse PL/PS arasında başka bir kayıp var */
    }
}
```

Beş nokta. (1) Halka bellek **uncached** ya da her geçişte önbellek
geçersizleştirmeli; aksi halde CPU eski PDW'leri okur ve "SEQ atlıyor"
sanırsın. (2) `dma_yazma_ofseti` DMA'nın **tamamladığı** tanımlayıcıdan
okunur; yazmakta olduğu bloğu tüketmek yarım PDW okutur. (3) SEQ farkı
`uint8_t` aritmetiğiyle alınır; `int`e çevirip çıkarırsan sarmada 255
yerine −1 bulursun. (4) EXT yarım gelmişse geri adım at, sonraki geçişte
tamamla. (5) Taşma işlemi kesme içinde değil döngüde: kesme bayrak kaldırır,
döngü sayacı okur ve temizler. `kayip_seq` ile `kayip_fifo` uzun vadede eşit
olmalıdır; değillerse FIFO'nun *sonrasında* bir kayıp var — genellikle
DMA halkasının üzerine yazılması, yani PS'in geç kalması.

:::tuzak Kesme içinde parse
Kurgusal vaka: "PDW gelince hemen işleyelim" diye FIFO-boş-değil kesmesinde
PDW okunup parse edilir, deinterleaving kuyruğuna atılır. Sakin ortamda
çalışır. Bir CW verici açılınca 10 000 PDW/s'lik SEG dizisi gelir, kesme
işleyicisi sistemi kilitler, watchdog resetler. Belirti: darbe yoğunluğuyla
orantılı gecikme ve rastgele resetler. Çözüm: kesme yalnızca bayrak, döngü
blok kopya, parse ayrı iş parçacığı; ve MAX_PW'yi CW'nin PDW hızını
kaldırılabilir tutacak kadar uzun seç.
:::

:::tuzak Taşma politikasını bilmeden sayaç yorumlamak
`PDW_FIFO_CTRL` bit1 "en eskiyi at" seçiliyken SEQ boşlukları en yeni değil
en eski PDW'lerde açılır: okuma döngüsü boşluğu, kaybın olduğu andan **1024
PDW sonra** görür. Yazılım kaybı yanlış zaman damgasına yazar ve "o anda
darbe yoğunluğu normaldi" der. Politika ne olursa olsun kayıp anını
`PDW_COUNT` ile (donanımın üretim sayacı) çapraz kontrol et; sayaç farkı
kaybın gerçek anını verir.
:::

:::tuzak Snapshot'ı kurmadan tetik beklemek
`SNAP_CTRL` bit1 (kur) W1P'dir: her yakalamadan sonra yeniden yazılmalıdır.
Yazılmazsa RAM'de ilk yakalama durur, "hazır" biti kalkık kalır ve her okuma
aynı eski darbeyi getirir. Ekip günlerce "darbeler hep aynı görünüyor, PL
donmuş" diye arar. Kural: oku → işle → **kur**; hazır bitini okumadan önce
kurma zamanını günlüğe yaz.
:::

:::ozet
- FSM: IDLE → RISING (TOA kilitlenir, k_r doğrulama) → IN_PULSE (tepe, güç, faz biriktir) → FALLING (T_off altında k_f doğrulama; çentikte geri dön) → EMIT (PW, paketle, FIFO'ya yaz, SEQ++). Min PW altı atılır.
- Histerezis ve doğrulama sayaçları eşik civarı titreşimi yutar; bedeli PW'nin eşik tanımına bağlılığı ve ~10 örneklik en küçük darbe aralığı.
- DET_MAX_PW zaman aşımı uzun darbe/CW'yi SEG bayraklı parça PDW'lere böler; POP bayrağı çakışan darbeyi işaretler, ayrıştırmaz.
- Zaman kolu ≈ 0.2 µs, frekans kolu 3–5 µs gecikir; birleştirme sabit gecikmeyle ya da TOA anahtarlı eşleştirmeyle yapılır; eşleşme yoksa PDW frekans kolu alanları boş yayımlanır.
- PDW FIFO (1024 × 128 bit) → AXI-Stream → DMA tanımlayıcı halkası (64 × 4 KB) → PS. Darboğaz PS işlem süresidir; döngü kopyalar, parse etmez.
- Kesme acil durumlar için (FIFO yarım, taşma), polling düzenli akış için; melez tasarım. IRQ_STATUS yapışkan, W1C.
- Taşma politikası (yeniyi/eskiyi at) register'la seçilir; kayıp DROP_CNT (donanım) ve SEQ boşluğu (yazılım) ile iki bağımsız yoldan sayılır ve tutarlı olmalıdır.
- Snapshot: ön-tetikli halka RAM, darbe başına ham I/Q; doğrulama aracıdır, sürekli kanal değildir; her yakalamadan sonra yeniden kurulur.
:::

:::kendini-sina
S: DET_MAX_PW = 1 ms iken bir CW verici saniyede kaç PDW üretir ve FIFO (1024) polling periyodu 5 ms olan bir PS'te taşar mı?
C: 1000 SEG PDW/s. 5 ms'de 5 PDW; FIFO taşmaz. MAX_PW = 10 µs seçilseydi 100 000 PDW/s olur, 5 ms'de 500 PDW birikir — yine sığar ama başka emiterlerle birlikte sınıra yaklaşır; 1 µs seçilseydi 1 M PDW/s ile 1 ms'de dolardı.
S: Okuma döngüsü SEQ boşluğu toplamda 300 buluyor, DROP_CNT 300 gösteriyor. Sonra SEQ boşluğu 900'e çıkıyor, DROP_CNT 300'de kalıyor. Nerede kayıp var?
C: İlk 300 FIFO taşmasıdır (iki sayaç tutarlı). Sonraki 600 FIFO'dan sonra kaybolmuştur: DMA halkasının üzerine yazılması (PS geç kalmış), tanımlayıcı hatası ya da önbellek tutarsızlığı. PL'yi değil PS tarafını incele.
S: Zaman kolu PDW'yi 0.2 µs'de hazırlıyor, FFT kolu 5 µs'de. Sabit gecikme yerine TOA anahtarlı eşleştirme neden tercih edilir?
C: Sabit gecikmede her PDW en kötü gecikmeyi öder ve gecikme hattı darbe yoğunluğuyla orantılı büyür (5 µs × 1 M PDW/s = 5 bekleyen PDW; 10 M/s'de 50). TOA eşleştirmede zaman kolu sonucu küçük bir tabloda bekler, FFT sonucu gelmezse PDW yine yayımlanır; gecikme yalnızca eşleşme olduğunda ödenir ve kayıp durumunda PDW'nin zaman alanları kurtulur.
S: İki darbe 20 ns arayla geliyor; referans FSM ayarlarıyla PDW'de ne görürsün?
C: k_f = 2 örnek (6.7 ns) ve histerezis toparlanması dahil ~10 örneklik (33 ns) ayırma sınırının altında: tek PDW, PW ≈ iki darbe + aralık, PA büyük olanın, frekans ikisinin ortalaması. Frekanslar farklıysa anlık frekans sıçraması POP bayrağını kaldırabilir; FFT kolu iki tepe görür. Ayırmak snapshot ya da daha küçük k_f ister.
:::

:::kopru
PDW FIFO'dan çıkıp PS'teki tamponuna düştü; kılavuzun antenden başlayan
yolculuğu burada, sinyal işlemenin bittiği yerde sona eriyor. Ama yazılımın
işi burada başlar: saniyede binlerce PDW'nin hangileri aynı radara ait,
radar kim, tehdit mi? Bölüm 27 bu sorulara kısa bir ufuk turu yapar —
deinterleaving, emiter takibi, kütüphane eşleme — ve kılavuzun bıraktığı
yerden nereye gidileceğini gösterir.
:::
