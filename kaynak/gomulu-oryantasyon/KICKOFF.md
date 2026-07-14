# KICKOFF — gomulu-oryantasyon

> Bu dosya, projenin tek başlangıç talimatıdır. Claude Code bu dosyayı okuyarak
> üretime başlar. Repo kökünde durur; CLAUDE.md bu dosyaya referans verir.

---

## 1. Proje Kimliği

- **Klasör / repo adı:** `gomulu-oryantasyon`
- **Doküman adı:** *Gömülü Sistemlere Giriş — Ekip Oryantasyon Yolculuğu*
- **Tür:** "Saha Kılavuzu" serisinin kardeşi ama farklı bir tür: **rehberli
  yolculuk (guided journey)**. Saha kılavuzu referans eseridir; bu doküman ise
  bir müfredattır — okuma bölümleri ile elde kart yapılan görevler dönüşümlü
  ilerler. Görsel aile ve kalite çıtası seriyle aynı.
- **Hedef kitle:** Üniversiteden yeni mezun, ekibe yeni katılan
  **elektrik-elektronik mühendisi**. C'yi derste görmüş, mikrodenetleyiciye
  belki Arduino düzeyinde dokunmuş; FPGA SoC, RTOS, register map, Vitis
  dünyasına sıfırdan başlıyor. Elinde bir **ZCU111** geliştirme kartı var
  (Zynq UltraScale+ RFSoC) ve ilk haftalarını bu dokümanla geçirecek.
- **Misyon:** Doküman bittiğinde arkadaşımız:
  1. Bir Zynq tabanlı sistemde PS/PL ayrımını, boot akışını ve bellek haritasını
     anlatabilmeli.
  2. Vitis'te sıfırdan bare-metal proje açıp derleyip karta JTAG ile atabilmeli,
     UART'tan çıktı alabilmeli, debugger ile adım adım yürütebilmeli.
  3. Register map okuyup volatile pointer ile donanım programlayabilmeli;
     polling ve interrupt tabanlı iki yaklaşımı da uygulayabilmeli.
  4. I2C/SPI/UART'ın tel seviyesinde nasıl çalıştığını çizip, karttaki gerçek
     bir I2C cihazından veri okuyabilmeli.
  5. FreeRTOS'ta task/queue/semaphore kullanan küçük bir uygulama yazabilmeli.
  6. Final projesini (Bölüm "Mezuniyet Görevi") tek başına tamamlayabilmeli.
- **Dil:** Türkçe gövde; teknik terimler İngilizce korunur, ilk geçtiği yerde
  parantezle açıklanır. Ton: kıdemli bir ekip arkadaşının ilk gün elinden tutan,
  samimi ama ciddiye alan sesi. "Hoş geldin" ruhu dokümanın her yerinde
  hissedilmeli — ama şirin olacağım derken içerik sulanmamalı.

---

## 2. Repo Yapısı

```
gomulu-oryantasyon/
├── KICKOFF.md
├── CLAUDE.md               ← "KICKOFF.md'yi oku, kurallara uy"
├── content/                ← bölüm başına bir markdown
│   ├── 00-hosgeldin.md
│   ├── 01-gomulu-dunya.md
│   ├── ...
├── labs/                   ← görevlerin ÇÖZÜM kodları (C kaynakları, ayrı klasörler)
│   ├── lab01-led/
│   ├── lab02-uart/
│   └── ...
├── assets/
│   ├── svg/
│   └── css/kilavuz.css
├── build/build.py          ← md → tek self-contained HTML
└── dist/index.html
```

**Kural:** `dist/index.html` tamamen self-contained (CSS/SVG/JS inline,
internet bağımlılığı yok). `labs/` altındaki çözüm kodları HTML'e katlanabilir
`<details>` bloklarında gömülür — arkadaş önce kendi dener, takılırsa açar.

---

## 3. Tasarım Sistemi

Saha kılavuzlarıyla aynı görsel aile (koyu/açık çift tema, aynı palet:
zemin `#0E1116`, kart `#161B22`, vurgu `#4DA3FF`, altın `#E8B84B`, yeşil
`#5BB0A6`; SVG'lerde CSS değişkenleri, hard-coded renk yasak; sticky TOC,
progress bar, anchor linkler, kod kopyala butonları — önceki kılavuzlardaki
tüm standartlar geçerli). Bu projeye özgü ekler:

