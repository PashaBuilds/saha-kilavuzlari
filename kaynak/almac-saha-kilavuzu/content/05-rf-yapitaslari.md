# Bölüm 5 — RF Zincirinin Yapıtaşları
::kisim II — RF Ön Uç ve Almaç Mimarileri
::meta onkosul=1,3,4 acar=6,7,9,28 blok=anten,onuc rota=yazilimci

:::neden-onemli
Sahadan soru: "Zayıflatıcıyı 10 dB artırdım, spektrumdaki küçük darbeler 30 dB
düştü — bunlar gerçek miydi?" Cevap RF zincirinin doğrusal olmayan
davranışında saklı: iki güçlü emiter aynı anda gelince yükselteç ve mixer,
hiçbir antenin görmediği üçüncü bir "darbe" üretir. Yazılımcı bu darbeyi
PDW'de görür, kaynağını bulamaz. Bu bölüm ADC'den önceki analog zinciri blok
blok açar: her bloğun ne yaptığını, hangi parametresinin senin register'ına
dokunduğunu ve zincirin nerede "yalan söylemeye" başladığını. {{bolum:4}}'te
gürültü tabanını kurmuştuk; burada tavanı kuruyoruz.
:::

## Sezgi: bir boru hattı ve iki duvar

RF zincirini bir boru hattı gibi düşün: sinyal antenden girer, her blok onu
biraz büyütür ya da küçültür, bir şeyler ekler (gürültü) ve bir şeyleri atar
(bant dışı). Boru hattının iki duvarı var. Alt duvar **gürültü tabanıdır**:
{{bolum:4}}'te gördüğün gibi zincirin *başında* belirlenir, LNA'nın NF'i
oranın kaderini çizer. Üst duvar ise **doğrusallık tavanıdır**: sinyal
büyüdükçe bloklar sıkışır, önce kazançları düşer, sonra yeni frekanslar
üretmeye başlarlar. Bu duvar zincirin *sonunda* belirlenir, çünkü sinyal en
büyük hâline en son katlarda ulaşır.

İki duvarın arasındaki mesafe **dinamik aralıktır**. Almaç tasarımı, o
mesafeyi olabildiğince açmak ve ADC'nin penceresini tam oraya oturtmaktır.
Register yazan yazılımcı bu pencereyi zayıflatıcı adımlarıyla kaydırır; ne
kadar kaydırabileceğini ve kaydırınca neyin bozulduğunu bilmek, bu bölümün
işidir.

:::analoji Hoparlör ve kısık sesli konuşma
Bir hoparlörü çok kısarsan arka plandaki uğultuyu duyarsın: gürültü tabanı.
Çok açarsan ses çatallanır, olmayan tiz ve baslar çıkar: sıkışma ve
intermodülasyon. İyi bir ses sistemi ikisinin arasında geniş bir aralık
bırakır ve sen sesi bu aralığın içinde ayarlarsın. RF zincirinde "ses
düğmesi" zayıflatıcıdır; "çatallanma" IMD3 ürünleridir; ve çatallanmayı
duymadan önce hafif bir "boğuklaşma" hissedersin: o, P1dB'dir.
:::

## Kavram: bloklar ve her birinin tek cümlelik işi

