# Bölüm 10 — İşletim Sistemi: Bare-metal'den FreeRTOS'a

Şu ana kadar yazdığın her şey **bare-metal**ti — işletim sistemi yok, tek
bir `main()`, sonsuz bir döngü, araya giren birkaç interrupt (kesme).
Görev 4 ve 5'te bunu güzelce çalıştırdın: buton kesmesi bir bayrak set
ediyor, timer kesmesi bir sayaç arttırıyor, ana döngü bayrakları kontrol
edip işini yapıyordu. Küçük bir sistemde bu mimari hem yeterli hem de
anlaşılırdır. Bu bölümün konusu, o mimarinin nerede çatırdamaya başladığı
ve bunun çözümü olan **FreeRTOS**. Konu yoğun olduğu için bölümü iki
oturuma ayırdık: önce FreeRTOS'un çekirdek mekaniğini (task, öncelik,
scheduler, tick) kuracağız ve elini kart üzerinde kirleteceksin; sonra
task'lar arasında veri ve olay paylaşmanın araçlarına (queue, semaphore,
mutex) ve bunların klasik tuzaklarına geçeceğiz.

## Birinci parça: RTOS çekirdeği

Bu ilk oturumda tek bir soru peşindeyiz: FreeRTOS bir task'ı nasıl tanır,
çalıştırır ve zamanlar? Task'lar arası iletişimi (queue, semaphore, mutex)
bilinçli olarak ikinci oturuma bırakıyoruz — önce tek bir task'ın hayat
döngüsünü sağlam anlamalısın, üstüne bir şey inşa etmeden önce.

## Bayrak çorbası: bare-metal'in sınırı

Görevlerin sayısı arttıkça süperdöngü + ISR mimarisi bir örüntüye girer:
her yeni iş için yeni bir bayrak, ana döngüde yeni bir `if`. Beş, altı iş
olunca döngü artık "hangi bayrak ne zaman set edildi, hangi sırayla
kontrol edilmeli, biri diğerini geciktirir mi" sorularının cevaplanamadığı
bir **bayrak çorbasına** dönüşür. Daha kötüsü: hiçbir işin zamanlama
garantisi yoktur. Döngünün başındaki iş uzun sürerse, sondaki iş o kadar
geç çalışır — kimse bunu sana söylemez, koddan da görünmez, sadece bir gün
"neden bu buton bazen geç tepki veriyor" sorusuyla karşına çıkar.

