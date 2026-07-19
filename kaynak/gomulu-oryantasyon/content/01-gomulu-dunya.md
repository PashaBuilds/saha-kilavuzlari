# Bölüm 1 — Gömülü Dünya ve Senin Rolün

Bölüm 0'da "gömülü yazılım pratikle öğrenilir" dedik. Ama el karta
değmeden önce netleşmesi gereken bir soru var: bundan sonra tam olarak ne
yapacaksın? Bu bölüm geniş bağlamı veriyor — gömülü sistem nedir,
alıştığın yazılım dünyasından nerede ayrılır ve bu alanda hangi
sorumluluklar sana düşer.

## Gömülü sistem nedir?

Gömülü sistem, belirli bir işlevi yerine getirmek üzere bir cihazın
içine yerleştirilmiş ve çoğu zaman varlığını dışarıya hiç belli etmeyen
bilgisayardır. Klavyesi yoktur, çoğu durumda ekranı yoktur, "uygulama
yükle" menüsü hiç yoktur; tek bir işi, her gün, cihazın ömrü boyunca,
istisnasız yapar.

Bu sabah uyandığından beri muhtemelen onlarcasını kullandın: seni
uyandıran telefon alarmı, kahvaltıda su ısıtıcısının sıcaklık kontrolü,
çıkarken bindiğin asansörün kat mantığı, arabanın fren pedalının
arkasındaki ABS kontrolcüsü, kulağındaki Bluetooth kulaklık, öğle
yemeğinin ödemesini geçiren POS terminali ve gün boyu telefonunu ağda
tutan baz istasyonu. Her birinin içinde, bizim yazdığımız türden
yazılımı koşturan irili ufaklı bir işlemci var.

{{svg:sema-01-evren.svg|Şekil 1 — Gömülü sistemler evreni: merkezde sensör → MCU/SoC → aktüatör zinciri, çevresinde günlük hayatta karşılaşılan gömülü cihazlar.}}

Tanımın çekirdeği, şekildeki üç parçalı zincir. **Sensör** dış dünyayı
ölçer: sıcaklık, basınç, bir buton basışı, bir anten sinyali. Ortadaki
**MCU** (microcontroller unit — mikrodenetleyici) ya da büyük kardeşi
**SoC** (system on chip — sistem-çipi) ölçümü okur ve karar verir.
**Aktüatör** kararı dünyaya uygular: motoru döndürür, valfi açar, LED'i
yakar, anteni sürer. Yazdığın kod bu döngünün tam ortasında oturur ve
döngü, cihaz güç gördüğü sürece döner.

:::analoji Gömülü sistem: hatta adanmış istasyon
Masaüstü bilgisayar çok amaçlı bir atölye tezgahıdır: pek çok işi yapar,
hiçbirine adanmamıştır. Gömülü sistem, üretim hattına sabitlenmiş tek
görevli istasyondur: tek işi vardır ve o işte kusursuz, öngörülebilir
olmak zorundadır. Tezgah arıza verirse işi başka tezgaha alırsın; hat
istasyonunun vardiya ortasında "geçici olarak hizmet dışıyım" deme lüksü
yoktur — bütün hat durur.
:::

## Masaüstü yazılımdan dört büyük fark

Üniversitede yazdığın C programları bir işletim sisteminin koruması
altında koştu: bellek istedin, verildi; ekrana yazdın, göründü; program
çöktü, bir şey olmadı. Gömülü dünyada bu tablo dört eksende değişir.

**1. Kaynak kısıtları.** Masaüstünde RAM gigabaytla ölçülür; gömülü
dünyada çoğu zaman kilobaytla, işlemci de gigahertz yerine megahertzle.
Açık olalım: önündeki ZCU111 bu yelpazenin lüks ucunda — dört çekirdeği
ve gigabaytlarca DDR belleği var. Ama gömülü zihniyet karta bağlı
değildir; her baytın ve her mikrosaniyenin hesabını tutma
alışkanlığıdır. O disiplini burada kuracaksın, çünkü bir sonraki projen
aynı lüksü tanımayabilir.

**2. Gerçek zaman.** Gömülü sistemlerde geç gelen doğru cevap, yanlış
cevapla aynı şeydir. ABS kontrolcüsü teker kilitlenmesini milisaniyeler
içinde algılayıp fren basıncını bırakmak zorundadır; "birazdan bakarım"
diye bir seçenek yoktur. Bu yüzden gömülü mühendis yalnızca *ne*
hesaplandığını değil, hesabın *ne kadar sürdüğünü* de tasarlar. Kavram,
Bölüm 7'de (interrupt) ve Bölüm 10'da (FreeRTOS) somutlaşacak.

**3. Donanıma yakınlık.** Masaüstünde seninle donanım arasında işletim
sistemi, sürücüler ve kütüphanelerden örülü kalın bir yastık var. Gömülü
dünyada o yastık incedir ya da hiç yoktur: donanımı doğrudan register
(çevre biriminin içindeki küçük kontrol ve durum hücreleri — Bölüm 4'ün
ana konusu) düzeyinde programlarsın. `printf` ile ekrana yazı basmak
bile, kendi elinle ayağa kaldırdığın bir UART'tan akar.