{{svg:g-50-rf-bloklar.svg|RF zincirinin on yapıtaşı: her kart bir sembol (bu kılavuzun tüm blok şemalarında aynı sembol kullanılır), tek satırlık işlev ve kilit parametreler. Altta zincirdeki tipik sıra. Aynı sembol dili Bölüm 7'deki mimari kartlarında tekrar karşına çıkacak.}}

Anten bu kılavuzda yalnızca bir arayüzdür: havadaki alanı 50 Ω'luk bir hatta
gerilime çevirir; bizim için önemli olan kazancı (dBi), bandı ve uyumsuzluğu
(**VSWR** — Voltage Standing Wave Ratio; 2:1 VSWR gücün %11'ini geri
yansıtır, ≈ 0.5 dB kayıp). Antenden sonra gelen **limiter**, LNA'nın önündeki
sigortadır: yakındaki bir vericinin darbesi geldiğinde geçirdiği gücü keser.
Bedeli birkaç onda bir dB ekleme kaybıdır ve o kayıp doğrudan NF'e eklenir
({{bolum:4}}: LNA'dan önceki her dB kayıp, NF'e bir dB olarak biner).
Referans senaryoda limiter {{s:on_uc.kaskad.0.kazanc_db}} dB ile ilk sıradadır.

**LNA** (Low Noise Amplifier — düşük gürültülü yükselteç) zincirin en önemli
bloğudur: {{s:on_uc.kaskad.1.kazanc_db}} dB kazanç, {{s:on_uc.kaskad.1.nf_db}}
dB NF. Kazancı arkadan gelen blokların gürültüsünü bastırır; NF'i sistem
NF'inin tabanını koyar. **Preselector** (ön seçici bant geçiren filtre) iki iş
yapar: bant dışı güçlü sinyalleri mixer'a ulaşmadan zayıflatır ve
{{bolum:6}}'da tanışacağın *image* frekansını bastırır. X-bant için 8–11 GHz
gibi bir pencere düşün; ekleme kaybı {{s:on_uc.kaskad.2.kazanc_db}} dB.

**Zayıflatıcı / AGC / STC** aynı bloğun üç adıdır. Sayısal adımlı zayıflatıcı
(örneğin 0.5 dB adım, 31.5 dB aralık) yazılımın kontrol ettiği register'dır.
**AGC** (Automatic Gain Control) o register'ı ölçülen seviyeye göre otomatik
ayarlayan döngüdür. **STC** (Sensitivity Time Control) radar almaçlarına özgü
halidir: verici darbesinden hemen sonra yakın mesafeden gelen güçlü ekoları
bastırmak için zayıflatma zamanla programlı olarak azaltılır. EH almacında
STC yoktur çünkü "verici anı" yoktur; ama AGC'nin zamanlaması tıpkı STC gibi
darbe genliğini bozabilir (tuzaklara bak).

**Mixer** RF'i LO ile çarpar ve frekansı IF'e taşır; {{bolum:6}} tümüyle
ona ayrılmıştır. Burada bilmen gereken: pasif bir mixer'ın "kazancı" negatiftir
(**dönüşüm kaybı**, referansta {{s:on_uc.kaskad.3.kazanc_db}} dB) ve NF'i
yaklaşık dönüşüm kaybına eşittir. **LO** (Local Oscillator — yerel osilatör)
bir **PLL** (Phase-Locked Loop) sentezleyicinin çıkışıdır; kilit parametresi
faz gürültüsüdür, birazdan. **IF filtre ve yükselteç** kanal seçiciliğini ve
kazancın büyük kısmını ({{s:on_uc.kaskad.5.kazanc_db}} dB) sağlar: IF'te dar
ve dik filtre yapmak RF'te yapmaktan çok daha kolaydır, IF'e inmenin ana
nedenlerinden biri budur. **Anti-alias filtre** (AAF) ADC'nin örnekleme
frekansının yarısından ötesini keser; direct IF sampling'de bu bir *bant
geçiren* filtredir, çünkü IF 1.8 GHz ikinci Nyquist bölgesindedir
({{bolum:8}}). Son olarak **balun / ADC sürücü** tek uçlu sinyali ADC'nin
istediği diferansiyel biçime çevirir ve seviyeyi tam ölçeğe göre ayarlar;
kendi doğrusallığı tüm zincirin doğrusallığını sınırlayabilir çünkü sinyal
burada en büyük hâlindedir.

## Kavram: sıkışma — P1dB

Her yükselteç küçük sinyalde doğrusaldır: girişi 1 dB artırırsan çıkış 1 dB
artar. Giriş büyüdükçe bir yerde çıkış artık aynı oranda artamaz; besleme
gerilimi, transistörün akımı bir yerde biter. Çıkışın ideal doğrudan **1 dB**
geri kaldığı nokta **P1dB** (1 dB compression point — 1 dB sıkışma noktası)
olarak tanımlanır. Çıkışa göre (OP1dB) ya da girişe göre (IP1dB) verilir; ikisi
arasındaki fark kazançtır (küçük sinyal kazancı eksi 1 dB). Datasheet hangisini
veriyor, her zaman bak: LNA'lar genellikle çıkış, mixer'lar genellikle giriş
P1dB'si yazar.

:::formul id=p1db baslik="1 dB sıkışma noktası"
f: P_{out}(P1dB) = IP1dB + G − 1  dB
f: OP1dB = IP1dB + G − 1
s: IP1dB | girişe göre 1 dB sıkışma noktası | dBm
s: OP1dB | çıkışa göre 1 dB sıkışma noktası | dBm
s: G | küçük sinyal kazancı | dB
o: Kurgusal LNA: G = {{s:on_uc.kaskad.1.kazanc_db}} dB, OP1dB = +15 dBm → IP1dB = −4 dBm (yaklaşık −5 dBm denir; 1 dB fark çoğu bütçede ihmal edilir). Referans darbe −60 dBm ile LNA girişine gelir: 55 dB pay var.
o: Zincirin sonunda pay erir: toplam kazanç {{s:on_uc.kazanc_toplam_db}} dB ile −20 dBm'lik güçlü bir emiter ADC girişinde +20 dBm olur; ADC tam ölçeği {{s:adc.tam_olcek_dbm}} dBm. Zayıflatıcı olmadan bu sinyal ADC'yi 16 dB aşar.
:::

P1dB'nin pratik anlamı sıkışan sinyalin kendisi değildir; 1 dB'lik sıkışma
darbe genliği ölçümünde 1 dB hata demektir, kabul edilebilir. Asıl sorun
sıkışmanın **başkalarına** yaptığıdır: sıkışan bir kat, o anda içinden geçen
zayıf sinyalleri de bastırır (desensitization) ve yeni frekanslar üretir.
Onun ölçüsü IP3'tür.

## Kavram: intermodülasyon, harmonikler ve IP3

Bir yükseltecin giriş-çıkış ilişkisini kuvvet serisiyle yazarsan
($y = a_1x + a_2x^2 + a_3x^3 + …$), ikinci ve üçüncü dereceli terimler girişte
olmayan frekanslar üretir. Tek tonda ($f$) bunlar **harmoniklerdir**: $2f$,
$3f$. Harmonikler genellikle bandın çok dışına düşer ve filtreyle atılır;
ADC'de nereye katlandıkları ayrı bir hikâyedir ({{bolum:8}}). İki tonda ($f_1$,
$f_2$) ise ikinci derece terim $f_1 ± f_2$ üretir (**IMD2**), üçüncü derece
terim de $2f_1 − f_2$ ve $2f_2 − f_1$ (**IMD3**). IMD3 ürünlerinin kötülüğü
konumlarındadır: tonlar birbirine ne kadar yakınsa ürünler de tonlara o kadar
yakındır, **hiçbir filtre onları ayıramaz**. İki emiter 10 MHz arayla
gelirse, hayalet darbeler 10 MHz ötede, tam senin bandının içindedir.

{{svg:g-51-cift-ton-imd3.svg|Çift ton testi (hesaplanmış, kurgusal yükselteç). Üstte geniş bakış: iki ton 1.8 GHz civarında, harmonikleri 3.6 ve 5.4 GHz'te — filtreyle atılabilir uzaklıkta. Ortada yakınlaştırma: IMD3 ürünleri 2f₁−f₂ ve 2f₂−f₁ tonların 10 MHz yanında, gürültü tabanının 40 dB üstünde. Altta kesişim grafiği: temel bileşen eğim 1, IMD3 eğim 3; kesikli uzantıları IP3'te kesişir, gerçek eğriler ondan çok önce sıkışır. Sağda çift ton SFDR tanımı.}}

Üçüncü derece ürünün gücü giriş gücünün küpüyle büyür: girişi 1 dB artırırsan
IMD3 3 dB artar. Log eksende temel bileşen eğim 1, IMD3 eğim 3'lük iki doğru
olur; doğruları uzatırsan bir noktada kesişirler. O hayalî noktaya **IP3**
(third-order intercept point — üçüncü derece kesişim noktası) denir; girişe
göre IIP3, çıkışa göre OIP3. Gerçek bir yükselteç IP3'e asla ulaşmaz (ondan
çok önce sıkışır), ama IP3 tek bir sayıyla her seviyedeki IMD3'ü verir:

:::formul id=imd3 baslik="IMD3 ürünü ve IP3"
f: P_{IMD3} = 3 · P_{out} − 2 · OIP3
f: IMD3_{dBc} = 2 · (P_{out} − OIP3)
s: P_{out} | ton başına çıkış gücü (iki ton eşit) | dBm
s: OIP3 | çıkışa göre üçüncü derece kesişim noktası | dBm
s: P_{IMD3} | her bir IMD3 ürününün gücü | dBm
s: IMD3_{dBc} | IMD3'ün tona göre seviyesi | dBc
o: Kurgusal LNA (OIP3 = +25 dBm), tonlar −10 dBm çıkış → P_IMD3 = −30 − 50 = **−80 dBm**, yani **−70 dBc**. Tonları 10 dB artır (0 dBm): IMD3 = −50 dBm, **−50 dBc** — ton 10 dB, ürün 30 dB büyüdü.
o: Kaba kural: **IIP3 ≈ IP1dB + 10 dB** (cihaza göre 8–15 dB). LNA'da IP1dB −5 dBm → IIP3 ≈ +5 dBm; kurgusal bütçe de öyle (OIP3 25 − G 20).
:::

Aynı mantık ikinci derece için **IP2**'yi verir (IMD2 eğim 2). IP2 dar bantlı
almaçta genellikle önemsizdir (ürünler bandın dışında), ama iki yerde öne
çıkar: çok geniş bantlı (bir oktavdan geniş) ön uçlarda $f_1 + f_2$ bandın
içine düşebilir; ve {{bolum:7}}'deki zero-IF mimaride $f_1 − f_2$ doğrudan
baseband'e, sinyalin üstüne gelir.

## Kavram: zincirin IP3'ü ve seviye planı

Zincirde IP3 de NF gibi kaskad edilir, ama ters yönden: NF'i baştaki bloklar,
IP3'ü sondaki bloklar belirler, çünkü sinyal sona doğru büyür. Her bloğun
IIP3'ünü, önündeki toplam kazanç kadar geriye (girişe) çekersin ve doğrusal
(mW) değerlerinin terslerini toplarsın:

