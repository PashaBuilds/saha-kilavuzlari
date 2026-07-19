# Bölüm 10 — İşletim Sistemleri: Bare-Metal'den FreeRTOS'a

Şimdiye dek yazdığın her şey **bare-metal**'di — işletim sistemi yok, tek
bir `main()`, bir sonsuz döngü ve araya giren interrupt'lar. Görev 4 ve
5'te bunu iyi kullandın: buton interrupt'ı bayrak kurdu, timer interrupt'ı
sayaç artırdı, ana döngü bayraklara bakıp işini yaptı. Küçük bir sistemde
bu mimari hem yeterlidir hem izlemesi kolaydır. Bu bölüm, o mimarinin
nerede kırılmaya başladığını ve çözümünü anlatıyor: **FreeRTOS**. Malzeme
yoğun olduğu için bölüm iki oturuma ayrılır: önce FreeRTOS'un çekirdek
mekaniğini (task, öncelik, scheduler, tick) kurar ve bunu kartta
uygularsın; sonra task'ler arasında veri ve olay paylaşma araçlarına
(queue, semaphore, mutex) ve bunların klasik tuzaklarına geçeriz.

## Birinci Kısım: RTOS Çekirdeği

Bu ilk oturumda tek bir sorunun peşindeyiz: FreeRTOS bir task'i nasıl
tanır, çalıştırır ve zamanlar? Task'ler arası iletişimi (queue, semaphore,
mutex) bilinçli olarak ikinci oturuma bırakıyoruz — üstüne bir şey
kurmadan önce tek bir task'in yaşam döngüsünü sağlam kavramış olmalısın.

## Bayrak Karmaşası: Bare-Metal'in Sınırı

İş sayısı arttıkça süperdöngü + ISR mimarisi bir kalıba oturur: her yeni
işe yeni bir bayrak, ana döngüye yeni bir `if`. Beş altı işten sonra döngü
bir **bayrak karmaşasına** dönüşür — "hangi bayrak ne zaman kuruldu, hangi
sırayla bakılmalı, biri diğerini geciktiriyor mu" sorularının artık
cevaplanamadığı bir durum. Daha kötüsü: hiçbir iş zamanlama garantisi
taşımaz. Döngünün başındaki iş uzun sürerse sondaki iş o kadar geç
çalışır — bunu sana kimse söylemez, koddan da görünmez; bir gün "bu buton
neden bazen geç tepki veriyor" sorusu olarak ortaya çıkar.

