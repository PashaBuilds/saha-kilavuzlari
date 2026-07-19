# Bölüm 7 — Interrupt: Olay Gerçekleştiğinde Haber Almak

Görev 3'te SW19'u polling ile okudun: ana döngü durmaksızın
`buttonRead()` çağırıp fiilen "basıldı mı" diye
sordu. Çalıştı, ama bir bedeli vardı — ana döngünün başka işi olmadığı
için belki fark etmedin. Bu bölüm o bedeli görünür kılar ve onu ortadan
kaldıran mekanizmayı tanıtır: **interrupt** (kesme).

## Polling'in Gizli Bedeli

Görev 3'teki döngüyü, bu kez ana döngüde gerçek iş de varken düşün:
sensörden veri toplamak, UART'a telemetri yazmak, bir hesap koşturmak.
Butonu da polling ile izlemek istersen önünde iki elverişsiz seçenek
var:

- Döngünün içine sık sık `buttonRead()` çağrıları serpiştirirsin — olay
  hiç gerçekleşmese bile CPU zamanının bir kısmı "oldu mu" sorusuna
  gider; emeğin büyük bölümü boşa akar.
- Asıl işini uzun bir bloğa koyarsan (büyük bir hesap ya da uzun bir
  gecikme), o blok bitene kadar butona hiç bakmazsın — basış ânı ile
  fark edilme ânı arasına bir **gecikme** girer.

Sistem büyüyüp izlenecek "olay" sayısı arttıkça (buton basışları, timer
tick'leri, UART'tan gelen veri, I2C işlem tamamlanmaları...), polling'e
giden pay da büyür; CPU zamanının giderek artan bir bölümü "sormakla"
tükenir. {{svg:sema-14-polling-interrupt.svg|Şekil 14 — Polling ile interrupt karşılaştırması: aynı olayın iki CPU çalışma kipinde fark edilme hızı.}}

Şekildeki ayrım net: polling şeridinde CPU olayı ancak bir sonraki
sorusunda fark eder — aradaki süre kayıptır. Interrupt şeridinde CPU
asıl işine devam eder; olay gerçekleştiği anda donanım CPU'yu kendisi
böler, kısa süreliğine yönlendirir, CPU sonra kaldığı yerden sürer.

:::analoji Interrupt: kapı zili
Polling, kargonun gelip gelmediğini birkaç dakikada bir kapıya çıkıp
denetlemektir. Interrupt, kapıya zil takmaktır: kargo gelene kadar
kendi işini yaparsın; zil çaldığında — donanım seni böldüğünde — kapıya
gidersin. Zilin kendisi bir donanım parçasıdır; bizim ortamımızda o
donanımın adı **GIC**'tir.
:::

## GIC: Kesmelerin Trafik Kontrolü

ZCU111'in APU'sundaki (Cortex-A53 çekirdekleri) kesme denetleyicisi bir
**GIC-400**'dür (Generic Interrupt Controller). Onlarca çevre biriminden
gelen kesme istekleri CPU'ya doğrudan gidemez; her biri önce GIC'ten
geçer. GIC üç iş yapar:

1. **Kaynak yönlendirme:** hangi çevre biriminin kesmesi gerçekleşti ve
   hangi CPU çekirdeğine iletilmeli?
2. **Öncelik:** aynı anda birden çok kesme gerçekleşirse önce hangisi
   servis edilir?
3. **Aç/kapat:** her kesme kaynağı tek tek açılıp kapatılabilir —
   dinlemediğin bir kesme seni rahatsız etmez.

GIC-400'ün iki register bloğu vardır: `0xF901_0000` adresindeki **GICD
(distributor)**, kesme kaynaklarının önceliğini ve hedefini yönetir;
`0xF902_0000` adresindeki **GICC (CPU interface)**, koşan çekirdeğin
belirli bir kesmeyi kabul edip etmeyeceğini belirler. Xilinx sürücüsü
(`XScuGic`) iki bloğu tek bir nesnenin arkasına gizler — register'lara
doğrudan dokunman gerekmeyecek, ama GIC'in kendi register haritası olan
bir donanım parçası olduğu bilgisini aklında tut.