:::formul id=iip3-kaskad baslik="Kaskad IIP3 (girişe indirgenmiş)"
f: frac{1}{IIP3_{top}} = frac{1}{IIP3_1} + frac{G_1}{IIP3_2} + frac{G_1 G_2}{IIP3_3} + …
s: IIP3_k | k. bloğun girişine göre IP3'ü | mW (doğrusal)
s: G_k | k. bloğun kazancı | oran (doğrusal)
s: IIP3_{top} | zincirin girişine indirgenmiş IP3 | mW → dBm
o: Referans zincirde (kurgusal OIP3 bütçesi: LNA +25, mixer +15, IF amp +38, sürücü +36 dBm) girişe indirgenmiş değerler LNA +5.5, mixer +4.5, IF amp −1.5, sürücü −4.0 dBm → toplam **IIP3 ≈ −6.6 dBm**. En zayıf halka en sondaki iki blok: önlerinde 40 dB kazanç var.
o: Bu sayı sana şunu söyler: girişte −30 dBm'lik iki emiter aynı anda gelirse IMD3 girişe göre 3·(−30) − 2·(−6.6) ≈ −77 dBm'dedir; hassasiyet −68 dBm'in altında, görünmez. −25 dBm'de −62 dBm: **eşiği aşar, hayalet darbe olur.**
:::

{{svg:g-52-seviye-plani.svg|Seviye planı (hesaplanmış, referans senaryo kaskadı). Mavi: −60 dBm'lik referans darbe blok blok ilerler, ADC girişinde −20 dBm. Gri: gürültü tabanı (kTB + kümülatif NF + kümülatif kazanç, B = 300 MHz); LNA'dan sonra sinyalle arası sabitlenir, SNR ≈ 26 dB. Altın: −20 dBm'lik güçlü emiter — hiçbir blok sıkışmadan ADC tam ölçeğini 16 dB aşar. Kırmızı: blokların çıkış P1dB'leri (kurgusal) ve ADC tam ölçeği. Her blok altında kazanç, NF ve kümülatif değerler.}}

