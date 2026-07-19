# Bölüm 2 — Zynq ve ZCU111 ile Tanış

Bölüm 1'de rolünü konuştuk; şimdi sahneyi tanıyalım. Masandaki yeşil
kartın adı **ZCU111**, çekirdeğindeki büyük çipin adı **Zynq UltraScale+
RFSoC** (XCZU28DR). Bu bölümün sonunda o çipin içindeki iki dünyayı
ayırt edebilecek ve kart üzerindeki her ana bileşenin ne işe yaradığını
söyleyebileceksin. Sonunda da ilk görevin bekliyor: kartla ilk
fiziksel temas.

## SoC: bütün sistem tek çipte

Önceki kuşak sistemlerde işlemci, bellek kontrolcüsü, çevre birimleri ve
özel devreler anakart üzerinde ayrı çipler halindeydi. SoC (system on
chip — sistem-çipi) yaklaşımı bunların tamamını tek silikon pakette
toplar: daha az kart alanı, daha düşük güç, çok daha hızlı iç
bağlantılar. Zynq ailesi fikri bir adım öteye taşır: aynı pakete
yalnızca bir işlem sistemi değil, hatırı sayılır bir FPGA da
yerleştirir. Çipin içinde iki ayrı dünya yan yana yaşar:

{{svg:sema-03-zynq-kusbakisi.svg|Şekil 3 — Zynq UltraScale+ kuşbakışı: solda sabit Processing System (PS), sağda Programmable Logic (PL), aralarında AXI köprüleri.}}

## PS — Processing System: sabit, hazır, tanıdık

**PS (Processing System)**, çipin silikonda sabitlenmiş yarısıdır; sen
ne yaparsan yap oradadır ve çalışır. Üç ana gruptan oluşur:

- **APU (Application Processing Unit):** dört adet **Arm Cortex-A53**
  çekirdeği. Linux koşturabilecek sınıfta uygulama işlemcileri; bu
  yolculukta üzerlerinde bare-metal (işletim sistemsiz) kod
  koşturacağız.
- **RPU (Real-time Processing Unit):** iki adet **Arm Cortex-R5F**
  çekirdeği. Gerçek zamanlı davranış ve öngörülebilir zamanlama için
  tasarlanmış çekirdekler — Bölüm 1'deki "geç gelen doğru cevap yanlış
  cevapla aynı şeydir" cümlesinin silikondaki karşılığı.
- **Sabit çevre birimleri:** UART, I2C, SPI ve GPIO (General Purpose
  Input/Output — genel amaçlı giriş/çıkış) kontrolcüleri, DDR bellek
  kontrolcüsü ve daha fazlası. Bunlar da silikonda sabittir; her birinin
  Xilinx tarafından yazılmış ve doğrulanmış driver'ı vardır.

PS çevre birimleri dış dünyaya **MIO** (multiplexed I/O — çoklanmış
giriş/çıkış) adlı sınırlı sayıda özel pin üzerinden çıkar. Bu ayrıntı
birazdan önem kazanacak.

## PL — Programmable Logic: boş fabrika zemini

**PL (Programmable Logic)**, çipin FPGA yarısıdır: milyonlarca küçük
mantık hücresinden dokunmuş bir **FPGA fabric** ("fabric" terimi, bu
hücrelerden kurulan yeniden yapılandırılabilir donanım dokusunu
anlatır). Güç verildiğinde bu doku boştur; donanımcı arkadaşların
Verilog/VHDL ile devre tasarlar, araç zinciri tasarımı bir
**bitstream**'e (fabric'i yapılandıran ikili dosya) çevirir — fabric
ancak o bitstream yüklendiğinde işleyen bir "devre" haline gelir.
Donanım mühendislerinin tasarladığı **IP** blokları (intellectual
property core — hazır ya da özel devre blokları) burada yaşar: bir
sinyal işleme zinciri, bir motor kontrol bloğu ya da mütevazı bir AXI
GPIO.

## Buluşma noktası: AXI

