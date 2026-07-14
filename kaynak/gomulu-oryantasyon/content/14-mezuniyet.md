# Bölüm 14 — Mezuniyet Görevi

On bir görev boyunca kartı parça parça tanıdın: register okudun, UART'a
kendi elinle yazı bastın, buton kesmesi kurdun, gerçek bir I2C çipiyle
konuştun, PL'deki bir IP'yi sürdün, FreeRTOS'ta task'lar arasında queue ve
semaphore ile veri taşıdın. Her görev bir beceriyi izole etti — bilinçli
olarak, çünkü tek seferde her şeyi öğrenmeye çalışmak hiçbir şeyi öğrenmemek
demektir. Mezuniyet Görevi'nin tek işi bu izolasyonu kaldırmak: artık hepsini
aynı anda, aynı proje içinde, birbirine bağımlı hâlde kullanacaksın. Bu, işe
yeni başlayan bir mühendisin ekipte alacağı ilk gerçek görevin tam
provasıdır — kimse sana adım adım tarif vermeyecek, sana bir gereksinim
listesi ve bir kabul kriteri seti verilecek, gerisi senin tasarımın.

## Bu Görev Neden Var

Aşağıdaki tablo, önceki bölümlerde öğrendiğin hangi becerinin bu projede
nerede karşına çıkacağını gösteriyor. Takıldığın bir yerde önce bu tabloya
bak — hangi bölüme dönmen gerektiğini burada bulursun.

| Beceri | Öğrenildiği Bölüm | Bu Projede Nerede Kullanılıyor |
|---|---|---|
| Register map okuma, `volatile` pointer, xparameters.h | Bölüm 4-5 | INA226 register erişimi, tüm donanım sürücüleri |
| Bit işlemleri (set/clear/toggle/test) | Bölüm 5 | LED durum kodlama, register alan okuma |
| Bellek/stack disiplini | Bölüm 6 | Task stack boyutlandırma (R10) |
| Polling ile giriş okuma | Bölüm 6 | CLI'nin RX polling task'ı (R7) |
| GIC kurulumu, ISR yazma kuralları | Bölüm 7 | SW19 buton kesmesi (R5) |
| TTC periyodik kesme | Bölüm 7 | Periyodik ölçüm/telemetri zamanlaması (R2, R8) |
| I2C protokolü, datasheet okuma | Bölüm 8 | INA226'dan ölçüm alma (R2, R3) |
| PL'deki IP ile konuşma (AXI GPIO) | Bölüm 9 | Gelişmiş LED gösterge (R4, opsiyonel katman) |
| FreeRTOS task/queue/semaphore | Bölüm 10 | Tüm mimarinin omurgası (R1, R9) |
| Vitis/debug becerileri | Bölüm 11 | Geliştirme ve doğrulama süreci boyunca |
| Savunmacı programlama, README/commit kültürü | Bölüm 12 | Teslim standardı (TESLİM) |

## Gereksinimler

Proje adı: **Kart Sağlık Monitörü**. FreeRTOS üzerinde çalışan, kartın güç
sağlığını izleyip UART üzerinden raporlayan ve LED'lerle görselleştiren bir
uygulama yaz. Aşağıdaki on gereksinim ölçülebilir olacak şekilde yazıldı;
her biri demoda tek tek gösterilebilmeli.

