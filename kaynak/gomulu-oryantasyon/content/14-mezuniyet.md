# Bölüm 14 — Mezuniyet Görevi

On bir görev boyunca kartı parça parça tanıdın: register okudun, kendi
kodunla UART'a yazı bastın, buton interrupt'ı yapılandırdın, gerçek bir
I2C çipiyle haberleştin, PL'deki bir IP bloğunu sürdün, FreeRTOS'ta
kuyruk ve semaphore ile task'lar arasında veri taşıdın. Her görev tek bir
beceriyi yalıttı — bilerek; çünkü her şeyi aynı anda öğrenmeye kalkmak,
hiçbirini iyi öğrenmemek demektir. Mezuniyet Görevi'nin tek amacı bu
yalıtımı kaldırmak: şimdi hepsini aynı anda, tek bir projede, her parça
diğerine bağlı olacak şekilde kullanacaksın. Bu, işe yeni giren bir
mühendisin ekipte alacağı ilk gerçek işin tam provasıdır — kimse eline
adım adım prosedür tutuşturmayacak; bir gereksinim listesi ve bir kabul
kriteri listesi alacaksın, gerisi senin tasarımın.

## Bu proje neden var

Aşağıdaki tablo, önceki bölümlerde kazandığın her becerinin bu projede
nerede yeniden karşına çıktığını gösteriyor. Bir yerde takılırsan önce bu
tabloya bak — hangi bölüme döneceğini söyler.

| Beceri | Öğrenildiği yer | Bu projede kullanıldığı yer |
|---|---|---|
| Register haritası okuma, `volatile` pointer, xparameters.h | Bölüm 4-5 | INA226 register erişimi, tüm donanım sürücüleri |
| Bit işlemleri (set/clear/toggle/test) | Bölüm 5 | LED durum kodlaması, register alanı okumaları |
| Bellek/stack disiplini | Bölüm 6 | Task stack boyutlandırma (R10) |
| Polling ile giriş okuma | Bölüm 6 | CLI'ın RX polling task'ı (R7) |
| GIC yapılandırma, ISR yazım kuralları | Bölüm 7 | SW19 buton interrupt'ı (R5) |
| TTC periyodik interrupt | Bölüm 7 | Periyodik ölçüm/telemetri zamanlaması (R2, R8) |
| I2C protokolü, datasheet okuma | Bölüm 8 | INA226'dan ölçüm okuma (R2, R3) |
| PL'deki IP ile haberleşme (AXI GPIO) | Bölüm 9 | Gelişmiş LED gösterimi (R4, opsiyonel katman) |
| FreeRTOS task/kuyruk/semaphore | Bölüm 10 | Tüm mimarinin omurgası (R1, R9) |
| Vitis/debug becerileri | Bölüm 11 | Geliştirme ve doğrulamanın tamamı |
| Savunmacı programlama, README/commit kültürü | Bölüm 12 | Teslim standardı (Teslim bölümü) |

## Gereksinimler

Projenin adı: **Board Health Monitor**. Kartın güç sağlığını izleyen,
UART üzerinden raporlayan ve LED'lerle görselleştiren bir FreeRTOS
uygulaması yazacaksın. Aşağıdaki on gereksinim ölçülebilir olacak şekilde
yazıldı; her biri demoda tek tek gösterilebilir olmalı.

**R1.** Sistem Xilinx FreeRTOS BSP'si (`freertos10_xilinx`) üzerinde
koşmalı ve en az üç ayrı task içermeli: ölçüm toplama task'ı, LED
gösterim task'ı ve UART/CLI task'ı (telemetri basma ile komut ayrıştırma
aynı task'ta da olabilir, ayrı task'larda da — bkz. Serbest Tasarım
Alanı).

**R2.** Bir task, PCA9544A mux'ını (U23, adres 0x75) kanal 0'a
yönlendirdikten sonra PS I2C0 üzerinden en az iki INA226 güç monitörünü
periyodik okumalı: **VCCINT (0x40)** ve **VCC1V8 (0x42)** — istersen
`_arastirma.md` §4'ten bir ray daha ekleyebilirsin.

**R3.** INA226 Bus Voltage register'ından (offset 0x02, LSB 1.25 mV)
okunan değer mV cinsinden bus gerilimine çevrilmeli.

