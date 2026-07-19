# Bölüm 4 — Register'lar: Donanımla Konuşmanın Dili

Bellek haritasını gördün: her şeyin bir adresi var. Bu bölümde o
adreslerin arkasında ne olduğunu öğreneceksin — **register'lar**.
Register, donanımın CPU ile konuştuğu küçük bir kutudur; bu bölümün
sonunda bir register map dokümanını okuyup yorumlayabilecek ve gerçek
bir donanım parçasına kendi kodunla karşılık verdireceksin.

## Memory-Mapped I/O: Adres Aslında Bir Kapıdır

**Memory-mapped I/O** (bellek eşlemeli giriş/çıkış), bir çevre biriminin
register'larının tıpkı RAM'deki bir değişken gibi bellek adresi
üzerinden okunup yazılabilmesi demektir. Başka deyişle `0xFF0A0040`
adresine `1` yazmak ile `myCounter = 1;` yazmak CPU açısından neredeyse
aynı işlemdir — fark şudur: adres RAM'e değil bir GPIO denetleyicisine
bağlıdır ve yazdığın anda gerçek dünyada fiziksel bir pin seviye
değiştirir.

{{svg:sema-07-adres-kapi.svg|Şekil 7 — "Adres = kapı numarası": bir okuma/yazma işleminin CPU'dan adres yolu üzerinden çevre birimi register'ına giden yolu.}}

Durum, sokak adresi bulmaya benzer: CPU adres yoluna
bir "kapı numarası" (adres) koyar, o numaradaki "bina" (çevre birimi)
cevap verir. `0xFF00_0000` numaralı kapıyı çalarsan UART0 açar;
`0xFF0A_0000` numaralı kapıyı çalarsan GPIO açar. Yanlış numara
yazarsan ya kimse cevap vermez ya da hiç beklemediğin biri verir.

## Register'ın İçi: Bit Alanları ve Erişim Tipleri