Seviye planı, tüm bu sayıların tek resmidir ve her almaç tasarımının ilk
belgesidir. Okuması: gürültü çizgisi LNA'dan sonra sinyale paralel gider
(Friis'in görsel hali: ondan sonra gelenler oranı değiştiremez); sinyal
çizgisi kırmızı P1dB çizgilerine yaklaştıkça IMD3 büyür; ve ADC tam ölçeği
çoğu tasarımda bloklardan **önce** dolar. Referans zincirde güçlü emiter için
son kat sıkışmadan ADC 16 dB taşar. Bu yüzden zayıflatıcı vardır ve yazılımın
kontrolündedir.

:::formul id=friis-hatirlatma baslik="Kaskad NF (hatırlatma, Bölüm 4)"
f: F_{top} = F_1 + frac{F_2 − 1}{G_1} + frac{F_3 − 1}{G_1 G_2} + …
s: F_k | k. bloğun gürültü faktörü (doğrusal) | oran
s: G_k | k. bloğun kazancı (doğrusal) | oran
o: Referans kaskad: limiter 0.5 → LNA 2.5 → preselector 2.52 → mixer 2.69 → IF filtre 2.89 → IF amp 3.45 → sürücü **{{s:on_uc.nf_friis_db}} dB**. Bütçedeki {{s:on_uc.nf_toplam_db}} dB, buna anten/kablo kaybı, ADC katkısı ve pay eklenerek çıkar ({{bolum:4}}, {{bolum:9}}).
:::

## Kavram: anlık dinamik aralık, toplam dinamik aralık ve çift ton SFDR

"Dinamik aralık" tek başına anlamsız bir sözdür; hangi tanım olduğunu
sormalısın. Üç tanım işine yarar:

**Anlık dinamik aralık** (instantaneous dynamic range), zayıflatıcıya
dokunmadan, aynı anda görülebilen en zayıf ve en güçlü sinyal arasındaki
farktır. Alt sınır MDS (hassasiyet, {{s:turetilmis_beklenen.hassasiyet_dbm}}
dBm), üst sınır genellikle ADC tam ölçeğinin girişe indirgenmiş hali
({{s:adc.tam_olcek_dbm}} − {{s:on_uc.kazanc_toplam_db}} = −36 dBm) ya da
IMD3'ün eşiğe değdiği seviyedir; hangisi önce gelirse. Referansta ≈ 47 dB.

**Toplam dinamik aralık** (total dynamic range), zayıflatıcının/AGC'nin tüm
adımları kullanılınca zaman içinde görülebilen aralıktır: anlık aralık artı
zayıflatıcı aralığı. 30 dB'lik bir zayıflatıcıyla ≈ 77 dB. Ama dikkat:
zayıflatıcıyı 30 dB'ye çektiğinde MDS de 30 dB kötüleşir; güçlü emiterin
yanındaki zayıf emiteri **o anda** göremezsin. Toplam aralık "ya biri ya
öbürü"dür, anlık aralık "ikisi birden".

**Çift ton SFDR** (two-tone spurious-free dynamic range) daha kesin bir anlık
tanımdır: iki eşit ton, IMD3 ürünleri tam gürültü tabanına değecek kadar
güçlüyken tonların MDS'ye göre seviyesi.

:::formul id=sfdr-cift-ton baslik="Çift ton SFDR"
f: SFDR = frac{2}{3} · (IIP3 − MDS)
s: IIP3 | zincirin girişe göre IP3'ü | dBm
s: MDS | en küçük tespit edilebilir sinyal (gürültü tabanı + gerekli SNR) | dBm
s: SFDR | çift ton spur'suz dinamik aralık | dB
o: IIP3 ≈ −6.6 dBm, gürültü tabanı {{s:turetilmis_beklenen.gurultu_tabani_dbm}} dBm ile SFDR ≈ ⅔ · 76.6 ≈ **51 dB**. Bu tanımda MDS yerine gürültü tabanı kullanıldı; gerekli SNR'ı katarsan sayı 10 dB civarı küçülür — tanımı yazmadan sayıyı yazma.
o: ADC'nin kendi SFDR'ı (tek ton, dBc/dBFS) başka bir tanımdır ({{bolum:9}}); ikisini karşılaştırmadan önce hangisinin ne olduğunu netleştir.
:::

## Kavram: LO faz gürültüsü ve karşılıklı karışma

LO ideal bir çizgi değildir; frekansı çevresinde bir "etek" taşır: **faz
gürültüsü**, taşıyıcıdan Δf uzaklıkta 1 Hz'lik banttaki güç olarak
dBc/Hz ile verilir (örneğin 10 kHz'te −100, 1 MHz'te −130 dBc/Hz; sayılar
sınıfa göre çok değişir). Mixer her giriş sinyalini LO'nun bu eteğiyle
çarpar; sonuç, her sinyalin IF'te aynı eteği taşımasıdır. Zayıf sinyalde
etek gürültü tabanının altında kalır, görünmez. Güçlü bir sinyalde (bloker)
ise etek tabanın üstüne çıkar ve yanındaki zayıf sinyalin üstünü örter: buna
**karşılıklı karışma** (reciprocal mixing) denir. Bloker senin bandında bile
değildir; LO'nun eteği onu senin bandına "sürükler".

:::formul id=reciprocal-mixing baslik="Karşılıklı karışma gürültüsü (tanım düzeyi)"
f: P_n = P_{bl} + L(Δf) + 10 · log_{10}(B)
s: P_{bl} | bloker gücü (mixer girişinde) | dBm
s: L(Δf) | LO faz gürültüsü, blokerden Δf uzaklıkta | dBc/Hz
s: B | bakılan bant (çözünürlük hücresi) | Hz
s: P_n | blokerin sürüklediği gürültü gücü | dBm
o: Bloker −20 dBm, Δf = 1 MHz'te L = −110 dBc/Hz, B = 1 MHz → P_n = −20 − 110 + 60 = **−70 dBm**. Aynı 1 MHz hücrede termal taban −174 + 60 + 6 = −108 dBm: bloker, 1 MHz ötesindeki tabanı **38 dB** yükseltir. LNA'nın NF'i burada hiçbir şey yapamaz.
:::

Sayısal almaçta bu mekanizmanın ikizi ADC saatinin jitter'ıdır ({{bolum:9}}):
orada "LO eteği" yerine "örnekleme saati eteği" vardır ve aynı biçimde
güçlü sinyalin çevresine gürültü serper. Analog tasarımcının LO'ya harcadığı
özen, direct RF sampling'de saat dağıtımına kayar.

:::pasaport durak="LNA çıkışı" alan=analog
Alan: analog (RF)
Frekans: {{s:sinyal.rf_ghz}} GHz, darbeli (PW {{s:sinyal.pw_us}} µs)
Tip: reel RF gerilimi, 50 Ω
!Seviye: −60 + ({{s:on_uc.kaskad.0.kazanc_db}}) + {{s:on_uc.kaskad.1.kazanc_db}} = **−40.5 dBm** (referans darbe)
!Gürültü tabanı: kTB(300 MHz) −89.2 + NF_kum 2.5 + G_kum 19.5 = **−67.2 dBm**
SNR: ≈ 26.7 dB (bundan sonra hiçbir blok bunu anlamlı iyileştiremez)
Tavan: LNA OP1dB +15 dBm (kurgusal) → giriş −4 dBm; IMD3 için IIP3 ≈ +5 dBm
Bit / fs: — (henüz sayı yok)
:::

## FPGA'da nasıl gerçeklenir

Bu bölümün blokları FPGA'da gerçeklenmez; ama FPGA'nın gördüğü her örneğin
üstünde bu blokların imzası vardır. Üç göz aynı olguya bakınca:

:::uc-goz
::rf::
Dinamik aralık iki duvar arasıdır: alt duvar Friis (LNA belirler), üst
duvar kaskad IP3 ve P1dB (son katlar ve ADC belirler). Seviye planı bu iki
duvarı blok blok çizer; iyi bir plan, ADC tam ölçeğini son yükseltecin
P1dB'sinden birkaç dB *altına* koyar ki ADC dolmadan hiçbir kat sıkışmasın
(sıkışan kat IMD3 üretir, dolan ADC yalnızca kırpar — kırpma en azından
"dürüst"tür, kaynağı bellidir). Zayıflatıcı, planı bir bütün olarak yukarı
aşağı kaydırır: 10 dB zayıflatma hem MDS'yi hem tavanı 10 dB yükseltir.
::fpga::
FPGA analog zinciri göremez ama sonuçlarını sayar. ADC örneklerinin
tepe değerini izleyen bir **tepe/kırpma sayacı** (kaç örnek tam ölçeğe
vurdu) AGC'nin gözüdür; darbe bazında ölçülen genlik (PA) ile zayıflatıcı
register'ının toplamı gerçek giriş seviyesini verir. IMD3 ürünlerinin
"hayalet darbeleri", zarf/CFAR zincirinde gerçek darbelerden ayırt
edilemez; ayırt etme yazılımın işidir. Kaynak maliyeti sıfıra yakın: bir
karşılaştırıcı, bir sayaç, bir register.
::yazilim::
Senin elinde iki şey var: zayıflatıcı register'ı (dB → kod dönüşümü,
aşağıda) ve ADC'den gelen seviye istatistikleri. Yapman gereken üç
hesap: (1) gerçek giriş seviyesi = ADC dBFS + FS(dBm) − zincir kazancı +
zayıflatma; (2) bu seviye IP1dB bütçesine (girişe göre ≈ −16 dBm) 3 dB'den
fazla yaklaşıyorsa **doğrusallık alarmı**; (3) aynı anda iki güçlü emiter
varken PDW listesinde $2f_1 − f_2$ ve $2f_2 − f_1$'de darbe görüyorsan
"IMD3 şüphelisi" bayrağı. Zayıflatıcıyı değiştirdiğinde PA ölçümlerini
düzeltmeyi unutma: PDW'deki PA, zayıflatıcı **dâhil** giriş gücü olmalı.
:::

