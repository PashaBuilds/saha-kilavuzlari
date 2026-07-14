# Bölüm 7 — Interrupt: Olay Geldiğinde Haber Ver

Görev 3'te SW19'u polling (sürekli sorgulama) ile okudun: ana döngü durmadan
`buttonRead()`'yu çağırıp "basılı mı, basılı mı, basılı mı" diye sordu.
Çalıştı, ama bir bedeli vardı — belki fark etmedin çünkü ana döngüde başka
iş yoktu. Şimdi o bedeli açık edelim ve ondan kurtulmanın yolunu öğrenelim:
**interrupt (kesme)**.

## Polling'in gizli faturası

Görev 3'ün döngüsünü hayal et ama bu sefer ana döngüde gerçek bir iş de
olsun: bir sensörden veri topluyor, UART'a telemetri basıyor, bir hesap
yapıyorsun. Butonu da polling ile izlemek istersen iki kötü seçeneğin var:

- Döngüye sık sık `buttonRead()` serpiştirirsin — CPU zamanının bir
  kısmı, olay hiç olmasa bile, "olmuş mu?" diye sormaya gider. Bu, hiç
  gelmeyecek bir misafiri her on saniyede bir kapıya çıkıp beklemeye
  benzer: yorucu ve çoğu zaman boşuna.
- Asıl işini uzun bir bloğun içine yazarsan (örneğin büyük bir hesap veya
  uzun bir gecikme), o blok bitene kadar butonu hiç sormazsın — basılma
  anı ile fark ediş anı arasına bir **gecikme** girer.

