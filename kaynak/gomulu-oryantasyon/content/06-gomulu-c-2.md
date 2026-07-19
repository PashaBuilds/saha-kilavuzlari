# Bölüm 6 — Gömülü C Pratikleri II: Bellek ve Cache

Bölüm 5, dilin donanımla konuşma kalıplarını ele aldı: `volatile`, bit
işlemleri ve doğru boyutlandırılmış tipler. Bu bölüm dilin inceliklerinden
belleğin gerçeklerine geçer — bildirdiğin her değişken ve çağırdığın her
fonksiyon, Bölüm 3'te tanıtılan memory map (bellek haritası) içinde bir
adreste yaşar. Bölümün sonunda iki soruya cevap verebileceksin: bir
değişken gerçekte nerede durur, ve CPU'nun gördüğü değer DDR'de
saklanandan neden bazen farklıdır.

## Stack, Heap ve Statik: Üç Bellek Bölgesi

C programındaki her değişken şu üç bölgeden birinde yaşar:

- **Stack (yığın).** Fonksiyon içindeki yerel değişkenler burada durur;
  alan fonksiyona girişte otomatik ayrılır, çıkışta otomatik bırakılır.
  Masaüstü sistemde stack taştığında işletim sistemi page fault üretip
  seni uyarabilir; bizim bare-metal ortamımızda böyle bir koruma yok —
  stack sessizce komşu belleğe (genellikle heap'e ya da diğer statik
  verilere) taşar. Bu hatayla Görev 10'da doğrudan karşılaşacaksın.
- **Statik/global (.data ve .bss).** Fonksiyon dışında bildirilen ya da
  `static` anahtar kelimesiyle işaretlenen değişkenler, programın ömrü
  boyunca sabit bir adreste durur. Açık başlangıç değeri verilenler
  `.data` bölümüne yerleşir (ELF dosyasında gerçek değerleriyle
  saklanır); sıfırla başlayanlar `.bss` bölümüne (ELF dosyasında yer
  kaplamaz — yalnızca "şu kadar baytı sıfırla" talimatı taşır; açılışta
  uygulanır).
- **Heap.** `malloc`/`free` ile çalışma anında ayrılıp bırakılan bellek.
  Masaüstünde bolca kullanılır; bizim ortamımızda temkinle yaklaşılır.

{{svg:sema-12-bellek-yerlesimi.svg|Şekil 12 — Stack/heap/statik bellek yerleşimi: ELF dosyasının .text/.rodata/.data/.bss bölümleri linker script aracılığıyla RAM'e yerleştirilir; heap yukarı, stack aşağı büyür.}}

:::ekip-notu Bizim Ortamımızda: malloc Ya Hiç, Ya Yalnızca Açılışta
Masaüstü uygulamada `malloc`/`free` serbestçe kullanılır; temizliği işletim
sistemi üstlenir. Bare-metal geliştirmede bu emniyet ağı yok:
fragmentation (parçalanma), öngörülemeyen gecikme (heap yöneticisi bir
çağrının ne kadar süreceği konusunda garanti vermez) ve "bellek bitti,
haber yok" senaryosunun tamamı senin sorumluluğundadır. Ekipteki pratik
kural şu: ya **malloc'tan tamamen uzak dur** (bütün tamponları derleme
anında sabit boyutlu dizi olarak ayır), ya da belleği **yalnızca
açılışta, bir kez** ayır ve programın geri kalanında asla `free`
çağırma. Çalışmanın ortasında malloc/free döngüsüne girmek, gömülü
geliştirmede uzak durulması gereken sorunları davet eder.
:::

## Linker Script'e Giriş: ELF'i Memory Map'e Yerleştirmek

Derleyici `.c` dosyalarını `.o` (object) dosyalarına çevirir; ancak bu
aşamada bir fonksiyonun hangi adreste duracağı bilgisi henüz yoktur. Bu
işi **linker** (bağlayıcı) yapar; linker'a hangi bölümü hangi adrese
koyacağını söyleyen dosyaya **linker script** denir (Xilinx araçlarında
genellikle `lscript.ld` adını taşır; platformun .xsa dosyasından otomatik
üretilir).

Derlemenin ürettiği **ELF** dosyası birkaç standart bölüme ayrılır:
`.text` (derlenmiş makine kodu), `.rodata` (salt okunur sabitler,
örneğin string literal'ler), `.data` ile `.bss` (yukarıda anlatılan
statik değişkenler) ve heap ile stack için ayrılan alan. Linker script
bunların her birine Bölüm 3'te tanıtılan memory map'ten bir adres
aralığı atar — tipik bir bare-metal projede hepsi DDR Low'a (`0x0`'dan
başlayan bölge) yerleştirilir; OCM ise boyutu sınırlı olduğundan
genellikle FSBL gibi özel durumlara ayrılır. Vitis bu dosyayı platformun
memory map'ine göre senin yerine üretir; çoğu durumda doğrudan
elleşmeden çalışırsın. Yine de varlığını ve ne yaptığını bilmek,
"program bu adrese sığmıyor" türünde bir hatayla karşılaştığında paha
biçilmezdir.

