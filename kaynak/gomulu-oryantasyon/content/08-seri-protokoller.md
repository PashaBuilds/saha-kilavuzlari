# Bölüm 8 — Seri Protokoller: UART, SPI, I2C

Kesmeyle konuşmayı öğrendin — CPU artık olayları anında fark ediyor. Ama o
olaylar nereden geliyor? Çoğu zaman, kartın üzerindeki başka bir çipten,
birkaç telin üzerinden akan bitlerden. Bu bölümde üç seri protokolün tel
seviyesinde nasıl çalıştığını göreceksin: **UART**, **SPI**, **I2C**. Üçü de
"1 ve 0'ı bir telden geçir" fikrinin farklı çözümleri; farkları anlamak,
hangi çipi hangi protokolle konuşturacağını bilmek demek.

## Ortak payda: voltaj, zaman, anlaşma

Her seri protokol aynı özde: bir hat, belirli anlarda yüksek (1) ya da düşük
(0) voltaja çekilir; alıcı tarafın bu voltajı doğru anda örneklemesi
gerekir. Fark, "doğru anı" kimin belirlediğinde: UART'ta iki taraf da
kendi saatine güvenir ve önceden anlaşır (**asenkron**); SPI ve I2C'de
tellerden biri doğrudan saat sinyalidir, herkes ona bakar (**senkron**).
Bu tek fark, üç protokolün neredeyse tüm davranış farkını açıklıyor.

## UART: iki tel, saat yok, sözlü anlaşma var

UART'ı Görev 2'den beri kullanıyorsun — terminaline yazı bastığın seri
port tam olarak bu. Şimdi tel seviyesine iniyoruz: o portun altında,
fiziksel telde gerçekte ne oluyor? Hat boşta **yüksektedir (idle-high)**. Bir bayt
göndermek şöyle işler: **start biti** (hat bir bit süresi boyunca düşer),
ardından **veri bitleri** (genelde 8, **LSB önce**), isteğe bağlı bir
**parity (eşlik) biti**, en sonda **stop biti** (hat tekrar yükselir). Bizim
kullandığımız ayar **115200-8N1**: 115200 baud, 8 veri biti, parity yok
(None), 1 stop biti.

{{svg:sema-16-uart-dalga.svg|Şekil 16 — UART kare dalga: start, 8 veri biti (LSB önce, örnek bayt 'A' = 0x41), stop; bit süresi 1/baud, 115200 örneği.}}

**Baud rate** aslında "saniyede kaç bit" demek; iki tarafın da aynı sayıyı
bilmesi şart çünkü paylaşılan bir saat yok — alıcı, start bitini gördüğü
anda kendi iç saatiyle "şimdi tam ortadayım" diyerek örnekleme yapar. Baud
rate'ler uyuşmazsa hat elektriksel olarak sorunsuz görünür ama alıcı yanlış
anlarda örnekler, terminalde anlamsız karakterler ("çöp") görürsün — bu,
"kablo doğru ama ayar yanlış" hatalarının en klasik belirtisidir. UART
**noktadan noktaya (point-to-point)** çalışır: bir TX her zaman tek bir
RX'e bağlanır, adresleme kavramı yoktur.

:::saha-notu Kanonik özet — UART
- **Tel sayısı:** 2 (TX, RX) + ortak toprak.
- **Zamanlama:** asenkron — paylaşılan saat yok, iki taraf da baud rate
  üzerinde önceden anlaşır.
- **Adresleme:** yok — noktadan noktaya (point-to-point), bir TX hep aynı
  RX'e bağlanır.
- **Tipik hız:** kilobit/saniye mertebesi (bizim ayarımız 115200 baud).
- **Ne zaman seç:** basit, az cihazlı, hızın kritik olmadığı bir seri
  hat/konsol istediğinde.
:::

## SPI: hız için dört tel

SPI (Serial Peripheral Interface) senkron bir protokol — **SCLK** (saat),
**MOSI** (Master Out Slave In), **MISO** (Master Out Slave In'in tersi:
Master In Slave Out) ve her slave için ayrı bir **CS** (Chip Select, aktif
düşük) hattı taşır. Saat master'da üretilir; her saat darbesinde bir bit
kayar — hem MOSI hem MISO **aynı anda** aktığı için SPI doğası gereği
**tam çift yönlü (full-duplex)**'tür. Adresleme yok; "kiminle konuştuğunu"
CS hattını o slave için düşürerek belirlersin.

{{svg:sema-17-spi-dalga.svg|Şekil 17 — SPI dalga şekli: CS, SCLK, MOSI, MISO ve örnekleme kenarları; altta mode 0-3 için CPOL/CPHA farkları.}}

