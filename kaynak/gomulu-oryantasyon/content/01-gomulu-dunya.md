# Bölüm 1 — Gömülü Dünya ve Senin Rolün

Bölüm 0'da "gömülü yazılım parmak uçlarında öğrenilir" demiştik. Ama parmaklar
karta değmeden önce bir soruyu netleştirelim: sen bundan sonra tam olarak ne iş
yapacaksın? Bu bölüm büyük resmi çiziyor — gömülü sistem nedir, alıştığın
yazılım dünyasından nerede ayrılır ve bu dünyada senin masana düşen sorumluluk
nedir.

## Gömülü sistem nedir?

Gömülü sistem (embedded system), belirli bir işi yapmak üzere bir cihazın
içine gömülmüş ve çoğu zaman varlığını hiç belli etmeyen bilgisayardır.
Klavyesi yok, ekranı çoğu zaman yok, "uygulama yükle" menüsü hiç yok; tek
bir işi vardır ve onu cihazın ömrü boyunca, her gün, şikâyet etmeden yapar.

Bu sabah uyandığından beri muhtemelen onlarcasını kullandın: seni uyandıran
telefonun alarmı bir yana, kahvaltıda su ısıtıcının sıcaklık kontrolü, evden
çıkarken asansörün kat mantığı, arabanın fren pedalının arkasındaki ABS
denetleyicisi, kulağındaki Bluetooth kulaklık, öğle yemeğini ödediğin POS
cihazı ve tüm gün telefonunu ayakta tutan baz istasyonu. Hepsinin içinde
küçük ya da büyük bir işlemci ve o işlemcinin üzerinde bizim yazdığımız
türden yazılım var.

{{svg:sema-01-evren.svg|Şekil 1 — Gömülü sistem evreni: ortada sensör → MCU/SoC → aktüatör zinciri, çevresinde her gün yanından geçtiğin gömülü cihazlar.}}

Tanımın kalbi şekildeki üçlü zincir. **Sensör** dış dünyayı ölçer: sıcaklık,
basınç, buton, anten sinyali. Ortadaki **MCU** (microcontroller unit —
mikrodenetleyici) ya da daha büyük kardeşi **SoC** (system on chip — tek
çipte sistem) ölçüleni okur, karar verir. **Aktüatör** kararı dünyaya
uygular: motoru döndürür, valfi açar, LED'i yakar, anteni sürer. Senin
yazacağın kod bu döngünün tam ortasında oturur ve döngü cihaz fişte kaldığı
sürece döner.

:::analoji Çakı ve neşter
Masaüstü bilgisayar bir İsviçre çakısıdır: her işi yapabilir, hiçbirine
adanmamıştır. Gömülü sistem ise neşterdir: tek iş, ama o işte kusursuz ve
öngörülebilir olmak zorunda. Çakın takılırsa katlar cebine korsun; neşterin
ameliyatın ortasında "şimdi meşgulüm" deme lüksü yoktur.
:::

## Masaüstü yazılımdan dört büyük fark

Üniversitede yazdığın C programları bir işletim sisteminin şefkatli kollarında
çalıştı: bellek istedin verildi, ekrana yazdın göründü, program çöktü —
kimsenin canı yanmadı. Gömülü dünyada bu dört başlıkta işler değişir.

**1. Kaynak kısıtı.** Masaüstünde gigabyte'larla ölçülen RAM, gömülü dünyada
çoğu zaman kilobyte'larla ölçülür; işlemci gigahertz değil megahertz
konuşabilir. Dürüst olalım: elindeki ZCU111 bu dünyanın lüks segmentidir —
dört çekirdeği ve gigabyte'larca DDR belleği var. Ama gömülü refleks kartla
değil kafayla ilgilidir: her byte'ın ve her mikrosaniyenin hesabını yapma
alışkanlığını burada kazanacaksın, çünkü bir sonraki projende o lüks
olmayabilir.

**2. Gerçek zaman (real time).** Gömülü sistemlerde doğru cevabın geç gelmesi,
yanlış cevaptır. ABS denetleyicisi tekerleğin kilitlendiğini milisaniyeler
içinde fark edip basıncı bırakmak zorundadır; "birazdan bakarım" diye bir
seçenek yok. Bu yüzden gömülü yazılımcı yalnızca *ne* hesaplandığını değil,
*ne kadar sürede* hesaplandığını da tasarlar. Bu kavram Bölüm 7'de
(interrupt) ve Bölüm 10'da (FreeRTOS) elle tutulur hale gelecek.

