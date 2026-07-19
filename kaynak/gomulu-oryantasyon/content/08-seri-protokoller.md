# Bölüm 8 — Seri Protokoller: UART, SPI, I2C

Kesmelerle çalışmayı öğrendin — CPU artık olayları anında fark ediyor.
Peki o olaylar nereden geliyor? Çoğu zaman karttaki başka bir çipten, az
sayıda tel üzerinde bit bit taşınarak. Bu bölüm üç seri protokolün tel
seviyesinde nasıl işlediğini inceler: **UART**, **SPI** ve **I2C**. Üçü
de aynı fikrin — 1'leri ve 0'ları bir tel üzerinden iletmenin — farklı
çözümleridir; farklarını anlamak, hangi çiple hangi protokolün
kullanılacağını bilmek demektir.

## Ortak Zemin: Gerilim, Zamanlama, Anlaşma

Özünde bütün seri protokoller aynı şekilde çalışır: bir hat belirli
anlarda yüksek (1) ya da düşük (0) gerilime sürülür; alıcı taraf o
gerilimi doğru anda örneklemek zorundadır. Fark, "doğru an"ı kimin
belirlediğindedir: UART'ta iki taraf kendi saatine güvenir ve
zamanlamada önceden anlaşır (**asenkron**); SPI ile I2C'de tellerden
biri saat sinyalini doğrudan taşır ve herkes ona bakar (**senkron**).
Üç protokol arasındaki davranış farklarının neredeyse tamamı bu tek
ayrımdan doğar.

## UART: İki Tel, Saat Yok, Önceden Anlaşma

UART'ı Görev 2'den beri kullanıyorsun — terminalde metin bastığın seri
port tam olarak bu. Bu kısım tel seviyesine iner: o portun altındaki
fiziksel telde gerçekte ne oluyor? Hat, kullanılmadığında
**idle-high**'dır (boşta yüksek). Bir bayt göndermek şöyle ilerler: bir
**start biti** (hat bir bit süresi boyunca düşüğe iner), ardından
**veri bitleri** (tipik olarak 8, **LSB first** — önce en düşük anlamlı
bit), isteğe bağlı bir **parity biti** (eşlik) ve son olarak bir **stop
biti** (hat yeniden yükseğe döner). Bu dokümanda kullanılan
konfigürasyon **115200-8N1**: 115200 baud, 8 veri biti, parity yok
(None), 1 stop biti.

{{svg:sema-16-uart-dalga.svg|Şekil 16 — UART kare dalgası: start biti, 8 veri biti (LSB first, örnek bayt 'A' = 0x41), stop biti; bit süresi = 1/baud, 115200 örneği.}}

**Baud rate**, "saniyedeki bit sayısı" demektir; ortak saat olmadığı
için iki taraf aynı değerde anlaşmak zorundadır — alıcı, start bitini
yakaladığında kendi iç saatiyle "şimdi bit ortasındayım" hesabını yapar
ve öyle örnekler. Baud'lar uyuşmazsa hat elektriksel olarak sağlam
görünür ama alıcı yanlış anlarda örnekler; terminale anlamsız
karakterler ("garbage") düşer — "kablolama doğru ama konfigürasyon
yanlış"ın klasik belirtisi budur. UART **noktadan noktaya** çalışır:
bir TX hattı her zaman tek bir RX hattına bağlanır; adresleme kavramı
yoktur.

:::saha-notu Hızlı Özet — UART
- **Tel sayısı:** 2 (TX, RX) + ortak toprak.
- **Zamanlama:** asenkron — ortak saat yok; iki taraf baud rate'te
  önceden anlaşır.
- **Adresleme:** yok — noktadan noktaya; bir TX hattı hep aynı RX
  hattına bağlıdır.
- **Tipik hız:** kilobit/saniye mertebesi (kullandığımız konfigürasyon: 115200
  baud).
- **Ne zaman seçilir:** az cihazlı, hızın kritik olmadığı basit seri
  bağlantı ya da konsol için.
:::

## SPI: Hız İçin Dört Tel

SPI (Serial Peripheral Interface); **SCLK** (saat), **MOSI** (Master
Out Slave In), **MISO** (Master In Slave Out, MOSI'nin karşılığı) ve
her slave (yönetilen çip) için ayrı bir **CS** (Chip Select, aktif-düşük) hattı
kullanan senkron bir protokoldür. Saati master (hattı yöneten taraf) üretir; her saat
vuruşunda bir bit kayar — MOSI ile MISO veriyi **aynı anda**
taşıdığından SPI, doğası gereği **full-duplex**'tir (iki yönde
eşzamanlı). Adresleme yoktur; "kiminle konuştuğunu", o slave'in CS
hattını düşüğe çekerek belirlersin.

