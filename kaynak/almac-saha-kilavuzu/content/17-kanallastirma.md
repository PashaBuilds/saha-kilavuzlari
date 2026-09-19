# Bölüm 17 — Kanallaştırma
::meta onkosul=3,7,15,16 acar=18,20,23,25,26 blok=filtre,fft rota=sayisal

:::neden-onemli
Sahadan soru: "Aynı anda gelen iki emiterden yalnızca güçlüsünü görüyoruz;
zayıfı neden kayboluyor?" Tek bir DDC, tek bir bant seçer: 300 MHz'lik
pencerenin içine iki emiter düşerse ikisi aynı zarfta toplanır, güçlü olan
CFAR eşiğini yukarı iter ({{bolum:23}}) ve zayıfı gömer. Radar alıcısı
kendi verici frekansını bilir ve tek pencereyle yaşar; EH almacı **bilmez** ve
bütün bandı, aynı anda, birbirinden bağımsız dar pencerelerle dinlemek
zorundadır. Bu pencerelere kanal, işleme kanallaştırma denir. Onlarca DDC'yi
yan yana koymak işe yarar ama pahalıdır; polyphase filtre bankası aynı işi bir
prototip filtre ve bir FFT ile yapar. Bu bölüm o yapıyı, kanalların nasıl
bindirildiğini ve darbelerin kanallaştırıcıda ürettiği tuhaf sanatı — "tavşan
kulaklarını" — anlatır.
:::

## Sezgi: bir büyük kulak yerine on altı küçük kulak

