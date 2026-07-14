# Bölüm 6 — Gömülü C Pratikleri II: Bellek ve Cache

Bölüm 5'te dilin donanımla konuşma kalıplarını öğrendin: `volatile`, bit
işlemleri, doğru genişlikli tipler. Şimdi dilin inceliklerinden belleğin
gerçeklerine geçiyoruz — çünkü senin yazdığın her değişken, her fonksiyon
çağrısı, aslında Bölüm 3'te gördüğün bellek haritasının bir köşesine
yerleşiyor. Bu bölümü bitirdiğinde, "değişkenim nerede yaşıyor" ve
"CPU'nun gördüğü değerle DDR'deki değer neden bazen aynı olmuyor"
sorularına cevap verebileceksin.

## Stack, heap, static: üç bellek bölgesi

Bir C programındaki her değişken üç bölgeden birinde yaşar:

- **Stack (yığıt).** Fonksiyon içindeki yerel değişkenler burada
  yaşar; bir fonksiyona girildiğinde otomatik ayrılır, çıkıldığında
  otomatik geri verilir. Masaüstünde işletim sistemi stack taştığında
  sayfa hatası verip seni uyarabilir; bizim bare-metal dünyamızda böyle
  bir koruma yoktur — stack, kendisinden sonraki belleğe (genelde heap'e
  ya da başka bir statik veriye) sessizce taşabilir. Görev 10'da bu
  hatayı bizzat avlayacaksın.
- **Static/global (.data ve .bss).** Fonksiyon dışında tanımlanan ya da
  `static` anahtar kelimesiyle işaretlenen değişkenler, programın ömrü
  boyunca sabit bir adreste yaşar. Başlangıç değeri verilenler `.data`
  bölümüne (ELF dosyasında gerçek değerleriyle saklanır), sıfırla
  başlayanlar `.bss` bölümüne gider (ELF dosyasında yer kaplamaz, sadece
  "şu kadar bayt sıfırla" bilgisi taşınır — açılışta bu sıfırlama
  gerçekten yapılır).
- **Heap.** `malloc`/`free` ile çalışma zamanında ayrılıp geri verilen
  bellek. Masaüstünde bolca kullanılan bir araçtır; bizim dünyamızda
  temkinli yaklaşılır.

{{svg:sema-12-bellek-yerlesimi.svg|Şekil 12 — Stack/heap/static bellek yerleşimi: ELF dosyasının .text/.rodata/.data/.bss bölümleri linker script aracılığıyla RAM'e oturur; heap yukarı, stack aşağı büyür.}}

:::ekip-notu Bizim dünyada malloc ya hiç ya başlangıçta
Masaüstü uygulamasında `malloc`/`free`'yi rahatça kullanırsın; işletim
sistemi arkanı toplar. Bare-metal'de arkanı toplayan kimse yok: parçalanma
(fragmentation), öngörülemeyen gecikme (heap yöneticisi her çağrıda ne
kadar sürer, garantisi yok) ve "bellek bitti ama kimse haber vermedi"
senaryosu hepsi senin sorumluluğun. Bizim ekipte pratik kural şu: ya
**hiç malloc kullanma** (tüm buffer'lar derleme zamanında sabit boyutlu
diziler olsun), ya da **yalnızca başlangıçta, bir kez** ayır ve programın
geri kalanında hiç `free` çağırma. Çalışma zamanının ortasında
malloc/free döngüsüne girmek, gömülü dünyada aramadığın bir belaya davet
çıkarmaktır.
:::

## Linker script'e giriş: ELF'in bellek haritasına oturması

Derleyici senin `.c` dosyalarını `.o` (object) dosyalarına çevirir; ama
bu dosyalarda henüz "bu fonksiyon şu adreste yaşayacak" bilgisi yoktur.
Bu işi **linker** (bağlayıcı) yapar — ve linker'a "hangi bölümü hangi
adrese koy" talimatını veren dosyaya **linker script** denir (Xilinx
araçlarında adı genelde `lscript.ld`'dir, platformun .xsa'sından
otomatik üretilir).

Derleme çıktısı olan **ELF** dosyası birkaç standart bölüme ayrılır:
`.text` (derlenmiş makine kodu), `.rodata` (salt okunur sabitler, örneğin
dizgi sabitleri), `.data` ve `.bss` (yukarıda gördüğün statik
değişkenler), ve heap/stack için ayrılan boşluklar. Linker script her
birine Bölüm 3'te tanıdığın bellek haritasından bir adres aralığı atar —
tipik bir bare-metal projede tüm bunlar DDR Low'a (`0x0`'dan başlayan
bölge) yerleşir; OCM ise küçüklüğü nedeniyle genelde yalnızca FSBL gibi
özel durumlar için kullanılır. Vitis bu dosyayı platformun bellek
haritasına göre senin için üretir; sen büyük çoğunlukla ona dokunmadan
çalışırsın, ama var olduğunu ve ne iş yaptığını bilmek, "programım neden
bu adrese sığmadı" gibi bir hatayla karşılaştığında hayat kurtarır.