PS ile PL bütünüyle ayrı dünyalar olsaydı çipin bir anlamı kalmazdı.
İkisini **AXI** (Advanced eXtensible Interface — Arm'ın çip içi bus
standardı) köprüleri bağlar. Senin için kritik sonuç şu: PS tarafından
bakıldığında PL'deki bir IP, bir adres penceresinden görünen register
kümesidir. Yani donanım mühendisinin IP'siyle konuşmak, Bölüm 4'te
öğreneceğin register okuma/yazma işlemlerine iner; köprünün ayrıntısını
Bölüm 9'da ele alıyoruz.

## Aynı iş, iki dünya: PS çevre birimi ve PL IP

Başta kafa karıştıran ama sonunda ufuk açan bir gerçek: aynı işlev çoğu
zaman iki tarafta da gerçeklenebilir. PS'te zaten bir UART var; donanım
mühendisi pekâlâ PL'ye de bir UART IP koyabilir. İkisini ne ayırır?

| | PS çevre birimi | PL IP |
|---|---|---|
| Varlık | Silikonda sabit, her zaman orada | Bitstream yüklenene kadar yok |
| Esneklik | Sayısı ve özellikleri sabit | Gerektiği sayıda, gerektiği kadar özelleştirilmiş |
| Driver | Hazır ve doğrulanmış (Xilinx) | Çoğu zaman donanımcının tablosuna göre sen yazarsın |
| Pin erişimi | MIO pinleriyle sınırlı | Karttaki uygun her FPGA pini |

:::analoji PS/PL: anahtar teslim hat ile boş fabrika zemini
PS, anahtar teslim kurulmuş bir üretim hattına girmek gibidir: makineler
yerli yerinde — belki tam senin yerleştireceğin gibi değil, ama üretime
bugün başlarsın. PL boş fabrika zeminidir: hattı istediğin gibi
kurarsın, ama proje (donanım mühendisinin tasarımı) çizilip kurulum
(bitstream) tamamlanana kadar tek parça bile üretemezsin.
:::

## Kart turu: ZCU111'in üzerinde ne var?

Çipten karta geçiyoruz. Aşağıdaki şema fotoğraf değil harita — bileşen
yerleşimi temsili, kimlikler doğru.

{{svg:sema-04-kart-anatomisi.svg|Şekil 4 — ZCU111 kart anatomisi (temsili kroki): sarıyla işaretli DS50/SW19 çifti bitstream olmadan PS'ten erişilebilir; LED'ler, butonlar ve DIP switch kümesi PL pinlerinde oturur.}}

- **U1 — RFSoC:** Kartın ortasındaki büyük paket — yukarıda tanıştığın
  XCZU28DR. PS de PL de bu tek paketin içinde.
- **DDR4 SODIMM (J50):** PS'in ana belleği — laptop bellek modülüne
  benzer soketli yapıda 4 GB'lık bir modül. Bölüm 3'te memory map
  üzerinde yerini bulacaksın.
- **8 kullanıcı LED'i (DS11–DS18):** Yeşil LED sırası. Dikkat: bunlar
  **PL pinlerine** bağlı — bu noktaya birazdan dönüyoruz.
- **DIP switch (SW14) ve 5'li buton kümesi (SW9–SW13):** 8 konumlu bir
  anahtar ve yön tuşları gibi dizilmiş beş buton. Bunlar da PL tarafında;
  kart turunda yerlerini belirleyip Bölüm 9'a kadar kenara koyuyoruz.