### 3.1 Görev Kartı (`gorev-karti`) — bu dokümanın imza bileşeni

Her laboratuvar görevi standart bir kart olarak render edilir:

- Başlıkta görev numarası + isim + zorluk (🔧 / 🔧🔧 / 🔧🔧🔧 yerine
  emoji DEĞİL, 1-3 dolu nokta gibi sade bir SVG göstergesi).
- **Hedef:** tek cümle. **Ön koşul:** hangi bölümler okunmuş olmalı.
- **Adımlar:** numaralı, net, kopyalanabilir komutlarla.
- **Başarı kriteri:** "UART terminalinde saniyede bir 'tick' görüyorsun" gibi
  gözlemlenebilir, ikili (oldu/olmadı) sonuç.
- **Kendini sına:** 2-3 kavrama sorusu ("interrupt yerine polling kullansaydın
  ne değişirdi?").
- **Takıldıysan:** katlanabilir ipucu merdiveni — önce yönlendirme, sonra
  daha somut ipucu, en sonda tam çözüm kodu (`<details>` içinde `<details>`).
- Kart köşesinde checkbox; işaretlenince localStorage'a yazılır ve sayfa
  başındaki **ilerleme panosu** güncellenir.

### 3.2 İlerleme Panosu

Dokümanın başında yolculuk haritası: tüm görevler bir patika üzerinde küçük
duraklar olarak (SVG), tamamlananlar dolu renkte. localStorage ile kalıcı.
Bu, dokümana "oyunlaştırılmış ama ciddi" hissini veren ana unsur.

### 3.3 Diğer İçerik Bileşenleri

Seriden aynen: `saha-notu` (altın), `tuzak` (kırmızı), `derin-dalis`
(katlanabilir mavi), `analoji` (yeşil), kopyala butonlu `komut` kutusu.
Bu projeye özel ek: `ekip-notu` (mor kenarlıklı) — "bizim ekipte bunu şöyle
yaparız" kültür aktarım kutuları (kodlama stili, isimlendirme, code review
beklentisi gibi; içerik genel tutulur, proje sırrı yazılmaz).

### 3.4 Diyagram Kuralları

- Birincil araç: **el yapımı inline SVG** (etiketler Türkçe, sinyal/alan
  adları İngilizce, `<title>` + `<figcaption>` zorunlu).
- Zaman diyagramları (UART/I2C/SPI dalga şekilleri) için WaveDrom tarzı
  görünüm elde SVG ile çizilir — runtime JS kütüphanesi YOK.
- Mermaid yalnızca akış/durum makinesi için kullanılabilir ama **build
  sırasında SVG'ye render edilip inline gömülür** (mmdc ile); HTML'e runtime
  mermaid.js asla eklenmez. mmdc yoksa o şemalar da elde SVG çizilir.

---

## 4. Görselleştirme Envanteri (ZORUNLU, en az 24 şema)