## Cache: hız dostu, tutarlılık düşmanı

**Cache** (önbellek), CPU ile DDR arasına giren küçük ama çok hızlı bir
bellektir. DDR'ye her erişim CPU hızına göre yavaştır; cache, sık
kullanılan verileri CPU'ya yakın tutarak bu farkı kapatır. Normal
şartlarda cache tamamen şeffaftır — sen hiçbir şey yapmadan işini görür
ve programın hızlanır.

Şeffaflık, tek bir yazarın (CPU'nun) belleğe eriştiği sürece bozulmaz.
Sorun, **ikinci bir yazar** sahneye çıktığında başlar — mesela bir
**DMA** (Direct Memory Access — doğrudan bellek erişimi, CPU'yu
atlayarak veri taşıyan bir donanım birimi) ya da PL'deki bir IP,
doğrudan DDR'ye yazar. CPU'nun cache'i bu yazmadan haberdar değildir;
CPU o adresi okuduğunda cache'te duran **eski** kopyayı döndürür, DDR'de
duran yepyeni veriyi değil.

{{svg:sema-13-cache-dma.svg|Şekil 13 — Cache hiyerarşisi ve tutarlılık: DMA'nın DDR'a yazdığı yeni veriyi CPU'nun cache'ten eski okuması, invalidate sonrası doğru okumaya dönüşü.}}

Bu, "DMA yazdı ama CPU eskiyi okuyor" senaryosudur ve gömülü dünyanın
klasik hata kaynaklarından biridir. Çözüm, CPU'ya "bu adres aralığındaki
cache kopyanı at, bir dahaki okumada gerçekten DDR'ye git" demektir —
buna **invalidate** (geçersiz kılma) denir. Tersi yönde bir ihtiyaç da
var: CPU bir veriyi yazdı ama henüz cache'te duruyor, DMA'nın DDR'den bu
veriyi okumasını istiyorsun — bu durumda CPU'nun cache'teki "kirli"
(henüz DDR'ye yazılmamış) veriyi DDR'ye göndermesi gerekir, buna
**flush** (temizleme) denir.

Xilinx standalone BSP'si (BSP — Board Support Package; çevre birimi
sürücülerini, başlangıç kodunu ve xparameters.h'i içeren/üreten ara
katman; ayrıntısı Bölüm 11'de) bu işlemleri hazır fonksiyonlarla sunar:
`Xil_DCacheInvalidateRange(adres, uzunluk)` ve
`Xil_DCacheFlushRange(adres, uzunluk)`. Kural basit: **DMA'nın yazdığı
bir bölgeyi CPU okumadan önce invalidate et; CPU'nun yazdığı bir bölgeyi
DMA okumadan önce flush et.**

:::derin-dalis A53'te FlushRange aslında InvalidateRange'dir
ARMv8 (Cortex-A53) standalone BSP'sinde ilginç bir ayrıntı var:
`Xil_DCacheFlushRange` fonksiyonu, kaynak kodda doğrudan
`Xil_DCacheInvalidateRange`'in bir takma adı (makro) olarak tanımlıdır —
`#define Xil_DCacheFlushRange Xil_DCacheInvalidateRange`. Yani isim
"flush" dese de, A53'te bu makronun gerçekte çalıştırdığı işlem bir
range-invalidate'tir (ki ARMv8'de bu, önce temizleyip sonra geçersiz
kılan bir "clean+invalidate" olarak uygulanır). Pratik sonucu: A53
kodunda iki ismi de görebilirsin, ikisi de aynı donanım işlemine gider —
ama isim, hangi kavramsal işlemi çağırdığını her zaman doğru
yansıtmayabilir. Kaynak: `content/_arastirma.md` §10.
:::

## Alignment: adresin hizası

**Alignment** (hizalama), bir verinin başladığı adresin, kendi
boyutunun katı olması gerekliliğidir — 4 baytlık bir `unsigned int`'in
adresi 4'ün katı, 8 baytlık bir `unsigned long long`'un adresi 8'in katı
olmalıdır gibi.
Çoğu ARM mimarisinde hizasız erişim çalışır ama yavaştır (ya da bazı
durumlarda hiç çalışmaz); DMA transferleri ise çoğu zaman belirli bir
hizalamayı (örneğin cache satırı boyutu — tipik 64 bayt) **şart koşar**.
Derleyici normal değişkenlerin hizalamasını kendi halleder; DMA'ya
vereceğin bir buffer'ı elle hizalamak istediğinde
`__attribute__((aligned(64)))` gibi bir nitelik kullanırsın. Şimdilik
kavramı tanı yeter — Bölüm 9'da DMA'ya değince tekrar karşına çıkacak.

:::tuzak "Debug'da çalışıyor, release'te çalışmıyor" klasiği
Bu cümleyi gömülü kariyerinde defalarca duyacaksın (ve söyleyeceksin).
İki sık kök nedeni var, ikisi de bu iki bölümde gördüğün konulardan
çıkıyor: **(1) eksik `volatile`** — debug derlemesi genelde `-O0`
(optimizasyonsuz) yapılır, derleyici gereksiz okuma/yazmayı silmez,
kod "tesadüfen" çalışır; release derlemesi `-O2` gibi agresif bir
seviyede yapılır, derleyici Bölüm 5'te gördüğün optimizasyonu uygular
ve `volatile` eksikse okuma sessizce kaybolur. **(2) cache/DMA
tutarlılığı** — debug'da genelde daha yavaş, daha öngörülebilir bir
akış vardır (ya da cache bazı debug yapılandırmalarında kapalı
tutulur); release'de hız artınca CPU'nun cache'ten eski veri okuma
penceresi gerçek bir sorun olarak ortaya çıkar. İkisi de "kod yanlış
değildi, optimizasyon seviyesi hatayı görünür kıldı" örneğidir — kodun
kendisi baştan yanlıştı, sadece -O0 bunu senden gizliyordu.
:::

Bellek nereye yerleşiyor, ne zaman cache'e güvenip ne zaman güvenmeyeceğini
artık biliyorsun. Sıra pratikte: bu sefer kartın tek girdisini —
butonu — okuyacaksın.

:::gorev no=3 zorluk=1 baslik="Buton Oku (Polling)" kisa="Buton Oku"
[Hedef]
SW19 butonunu (PS MIO22) sürekli sorgulama (polling) ile okuyup DS50
LED'ine (PS MIO23) yansıtmak; debounce'lu (sıçrama'dan arındırılmış) bir
basma sayacını UART'a basmak.

[Ön koşul]
Bölüm 6 okundu; Görev 2 tamamlandı (`uart_ps` modülün hazır ve çalışıyor).

[Adımlar]
1. Karttaki 8 LED, 5 buton ve DIP switch'in PL pinlerinde olduğunu
   Bölüm 2'den hatırla — bu görevde de yalnızca tek PS butonu (SW19) ve
   tek PS LED'i (DS50) kullanıyoruz; 8 LED'lik yürüyen ışık Görev 7'yi
   bekliyor.
2. `buton_ps.h/.c` modülünü yaz: `buttonInit()` içinde `XGpioPs`
   sürücüsünü (Görev 1'den tanıdık) `LookupConfig` + `CfgInitialize`
   ile kur; SW19'u giriş, DS50'yi çıkış (+ çıkış etkinleştirme) yap.
3. `buttonRead()` içinde `XGpioPs_ReadPin` ile SW19'u oku;
   `ledPsWrite()` içinde `XGpioPs_WritePin` ile DS50'yi sür.
4. `main()`'de her birkaç milisaniyede bir (`usleep`, `sleep.h`) SW19'u
   oku; okunan ham değer art arda birkaç turda aynı kalıp mevcut kararlı
   durumdan farklıysa geçişi "gerçek" kabul et (sayaç-tabanlı debounce —
   aşağıdaki analojiye bak), LED'i güncelle ve basılma yönündeki her
   geçişte bir sayaç artır.
5. Sayaç değiştiğinde `uart_ps` modülünle ("Görev 2'nin çıktısı yeniden
   kullanılıyor") bir durum satırı bas.

:::analoji Debounce, bir kapı zilinin "gerçekten mi çaldı" sorusu gibidir
Titreşen bir kapı ziline tek dokunuşta zil birkaç kez art arda öter;
sen yine de "biri bir kez geldi" dersin, üç kez gelmiş saymazsın. Beynin
bunu, kısa süreli titreşimleri göz ardı edip "birkaç an sonra hâlâ aynı
mı" diye kontrol ederek yapar. Sayaç-tabanlı debounce da tam bunu yapar:
ham okumayı hemen güvenmez, birkaç ardışık turda aynı değeri görene kadar
bekler.
:::

[Başarı kriteri]
Butona basılı tuttuğun sürece DS50 yanıyor, bıraktığın anda sönüyor;
butona tam 10 kez bastığında UART'taki sayaç tam "10" diyor — sıçrama
yüzünden 11 ya da 12 demiyor.

[Kendini sına]
- Debounce süresini (örnekleme aralığı × ardışık tur sayısı) neye göre
  seçtin? Çok kısa tutsaydın ne olurdu, çok uzun tutsaydın ne olurdu?
- Bu polling döngüsü çalışırken CPU başka hiçbir iş yapamıyor —
  döngünün her turu ne kadar sürüyor, CPU zamanının ne kadarını bu
  beklemeye harcıyorsun?
- `buttonRead()`'in döndürdüğü ham değeri debounce'suz doğrudan
  LED'e yazsaydın, gözle görülür fark ne olurdu?

[Takıldıysan]
::ipucu İpucu 1 — LED hiç yanmıyor ya da hep yanık
Yön (DIRM) ve çıkış etkinleştirme (OEN) register'larını doğru pinler
için mi kurdun — SW19 (MIO22) giriş, DS50 (MIO23) çıkış olacak şekilde
mi? `buttonInit()`'in dönüş değerini kontrol ettin mi; `XST_SUCCESS`
dönmüyorsa `XPAR_XGPIOPS_0_DEVICE_ID` doğru mu diye `xparameters.h`'a
bak.
::/
::ipucu İpucu 2 — Sayaç sekiyor (10 basışta 11-12 diyor)
`DEBOUNCE_ESIK` (ardışık aynı okuma eşiği) çok küçük olabilir — bir
sıçramanın birkaç ardışık turda "gerçek" sanılacak kadar uzun sürmesi
mümkün. Eşiği artırıp örnekleme aralığını (kaç mikrosaniyede bir
okuduğunu) birlikte değerlendir; ikisinin çarpımı senin debounce
penceren.
::/
::cozum Tam çözüm — lab03-buton
Aşağıdaki dosyalar SW19/DS50'yi debounce'lu polling ile okuyup UART'a
basar (`uart_ps` modülü lab02'den birebir kopyadır):
{{kod:lab03-buton/src/buton_ps.h}}
{{kod:lab03-buton/src/buton_ps.c}}
{{kod:lab03-buton/src/main.c}}
::/
:::

Butonu her birkaç milisaniyede bir sen sorduğun için CPU'nun neredeyse
tüm zamanı bu soruyu sormakla geçti — polling'in bedelini gördün, şimdi
kesme zamanı: Bölüm 7'de aynı buton, CPU'yu hiç meşgul etmeden sana haber
verecek.