## Yazılımcıya dokunan yer

Zayıflatıcı register'ı çoğu kartta basittir: N bitlik bir sözcük, her LSB
sabit bir dB adımı. Ama dB matematiğini tam sayıyla yapmak, 0.5 dB adımlı
cihazda 0.25 dB çözünürlüklü bir sabit nokta gerektirir; `float` kullanmak
kolaydır ama kesme yönü önemlidir. Aşağıdaki kurgusal, öğretici register
haritası tipik bir yapıyı gösterir:

```c
#include <stdint.h>

/* Kurgusal register haritası (öğretici):
 *   ATT_CTRL[5:0]  : zayıflatma, LSB = 0.5 dB, 0..31.5 dB
 *   ADC_PEAK_DBFS  : son N örnekte tepe seviyesi, Q8.8, dBFS (negatif)
 *   ADC_CLIP_CNT   : tam ölçeğe vuran örnek sayısı (okununca sıfırlanır) */
#define ATT_LSB_DB      0.5
#define ATT_MAX_CODE    63
#define ZINCIR_KAZANC   40.0      /* dB, zayıflatıcı 0 dB iken (senaryo) */
#define ADC_FS_DBM       4.0      /* dBm, senaryo */
#define IP1DB_GIRIS    -16.0      /* dBm, kurgusal bütçe (IIP3 - 10) */

static uint8_t att_kodu(double att_db)
{
    if (att_db < 0) att_db = 0;
    long k = (long)(att_db / ATT_LSB_DB + 0.5);   /* en yakına yuvarla */
    return (uint8_t)(k > ATT_MAX_CODE ? ATT_MAX_CODE : k);
}

/* ADC tepe seviyesi + mevcut zayıflatma -> anten girişindeki gerçek güç */
static double giris_dbm(int16_t peak_q88, uint8_t att_kod)
{
    double peak_dbfs = peak_q88 / 256.0;            /* Q8.8 -> dB */
    double att_db    = att_kod * ATT_LSB_DB;
    return peak_dbfs + ADC_FS_DBM - ZINCIR_KAZANC + att_db;
}

/* Basit adımlı AGC: tepe -1 dBFS'yi aşınca 6 dB artır, -20 dBFS altına
 * inince 6 dB azalt (histerezis). Darbe süresinden yavaş çalışmalı! */
static uint8_t agc_adim(uint8_t att_kod, double peak_dbfs, unsigned clip)
{
    int kod = att_kod;
    if (clip > 0 || peak_dbfs > -1.0)       kod += 12;   /* +6 dB */
    else if (peak_dbfs < -20.0 && kod > 0)  kod -= 12;   /* -6 dB */
    if (kod < 0) kod = 0;
    if (kod > ATT_MAX_CODE) kod = ATT_MAX_CODE;
    return (uint8_t)kod;
}

/* Doğrusallık alarmı: giriş seviyesi IP1dB bütçesine 3 dB yaklaştı mı? */
static int p1db_alarm(double giris)
{
    return giris > (IP1DB_GIRIS - 3.0);
}
```