| # | Şema | Bölüm |
|---|------|-------|
| 1 | "Gömülü sistem nedir" evren haritası: sensör → MCU/SoC → aktüatör; çevremizdeki gömülü cihazlar | 1 |
| 2 | Gömülü yazılımcının sorumluluk katmanları: donanım ↔ driver ↔ middleware ↔ uygulama; "biz bu katmanlardayız" vurgusu | 1 |
| 3 | Zynq UltraScale+ kuşbakışı: PS (APU A53×4, RPU R5×2, çevre birimleri) + PL (FPGA kumaşı) + aralarındaki AXI köprüleri | 2 |
| 4 | ZCU111 kart anatomisi: üstten görünüm krokisi — LED'ler, butonlar, DIP switch, UART-USB, JTAG, DDR4, PMOD, SD kart yuvası etiketli | 2 |
| 5 | Boot akışı zaman çizgisi: BootROM → FSBL → (ATF) → uygulama; boot.bin'in içi | 3 |
| 6 | Bellek haritası çubuğu: OCM, DDR, PL adres pencereleri, çevre birimi register blokları — adresleriyle | 3 |
| 7 | "Adres = kapı numarası" register kavramı: CPU → adres yolu → çevre birimi register'ı; memory-mapped I/O sezgisi | 4 |
| 8 | Bir register'ın bit alanı anatomisi: 32-bit kutu, alanlar renkli, read/write/w1c davranışları | 4 |
| 9 | Register map dokümanı okuma dersi: gerçek bir UART register tablosu ekran-anatomisi | 4 |
| 10 | volatile'ın hikâyesi: derleyici optimizasyonunun okuma/yazmayı yok etmesi — volatile'lı ve volatile'sız iki derleme akışı yan yana | 5 |
| 11 | Bit işlemleri görsel referansı: set / clear / toggle / test maskeleri, önce-sonra bit kutuları | 5 |
| 12 | Cache hiyerarşisi ve tutarlılık: CPU-cache-DDR-DMA dörtgeni; "DMA yazdı ama CPU eskiyi okuyor" senaryosu | 6 |
| 13 | Stack vs heap vs static bellek yerleşimi; linker script'in ELF bölümlerini haritaya oturtması | 6 |
| 14 | Polling vs interrupt karşılaştırma zaman çizgisi: CPU meşguliyeti iki şeritte | 7 |
| 15 | Interrupt yaşam döngüsü: olay → GIC → vektör → ISR → dönüş; "ISR kısa tutulur" kuralının görseli | 7 |
| 16 | UART kare yapısı dalga şekli: start, 8 veri biti, parity, stop; baud rate kavramı | 8 |
| 17 | SPI dalga şekli: SCLK/MOSI/MISO/CS, mode 0-3 farkları mini panellerde | 8 |
| 18 | I2C dalga şekli: start, adres+R/W, ACK, veri, stop; open-drain ve pull-up sezgisi | 8 |
| 19 | Üç protokol karşılaştırma tablosu-görseli: tel sayısı, hız, topoloji, kullanım yeri | 8 |
| 20 | AXI el sıkışma sezgisi: valid/ready; PS'ten PL'deki IP'ye bir okuma işleminin yolculuğu | 9 |
| 21 | Bare-metal süperdöngü vs FreeRTOS task'ları: iki dünya yan yana, context switch kavramı | 10 |
| 22 | FreeRTOS çekirdek nesneleri haritası: task durum makinesi + queue/semaphore/mutex'in task'lar arası köprüleri | 10 |
| 23 | Vitis ekran anatomisi: workspace/platform/uygulama projesi ilişkisi + perspektifler | 11 |
| 24 | Debug oturumu akışı: JTAG → breakpoint → step → register/memory izleme döngüsü | 11 |
| 25 | Mezuniyet görevi sistem mimarisi: tüm öğrenilenlerin tek projede birleşimi | 14 |

---

## 5. İçerik ve Görev Kurgusu

Yapı: **okuma bölümü → hemen ardından o bölümü ete kemiğe büründüren görev(ler)**.
Görevler birbirinin üstüne inşa edilir; her görev bir öncekinin kodunu genişletir
ya da yeni bir beceri ekler. Aşağıdaki iskelet bağlayıcıdır; Claude Code
adımların teknik detayını (Vitis menü yolları, xparameters sabitleri, ZCU111
pin/cihaz bilgileri) resmî dokümantasyondan teyit ederek doldurur.

### Bölüm 0 — Hoş Geldin
Ekibe ve dokümana giriş; yolculuk haritası; "ilk iki haftada nereye
varacaksın" beklentisi; kurulum kontrol listesi (Vitis kurulumu, kart kutusu
içeriği, terminal programı, sürücüler). İlerleme panosu burada tanıtılır.

### Bölüm 1 — Gömülü Dünya ve Senin Rolün
Gömülü sistem nedir; masaüstü yazılımdan farkları (kaynak kısıtı, gerçek
zaman, donanıma yakınlık, "hata = cihaz tuğlalaşabilir" sorumluluğu);
gömülü yazılımcının görev tanımı: driver yazmak, donanımcıyla register map
üzerinden konuşmak, bring-up, debug, entegrasyon. `ekip-notu`: bizim ekipte
tipik bir işin yaşam döngüsü.