Her çevre biriminin GIC nezdindeki kimliği bir **kesme numarasıdır**. Bu
yolculukta üçüyle çalışacaksın:

| Çevre birimi | GIC Kesme ID'si |
|---|---|
| PS GPIO (SW19 dahil) | **48** |
| UART0 | 53 |
| TTC0 kanal 0 | **68** |

## ISR: Kısa, Keskin, Sessiz

Kesme gerçekleştiğinde CPU, senin yazdığın bir fonksiyona sıçrar: **ISR**
(Interrupt Service Routine — kesme servis rutini). Burada üç katı kural
geçerlidir:

- **Kısa tut.** ISR koşarken diğer kesmeler ya bekler (önceliğe bağlı)
  ya da kaçar. ISR'nin işi "bir şey oldu" sinyalini vermektir; işin
  kendisini yapmak değil. İyi kurulmuş bir ISR tipik olarak şunları
  yapar: bir bayrak set eder, donanımın kesme kaynağını **acknowledge**
  eder (temizler — yoksa GIC, ISR daha bitmeden aynı kesmeyi yeniden
  tetikler) ve çıkar.
- **Paylaşılan veriyi `volatile` yap.** ISR'nin yazıp ana döngünün
  okuduğu her değişken `volatile` olmalı — Bölüm 5'teki ders tam burada
  hayati hale gelir. `volatile` yoksa derleyici ana döngünün okumasını
  önbelleğe alıp bir daha güncellemeyebilir; bayrak hiç değişmiyor gibi
  görünür.
- **ISR içinde `printf`/`xil_printf` yok.** UART'a yazmak (Bölüm 4'ü
  hatırla) TX FIFO'nun dolu olma ihtimaline karşı beklemeyi içerir —
  yani ISR içindeki bir UART yazması, FIFO boşalana kadar ISR'yi
  oyalayabilir. Kısa kalması gereken bir fonksiyona süresi belirsiz bir
  bekleme sokmak, "kısa tut" kuralının doğrudan ihlalidir. Yazdırılacak
  metni ana döngüye bırak.

:::tuzak Klasik "Acknowledge Etmeyi Unuttum" Vakası
ISR'de bayrağı set edip donanımın kesme durumunu temizlemeyi
(acknowledge) unutursan, ISR'den çıkıldığı anda GIC "kesme hâlâ aktif"
deyip anında yeniden girer — sonu gelmez bir kesme fırtınası. Sistem
donmuş gibi görünür; gerçekteyse saniyede binlerce kez aynı ISR'ye
giriyordur. Acknowledge eksikliği, bu meslekte "neden hiçbir şey
ilerlemiyor" sorusunun klasik kök nedenlerindendir.
:::

