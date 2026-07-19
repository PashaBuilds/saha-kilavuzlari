# Bölüm 0 — Hoş Geldin

Ekibe hoş geldin. Bu doküman, önümüzdeki iki haftanın yol arkadaşı.

Masanda (ya da yakında masanda olacak) bir **ZCU111** geliştirme kartı var:
çekirdeğinde bir Zynq UltraScale+ RFSoC (Radio Frequency System-on-Chip —
radyo frekanslı sistem-çipi) oturuyor — alanımızın ciddi cihazlarından
biri. Üniversitede C gördün, belki bir Arduino üzerinde LED yaktın —
sağlam bir başlangıç. Ama önündeki kart bir Arduino değil: içinde dört
çekirdekli bir uygulama işlemcisi, iki real-time (gerçek zamanlı)
çekirdek, geniş bir FPGA fabric ve henüz adını duymadığın onlarca çevre
birimi var. İlk bakışta gözünün korkması makul. Bu dokümanın işi, o
yabancılığı iki hafta içinde kartla çalışan bir yetkinliğe çevirmek.

## Bu doküman nasıl çalışır

Bu bir referans kılavuzu değil, bir **yolculuk**. Okuma bölümleriyle
doğrudan kart üzerinde yapılan görevler dönüşümlü ilerler: bir kavramı
okur, hemen kartta uygularsın. Hiçbir okuma bölümü, elin karta değmeden
uzun süre teori biriktirmez — bu bilinçli bir tasarım tercihi. Gömülü
yazılım pratikle öğrenilir.

Yolculuğun durakları aşağıdaki haritada. Her görevi bitirdiğinde
kartındaki "Tamamlandı" kutusunu işaretle; harita ilerledikçe dolar.
İşaretlerin bu tarayıcıda kalıcıdır (localStorage — tarayıcının yerel
deposu — üzerinden saklanır); sekmeyi kapatıp ertesi gün kaldığın yerden
devam edebilirsin.

{{ilerleme-panosu}}

Görev kartlarının anatomisine alışacaksın: her kart bir **hedef**, seni
ona hazırlayan **ön koşullar**, numaralı **adımlar** ve en önemlisi
gözlemlenebilir bir **başarı kriteri** tanımlar — ya sağlanır ya
sağlanmaz, arası yoktur. Takılırsan kartın altında bir **ipucu merdiveni**
hazır: önce nazik bir yön işareti, sonra daha somut bir ipucu, en sonda
tam çözüm. Basamakları sırayla kullan; doğrudan çözüme atlamak bugün
zaman kazandırır, iki hafta sonra fazlasıyla geri alır.

:::saha-notu Takılmak sürecin parçası
Bu yolculukta bir yerde takılacaksın; bu bir aksilik değil, müfredatın
kendisi. Bu meslekte hata mesajı okumak, var olmayan dokümantasyonu
aramak ve "neden çalışmıyor" sorusunun peşine düşmek, kod yazmaktan daha
çok zaman alır. Görev 10'a geldiğimizde bunu sistematik bir egzersize
dönüştüreceğiz.
:::

## İlk iki haftanın sonunda nerede duracaksın

Somut olarak, bu dokümanı bitirdiğinde şunları yapabileceksin:

- Zynq tabanlı bir sistemin **PS/PL ayrımını**, **boot (açılış) akışını**
  ve **memory map'ini** (bellek haritası) beyaz tahta düzeyinde anlatmak.
- Vitis'te sıfırdan bare-metal (işletim sistemsiz) bir proje oluşturmak,
  derlemek, JTAG üzerinden karta yüklemek, UART'tan çıktı almak ve
  debugger (hata ayıklayıcı) ile adım adım yürütmek.
- Register map (register tablosu) okuyup `volatile` işaretçilerle donanım
  programlamak; hem polling (sürekli sorgulama) hem interrupt (kesme)
  tabanlı yaklaşımı uygulamak.
- I2C, SPI ve UART'ın kablo düzeyinde nasıl işlediğini anlatmak ve
  karttaki gerçek bir I2C cihazından veri okumak.
- Task, queue ve semaphore kullanan küçük bir FreeRTOS uygulaması yazmak.
- Ve sonunda, **Mezuniyet Görevi** olarak küçük ama çalışan bir sistemi
  tasarlayıp ekibe sunmak.

Liste iddialı görünüyorsa — öyle. Ama her madde, seni oraya taşıyan
küçük ve yönetilebilir adımlara bölünmüş durumda. Kimse ikinci gün
driver (sürücü) yazmanı beklemiyor; ikinci gün senden beklenen,
Görev 0'ı bitirmiş olman.

## Başlamadan önce: kurulum kontrol listesi

Aşağıdakileri ilk gün tamamla. Takılırsan bir ekip arkadaşına sor — bu
ekipte yardım istemek zayıflık değil, verimlilik göstergesidir.

1. **Vitis'i kur.** Ekibin kullandığı sürümü sistem yöneticine ya da ekip
   liderine teyit ettirip kur (kurulum saatler sürebilir, onlarca
   gigabayt yer ister; indirmeyi sabah başlat, bir aranın ardından
   kontrol et). Vitis'in ne olduğunu ve kavramsal yerleşimini Bölüm 11'de
   ayrıntısıyla ele alıyoruz; şimdilik "derleyici artı IDE artı kart
   programlayıcı" olarak kabul et ve geç.
2. **Kart kutusu.** ZCU111 kutusunu aç; güç adaptörünü ve kartla gelen
   USB kablolarını çıkar. Kutu içeriğini ve kartın fiziksel kurulumunu
   Görev 0'da adım adım geçeceğiz. Şimdilik kutuyu aç, parçaları masana
   diz ve kartı antistatik torbadan çıkarırken kenarlarından tut.
3. **Terminal programı.** Kartla en temel haberleşme yolu seri
   terminaldir. Ortamımız **Windows 10**; PuTTY ya da Tera Term (ikisi
   de ücretsiz) işi görür. Birini kur; Görev 0'da kullanacağız. (Vitis'in
   kendi seri terminali de var; ayrı program kurmak istemezsen onu
   kullanabilirsin.)
4. **Sürücüler.** Kartın USB-UART köprüsü Windows'ta birden fazla sanal
   COM portu oluşturur. Sürücü (FTDI VCP) genellikle kendiliğinden
   kurulur; Device Manager'da soru işaretli bir cihaz görürsen Görev
   0'daki ipucu merdivenine bak.
5. **Hesaplar ve erişim.** Ekibin git sunucusuna, wiki'sine ve dosya
   paylaşımına erişimini ilk gün doğrula. Git akışımızı Bölüm 12'de
   konuşuyoruz.

:::ekip-notu İlk hafta "çıktı" beklenmez
Bu ekipte yeni gelen birinin ilk haftası öğrenmeye ayrılır; bu doküman o
haftanın kendisidir. Ekip liderin sana sprint teslimatlarını değil, bu
dokümandaki görevlerde nerede olduğunu soracak. Acele etme, ama temposunu
düşürme.
:::

Hazır olduğunda Bölüm 1 büyük resimle açılıyor: gömülü sistem tam olarak
nedir ve bu alandaki rolün ne olacak?