Tek DDC, geniş bantlı bir kulaktır: her şeyi duyar ama hepsini üst üste.
Kanallaştırıcı, bandı yan yana dizilmiş K dar kulağa böler; her kulak yalnızca
kendi 150 MHz'ini dinler ve kendi zarfını, kendi gürültü tahminini, kendi
tespitini üretir. Güçlü emiter 5. kulağı doldurur; 9. kulaktaki zayıf emiter
bundan habersizdir. Bu, tespit için üç kazanç demektir: **eşzamanlı sinyal
ayrımı** (farklı kanallardaki sinyaller birbirini maskelemez), **dinamik
aralık** (her kanalın kendi CFAR'ı vardır) ve **kaba frekans ölçümü**
(hangi kanal tetiklendiyse frekans o kanalın içindedir — PDW'nin RF alanının
ilk basamağı, {{bolum:25}}). Bedeli, K kat veri ve K kat işlemedir; polyphase
yapı ikinci bedeli düşürür, ilki kalır.

:::analoji Posta tasnif makinesi
Bir postane bütün mektupları tek bir kutuya atıp sonra aramaz; posta koduna
göre K gözlü bir rafa dağıtır. Her göz kendi mektuplarını kendi hızında
işler. Kanallaştırıcı bu raftır: frekans posta kodudur. Raf iyi tasarlanmışsa
göz sınırına düşen mektup (kanal kenarındaki sinyal) iki göze birden düşmez ya
da düşerse ikisi de "bu benim" demez — ikinci kısım bu bölümün en pratik
konusudur.
:::

## Kavram: DDC bankasından polyphase filtre bankasına

En doğrudan kanallaştırıcı K adet DDC'dir: k. DDC'nin NCO'su $f_k = k · Δf$
frekansına ayarlanır, hepsi aynı alçak geçiren filtreyi ve aynı ↓M decimation'ı
kullanır ({{bolum:15}}, {{bolum:16}}). K = 16 ve Δf = 150 MHz ile 2400 MSPS'lik
reel bandın tamamı kaplanır. Maliyet K ile doğru orantılıdır: 16 mixer, 16 ×
2 filtre, 16 NCO — SSR-8'de binlerce DSP.

İki gözlem bu maliyeti eritir. Birincisi: bütün kanallar **aynı** filtreyi
kullanır, yalnızca farklı bir frekansa kaydırılmış. İkincisi: mixing ile
filtreleme yer değiştirebilir ve decimation filtrenin **içine** alınabilir
(polyphase, {{bolum:16}}). Bu iki dönüşümün sonunda ortaya çıkan yapıda giriş
örnekleri bir komütatörle K yola dağıtılır, her yol prototip filtrenin bir
polyphase alt-filtresinden geçer ve K yolun çıkışı **K noktalı bir DFT'ye**
girer. DFT'nin k. çıkışı, k. DDC'nin çıkışının tam kendisidir. Bu DFT bir
**FFT** ile hesaplanır — FFT'nin nasıl çalıştığı {{bolum:18}}'in konusudur;
burada onu "K girişten K kanal çıkışını aynı anda hesaplayan bir kara kutu"
olarak kullan.

{{svg:g-170-ddc-bankasi-polyphase.svg|DDC bankasından polyphase kanallaştırıcıya. Solda: K paralel DDC; her biri kendi NCO'su (f_k = k·Δf), kompleks mixer'ı, alçak geçiren filtresi ve ↓M decimator'ıyla — K kat kaynak. Sağda: aynı işin verimli hali; giriş komütatörle K yola dağıtılır (her yol fs/K hızında), her yol prototip filtrenin bir polyphase alt-filtresinden (p_0 … p_{K−1}) geçer, K çıkış K noktalı FFT'ye girer (Bölüm 18; burada kara kutu) ve FFT'nin k. çıkışı k. kanaldır. Tek prototip filtre, tek FFT; mixer ve NCO yoktur. Aşırı örneklenmiş (M = K/2) durumda komütatör K/2 adımla döner ve FFT girişinde dairesel kaydırma yapılır (kesikli).|kaydir}}

:::formul id=kanallastirici baslik="Kanallaştırıcı parametreleri"
f: f_k = k · frac{f_s}{K}      B_k = frac{f_s}{K}      f_{s,kanal} = frac{f_s}{M}      OSR = frac{K}{M}
f: N_p = K · L      (L: yol başına tap)
s: K | kanal sayısı (= FFT boyu) | —
s: f_k | k. kanalın merkez frekansı | Hz
s: B_k | kanal aralığı (komşu merkezler arası) | Hz
s: M | decimation oranı; M = K kritik, M = K/2 iki kat aşırı örnekleme | —
s: OSR | aşırı örnekleme oranı | —
s: N_p, L | prototip filtre tap sayısı, yol başına tap | —
o: f_s = {{s:adc.fs_msps}} MSPS, K = 16 → B_k = **150 MHz**, merkezler 0, 150, 300 … 1200 MHz (reel giriş için 0–1200 MHz'de 9 anlamlı kanal; kompleks giriş olsaydı 16). M = 8 → f_s,kanal = **300 MSPS**, OSR = 2: her kanal, referans senaryonun DDC çıkışıyla **aynı pasaporta** sahiptir — DDC, 16 kanallı kanallaştırıcının 4. kanalıdır (600 MHz).
o: L = 8 → N_p = 128 tap prototip; geçiş bandı ve stopband'i {{bolum:16}}'daki Kaiser kestirimiyle: 80 dB için Δf ≈ 150 MHz → yeterli.
:::

:::formul id=kanal-kaynak baslik="Kaynak karşılaştırması: DDC bankası ve polyphase"
f: Ç_{banka} ≈ K · ( 2 + 2 · N_p / M )      Ç_{poly} ≈ N_p / OSR + frac{K}{2} · log_2 K · 2
s: Ç | örnek başına reel çarpım sayısı (kaba) | —
s: N_p | filtre tap sayısı (banka'da kanal başına, polyphase'de prototip) | —
o: K = 16, N_p = 128, M = 8: banka ≈ 16 · (2 + 32) = **544** çarpım/örnek; polyphase ≈ 64 + 64 = **128** — dörtte biri, ve NCO'suz. K büyüdükçe fark büyür: K = 256'da banka ≈ 8700, polyphase ≈ 3100.
:::

Yapının bir inceliği aşırı örneklemedir. **Kritik örnekleme** (M = K): her
kanalın çıkış hızı tam kanal aralığına eşittir; verimli ama kanal filtresinin
geçiş bandı decimation'da kanalın kendi içine katlanır ({{bolum:16}}'daki
katlanma, kanal başına) — kanal kenarındaki sinyaller bozulur. **İki kat aşırı
örnekleme** (M = K/2): kanal çıkışı iki kat hızlıdır, geçiş bandı katlanmaz,
komşu kanallar −3 dB'de kesişir ve bir sinyal kanal kenarında bile bozulmadan
alınır. EH kanallaştırıcıları neredeyse hep aşırı örneklenmiştir; bedeli iki
kat çıkış verisidir ve polyphase yapıda komütatörün K/2 adımla dönmesi ile FFT
girişinde bir dairesel kaydırma gerektirir (harris'in klasik yapısı; ayrıntı
{{ek:e}}).

## Kavram: kanal yanıtları, bindirme ve komşu sızıntı

{{svg:g-171-kanal-yanitlari.svg|Kanal yanıtları ve bindirme (hesaplanmış, prototip 128 tap Kaiser). Üstte kritik örnekleme (M = K = 16, kanal fs 150 MSPS): kanal yanıtları (mavi, komşular soluk) ≈ −3.5 dB'de kesişir ve her kanalın kendi Nyquist sınırı ±75 MHz (kesikli) tam bu kesişimden geçer → 75–100 MHz'lik geçiş bandı kanalın içine katlanır (kırmızı taralı). Altta iki kat aşırı örnekleme (M = 8, kanal fs 300 MSPS): aynı yanıtlar, Nyquist sınırı ±150 MHz stopband'de → katlanma yok; 600 MHz'de güçlü bir emiterin (mavi ok) 450 ve 750 MHz kanallarına sızıntısı prototipin stopband seviyesinde (≈ −90 dB, kırmızı ok). Kanal kenarındaki bir sinyal (altın ok, 675 MHz) iki kanalda eşit görünür.|kaydir}}

Üç kavram şekilden okunur. **Bindirme (overlap)**: aşırı örneklenmiş
kanallar −3 dB'de kesişir; kenardaki bir sinyal iki kanalda birden, her
birinde 3 dB düşük görünür. Bu bir hata değil, tasarımdır — ama tespit
mantığı bunu bilmelidir, yoksa iki PDW üretir. **Komşu kanal sızıntısı**:
güçlü bir emiter komşu kanallarda prototip filtrenin stopband seviyesinde
görünür; stopband 60 dB ise 70 dB dinamik aralıktaki bir emiter iki komşu
kanalda "sahte" sinyal üretir. Kanal filtresinin stopband'i, almacın anlık
dinamik aralığına göre seçilir ({{bolum:9}}: ADC SFDR'ı ile aynı mertebe).
**Kanal kenarı kaybı**: kritik örneklemede kenardaki sinyal hem zayıflar hem
katlanır; frekans ölçümü ({{bolum:25}}) kanal kenarında güvenilmez olur.

## Kavram: "tavşan kulakları" (rabbit ears)

Darbenin kendisi dar bantlı olabilir; **kenarları** değildir. 50 ns'lik bir
yükselme, spektrumda onlarca MHz'e yayılan bir geçici bileşen üretir
({{bolum:3}}). Kanallaştırıcıda bu, darbenin ait olduğu kanalın komşularında
kısa süreli enerji patlamaları demektir: her darbenin başında ve sonunda,
komşu kanallarda (bazen iki-üç kanal öteye kadar) birkaç on nanosaniyelik
"çıkıntılar". Zaman–kanal görüntüsünde darbenin iki yanında yükselen iki
kulağa benzedikleri için **rabbit ears** adı yerleşmiştir. Fiziksel neden
ikilidir: kenarın geniş bant spektrumu komşu kanalın geçirme bandına düşer,
ve komşu kanalın filtresi bant dışı bir sinyalin **açılıp kapanmasına** geçici
rejimle yanıt verir — filtre uzunluğu kadar süren bir transient.

{{svg:g-172-rabbit-ear.svg|Rabbit ear etkisi, zaman–kanal görünümünde (hesaplanmış: 16 kanallı kanallaştırıcı, 128 tap prototip, 1 µs darbe, 10 ns kenar, taşıyıcı 620 MHz = 4. kanalın 20 MHz üstü). Üstte 4. kanal (darbenin kanalı): temiz zarf, 1 µs. Ortada ve altta komşu kanallar (3 ve 5): darbe süresince yalnızca sızıntı (−76 / −58 dBc; 5. kanal taşıyıcıya daha yakın), ama darbenin **başında ve sonunda** filtre geçici rejimi boyunca (toplam ≈ 53 ns, −10 dB genişliği ≈ 20 ns) süren, −34 / −21 dBc'lik iki çıkıntı — kulaklar. Kesikli çizgi komşu kanalın CFAR eşiği (−62 dBc): güçlü darbede kulaklar eşiği aşar ve onlarca ns'lik iki sahte darbe üretir; TOA'ları gerçek darbenin başlangıç ve bitişine eşittir. Sağdaki küçük panel: aynı durumun kanal–zaman ısı haritası.|kaydir}}

Kulakların PDW tablosundaki görünümü karakteristiktir ve teşhisi kolaydır:
komşu kanalda, gerçek darbenin **tam başlangıç TOA'sında** ve **tam bitiş
anında** iki kısa darbe (PW ≈ filtre geçici rejimi, ör. 20–60 ns), PA gerçek darbeden 20–40 dB düşük, frekans ölçümü kararsız. Zayıf darbelerde kulaklar
komşu kanalın CFAR eşiğinin altında kalır ve sorun görünmez; güçlü (yakın)
emiterlerde her darbe iki sahte PDW üretir — PDW hızını üçe katlar ve emiter
ayrıştırmayı ({{bolum:29}}) kirletir.

:::formul id=rabbit-ear baslik="Kulak süresi ve seviyesi (kestirim)"
f: T_{kulak} ≈ frac{N_p}{f_s}      L_{kulak} ≈ 20 · log10( frac{1}{π · t_r · Δf_{komşu}} )   (Δf_komşu > 1/(π t_r) için)
s: N_p | prototip filtre tap sayısı | —
s: f_s | giriş örnek hızı | Hz
s: t_r | darbe kenarının yükselme süresi | s
s: Δf_{komşu} | darbenin taşıyıcısı ile komşu kanal merkezinin uzaklığı | Hz
o: N_p = 128, f_s = 2400 MSPS → T_kulak ≈ **53 ns**: kulaklar minimum PW filtresinin ({{s:tespit.min_pw_ornek}} örnek = 13 ns) üstünde kalır; PW'ye göre elenemez.
o: t_r = {{s:sinyal.rise_time_ns}} ns, Δf = 130 MHz (komşu merkeze) → L ≈ 20·log10(1/(π·50e−9·130e6)) ≈ **−26 dB**; 10 ns kenarla ≈ −12 dB. Kenar ne kadar keskinse kulak o kadar güçlüdür; 60 dB üstünde SNR ile gelen bir darbenin kulakları komşu kanalın eşiğini rahatça aşar.
:::

Çözüm **kanal hakemliğidir** (channel arbitration): aynı zaman diliminde
birden fazla kanal tetiklendiğinde yalnızca en güçlü kanalın tespiti kabul
edilir, komşularının tespiti ya bastırılır ya da "komşu" bayrağıyla
işaretlenir. Üç yaygın kural: (1) **yerel maksimum**: kanal k ancak PA_k >
PA_{k−1} ve PA_k > PA_{k+1} ise tespit ilan eder; (2) **zaman örtüşmesi**:
komşu kanaldaki tespit, ana kanaldaki darbenin başlangıcından ± T_kulak
içinde başlıyor ve PW'si T_kulak mertebesindeyse kulaktır; (3) **frekans
tutarlılığı**: komşu kanalın kendi ince frekans ölçümü ({{bolum:25}})
kanalın dışını gösteriyorsa sinyal ona ait değildir. Kural (1) FPGA'da
ucuzdur (üç kanalın zarfını karşılaştıran bir devre) ve kulakların çoğunu
keser; (2) ve (3) PDW üretim FSM'inde ({{bolum:26}}) ya da PS'te uygulanır.
Bindirme de aynı hakemlikle çözülür: kenardaki sinyal iki kanalda eşit
göründüğünde yerel maksimum kuralı birini seçer, ideal olarak iki kanalın
genlik oranından kesirli kanal konumu (dolayısıyla daha iyi frekans)
türetilir.

## FPGA'da nasıl gerçeklenir

:::uc-goz
::rf::
Kanallaştırıcı, analog dünyanın **kanallı almacının** ({{bolum:7}}: filtre
bankası + dedektör dizisi) sayısal ikizidir; oradaki her filtrenin sıcaklıkla
kayan kenarı ve dedektörlerin eşleşmeyen kazançları burada yoktur — bütün
kanallar tek prototipin kopyasıdır ve bit bit özdeştir. RF mühendisinin
katkısı iki yerdedir: kanal aralığını tehdidin tipik bant genişliğine göre
seçmek (LFM darbenin bandı kanal aralığını aşarsa sinyal birden çok kanala
yayılır ve hiçbirinde tam görünmez) ve ADC'nin SFDR'ı ile prototipin
stopband'ini eşleştirmek (60 dB stopband'li kanallaştırıcı 80 dB'lik ADC'yi
israf eder).
::fpga::
16 kanal, 128 tap prototip, M = 8, SSR-8 giriş: komütatör kablodur (SSR-8'in
8 örneği zaten yan yana; K = 16 için iki saatlik toplama), 16 polyphase yol ×
8 tap = 128 çarpıcı (reel giriş: 128 DSP; simetri polyphase'de doğrudan
kullanılamaz), 16 noktalı FFT her saatte bir kez (≈ 32 kompleks çarpım ≈ 100
DSP, ya da radix-4 ile daha az) → toplam ≈ 230 DSP, 16 kanal × 300 MSPS
kompleks çıkış = 16 × 9.6 = 154 Gbps iç veri. Karşılaştır: 16 ayrı DDC ≈ 16 ×
80 = 1280 DSP. Kanal hakemliği (yerel maksimum) her kanal için iki
karşılaştırıcı: önemsiz. Latency: prototip grup gecikmesi 64 giriş örneği
(27 ns) + FFT pipeline ≈ 20 saat + polyphase pipeline; latency tablosuna
yazılır.
::yazilim::
Yazılımcının gördüğü: kanal sayısı ve aralığı sentez sabitidir; register
olarak kanal başına **enable** biti (bilinen bozucu bantları kapatmak),
kanal başına CFAR parametreleri ({{bolum:23}}), hakemlik modu (kapalı / yerel
maksimum / bayrakla) ve PDW'deki **kanal alanı** ({{bolum:26}}). Kanal
numarasından RF'e dönüş: f_RF = LO + IF ± (f_k − f_NCO,ref + f_ince) — evriklik
dahil ({{bolum:15}}'teki `bb_to_rf` mantığı kanal merkezine uygulanır).
Hakemlik kapalıysa PDW akışında kulakları PS'te elemen gerekir: aynı TOA'lı
komşu kanal PDW'leri, PW ≈ T_kulak, PA farkı > 20 dB.
:::

## Yazılımcıya dokunan yer

```c
#include <stdint.h>

/* Kurgusal: kanal başına tespit özeti (FPGA'dan aynı zaman diliminde gelir) */
typedef struct { uint8_t kanal; uint16_t pa_q; uint32_t toa; uint32_t pw; } tespit_t;

#define K_KANAL      16
#define KULAK_PW_MAX 20      /* örnek @300 MSPS ≈ 67 ns: T_kulak üstü küçük pay */
#define KULAK_PA_DB  20      /* komşu, ana kanaldan bu kadar düşükse kulak */

/* Yerel maksimum hakemliği + kulak filtresi.
 * pa_db[k]: aynı zaman diliminde her kanalın zarf tepe değeri (dB, yoksa -999).
 * Dönüş: kabul edilen kanal maskesi (bit k = kanal k gerçek tespit). */
uint32_t kanal_hakem(const int16_t *pa_db, const tespit_t *t, int n)
{
    uint32_t kabul = 0;
    for (int i = 0; i < n; i++) {
        int k = t[i].kanal;
        int sol  = (k > 0)           ? pa_db[k - 1] : -999;
        int sag  = (k < K_KANAL - 1) ? pa_db[k + 1] : -999;
        int yerel_maks = (pa_db[k] >= sol) && (pa_db[k] >= sag);
        int komsu_guclu = (sol - pa_db[k] > KULAK_PA_DB) || (sag - pa_db[k] > KULAK_PA_DB);
        int kulak_gibi  = komsu_guclu && (t[i].pw <= KULAK_PW_MAX);
        if (yerel_maks && !kulak_gibi) kabul |= (1u << k);
    }
    return kabul;
}

/* Kanal numarasından kaba RF (Hz): kanal merkezi + ince ölçüm, evriklik dahil.
 * f_k = k * fs / K; referans DDC kanalı k_ref = 4 (600 MHz). */
static double kanal_to_rf(int k, double f_ince_hz, double fs_hz, int inv,
                          double lo_hz, double if_hz, int k_ref)
{
    double f_bb = (k - k_ref) * fs_hz / K_KANAL + f_ince_hz;   /* referans NCO'ya göre */
    double if_ofset = inv ? f_bb : -f_bb;                       /* Bölüm 15 */
    return lo_hz + if_hz + if_ofset;
}
```

:::tuzak Kulaklar ayrı emiter sanılır
PDW akışında, güçlü bir emiterin her darbesine eşlik eden, komşu kanalda,
50 ns'lik, PA'sı 30 dB düşük iki darbe görülür. Emiter ayrıştırma
({{bolum:29}}) bunları "aynı PRI'lı, kısa darbeli, komşu frekanslı yeni bir
emiter" olarak raporlar; operatör 150 MHz ötede hayalet bir radar görür.
Teşhis: hayaletin TOA'sı gerçek darbenin başlangıcına (ve ikincisi bitişine)
örnek hassasiyetinde eşittir; PW'si prototip filtre uzunluğu mertebesindedir;
PA farkı sabittir. Çözüm: FPGA'da yerel maksimum hakemliği; PS'te aynı zaman
dilimli komşu kanal PDW'lerini birleştirme. Çözüm **olmayan**: minimum PW'yi
60 ns'ye çekmek — gerçek kısa darbeleri de kaybedersin.
:::

:::tuzak Kanal kenarındaki sinyal iki PDW, iki frekans
675 MHz'deki bir emiter (4. ve 5. kanalın tam sınırı) iki kanalda birden
3 dB düşük görünür; hakemlik kapalıysa her darbe için iki PDW üretilir,
biri "kanal 4, 600 + 75 MHz", diğeri "kanal 5, 750 − 75 MHz" — aynı frekans,
iki kayıt. Hakemlik açık ama eşitlik kuralı yoksa (`>` yerine `>=`) hiçbiri
tespit etmez: emiter **kaybolur**. Teşhis: emiter frekansı tam kanal
sınırındaysa ve PDW sayısı ikiye katlanıyor ya da sıfırlanıyorsa. Çözüm:
eşitlikte küçük indisi seç (deterministik), ideal olarak iki kanalın genlik
oranından kesirli kanal konumu türet ve frekansı ince ölçümle
({{bolum:25}}) doğrula.
:::

:::tuzak Kritik örneklenmiş kanallaştırıcı "verimli" diye seçilir
Çıkış verisi yarıya iner, FFT girişi kaydırma istemez — cazip. Ama kanal
filtresinin geçiş bandı kanalın içine katlanır: kenara yakın sinyaller bozuk,
anlık frekans ölçümü kenarda yanlış, LFM darbenin kanal sınırını geçen kısmı
katlanıp "ters chirp" görünür. İletişim sistemlerinde (kanallar arası boşluk
garanti) kabul edilebilir; EH'de sinyal nereye düşeceğini seçmez. Kural:
tespit almaçlarında iki kat aşırı örnekleme; veri hızı gerçekten sorunsa
kanal sayısını azalt, örneklemeyi değil.
:::

:::ozet
- EH almacı frekansı bilmez ve eşzamanlı sinyallerle yaşar; kanallaştırma bandı K bağımsız kanala böler: eşzamanlı ayrım, kanal başına dinamik aralık, kaba frekans.
- K DDC = tek prototip filtre (polyphase) + K noktalı FFT (Bölüm 18'de açılır); K = 16, 128 tap: ≈ 128 çarpım/örnek, banka ≈ 544; K büyüdükçe fark büyür.
- Referans DDC, 16 kanallı, 2× aşırı örneklenmiş (M = 8) bir kanallaştırıcının 4. kanalıdır: aynı 300 MSPS, ±150 MHz pasaportu.
- Kritik örnekleme (M = K) geçiş bandını kanalın içine katlar; iki kat aşırı örnekleme (M = K/2) katlamaz, komşular −3 dB'de kesişir; EH'de standart ikincisidir.
- Komşu kanal sızıntısı prototipin stopband'i kadardır; stopband ADC SFDR'ı ile eşleşmeli.
- Rabbit ears: darbe kenarlarının geniş bant spektrumu + komşu filtrenin geçici rejimi → darbenin başında ve sonunda komşu kanallarda ≈ N_p/fs süreli, −20 … −40 dB'lik sahte darbeler; güçlü emiterde eşiği aşar.
- Kanal hakemliği: yerel maksimum (FPGA, ucuz), zaman örtüşmesi ve frekans tutarlılığı (FSM/PS); eşitlikte deterministik seçim, ideal olarak genlik oranından kesirli kanal.
:::

:::kendini-sina
S: fs = 2400 MSPS, K = 16, M = 8. Bir kanalın aralığı, çıkış hızı ve aşırı örnekleme oranı nedir; kanal 6'nın merkezi baseband'e göre nerededir (referans NCO 600 MHz)?
C: Aralık 150 MHz, çıkış 300 MSPS, OSR = 2. Kanal 6'nın merkezi 900 MHz; referans DDC kanalı (4, 600 MHz) ile arasında +300 MHz — evriklik düzeltilmişse IF'in 300 MHz altına, düzeltilmemişse üstüne karşılık gelir ({{bolum:15}}).
S: Prototip filtrenin stopband'i 55 dB. 75 dB dinamik aralıklı bir ortamda ne olur?
C: 75 dB'lik güçlü emiter komşu kanallarda −55 dB'de, yani gürültü tabanının 20 dB üstünde görünür: iki komşu kanal aynı darbeyi tespit eder, hakemlik yoksa üç PDW. Stopband ADC'nin SFDR'ı ve almacın anlık dinamik aralığı ile eşleşmeli (≈ 75–80 dB); bu prototip tap sayısını artırır ({{bolum:16}} Kaiser kestirimi).
S: Rabbit ear'ları elemek için minimum PW'yi 100 ns yapmak neden kötü bir fikirdir; ne yapılmalı?
C: Kulakların PW'si filtre uzunluğuyla belirlenir (≈ 50 ns) ve gerçek kısa darbeler de bu aralıktadır; minimum PW'yi yükseltmek gerçek darbeleri kaybettirir. Doğru çözüm, kulağın ayırt edici özelliklerini kullanan hakemliktir: komşu kanalda aynı anda çok daha güçlü bir tespit varsa (yerel maksimum değilse) ve PW ≈ T_kulak ise eleme.
S: Kanal kenarında (675 MHz) bir emiter iki kanalda eşit güçte görünüyor. Bu bilgiden frekansı nasıl iyileştirirsin?
C: Kanal yanıtları bilindiğinden iki kanalın genlik oranı, sinyalin iki merkez arasındaki kesirli konumunu verir (eşitlik → tam ortada, 675 MHz). Bu, kanal aralığından çok daha ince bir kaba frekanstır; ince ölçüm ({{bolum:25}}) seçilen kanalın içinde tamamlar. Aynı bilgi hakemliğin hangi kanalı seçtiğinden bağımsız olarak PDW'ye yazılmalıdır.
:::

:::kopru
Kanallaştırıcının kalbinde bir kara kutu bıraktık: K polyphase çıkışını aynı
anda K kanala çeviren FFT. Aynı kutu, almacın ikinci kolunun da temelidir —
darbeye zarfıyla değil spektrumuyla bakmak, frekansı kanal aralığından çok
daha ince ölçmek, dar bantlı sinyali geniş bant gürültüden FFT'nin kendi
kazancıyla çıkarmak. Bölüm 18 kutuyu açıyor: DFT, bin, çözünürlük, ölçekleme
ve "FFT tabanı neden datasheet SNR'ından aşağıda" sorusu.
:::