Saatin ayrıntısında dört varyant var — **mode 0-3** — iki parametrenin
kombinasyonu: **CPOL** (Clock Polarity — hat boştayken saat yüksek mi
düşük mü) ve **CPHA** (Clock Phase — veri önder kenarda mı izleyen kenarda
mı örnekleniyor). İki çip farklı mode bekliyorsa veri akar ama anlamsızdır
— bit kayması olur, her şey bir konum ötelenmiş görünür. Datasheet'te
"SPI Mode" ya da "CPOL/CPHA" satırını bulmadan bir SPI çipine bağlanmak,
tahminen doğru moddaki bir kilide yanlış anahtarla dokunmaya benzer. SPI
tipik olarak hızlı ADC/DAC'lerde, flash bellekte ve ekranlarda kullanılır
— saat frekansı onlarca MHz'e çıkabilir, UART'ın çok üzerinde.

:::saha-notu Kanonik özet — SPI
- **Tel sayısı:** 4 (SCLK, MOSI, MISO) + her slave için ayrı bir CS hattı.
- **Zamanlama:** senkron — saat master'da üretilir, herkes ona bakar;
  MOSI/MISO aynı anda aktığı için full-duplex.
- **Adresleme:** yok — "kiminle konuştuğunu" o slave'in CS hattını
  düşürerek belirlersin.
- **Tipik hız:** onlarca MHz'e çıkabilir — üçü içindeki en hızlısı.
- **Ne zaman seç:** hız kritikse (hızlı ADC/DAC, flash bellek, ekran) ve
  slave başına bir pin harcamak sorun değilse.
:::

## I2C: iki telle koca bir ağaç

I2C (Inter-Integrated Circuit) yalnızca iki tel kullanır: **SDA** (veri) ve
**SCL** (saat) — ama bu iki tel üzerinde onlarca çip aynı anda yaşayabilir.
Bunu mümkün kılan şey **open-drain** çıkış yapısı: her çip hattı yalnızca
**aşağı çekebilir**, yukarı itemez. Hattı yukarı taşıyan şey harici bir
**pull-up direnci**dir. Kimse çekmezse direnç hattı yükseğe çeker; herhangi
bir çip çekerse hat düşük olur — bu "wired-AND" davranışı, iki çipin aynı
anda konuşup hattı fiziksel olarak çatışmaya sokmasını imkânsız kılar.

{{svg:sema-18-i2c-dalga.svg|Şekil 18 — I2C dalga şekli: START koşulu, 7-bit adres + R/W, slave ACK, bir veri baytı, STOP; altta open-drain hat ve pull-up direncinin sezgisi.}}

Aynı open-drain mantığı SCL için de geçerlidir; bu sayede bir slave, veriyi
hazırlamak için zamana ihtiyaç duyduğunda saati kendisi aşağıda tutabilir
(**clock stretching** — saat gerdirme). Master bunu "slave meşgul, bekle"
sinyali olarak okur ve SCL'nin gerçekten yükselmesini bekler. Bu, I2C'nin
basit iki telle nasıl bu kadar esnek davranabildiğinin küçük ama zarif bir
detayıdır.

