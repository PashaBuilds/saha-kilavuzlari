# Bölüm 4 — Register'lar: Donanımla Konuşma Dili

Bellek haritasını gördün: her şeyin bir adresi var. Bu bölümde o adreslerin
ardında ne olduğunu öğreneceksin — **register**'lar (yazmaçlar). Bir
register, donanımın CPU'yla konuştuğu küçük bir kutudur; bu bölümü
bitirdiğinde bir register map (yazmaç haritası) dokümanını okuyup
anlamlandırabilecek, kendi kodunla gerçek bir donanımı konuşturacaksın.

## Memory-mapped I/O: adres aslında bir kapı

**Memory-mapped I/O** (bellek eşlemeli giriş/çıkış), bir çevre biriminin
register'larının, tıpkı RAM'deki bir değişken gibi, bir bellek adresinden
okunup yazılabilmesi demektir. Yani `0xFF0A0040` adresine `1` yazmakla
`benimSayacim = 1;` yazmak, CPU'nun gözünden neredeyse aynı işlemdir —
farkı, o adresin RAM'e değil bir GPIO denetleyicisine bağlı olmasıdır ve
oraya yazdığın anda gerçek dünyada bir pin seviye değiştirir.

{{svg:sema-07-adres-kapi.svg|Şekil 7 — "Adres = kapı numarası": CPU'dan adres yolu üzerinden çevre birimi register'ına giden bir okuma/yazma işleminin yolu.}}

Bunu sokakta kapı numarası bulmaya benzetebilirsin: CPU adres yoluna
(bus) bir "kapı numarası" (adres) koyar, o numaradaki "bina" (çevre
birimi) cevap verir. `0xFF00_0000` numaralı kapıyı çalarsan UART0 açar;
`0xFF0A_0000` numaralı kapıyı çalarsan GPIO açar. Kapı numarasını yanlış
yazarsan, ya kimse açmaz ya da hiç beklemediğin biri açar.

## Bir register'ın içi: bit alanları ve erişim tipleri

