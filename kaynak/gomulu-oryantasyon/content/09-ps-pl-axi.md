# Bölüm 9 — PS ↔ PL: AXI ve IP Dünyası

Bölüm 8'de kablo seviyesinde çalıştın: UART, SPI, I2C — kartı dış dünyaya
bağlayan protokoller. Şimdi yön *içeri*, çipin kendisine dönüyor. Bölüm
2'de PS ile PL'nin **AXI** köprüleriyle birleştiğini söylemiş, ayrıntıyı
Bölüm 9'a bırakmıştık. O bölüm bu. Sonunda, bir donanım mühendisinin
teslim ettiği IP bloğuyla nasıl haberleşeceğini bileceksin — ve Bölüm 2'nin
kapanışında verilen sözü tutup 8 LED'in tümünü yakacaksın.

## AXI: PS ile PL'nin Ortak Dili

**AXI (Advanced eXtensible Interface)**, Arm'ın çip içi veri yolu (bus)
ailesinin adıdır; Zynq üzerinde PS ile PL arasındaki her veri alışverişi
bu protokolün bir türevinden geçer. Ayrıntıya girmeden önce tek bir
sezgiyi yerleştir: AXI, **valid/ready el sıkışması** (handshake) üzerine
kuruludur. Gönderen taraf "elimde geçerli veri var" der (**VALID**); alıcı
taraf "kabul etmeye hazırım" der (**READY**). İki sinyal aynı anda yüksek
olmadıkça karşıya tek bit geçmez — taraflardan her biri diğerini
bekletebilir, hiçbiri veriyi zorla itemez. Telsiz disiplinindeki
gönderme/teyit sırasıyla aynı mantık: karşı taraf "anlaşıldı" demeden
mesaj iletilmiş sayılmaz.

{{svg:sema-20-axi-el-sikisma.svg|Şekil 20 — AXI valid/ready el sıkışması zamanlama diyagramı (üstte) ve bir okuma isteğinin PS'ten PL'deki AXI GPIO'ya yolculuğu (altta).}}

AXI'de okuma ve yazma işlemleri ayrı **kanallar** üzerinden yürür (bir
adres kanalı, bir veri kanalı ve yazma için ek bir "cevap" kanalı) — tüm
ayrıntı şimdilik önemli değil. Senin için önemli olan şu: bir register
okuyup yazdığında bu el sıkışmaların tamamı, tek bir CPU load/store
komutunun (`Xil_In32`/`Xil_Out32` ya da doğrudan `volatile` pointer
erişimi) arkasında gerçekleşir. Register erişimi tam olarak Bölüm 4'te
öğrendiğin şeydir; AXI, o erişimi PL'ye taşıyan mekanizmadan ibarettir.

## PL'deki Bir IP Bloğu PS'ten Nasıl Görünür

Bir donanım mühendisi PL'ye bir devre yerleştirdiğinde (bir sinyal işleme
bloğu, bir motor sürücüsü ya da basit bir LED denetleyicisi), o devre
PS'e yalnızca tek bir biçimde görünür: **bir adres penceresi üzerinden
erişilen register kümesi**. Vivado'da (donanım mühendislerinin kullandığı
tasarım aracı) her IP bloğuna Address Editor üzerinden bir taban adres ve
boyut atanır; bu pencere senin `xparameters.h` dosyanda
`XPAR_<isim>_BASEADDR` biçiminde bir satır olarak belirir. PL'deki bir IP
bloğuyla haberleşmek bu yüzden Bölüm 4'te öğrendiğin akıştan farklı
değildir: taban adresi al, offset'i ekle, oku ya da yaz. Fark şu: bu kez
adres silikona sabitlenmiş değildir — **tasarımdan tasarıma değişen** bir
penceredir.

Ekipte bu akış net tanımlıdır: "donanımcı IP bloğunu teslim etti" cümlesi
tek başına yeterli değildir. İki şey daha istersin: bitstream'e eşlik eden
**.xsa** dosyası (adres pencerelerini `xparameters.h`'e taşıyan platform
tanımı) ve IP bloğunun **register haritası** (hangi offset ne iş yapar,
hangi bit ne anlama gelir). İkisi olmadan elindeki, "kara kutu"dan fazlası
değildir.