Bir I2C işlemi sırayla şöyle akar: **START** (SCL yüksekken SDA düşer —
diğer her iki hattın da aynı anda değiştiği tek an budur, bu yüzden
tanınabilir), **7-bit adres + R/W biti**, alıcının **ACK**'i (SDA'yı bir
bit süresi düşük tutması — "seni duydum"), sonra veri baytları (her biri
kendi ACK'iyle), en sonda **STOP** (SCL yüksekken SDA yükselir). Standart
modda 100 kHz, fast-mode'da 400 kHz saat hızı tipiktir.

7-bit adresleme demek, aynı I2C hattında en fazla 128 farklı adres var
demek — ve pratikte birçok çipin fabrika adresi sabit ya da sadece birkaç
pinle değiştirilebilir. Aynı modelden birden fazla çip (örn. kartta 14
tane INA226 güç monitörü!) aynı hatta olamaz; adresleri çakışır. Çözüm:
**I2C mux/switch** çipleri. Bunlar kendileri bir I2C adresinde yaşayan ama
"arkalarında" birkaç ayrı I2C dalı barındıran anahtarlardır — sen önce
mux'a "şimdi şu dalı bağla" dersin, sonra o dal üzerindeki çipe normal
şekilde konuşursun. ZCU111'de bu tam olarak gerçekleşiyor: **PS I2C0**
(MIO14-15), bir **PCA9544A** (4 kanallı mux, adres 0x75) üzerinden karttaki
INA226 güç monitörlerine dallanıyor; **PS I2C1** (MIO16-17) ise iki adet
**TCA9548A** (8 kanallı switch, 0x74 ve 0x75) üzerinden EEPROM'a, saat
üreteçlerine, SYSMON'a, DDR SPD'ye ve SFP modüllerine dallanıyor. Tek bir
I2C denetleyicisinden koca bir ağaç.

:::saha-notu Kanonik özet — I2C
- **Tel sayısı:** 2 (SDA, SCL) — open-drain çıkış + harici pull-up direnç.
- **Zamanlama:** senkron — saat SCL üzerinden taşınır; slave gerekirse
  clock stretching ile saati kendisi gerdirebilir.
- **Adresleme:** var — 7-bit adres + R/W biti; aynı hatta onlarca çip,
  mux/switch ile dallanan koca bir ağaç kurulabilir.
- **Tipik hız:** standart modda 100 kHz, fast-mode'da 400 kHz.
- **Ne zaman seç:** çok sayıda düşük hızlı çipi az pinle (yalnızca 2 tel)
  yönetmek istediğinde.
:::

{{svg:sema-19-protokol-karsilastirma.svg|Şekil 19 — UART, SPI ve I2C karşılaştırması: tel sayısı, hız sınıfı, topoloji, senkron olup olmadığı ve tipik kullanım.}}

Üçünü yan yana koyduğunda seçim netleşir: az tel ve basitlik istiyorsan
UART, ham hız istiyorsan SPI, çok sayıda çipi az pinle yönetmek istiyorsan
I2C. Gerçek kartlarda genelde üçü birden, farklı çipler için, aynı anda
kullanılır — tıpkı ZCU111'de olduğu gibi.

:::saha-notu Yazılımcı da prob tutar
Bir I2C işlemi "ACK gelmiyor" diye başarısız olduğunda, kaynak kodunu
okumak yeterli değildir — telin üzerinde gerçekte ne olduğunu görmen
gerekir. Bizim ekipte bir lojik analizör ya da osiloskobu SDA/SCL'ye
takıp START'ın gerçekten oluştuğunu, adresin doğru gönderildiğini,
ACK'in gelip gelmediğini gözle görmek yazılımcının da işidir — bu sadece
donanımcının aleti değil. Bir dalga şeklini elle okuyabilmek (bu bölümdeki
şemaları tanımak) gerçek bir hattaki dalgayı okumaya doğrudan taşınır;
ilk seferinde tuhaf gelir, üçüncü seferinde refleks olur.
:::

Teori burada bitiyor; şimdi kartındaki gerçek bir I2C ağacına gireceksin —
mux'tan geçip gerçek bir çipten gerçek bir ölçüm okuyacaksın.

:::gorev no=6 zorluk=3 baslik="I2C ile Gerçek Bir Çiple Konuş" kisa="I2C Ölçüm"
[Hedef]
PS I2C0 üzerinden PCA9544A mux'ını kanal 0'a yönlendirip bir INA226 güç
monitöründen VCCINT bus geriliminin gerçek değerini okuyup UART'a bas.

[Ön koşul]
Bölüm 8 okundu; Görev 2'nin `uart_ps` modülü elinde; Görev 4-5'ten register
seviyesinde donanımla konuşma alışkanlığın var.

[Adımlar]
**Aşama 1 — Bağlantıyı doğrula.** Bu aşamanın sonunda elinde henüz hiçbir
ölçüm yok; tek kanıtladığın şey hattın gerçekten çalıştığı — mux doğru
kanalı seçti mi, INA226 doğru adreste yanıt veriyor mu. Adım 1-5'in hepsi
az sonra tek bir fonksiyonda, `ina226Init()`'te toplanacak.

1. **I2C ağacını anla:** PS I2C0 (**MIO14-15**) → **PCA9544A mux, U23,
   I2C adresi 0x75** → kanal 0 → **INA226, I2C adresi 0x40** (VCCINT
   rayı, 0.85 V nominal). Bu görevde "datasheet okuma vaftizi"nden
   geçeceksin: her adımda kod yazmadan önce ilgili register tablosunu
   oku.
2. `XIicPs` nesnesini başlat (`XIicPs_LookupConfig` + `XIicPs_CfgInitialize`)
   ve saat hızını **100 kHz**'e ayarla: `XIicPs_SetSClk(&G_sIic, 100000)`.
3. **Mux'a kanal-0 seçim baytını yaz.** PCA9544A'nın 8-bit kontrol
   yazmacında bit 2 "enable", bit 1-0 kanal numarasıdır — kanal 0 için
   yazılacak bayt datasheet'ten tek bir doğru değer çıkarır. Kendin
   doğrulamadan `lab06-i2c` çözümüne bakma; datasheet'i (PCA9544A,
   §8.6 "Register Map") bulup Table 8-1'i oku, kanal-0 komutunu kendi
   çıkarımınla yaz, sonra çözümle karşılaştır.