Sistem büyüdükçe, izlenecek "olay" sayısı arttıkça (buton, zamanlayıcı,
UART'tan gelen veri, I2C tamamlanması...) polling'in payı da büyür; CPU'nun
gitgide daha fazla zamanı "sormakla" geçer. {{svg:sema-14-polling-interrupt.svg|Şekil 14 — Polling ve interrupt karşılaştırması: aynı olayı fark etme hızı iki CPU çalışma biçiminde.}}

Şekildeki fark nettir: polling şeridinde CPU olayı ancak bir sonraki
sorgusunda fark eder — aradaki süre kayıp zamandır. Interrupt şeridinde CPU
asıl işini yapmaya devam eder; olay geldiği anda donanımın kendisi CPU'yu
keser, kısa bir sapma yaptırır, sonra CPU kaldığı yerden devam eder.

:::analoji Kapıda beklemek yerine zil
Polling, gelecek kargoyu merak edip her birkaç dakikada bir kapıya çıkıp
bakmaktır. Interrupt, zili olan bir kapıdır: kargo gelene kadar sen işine
bakarsın, zil çaldığında (donanım seni keser) kapıya gidersin. Zilin kendisi
bir donanım — bizim dünyamızda bu donanımın adı **GIC**.
:::

## GIC: kesmelerin trafik polisi

ZCU111'in APU'sundaki (Cortex-A53 çekirdekleri) kesme denetleyicisi bir
**GIC-400** (Generic Interrupt Controller — genel kesme denetleyicisi). Onlarca
çevre biriminin kesme talebi doğrudan CPU'ya gidemez; hepsi önce GIC'e uğrar.
GIC üç işi üstlenir:

1. **Kaynak yönlendirme:** hangi çevre biriminin kesmesi geldi, hangi CPU
   çekirdeğine gönderilsin?
2. **Öncelik:** aynı anda birden fazla kesme gelirse hangisi önce işlenir?
3. **Enable/disable:** her kesme kaynağı ayrı ayrı açılıp kapatılabilir —
   dinlemediğin bir kesme seni rahatsız etmez.

GIC-400'ün iki register bloğu var: **GICD (dağıtıcı — distributor)**
`0xF901_0000` adresinde, kesme kaynaklarının önceliğini ve hedefini
yönetir; **GICC (CPU arayüzü)** `0xF902_0000` adresinde, çalışan
çekirdeğin kesmeyi kabul edip etmeyeceğini yönetir. Xilinx sürücüsü
(`XScuGic`) bu iki bloğu senin için tek bir nesne arkasında saklar —
register'ları elle karıştırman gerekmez, ama "GIC bir donanım, o da bir
register haritası" bilgisi elinde kalsın.

Her çevre biriminin GIC'teki kimliği bir **kesme numarasıdır**. Bu
yolculukta üç tanesiyle çalışacaksın:

| Çevre birimi | GIC kesme ID |
|---|---|
| PS GPIO (SW19 dahil) | **48** |
| UART0 | 53 |
| TTC0 kanal 0 | **68** |

## ISR: kısa, keskin, sessiz

Kesme geldiğinde CPU, senin yazdığın bir fonksiyona sıçrar: **ISR**
(Interrupt Service Routine — kesme işleyicisi). Burada üç katı kural var:

- **Kısa tut.** ISR çalışırken (önceliğine göre) başka kesmeler bekler ya
  da kaçar. ISR'nin işi "bir şey oldu" demek, işin kendisini yapmak değil.
  Tipik iyi bir ISR: bayrağı set et, donanımın kesme kaynağını **ack'le**
  (onayla/temizle — yoksa GIC aynı kesmeyi bitmeden tekrar tetikler), çık.
- **Paylaşılan veriye `volatile`.** ISR'nin yazıp ana döngünün okuduğu her
  değişken `volatile` olmalı — Bölüm 5'teki dersin tam burada hayat
  kurtardığı yer. `volatile` olmazsa derleyici ana döngüdeki okumayı
  önbelleğe alıp bir daha güncellemeyebilir; bayrak hiç değişmemiş gibi
  görünür.
- **ISR'de `printf`/`xil_printf` YOK.** UART'a yazmak (Bölüm 4'ü hatırla)
  TX FIFO dolu olabilir diye beklemeyi içerir — yani ISR içinde UART'a
  yazmak, ISR'yi FIFO boşalana kadar dondurabilir. Kısa tutulması gereken
  bir fonksiyonun içine belirsiz süreli bir bekleme koymak, "kısa tut"
  kuralının doğrudan ihlalidir. Basılacak metni ana döngüye bırak.

:::tuzak "Ack'lemeyi unuttum" klasiği
ISR'de bayrağı set edip donanımın kesme durumunu temizlemeyi (ack)
unutursan, ISR'den çıkar çıkmaz GIC "kesme hâlâ aktif" der ve seni anında
tekrar ISR'ye sokar — sonsuz bir kesme fırtınası. Sistem donmuş gibi
görünür ama aslında saniyede binlerce kez aynı ISR'ye giriyordur. Ack
satırını unutmak, bu meslekte "neden hiçbir şey ilerlemiyor" sorularının
klasik köküdür.
:::

{{svg:sema-15-interrupt-yasam.svg|Şekil 15 — Kesme yaşam döngüsü: olaydan ana döngünün bayrağı işlemesine altı adım; ISR'nin kısa tutulması gerektiği ve yanlış bir örnek vurgulanır.}}

## Interrupt latency: "anında" ne kadar anında?

Interrupt, polling'e göre çok daha hızlı tepki verir ama **sıfır gecikme**
değildir. Donanımın kesmeyi GIC'e iletmesi, GIC'in önceliklendirmesi, CPU'nun
o anki işini durdurup bağlamını kaydetmesi, ISR'ye atlaması — hepsi birkaç
mikrosaniye sürer. Buna **interrupt latency** (kesme gecikmesi) denir. Bizim
yolculuğumuzda bu süre gözle görülmeyecek kadar küçüktür (polling'in
saniyelerce sürebilen fark ediş gecikmesiyle kıyaslanmayacak kadar), ama
gerçek zamanlı sistemlerde bu mikrosaniyeler bile tasarım kararı
gerektirebilir — RPU'nun (Cortex-R5F) var olma sebeplerinden biri de bu
gecikmeyi daha öngörülebilir kılmaktır (Bölüm 2'yi hatırla).

## Edge mi, level mi?

Bir kesme kaynağı CPU'yu iki şekilde tetikleyebilir: **edge (kenar)
tetikleme** sinyalin değiştiği anı yakalar (örneğin 0'dan 1'e geçiş) — bir
kez tetikler, sinyal yüksekte kalsa bile tekrar tetiklemez. **Level
(seviye) tetikleme** sinyal belirli bir seviyedeyken sürekli tetikler —
sen o seviyeyi kaldırana kadar (bayrağı temizleyene kadar) GIC ısrarla
kesme gönderir. Buton gibi "bir kez oldu" olaylarında edge doğaldır;
"bir şey hâlâ bekliyor" durumlarında (örn. RX FIFO'da veri var) level daha
uygun olabilir. `XGpioPs_SetIntrTypePin()` fonksiyonu ikisini de destekler;
Görev 4'te SW19 için yükselen kenar (rising edge) kullanacaksın.

## GIC'i devreye almanın deseni

Her interrupt lab'ında (Görev 4, 5 ve ileride 8-9'da) tekrar edecek sabit
bir kurulum sırası var:

```c
XScuGic_Config* spGicConfig;
spGicConfig = XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
XScuGic_CfgInitialize(&G_sGic, spGicConfig, spGicConfig->CpuBaseAddress);

Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
    (Xil_ExceptionHandler)XScuGic_InterruptHandler, &G_sGic);
Xil_ExceptionEnable();

XScuGic_Connect(&G_sGic, KESME_ID, (Xil_ExceptionHandler)benimIsr, (void*)&sCallBackRef);
XScuGic_Enable(&G_sGic, KESME_ID);
```

Beş adım, hep aynı sırayla: **bul (LookupConfig) → başlat (CfgInitialize)
→ CPU'nun IRQ istisnasını GIC'in genel işleyicisine bağla
(Xil_ExceptionRegisterHandler) → senin ISR'ini belirli bir kesme ID'sine
bağla (Connect) → o kesmeyi aç (Enable)**. Bu deseni ezberlemene gerek yok;
tanımasına ihtiyacın var — her yeni kesme kaynağında son iki satır tekrar
eder, ilk üçü bir kez yapılır.

Kesme mekanizmasını gördün. Şimdi onu Görev 3'ün butonuna uygulama sırası —
sonra da düzenli aralıklarla kendi kendine tetiklenen bir kesme kaynağıyla,
zamanlayıcıyla tanışma sırası.

:::gorev no=4 zorluk=2 baslik="Buton Interrupt'ı" kisa="Buton Kesmesi"
[Hedef]
Görev 3'ün polling ile okuduğu SW19 butonunu GIC üzerinden bağlanan bir
GPIO kesmesine dönüştür: ana döngü kendi işiyle meşgulken buton basımı
gecikmesiz fark edilsin.

[Ön koşul]
Bölüm 7 okundu; Görev 2'nin `uart_ps` modülü (ya da bu görevin kendi
kopyası) elinde; XGpioPs ile pin okuma/yazmaya Görev 1'den aşinasın.

[Adımlar]
1. Vitis'te yeni bir bare-metal uygulama projesi aç (platform Görev 1-3 ile
   aynı .xsa). `lab04-kesme/src/` altındaki kaynakları projeye kopyala.
2. PS GPIO nesnesini başlat (`XGpioPs_CfgInitialize`), SW19 (**MIO22**)
   giriş, DS50 (**MIO23**) çıkış olacak şekilde yönlerini ayarla — Görev 1
   ve 3'te yaptığın kurulumun aynısı.
3. SW19 pini için kesme türünü **yükselen kenar** yap:
   `XGpioPs_SetIntrTypePin(&G_sGpio, 22, XGPIOPS_IRQ_TYPE_EDGE_RISING)`.
4. GIC'i bu bölümdeki beşli desenle kur; `benimIsr`'i **GPIO'nun kesme
   ID'si olan 48**'e bağla (`XScuGic_Connect` + `XScuGic_Enable`), sonra
   pin kesmesini aç: `XGpioPs_IntrEnablePin(&G_sGpio, 22)`.
5. ISR'yi yaz — ve onu KISA tut: `XGpioPs_IntrGetStatusPin` ile bu pinin
   kestiğini doğrula, `G_ucButtonFlag = 1` yap, `XGpioPs_IntrClearPin` ile
   ack'le. Başka hiçbir şey yapma — özellikle UART'a yazma.
6. Ana döngüde "meşgul" bir iş simüle et: DS50'yi belirli aralıklarla
   yakıp söndüren basit bir sayaç döngüsü (heartbeat) çalıştır. Her
   turda `G_ucButtonFlag`'ni kontrol et; set görürsen basış sayacını
   artır, UART'a `"buton basildi, sayac = N"` yaz, bayrağı sıfırla.

[Başarı kriteri]
Ana döngü DS50 heartbeat'iyle "meşgulken" butona her bastığında terminalde
gecikmesiz yeni bir satır görünüyor; sayaç basış sayısını sekmeden,
kaçırmadan artırıyor.

[Kendini sına]
- ISR'de neden `xil_printf` çağırmıyoruz? UART yazmanın içinde ISR'yi
  uzatacak ne var?
- Bayrağı ana döngüde sıfırlarken ISR tam o anda tekrar tetiklenirse bir
  yarış (race) riski var mı? `volatile`'ın burada koruduğu şey tam olarak
  ne, koruMADIĞI şey ne?
- SW19'u yükselen kenar yerine seviye (level) tetiklemeli kursaydın ne
  değişirdi — buton basılı tutulduğunda ISR kaç kez çağrılırdı?

[Takıldıysan]
::ipucu İpucu 1 — Kesme hiç gelmiyor
Sıra kontrolü yap: yön ayarı (giriş), `SetIntrTypePin`, `XScuGic_Connect`,
`XScuGic_Enable`, `XGpioPs_IntrEnablePin` — beşi de eksiksiz mi? Bir tanesi
eksikse donanım kesmeyi hiç üretmez ya da GIC onu CPU'ya hiç iletmez.
`Xil_ExceptionEnable()` çağrısını unutmak da aynı sessiz sonucu verir.
::/
::ipucu İpucu 2 — Kesme bir kez geliyor, sonra hiç gelmiyor
Büyük ihtimalle ack (`XGpioPs_IntrClearPin`) eksik ya da yanlış pine
yapılıyor. GIC'in kendi tarafında da bir "end of interrupt" adımı vardır
ama `XScuGic_InterruptHandler` bunu senin için hallediyor — sen sadece
GPIO'nun kendi durum bitini temizlemekle yükümlüsün.
::/
::cozum Tam çözüm — lab04-kesme
Aşağıdaki `main.c`, GPIO kesmesini GIC'e bağlar, ISR'de yalnızca bayrak
set eder, ana döngüde heartbeat ve basış sayacını yönetir.
{{kod:lab04-kesme/src/main.c}}
::/
:::

:::gorev no=5 zorluk=2 baslik="Timer ile Kalp Atışı" kisa="Timer Kalp Atışı"
[Hedef]
TTC0 kanal 0'ı 1 Hz periyodik kesme üretecek şekilde kur; her tikte
UART'a bir satır bas ve DS50'yi kalp atışı gibi çalıştır — tamamen
kesme tabanlı, ana döngüde bekleme yok.

[Ön koşul]
Görev 4 tamamlandı (GIC kurulum deseni elinde); Bölüm 7'nin TTC/interval
bölümü okundu.

[Adımlar]
1. `lab05-timer/src/` kaynaklarını yeni bir bare-metal projeye kopyala.
2. `XTtcPs` nesnesini TTC0 kanal 0 üzerinde başlat (`XTtcPs_LookupConfig`
   + `XTtcPs_CfgInitialize`, taban adres **0xFF11_0000**); sayacı
   "interval mode"a al (`XTtcPs_SetOptions`).
3. **1 Hz için interval değerini hesapla:**
   `Interval = (XPAR_XTTCPS_0_CLOCK_HZ / 1) - 1`. Bu makro senin
   platformunun gerçek TTC giriş saatini taşır — `xparameters.h`'tan
   oku, burada elle bir MHz rakamı varsaymıyoruz. `XTtcPs_SetInterval`
   ile yaz.
4. Kesmeyi aç: `XTtcPs_EnableInterrupts(&G_sTtc, XTTCPS_IXR_INTERVAL_MASK)`.
   GIC'i Görev 4'teki beşli desenle kur; bu sefer **kesme ID'si 68**
   (TTC0 kanal 0).
5. `XTtcPs_Start` ile sayacı çalıştır. ISR'de sadece `G_ucTickFlag = 1`
   yap ve `XTtcPs_InterruptHandler` (ya da doğrudan ISR biti okuma)
   ile durumu ack'le.
6. `main()` döngüsünde bayrağı gördüğünde: tik sayacını artır, UART'a
   `"tick N"` bas, DS50'yi tersine çevir (toggle) — kalp atışı hissi
   burada oluşur.

[Başarı kriteri]
Terminalde saniyede tam bir "tick N" satırı akıyor; DS50 gözle görülür,
düzenli bir kalp atışı ritmiyle yanıp sönüyor.

[Kendini sına]
- `XPAR_XTTCPS_0_CLOCK_HZ` değerini kendi platformunda bulup, elle
  interval hesabını (bölme + çıkarma) kâğıt üzerinde tekrar yap — kod
  bulduğun sonuçla eşleşiyor mu?
- Interval değerini yanlışlıkla iki katına çıkarsaydın (örn. `-1`
  yazmayı unutsaydın) tik hızı ne yönde değişirdi, ne kadar?
- Prescaler'ı hiç kullanmadık — 32-bit'lik interval yazmacı bunu neden
  gereksiz kıldı? Çok daha düşük bir tik frekansında (örn. 0.001 Hz)
  aynı şey geçerli olur muydu?

[Takıldıysan]
::ipucu İpucu 1 — Tik hiç gelmiyor ya da bir kere gelip duruyor
`XTtcPs_Start` çağrısını unutmak ya da "interval mode" seçeneğini
(`XTTCPS_OPTION_INTERVAL_MODE`) atlamak sık rastlanan hatadır — mode
ayarlanmazsa sayaç interval'e ulaşınca kesme üretmeden serbestçe saymaya
devam edebilir.
::/
::ipucu İpucu 2 — Hız yanlış (çok hızlı/çok yavaş tik)
`XPAR_XTTCPS_0_CLOCK_HZ` makrosunun gerçek değerini `xparameters.h`
içinde ara ve hesabı elle doğrula; interval hesabında `-1` unutmak da
tik süresini gözle fark edilecek kadar kaydırmaz ama saf bir aritmetik
yazım hatası (yanlış makro, yanlış birim) genelde büyük sapmaya yol açar.
::/
::cozum Tam çözüm — lab05-timer
{{kod:lab05-timer/src/main.c}}
::/
:::