Her register 32 bitlik bir kutudur ve her bit (ya da bit grubu) farklı bir
anlam taşır. UART'ın SR (Channel Status) register'ında bit 4 = TXFULL
(gönderim FIFO'su (First In First Out — ilk giren ilk çıkan; donanımın
veriyi geçici tuttuğu sıralı tampon) dolu mu), bit 1 = RXEMPTY (alım
FIFO'su boş mu) gibi.

{{svg:sema-08-register-bit.svg|Şekil 8 — 32-bit register bit alanı anatomisi: UART SR'den TXFULL/TXEMPTY/RXFULL/RXEMPTY bitleri vurgulu; altta R/W, RO, W1C rozetleri.}}

Bit alanlarının yanında, her register'ın kendine has bir **erişim tipi**
vardır. Üç tanesiyle sık karşılaşacaksın:

- **R/W (Read/Write):** Hem okunur hem yazılır, tıpkı normal bir değişken
  gibi. CR (0x00) böyle — TX/RX'i etkinleştirmek için üzerine yazarsın.
- **RO (Read-Only):** Sadece okunur; donanım günceller, sen yazamazsın.
  SR (0x2C) böyle — TX FIFO'nun dolu olup olmadığını *sorarsın*, donanıma
  *söylemezsin*.
- **W1C (Write-1-to-Clear):** İlginç ve ilk görüşte kafa karıştıran bir
  desen. Bu register'a **1 yazdığın bit temizlenir**, 0 yazdığın bitler
  değişmeden kalır. ISR (0x14) böyle çalışır: bir kesme bayrağını
  kapatmak için o bite `1` yazarsın — `0` yazmak hiçbir şey yapmaz. Yani
  "temizlemek" fiili burada "üzerine 1 bas" anlamına geliyor; sezgine
  aykırı ama gömülü dünyada çok yaygın bir kalıp.

Bölüm 5'te bu bitleri maskelerle okuyup yazmayı öğreneceksin; şimdilik
onları doğru isimle tanı yeter.

## Register map dokümanını okumak

Donanımcılar (ya da Xilinx) her çevre birimi için bir **register map**
dokümanı yayınlar: hangi register hangi **offset**'te (taban adrese göre
kayma), güç sonrası **reset değeri** ne ve az önce tanıdığın **erişim
tipi** ne. ZynqMP UART'ının gerçek register map'inden küçük bir kesit:

{{svg:sema-09-register-map-okuma.svg|Şekil 9 — Register map dokümanı okuma dersi: UART register tablosu üzerinde offset/erişim/reset anotasyonları.}}

| Register | Offset | Erişim | Reset | Açıklama |
|---|---|---|---|---|
| CR (Control) | 0x00 | R/W | 0x00000128 | TX/RX etkinleştirme, reset bitleri |
| MR (Mode) | 0x04 | R/W | 0x00000000 | Baud kaynağı, veri/durma biti sayısı |
| SR (Channel Status) | 0x2C | RO | — | TX/RX FIFO durumu (TXFULL, RXEMPTY...) |
| ISR (Interrupt Status) | 0x14 | **W1C** | 0x00000000 | Kesme bayrakları |

Dört sütun da kritik: **offset** taban adrese eklenecek sayı; **erişim**
register'la ne yapabileceğini söylüyor; **reset değeri** kart açıldığı
anda register'da ne bulacağını; **açıklama** ise register'ın işini.
Bunları okumadan kod yazmak, kullanma kılavuzunu okumadan cihaz kurmaya
benzer — bazen işe yarar, çoğu zaman saatlerini yer.

## Base address + offset aritmetiği

Bir register'ın gerçek adresi tek bir formülle çıkar:

```metin
gerçek_adres = taban_adres + offset
```

Örnek: GPIO denetleyicisinin taban adresi `0xFF0A_0000`. Bank 0'ın veri
register'ı (DATA_0) `0x40` offset'inde. Gerçek adres:
`0xFF0A_0000 + 0x40 = 0xFF0A_0040`. Bu toplamayı elle her seferinde
yapman gerekmez — az sonra göreceğin gibi bunu senin için sürücü (driver)
fonksiyonları ya da hazır sabitler yapar — ama formülün kendisini
anlamadan register map okumak mümkün değil.

:::tuzak Offset'i taban adresle karıştırmak
Register map dokümanları çoğu zaman offset'i tek başına yazar (`0x2C`
gibi), taban adresi ayrı bir tabloda verir. İkisini karıştırıp doğrudan
`0x2C`'ye yazan ya da UART1'in taban adresini kopyalayıp UART0 kodunda
kullanan bir satır, derlenir, çalışır gibi görünür ve seni yanlış çevre
birimini programlarken bulur. Her register adresini kullanmadan önce
"bu hangi taban + hangi offset" diye kendine sor.
:::

## xparameters.h: adresleri elle yazmayız

Peki bu taban adresleri koddan nereden okuyorsun? Elle yazmazsın —
Vitis, donanım tanımından (.xsa) otomatik olarak **`xparameters.h`**
başlık dosyasını üretir; her çevre biriminin adresi, kesme numarası ve
kimliği burada bir sabit olarak hazır durur. İki farklı Vitis akışında
isimlendirme biraz değişir:

- **Klasik akış** (2023.1 ve öncesi Vitis Classic): her aygıt bir
  **DEVICE_ID** ile tanınır, örn. `XPAR_XUARTPS_0_DEVICE_ID`. Sürücünün
  `LookupConfig` fonksiyonuna bu kimliği verirsin, o da sana taban adresi
  içeren bir konfigürasyon yapısı döner.
- **SDT akışı** (System Device Tree — Vitis Unified IDE'nin güncel
  yöntemi): aygıtlar doğrudan taban adresle anılır, örn.
  `XPAR_XUARTPS_0_BASEADDR`. `LookupConfig` bu durumda adresin kendisini
  parametre olarak alır.

İkisinin de mantığı aynı: **adresi elle yazma, üretilen başlıktan al.**
Elle yazdığın bir adres, donanım tasarımı değiştiğinde (ya da başka bir
projeye taşındığında) sessizce yanlışlanır; `xparameters.h`'den gelen
sabit ise donanımla birlikte otomatik güncellenir.

## Gerçek örnek: UART0'dan bir karakter göndermek

Şimdi bütün bu kavramları tek bir gerçek işleme bağlayalım: UART0
(`0xFF00_0000`) üzerinden 'A' karakterini register seviyesinde göndermek.
Sürücü fonksiyonlarının arkasında olan biten tam olarak şu:

1. **SR register'ını oku** (taban + `0x2C`).
2. **TXFULL bitini kontrolü et** (maske `0x10`). Bit 1 ise gönderim
   FIFO'su dolu demektir — boş yer açılana kadar bu adımı tekrarla
   (bu, Bölüm 6'da tanışacağın "polling" deseninin ta kendisi; bedeli ve
   interrupt'la karşılaştırması Bölüm 7'de).
3. TXFULL sıfır olduğunda **FIFO register'ına** (taban + `0x30`) 'A'
   karakterinin ASCII değerini yaz.

Donanım bundan sonrasını kendi üstlenir: karakteri fiziksel TX pininden
seri olarak dışarı gönderir. Bu üç adım — durumu oku, bekle, yaz —
gömülü dünyada saymakla bitmeyecek kadar sık göreceğin bir kalıptır.

Artık teoriyi yeterince biriktirdin. Sıra pratik yapmakta: ilk görevin,
bu bölümdeki register mantığını gerçek bir LED üzerinde denemek.

## Vitis'e ilk bakış: proje aç, derle, karta at

Az sonra Görev 1'de Vitis'i ilk kez açacaksın; burada tıklama sırasının
kendisini önceden tarif edelim ki karşına çıktığında yabancı gelmesin.
Vitis'in ne olduğu, BSP (board support package) kavramı, debugger,
Run/Debug config'leri ve disassembly gibi derinlikler Bölüm 11'de
bütünüyle işlenecek — burada anlattığımız yalnızca tıklama sırasının
kendisi; şimdilik "ne yaptığını bilerek tıkla" yeter.

İlk açılışta Vitis senden bir workspace (çalışma alanı) seçmeni ister:
projelerini, ayarlarını ve derleme çıktılarını tuttuğu bir klasör.
Workspace açıldıktan sonra ilk iş, ekibin sana hazırladığı platformu
seçmektir — bu, donanımın tarifini taşıyan bir .xsa dosyasından türetilir;
platformu sen tasarlamıyorsun, donanımcı tasarlıyor, sen listeden
seçiyorsun.

Platform seçiliyken yeni bir boş (empty) uygulama projesi açarsın:
"empty application" şablonu hazır örnek kod getirmez, sıfırdan
dolduracağın bir kabuk verir — ki bu yolculukta neredeyse hep tercih
edeceğin şablon bu olacak. Vitis bu projeyi seçtiğin platforma otomatik
bağlar ve hangi işlemci çekirdeğinde koşacağını sorar (bu yolculukta
neredeyse hep APU'nun bir Cortex-A53 çekirdeği).

Proje açıldıktan sonra kaynak dosyalarını projenin src/ klasörüne
koyarsın — göreve gelince çözüm dosyasını oraya kopyalaman tam olarak bu
yüzden. Ardından Build (derle) düğmesine basarsın; hata varsa
Console/Problems panelinde kırmızı satırlar olarak görürsün, temizse bir
çalıştırılabilir çıktı üretilir ve proje ağacında yeni bir Debug/Release
klasörü belirir.

Derleme temizse sıra karta atmakta: projeye sağ tık, Run As → Launch on
Hardware (JTAG). Vitis JTAG üzerinden karta bağlanır, derlediğini yükler
ve çalıştırır; karttaki bir LED yanıp sönmeye başlar ya da Görev 0'da
açtığın terminalde bir satır akar — kodunun gerçekten karta ulaştığının
kanıtı budur.

Bu sıra — workspace, platform seç, boş proje aç, src/'e kod koy, Build,
Run As → Launch on Hardware — Görev 1'den Görev 10'a kadar defalarca
elinden geçecek. İlk seferinde adım adım oku, birkaç görev sonra
parmakların ezberleyecek.

:::gorev no=1 zorluk=1 baslik="LED Yak (Merhaba Donanım)" kisa="LED Yak"
[Hedef]
Vitis'te bare-metal bir uygulama derleyip karta yükleyerek DS50 LED'ini
(PS MIO23) 500 ms periyotla (500 ms açık / 500 ms kapalı) yakıp söndürmek.

[Ön koşul]
Bölüm 3 ve 4 okundu; Görev 0 tamamlandı (kart JTAG modunda, terminal
bağlantısı hazır).

[Adımlar]
1. Vitis'te ekibin sağladığı hazır **platformu** (donanım tanımı, .xsa)
   seç — platform ile uygulama projesi ilişkisini Bölüm 11'de bütünüyle
   göreceğiz, şimdilik "donanımın tarifi" olarak düşün.
2. Yeni bir **boş (empty) uygulama** projesi aç ve seçtiğin platforma
   bağla.
3. Bu görevin çözüm dosyası olan `lab01-led/src/main.c`'yi projenin
   `src/` klasörüne kopyala.
4. Projeyi **derle** (Build).
5. **JTAG üzerinden karta yükle ve çalıştır** (Run As → Launch on
   Hardware). Adım adım JTAG/debug ayrıntılarına Bölüm 11'de gireceğiz;
   bu beş adım şimdilik yeter.
6. (opsiyonel) UART terminalini Görev 0'daki ayarlarla aç; "Görev 1"
   satırının basıldığını gör.

   :::derin-dalis Aynı işi doğrudan register ile yapmak
   `XGpioPs_WritePin` gibi sürücü fonksiyonları senin için tam olarak
   Bölüm 4'te öğrendiğin taban+offset aritmetiğini ve oku-değiştir-yaz
   işlemini yapar. Bu satırların arkasını görmek istersen,
   `content/_arastirma-ek-B.md`'de kaynaklı olarak doğrulanmış DIRM_0,
   OEN_0 ve DATA_0 register ofsetleriyle aynı LED'i doğrudan volatile
   pointer (volatile — derleyici bu adresi her erişimde gerçekten
   okusun/yazsın; ayrıntısı Bölüm 5'te) üzerinden yakan alternatif çözüm
   burada:
   {{kod:lab01-led/src/main_registerli.c}}
   Merak ediyorsan bu dosyayı ayrı bir uygulama projesi olarak derleyip
   DS50'nin aynı şekilde yanıp söndüğünü gör — iki yaklaşımın ürettiği
   davranış birebir aynı, yolculuk farklı.
   :::

[Başarı kriteri]
DS50 saniyede bir yanıp sönüyor: 500 ms açık, 500 ms kapalı, gözle net
görülen düzenli bir ritim.

[Kendini sına]
- `XGpioPs_WritePin` yerine DATA_0 register'ına doğrudan `=` ile (yani
  `|=` kullanmadan) yazsaydın, MIO23 dışındaki diğer MIO pinlerine ne
  olurdu?
- MASK_DATA (LSW/MSW) yazmaçları ne işe yarar; DATA_0'dan farkı ne?
- `SetDirectionPin` ve `SetOutputEnablePin` çağrılarını atlayıp doğrudan
  `WritePin` çağırsaydın LED yanar mıydı? Neden?

[Takıldıysan]
::ipucu İpucu 1 — Platform/uygulama ilişkisini karıştırdıysan
Bir "platform component" donanım tanımını (.xsa) ve işletim sistemi
seçimini taşır; "application component" ona bağlanan senin kodundur.
Yanlış ya da boş bir platforma bağlandıysan derleme hatası genelde
`XPAR_` tanımlarının bulunamamasıyla kendini gösterir — önce platform
seçimini kontrol et.
::/
::ipucu İpucu 2 — Derleniyor ama LED yanmıyorsa
`XGpioPs_LookupConfig` ve `XGpioPs_CfgInitialize`'ın dönüş değerlerini
gerçekten kontrol ettin mi? UART terminalinde "HATA" satırı görüyorsan
`DEVICE_ID`'yi `xparameters.h`'den doğrula. Terminalde hiçbir şey
görünmüyorsa Görev 0'daki port/baud ayarına geri dön; kod çalışıyor
olabilir, terminal yanlış porta bakıyor olabilir.
::/
::cozum Tam çözüm — lab01-led
Aşağıdaki dosya `XGpioPs` sürücüsüyle DS50'yi 500 ms periyotla yakıp
söndürür; klasik (DEVICE_ID) akış kullanır, SDT farkı yorum satırında not
düşülmüştür.
{{kod:lab01-led/src/main.c}}
::/
:::

Register'ları register map'ten okuyup elle adresledin; ama C dilinin bu
düzeyde donanımla ilişkisi ince noktalarla dolu — `volatile`, bit
işlemleri, sabit genişlikli tipler. C tarafında seni bekleyen incelikler
bir sonraki bölümün konusu.