4. `XIicPs_MasterSendPolled(&G_sIic, kontrolBaytı, 1, 0x75)` ile mux'a
   yaz — ardından bir **STOP** oluşması gerektiğini unutma (bu API
   çağrısı zaten tam bir yazma işlemi olduğu için stop'u kendisi üretir).
5. **INA226'nın kimliğini doğrula:** register pointer olarak `0xFE`
   (Manufacturer ID) yaz (`XIicPs_MasterSendPolled`, 1 bayt, adres 0x40),
   sonra 2 bayt oku (`XIicPs_MasterRecvPolled`). Gelen iki baytı big-endian
   sırayla (MSB önce) birleştir; sonuç **0x5449** ("TI" ASCII) olmalı. Eşleşmezse
   devam etme — mux kanalı, adres ya da kablolamada bir sorun var demektir.
   `ina226Init()` tam olarak bu beş adımı yapar: init + mux seçimi +
   kimlik doğrulaması, dönüşü 0 (başarı) ya da 0-dışı (hata). Terminalde
   kimliğin doğrulandığını görmeden Aşama 2'ye geçme.

**Aşama 2 — Ölç ve ölçekle.** Hat kanıtlandı; şimdi üstüne gerçek ölçümü
ekliyorsun.

6. **Bus Voltage register'ını (0x02)** aynı pointer-yaz + oku deseniyle
   çek; ham 16-bit değeri **LSB = 1.25 mV** ile çarpıp milivolt'a çevir.
   Bu mantığı `ina226ReadBusVoltageMv()` fonksiyonuna yaz — dönüşü yine
   0 (başarı) / 0-dışı (hata), ölçümün kendisi bir çıkış parametresiyle
   (`unsigned int*`) gelsin. Sonucu `uartSendString()` ile
   `"VCCINT = NNN mV"` biçiminde bas; bu döngüyü saniyede bir tekrar et.

[Başarı kriteri]
Terminalde saniyede bir, VCCINT için yaklaşık 850 mV civarında (kartın
gerçek yüküne göre birkaç mV oynayabilir) bir değer akıyor.

[Kendini sına]
- ID register'ını (0xFE) neden bus geriliminden ÖNCE okuduk — bu adımı
  atlasaydık ve mux/adres yanlış olsaydı hatayı nerede, nasıl fark
  ederdik?
- Mux olmasaydı ve kartta iki INA226 aynı 0x40 adresinde olsaydı, ikisine
  de aynı anda yazma isteği gönderirsen elektriksel olarak ne olurdu?
- SDA/SCL hattında pull-up direnci olmasaydı hat hangi seviyede kalırdı
  (open-drain sezgisini hatırla) — I2C hiç çalışır mıydı?

[Takıldıysan]
::ipucu İpucu 1 — Mux adımı atlanmış olabilir
`XIicPs_MasterSendPolled` ile INA226'ya (0x40) hiçbir şey yazamıyor ya da
hep zaman aşımına uğruyorsan, en olası sebep mux'a kanal seçimini hiç
yapmamış olman ya da yanlış kontrol baytı göndermiş olmandır — güç
açılışında (POR) PCA9544A hiçbir kanalı seçili tutmaz, her seferinde
açıkça seçmen gerekir.
::/
::ipucu İpucu 2 — "Register pointer" kavramını netleştir
INA226 (ve çoğu I2C çipi) çok yazmaçlı bir cihazdır; hangi yazmacı
okumak istediğini önce tek baytlık bir "pointer" yazarak söylersin, ardından
ayrı bir okuma işlemiyle o yazmacın içeriğini alırsın. Yani her okuma
aslında iki I2C işlemidir: kısa bir yazma (pointer) + bir okuma (veri).
::/
::ipucu İpucu 3 — mV çevrimi tutmuyor
Bus Voltage register'ının LSB'si **1.25 mV**'dir — ham 16-bit değeri
`(unsigned int)usRaw * 1250 / 1000` gibi tam sayı aritmetiğiyle çarp (kayan nokta
gerekmez); işaretsiz bir büyüklük olduğu için negatif değer beklemene
gerek yok.
::/
::cozum Tam çözüm — lab06-i2c
`ina226.c/.h` mux seçimini ve register okuma desenini kapsar; `main.c`
saniyede bir ölçümü UART'a basar.
{{kod:lab06-i2c/src/ina226.c}}
{{kod:lab06-i2c/src/main.c}}
::/
:::