{{svg:sema-15-interrupt-yasam.svg|Şekil 15 — Interrupt yaşam döngüsü: olaydan ana döngünün bayrağı işlemesine altı adım; ISR'yi kısa tutma zorunluluğu ve yanlış bir örnek vurgulanıyor.}}

## Interrupt Latency: "Anında" Ne Kadar Anında?

Interrupt, polling'den çok daha hızlı yanıt verir; ama **sıfır gecikme**
değildir. Donanımın kesmeyi GIC'e bildirmesi, GIC'in önceliklendirmesi,
CPU'nun elindeki işi askıya alıp bağlamını (context) kaydetmesi ve
ISR'ye sıçraması — hepsi birkaç mikrosaniye sürer. Buna **interrupt
latency** (kesme gecikmesi) denir. Bu yolculukta o süre hissedilemeyecek
kadar küçüktür (saniyelere varabilen polling fark etme gecikmesiyle
kıyaslanamaz bile); ama gerçek zamanlı sistemlerde bu mikrosaniyeler
bile bir tasarım kararını belirleyebilir — RPU'nun (Cortex-R5F) varoluş
nedenlerinden biri, bu gecikmeyi daha öngörülebilir kılmaktır (Bölüm
2'yi hatırla).

## Edge mi, Level mi?

Bir kesme kaynağı CPU'yu iki biçimden biriyle tetikleyebilir. **Edge
triggering** (kenar tetikleme) sinyalin değiştiği ânı yakalar (örneğin
0'dan 1'e geçiş) — bir kez ateşler; sinyal yüksekte kalsa da yeniden
ateşlemez. **Level triggering** (seviye tetikleme) sinyal belirli bir
seviyede kaldığı sürece ateşler — sen o seviyeyi ortadan kaldırana
(bayrağı temizleyene) kadar GIC kesmeyi ısrarla üretir. Buton basışı
gibi "bir kez oldu" olayları için edge doğaldır; RX FIFO'da veri
bulunması gibi "hâlâ bekleyen bir şey var" durumları için level daha
uygun olabilir. `XGpioPs_SetIntrTypePin()` fonksiyonu ikisini de
destekler; Görev 4'te SW19 için rising edge (yükselen kenar)
kullanacaksın.

## GIC'i Ayağa Kaldırma Kalıbı

Kesme tabanlı her lab'de (Görev 4, Görev 5 ve ileride Görev 8-9) aynı
kurulum dizisi tekrarlanır:

```c
XScuGic_Config* spGicConfig;
spGicConfig = XScuGic_LookupConfig(XPAR_SCUGIC_SINGLE_DEVICE_ID);
XScuGic_CfgInitialize(&G_sGic, spGicConfig, spGicConfig->CpuBaseAddress);

Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_IRQ_INT,
    (Xil_ExceptionHandler)XScuGic_InterruptHandler, &G_sGic);
Xil_ExceptionEnable();

XScuGic_Connect(&G_sGic, INTERRUPT_ID, (Xil_ExceptionHandler)myIsr, (void*)&sCallBackRef);
XScuGic_Enable(&G_sGic, INTERRUPT_ID);
```

Beş adım, hep aynı sırayla: **bul (LookupConfig) → başlat
(CfgInitialize) → CPU'nun IRQ exception'ını GIC'in genel handler'ına
bağla (Xil_ExceptionRegisterHandler) → kendi ISR'ni belirli bir kesme
ID'sine bağla (Connect) → o kesmeyi aç (Enable)**. Bu kalıbı ezberlemen
gerekmiyor — tanıyabilmen gerekiyor. Son iki satır her yeni kesme
kaynağı için tekrarlanır; ilk üçü bir kez yapılır.

Kesme mekanizmasını gördün. Sıra bunu Görev 3'teki butona uygulamakta —
ardından düzenli aralıklarla kendi kendini tetikleyen bir kesme
kaynağıyla tanışmakta: timer.

:::gorev no=4 zorluk=2 baslik="Buton Interrupt'ı" kisa="Buton Interrupt'ı"
[Hedef]
Görev 3'te polling ile okunan SW19 butonunu, GIC üzerinden bağlanan bir
GPIO kesmesine dönüştür: ana döngü kendi işiyle meşgulken buton basışı
gecikmesiz fark edilsin.

[Ön koşul]
Bölüm 7 okundu; Görev 2'deki `uart_ps` modülün (ya da bu görevin kendi
kopyası) elinde; Görev 1'den XGpioPs ile pin okuma/yazmaya aşinasın.

[Adımlar]
1. Vitis'te yeni bir bare-metal uygulama projesi aç (Görev 1-3'teki
   .xsa platformunun aynısıyla). `lab04-interrupt/src/` altındaki
   kaynakları projeye kopyala.
2. PS GPIO nesnesini başlat (`XGpioPs_CfgInitialize`); SW19'u
   (**MIO22**) giriş, DS50'yi (**MIO23**) çıkış yap — Görev 1 ve 3'te
   yaptığın kurulumun aynısı.
3. SW19 pini için kesme tipini **rising edge** yap:
   `XGpioPs_SetIntrTypePin(&G_sGpio, 22, XGPIOPS_IRQ_TYPE_EDGE_RISING)`.
4. GIC'i bu bölümdeki beş adımlık kalıpla kur; `myIsr`'yi **GPIO'nun
   kesme ID'si olan 48'e** bağla (`XScuGic_Connect` +
   `XScuGic_Enable`), ardından pin kesmesini aç:
   `XGpioPs_IntrEnablePin(&G_sGpio, 22)`.
5. ISR'yi yaz — ve KISA tut: kesmeye bu pinin yol açtığını
   `XGpioPs_IntrGetStatusPin` ile doğrula, `G_ucButtonFlag = 1` yap,
   `XGpioPs_IntrClearPin` ile acknowledge et. Başka hiçbir şey yapma —
   özellikle UART'a yazma.
6. Ana döngüde "meşgul" işi taklit et: DS50'yi düzenli aralıklarla
   yakıp söndüren basit bir sayma döngüsü (heartbeat) koştur. Her
   iterasyonda `G_ucButtonFlag`'e bak; set edilmişse basış sayacını
   artır, UART'a `"button pressed, count = N"` (butona basıldı, sayaç =
   N) satırını yaz ve bayrağı temizle.