**R4.** LED gösterim task'ı en az iki seviyede çalışmalı:
- **Temel seviye** (herkes için zorunlu): yalnızca DS50 (MIO23) ile durum
  kodlaması — örneğin sürekli yanık = sağlıklı, yavaş yanıp sönme =
  uyarı, hızlı yanıp sönme = hata.
- **Gelişmiş seviye** (Görev 7 bitstream'in varsa): 8 PL LED'ini (AXI
  GPIO üzerinden) bir ölçüm seviyesini ya da ek durum bilgisini gösteren
  bar grafik olarak kullanmak.

**R5.** SW19 butonu (MIO22, GIC IRQ 48) interrupt tabanlı çalışmalı; her
basış gösterim/telemetri modunu değiştirmeli (örneğin "VCCINT görünümü" ↔
"VCC1V8 görünümü" ↔ "genel özet"), yazılımsal debounce ile.

**R6.** UART0 üzerinden periyodik bir telemetri satırı basılmalı (en az
tick/zaman bilgisi + geçerli mod + ilgili ölçüm değerleri).

**R7.** UART üzerinde satır tamponlu bir mini komut satırı (CLI) koşmalı
ve en az şu komutları desteklemeli: `status` (geçerli ölçüm ve mod
özetini basar), `led on` / `led off` (gösterim task'ını durdurur/başlatır),
`rate <ms>` (ölçüm/telemetri periyodunu değiştirir). Tanınmayan komut
anlamlı bir hata mesajı basmalı.

**R8.** `rate <ms>` komutu çalışma zamanında etkili olmalı ve makul bir
aralıkla sınırlanmalı (örneğin 100–5000 ms); aralık dışı değer,
kullanıcıya geri bildirimle reddedilmeli.

**R9.** Task'lar arası veri paylaşımı FreeRTOS senkronizasyon nesneleri
(kuyruk, semaphore, mutex) üzerinden yapılmalı; birden çok task'ın ortak
bir değişkene kilitsiz doğrudan eriştiği (race condition riski taşıyan)
bir tasarım kabul edilmez.

**R10.** Sistem en az 5 dakika kesintisiz, çökmeden, asılı kalmadan ve
stack taşması yaşamadan koşmalı. `configCHECK_FOR_STACK_OVERFLOW` açık
kalmalı ve task stack boyutları bilinçli seçilmeli (Bölüm 6 ile 10'un
öğrettiği disiplin burada uygulanır).

## Kabul kriterleri

Aşağıdakilerin her biri demoda gözlemle, tek tek gösterilebilir olmalı:

- Güç verildiğinde UART'ta bir karşılama mesajı, kısa süre sonra ilk
  telemetri satırı görünüyor.
- `status` komutu geçerli ölçüm değerlerini ve geçerli modu doğru
  basıyor.
- `led on` / `led off` komutları LED gösterimini gözle görülür biçimde
  durdurup yeniden başlatıyor.
- `rate 200` sonrası telemetri satırlarının sıklığı gözle görülür
  artıyor; `rate 2000` sonrası gözle görülür azalıyor.
- SW19'a basmak modu anında değiştiriyor — ana döngü/task başka işle
  meşgulken bile buton yanıtı gecikmiyor (Bölüm 7'de söz verildiği gibi,
  interrupt'ın polling'e üstünlüğünü kanıtladığı yer burası).
- INA226'dan okunan VCCINT ve VCC1V8 değerleri mühendislik açısından
  makul aralıkta (nominal değerin kabaca ±%10'u).
- Sistem demo süresince (en az 10 dakika) çökmeden ve asılı kalmadan
  koşuyor.

## Serbest Tasarım Alanı

Buraya kadarki her gereksinim sana *ne* yapacağını söyledi, *nasıl*
yapacağını değil. Kaç task kullanacağın, kuyruklarını nasıl
adlandıracağın, mod değişikliğini hangi FreeRTOS nesnesinin taşıyacağı,
CLI ayrıştırıcısını nasıl yazacağın — hepsi senin kararın. Aşağıdaki
şema olası bir mimariyi gösteriyor; **bir öneridir, kopyalamak zorunda
olduğun bir şey değil**. Bu gereksinimleri üç task'la da
karşılayabilirsin, beş task'la da; önemli olan R9'un istediği temiz
senkronizasyondur.

{{svg:sema-25-mezuniyet-mimari.svg|Şekil 25 — Önerilen Mezuniyet Görevi mimarisi: FreeRTOS task'ları, kuyruklar, ISR/semaphore ile mod geçişleri ve donanım bağlantıları}}

Görev 7 bitstream'in yoksa ya da PL LED barını kurmaya vaktin olmadıysa,
R4'ün temel seviyesi (yalnızca DS50) tek başına yeterli bir teslimdir —
gelişmiş seviye bonustur, şart değil. Ölçüm rayı eklemek ya da üçüncü bir
CLI komutu (örneğin `help`) gibi ek dokunuşlar da serbest tasarım
alanının parçasıdır; gereksinimlerin üstüne çıkmak her zaman kabul
edilir, altında kalmak edilmez.

## Teslim

İki parça teslim edeceksin:

1. **Kısa bir README** (diğer `labs/` lab'larındaki dosyaların bir
   benzeri gibi düşün — ama bunu kendin yazıyorsun). Şunları içermeli:
   - Projenin amacı ve kısa mimari özeti (kaç task, hangi
     kuyruklar/semaphore'lar).
   - Donanım/yazılım gereksinimleri (Vitis sürümü, gerekiyorsa hangi
     .xsa/bitstream).
   - Nasıl derlenip karta yükleneceği (Vitis proje tipi, adımlar).
   - CLI komut listesi ve beklenen çıktıdan bir örnek.
   - Bilinen sınırlamalar ("X'i şu nedenle yapmadım..." — Bölüm 12'nin
     öğrettiği gibi, burada dürüstlük değerlidir).
2. **Ekip önünde 10 dakikalık canlı demo.** Kabul kriterlerini sırayla
   gez ve soruları anında yanıtlamaya hazır ol. Bu, gerçek işte
   vereceğin "bitti" demosunun provasıdır.

## Takıldıysan

Çözüm kodu vermiyoruz — bu projenin bütün amacı kendi tasarımını kurman.
Ama üç yaygın mimari tuzaktan kaçınman için üç işaret bırakıyoruz:

- **UART'ı tek task'a ver.** Telemetri basma (TX) ile CLI okuma (RX) aynı
  fiziksel çevre birimini paylaşır; iki ayrı task aynı anda
  `XUartPs_Send` çağırırsa çıktı iç içe geçip bozulabilir. RX tarafı için
  ayrı bir interrupt yolu kurmaya gerek yok — kısa gecikmeyle dönen bir
  `XUartPs_Recv` **polling** task'ı, karakterleri satır tamponunda
  biriktirip `\r`/`\n` görünce komutu ayrıştırmak bu ölçekte yeterli ve
  makuldür.
- **Ölçüm toplama, gösterim ve CLI'ı kuyruklarla ayır.** Ölçüm task'ının
  INA226'dan okuduğu değer diğer task'lara doğrudan paylaşılan bir global
  değişkenle değil, kuyrukla (ya da en azından mutex korumalı bir ortak
  yapıyla) ulaşmalı. Aynı şekilde CLI'ın ayrıştırdığı komutlar (`led on`,
  `rate <ms>`) ilgili task'a kuyruk mesajı olarak gitmeli — R9'un
  "kilitsiz paylaşım yok" kuralının doğal sonucu budur.
- **Mod değişikliğini semaphore ya da event ile taşı; ISR içinde işleme.**
  SW19 ISR'ı kısa kalmalı (Bölüm 7'nin kuralı burada da geçerli): ISR
  yalnızca `FromISR` API'siyle bir binary semaphore vermeli; mod değişikliği
  mantığının kendisi (hangi ekrana geçileceğine karar vermek, LED
  desenini güncellemek) o semaphore'u bekleyen bir task'ta koşmalı.

:::gorev no=mezuniyet zorluk=3 baslik="Board Health Monitor" kisa="Mezuniyet"
[Hedef]
I2C üzerinden güç ölçümleri toplayan, durumu LED'lerle gösteren, SW19
interrupt'ı ile mod değiştiren, UART üzerinden hem periyodik telemetri
hem mini CLI sunan bağımsız bir "Board Health Monitor" uygulamasını
FreeRTOS üzerinde tasarla ve çalışır hâle getir.
[Ön koşul]
Görev 0'dan Görev 10'a kadar tamamlanmış olmalı: I2C okuma, interrupt
yapılandırma, FreeRTOS task/kuyruk/semaphore becerileri ve (varsa) AXI
GPIO becerisi burada bir araya geliyor.
[Gereksinimler]
- En az 3 FreeRTOS task'ı: ölçüm toplama, LED gösterim, UART/CLI
  (R1, R9).
- INA226'dan VCCINT (0x40) ve VCC1V8 (0x42) periyodik okuması, mV'a
  çevrim (R2, R3).
- İki seviyeli LED gösterimi: DS50 temel seviye + PL LED barı gelişmiş
  seviye, opsiyonel (R4).
- SW19 interrupt'ı ile mod değişimi (R5).
- Periyodik UART telemetrisi + `status` / `led on` / `led off` /
  `rate <ms>` mini CLI'ı (R6, R7, R8).
- Kilitsiz paylaşım olmadan, senkronize, 5 dakika kesintisiz çalışma
  (R9, R10).

Tam gereksinim listesi (R1–R10) ve kabul kriterleri için bölümün başına
bak.
[Kabul kriterleri]
- Açılışta UART karşılama mesajı + ilk telemetri satırı.
- `status`, `led on`, `led off` ve `rate <ms>` komutları beklendiği gibi
  çalışıyor.
- SW19 modu anında değiştiriyor (sistem meşgulken bile).
- VCCINT/VCC1V8 okumaları makul aralıkta.
- Sistem 10 dakikalık demo boyunca çökmeden koşuyor.
[Teslim]
Kısa bir README (amaç, mimari özeti, derleme/yükleme adımları, CLI komut
listesi, bilinen sınırlamalar) + ekip önünde 10 dakikalık canlı demo.
[Kendini sına]
- Mod değişikliğini ISR içinde doğrudan işlemek yerine neden bir semaphore'a
  devrettin? Doğrudan işleseydin hangi task'lar risk altında olurdu?
- `rate <ms>` değerini kuyruk yerine paylaşılan bir global değişkende
  tutsaydın, race condition hangi senaryoda ortaya çıkardı?
- İki ayrı task (biri telemetri, biri CLI yanıtları için) UART'a doğrudan
  bassaydı ne gözlemlerdin? Bunu nasıl önledin?
[Takıldıysan]
::ipucu İpucu 1 — Mimariyi kodlamadan önce çiz
Klavyeye dokunmadan önce task'larını, aralarındaki
kuyrukları/semaphore'ları ve her birinin kullandığı donanımı kutu-ok
şeması olarak çiz (Şekil 25'e bakmadan önce kendi sürümünü dene). "Bu
veri nereden nereye gidiyor" sorusuna kâğıt üzerinde net cevap
veremiyorsan, kodda da veremezsin.
::/
::ipucu İpucu 2 — Küçük başla, katman katman büyüt
Yalnızca iki task'la başla: ölçüm toplama ve UART'a basma (arada bir
kuyruk). Bu ikisi güvenilir çalışınca LED gösterim task'ını, sonra SW19
interrupt'ını, en son CLI ayrıştırıcısını ekle. Her yeni katmanı
eklediğinde bir öncekinin hâlâ çalıştığını doğrula — Bölüm 12'nin "küçük
adımlarla ilerle" öğüdünün en değerli olduğu yer burasıdır.
::/
:::

Kartı gördün, gereksinimleri okudun, şemayı inceledin. Şimdi sıra sende.

---

Buraya kadar geldiysen: tebrikler. İlk gün masanda seni ürküten kart
artık senin komutanda — register'larını okudun, interrupt'larını
yapılandırdın, protokollerini konuştun, kendi FreeRTOS uygulamanı yazdın.
Bu doküman burada bitiyor ama öğrenmen bitmiyor; sırada ekipte **ilk
gerçek işin** var ve bu kez büyük ihtimalle kimse senin için görev kartı
hazırlamayacak — işi parçalara kendin böleceksin. Gerektiğinde yanına iki
kaynak al: bu dokümanın **Ek A — Hızlı Referans**'ı (masanda
tutabileceğin bir özet) ve Bölüm 13'te tanıtılan **saha kılavuzları** —
Bellek Mimarisi, Ethernet, RF Örnekleme — bu yolculuğun bilerek sana
bıraktığı derinlikler için oradalar.

Kolay gelsin. Ekibe hoş geldin.