### Bölüm 2 — Tanış: Zynq ve ZCU111
SoC kavramı; **PS (Processing System)**: A53 uygulama çekirdekleri, R5
gerçek-zaman çekirdekleri, sabit çevre birimleri (UART, I2C, SPI, GPIO, DDR
denetleyici); **PL (Programmable Logic)**: FPGA kumaşı, "donanımcının
tasarladığı IP'ler burada yaşar"; PS-PL'nin AXI ile evliliği. PS IP vs PL IP
ayrımı: aynı UART işini ikisinde de yapabilirsin, farkları ne? ZCU111 kart
turu: şema #4 üzerinde her elemanın kısa hikâyesi. RFSoC'un RF tarafına
sadece bir pencere ("bu kartın süper gücü, ama bizim yolculuğumuzda değil").

> **GÖREV 0 — İlk Temas:** Kartı kutudan çıkar, jumper/switch konfigürasyonunu
> doğrula (JTAG boot modu), güç ver, USB-UART bağla, terminal programında
> doğru COM portu bul. Başarı: kart açılıyor, terminal hazır.

### Bölüm 3 — Sistem Nasıl Ayağa Kalkar: Boot ve Bellek Haritası
Reset'ten `main()`'e yolculuk: BootROM, FSBL'nin işleri (DDR init, PL bitstream
yükleme), boot.bin kavramı; boot modları (JTAG/SD/QSPI). Bellek haritası:
"her şeyin bir adresi var" — OCM, DDR, çevre birimleri, PL pencereleri.
`derin-dalis`: ATF/PMU'ya bir paragraf, TrustZone'a bir cümle.

### Bölüm 4 — Register'lar: Donanımla Konuşma Dili
Memory-mapped I/O; register map dokümanı nasıl okunur (offset, alanlar,
reset değeri, erişim tipleri R/W/RO/W1C); base address + offset aritmetiği;
xparameters.h'nin rolü ("adresleri elle yazmayız, üretilen başlıktan alırız").
Gerçek örnek: ZynqMP UART register bloğu üzerinden bir satır veri göndermenin
register düzeyinde adımları.

> **GÖREV 1 — LED Yak (Merhaba Donanım):** Vitis'te hazır platformla boş
> bare-metal proje aç; PS GPIO (ya da karttaki LED'lerin bağlı olduğu yol —
> teyit et) üzerinden LED'leri register seviyesinde yak/söndür. Önce hazır
> driver (XGpioPs) ile, sonra `derin-dalis` olarak doğrudan volatile pointer
> ile aynı işi yap — iki yaklaşımın farkını gör. Başarı: 8 LED'de yürüyen ışık.

### Bölüm 5 — Gömülü C Pratikleri I: Dil Donanıma Değince
`volatile` (neden, ne zaman, derleyicinin kafası); bit işlemleri (set/clear/
toggle/test, maske makroları); sabit genişlikli tipler (`uint32_t` neden
`int` değil); bitfield struct'lar — cazibesi ve tuzakları (taşınabilirlik,
sıralama); pointer ile register erişim kalıpları; `const volatile` gibi
kombinasyonlar. `ekip-notu`: ekip kodlama stili (Hungarian notation kalıpları,
`module_object_action()` isimlendirmesi, Allman braces) — "kod review'da
bunlara bakılır".

> **GÖREV 2 — UART "Merhaba Dünya" ve printf'in Arkası:** UART'tan yazı bas;
> `xil_printf` ile standart `printf` farkını gör; kendi `uart_putc/puts`
> fonksiyonunu register seviyesinde yaz (TX FIFO full kontrolü ile).
> Başarı: terminalde kendi fonksiyonunla bastığın karşılama ekranı.