## Cache: Hızın Müttefiki, Tutarlılığın Rakibi

**Cache** (önbellek), CPU ile DDR arasında duran küçük ama çok hızlı bir
bellektir. DDR'ye her erişim CPU hızına göre yavaştır; cache, sık
kullanılan veriyi CPU'ya yakın tutarak bu açığı daraltır. Normal
koşullarda cache tamamen şeffaftır — sen hiçbir şey yapmadan işini
görür, programın hızlanır.

Bu şeffaflık, belleğe yazan tek birim CPU olduğu sürece geçerlidir.
Sorun, sahneye **ikinci bir yazan birim** girdiğinde başlar: örneğin bir
**DMA** (Direct Memory Access; CPU'yu aradan çıkarıp veriyi doğrudan
belleğe taşıyan donanım birimi) motoru ya da PL'deki bir IP bloğu
DDR'ye doğrudan yazar. CPU'nun cache'i bu yazmadan habersizdir; CPU o
adresi sonradan okuduğunda, DDR'deki yeni veri yerine cache'te tuttuğu
**bayat** (stale) kopyayı döndürür.

{{svg:sema-13-cache-dma.svg|Şekil 13 — Cache hiyerarşisi ve tutarlılık: DMA DDR'ye yeni veri yazdıktan sonra CPU'nun cache'ten bayat veri okuması; invalidate sonrası doğru okumaya dönüş.}}

Bu, "DMA yazdı ama CPU bayat okuyor" senaryosudur ve gömülü
geliştirmenin klasik hata kaynaklarından biridir. Çare, CPU'ya "şu adres
aralığı için cache'teki kopyayı at, bir sonraki okumada gerçekten DDR'ye
git" demektir — bu işleme **invalidate** denir. Tersi ihtiyaç da vardır:
CPU'nun yazdığı veri henüz yalnızca cache'te durur ve bir DMA motorunun
o veriyi DDR'den okuması gerekir — bu durumda CPU'nun "kirli" (henüz
DDR'ye yazılmamış) cache verisi DDR'ye yazdırılmalıdır; bu işleme de
**flush** denir.

Xilinx standalone BSP'si (BSP — Board Support Package; çevre birimi
sürücülerini, açılış kodunu ve xparameters.h'yi içeren ya da üreten ara
katman; ayrıntısı Bölüm 11'de) bu işlemleri hazır fonksiyon olarak
sunar: `Xil_DCacheInvalidateRange(adres, uzunluk)` ve
`Xil_DCacheFlushRange(adres, uzunluk)`. Kural basit: **DMA'nın yazdığı
bölgeyi CPU okumadan önce invalidate et; CPU'nun yazdığı bölgeyi DMA
okumadan önce flush et.**

:::derin-dalis A53'te FlushRange Aslında InvalidateRange
ARMv8 (Cortex-A53) standalone BSP'sinde dikkate değer bir ayrıntı var:
`Xil_DCacheFlushRange` fonksiyonu kaynak kodda doğrudan
`Xil_DCacheInvalidateRange` için bir takma ad (makro) olarak
tanımlanmıştır — `#define Xil_DCacheFlushRange Xil_DCacheInvalidateRange`.
Yani adı "flush" dese de A53'te bu makro aslında bir range-invalidate
işlemi yapar (ARMv8'de bu işlem, invalidate öncesi temizlik yapan bir
"clean+invalidate" olarak gerçeklenir). Pratik sonuç: A53 kodunda iki
isme de rastlayabilirsin ve ikisi de aynı donanım işlemine çıkar — ama
isim, çağırdığı kavramsal işlemi her zaman doğru yansıtmaz. Kaynak:
`content/_arastirma.md` §10.
:::

## Alignment: Adres Sınırı

**Alignment** (hizalama), bir verinin başlangıç adresinin kendi
boyutunun katı olması gereğidir — örneğin 4 baytlık `unsigned int` 4'ün
katı bir adreste, 8 baytlık `unsigned long long` 8'in katı bir adreste
durmalıdır. Çoğu ARM mimarisinde hizasız erişim çalışır ama yavaştır
(kimi durumlarda hiç çalışmaz); DMA transferleri ise belirli bir
hizalamayı çoğu zaman **şart koşar** (örneğin cache satırı boyutu —
tipik olarak 64 bayt). Sıradan değişkenlerin hizalamasını derleyici
kendiliğinden halleder; DMA'ya ayrılmış bir tamponu elle hizalaman
gerektiğinde `__attribute__((aligned(64)))` gibi bir öznitelik
kullanırsın. Şimdilik kavrama aşina olman yeterli — Bölüm 9'da DMA ele
alınırken yeniden karşına çıkacak.

:::tuzak "Debug'da Çalışıyor, Release'te Çalışmıyor" — Tanıdık Bir Kalıp
Bu cümleyi gömülü kariyerin boyunca defalarca duyacaksın — ve kuracaksın.
İki yaygın kök nedeni vardır; ikisi de bu iki bölümde işlenen konulara
dayanır. **(1) Eksik `volatile`** — debug derlemesi genellikle `-O0`
(optimizasyonsuz) yapılır; derleyici görünüşte gereksiz okuma/yazmaları
elemez, kod "kazara" çalışır. Release derlemesi `-O2` gibi daha agresif
bir seviyede yapılır; derleyici Bölüm 5'te anlatılan optimizasyonu
uygular ve `volatile` eksikse bir okuma sessizce yok olur. **(2)
Cache/DMA tutarlılığı** — debug derlemesi genellikle daha yavaş, daha
öngörülebilir bir yolda koşar (ya da bazı debug konfigürasyonlarında
cache kapalıdır); release'te hız artınca CPU'nun cache'ten bayat veri
okuduğu pencere gerçek bir soruna dönüşür. İki durum da aynı ilkeyi
gösterir: kod baştan doğru değildi; optimizasyon seviyesi, -O0'ın
örttüğü mevcut kusuru yalnızca görünür kıldı.
:::

Belleğin nereye yerleştiğini ve cache'e ne zaman güvenilip
güvenilemeyeceğini artık biliyorsun. Sıra pratiğe geldi: bu kez kartın
tek giriş aygıtını — butonu — okuyacaksın.

:::gorev no=3 zorluk=1 baslik="Butonu Oku (Polling)" kisa="Butonu Oku"
[Hedef]
SW19 butonunu (PS MIO22) polling ile oku ve durumunu DS50 LED'ine (PS
MIO23) yansıt; debounce edilmiş basış sayacını UART'a yazdır.

[Ön koşul]
Bölüm 6 okundu; Görev 2 tamamlandı (`uart_ps` modülü hazır ve
çalışıyor).

[Adımlar]
1. Bölüm 2'den hatırla: kartın 8 LED'i, 5 butonu ve DIP switch'i PL
   pinlerindedir — bu görev yine yalnızca tek PS butonunu (SW19) ve tek
   PS LED'ini (DS50) kullanır; 8 LED'lik yürüyen ışık deseni Görev 7'ye
   ayrıldı.
2. `button_ps.h/.c` modülünü yaz: `buttonInit()` içinde, Görev 1'den
   tanıdığın `XGpioPs` sürücüsünü `LookupConfig` + `CfgInitialize` ile
   kur; SW19'u giriş, DS50'yi çıkış (artı output enable) olarak ayarla.
3. `buttonRead()` içinde SW19'u `XGpioPs_ReadPin` ile oku;
   `ledPsWrite()` içinde DS50'yi `XGpioPs_WritePin` ile sür.
4. `main()` içinde SW19'u birkaç milisaniyede bir oku (`usleep`,
   `sleep.h`); okunan ham değer art arda birkaç iterasyon boyunca
   tutarlı kalıyor ve mevcut kararlı durumdan farklıysa geçişi gerçek
   say (sayaç tabanlı debounce — aşağıdaki analojiye bak), LED'i
   güncelle ve basılı duruma doğru her geçişte sayacı bir artır.
5. Sayaç değiştiğinde `uart_ps` modülünle bir durum satırı yazdır
   (Görev 2'nin çıktısını yeniden kullan).

:::analoji Debounce: zilin gerçekten çalıp çalmadığı
Mekanik olarak gürültülü bir zil butonuna tek basış, zili art arda
birkaç kez çaldırabilir; yine de "bir kez çalındı" sonucuna varırsın,
çünkü kısa dalgalanmaları saymaz, durumun az sonra hâlâ aynı olup
olmadığına bakarsın. Sayaç tabanlı debounce aynı ilkeyle çalışır: ham
okumaya hemen güvenmez, aynı değeri art arda birkaç iterasyonda görene
kadar bekler.
:::

[Başarı kriteri]
Buton basılı tutulduğu sürece DS50 yanık kalır, bırakıldığı anda söner;
butona tam 10 kez basıldığında UART'taki sayaç tam olarak "10"
gösterir — bounce yüzünden 11 ya da 12 değil.

[Kendini sına]
- Debounce süresini (örnekleme aralığı x ardışık iterasyon sayısı) neye
  göre seçtin? Çok kısa olsa ne olurdu, çok uzun olsa ne olurdu?
- Bu polling döngüsü dönerken CPU başka hiçbir iş yapamıyor — her döngü
  iterasyonu ne kadar sürüyor ve CPU zamanının ne kadarı bu beklemeye
  gidiyor?
- `buttonRead()`'in döndürdüğü ham değeri debounce etmeden doğrudan
  LED'e yazsaydın, gözle görülür fark ne olurdu?

[Takıldıysan]
::ipucu İpucu 1 — LED Hiç Yanmıyor ya da Hep Yanık
Yön (DIRM) ve output-enable (OEN) register'larını doğru pinler için
ayarladın mı — SW19 (MIO22) giriş, DS50 (MIO23) çıkış? `buttonInit()`'in
dönüş değerini denetledin mi? `XST_SUCCESS` dönmüyorsa `xparameters.h`'ye
bakıp `XPAR_XGPIOPS_0_DEVICE_ID`'nin doğru olduğunu doğrula.
::/
::ipucu İpucu 2 — Sayaç Atlıyor (10 Basışta 11-12 Gösteriyor)
`DEBOUNCE_ESIK` (ardışık özdeş okuma eşiği) fazla küçük olabilir — bir
bounce, art arda birkaç iterasyonu dolduracak kadar uzun sürüp gerçek
geçiş sanılabilir. Eşiği büyüt ve örnekleme aralığıyla (kaç
mikrosaniyede bir okuduğunla) birlikte yeniden değerlendir; ikisinin
çarpımı senin debounce pencerendir.
::/
::cozum Tam Çözüm — lab03-button
Aşağıdaki dosyalar SW19/DS50'yi debounce'lu polling ile okuyup UART'a
yazdırır (`uart_ps` modülü lab02'den birebir kopyadır):
{{kod:lab03-button/src/button_ps.h}}
{{kod:lab03-button/src/button_ps.c}}
{{kod:lab03-button/src/main.c}}
::/
:::

Butonu birkaç milisaniyede bir sorguladığın için CPU, zamanının
neredeyse tamamını o soruya harcadı — polling'in bedelini artık gördün.
Sıra interrupt'ta: Bölüm 7'de aynı buton, CPU'yu hiç meşgul etmeden
sana kendisi haber verecek.