{{svg:sema-17-spi-dalga.svg|Şekil 17 — SPI dalga şekli: CS, SCLK, MOSI, MISO ve örnekleme kenarları; altta mod 0-3 için CPOL/CPHA farkları.}}

Saatin ayrıntısında dört varyant vardır — **mod 0-3** — iki
parametrenin kombinasyonundan oluşur: **CPOL** (Clock Polarity — saat
boşta yüksek mi, düşük mü) ve **CPHA** (Clock Phase — veri ön kenarda
mı, arka kenarda mı örneklenir). İki çip farklı mod beklerse veri yine
akar ama anlamsızdır — bir bit kayması olur, her şey bir konum
ötelenmiş görünür. Bir SPI çipine, datasheet'inde "SPI Mode" ya da
"CPOL/CPHA" satırını bulmadan bağlanmaya kalkmak, şartnameyi okumadan
sahaya çıkmaktır. SPI tipik olarak hızlı ADC/DAC'lerde, flash bellekte
ve ekranlarda kullanılır — saat frekansı onlarca MHz'e çıkabilir;
UART'ın çok üstünde.

:::saha-notu Hızlı Özet — SPI
- **Tel sayısı:** 3 ortak hat (SCLK, MOSI, MISO) + her slave için ayrı bir CS
  hattı.
- **Zamanlama:** senkron — saati master üretir, herkes ona bakar;
  MOSI/MISO aynı anda taşıdığından full-duplex.
- **Adresleme:** yok — "kiminle konuştuğunu" o slave'in CS hattını
  düşüğe çekerek belirlersin.
- **Tipik hız:** onlarca MHz'e çıkabilir — üçünün en hızlısı.
- **Ne zaman seçilir:** hız kritikse (hızlı ADC/DAC, flash bellek,
  ekran) ve slave başına bir pin ayırmak kabul edilebilirse.
:::

## I2C: İki Tel Üzerinde Büyük Bir Ağaç

I2C (Inter-Integrated Circuit) yalnızca iki tel kullanır — **SDA**
(veri) ve **SCL** (saat) — ama bu iki telin üzerinde onlarca çip aynı
anda var olabilir. Bunu mümkün kılan, **open-drain** çıkış yapısıdır:
her çip hattı yalnızca **düşüğe çekebilir**, asla yükseğe süremez.
Hattı yükseğe taşıyan, harici bir **pull-up direncidir**. Hiçbir çip
çekmiyorsa direnç hattı yükseğe çeker; herhangi bir çip çekiyorsa hat
düşer — bu "wired-AND" davranışı, aynı anda konuşan iki çipin hattı
elektriksel çatışmaya sokmasını fiziksel olarak imkânsız kılar.