Her register 32 bitlik bir kutudur ve her bit (ya da bit grubu) ayrı bir
anlam taşır. UART'ın SR (Channel Status) register'ında bit 4 = TXFULL
(gönderim FIFO'sunun — First In First Out, donanımın veriyi geçici
olarak sıralı tuttuğu tampon — dolu olup olmadığı), bit 1 = RXEMPTY
(alım FIFO'sunun boş olup olmadığı) vb.

{{svg:sema-08-register-bit.svg|Şekil 8 — 32 bitlik bir register'ın bit alanları anatomisi: UART SR'den TXFULL/TXEMPTY/RXFULL/RXEMPTY bitleri vurgulu; altta R/W, RO ve W1C rozetleri.}}

Bit alanlarının yanı sıra her register'ın bir de **erişim tipi** vardır.
Üçüyle sık karşılaşacaksın:

- **R/W (Read/Write):** Sıradan bir değişken gibi hem okunur hem
  yazılır. CR (0x00) böyledir — TX/RX'i etkinleştirmek için ona
  yazarsın.
- **RO (Read-Only):** Yalnızca okunur; donanım günceller, sen
  yazamazsın. SR (0x2C) böyledir — TX FIFO'nun dolu olup olmadığını
  donanıma *sorarsın*, donanıma bunu *söylemezsin*.
- **W1C (Write-1-to-Clear):** İlk bakışta kafa karıştırabilen
  alışılmadık bir desen. Bu register'da bir bite 1 yazmak o biti
  **temizler**; 0 yazdığın bitler olduğu gibi kalır. ISR (0x14) böyle
  çalışır: bir interrupt bayrağını temizlemek için o bite 1 yazarsın —
  0 yazmak hiçbir şey yapmaz. Yani buradaki "temizle" fiili "1 yaz"
  demektir; sezgiye aykırıdır ama gömülü sistemlerde çok yaygın bir
  desendir.

Bölüm 5'te bu bitleri mask'lerle okuyup yazmayı öğreneceksin; şimdilik
doğru adlarıyla tanıman yeter.

## Register Map Dokümanı Okumak

Donanım tasarımcıları (ya da Xilinx) her çevre birimi için bir
**register map** dokümanı yayımlar: hangi register hangi **offset**'te
(taban adresten uzaklık) oturur, enerji sonrası **reset değeri** nedir
ve az önce öğrendiğin **erişim tipi** hangisidir. ZynqMP UART'ının
gerçek register map'inden küçük bir kesit:

{{svg:sema-09-register-map-okuma.svg|Şekil 9 — Register map dokümanı okuma dersi: UART register tablosu üzerinde offset/erişim/reset açıklamaları.}}

| Register | Offset | Erişim | Reset | Açıklama |
|---|---|---|---|---|
| CR (Control) | 0x00 | R/W | 0x00000128 | TX/RX etkinleştirme, reset bitleri |
| MR (Mode) | 0x04 | R/W | 0x00000000 | Baud kaynağı, veri/stop bit sayısı |
| SR (Channel Status) | 0x2C | RO | — | TX/RX FIFO durumu (TXFULL, RXEMPTY...) |
| ISR (Interrupt Status) | 0x14 | **W1C** | 0x00000000 | Interrupt bayrakları |

Dört sütunun dördü de kritiktir: **offset**, taban adrese eklenecek
sayıdır; **erişim**, register'la ne yapabileceğini söyler; **reset
değeri**, karta güç verildiği anda register'da ne bulacağını söyler;
**açıklama**, register'ın ne işe yaradığını. Bunları okumadan kod
yazmak, bir cihazı kılavuzunu okumadan devreye almaya benzer — bazen
tutar, çok daha sık saatlerine mal olur.

## Taban Adres + Offset Aritmetiği

Bir register'ın gerçek adresi tek formülden çıkar:

```metin
actual_address = base_address + offset
```

Örnek: GPIO denetleyicisinin taban adresi `0xFF0A_0000`. Bank 0'ın veri
register'ı (DATA_0) offset `0x40`'ta. Gerçek adres:
`0xFF0A_0000 + 0x40 = 0xFF0A_0040`. Bu toplamayı her seferinde elle
yapman gerekmez — birazdan göreceğin gibi driver fonksiyonları ya da
hazır sabitler senin yerine yapar — ama formülün kendisini anlamadan
register map okumak mümkün değildir.

:::tuzak Offset'i Taban Adresle Karıştırmak
Register map dokümanları çoğu zaman yalnızca offset'i verir (`0x2C`
gibi), taban adresi ayrı bir tabloda tutar. İkisini karıştıran bir
satır — doğrudan `0x2C`'ye yazmak ya da UART1'in taban adresini UART0
koduna kopyalamak — derlenir, çalışıyor görünür ve seni yanlış çevre
birimini programlarken bırakır. Herhangi bir register adresini
kullanmadan önce kendine sor: "bu hangi taban adres artı hangi offset?"
:::

## xparameters.h: Adresi Elle Yazmıyoruz

Peki bu taban adresleri kodda nereden bulacaksın? Elle yazmazsın —
Vitis, donanım tanımından (.xsa) **`xparameters.h`** başlık dosyasını
otomatik üretir; her çevre biriminin adresi, interrupt numarası ve
kimliği burada hazır sabit olarak durur. Adlandırma iki Vitis akışı
arasında biraz farklıdır:

- **Klasik akış** (Vitis Classic, 2023.1 ve öncesi): her aygıt bir
  **DEVICE_ID** ile tanınır, örn. `XPAR_XUARTPS_0_DEVICE_ID`. Bu
  kimliği driver'ın `LookupConfig` fonksiyonuna verirsin; fonksiyon
  taban adresi içeren yapılandırma yapısını döndürür.
- **SDT akışı** (System Device Tree — Vitis Unified IDE'nin kullandığı
  güncel yöntem): aygıtlara doğrudan taban adresle atıf yapılır, örn.
  `XPAR_XUARTPS_0_BASEADDR`. Bu durumda `LookupConfig` parametre olarak
  adresin kendisini alır.

İkisinde de temel mantık aynıdır: **adresi elle yazma — üretilen
başlıktan al.** Elle yazılmış adres, donanım tasarımı değiştiğinde (ya
da kod başka projeye taşındığında) sessizce yanlışlaşır;
`xparameters.h`'ten gelen sabit ise donanımla birlikte kendiliğinden
güncellenir.

## Somut Örnek: UART0'dan Karakter Göndermek

Şimdi tüm bu kavramları tek bir somut işleme bağlayalım: 'A'
karakterini UART0 (`0xFF00_0000`) üzerinden register düzeyinde
göndermek. Driver fonksiyonlarının arkasında olan tam olarak şudur:

1. **SR register'ını oku** (taban + `0x2C`).
2. **TXFULL bitini kontrol et** (mask `0x10`). Bit 1 ise gönderim
   FIFO'su doludur — yer açılana kadar bu adımı tekrarla (bu, Bölüm
   6'da tanışacağın "polling" deseninin ta kendisidir; maliyeti ve
   interrupt'la karşılaştırması Bölüm 7'de).
3. TXFULL sıfırlanınca **'A' karakterinin ASCII değerini** FIFO
   register'ına yaz (taban + `0x30`).

Gerisini donanım devralır: karakteri fiziksel TX pininden seri olarak
dışarı aktarır. Bu üç adım — durumu oku, bekle, yaz — gömülü
sistemlerde sayamayacağın kadar çok karşına çıkacak bir desendir.

Yeterince teori biriktirdin. İlk görevin, bu bölümdeki register
mantığını gerçek bir LED'e uygulamak — ama önce görevde kullanacağın
aracı kısaca tanıman gerekiyor.

## Vitis'e İlk Bakış: Proje Açmak, Derlemek, Karta Yüklemek

Vitis'i ilk kez birazdan, Görev 1'de açacaksın; karşılaştığında
yabancılık çekmemen için tıklama sırasını önceden tarif edelim. Vitis'in
ne olduğu, BSP (board support package — kart destek paketi) kavramı,
debugger, Run/Debug yapılandırmaları ve disassembly Bölüm 11'de tüm
derinliğiyle ele alınır — burada anlatılan yalnızca tıklama sırasının
kendisidir; şimdilik her adımın ne yaptığını bilerek tıklaman yeter.

İlk açılışta Vitis senden bir **workspace** (çalışma alanı) seçmeni
ister: projelerini, ayarlarını ve derleme çıktılarını tutan bir klasör.
Workspace açıldıktan sonra ilk iş, ekibin senin için hazırladığı
platformu seçmektir — platform, donanım tanımını taşıyan bir .xsa
dosyasından türetilir; platformu sen tasarlamazsın, donanım tasarımcısı
tasarlar, sen listeden seçersin.

Platform seçiliyken yeni bir **empty application** projesi açarsın:
"empty application" şablonu örnek kod getirmez — sıfırdan doldurduğun
bir iskelet verir ve bu yolculuk boyunca hemen her zaman seçeceğin
şablon budur. Vitis bu projeyi seçtiğin platforma otomatik bağlar ve
hangi işlemci çekirdeğinde çalışacağını sorar (bu yolculuk boyunca hemen
her zaman APU'nun Cortex-A53 çekirdeklerinden biri olacak).

Proje açıldıktan sonra kaynak dosyalarını projenin `src/` klasörüne
koyarsın — bir göreve geldiğinde çözüm dosyasını oraya kopyalayacak
olman tam da bundandır. Ardından **Build** düğmesine basarsın; hata
varsa Console/Problems panelinde kırmızı satırlar olarak görürsün,
derleme temizse çalıştırılabilir çıktı üretilir ve proje ağacında yeni
bir Debug/Release klasörü belirir.

Derleme temizlenince sıra karta yüklemededir: projeye sağ tıkla,
**Run As → Launch on Hardware (JTAG)**. Vitis karta JTAG üzerinden
bağlanır, derlediğini yükler ve çalıştırır; kartta bir LED yanıp
sönmeye başlar ya da Görev 0'da açtığın terminalde bir satır belirir —
kodunun karta gerçekten ulaştığının kanıtı budur.

Bu sıra — workspace, platform seç, boş proje aç, kodu `src/`e koy,
Build, Run As → Launch on Hardware — Görev 1'den Görev 10'a kadar
defalarca elinden geçecek. İlk seferinde adım adım oku; birkaç görev
sonra elin ezberleyecek.

:::gorev no=1 zorluk=1 baslik="LED Yak (Merhaba Donanım)" kisa="LED Yak"
[Hedef]
Vitis'te bare-metal bir uygulamayı derle, karta yükle ve DS50 LED'ini
(PS MIO23) 500 ms periyotla (500 ms yanık / 500 ms sönük) yakıp
söndür.

[Ön koşul]
Bölüm 3 ve 4 okundu; Görev 0 tamamlandı (kart JTAG modunda, terminal
bağlantısı hazır).

[Adımlar]
1. Vitis'te ekibinin sağladığı hazır **platformu** (donanım tanımı,
   .xsa) seç — platform/uygulama projesi ilişkisini Bölüm 11'de tam
   olarak inceleyeceğiz; şimdilik "donanımın tarifi" olarak düşün.