{{svg:sema-21-superdongu-rtos.svg|Şekil 21 — Bare-metal süperdöngü ile FreeRTOS scheduler'ının yan yana karşılaştırması: "aynı anda" çalışmak, tek çekirdekte hızlı dilimlemedir.}}

## Neden RTOS

**RTOS (Real-Time Operating System — gerçek zamanlı işletim sistemi)**,
tek bir sorunu çözmek için var: birden çok **mantıksal işi**, her birinin
kendi zamanlama beklentisini karşılayacak şekilde, tek bir CPU üzerinde
yönetmek. Anahtar kelime **bloklanma**dır. Bare-metal dünyada "bekle"
demek çoğu zaman boş bir döngüde CPU'yu döndürmek demekti (`while
(!bayrak);` gibi) — CPU o sürede hiçbir faydalı iş yapmaz. RTOS dünyasında
"bekle" demek, o işin CPU'yu **gönüllü olarak bıraktığı**, scheduler'ın
(zamanlayıcı) o süre boyunca CPU'yu başka işe verdiği bir durumdur. Aynı
kelime, tamamen farklı bir davranış.

## FreeRTOS çekirdeği: task, öncelik, tick

FreeRTOS'un temel birimi **task** (görev — bare-metal'deki "iş" kelimesiyle
karıştırma, burada FreeRTOS'un resmi terimi). Her task, kendi yığınına
(stack) sahip, bağımsız çalışan bir fonksiyondur ve her an dört durumdan
birindedir:

- **Running** — o an CPU'da çalışan (tek çekirdekte aynı anda yalnızca bir
  task Running olabilir).
- **Ready** — çalışmaya hazır, sırasını bekliyor.
- **Blocked** — bir olayı (süre dolması, veri gelmesi, bir kaynağın
  serbest kalması) bekliyor; o olay gerçekleşene kadar CPU'ya aday değil.
- **Suspended** — zamanlama dışı bırakılmış, biri onu açıkça uyandırana
  kadar hiçbir şey beklemez.

Her task'a bir **öncelik** (priority) atarsın. FreeRTOS'un scheduler'ı
**preemptive**tir (önalımlı) — yani Ready durumundaki en yüksek öncelikli
task her zaman CPU'yu alır; düşük öncelikli bir task çalışırken yüksek
öncelikli bir task Ready olursa, scheduler düşük öncelikliyi anında keser.
Bu kesme kararını hangi sıklıkla verdiğini belirleyen şey **tick**tir:
periyodik bir donanım zamanlayıcısının ürettiği düzenli kesme.
`configTICK_RATE_HZ` bizim BSP'mizde (`freertos10_xilinx`) varsayılan
olarak **100 Hz**'dir — yani scheduler saniyede 100 kez "şu an kim
çalışmalı" kararını gözden geçirir.

Task'ların doğuşunu, önceliklerini ve scheduler'ın onları nasıl sıraya
soktuğunu gördün; sıra elini kirletmede. Görev 8'de üç task'ı aynı anda
ayağa kaldıracaksın — aralarında SW19'dan gelen bir sinyal de olacak; onu
nasıl taşıdığımızın ayrıntılı mekaniğine ikinci oturumda gireceğiz, şimdilik
görev kartındaki adımlar sana yeter.

:::gorev no=8 zorluk=2 baslik="İlk FreeRTOS Uygulaman" kisa="İlk FreeRTOS"
[Hedef]
Üç FreeRTOS task'ını (heartbeat, durum, buton işleyici) birbirini
bozmadan aynı sistemde çalıştırmak.

[Ön koşul]
Bölüm 10'un birinci parçası okundu; Görev 4'te (buton kesmesi) kurduğun
GIC/GPIO kesme mantığına aşinasın.

[Adımlar]
1. Vitis'te platform component'ini OS = `freertos10_xilinx` ile oluştur
   (işlemci `psu_cortexa53_0`).
2. `heartbeatTask` task'ını yaz: DS50 LED'ini (MIO23) 500 ms periyotla
   `vTaskDelay` ile toggle etsin — **boş döngüyle bekleme yok**.
3. `statusTask` task'ını yaz: her 2 saniyede bir UART'a bir durum satırı
   bassın.
4. SW19 (MIO22) için bir binary semafor oluştur; ISR içinde
   `xSemaphoreGiveFromISR` ile ver, sonunda `portYIELD_FROM_ISR` çağır.
5. `buttonHandlerTask` task'ını yaz: `xSemaphoreTake` ile semaforu bekleyip
   her basışta bir satır bassın.
6. `xTaskCreate` ile üç task'ı da oluştur, `vTaskStartScheduler()` ile
   başlat.

[Başarı kriteri]
DS50 düzenli 500 ms'de bir yanıp sönerken terminalde her 2 saniyede bir
durum satırı akıyor ve SW19'a her basışında araya bir buton satırı
giriyor — üç iş birbirini bozmadan çalışıyor.

[Kendini sına]
- `vTaskDelay` ile boş bir `while` döngüsünde beklemenin CPU açısından
  farkı ne?
- Semaphore yerine bare-metal'deki gibi bir global bayrak kullansaydın
  ne kaybederdin?
- `statusTask` ve `heartbeatTask` aynı önceliğe sahip — bu bir sorun
  yaratır mı? Neden?

[Takıldıysan]
::ipucu İpucu 1 — LED yanıp sönmüyor ya da terminal hiç yazmıyor
`vTaskStartScheduler()`'dan önce GPIO ve GIC kurulumunun (yön ayarı,
kesme bağlama) bare-metal'deki Görev 4'ten farksız olduğunu doğrula.
Scheduler başlamadan önce çağrılan kod hâlâ sıradan bare-metal koddur.
::/
::ipucu İpucu 2 — buton satırı hiç görünmüyor
`XGpioPs_IntrClearPin`'i ISR içinde çağırmayı unutma — temizlenmeyen bir
kesme, GIC'i kilitli tutar ve bir daha tetiklenmez. `portYIELD_FROM_ISR`'a
verdiğin `BaseType_t` değişkeninin ISR başında `pdFALSE` ile
başlatıldığından emin ol.
::/
::cozum Tam çözüm — lab08-freertos
`labs/lab08-freertos/src/main.c` üç task'ı, GIC/GPIO kurulumunu ve
FromISR akışını uçtan uca gösterir.
{{kod:lab08-freertos/src/main.c}}
::/
:::

Şu ana kadar tek tek task'ların nasıl doğduğunu, önceliklendiğini ve
scheduler tarafından nasıl değiştirildiğini gördün — Görev 8'de SW19'dan
gelen bir sinyali bir semaforla task'a taşıyarak bunu elinle de kurdun.
Ama gerçek sistemlerde task'lar adalar gibi izole çalışmaz; veri ve olay
paylaşmaları gerekir. İkinci oturumda bu paylaşımın üç temel aracına ve
beraberinde gelen klasik tuzaklara geçiyoruz.

## İkinci parça: task'lar arası iletişim ve tuzaklar

Görev 8'de SW19 için oluşturduğun semaforun aslında ne olduğunu, queue ve
mutex'le birlikte nasıl bir aile oluşturduğunu ve bu ailenin hangi
tuzaklara açık olduğunu bu oturumda göreceksin. Aşağıdaki şema bu ikinci
oturumun tamamını tek bakışta özetliyor: task durum makinesi, artık
queue/semaphore/mutex/ISR'in tetiklediği geçişlerle birlikte.

{{svg:sema-22-freertos-nesneleri.svg|Şekil 22 — FreeRTOS çekirdek nesneleri haritası: task durum makinesi ile queue, semaphore, mutex ve ISR'in tetiklediği geçişler.}}

## Queue, semaphore, mutex: ne zaman hangisi

Task'lar birbirinden izole çalışır ama gerçek sistemler veri ve olay
paylaşmak zorundadır. FreeRTOS bunun için üç temel nesne sunar, üçü de
farklı bir soruya cevap verir:

- **Queue (kuyruk)** — *veri taşımak* içindir. Bir task `xQueueSend` ile
  bir kopya veri koyar, başka bir task `xQueueReceive` ile alır; FIFO
  sırayla, boyutu sabit bir tampon üzerinden. "Bu ölçüm değerini oradan
  buraya güvenli taşı" sorusunun cevabı budur.
- **Semaphore (semafor)** — *olay bildirmek* içindir, veri taşımaz.
  İkili (binary) semafor "bir şey oldu" der (bir kesme geldi, bir iş
  bitti); sayaçlı (counting) semafor "şu kadar kaynak/olay birikti" der.
  "Buton basıldı, uyan" sorusunun cevabı budur — Görev 8'deki SW19
  semaforu tam olarak bu.
- **Mutex (mutual exclusion — karşılıklı dışlama)** — *paylaşılan bir
  kaynağı korumak* içindir. Görünüşte ikili semaforla aynı API'yi
  kullanır ama anlamı farklıdır: mutex'i alan task'ın onu geri vermesi
  beklenir ("bu kaynağı ben kilitledim, işim bitince açarım"), semaforda
  böyle bir "sahiplik" fikri yoktur. Bu farkın neden önemli olduğunu
  birazdan (öncelik ters dönmesi) göreceksin.

## ISR'den task'a: FromISR ailesi

Bölüm 7'de öğrendiğin kural hâlâ geçerli: ISR (kesme rutini) kısa tutulur,
içinde `xil_printf` çağırmazsın, uzun iş yapmazsın. FreeRTOS'ta ISR'ler bir
task'ı Blocked'tan Ready'e taşıyarak "haber verir" ama normal
`xQueueSend`/`xSemaphoreGive` çağrılarını ISR içinde **kullanamazsın** —
bunlar scheduler'ı bloklayabilecek varsayımlarla yazılmıştır ve kesme
bağlamında güvenli değildir. Bunun yerine her nesnenin bir **FromISR**
kardeşi vardır: `xQueueSendFromISR`, `xSemaphoreGiveFromISR`. Bu
fonksiyonlar bir çıktı parametresiyle "bu işlem, benden daha yüksek
öncelikli bir task'ı uyandırdı mı" bilgisini verir; ISR'in sonunda
`portYIELD_FROM_ISR()` çağrısı, cevap evetse scheduler'a "ISR'den çıkar
çıkmaz o task'a geç" der. Görev 8'de bunu SW19 butonuyla zaten kurdun —
şimdi az önce elinle yaptığının arkasındaki mekanizmayı görüyorsun.

:::tuzak Stack taşması: sessiz ve tehlikeli
Her task kendi stack'ine sahiptir ve bu stack `xTaskCreate` çağrısında
verdiğin sabit boyuttadır — büyümez. Yerel değişkenlerin, fonksiyon çağrı
zincirin bu sınırı aşarsa **stack taşması (stack overflow)** olur ve
sonuç genelde açık bir hata mesajı değil, rastgele bozulma, çökme, ya da
hiç ilgisiz bir değişkenin beklenmedik şekilde değişmesidir. BSP'mizin
varsayılanı `configCHECK_FOR_STACK_OVERFLOW = 2` — FreeRTOS her context
switch'te (context switch — CPU'nun bir task'tan diğerine geçerken o anki
durumunu kaydedip yenisini yüklemesi) stack'in belirli bir deseni koruyup
korumadığını denetler ve taşma tespit ederse
`vApplicationStackOverflowHook`'u çağırır. Şüphelendiğin bir task için
`uxTaskGetStackHighWaterMark(handle)` fonksiyonu, o task'ın şimdiye kadar
stack'inin ne kadarına yaklaştığını (kalan en düşük boş alan) döndürür —
sayı küçüldükçe tehlike büyür. Görev 10'da (Bug Avı) bu tuzağın canlı bir
örneğiyle karşılaşacaksın.
:::

:::derin-dalis Öncelik ters dönmesi (priority inversion) ve mirası
Şu senaryoyu düşün: düşük öncelikli bir task bir mutex'i almış, kaynağı
kullanıyor. Yüksek öncelikli bir task aynı mutex'i istiyor, doğal olarak
Blocked'a düşüyor — düşük öncelikli task işini bitirip mutex'i bırakana
kadar bekleyecek, makul. Ama araya **orta öncelikli** bir task girip
CPU'yu meşgul ederse ne olur? Scheduler kuralına göre orta öncelikli task,
düşük öncelikliyi keser (çünkü daha yüksek öncelikli); düşük öncelikli
task mutex'i bırakamaz, dolayısıyla yüksek öncelikli task da bekletmeye
devam eder. Sonuç: en yüksek öncelikli task, ondan daha düşük öncelikli
bir task yüzünden değil, **ondan da düşük bir task'ın CPU'yu tutması**
yüzünden bekliyor — önceliklerin sırası fiilen tersine dönmüş oldu. Buna
**öncelik ters dönmesi** denir ve gerçek zamanlı sistemlerde ciddi
zamanlama ihlallerine yol açabilir.

FreeRTOS'un mutex'i (adi semaforun aksine) **öncelik mirası (priority
inheritance)** uygular: düşük öncelikli task bir mutex'i tutarken ondan
daha yüksek öncelikli biri o mutex'i beklemeye başlarsa, düşük öncelikli
task *geçici olarak* bekleyenin önceliğine yükseltilir — böylece orta
öncelikli task onu kesemez, mutex çabucak serbest kalır, gerçek sahibi
işine devam eder. Bu, semaforla mutex arasındaki API benzerliğinin altında
yatan gerçek farktır: paylaşılan kaynağı koruman gerektiğinde her zaman
mutex kullan, "aynı işi görüyor" diye adi semaforla idare etme.
:::

Task/queue/semaphore mekaniği artık elinde; sıra bunu gerçek bir
üretici/tüketici hattında birleştirmede.

:::gorev no=9 zorluk=2 baslik="Queue ile Üretici/Tüketici" kisa="Queue Akışı"
[Hedef]
Bir üretici task'ın periyodik ölçtüğü veriyi bir queue üzerinden bir
tüketici task'a taşıyıp güvenli, düzenli bir çıktı üretmek.

[Ön koşul]
Bölüm 10'un ikinci parçası okundu; Görev 8 tamamlandı; Görev 6'nın
`ina226` modülüne (ya da bu lab'ın kendi kopyasına — bkz.
`labs/lab09-kuyruk/README.md`) aşinasın.

[Adımlar]
1. `SMeasurementPacket` struct'ını tanımla: zaman damgası + VCCINT mV
   değeri.
2. Bir queue oluştur: `xQueueCreate(uzunluk, sizeof(SMeasurementPacket))`.
3. `producerTask` task'ını yaz: 500 ms'de bir `ina226ReadBusVoltageMv` ile
   ölçüm al, paketle, `xQueueSend` ile kuyruğa koy.
4. `consumerTask` task'ını yaz: `xQueueReceive` ile bekle, gelen paketi
   formatlayıp `xil_printf` ile bas.
5. UART'a **yalnızca** `consumerTask`'ın yazdığından emin ol — bu,
   satırların karışmamasını mimari olarak garantiler.

[Başarı kriteri]
Terminalde zaman damgalı mV satırları düzenli akıyor; üretici ve tüketici
farklı hızlarda çalışsa da veri kaybolmuyor (kuyruk doluysa bu açıkça
bildiriliyor, sessizce kaybolmuyor).

[Kendini sına]
- Kuyruk dolduğunda `xQueueSend` ne yapar? Bu davranışı nasıl gözlemlersin?
- Ölçümü doğrudan `consumerTask` içinde alsaydın (queue'suz, tek task)
  mimari olarak ne kaybederdin?

[Takıldıysan]
::ipucu İpucu 1 — hiç veri akmıyor
`ina226Init()`'ın dönüş değerini kontrol ettiğinden emin ol; INA226
kimlik doğrulaması (`0x5449`) başarısızsa üretici hiç ölçüm göndermez.
I2C0/mux kurulumunu Bölüm 8'deki (I2C) refleksle kontrol et.
::/
::ipucu İpucu 2 — satırlar bazen karışıyor gibi görünüyor
İki task'ın da doğrudan `xil_printf` çağırmadığından emin ol; yalnızca
`consumerTask` yazmalı. `producerTask`'ın yazdığı tek şey kuyruk dolu
uyarısıdır ve bu da nadiren, yalnızca gerçekten tüketici geride
kaldığında olmalı.
::/
::cozum Tam çözüm — lab09-kuyruk
`labs/lab09-kuyruk/src/main.c` üretici/tüketici çiftini, `src/ina226.c`
INA226 okuma modülünü içerir.
{{kod:lab09-kuyruk/src/main.c}}
::/
:::

## Bizim dünyanın dışında: ticari RTOS'lar

FreeRTOS bizim ekipte ve genel gömülü dünyada en yaygın tercih — açık
kaynaklı, hafif, Xilinx'in resmi desteğiyle geliyor. Ama havacılık, tıbbi
cihaz ya da otomotiv gibi sertifikasyon gerektiren (DO-178C, IEC 62304
gibi standartlara uyum isteyen) alanlarda **VxWorks**, **QNX** ya da
**Integrity** gibi ticari, sertifikalı RTOS'lar tercih edilir; bunların
maliyeti ve destek modeli farklıdır ama garantileri (belgelenmiş worst-case
zamanlama, sertifikasyon dosyaları) bu alanlarda vazgeçilmezdir. Bizim
yolculuğumuzda karşına çıkmayacaklar ama adlarını duyduğunda "FreeRTOS'un
ticari akrabaları" diye tanıyabilmen yeterli.

Bunca parçayı (görevler, kesmeler, kuyruklar, register haritaları) bir
arada yönetmek için artık aletlerini daha iyi tanıman gerekiyor —
sıradaki durak Vitis'in kendisi.