### Bölüm 6 — Gömülü C Pratikleri II: Bellek ve Cache
Stack/heap/static ayrımı; gömülüde dinamik belleğe temkinli yaklaşım;
linker script'e giriş (bölümler, ELF'in haritaya oturması); cache'in ne
işe yaradığı ve ne zaman düşman olduğu (DMA tutarlılığı, cache flush/
invalidate kavramları, Xil_DCacheFlushRange gibi API'lerin varlığı);
alignment kavramı. `tuzak`: "debug'da çalışıyor release'te çalışmıyor"
klasiğinin volatile/cache kökenleri.

> **GÖREV 3 — Buton Oku (Polling):** DIP switch ve push buton durumunu
> polling ile oku, LED'lere yansıt, UART'a durum bas. Debounce kavramıyla
> tanış. Başarı: butona basınca LED deseni değişiyor.

### Bölüm 7 — Interrupt: Olay Geldiğinde Haber Ver
Polling'in bedeli; interrupt kavramı; GIC'in rolü (öncelik, enable, kaynak);
ISR yazma kuralları (kısa tut, paylaşılan veriye volatile + dikkat, ISR'de
printf yapmama); interrupt latency sezgisi; edge vs level tetikleme.

> **GÖREV 4 — Buton Interrupt'ı:** Görev 3'ü interrupt tabanlıya dönüştür:
> GPIO interrupt'ı GIC'e bağla, ISR'de bayrak set et, ana döngüde işle.
> Başarı: CPU ana döngüde başka iş yaparken buton anında tepki alıyor.
>
> **GÖREV 5 — Timer ile Kalp Atışı:** TTC timer'ı periyodik interrupt'a
> kur; saniyede bir "tick" bas + LED heartbeat. Başarı: düzenli tick akışı.
> Kendini sına: tick süresini register değerinden elle hesapla.

### Bölüm 8 — Seri Protokoller: UART, SPI, I2C
Her biri için: tel seviyesi dalga şekli, adresleme/topoloji, hız sınıfı,
tipik kullanım. UART (asenkron, baud anlaşması), SPI (senkron, hızlı,
CS ile seçim, mode 0-3), I2C (iki tel, çoklu cihaz, ACK/NACK, pull-up).
Karşılaştırma şeması #19. `saha-notu`: lojik analizör/osiloskopla bu
hatlara bakma kültürü — "yazılımcı da prob tutar".

> **GÖREV 6 — I2C ile Gerçek Bir Çiple Konuş:** ZCU111 üzerindeki I2C
> ağacından bir cihaz seç (kart üstü güç monitörü INA226 sınıfı bir cihaz
> veya EEPROM — Claude Code kart user guide'ından adresleri teyit etsin;
> I2C mux/switch varsa yolculuğa dahil et, bu da öğreticidir). Cihazın
> datasheet'inden register'ını bul, oku, anlamlandır (örn. gerilim/akım
> değeri), UART'a bas. Başarı: terminalde kartın gerçek ölçümü akıyor.
> Bu görev "datasheet okuma" becerisinin vaftizidir — adımlar bunu bilinçli
> yaşatsın.

### Bölüm 9 — PS ↔ PL: AXI ve IP Dünyası
AXI'nin ne olduğu (sezgi düzeyinde valid/ready el sıkışması, okuma/yazma
kanalları); PL'de yaşayan IP'lerin PS'ten nasıl görüldüğü (adres penceresi,
yine register map!); "donanımcı IP verdi, bana header ve register tablosu
lazım" iş akışı; AXI GPIO / AXI Timer / BRAM gibi standart IP'ler;
`derin-dalis`: AXI-Lite vs AXI4 vs AXI-Stream farkları, DMA kavramına giriş.
`ekip-notu`: donanımcıyla register map üzerinden anlaşma kültürü.

> **GÖREV 7 — PL'deki IP ile Konuş:** Hazır verilen bir bitstream'de
> (repo `labs/` içinde hazır .xsa/bitstream sağlanır — Claude Code basit bir
> AXI GPIO'lu tasarım varsayımıyla kurgular, donanım tarafı ekipçe temin
> edilir notu düşülür) PL LED'lerini AXI GPIO üzerinden sür; aynı LED'i
> PS GPIO ile sürmekle farkını kavra. Başarı: PL üzerinden LED kontrolü.