Üç ayrıntı: (1) `att_kodu` içinde `+0.5` ile yuvarlama, `(long)` kesmesinin
her zaman aşağı yuvarlamasını önler; 10.4 dB istersen 10.5 alırsın, 10.0
değil. (2) `giris_dbm` PDW'ye yazılacak PA'nın kaynağıdır: zayıflatıcıyı
değiştirdiğin anda önceki PDW'lerle sonrakiler farklı referansta olur;
değişim anını (TOA ile) kaydet. (3) `agc_adim` **darbe süresinden yavaş**
olmalı: 1 µs'lik darbe içinde zayıflatıcıyı değiştirirsen darbenin ortası
düşer, PW ve PA ölçümü bozulur. Tipik AGC güncelleme periyodu milisaniyeler
ya da PRI mertebesidir, mikrosaniye değil.

:::saha-notu Hayalet darbe testi: 10 dB kuralı
PDW listesinde açıklayamadığın bir frekansta darbe varsa zayıflatıcıyı 10
dB artır. Gerçek darbe 10 dB düşer. IMD3 ürünü **30 dB** düşer (eğim 3);
IMD2 ürünü 20 dB. Üç dakikalık bu test, "RF'te bir emiter var" ile
"zincirimiz IMD üretiyor" arasındaki farkı kesin olarak söyler. ADC'nin
kendi harmonikleri de benzer davranır ({{bolum:8}}); ayrımı katlanma
haritasıyla yaparsın.
:::

:::tuzak "Kazancı artırdım, hassasiyet artmadı"
IF yükseltecinin kazancını 10 dB artırmak (ya da zayıflatıcıyı 10 dB
azaltmak) ADC'deki sinyali 10 dB yükseltir — ama gürültüyü de. Friis'e göre
sistem NF'i LNA'da belirlenmiştir; LNA'dan sonraki kazanç SNR'ı değiştirmez,
yalnızca ADC'nin kendi gürültüsünün payını küçültür (o da ADC gürültüsü
tabanın altındaysa zaten sıfıra yakındır, {{bolum:9}}). Belirti: kazanç
arttı, MDS aynı kaldı, tavan 10 dB düştü — yani anlık dinamik aralığı
küçülttün. Kazancı artırmanın işe yaradığı tek durum ADC gürültüsünün analog
gürültü tabanının üstünde kaldığı, "az kazançlı" zincirlerdir; seviye planına
bakmadan bilemezsin.
:::

:::tuzak IMD3 ürünü gerçek emiter sanılır
İki güçlü emiter ($f_1$, $f_2$) aynı anda gelirken PDW listesinde $2f_1 − f_2$
frekansında, PRI'ı ikisinin örtüşme desenine bağlı düzensiz bir "üçüncü emiter"
belirir. Hem darbe genişliği hem TOA gerçeğe benzer, çünkü ürün yalnızca iki
darbe **üst üste binerken** vardır. Teşhis: yukarıdaki 10 dB kuralı; ve
frekans aritmetiği — üçüncü emiterin frekansı $2f_1 − f_2$ ya da $2f_2 − f_1$
ile 1 MHz içinde eşleşiyorsa şüpheli. Kalıcı çözüm PDW sonrası işlemededir
({{bolum:27}}); yazılımın yapabileceği en ucuz şey, aynı anda yüksek PA'lı
iki darbe varken bu frekanslara "IMD şüphelisi" bayrağı koymaktır.
:::

:::tuzak Hızlı AGC darbeyi yer
AGC'nin zaman sabiti darbe genişliğine yakınsa döngü darbe içinde tepki
verir: zayıflatma darbenin ortasında artar, zarf "önce yüksek sonra alçak"
bir merdiven olur. Sonuç: PA düşük ölçülür, darbe sonu eşiğin altına
düştüğü için PW kısa ölçülür, bazen tek darbe iki PDW'ye bölünür. Radar
almaçlarındaki STC bilinçli ve zamanlanmıştır (menzile bağlı); EH almacında
böyle bir referans yoktur, dolayısıyla AGC ya darbeden çok yavaş (PRI
mertebesi) ya da "darbe içinde dondurulmuş" olmalıdır. Kontrol: bilinen bir
CW ton ver, sonra darbeli ver; PA aynı çıkmıyorsa AGC darbeyi yiyor.
:::