2. Yeni bir **empty application** projesi aç ve seçtiğin platforma
   bağla.
3. Bu görevin çözüm dosyası `lab01-led/src/main.c`'yi projenin `src/`
   klasörüne kopyala.
4. Projeyi **Build** et.
5. **JTAG üzerinden karta yükleyip çalıştır** (Run As → Launch on
   Hardware). JTAG/debug ayrıntılarına Bölüm 11'de adım adım gireceğiz;
   şimdilik bu beş adım yeter.
6. (isteğe bağlı) UART terminalini Görev 0'daki ayarlarla aç ve
   "Task 1" satırının basıldığını doğrula.

   :::derin-dalis Aynı İşi Doğrudan Register'larla Yapmak
   `XGpioPs_WritePin` gibi driver fonksiyonları, Bölüm 4'te öğrendiğin
   taban+offset aritmetiğini ve read-modify-write işlemini senin yerine
   yapar. Bu çağrıların arkasında ne olduğunu görmek istersen, aynı
   LED'i `volatile` bir pointer üzerinden (volatile — derleyici bu
   adresi her erişimde gerçekten okumalı/yazmalı; ayrıntısı Bölüm 5'te)
   doğrudan yakan alternatif çözüm aşağıda; `content/_arastirma-ek-B.md`
   içinde kaynaklarıyla doğrulanmış DIRM_0, OEN_0 ve DATA_0 register
   offset'lerini kullanır:
   {{kod:lab01-led/src/main_registers.c}}
   Merak ediyorsan bu dosyayı ayrı bir uygulama projesi olarak derle ve
   DS50'nin aynı şekilde yanıp söndüğünü doğrula — iki yaklaşımın
   ürettiği davranış birebir aynıdır; yalnızca oraya giden yol
   farklıdır.
   :::

[Başarı kriteri]
DS50 saniyede bir yanıp söner: 500 ms yanık, 500 ms sönük, gözle
rahatça seçilen düzenli bir ritim.

[Kendini sına]
- `XGpioPs_WritePin` yerine DATA_0 register'ına doğrudan `=` ile (yani
  `|=` olmadan) yazsaydın, MIO23 dışındaki diğer MIO pinlerine ne
  olurdu?
- MASK_DATA (LSW/MSW) register'ları ne işe yarar, DATA_0'dan farkı
  nedir?
- `SetDirectionPin` ve `SetOutputEnablePin` çağrılarını atlayıp
  doğrudan `WritePin` çağırsaydın LED yanar mıydı? Neden?

[Takıldıysan]
::ipucu İpucu 1 — Platform/Uygulama İlişkisini Karıştırdıysan
"Platform bileşeni" donanım tanımını (.xsa) ve işletim sistemi seçimini
taşır; "uygulama bileşeni" ona bağlanan kendi kodundur. Yanlış ya da
boş bir platforma bağlandıysan derleme hatası genellikle eksik `XPAR_`
tanımları olarak görünür — önce platform seçimini kontrol et.
::/
::ipucu İpucu 2 — Derleniyor ama LED Yanmıyorsa
`XGpioPs_LookupConfig` ve `XGpioPs_CfgInitialize` dönüş değerlerini
gerçekten kontrol ettin mi? UART terminalinde "ERROR" satırı
görüyorsan `DEVICE_ID` değerini `xparameters.h` ile karşılaştır.
Terminalde hiçbir şey görünmüyorsa Görev 0'daki port/baud ayarlarına
dön — kod sorunsuz çalışırken terminal yanlış porta bakıyor olabilir.
::/
::cozum Tam Çözüm — lab01-led
Aşağıdaki dosya DS50'yi `XGpioPs` driver'ıyla 500 ms periyotla yakıp
söndürür; klasik (DEVICE_ID) akışını kullanır, SDT farkı yorumda
belirtilmiştir.
{{kod:lab01-led/src/main.c}}
::/
:::

Register'ları register map'ten okudun ve elle adresledin; ama C dilinin
donanımla bu düzeydeki ilişkisi inceliklerle doludur — `volatile`, bit
işlemleri, sabit genişlikli tipler. C tarafında seni bekleyen
incelikler bir sonraki bölümün konusudur.