**4. Sorumluluk.** Çöken masaüstü programı yeniden başlatılır. Gömülü
sistemde hatalı bir yazılım güncellemesi cihazı brick edebilir (kalıcı
olarak çalışmaz hale getirmek). Üstelik cihaz sahada olabilir: bir
kulenin tepesinde, bir aracın içinde, müşterinin elinde. Cihaza fiziksel
erişimin yoksa "düzeltmeyi yarın gönderirim" cümlesinin bir karşılığı
yoktur.

:::saha-notu Brick hikâyeleri gerçektir
Her gömülü ekibin geçmişinde bir brick hikâyesi vardır: yanlış boot
imajı, yarıda kesilen flash yazımı, "küçücük değişiklikti" diye test
edilmeden çıkılan sürüm. Bunu seni ürkütmek için anlatmıyoruz —
masandaki ZCU111 bir geliştirme kartı, JTAG ile hemen her durumdan
kurtarılabilir; denemekten çekinme. Üretim kartı başka bir konudur;
alanımızın temel kuralı da bu yüzden şudur: değiştirdiysen test et.
:::

## İş tanımın

Peki bu alanda "gömülü yazılım mühendisi" fiilen ne yapar? Beş fiille
özetleyelim; önümüzdeki haftalarda her birini bizzat yaşayacaksın.

- **Driver yazmak.** Bir çevre birimiyle register düzeyinde konuşmak ve
  bunu ekibin geri kalanının kullanacağı temiz fonksiyonlara çevirmek:
  `uartSendChar()` fonksiyonunu yazan kişi olmak. İlk driver'ını
  Görev 2'de yazacaksın.
- **Register map üzerinden donanımcıyla konuşmak.** Register map, donanım
  ekibiyle aramızdaki sözleşmedir: hangi adres, hangi bit, ne anlama
  geliyor. Donanım mühendisi FPGA'de bir IP tasarlar ve sana register
  tablosunu verir; sen o tabloyu koda çevirirsin. Bu akışı Bölüm 9'da
  işliyoruz.
- **Bring-up.** Yeni bir kart ya da yeni bir IP masaya geldiğinde ona ilk
  nefesini aldırmak: clock çalışıyor mu, işlemci kalkıyor mu, UART'ta
  ilk bayt görünüyor mu? Görev 0 senin ilk küçük bring-up alıştırman.
- **Debug.** Arıza teşhis etmek — çoğu zaman ekransız, bazen `printf`
  bile yokken. Debugger, LED'ler, UART ve gerektiğinde osiloskop; bu
  takım çantasını Bölüm 11'de ele alıyoruz.
- **Entegrasyon.** Her parçanın tek tek doğru olduğu ama bütünün
  çalışmadığı bildik senaryoyu çözmek: parçaları tek sistemde
  buluşturmak ve arayüz hatalarını ayıklamak.

Bu listeyi katmanlara oturtalım. Aşağıdaki şekil gömülü bir sistemin
yazılım katmanlarını gösteriyor: en altta donanım, üstünde driver'lar,
onun üstünde middleware (protokol yığınları, RTOS ve diğer ortak
servisler), en üstte uygulama.

{{svg:sema-02-katmanlar.svg|Şekil 2 — Sorumluluk katmanları: gömülü yazılım mühendisi ağırlıkla driver ve middleware katmanlarında çalışır; masaüstü yazılımcının işi donanıma nadiren doğrudan dokunur.}}

Masaüstü yazılımcısı en üst katmanda çalışır; işletim sistemi altındaki
her şeyi görünmez kılar. Bizse ağırlıkla driver ve middleware
katmanlarındayız: bir el register'larda, öteki el uygulamaya temiz bir
arayüz uzatır. Uygulama katmanında da çalışırız — ama bizi tanımlayan,
onun altındaki iki katmanı güvenle yönetebilmektir.

:::ekip-notu Bu ekipte bir görevin yaşam döngüsü
Tipik bir görev şöyle ilerler: (1) görevi alırsın — çoğu zaman "şu çevre
birimine driver lazım" ya da "şu IP'yi ayağa kaldır" cümlesiyle; (2)
register map'i ve cihaz datasheet'ini okursun — kod yazmadan önce, sonra
değil; (3) driver'ı yazarsın; (4) bring-up: kod gerçek kartta ilk kez
koşar ve ilk denemede çalışmaması normaldir; (5) test edersin — başarı
kriterin baştan tanımlıdır; (6) code review'a gönderirsin (beklentiler
Bölüm 12'de); (7) entegrasyon: bileşenin sistemin geri kalanıyla
buluşur. Dikkat et: "kod yazmak" yedi adımdan yalnızca biri. Bu doküman
seni tam olarak bu döngüye hazırlıyor.
:::

Bu tarifler hâlâ soyut geliyorsa sorun değil; önündeki görevlerle
somutlaşacaklar. Sırada bu işin sahnesi var: bir sonraki bölümde
masandaki kartı tanıtıyoruz — Zynq ve ZCU111.