[Başarı kriteri]
Ana döngü DS50 heartbeat'iyle "meşgulken" butona her basışta terminale
gecikmesiz yeni bir satır düşer; sayaç atlamadan, basış kaçırmadan
doğru sayar.

[Kendini sına]
- ISR'den neden `xil_printf` çağırmıyoruz? UART yazmasının içindeki ne,
  ISR'nin çalışma süresini uzatabilir?
- Ana döngü bayrağı temizlediği anda ISR yeniden ateşlerse race
  condition (yarış durumu) riski var mı? `volatile` burada tam olarak
  neye karşı korur, neye karşı KORUMAZ?
- SW19'u rising edge yerine level tetiklemeli yapsaydın ne değişirdi —
  buton basılı tutulurken ISR kaç kez çağrılırdı?

[Takıldıysan]
::ipucu İpucu 1 — Hiç Kesme Gelmiyor
Sırayı denetle: yön ayarı (giriş), `SetIntrTypePin`, `XScuGic_Connect`,
`XScuGic_Enable`, `XGpioPs_IntrEnablePin` — beşi de var mı? Biri
eksikse ya donanım kesmeyi hiç üretmez ya da GIC CPU'ya iletmez.
`Xil_ExceptionEnable()` çağrısını unutmak da aynı sessiz arızayı
üretir.
::/
::ipucu İpucu 2 — Kesme Bir Kez Geliyor, Sonra Hiç
Büyük olasılıkla acknowledge (`XGpioPs_IntrClearPin`) eksik ya da
yanlış pine yapılıyor. GIC'in de kendi "end of interrupt" adımı vardır
ama onu `XScuGic_InterruptHandler` senin yerine halleder — senin
sorumluluğun yalnızca GPIO'nun kendi durum bitini temizlemek.
::/
::cozum Tam Çözüm — lab04-interrupt
Aşağıdaki `main.c`, GPIO kesmesini GIC'e bağlar, ISR içinde yalnızca
bayrak set eder; heartbeat ile basış sayacını ana döngüde yönetir.
{{kod:lab04-interrupt/src/main.c}}
::/
:::

:::gorev no=5 zorluk=2 baslik="Timer ile Heartbeat" kisa="Timer Heartbeat"
[Hedef]
TTC0 kanal 0'ı 1 Hz periyodik kesme üretecek şekilde kur; her tick'te
UART'a bir satır yazdır ve DS50'yi heartbeat deseninde sür — tamamı
kesme güdümlü, ana döngüde bekleme yok.