{{svg:sema-18-i2c-dalga.svg|Şekil 18 — I2C dalga şekli: START koşulu, 7 bit adres + R/W, slave ACK'i, bir veri baytı, STOP; altta open-drain hat ve pull-up direncinin sezgisi.}}

Aynı open-drain mantığı SCL için de geçerlidir; verisini hazırlamak
için zamana ihtiyaç duyan bir slave, saati kendisi düşükte tutabilir
(**clock stretching**). Master bunu "slave meşgul, bekle" sinyali
olarak okur ve SCL gerçekten yükselene kadar bekler. I2C'nin iki basit
telle bu kadar esneklik sağlamasının arkasındaki küçük ama zarif
ayrıntılardan biri budur.

Bir I2C işlemi şöyle ilerler: **START** (SCL yüksekken SDA düşer — iki
hattın birlikte değiştiği tek an; onu tanınır kılan da budur), **7 bit
adres artı R/W biti**, alıcının **ACK'i** (SDA'yı bir bit süresi
düşükte tutmak — "seni duydum"), ardından veri baytları (her biri kendi
ACK'iyle) ve son olarak **STOP** (SCL yüksekken SDA yükselir). Standart
modda 100 kHz, fast modda 400 kHz saat hızı tipiktir.

7 bit adres, bir I2C hattında en fazla 128 ayrı adres demektir —
pratikte çoğu çipin fabrika adresi ya sabittir ya da yalnızca birkaç
pinle ayarlanabilir. Aynı modelden birden çok çip (örneğin bu karttaki
14 adet INA226 güç monitörü) tek bir hattı paylaşamaz; adresleri
çakışır. Çözüm, **I2C mux/switch** çipidir. Bu cihazlar kendileri bir
I2C adresinde oturur ama "arkalarında" birkaç ayrı I2C dalı barındırır
— önce mux'a "şimdi şu dalı bağla" dersin, sonra o daldaki çiple her
zamanki gibi konuşursun. ZCU111'de tam olarak böyle çalışır: **PS
I2C0** (MIO14-15), bir **PCA9544A** (4 kanallı mux, adres 0x75)
üzerinden kartın INA226 güç monitörlerine dallanır; **PS I2C1**
(MIO16-17), iki **TCA9548A** (8 kanallı switch, 0x74 ve 0x75) üzerinden
EEPROM'a, saat üreteçlerine, SYSMON'a, DDR SPD'ye ve SFP modüllerine
dallanır. Tek I2C denetleyicisinden geniş bir ağaç.

:::saha-notu Hızlı Özet — I2C
- **Tel sayısı:** 2 (SDA, SCL) — open-drain çıkış artı harici pull-up
  direnci.
- **Zamanlama:** senkron — saat SCL üzerinden taşınır; gerekirse slave,
  clock stretching ile saati kendisi uzatabilir.
- **Adresleme:** var — 7 bit adres artı R/W biti; onlarca çip bir hattı
  paylaşabilir, mux/switch cihazlarıyla dallardan büyük bir ağaç
  kurulur.
- **Tipik hız:** standart modda 100 kHz, fast modda 400 kHz.
- **Ne zaman seçilir:** az pinle (yalnızca 2 tel) çok sayıda düşük
  hızlı çipi yönetmen gerektiğinde.
:::

{{svg:sema-19-protokol-karsilastirma.svg|Şekil 19 — UART, SPI ve I2C karşılaştırması: tel sayısı, hız sınıfı, topoloji, senkron olup olmadığı ve tipik kullanım.}}

Üçü yan yana konduğunda seçim netleşir: az tel ve basitlik için UART,
ham hız için SPI, az pinle çok çip yönetmek için I2C. Gerçek kartlarda
üçü de farklı çipler için genellikle aynı anda kullanılır — tıpkı
ZCU111'de olduğu gibi.

:::saha-notu Probu Yazılımcı da Tutar
Bir I2C işlemi "ACK gelmiyor" diye başarısız olduğunda kaynak kodu
okumak yetmez — telde gerçekte ne olduğunu görmen gerekir. Bizim ekipte
SDA/SCL'ye logic analyzer ya da osiloskop bağlayıp START'ın gerçekten
oluştuğunu, adresin doğru gittiğini ve ACK'in gelip gelmediğini gözle
doğrulamak yazılımcının da işidir — yalnızca donanımcının aleti
değildir. Dalga biçimini elle okuyabilme becerisi (bu bölümdeki
şemaları tanımak), gerçek hattaki dalga şeklini okumaya doğrudan
aktarılır; ilk seferinde yabancı gelir, üçüncüsünde refleks olur.
:::

Teori burada bitiyor; şimdi kartındaki gerçek bir I2C ağacına
gireceksin — mux'tan geçip gerçek bir çipten gerçek bir ölçüm
okuyacaksın.

:::gorev no=6 zorluk=3 baslik="I2C ile Gerçek Bir Çiple Konuş" kisa="I2C Ölçüm"
[Hedef]
PS I2C0 üzerinden PCA9544A mux'ı kanal 0'a yönlendir, bir INA226 güç
monitöründen gerçek VCCINT hat gerilimini oku ve UART'a yazdır.

[Ön koşul]
Bölüm 8 okundu; Görev 2'deki `uart_ps` modülün elinde; Görev 4-5'ten
register seviyesinde donanım haberleşmesi alışkanlığın oluştu.

[Adımlar]
**Faz 1 — Bağlantıyı doğrula.** Bu fazın sonunda henüz ölçümün
olmayacak; kanıtladığın tek şey hattın gerçekten çalıştığı — mux'ın
doğru kanalı seçtiği ve INA226'nın doğru adresten yanıt verdiği
olacak. 1-5. adımlar az sonra tek bir fonksiyonda toplanacak:
`ina226Init()`.

1. **I2C ağacını kavra:** PS I2C0 (**MIO14-15**) → **PCA9544A mux,
   U23, I2C adresi 0x75** → kanal 0 → **INA226, I2C adresi 0x40**
   (VCCINT hattı, 0.85 V nominal). Bu görevde datasheet okumaya bir
   giriş yapıyorsun: her adımda kod yazmadan önce ilgili register
   tablosunu oku.
2. `XIicPs` nesnesini başlat (`XIicPs_LookupConfig` +
   `XIicPs_CfgInitialize`) ve saat hızını **100 kHz** yap:
   `XIicPs_SetSClk(&G_sIic, 100000)`.
3. **Mux'a kanal-0 seçim baytını yaz.** PCA9544A'nın 8 bitlik kontrol
   register'ında bit 2 "enable", bit 1-0 kanal numarasıdır — kanal 0
   için yazılacak bayt, datasheet'ten tek bir doğru değere çıkar. Bunu
   kendin doğrulamadan `lab06-i2c` çözümüne bakma; datasheet'i
   (PCA9544A, §8.6 "Register Map") bul, Tablo 8-1'i oku, kanal-0
   komutunu kendin türet, sonra çözümle karşılaştır.
4. Mux'a `XIicPs_MasterSendPolled(&G_sIic, controlByte, 1, 0x75)` ile
   yaz — ve ardından bir **STOP** gerektiğini hatırla (bu API çağrısı
   zaten eksiksiz bir yazma işlemidir; stop'u kendisi üretir).
5. **INA226'nın kimliğini doğrula:** register pointer olarak `0xFE`
   (Manufacturer ID) yaz (`XIicPs_MasterSendPolled`, 1 bayt, adres
   0x40), sonra 2 bayt oku (`XIicPs_MasterRecvPolled`). Dönen iki
   baytı big-endian sırayla (önce MSB) birleştir; sonuç **0x5449**
   olmalı (ASCII'de "TI"). Tutmuyorsa ilerleme — mux kanalında,
   adreste ya da kablolamada sorun var demektir. `ina226Init()` tam
   olarak bu beş adımı yapar: başlatma, mux seçimi ve kimlik
   doğrulama; 0 (başarı) ya da sıfırdan farklı (hata) döndürür.
   Terminalde kimliğin doğrulandığını görmeden Faz 2'ye geçme.

**Faz 2 — Ölç ve ölçekle.** Hat kanıtlandı; şimdi üstüne asıl ölçümü
ekliyorsun.

6. **Bus Voltage register'ını (0x02) oku** — aynı
   pointer-yaz-sonra-oku kalıbıyla; ham 16 bit değeri **LSB = 1.25 mV**
   ile çarpıp milivolta çevir. Bu mantığı `ina226ReadBusVoltageMv()`
   fonksiyonunda gerçekle — yine 0 (başarı) / sıfırdan farklı (hata)
   döndür; ölçümün kendisini çıkış parametresiyle (`unsigned int*`)
   teslim et. Sonucu `uartSendString()` ile `"VCCINT = NNN mV"`
   biçiminde yazdır; bu döngüyü saniyede bir tekrarla.

[Başarı kriteri]
Terminal, VCCINT için saniyede bir, yaklaşık 850 mV civarında bir değer
basar (kartın anlık yüküne göre birkaç mV oynayabilir).

[Kendini sına]
- Bus voltage'dan ÖNCE neden ID register'ını (0xFE) okuduk — bu adımı
  atlasaydık ve mux/adres yanlış olsaydı, hatayı nerede ve nasıl fark
  ederdik?
- Mux olmasaydı ve karttaki iki INA226 aynı 0x40 adresini paylaşsaydı,
  ikisine aynı anda yazma isteği gönderdiğinde elektriksel olarak ne
  olurdu?
- SDA/SCL hattında pull-up direnci olmasaydı hat hangi seviyede
  kalırdı (open-drain sezgisini hatırla) — I2C hiç çalışır mıydı?

[Takıldıysan]
::ipucu İpucu 1 — Mux Adımı Atlanmış Olabilir
`XIicPs_MasterSendPolled` ile INA226'ya (0x40) hiçbir şey yazamıyorsan
ya da sürekli zaman aşımı alıyorsan, en olası neden mux'ta kanal
seçimini hiç yapmamış ya da yanlış kontrol baytı göndermiş olmandır —
power-on reset (POR) sonrasında PCA9544A hiçbir kanalı seçili tutmaz;
her seferinde açıkça seçmek zorundasın.
::/
::ipucu İpucu 2 — "Register Pointer" Kavramını Netleştir
INA226 (çoğu I2C çipi gibi) çok register'lı bir cihazdır; hangi
register'ı okumak istediğini önce tek baytlık bir "pointer" yazarak
belirtir, o register'ın içeriğini ayrı bir okuma işlemiyle alırsın.
Yani her okuma aslında iki I2C işlemidir: kısa bir yazma (pointer) ve
ardından bir okuma (veri).
::/
::ipucu İpucu 3 — mV Dönüşümü Tutmuyor
Bus Voltage register'ının LSB'si **1.25 mV**'dir — ham 16 bit değeri
`(unsigned int)usRaw * 1250 / 1000` gibi tamsayı aritmetiğiyle çarp
(floating point gerekmez); büyüklük işaretsiz olduğundan negatif
değerleri hesaba katman gerekmez.
::/
::cozum Tam Çözüm — lab06-i2c
`ina226.c/.h` mux seçimini ve register okuma kalıbını kapsar; `main.c`
ölçümü saniyede bir UART'a basar.
{{kod:lab06-i2c/src/ina226.c}}
{{kod:lab06-i2c/src/main.c}}
::/
:::