- **DS50 LED'i ve SW19 butonu:** Kartın gösterişsiz ama bizim için en
  değerli ikilisi. PS MIO pinlerine bağlılar (LED MIO23'te, buton
  MIO22'de) — yani bitstream olmadan, saf PS kodundan erişilebilen tek
  LED ve tek buton bunlar. İlk görevlerinin merkezinde bu ikili olacak.
- **J83 micro-USB:** Tek başına çok iş gören bir kablo. Karttaki FT4232
  köprü çipi bu tek USB bağlantısı üzerinden bilgisayarına dört ayrı
  port açar: Port A **JTAG** (programlama/debug arayüzü — harici prob
  gerekmez), Port B **PS UART0** (terminal çıktın buradan akar), kalan
  ikisi PL UART ile sistem kontrolcüsüne hizmet eder.
- **SD kart yuvası (J100) ve boot anahtarı (SW6):** Kart güç
  verildiğinde boot kaynağını SW6'nın konumundan belirler: JTAG, QSPI
  flash ya da SD kart. Boot hikâyesinin tamamı Bölüm 3'te.
- **PMOD konnektörleri (J48/J49):** Hobi elektroniği dünyasından tanıdık
  genişleme soketleri; küçük sensör ya da prototip kartları buraya
  takılır.
- **Güç girişi:** Kartın kendi güç adaptörü ve güç anahtarı var; USB'den
  beslenmez.

## Dürüst bir tespit: LED'ler neden hemen yanmayacak

İki kez vurguladık, artık açıkça söyleyelim: kartın 8 LED'i, 5 butonu ve
DIP switch'i tamamen PL pinlerinde. PL güç verildiğinde boş bir fabric
olduğuna göre, bitstream yüklenene kadar PS'ten o LED'lere giden bir yol
yok. Bitstream olmadan PS kodundan ulaşılabilen tek kullanıcı arayüzü
DS50 LED'i ile SW19 butonu.

Bu yüzden ilk görevlerin (Görev 1–5) yalnızca tek LED ve tek butonla
çalışacak. Gösterişsiz görünebilir, ama bu kısıt dersin ta kendisi: PS/PL ayrımını bir slayttan değil, "LED'im neden yanmıyor"
sorusundan öğreneceksin. Sabret — Bölüm 9'da donanım ekibinin
hazırladığı bitstream ile PL kapısını açıyoruz; sekiz LED'lik yürüyen ışık
deseni seni orada bekliyor (Görev 7).

:::tuzak İnternetteki her Zynq örneği senin kartında çalışmaz
İnternette bulunan "Zynq'te LED yakma" örneklerinin çoğu başka bir kart
için, LED'leri başka pinlere (MIO ya da değil) bağlanmış halde
yazılmıştır. Kod hatasız derlenir, hiçbir şey yanmaz, saatler
kaybedilir. Karta özgü her bağlantıyı kendi kartının kullanıcı
kılavuzundan (ZCU111 için UG1271) doğrulama alışkanlığı, bu meslekte
sana çok saat kazandıracak.
:::

## RF tarafına bir pencere

Kartın adındaki RF'yi fark etmişsindir: RFSoC'yi tanımlayan yetenek,
doğrudan çipin içine gömülü radyo frekansı veri dönüştürücüleridir —
8 RF-ADC (4.096 GSPS'e kadar örnekleme) ve 8 RF-DAC (6.554 GSPS'e
kadar). Bu çip antenden gelen sinyali neredeyse doğrudan
sayısallaştırabilir; kartın RF sinyalleri XM500 ek kartı üzerinden SMA
konnektörlerine çıkar. ZCU111'i sıradan bir geliştirme kartından ayıran
budur — ama bu yolculuğun kapsamı dışındadır. Önce yürümeyi öğreniyoruz;
hazır olduğunda serinin *RF Örnekleme Saha Kılavuzu*'na başvur.

Kart turu tamamlandı; sıra elini karta sürmeye geldi.

:::gorev no=0 zorluk=1 baslik="İlk Temas" kisa="İlk Temas"
[Hedef]
Kartı fiziksel olarak kurmak, JTAG boot moduna almak ve bilgisayarınla
kart arasında doğru port üzerinde çalışan bir seri terminal bağlantısı
kurmak.

[Ön koşul]
Bölüm 0'daki kurulum kontrol listesi tamam (özellikle bir terminal
programı kurulu); Bölüm 1 ve 2 okundu.

[Adımlar]
1. Kartı ambalajından çıkar: antistatik torbayı metal yüzey üzerinde
   açma, kartı kenarlarından tut, çipe ve konnektör pinlerine dokunma.
   Kuru ve iletken olmayan bir masa yüzeyi yeterli.
2. **SW6 boot anahtarını JTAG konumuna al: dört anahtarın dördü de ON.**
   Kart fabrikadan QSPI32 ayarıyla gelir (ON, ON, OFF, ON) — yani büyük
   olasılıkla tek bir anahtarı çevirmen gerekecek. SW6'nın karttaki yeri
   için Şekil 4'e bak.
