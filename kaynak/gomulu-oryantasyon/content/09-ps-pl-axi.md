# Bölüm 9 — PS ↔ PL: AXI ve IP Dünyası

Bölüm 8'de tel seviyesinde konuştun: UART, SPI, I2C — hepsi kartın dışına
açılan protokoller. Şimdi çipin *içine* dönüyoruz. Bölüm 2'de PS ile PL'nin
**AXI** köprüleriyle evli olduğunu söylemiştik ve "ayrıntılarına Bölüm 9'da
gireceğiz" demiştik. O bölüm burası. Bitince donanımcının sana verdiği bir
IP'yle nasıl konuşacağını bileceksin — ve Bölüm 2'nin sonunda yarım bıraktığı
sözü tutup 8 LED'i de yakacaksın.

## AXI: PS ile PL'nin ortak dili

**AXI (Advanced eXtensible Interface)**, Arm'ın çip-içi veriyolu ailesinin
adıdır; Zynq'te PS ile PL arasındaki her veri alışverişi bu protokolün bir
türüyle olur. Ayrıntıya girmeden önce tek bir sezgiyi kafana yerleştir:
AXI, **valid/ready el sıkışması** üzerine kuruludur. Veriyi gönderen taraf
"elimde geçerli veri var" der (**VALID**); alan taraf "alabilirim" der
(**READY**). İkisi de aynı anda yüksek olmadan tek bir bit bile karşıya
geçmez — biri diğerini bekletebilir, kimse zorla veri iletmez. Bu, telefonda
"duyuyor musun" — "duyuyorum" el sıkışmasına benzer: biri konuşurken öbürü
hattı kapatmışsa mesaj kaybolur.

{{svg:sema-20-axi-el-sikisma.svg|Şekil 20 — AXI valid/ready el sıkışması zaman diyagramı (üstte) ve PS'ten PL'deki bir AXI GPIO'ya okuma isteğinin yolculuğu (altta).}}

AXI'de okuma ve yazma işlemleri ayrı **kanallardan** yürür (adres kanalı,
veri kanalı, yazmada ayrıca bir "tamamlandı" kanalı) — bunun tam ayrıntısı
şimdilik önemli değil, önemli olan senin açından şu: sen bir register'ı
okuduğunda ya da yazdığında, arkada bu el sıkışmalarının hepsi CPU'nun tek
bir yükleme/saklama komutunun (`Xil_In32`/`Xil_Out32` ya da doğrudan
`volatile` pointer erişimi) altında saklıdır. Register erişimi Bölüm 4'te
öğrendiğin şeyin ta kendisidir; AXI sadece o erişimin PL'ye kadar nasıl
taşındığının hikâyesidir.

## PL'deki bir IP'nin PS'ten görünüşü

Donanımcı arkadaşın PL'ye bir devre koyduğunda (bir sinyal işleme bloğu, bir
motor sürücü, ya da mütevazı bir LED denetleyicisi), bu devre PS'ten tek bir
şekilde görünür: **bir adres penceresinden erişilen bir register kümesi**.
Vivado'da (donanımcının kullandığı tasarım aracı) her IP'ye Address Editor
üzerinden bir taban adres ve bir boyut atanır; bu pencere senin
`xparameters.h`'inde bir `XPAR_<isim>_BASEADDR` satırı olarak karşına çıkar.
Yani PL'deki IP'yle konuşmak, Bölüm 4'te öğrendiğin iş akışından farksızdır:
taban adresi al, ofset ekle, oku ya da yaz. Fark, adresin bu sefer silikonda
sabit değil, **tasarıma göre değişen** bir pencere olmasıdır.

Bizim ekipte bu iş akışı nettir: "donanımcı bir IP verdi" cümlesi tek
başına yetmez. Sana lazım olan iki şey vardır — bitstream'in eşlik ettiği
**.xsa** dosyası (adres pencerelerini `xparameters.h`'e taşıyan platform
tanımı) ve IP'nin **register haritası** (hangi ofset ne işe yarar, hangi
bit ne anlama gelir). İkisi olmadan elindeki "kara kutu"dan ibarettir.

:::ekip-notu Offset tablosu olmadan IP teslim alınmaz
Bizim ekipte bir donanımcı sana "IP'yi PL'ye koydum, kullan" dediğinde
ilk sorun "register haritası nerede?" olur. Hazır bir IP'yse (AXI GPIO gibi)
üreticinin product guide'ı (Xilinx için "PGxxx" numarasıyla anılır) bu işi
görür. Özel tasarım bir IP'yse donanımcının en az bir offset tablosu ve
her bitin anlamını yazan bir not düşmesi beklenir — bu, yazılım ile donanım
arasındaki en temel sözleşmedir. Bu tabloyu istemeden IP'yi "teslim almış"
sayılmazsın; günler sonra "şu bit ne işe yarıyordu" diye sormak, en
başta bir satırlık soruyla kaçınabileceğin bir kayıptır.
:::