:::ozet
- RF zinciri iki duvar arasında çalışır: alt duvar gürültü tabanı (LNA, Friis), üst duvar doğrusallık (son katlar ve ADC). Aradaki mesafe dinamik aralıktır.
- P1dB, kazancın 1 dB geri kaldığı noktadır; giriş mi çıkış mı verildiğine bak. Sıkışan kat zayıf sinyalleri de bastırır.
- IMD3 ürünleri ($2f_1 − f_2$, $2f_2 − f_1$) tonların yanına düşer, filtreyle atılamaz; gücü giriş gücünün küpüyle büyür (eğim 3). IP3 tek sayıyla her seviyedeki IMD3'ü verir; IIP3 ≈ IP1dB + 10 dB.
- Kaskad IIP3'ü sondaki bloklar belirler (önlerindeki kazanç kadar geri çekilirler); referansta ≈ −6.6 dBm (kurgusal bütçe).
- Anlık dinamik aralık (aynı anda, ≈ 47 dB) ile toplam dinamik aralık (zayıflatıcıyla, ≈ 77 dB) farklı şeylerdir; çift ton SFDR = ⅔·(IIP3 − MDS) ≈ 51 dB.
- LO faz gürültüsü, güçlü bir blokerin eteğini zayıf sinyalin üstüne serer (reciprocal mixing); sayısal almaçta ikizi saat jitter'ıdır.
- Yazılım için: zayıflatıcı kodu ↔ dB dönüşümü, giriş seviyesi = dBFS + FS − kazanç + zayıflatma, P1dB alarmı, 10 dB kuralı ile hayalet darbe testi; AGC darbeden yavaş olmalı.
:::

:::kendini-sina
S: Kurgusal LNA'da OIP3 = +25 dBm, G = 20 dB. İki ton çıkışta −5 dBm iken IMD3 ürünleri kaç dBm ve kaç dBc'dir?
C: P_IMD3 = 3·(−5) − 2·25 = −65 dBm; dBc olarak 2·(−5 − 25) = −60 dBc. Tonları 5 dB daha artırırsan IMD3 15 dB artar (−50 dBm, −50 dBc).
S: Zincirin kaskad IIP3'ünü hangi bloklar belirler ve neden LNA'nın IIP3'ü (+5.5 dBm) toplamda (−6.6 dBm) neredeyse görünmez?
C: Sondaki bloklar, çünkü her bloğun IIP3'ü önündeki kazanç kadar girişe geri çekilir: IF yükseltecin +6 dBm'lik IIP3'ü 7.5 dB kazanç arkasında −1.5, sürücünün +35.5 dBm'i 39.5 dB arkasında −4.0 dBm olur. Doğrusal toplamda en küçük IIP3 (en büyük 1/IIP3) baskındır.
S: Zayıflatıcıyı 20 dB'ye aldın. Anlık dinamik aralık ve MDS'ye ne olur? Toplam dinamik aralığa?
C: Anlık dinamik aralık değişmez (≈ 47 dB), yalnızca pencere 20 dB yukarı kayar: MDS −68'den −48 dBm'e kötüleşir, tavan −36'dan −16 dBm'e çıkar. Toplam dinamik aralık zayıflatıcının tüm aralığıyla tanımlıdır, bu adımla değişmez; ama o anda −48 dBm altındaki emiterleri kaçırırsın.
S: Bir bloker −20 dBm ile geliyor, LO faz gürültüsü 1 MHz'te −110 dBc/Hz. 1 MHz'lik çözünürlük hücresinde blokerin 1 MHz ötesine serdiği gürültü kaç dBm'dir ve bu, LNA'nın NF'ini 1 dB iyileştirmekle düzelir mi?
C: −20 − 110 + 60 = −70 dBm; termal taban aynı hücrede −108 dBm, yani 38 dB üstünde. LNA NF'i bunu etkilemez; çare daha temiz LO (ya da bloker'ı preselector'da bastırmak).
:::

:::kopru
Zincirin en ilginç bloğunu bilerek geçtik: mixer. Bir çarpma işleminin
frekansı nasıl taşıdığını, taşırken neden bir "image" kopyası getirdiğini,
LO'yu sinyalin altına ya da üstüne koymanın spektrumu neden ters çevirdiğini
ve 9.4 GHz'i 1.8 GHz'e indiren planın nasıl seçildiğini Bölüm 6 anlatır. O
bölümün sonunda pasaportta ilk kez "frekans" satırı değişecek.
:::