:::ekip-notu Offset Tablosu Olmadan IP Bloğu Teslim Alınmaz
Ekipte bir donanım mühendisi sana "IP bloğunu PL'ye koydum,
kullanabilirsin" dediğinde ilk soru şudur: "Register haritası nerede?"
Hazır bir IP bloğu için (AXI GPIO gibi) bu işi üreticinin ürün kılavuzu
görür (Xilinx'te "PGxxx" numarasıyla anılır). Özel tasarlanmış bir IP
bloğu içinse donanımcıdan en azından bir offset tablosu ve her bitin
anlamını açıklayan bir not beklenir — bu, yazılım ile donanım arasındaki
en temel sözleşmedir. Bu tabloyu istemeden bir IP bloğunu "teslim
alınmış" sayma; günler sonra "o bit ne yapıyordu" diye sormak, başta tek
soruyla önleyebileceğin bir kayıptır.
:::

## Hazır IP Blokları: Raftan İnen Parçalar

Her IP bloğu sıfırdan tasarlanmaz; Xilinx (ve üçüncü taraflar), sık
kullanılan işlevler için hazır IP bloğu kütüphaneleri tutar; donanım
mühendisi bunları Vivado'da yerine sürükler. İşinde en sık karşılaşacağın
üçü:

- **AXI GPIO** — en basit IP bloğu; PL pinlerini PS'ten okuyup yazmanı
  sağlar ve Görev 7'nin de konusudur. Kendi register haritası vardır
  (birazdan geliyor); *kavram* olarak PS GPIO (Bölüm 4–7) ile aynıdır,
  ama ayrı bir donanım parçasıdır ve ayrı bir sürücü ailesi vardır
  (`XGpio`, `XGpioPs` değil).
- **AXI Timer** — PL'de duran bir zamanlayıcı; PS'in TTC'sine (Bölüm 7)
  benzer, ama donanım mühendisinin ihtiyaç duyduğu sayıda ve
  yapılandırmada çoğaltılabilir.
- **AXI BRAM Controller** — PL'in Block RAM'ine (FPGA fabric içindeki
  gömülü bellek) AXI erişimi sağlar; küçük bir ortak bellek gibi
  düşünebilirsin.

Üçü de aynı ailedendir: PS'ten bakınca her biri bir adres penceresi ve
bir register haritasından ibarettir. Birini öğrenmek, diğerleriyle nasıl
çalışacağını da öğretir.

## Kapı Açılıyor: 8 LED'in Tümü Artık Erişilebilir

Bölüm 2'de açıkça not etmiştik: kartın 8 kullanıcı LED'i (DS11–DS18) PL
pinlerine bağlıdır ve bitstream olmadan PS'ten erişilemez. Görev 1–5
boyunca yalnızca DS50 ile çalıştın. O sınır burada kalkıyor: ekipçe
hazırlanan bitstream'de `GPIO_LED[7:0]` pinlerine — yani DS11–DS18'e —
bağlı bir **AXI GPIO** IP bloğu var. Bu IP bloğunun register haritasını
okuyacak ve Bölüm 4 yaklaşımını (taban adres + offset) bir kez daha
uygulayacaksın; tek fark, adresin bu kez bir `.xsa` dosyasından geliyor
olması.

:::derin-dalis AXI-Lite, AXI4 ve AXI-Stream: Üç Tür, Üç Amaç
AXI ailesinin PS–PL dünyasında en sık karşılaşacağın üç üyesi vardır; üçü
de aynı valid/ready kavramını paylaşır ama farklı iş yüklerine hizmet
eder:

- **AXI-Lite**: ailenin en yalını. Bir seferde tek register okur ya da
  yazar; burst (tek istek içinde birden çok ardışık adresi aktarma)
  desteklemez. AXI GPIO gibi register tabanlı, düşük hızlı kontrol IP
  blokları bunu kullanır — Görev 7'de çalışacağın arayüz budur.
- **AXI4 (AXI4-Full)**: burst destekler — tek istekte birden çok ardışık
  veri sözcüğü taşıyabilir (örneğin tek bir el sıkışma dizisi içinde on
  altı 32-bit sözcük). Yüksek bant genişliği isteyen bellek erişimlerinde
  (BRAM/DDR denetleyicileri gibi) kullanılır.
- **AXI-Stream**: adres kavramı yoktur — kesintisiz, sıralı bir veri
  akışı taşır (adresin yerini "sıradaki veri" mantığı alır). Görüntü
  işleme ya da RF örnekleme gibi sürekli veri akışı isteyen işlevler
  arasında, IP bloğundan IP bloğuna veri taşımakta kullanılır.

CPU'nun büyük hacimli veriyi (bir kamera görüntüsü, bir blok RF örneği)
register register okuyarak taşıması pratik değildir — bu iş CPU'yu
tamamen meşgul eder. **DMA (Direct Memory Access)** burada devreye girer:
"şu kaynaktan şu hedefe şu kadar veri taşı" talimatını verirsin, aktarım
CPU'yu meşgul etmeden arka planda AXI4/AXI-Stream üzerinden yürür;
aktarım bitince CPU bir interrupt (Bölüm 7) ile haberdar edilir. DMA'nın
kendisi Bölüm 13'te (Ufuk Turu) yeniden karşına çıkacak; şimdilik
"CPU'yu baypas eden toplu veri aktarımı" kavramını tanıman yeterli.
:::

Bir register haritasını öğrenmenin en iyi yolu elini kirletmektir. Sıra
Görev 7'de.

:::gorev no=7 zorluk=2 baslik="PL'deki Bir IP Bloğuyla Haberleş" kisa="PL LED'leri"
[Hedef]
Ekipçe sağlanan bitstream'deki AXI GPIO IP bloğunun register'larına
volatile pointer ile eriş ve 8 kullanıcı LED'inde (DS11–DS18) soldan sağa
yürüyen ışık deseni üret.

[Ön koşul]
Bölüm 9 okundu; Görev 0 tamamlandı. Bu görevde donanım tarafı
(bitstream/.xsa) **ekip tarafından sağlanır** — tasarımda `GPIO_LED[7:0]`
pinlerine bağlı bir AXI GPIO IP bloğu olduğu varsayılır (bkz.
`labs/lab07-axigpio/README.md`).

[Adımlar]
1. Ekibin verdiği `.xsa` dosyasından Vitis'te bir platform bileşeni
   oluştur (OS: `standalone`, işlemci: `psu_cortexa53_0`).
2. Üretilen `xparameters.h` içinde AXI GPIO IP bloğunun taban adresini
   bul: aradığın, `XPAR_<instance-adı>_BASEADDR` biçiminde bir satır. Bu,
   donanım mühendisinin Vivado Address Editor'da bu IP bloğuna atadığı
   adres penceresidir (Şekil 20'nin alt yarısındaki 3 numaralı kutu).
   Instance adı, donanımcının Vivado'da bloğa verdiği isme bağlıdır; bu
   lab `axi_gpio_0` varsayar.
3. AXI GPIO register haritasını teyit et — bu doküman için Xilinx
   PG144'ten doğrulanıp kaynağıyla birlikte `content/_arastirma-ek-E.md`'ye
   işlendi: `GPIO_DATA` offset `0x0000` (veri), `GPIO_TRI` offset
   `0x0004` (yön: bit=0 çıkış, bit=1 giriş).
4. Önce `GPIO_TRI`'ye yazarak 8 bitin tümünü çıkış yap, sonra tek biti
   sırayla kaydırarak yürüyen ışık desenini `GPIO_DATA`'ya yaz —
   `labs/lab07-axigpio/src/main.c`'deki gibi doğrudan
   `volatile`/`Xil_Out32` register erişimiyle.
5. Derin dalış (isteğe bağlı ama önerilir): aynı görevi Xilinx'in hazır
   `XGpio` sürücüsüyle (`XGpio_Initialize`, `XGpio_SetDataDirection`,
   `XGpio_DiscreteWrite`) yeniden yaz; iki yaklaşımın da birebir aynı
   register trafiğini ürettiğini gözle.

[Başarı kriteri]
8 kullanıcı LED'inde (DS11–DS18) soldan sağa düzenli bir yürüyen ışık
deseni gözlüyorsun.

[Kendini sına]
- `GPIO_TRI` register'ı tam olarak ne yapar? Yapılandırmayı unutursan ne
  olur?
- Aynı bitstream'de ikinci bir AXI GPIO IP bloğu olsaydı, adresini nerede
  bulurdun?
- AXI GPIO'nun taban adresi tasarımdan tasarıma değişebilirken PS GPIO'nun
  taban adresi (`0xFF0A_0000`) neden hep aynıdır?

[Takıldıysan]
::ipucu İpucu 1 — LED'lerin hiçbiri yanmıyor
Önce `GPIO_TRI`'yi doğru yapılandırdığından emin ol: sıfır yazılan bitler
çıkış olur. Yön ayarını atlarsan (ya da tersine çevirirsen) `GPIO_DATA`'ya
yazdığın hiçbir şey dışarıya yansımaz — donanım seni "giriş" modunda
tutuyor olabilir. İkinci şüpheli: taban adresi doğru mu okudun, yoksa PS
GPIO'nun adresiyle (`0xFF0A_0000`) mi karıştırdın?
::/
::ipucu İpucu 2 — xparameters.h'te aradığım ismi bulamıyorum
Vivado'daki IP instance adı makro adına doğrudan taşınır, ama büyük harfe
çevrilir ve tireler alt çizgi olur. Dosyayı editörde aç, `BASEADDR` geçen
satırları arama (Ctrl+F) ile listele ve AXI GPIO'ya benzeyen tek aday
kalana kadar daralt. Birden fazla AXI GPIO bloğu varsa LED'lere hangisinin
bağlı olduğunu donanım mühendisine sor — bu da register haritası
kültürünün parçasıdır.
::/
::cozum Tam Çözüm — lab07-axigpio
`labs/lab07-axigpio/src/main.c`, TRI/DATA register çiftine volatile
pointer ile erişir; dosyanın sonundaki yorum bloğu aynı işin `XGpio`
sürücüsüyle nasıl yapılacağını gösterir.
{{kod:lab07-axigpio/src/main.c}}
::/
:::

PL'ye açılan kapıyı geçtin ve donanımın iki yüzünü de gördün. Şimdi
yazılımı ölçeklendirme zamanı — sıradaki durak, tek bir `main()`
fonksiyonundan gerçek bir işletim sistemine geçiş.