## Standart IP'ler: hazır parçalar kutusu

Her IP'yi donanımcı sıfırdan tasarlamaz; Xilinx'in (ve üçüncü tarafların)
hazır IP kütüphanesinde sık kullanılan bloklar vardır, donanımcı bunları
Vivado'da sürükleyip PL'ye yerleştirir. Yolculuğunda karşına çıkması en
olası üçü:

- **AXI GPIO** — PL pinlerini PS'ten okuyup yazmanı sağlayan en basit IP;
  Görev 7'nin de kahramanı. Kendi register haritası vardır (birazdan
  göreceksin), PS GPIO'yla (Bölüm 4-7) aynı *fikri* taşır ama ayrı bir
  donanım ve ayrı bir sürücü ailesidir (`XGpio`, `XGpioPs` değil).
- **AXI Timer** — PL'de yaşayan, PS'in TTC'sine (Bölüm 7) benzeyen ama
  donanımcının istediği sayıda ve özellikte örneklenebilen bir zamanlayıcı.
- **AXI BRAM Controller** — PL'nin Block RAM'ine (FPGA fabric'indeki gömülü
  bellek) AXI üzerinden erişim sağlar; küçük bir paylaşımlı bellek gibi
  düşünebilirsin.

Bu üçü de aynı ailenin üyesidir: PS'ten bakınca hepsi bir adres penceresi ve
bir register haritasıdır. Birini öğrenmek, ötekilerin de nasıl
okunacağını öğretir.

## Kapı açılıyor: 8 LED artık erişilebilir

Bölüm 2'de dürüst bir itirafta bulunmuştuk: kartın 8 kullanıcı LED'i
(DS11–DS18) PL pinlerindedir ve bitstream'siz PS'ten erişilemez. Görev 1-5
boyunca yalnızca DS50 ile idare ettin. İşte tam burada o sınır kalkıyor:
ekipçe hazırlanan bitstream'de bir **AXI GPIO** IP'si, `GPIO_LED[7:0]`
pinlerine — yani DS11-DS18'e — bağlı geliyor. Sen bu IP'nin register
haritasını okuyup aynı Bölüm 4 refleksini (taban adres + ofset) tekrar
uygulayacaksın; tek fark, adresin bu sefer bir `.xsa` dosyasından geldiği.

:::derin-dalis AXI-Lite, AXI4 ve AXI-Stream: üç kardeş, üç iş
AXI ailesinin PS-PL dünyasında en sık gördüğün üç üyesi var, hepsi aynı
valid/ready fikrini paylaşır ama iş yükleri farklıdır:

- **AXI-Lite**: en basit üye. Tek seferde bir register okur/yazar, burst
  (art arda birden çok adresi tek istekte taşıma) desteklemez. AXI GPIO gibi
  register-tabanlı, düşük hızlı kontrol IP'leri bunu kullanır — Görev 7'de
  konuştuğun arayüz budur.
- **AXI4 (AXI4-Full)**: burst destekler — tek bir istekle art arda birden
  çok veri sözcüğü taşıyabilir (örneğin 16 adet 32-bit kelimeyi tek
  el sıkışma dizisinde). Yüksek bant genişliği isteyen bellek erişimlerinde
  (BRAM/DDR denetleyicileri gibi) kullanılır.
- **AXI-Stream**: adres kavramı yoktur — sürekli, sıralı bir veri akışı
  taşır (adres yerine yalnızca "bir sonraki veri sözcüğü" mantığı). Görüntü
  işleme, RF örnekleme gibi sürekli veri akışı isteyen bloklar arasında
  IP'den IP'ye veri taşımak için kullanılır.

Büyük veri hacimlerini (bir kamera görüntüsünü, bir RF örnek bloğunu) CPU'nun
tek tek register okuyarak taşıması gerçekçi değildir — CPU'yu tıkar. Burada
devreye **DMA (Direct Memory Access — doğrudan bellek erişimi)** girer: CPU'ya
"şu kaynaktan şu hedefe şu kadar veri taşı" der, taşıma işi CPU'yu meşgul
etmeden arka planda AXI4/AXI-Stream üzerinden yürür, iş bitince CPU'ya bir
interrupt (Bölüm 7) ile haber verilir. DMA'nın kendisi Bölüm 13'te (Ufuk
Turu) tekrar karşına çıkacak; şimdilik "CPU'yu bypass eden toplu veri
taşıma" fikrini tanımış ol.
:::

Register haritasını öğrenmenin en iyi yolu, elini kirletmek. Sıra Görev
7'de.