{{svg:sema-21-superdongu-rtos.svg|Şekil 21 — Bare-metal süperdöngü ile FreeRTOS scheduler'ının yan yana karşılaştırması: "aynı anda" çalışma, tek çekirdekte hızlı zaman dilimlemedir.}}

## Neden RTOS

**RTOS (Real-Time Operating System — gerçek zamanlı işletim sistemi)**
tek bir problemi çözmek için vardır: tek CPU üzerinde birden çok
**mantıksal işi**, her biri kendi zamanlama beklentisini karşılayacak
biçimde yönetmek. Anahtar sözcük **blocking** (bloklanarak bekleme).
Bare-metal dünyada "bekle" çoğunlukla CPU'yu boş bir döngüde döndürmek
demekti (`while (!flag);` gibi) — o süre boyunca CPU yararlı hiçbir iş
yapmaz. RTOS dünyasında "bekle", işin **CPU'yu gönüllü olarak bıraktığı**
bir durumdur; scheduler (zamanlayıcı) o süre boyunca CPU'yu başka işlere
verir. Aynı kelime, bambaşka bir davranış.

## FreeRTOS Çekirdeği: Task, Öncelik, Tick

FreeRTOS'un temel birimi **task**'tir — yukarıda bare-metal anlatımında
kullandığımız "iş" sözcüğüyle karıştırma; task burada FreeRTOS'un resmî
terimidir. Her task, kendi stack'ine sahip, bağımsız çalışan bir
fonksiyondur ve herhangi bir anda dört durumdan birindedir:

- **Running** — şu anda CPU'da çalışıyor (tek çekirdekte aynı anda
  yalnızca bir task Running olabilir).
- **Ready** — çalışmaya hazır, sırasını bekliyor.
- **Blocked** — bir olayı bekliyor (sürenin dolması, veri gelmesi,
  kaynağın boşalması); o olay gerçekleşene kadar CPU adayı değil.
- **Suspended** — zamanlamanın dışına alınmış; biri onu açıkça geri
  almadıkça hiçbir şey beklemez.

Her task'e bir **öncelik** (priority) atarsın. FreeRTOS'un scheduler'ı
**preemptive**'dir (öncelikliye yer açmak için çalışanı kesen): Ready
durumundaki en yüksek öncelikli task CPU'yu her zaman alır; düşük
öncelikli bir task çalışırken daha yüksek öncelikli biri Ready olursa
scheduler düşük olanı anında keser. Bu kararın hangi sıklıkla gözden
geçirileceğini **tick** belirler: periyodik bir donanım timer'ının
ürettiği düzenli interrupt'tır. `configTICK_RATE_HZ` bizim BSP'de
(`freertos10_xilinx`) varsayılan olarak **100 Hz**'dir — yani scheduler
"şimdi kim çalışmalı" kararını saniyede 100 kez gözden geçirir.

Task'lerin nasıl doğduğunu, nasıl önceliklendirildiğini ve scheduler'ın
onları nasıl sıraladığını gördün; şimdi uygulama zamanı. Görev 8'de, biri
SW19'dan sinyal taşıyan üç task'i aynı anda ayağa kaldıracaksın — o
sinyalin nasıl taşındığının ayrıntılı mekaniğini ikinci oturumda
işleyeceğiz; şimdilik görev kartındaki adımlar sana yeter.

:::gorev no=8 zorluk=2 baslik="İlk FreeRTOS Uygulaman" kisa="İlk FreeRTOS"
[Hedef]
Üç FreeRTOS task'ini (heartbeat, durum, buton işleyici) aynı sistemde
birbirini aksatmadan çalıştır.

[Ön koşul]
Bölüm 10'un Birinci Kısmı okundu; Görev 4'te kurduğun GIC/GPIO interrupt
mantığına (buton interrupt'ı) hâkimsin.

[Adımlar]
1. Vitis'te platform bileşenini OS = `freertos10_xilinx` ile oluştur
   (işlemci `psu_cortexa53_0`).
2. `heartbeatTask` task'ini yaz: DS50 LED'ini (MIO23) `vTaskDelay` ile
   500 ms'de bir toggle etsin — **boş döngüyle bekleme yok**.
3. `statusTask` task'ini yaz: 2 saniyede bir UART'a bir durum satırı
   bassın.
4. SW19 (MIO22) için bir binary semaphore oluştur; ISR içinden
   `xSemaphoreGiveFromISR` ile ver, sonunda `portYIELD_FROM_ISR` çağır.
5. `buttonHandlerTask` task'ini yaz: `xSemaphoreTake` ile semaphore'u
   beklesin, her basışta bir satır bassın.
6. Üç task'i `xTaskCreate` ile oluştur, scheduler'ı
   `vTaskStartScheduler()` ile başlat.

[Başarı kriteri]
DS50 500 ms'de bir düzenli yanıp söner, terminale 2 saniyede bir durum
satırı düşer ve her SW19 basışında araya bir buton satırı girer — üç iş de
birbirini aksatmadan çalışır.

[Kendini sına]
- CPU açısından `vTaskDelay` ile beklemekle boş bir `while` döngüsünde
  beklemenin farkı nedir?
- Semaphore yerine bare-metal'deki gibi global bir bayrak kullansaydın ne
  kaybederdin?
- `statusTask` ile `heartbeatTask` aynı önceliği paylaşıyor — bu sorun
  yaratır mı? Neden?

[Takıldıysan]
::ipucu İpucu 1 — LED yanıp sönmüyor ya da terminalde çıktı yok
`vTaskStartScheduler()` öncesindeki GPIO ve GIC kurulumunun (yön ayarı,
interrupt bağlama) bare-metal bölümlerdeki Görev 4'ten farklı olmadığını
doğrula. Scheduler başlamadan önce çağrılan kod hâlâ sıradan bare-metal
koddur.
::/
::ipucu İpucu 2 — Buton satırı hiç düşmüyor
ISR içinde `XGpioPs_IntrClearPin` çağırmayı unutma — temizlenmeyen
interrupt GIC'i kilitli tutar ve bir daha hiç tetiklenmez.
`portYIELD_FROM_ISR`'a verdiğin `BaseType_t` değişkenini ISR'nin başında
`pdFALSE` ile başlattığından emin ol.
::/
::cozum Tam Çözüm — lab08-freertos
`labs/lab08-freertos/src/main.c` üç task'i, GIC/GPIO kurulumunu ve
FromISR akışını uçtan uca gösterir.
{{kod:lab08-freertos/src/main.c}}
::/
:::

Buraya kadar task'lerin tek tek nasıl doğduğunu, nasıl
önceliklendirildiğini ve scheduler'ın aralarında nasıl geçiş yaptığını
gördün — Görev 8'de bunu kendin de kurdun; SW19'dan gelen sinyali bir
semaphore üzerinden task'e taşıdın. Gerçek sistemlerde ise task'ler ayrı
adalar gibi yalıtık çalışmaz; veri ve olay paylaşmak zorundadır. İkinci
oturumda bu paylaşımın üç temel aracına ve beraberindeki klasik tuzaklara
dönüyoruz.

## İkinci Kısım: Task'ler Arası İletişim ve Tuzaklar

Bu oturumda, Görev 8'de SW19 için oluşturduğun semaphore'un aslında ne
olduğunu, queue ve mutex ile birlikte nasıl bir aile oluşturduğunu ve o
ailenin hangi tuzaklara açık olduğunu göreceksin. Aşağıdaki şema bu
ikinci oturumun tamamını tek bakışta özetler: task durum makinesi, bu kez
queue, semaphore, mutex ve ISR'nin tetiklediği geçişlerle birlikte.

{{svg:sema-22-freertos-nesneleri.svg|Şekil 22 — FreeRTOS çekirdek nesnelerinin haritası: task durum makinesi; queue, semaphore, mutex ve ISR'nin tetiklediği geçişlerle birlikte.}}

## Queue, Semaphore, Mutex: Hangisi, Ne Zaman

Task'ler birbirinden yalıtık çalışır, ama gerçek sistemler veri ve olay
paylaşmak zorundadır. FreeRTOS bunun için üç temel nesne sunar; her biri
farklı bir soruya cevaptır:

- **Queue (kuyruk)** — *veri taşımak* için. Bir task verinin kopyasını
  `xQueueSend` ile bırakır; diğer task `xQueueReceive` ile, FIFO
  sırasında, sabit boyutlu bir tampon üzerinden alır. "Şu ölçümü oradan
  buraya güvenle taşı" sorusunun cevabıdır.
- **Semaphore (semafor)** — *olay bildirmek* için; veri taşımaz. Binary
  semaphore "bir şey oldu" der (interrupt geldi, iş bitti); counting
  semaphore "şu kadar kaynak/olay birikti" der. "Butona basıldı, uyan"
  sorusunun cevabıdır — Görev 8'deki SW19 semaphore'u tam olarak budur.
- **Mutex (mutual exclusion — karşılıklı dışlama)** — *ortak kaynağı
  korumak* için. Görünüşte binary semaphore ile aynı API'yi kullanır,
  ama anlamı farklıdır: mutex'i alan task'ten onu geri vermesi beklenir
  ("bu kaynağı kilitledim; işim bitince bırakacağım"); semaphore'da ise
  "sahiplik" kavramı yoktur. Bu ayrımın neden önemli olduğunu birazdan
  göreceksin (priority inversion).

## ISR'den Task'e: FromISR Ailesi

Bölüm 7'de öğrendiğin kural geçerliliğini korur: ISR'yi (interrupt
service routine) kısa tut — içinde `xil_printf` çağırma, uzun süren iş
yapma. FreeRTOS'ta ISR'ler "haber vermeyi", bir task'i Blocked'dan
Ready'ye taşıyarak yapar; ama ISR içinde normal
`xQueueSend`/`xSemaphoreGive` çağrılarını **kullanamazsın** — bunlar
scheduler'ı bloklayabilecek varsayımlarla yazılmıştır ve interrupt
bağlamında güvenli değildir. Bunun yerine her nesnenin bir **FromISR**
karşılığı vardır: `xQueueSendFromISR`, `xSemaphoreGiveFromISR`. Bu
fonksiyonlar, işlemin kesilen task'ten daha yüksek öncelikli bir task'i
uyandırıp uyandırmadığını bir çıkış parametresiyle bildirir; ISR'nin
sonunda çağrılan `portYIELD_FROM_ISR()`, cevap evetse scheduler'a "ISR
biter bitmez o task'e geç" der. Görev 8'de SW19 butonuyla bunu zaten
kurdun — şimdi elle kurduğun düzeneğin arkasındaki mekanizmayı
görüyorsun.

:::tuzak Stack Overflow: Sessiz ve Tehlikeli
Her task'in kendi stack'i vardır ve o stack, `xTaskCreate` çağrısında
verdiğin sabit boyuttur — büyümez. Yerel değişkenlerin ve fonksiyon çağrı
zincirin bu sınırı aşarsa **stack overflow** (yığın taşması) oluşur;
sonuç çoğunlukla net bir hata mesajı değil, rastgele bozulma, çökme ya da
ilgisiz bir değişkenin beklenmedik biçimde değişmesidir. BSP'mizin
varsayılanı `configCHECK_FOR_STACK_OVERFLOW = 2` — her context switch'te
(CPU'nun task'ler arasında geçerken birinin durumunu kaydedip diğerininkini
yüklemesi) FreeRTOS, stack'in belirli bir deseni hâlâ koruyup korumadığını
denetler ve taşma saptarsa `vApplicationStackOverflowHook` çağırır.
Şüphelendiğin bir task için `uxTaskGetStackHighWaterMark(handle)`, o
task'in stack'ini tüketmeye ne kadar yaklaştığını (kalan en düşük boş
alanı) döndürür — sayı küçüldükçe tehlike büyür. Görev 10'da (Hata Avı)
bu tuzağın canlı bir örneğiyle karşılaşacaksın.
:::

:::derin-dalis Önceliğin Tersine Dönüşü: Priority Inversion ve Priority Inheritance
Şu senaryoyu düşün: düşük öncelikli bir task mutex'i almış, kaynağı
kullanıyor. Yüksek öncelikli bir task aynı mutex'i istiyor ve doğal
olarak Blocked'a düşüyor — düşük öncelikli task işini bitirip mutex'i
bırakana kadar bekleyecek; buraya kadar makul. Peki araya **orta
öncelikli** bir task girip CPU'yu işgal ederse? Scheduler kuralı gereği
orta öncelikli, düşük öncelikliyi keser (önceliği daha yüksek); düşük
öncelikli mutex'i bırakamaz, dolayısıyla yüksek öncelikli de beklemeye
devam eder. Sonuç: en yüksek öncelikli task, kendisinden düşük öncelikli
bir task yüzünden değil, **ondan da düşük birinin CPU'yu tutması**
yüzünden bekliyor — öncelik sırası fiilen tersine dönmüş durumda. Buna
**priority inversion** (öncelik tersine dönmesi) denir ve gerçek zamanlı
sistemlerde ciddi zamanlama ihlallerine yol açabilir.

FreeRTOS'un mutex'i (sıradan semaphore'dan farklı olarak) **priority
inheritance** (öncelik kalıtımı) uygular: mutex'i tutan düşük öncelikli
task'i daha yüksek öncelikli biri beklemeye başlarsa, düşük öncelikli
*geçici olarak* bekleyenin önceliğine yükseltilir — böylece orta
öncelikli araya giremez, mutex hızla bırakılır ve gerçek bekleyen yoluna
devam eder. Semaphore ile mutex arasındaki API benzerliğinin altındaki
asıl fark budur: ortak kaynak koruman gereken her yerde mutex kullan —
"aynı işi görüyor" diyerek sıradan semaphore ile idare etme.
:::

Task/queue/semaphore mekaniği artık elinde; sıra bunları gerçek bir
üretici/tüketici hattında birleştirmekte.

:::gorev no=9 zorluk=2 baslik="Queue ile Üretici/Tüketici" kisa="Queue Akışı"
[Hedef]
Üretici task'in periyodik olarak ölçtüğü veriyi bir queue üzerinden
tüketici task'e taşı; güvenli ve düzenli çıktı üret.

[Ön koşul]
Bölüm 10'un İkinci Kısmı okundu; Görev 8 tamamlandı; Görev 6'nın `ina226`
modülüne (ya da bu lab'ın kendi kopyasına — bkz.
`labs/lab09-queue/README.md`) hâkimsin.

[Adımlar]
1. `SMeasurementPacket` struct'ını tanımla: zaman damgası + VCCINT mV
   değeri.
2. Bir queue oluştur: `xQueueCreate(uzunluk, sizeof(SMeasurementPacket))`.
3. `producerTask` task'ini yaz: 500 ms'de bir `ina226ReadBusVoltageMv`
   ile ölçüm al, paketle, `xQueueSend` ile kuyruğa bırak.
4. `consumerTask` task'ini yaz: `xQueueReceive` ile bekle, gelen paketi
   biçimleyip `xil_printf` ile bas.
5. UART'a **yalnızca** `consumerTask`'in yazdığından emin ol — satırların
   birbirine girmemesini mimari olarak bu garanti eder.

[Başarı kriteri]
Terminalde zaman damgalı mV satırları düzenli akar; üretici ile tüketici
farklı hızlarda çalışsa bile veri kaybolmaz (queue doluysa bu sessizce
yutulmaz, açıkça raporlanır).

[Kendini sına]
- Queue doluyken `xQueueSend` ne yapar? Bu davranışı nasıl gözlemlerdin?
- Ölçümü doğrudan `consumerTask` içinde alsaydın (queue yok, tek task),
  mimari olarak ne kaybederdin?

[Takıldıysan]
::ipucu İpucu 1 — Hiç veri akmıyor
`ina226Init()` dönüş değerini denetlediğinden emin ol; INA226 kimlik
doğrulaması (`0x5449`) başarısızsa üretici hiç ölçüm göndermez. I2C0/mux
kurulumunu Bölüm 8'deki (I2C) yaklaşımla gözden geçir.
::/
::ipucu İpucu 2 — Satırlar bazen birbirine giriyor
`consumerTask` dışında hiçbir task'in doğrudan `xil_printf` çağırmadığını
doğrula; yalnızca o yazmalı. `producerTask`'in basabileceği tek şey
queue-dolu uyarısıdır ve bu nadir olmalı — yalnızca tüketici gerçekten
geride kaldığında.
::/
::cozum Tam Çözüm — lab09-queue
`labs/lab09-queue/src/main.c` üretici/tüketici çiftini, `src/ina226.c`
INA226 okuma modülünü içerir.
{{kod:lab09-queue/src/main.c}}
::/
:::

## Bizim Dünyamızın Ötesi: Ticari RTOS'lar

FreeRTOS hem ekipte hem gömülü dünyada genel olarak en yaygın tercihtir —
açık kaynaktır, hafiftir ve resmî Xilinx desteğiyle gelir. Sertifikasyon
gerektiren alanlarda ise — DO-178C ya da IEC 62304 gibi standartlara
uyumun zorunlu olduğu havacılık, tıbbi cihaz veya otomotiv — **VxWorks**,
**QNX**, **Integrity** gibi ticari, sertifikalı RTOS'lar tercih edilir;
maliyetleri ve destek modelleri farklıdır, ama garantileri (belgelenmiş
en-kötü-durum zamanlaması, sertifikasyon kanıtları) o alanlarda
vazgeçilmezdir. Buradaki yolculuğunda karşına çıkmayacaklar; adlarını
duyduğunda "FreeRTOS'un ticari muadilleri" diye tanıman yeterli.

Tüm bu parçaları — task'leri, interrupt'ları, queue'ları, register
haritalarını — bir arada yönetmek, artık aletlerini daha iyi tanımanı
gerektiriyor. Sıradaki durak Vitis'in kendisi.