3. Güç adaptörünü karta bağla, ama gücü henüz açma.
4. J83 micro-USB konnektörünü bilgisayarına bağla.
5. Bilgisayarında (Windows 10) seri portları bul. FT4232 köprüsü tek
   kablo üzerinden birden fazla COM portu açar; terminal çıktısı
   **PS UART0 = Port B**'den gelir — genellikle dördün ikincisi, ama COM
   numaralandırması makineden makineye değişir; doğrudan doğrula (emin
   değilsen İpucu 2'ye bak). Portları görmenin en kolay yolu
   **Device Manager → Ports (COM & LPT)**; istersen tek PowerShell
   komutuyla da listeleyebilirsin:

   ```komut
   Get-CimInstance Win32_SerialPort | Select-Object Name, DeviceID
   ```

6. Terminal programını o porta **115200 baud, 8 veri biti, parity yok,
   1 stop biti (115200-8N1)** ayarıyla bağla.
7. Kartın gücünü aç.

[Başarı kriteri]
Doğru COM portunu belirledin ve terminal bağlantısı hatasız açık; güç
verildiğinde kartın güç LED'leri yanıyor (hangi LED'lerin güç durumunu
gösterdiğini kart kullanıcı kılavuzundan — UG1271 — doğrula). Not: kart
JTAG modunda kendi başına boot etmez; terminalde hiçbir çıktı
görünmemesi beklenen davranıştır. SD/QSPI üzerinde hazır imajla açan
ekiplerde ise burada bir boot mesajı görünür.

[Kendini sına]
- SW6'yı JTAG yerine SD konumunda bıraksaydın kart güç verildiğinde ne
  yapmaya çalışırdı? (İpucu: tam cevap Bölüm 3'te.)
- Tek bir micro-USB kablo hem JTAG hem UART taşıyor — bu nasıl mümkün
  oluyor ve karttaki hangi çip sağlıyor?
- 115200-8N1 ayarındaki "8", "N" ve "1" neyi ifade eder? (Kablo
  düzeyindeki karşılıklarını Bölüm 8'de göreceksin; şimdilik bir
  terminal ayarı olarak kabul et.)

[Takıldıysan]
::ipucu İpucu 1 — Hiç seri port görünmüyor (sürücü sorunu)
Önce basit şüphelileri ele: kablo gerçekten veri kablosu mu (bazı
micro-USB kablolar yalnızca güç taşır), farklı bir USB portu denedin mi,
kartın güç anahtarı açık mı (köprü çipi gücünü karttan alıyor olabilir —
kapalıysa aç, kabloyu çıkarıp yeniden tak)? Bunlar temizse sorun büyük
olasılıkla FTDI sürücüsüdür: Device Manager'da sarı ünlem işaretli ya da
"Unknown device" etiketli bir cihaz görüyorsan FTDI'nin resmi sitesinden
**VCP (Virtual COM Port)** sürücüsünü indirip kur, sonra kabloyu çıkarıp
yeniden tak — "Ports (COM & LPT)" altında yeni girişler görünmeli.
::/
::ipucu İpucu 2 — Dört port görünüyor; doğrusu hangisi?
Aradığın, FT4232'nin **ikinci arayüzü** (Port B). Device Manager'da
"Ports (COM & LPT)" altında aynı USB köprüsüne ait birden fazla "USB
Serial Port (COMx)" girişi göreceksin; bir COM portuna sağ tıklayıp
**Properties → Details → "Location information"** (ya da "Bus reported
device description") alanına bak — girişin hangi arayüze (A/B/C/D)
karşılık geldiğini görürsün; aradığın Port B. Kestirme: COM numaralarını
küçükten büyüğe sırala; ikincisi genellikle Port B'dir. Hâlâ emin
değilsen hepsini not et: Görev 1'de karttan ilk çıktıyı aldığında hangi
portun aktif olduğunu kesin olarak belirleyeceksin ve bir daha tahmin
etmen gerekmeyecek.
::/
:::

Kart masanda kurulu, terminal bağlı, boot anahtarı JTAG modunda
bekliyor. Peki gücü açtığın anda çipin içinde ne olur? Bir sonraki
bölümün konusu tam olarak bu.