:::gorev no=7 zorluk=2 baslik="PL'deki IP ile Konuş" kisa="PL LED'leri"
[Hedef]
Ekipçe sağlanan bitstream'deki bir AXI GPIO IP'sinin register'larına
volatile pointer ile erişip 8 kullanıcı LED'inde (DS11-DS18) soldan sağa
yürüyen ışık oluşturmak.

[Ön koşul]
Bölüm 9 okundu; Görev 0 tamamlandı. Donanım tarafı (bitstream/.xsa) bu
görevde **ekipçe temin edilir** — tasarımda bir AXI GPIO IP'sinin
`GPIO_LED[7:0]` pinlerine bağlı olduğu varsayılır (bkz.
`labs/lab07-axigpio/README.md`).

[Adımlar]
1. Ekipten aldığın `.xsa` dosyasından Vitis'te bir platform component
   oluştur (OS: `standalone`, işlemci: `psu_cortexa53_0`).
2. Üretilen `xparameters.h`'te AXI GPIO IP'sinin taban adresini bul:
   `XPAR_<instance-adı>_BASEADDR` biçiminde bir satır arıyorsun. Bu, Vivado
   Address Editor'da donanımcının bu IP'ye verdiği adres penceresidir
   (Şekil 20'nin alt yarısındaki 3. kutu). Instance adı donanımcının
   Vivado'da IP'ye verdiği isme bağlıdır; bu lab'da `axi_gpio_0` varsayıldı.
3. AXI GPIO register haritasını doğrula — bu doküman için Xilinx PG144'ten
   web ile teyit edilip `content/_arastirma-ek-E.md`'ye kaynaklı not olarak
   düşüldü: `GPIO_DATA` ofset `0x0000` (veri), `GPIO_TRI` ofset `0x0004`
   (yön: bit=0 çıkış, bit=1 giriş).
4. Önce `GPIO_TRI`'ye yazarak 8 biti çıkışa al, sonra `GPIO_DATA`'ya
   sırayla tek bit kaydırarak yürüyen ışık deseni yaz — doğrudan
   `volatile`/`Xil_Out32` register erişimiyle, `labs/lab07-axigpio/src/main.c`
   gibi.
5. Derin dalış (isteğe bağlı ama tavsiye edilir): aynı işi Xilinx'in hazır
   `XGpio` sürücüsüyle (`XGpio_Initialize`, `XGpio_SetDataDirection`,
   `XGpio_DiscreteWrite`) tekrar yaz; iki yaklaşımın ürettiği register
   trafiğinin aynı olduğunu gözlemle.

[Başarı kriteri]
8 kullanıcı LED'inde (DS11-DS18) soldan sağa doğru düzenli ilerleyen bir
yürüyen ışık deseni görüyorsun.

[Kendini sına]
- `GPIO_TRI` register'ı tam olarak ne işe yarıyor? Onu ayarlamayı unutursan
  ne olur?
- Aynı bitstream'de ikinci bir AXI GPIO IP'si olsaydı, onun adresini nereden
  öğrenirdin?
- PS GPIO'nun taban adresi (`0xFF0A_0000`) her zaman aynıyken AXI GPIO'nunki
  neden tasarımdan tasarıma değişebiliyor?

[Takıldıysan]
::ipucu İpucu 1 — LED'lerden hiçbiri yanmıyor
Önce `GPIO_TRI`'yi doğru ayarladığından emin ol: sıfır yazdığın bitler
çıkış olur. Yön ayarını atlarsan (ya da tersini yaparsan) `GPIO_DATA`'ya
yazdığın hiçbir şey dışarı yansımaz — donanım seni "giriş" modunda
bekletiyor olabilir. İkinci şüpheli: taban adresi doğru mu okudun,
yoksa PS GPIO'nun (`0xFF0A_0000`) adresiyle mi karıştırdın?
::/
::ipucu İpucu 2 — xparameters.h'te aradığım ismi bulamıyorum
Vivado'daki IP instance adı ile makro adı birebir eşleşir ama büyük harfe
çevrilir ve tire alt çizgiye döner. Dosyada `BASEADDR` geçen tüm satırları
listele (`grep BASEADDR xparameters.h`), AXI GPIO'ya benzeyen tek bir
aday kalana kadar dışla. Birden fazla AXI GPIO varsa donanımcıya hangisinin
LED'lere bağlı olduğunu sor — bu da register map kültürünün bir parçası.
::/
::cozum Tam çözüm — lab07-axigpio
`labs/lab07-axigpio/src/main.c` volatile pointer ile TRI/DATA register
çiftini kullanır; dosyanın sonundaki yorum bloğu aynı işi `XGpio`
sürücüsüyle nasıl yapacağını gösterir.
{{kod:lab07-axigpio/src/main.c}}
::/
:::

PL kapısını açtın; donanımın iki yakasını da gördün. Şimdi yazılımı
büyütme zamanı — bir sonraki durak, tek bir `main()` fonksiyonundan
gerçek bir işletim sistemine geçiş.