### Bölüm 10 — İşletim Sistemi: Bare-metal'den FreeRTOS'a
Bare-metal süperdöngü + ISR mimarisi: gücü ve sınırı; "neden RTOS":
çoklu iş, zamanlama garantileri, bekleme yerine bloklanma. FreeRTOS çekirdeği:
task, öncelik, scheduler, tick; queue/semaphore/mutex; ISR'den task'a haber
(FromISR API'leri); stack boyutu ve taşma tuzağı; priority inversion'a
`derin-dalis`. Bizim dünyada üçüncü seçenek olarak ticari RTOS'ların
(VxWorks gibi) varlığına bir paragraf pencere.

> **GÖREV 8 — İlk FreeRTOS Uygulaman:** İki task: biri LED heartbeat, biri
> UART'a durum basan; butonu ISR'den semaphore ile bir task'a bağla.
> Başarı: üç işin "aynı anda" huzur içinde çalışması.
>
> **GÖREV 9 — Queue ile Üretici/Tüketici:** Timer task'ı I2C ölçümünü
> (Görev 6) periyodik alıp queue'ya koysun; tüketici task formatlayıp
> bassın. Başarı: mimarisi temiz, veri akışlı mini sistem.

### Bölüm 11 — Alet Çantası: Vitis ve Debug
Vitis kavram haritası: platform (.xsa) / BSP / uygulama projesi ilişkisi;
proje açma, derleme, Run/Debug konfigürasyonları; JTAG üzerinden yükleme;
debugger kullanımı: breakpoint, step, değişken/register/memory izleme,
disassembly'ye korkusuz bakış; XSCT konsoluna bir pencere. Debug felsefesi:
`saha-notu` olarak "printf, LED, debugger, lojik analizör — dört silah"
anlatısı. (Bu bölüm görevlere hizmet ettiği için 4. bölümden itibaren
parça parça referans verilir, burada bütünleşir.)

> **GÖREV 10 — Bug Avı:** `labs/lab10-bugav/` içine bilerek 3-4 klasik hata
> gömülmüş bir proje konur (volatile eksikliği, ISR'de uzun iş, yanlış maske,
> stack taşması gibi). Görev: debugger ve öğrenilen tekniklerle hepsini bul,
> düzelt, her bug için bir cümle "kök neden" yaz. Başarı: temiz çalışan proje
> + kök neden listesi. Bu görev dokümanın en eğlenceli durağı olacak şekilde
> kurgulanır (dedektif tonu, ipucu merdiveni).

### Bölüm 12 — Meslek Kültürü: İyi Gömülü Yazılımcı
Savunmacı programlama (dönüş değeri kontrolü, assert, timeout'suz sonsuz
bekleme yasağı); kod okunabilirliği ve yorum kültürü; versiyon kontrol
temelleri (git akışı, anlamlı commit); code review'a nasıl kod gönderilir;
datasheet/user guide okuma stratejisi; soru sorma sanatı ("ne denedin"
şablonu). `ekip-notu` yoğun bölüm.

### Bölüm 13 — Ufuk Turu (derin-dalis niteliğinde kısa pencereler)
Bu yolculuğa sığmayan ama adını duyacağı kavramlar: DMA ve scatter-gather,
watchdog, DDR/QSPI/eMMC farkları, device tree ve Linux'lu Zynq dünyası,
güvenli boot/kriptografi, JESD/PCIe gibi yüksek hızlı arayüzler, birim test
ve CI. Her biri 1 paragraf + "hazır olduğunda şu saha kılavuzuna bak" linki
(Bellek Mimarisi, Ethernet, RF Örnekleme kılavuzlarına çapraz referans).

### Bölüm 14 — MEZUNİYET GÖREVİ
Tüm becerileri birleştiren mini proje: **"Kart Sağlık Monitörü"** —
FreeRTOS üzerinde; bir task I2C'den güç/sıcaklık ölçümlerini toplar,
bir task LED'lerde durum kodu gösterir, buton interrupt'ı ekran modunu
değiştirir, UART'ta hem periyodik telemetri hem basit bir komut satırı
(komutları parse eden mini CLI: `status`, `led on/off`, `rate <ms>`).
Gereksinim listesi + kabul kriterleri + serbest tasarım alanı. Çözüm kodu
VERİLMEZ; sadece mimari önerisi şeması (#25) ve kilit ipuçları. Teslim:
kısa bir README + ekip önünde 10 dakikalık demo. Kapanış: tebrik + "sırada
ne var" yönlendirmesi.

### Ek A — Hızlı Referans
Bit işlem makroları, sık Vitis kısayolları, UART/I2C/SPI özet tablosu,
FreeRTOS API mini kartı, ZCU111 önemli adres/cihaz özeti.

### Ek B — Sözlük
Alfabetik, bölüm linkleriyle.

---

## 6. Yazım Kuralları

1. **Sıfır varsayım:** okuyucunun bildiği tek şey temel C ve devre teorisi.
   Her kavram tanımlanmadan kullanılmaz; ileri kavram gerekirse "Bölüm X'te"
   denir.
2. **Okuma/görev ritmi:** hiçbir okuma bölümü art arda iki bölümden fazla
   görevsiz ilerlemez. Eller karta değmeden teori birikmez.
3. **Görev doğrulanabilirliği:** her görevin başarı kriteri gözlemlenebilir
   ve ikilidir. "Anla", "incele" gibi ölçülemez hedef yasak.
4. **Teknik doğruluk:** ZCU111'e özgü her iddia (LED/buton bağlantıları, I2C
   cihaz adresleri, boot switch konumları, UART cihaz numarası) kart user
   guide'ı ve Xilinx/AMD dokümantasyonundan web ile teyit edilir; teyit
   edilemeyen detay "kart dokümanından doğrula" notuyla işaretlenir, asla
   uydurulmaz.
5. **Kod kalitesi:** tüm çözüm kodları derlenebilir bütünlükte, yorumlu,
   ekip stiline uygun (Hungarian notation, module_object_action, Allman).
   Her lab klasöründe kısa README.
6. **Ton:** sıcak, cesaretlendirici, ara sıra ince espri — ama asla
   çocuklaştırma yok. Emoji yok. Hata yapmanın normal olduğu mesajı
   (özellikle Görev 10 çevresinde) bilinçli işlenir.
7. **Bölüm uzunluğu:** okuma bölümleri 800–1500 kelime; görev kartları
   kompakt; Bölüm 14 gereksinim dokümanı netliğinde.

---

## 7. Build Kuralları

- `build/build.py`: `content/*.md` → SVG göm → çözüm kodlarını `labs/`'tan
  çekip katlanabilir bloklara yerleştir → TOC + görev listesi üret → tek
  `dist/index.html`.
- JS bütçesi: tema toggle, TOC vurgusu, kod kopyala, progress bar,
  **görev checkbox'ları + ilerleme panosu (localStorage)**. Framework yok.
- HTML 2.5 MB altı hedef (kod blokları nedeniyle pay biraz geniş).

---

## 8. Üretim Akışı (Claude Code için)

1. Repo iskeleti + CLAUDE.md + tema; boş bölümle build doğrula.
2. **Araştırma turu:** ZCU111 user guide + ZynqMP TRM'den görevlerde geçen
   somut detayları (LED/buton MIO-PL bağlantıları, I2C ağacı ve adresler,
   boot switch tablosu, TTC/GIC ayrıntıları) topla; `content/_arastirma.md`
   dosyasına kaynaklı not al. İçerikteki her karta-özgü değer buradan gelir.
3. İlerleme panosu + görev kartı bileşenlerini önce tek örnek görevle uçtan
   uca çalışır hale getir (HTML+CSS+JS prototipi), sonra içeriğe geç.
4. Bölümleri sırayla yaz; her görevin çözüm kodunu `labs/` altında gerçekten
   yaz ve mantıksal tutarlılığını gözden geçir (derleme ortamı yoksa en
   azından statik olarak dikkatle incele; API adlarını dokümandan teyit et).
5. Her 3 bölümde build alıp kontrol: kartlar, checkbox kalıcılığı, iki temada
   dalga şekli SVG'lerinin okunurluğu.
6. Görev 10'un buglı projesini en son, dokümandaki öğretileri bilerek
   yansıtacak şekilde tasarla.
7. Son tur: görev zinciri tutarlılığı (her görev öncekinin çıktısını doğru
   varsayıyor mu), çapraz linkler, sözlük, hızlı referans.

## 9. Kalite Çıtası (bitmiş sayılma kriterleri)

- [ ] `dist/index.html` internetsiz kusursuz açılıyor; ilerleme panosu ve
      görev checkbox'ları kalıcı çalışıyor
- [ ] 11 görev + mezuniyet görevi tam kurgulu; her birinde hedef/adım/başarı
      kriteri/kendini sına/ipucu merdiveni eksiksiz
- [ ] En az 24 el yapımı SVG (UART/SPI/I2C dalga şekilleri dahil), iki temada
      okunaklı
- [ ] Tüm çözüm kodları `labs/` altında, ekip stilinde, yorumlu
- [ ] ZCU111'e özgü hiçbir değer teyitsiz yazılmamış
- [ ] Görev 10 buglı projesi gerçekten öğretici 3-4 hata içeriyor
- [ ] Saha kılavuzlarına çapraz referanslar yerinde
- [ ] Sözlük ve hızlı referans tam
