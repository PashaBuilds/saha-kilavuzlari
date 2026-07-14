# Bölüm 0 — Hoş Geldin

Ekibe hoş geldin. Bu doküman, önümüzdeki birkaç haftanın yol arkadaşı olacak.

Masanda (ya da yakında masanda olacak) bir **ZCU111** geliştirme kartı var:
üzerinde Zynq UltraScale+ RFSoC (Radio Frequency System-on-Chip — RF
örnekleyicili sistem-çipi) taşıyan, bizim dünyamızın ciddi oyuncaklarından
biri. Üniversitede C gördün, belki Arduino'ya LED yakıp söndürdün — güzel.
Ama önündeki kart bir Arduino değil; içinde dört çekirdekli bir uygulama
işlemcisi, iki gerçek-zaman çekirdeği, koca bir FPGA fabric'i ve senin henüz
adını duymadığın düzinelerce çevre birimi var. İlk bakışta gözünün korkması
normal. Bu dokümanın işi, o korkuyu iki hafta içinde "ben bu kartla iş
yapıyorum" rahatlığına çevirmek.

## Bu doküman nasıl çalışır

Bu bir referans kitabı değil, bir **yolculuk**. Okuma bölümleriyle elde kart
yapılan görevler dönüşümlü ilerler: bir kavramı okursun, hemen ardından o
kavramı kartın üzerinde elinle yaparsın. Hiçbir okuma bölümü, eller karta
değmeden uzun süre teori biriktirmez — bu bilinçli bir tasarım. Gömülü
yazılım ancak parmak uçlarında öğrenilir.

Yolculuğun durakları aşağıdaki haritada. Her görevi bitirdiğinde kartındaki
"Tamamladım" kutusunu işaretle; harita seninle birlikte dolar. İşaretlerin
bu tarayıcıda kalıcıdır (localStorage — tarayıcının yerel depolaması — ile
saklanır), yani sekmeyi kapatıp ertesi gün devam edebilirsin.

{{ilerleme-panosu}}

Görev kartlarının anatomisine alışacaksın: her kartta bir **hedef**, seni
hazırlayan **ön koşullar**, numaralı **adımlar** ve en önemlisi
gözlemlenebilir bir **başarı kriteri** var — "oldu" ya da "olmadı", arası
yok. Takılırsan kartın altındaki **ipucu merdiveni** seni bekliyor: önce
nazik bir yönlendirme, sonra daha somut bir ipucu, en sonda tam çözüm.
Merdivenin basamaklarını sırayla kullan; çözüme atlamak seni bugün
hızlandırır ama iki hafta sonra yavaşlatır.

:::saha-notu Takılmak işin parçası
Bu yolculukta bir yerlerde takılacaksın; bu bir aksilik değil, müfredatın ta
kendisi. Bizim işte hata mesajı okumak, olmayan dokümanı aramak ve "neden
çalışmıyor"un peşine düşmek, kod yazmaktan daha fazla zaman alır. Görev 10'a
geldiğinde bunu bir dedektiflik oyununa çevireceğiz.
:::

## İlk iki haftanın sonunda nereye varacaksın

Somut konuşalım. Bu dokümanı bitirdiğinde:

- Bir Zynq tabanlı sistemde **PS/PL ayrımını**, **boot akışını** ve **bellek
  haritasını** beyaz tahtada anlatabileceksin.
- Vitis'te sıfırdan bare-metal (işletim sistemsiz) proje açıp derleyip karta
  JTAG ile atabilecek, UART'tan çıktı alabilecek, debugger ile adım adım
  yürütebileceksin.
- Register map (yazmaç haritası) okuyup `volatile` pointer ile donanım
  programlayabilecek; polling ve interrupt tabanlı iki yaklaşımı da
  uygulayabileceksin.
- I2C/SPI/UART'ın tel seviyesinde nasıl çalıştığını çizebilecek, karttaki
  gerçek bir I2C cihazından veri okuyabileceksin.
- FreeRTOS'ta task/queue/semaphore kullanan küçük bir uygulama yazabileceksin.
- Ve final: **Mezuniyet Görevi**'ni — küçük ama gerçek bir sistemi — tek
  başına tasarlayıp ekip önünde sunacaksın.

Liste iddialı görünüyorsa: evet, öyle. Ama her maddenin altında seni oraya
taşıyan küçük, sindirilebilir adımlar var. Kimse senden ikinci gün driver
yazmanı beklemiyor; ikinci gün senden beklenen, Görev 0'ı bitirmiş olman.

## Başlamadan: kurulum kontrol listesi

Aşağıdakileri ilk gün hallet; takıldığın yerde yanındaki masaya sor —
sormak bu ekipte zayıflık değil, verimlilik göstergesidir.

1. **Vitis kurulumu.** Ekipçe kullandığımız sürümü sistem yöneticisinden ya
   da takım liderinden öğren ve kur (kurulum saatler sürebilir ve onlarca GB
   yer ister; indirmeyi sabah başlat, öğleden sonra kahveyle kontrol et).
   Vitis'in ne olduğunu ve içindeki kavram haritasını Bölüm 11'de ayrıntılı
   göreceğiz; şimdilik "derleyici + IDE + kart programlayıcı" de, geç.
2. **Kart kutusu.** ZCU111 kutusundan kartla birlikte güç adaptörü ve
   USB kabloları çıkar; kutu içeriğini ve kartın fiziksel kurulumunu Görev
   0'da adım adım yapacağız. Şimdilik kutuyu aç, parçaları masana diz,
   antistatik torbadan çıkarırken kartı kenarlarından tut.
3. **Terminal programı.** Kartla konuşmanın en temel yolu seri terminaldir.
   Bizim ortamımız **Windows 10**; PuTTY ya da Tera Term (ikisi de ücretsiz)
   işini görür. Birini kur, Görev 0'da kullanacağız. (Vitis'in kendi seri
   terminali de vardır; ayrı bir program istemezsen onu da kullanabilirsin.)
4. **Sürücüler.** Kartın USB-UART köprüsü Windows'ta birkaç sanal COM portu
   oluşturur. Sürücü (FTDI VCP) çoğu zaman otomatik gelir; Aygıt
   Yöneticisi'nde soru işaretli bir aygıt görürsen Görev 0'daki ipucu
   merdivenine bak.
5. **Hesaplar ve erişimler.** Ekibin git sunucusuna, wiki'sine ve dosya
   paylaşımına erişimini ilk gün doğrula. Bölüm 12'de git akışımızı
   konuşacağız.

:::ekip-notu İlk hafta kimseden "çıktı" beklenmez
Bizim ekipte yeni başlayan arkadaşın ilk haftası öğrenmeye ayrılmıştır; bu
doküman o haftanın ta kendisi. Takım liderin senden bu dokümandaki görevlerin
ilerleyişini soracaktır, sprint görevi değil. Rahat ol, ama boş da durma.
:::

Hazırsan Bölüm 1'de büyük resimden başlıyoruz: gömülü sistem tam olarak
nedir ve senin bu dünyadaki rolün ne olacak?