[Ön koşul]
Görev 4 tamamlandı (GIC kurulum kalıbı elinde); Bölüm 7'nin TTC/interval
kısmı okundu.

[Adımlar]
1. `lab05-timer/src/` altındaki kaynakları yeni bir bare-metal projeye
   kopyala.
2. `XTtcPs` nesnesini TTC0 kanal 0 üzerinde başlat
   (`XTtcPs_LookupConfig` + `XTtcPs_CfgInitialize`, taban adres
   **0xFF11_0000**); sayacı "interval mode"a al (`XTtcPs_SetOptions`).
3. **1 Hz için interval değerini hesapla:**
   `Interval = (XPAR_XTTCPS_0_CLOCK_HZ / 1) - 1`. Bu makro,
   platformunun gerçek TTC giriş saatini taşır — `xparameters.h`'den
   oku; burada elle seçilmiş bir MHz değeri varsayma. Değeri
   `XTtcPs_SetInterval` ile yaz.
4. Kesmeyi aç:
   `XTtcPs_EnableInterrupts(&G_sTtc, XTTCPS_IXR_INTERVAL_MASK)`. GIC'i
   Görev 4'teki beş adımlık kalıpla kur; bu kez **kesme ID'si 68**
   (TTC0 kanal 0).
5. Sayacı `XTtcPs_Start` ile başlat. ISR'de yalnızca `G_ucTickFlag = 1`
   yap ve durumu `XTtcPs_InterruptHandler` üzerinden (ya da ISR bitini
   doğrudan okuyarak) acknowledge et.
6. `main()` döngüsünde bayrağı görünce: tick sayacını artır, UART'a
   `"tick N"` yaz ve DS50'yi toggle et — heartbeat etkisini yaratan
   budur.

[Başarı kriteri]
Terminal, saniyede tam olarak bir "tick N" satırı basar; DS50 gözle
görülür, düzenli bir heartbeat ritmiyle yanıp söner.

[Kendini sına]
- Kendi platformundaki `XPAR_XTTCPS_0_CLOCK_HZ` değerini bul ve
  interval hesabını (bölme artı çıkarma) kağıt üstünde elle tekrarla —
  kodun hesapladığıyla tutuyor mu?
- Interval değerini yanlışlıkla iki katına çıkarsaydın (örneğin
  `-1`'i unutmak gibi bir hatayla değil, düpedüz iki katını yazarak),
  tick hızı hangi yöne ve ne kadar değişirdi?
- Prescaler'ı hiç kullanmadık — 32 bitlik interval register'ı bunu
  neden gereksiz kıldı? Çok daha düşük bir tick frekansında (örneğin
  0.001 Hz) da böyle olur muydu?

[Takıldıysan]
::ipucu İpucu 1 — Hiç Tick Gelmiyor ya da Tek Tick, Sonrası Yok
`XTtcPs_Start` çağrısını ya da "interval mode" seçeneğini
(`XTTCPS_OPTION_INTERVAL_MODE`) unutmak yaygın bir hatadır — kip
ayarlanmazsa sayaç, interval'i geçip serbestçe saymaya devam edebilir
ve kesme üretmez.
::/
::ipucu İpucu 2 — Hız Yanlış (Tick Çok Hızlı ya da Çok Yavaş)
`XPAR_XTTCPS_0_CLOCK_HZ` makrosunun gerçek değerini `xparameters.h`'de
bul ve hesabı elle doğrula; interval hesabındaki `-1`'i unutmak tick
periyodunu gözle fark edilir ölçüde kaydırmaz, ama düz bir aritmetik
hata (yanlış makro, yanlış birim) genellikle büyük sapma yaratır.
::/
::cozum Tam Çözüm — lab05-timer
{{kod:lab05-timer/src/main.c}}
::/
:::