**3. Donanıma yakınlık.** Masaüstünde donanımla aranda işletim sistemi,
sürücüler ve kütüphanelerden oluşan kalın bir yastık var. Gömülüde o yastık
ya incecik ya hiç yok: donanımı register (yazmaç — çevre biriminin içindeki
küçük kontrol ve durum hücreleri; Bölüm 4'ün ana konusu) seviyesinde kendin
programlarsın. Ekrana `printf` ile yazı basmak bile, senin ayağa
kaldırdığın bir UART üzerinden akar.

**4. Sorumluluk.** Masaüstü program çökerse yeniden başlatılır. Gömülü
sistemde kötü giden bir yazılım güncellemesi cihazı tuğlalaştırabilir
(brick — bir daha açılamaz hale getirmek). Üstelik cihaz sahada olabilir:
bir kulenin tepesinde, bir aracın içinde, müşterinin elinde. "Düzeltmeyi
yarın gönderirim" cümlesi, cihaza fiziksel erişim yoksa bir anlam ifade
etmez.

:::saha-notu Tuğla hikâyeleri gerçektir
Her gömülü ekibin dolabında bir tuğla hikâyesi vardır: yanlış boot imajı,
yarıda kesilen flash yazımı, "küçücük bir değişiklikti" diye test edilmeden
gönderilen sürüm. Bunu korkutmak için anlatmıyoruz — masandaki ZCU111 bir
geliştirme kartıdır, JTAG sayesinde hemen her durumdan kurtarılır ve
denemekten çekinmemen gerekir. Ama ürün kartı öyle değildir; bu yüzden bizim
dünyada asıl kural şudur: değiştirdiysen, test et.
:::

## Senin görev tanımın

Peki bu dünyada "gömülü yazılımcı" somut olarak ne yapar? Beş fiille
özetleyelim; önümüzdeki haftalarda hepsini tek tek yaşayacaksın.

- **Driver (sürücü) yazmak.** Bir çevre birimini register seviyesinde konuşup
  onu ekibin geri kalanı için temiz fonksiyonlara çevirmek:
  `uartSendChar()` yazan kişi olmak. Görev 2'de ilk driver'ını
  yazacaksın.
- **Donanımcıyla register map üzerinden konuşmak.** Register map (yazmaç
  haritası), donanımcıyla aramızdaki sözleşmedir: hangi adreste hangi bit ne
  anlama geliyor. Donanımcı FPGA'da bir IP tasarlar, sana register tablosunu
  verir; sen o tabloyu koda çevirirsin. Bu iş akışını Bölüm 9'da göreceğiz.
- **Bring-up.** Yeni bir kart ya da yeni bir IP masaya ilk geldiğinde ona ilk
  nefesini aldırmak: saat çalışıyor mu, işlemci ayağa kalkıyor mu, ilk byte
  UART'tan çıkıyor mu? Görev 0 senin ilk minik bring-up'ın olacak.
- **Debug.** Hata ayıklamak — ama ekransız, bazen printf'siz bir dünyada.
  Debugger, LED, UART ve gerektiğinde osiloskop; silah çantasını Bölüm 11'de
  açacağız.
- **Entegrasyon.** Herkesin parçası doğruyken bütünün yanlış çalıştığı o
  meşhur güne çözüm bulmak: parçaları tek sistemde birleştirmek ve arayüz
  hatalarını ayıklamak.

Bu listeyi katmanlar üzerinde gösterelim. Aşağıdaki şekilde bir gömülü
sistemin yazılım katmanları var: en altta donanım, üstünde driver'lar,
üstünde middleware (ara katman — protokol yığınları, RTOS gibi ortak
hizmetler), en üstte uygulama.

{{svg:sema-02-katmanlar.svg|Şekil 2 — Sorumluluk katmanları: gömülü yazılımcı driver ve middleware katmanlarında yaşar; masaüstü yazılımcının ayağı donanıma neredeyse hiç değmez.}}

Masaüstü yazılımcı en üst şeritte yaşar; altındaki her şeyi işletim sistemi
görünmez kılar. Biz ise ağırlıklı olarak driver ve middleware şeritlerinde
çalışırız: bir elimiz register'larda, öbür elimiz uygulamaya temiz bir arayüz
uzatır. Uygulama katmanına da çıkarız elbette — ama bizi biz yapan, alttaki
iki şeridi korkusuzca yönetebilmektir.

:::ekip-notu Bizim ekipte bir işin yaşam döngüsü
Tipik bir görev şöyle akar: (1) görevi alırsın — çoğu zaman "şu çevre birimi
için driver lazım" ya da "şu IP'yi ayağa kaldır" cümlesiyle; (2) register
map'i ve cihazın datasheet'ini okursun — kod yazmadan önce, sonra değil;
(3) driver'ı yazarsın; (4) bring-up: kod gerçek kartta ilk kez çalışır, ilk
seferde çalışmaması normaldir; (5) test edersin — başarı kriterin baştan
bellidir; (6) code review'a gönderirsin (beklentileri Bölüm 12'de
konuşacağız); (7) entegrasyon: parçan sistemin geri kalanıyla buluşur.
Fark ettiysen "kod yazmak" yedi adımdan yalnızca biri. Bu doküman da seni
tam olarak bu döngüye hazırlıyor.
:::

Bu tanımlar şu an biraz havada duruyorsa endişelenme; hepsi önümüzdeki
görevlerde elinin altında somutlaşacak. Şimdi sıra bu işleri üzerinde
yapacağın sahneyi tanımakta: bir sonraki bölümde masandaki kartla — Zynq ve
ZCU111 ile — tanışıyoruz.