**R1.** Sistem, Xilinx FreeRTOS BSP'si (`freertos10_xilinx`) üzerinde
çalışmalı ve en az üç ayrı task içermeli: bir ölçüm toplama task'ı, bir LED
gösterge task'ı, bir UART/CLI task'ı (telemetri basımı ve komut ayrıştırma
aynı task'ta ya da ayrı task'larda olabilir — Serbest Tasarım Alanı'na bak).

**R2.** Bir task, PS I2C0 üzerinden PCA9544A mux'ı (U23, adres 0x75) kanal
0'a alıp en az iki INA226 güç monitörünü periyodik olarak okumalı:
**VCCINT (0x40)** ve **VCC1V8 (0x42)** — dilersen `_arastirma.md` §4'teki
başka bir rayı da ekleyebilirsin.

**R3.** Okunan değer, INA226 Bus Voltage yazmacından (offset 0x02, LSB
1.25 mV) mV cinsinden bus gerilimine çevrilmeli.

**R4.** LED gösterge task'ı en az iki seviyeli çalışmalı:
- **Temel seviye** (herkeste zorunlu): yalnızca DS50 (MIO23) ile durum
  kodlama — örn. sabit yanma = sağlıklı, yavaş yanıp sönme = uyarı, hızlı
  yanıp sönme = hata.
- **Gelişmiş seviye** (Görev 7'nin bitstream'i elindeyse): PL'deki 8 LED'i
  (AXI GPIO üzerinden) bir bar-graph gibi kullanarak ölçüm seviyesini ya da
  ek durum bilgisini göster.

**R5.** SW19 butonu (MIO22, GIC IRQ 48) interrupt tabanlı çalışmalı; her
basışta gösterge/telemetri modu değişmeli (örn. "VCCINT görünümü" ↔
"VCC1V8 görünümü" ↔ "genel özet"), yazılım debounce'lu.

**R6.** UART0 üzerinden periyodik olarak bir telemetri satırı basılmalı
(en azından tick/zaman bilgisi + o anki mod + ilgili ölçüm değerleri).

**R7.** UART'ta satır tamponlamalı (line-buffered) bir mini komut satırı
(CLI) çalışmalı ve en az şu komutları desteklemeli: `status` (anlık ölçüm ve
mod özetini basar), `led on` / `led off` (gösterge task'ını
durdurur/başlatır), `rate <ms>` (ölçüm/telemetri periyodunu değiştirir).
Tanınmayan komutta anlamlı bir hata mesajı basılmalı.

**R8.** `rate <ms>` komutu çalışma zamanında etkili olmalı ve makul bir
aralıkla sınırlanmalı (örn. 100–5000 ms); sınır dışı değerde komut
reddedilip kullanıcıya bildirilmeli.

**R9.** Task'lar arası veri paylaşımı FreeRTOS senkronizasyon nesneleriyle
(queue, semaphore, mutex) yapılmalı; paylaşılan bir değişkene birden fazla
task'ın kilitsiz, doğrudan erişmesi (race condition riski taşıyan tasarım)
kabul edilmez.

**R10.** Sistem en az 5 dakika kesintisiz çalışabilmeli — çökme, kilitlenme
ya da stack taşması olmadan. `configCHECK_FOR_STACK_OVERFLOW` açık
tutulmalı ve task stack boyutları bilinçli seçilmeli (Bölüm 6 ve Bölüm 10'un
öğrettiği disiplinle).

## Kabul Kriterleri

Demoda aşağıdakilerin her biri tek tek, gözlem yoluyla gösterilebilmeli:

- Kart açılınca UART'ta bir karşılama mesajı ve kısa süre içinde ilk
  telemetri satırı görünüyor.
- `status` komutu anlık ölçüm değerlerini ve o anki modu doğru basıyor.
- `led on` / `led off` komutları LED göstergeyi gözle görülür şekilde
  durdurup yeniden başlatıyor.
- `rate 200` sonrası telemetri satırlarının sıklığı gözle görülür şekilde
  artıyor; `rate 2000` ile belirgin biçimde azalıyor.
- SW19'a basınca mod anında değişiyor — ana döngü/task başka bir işle meşgul
  olsa bile buton tepkisi gecikmiyor (interrupt'ın polling'e üstünlüğü,
  Bölüm 7'nin sözünü tuttuğu yer).
- INA226'dan okunan VCCINT ve VCC1V8 değerleri mühendislik açısından makul
  aralıkta (nominal değerin kabaca ±%10'u civarında).
- Sistem demo süresince (en az 10 dakika) çökmeden, donmadan çalışıyor.

## Serbest Tasarım Alanı

Buraya kadarki her gereksinim *ne* yapman gerektiğini söyledi, *nasıl*
yapacağını değil. Kaç task kullanacağın, queue'ları nasıl adlandıracağın,
mod değişimini hangi FreeRTOS nesnesiyle taşıyacağın, CLI ayrıştırıcısını
nasıl yazacağın — hepsi sana ait. Aşağıdaki şema, olası bir mimariyi
gösteriyor; **bir öneridir, kopyalamak zorunda değilsin**. Üç task ile de,
beş task ile de bu gereksinimleri karşılayabilirsin; önemli olan
R9'un istediği temiz senkronizasyon.

{{svg:sema-25-mezuniyet-mimari.svg|Şekil 25 — Mezuniyet görevi öneri mimarisi: FreeRTOS task'ları, queue'lar, ISR/semaphore mod geçişi ve donanım bağlantıları}}

Görev 7'nin bitstream'i elinde değilse ya da PL LED bar'ını kurmaya vaktin
kalmadıysa, R4'ün temel seviyesi (yalnızca DS50) tek başına yeterli bir
teslimdir — gelişmiş seviye bonus, zorunluluk değil. Ölçüm rayı sayısını
artırmak, üçüncü bir CLI komutu eklemek (örn. `help`) gibi ek dokunuşlar da
serbest alanın parçası; gereksinimlerin *üstüne* çıkmak her zaman kabul
edilir, *altında* kalmak değil.

## Teslim

İki parça teslim edeceksin:

1. **Kısa bir README** (`labs/`teki diğer lab'lardaki gibi bir dosya
   düşün — ama bu seferki senin kendi yazdığın). İçermesi gerekenler:
   - Projenin amacı ve kısa mimari özeti (kaç task, hangi queue/semaphore).
   - Donanım/yazılım gereksinimleri (Vitis sürümü, gerekli .xsa/bitstream
     varsa hangisi).
   - Nasıl derlenir ve karta yüklenir (Vitis proje tipi, adımlar).
   - CLI komut listesi ve beklenen çıktı örneği.
   - Bilinen sınırlamalar ("şunu yapmadım çünkü..." dürüstlüğü burada
     değerlidir; Bölüm 12'nin öğrettiği gibi).
2. **Ekip önünde 10 dakikalık demo.** Kabul kriterlerini sırayla göster;
   sorulara canlı cevap vermeye hazır ol. Bu, gerçek bir iş ortamında
   yapacağın "bitti" demonun provasıdır.

## İpuçları

Çözüm kodu vermiyoruz — bu görevin bütün amacı kendi tasarımını kurman. Ama
üç mimari tuzağa düşmemen için üç yönlendirme:

- **UART'ı tek bir task'a ver.** Hem telemetri basımı (TX) hem CLI okuma
  (RX) aynı fiziksel çevre birimini paylaşıyor; iki farklı task aynı anda
  `XUartPs_Send` çağırırsa çıktı karışabilir. RX tarafı için ayrı bir kesme
  altyapısı kurmaya gerek yok — küçük bir gecikmeyle dönen bir
  `XUartPs_Recv` **polling** task'ı, karakterleri satır tamponuna
  biriktirip `\r`/`\n` gördüğünde komutu ayrıştırması için yeterli ve bu
  ölçekte makul bir tasarımdır.
- **Ölçüm toplama, görselleştirme ve CLI'ı queue'larla ayır.** Ölçüm
  task'ının INA226'dan okuduğu değer başka task'lara doğrudan paylaşılan bir
  global değişkenle değil, bir queue (ya da en azından mutex'li bir paylaşım
  yapısı) üzerinden gitmeli. Aynı şekilde CLI'nin ayrıştırdığı komutlar
  (`led on`, `rate <ms>`) ilgili task'a bir queue mesajı olarak ulaşmalı —
  bu, R9'un istediği "kilitsiz paylaşım yok" kuralının doğal sonucu.
- **Mod değişimini semaphore ya da event ile taşı, ISR içinde işleme.**
  SW19 ISR'i kısa tutulmalı (Bölüm 7'nin kuralı burada da geçerli): ISR
  yalnızca bir binary semaphore'u `FromISR` API'siyle verir, mod değiştirme
  mantığının kendisi (hangi ekrana geçileceğine karar vermek, LED desenini
  güncellemek) o semaphore'u bekleyen bir task içinde çalışır.

:::gorev no=mezuniyet zorluk=3 baslik="Kart Sağlık Monitörü" kisa="Kart Sağlık Monitörü"
[Hedef]
FreeRTOS üzerinde; I2C'den güç ölçümü toplayan, LED'lerde durum gösteren, SW19
kesmesiyle mod değiştiren ve UART'ta hem periyodik telemetri hem mini bir CLI
sunan bağımsız bir "Kart Sağlık Monitörü" uygulamasını tasarlayıp çalışır hale
getirmek.
[Ön koşul]
Görev 0 – Görev 10 tamamlanmış olmalı: I2C okuma, interrupt kurma, FreeRTOS
task/queue/semaphore ve (varsa) AXI GPIO becerilerinin hepsi burada birleşiyor.
[Gereksinimler]
- En az 3 FreeRTOS task'ı: ölçüm toplama, LED gösterge, UART/CLI (R1, R9).
- INA226'dan VCCINT (0x40) + VCC1V8 (0x42) periyodik okuma, mV'a çevirme
  (R2, R3).
- İki seviyeli LED gösterge: DS50 temel + PL LED bar gelişmiş, opsiyonel
  (R4).
- SW19 interrupt ile mod değişimi (R5).
- UART'ta periyodik telemetri + `status` / `led on` / `led off` /
  `rate <ms>` mini CLI (R6, R7, R8).
- 5 dakika kesintisiz, senkronize (kilitsiz paylaşım yok) çalışma (R9, R10).

Tam gereksinim listesi (R1–R10) ve kabul kriterleri için bu bölümün üst
kısmına bak.
[Kabul kriterleri]
- Açılışta UART karşılaması + ilk telemetri satırı.
- `status`, `led on`, `led off`, `rate <ms>` komutları beklendiği gibi
  çalışıyor.
- SW19 anında mod değiştiriyor (sistem meşgulken bile).
- VCCINT/VCC1V8 okumaları makul aralıkta.
- Sistem 10 dakikalık demo boyunca çökmeden çalışıyor.
[Teslim]
Kısa README (amaç, mimari özeti, derleme/yükleme adımları, CLI komut
listesi, bilinen sınırlamalar) + ekip önünde 10 dakikalık canlı demo.
[Kendini sına]
- Mod değişimini ISR içinde doğrudan yapmak yerine neden bir semaphore'a
  devrettin? Doğrudan yapsaydın hangi görev(ler) risk altında kalırdı?
- `rate <ms>` değerini paylaşılan bir global değişkende tutup queue
  kullanmasaydın, hangi senaryoda yarış durumu (race condition) oluşurdu?
- UART çıktısını iki ayrı task'tan (biri telemetri, biri CLI yanıtı) doğrudan
  bastırsaydın ne görürdün? Bunu nasıl önledin?
[Takıldıysan]
::ipucu İpucu 1 — Mimariyi kodlamadan önce kağıda dök
Klavyeye dokunmadan önce task'larını, aralarındaki queue/semaphore'ları ve
her birinin hangi donanımı kullandığını bir kutu-ok şeması olarak çiz (Şekil
25'e bakmadan önce kendi versiyonunu dene). Kağıt üzerinde "bu veri nereden
nereye gidiyor" sorusuna net cevap veremiyorsan, kodda da veremezsin.
::/
::ipucu İpucu 2 — Küçükten başla, katman katman büyüt
Önce yalnızca iki task ile başla: ölçüm toplama + UART'a basma (queue ile
bağlı). Bu ikisi kararlı çalıştıktan sonra LED gösterge task'ını, ardından
SW19 kesmesini, en son CLI ayrıştırıcısını ekle. Her katmanı eklerken bir
önceki katmanın hâlâ çalıştığını doğrula — Bölüm 12'nin "küçük adımlarla
ilerle" öğüdü hiçbir yerde burada olduğu kadar değerli değil.
::/
:::

Kartı gördün, gereksinimleri okudun, şemayı inceledin. Şimdi klavye senin.

---

Buraya kadar geldiysen: tebrikler. İlk gün masana oturduğunda gözünü korkutan
kart artık senin elinde — register'larını okudun, kesmelerini kurdun,
protokollerini konuştun, kendi FreeRTOS uygulamanı yazdın. Bu doküman burada
bitiyor ama senin öğrenmen bitmiyor; sırada ekipteki **ilk gerçek görevin**
var, ve muhtemelen bu sefer kimse sana bir görev kartı hazırlamayacak — onu
kendi başına parçalayacaksın. İhtiyacın olduğunda yanına şu iki kaynağı al:
bu dokümanın **Ek A — Hızlı Referans**'ı (masana asabileceğin bir özet) ve
Bölüm 13'te tanıştığın **saha kılavuzları** — Bellek Mimarisi, Ethernet, RF
Örnekleme — bu yolculuğun sana bilerek bırakmadığı derinlikler için oradalar.

İyi çalışmalar. Ekibe hoş geldin.
