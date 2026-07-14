# Bölüm 2 — Tanış: Zynq ve ZCU111

Bölüm 1'de rolünü konuştuk; şimdi sahneyi tanıyalım. Masandaki yeşil kartın
adı **ZCU111**, kalbindeki büyük çipin adı **Zynq UltraScale+ RFSoC**
(XCZU28DR). Bu bölümün sonunda o çipin içindeki iki dünyayı ayırt edebilecek
ve kartın üzerindeki her önemli parçanın ne işe yaradığını söyleyebileceksin.
Bölüm sonunda da ilk görevin var: karta ilk kez dokunacaksın.

## SoC: tek çipte koca bir sistem

Eski nesil bir sistemde işlemci, bellek denetleyicisi, çevre birimleri ve
özel devreler anakart üzerinde ayrı çipler olurdu. SoC (system on chip)
yaklaşımı bunların hepsini tek silikon pakete toplar: daha az yer, daha az
güç, çok daha hızlı iç bağlantılar. Zynq ailesi bu fikri bir adım öteye
taşır ve tek pakete yalnızca işlemci sistemini değil, kocaman bir FPGA'yı da
koyar. Yani çipin içinde iki dünya yan yana yaşar:

{{svg:sema-03-zynq-kusbakisi.svg|Şekil 3 — Zynq UltraScale+ kuşbakışı: solda sabit işlemci sistemi (PS), sağda programlanabilir lojik (PL), aralarında AXI köprüleri.}}

## PS — Processing System: sabit, hazır, tanıdık

**PS (Processing System — işlemci sistemi)** çipin silikonda sabit
dökülmüş yarısıdır; sen hiçbir şey yapmasan da oradadır ve çalışır.
İçinde üç ana grup var:

- **APU (Application Processing Unit):** 4 adet **Arm Cortex-A53**
  çekirdeği. Linux koşturabilecek sınıfta uygulama işlemcileri — biz bu
  yolculukta üzerlerinde bare-metal (işletim sistemsiz) kod çalıştıracağız.
- **RPU (Real-time Processing Unit):** 2 adet **Arm Cortex-R5F** çekirdeği.
  Gerçek zaman için tasarlanmış, davranışı öngörülebilir çekirdekler;
  Bölüm 1'deki "doğru cevabın geç gelmesi yanlış cevaptır" cümlesinin
  silikondaki karşılığı.
- **Sabit çevre birimleri:** UART, I2C, SPI, GPIO (General Purpose I/O —
  genel amaçlı giriş/çıkış pinleri) denetleyicileri, DDR bellek
  denetleyicisi ve daha fazlası. Bunlar da silikonda hazır; her birinin
  Xilinx tarafından yazılmış, denenmiş driver'ı vardır.

PS çevre birimleri dış dünyaya **MIO** (multiplexed I/O — çoklanmış
giriş/çıkış) adı verilen sınırlı sayıda özel pin üzerinden çıkar. Bu
ayrıntı birazdan önem kazanacak.

## PL — Programmable Logic: boş tuval

**PL (Programmable Logic — programlanabilir lojik)** çipin FPGA yarısıdır:
milyonlarca küçük lojik hücreden örülü bir **FPGA fabric**'i (İngilizce
"fabric" = kumaş; hücrelerden dokunmuş, yeniden yapılandırılabilir bir
donanım örgüsü). Güç verildiğinde bu fabric boştur; donanımcı arkadaşların
Verilog/VHDL ile devre tasarlar, araç bu tasarımı **bitstream** (fabric'i
yapılandıran ikili dosya) haline getirir ve fabric ancak o yüklendiğinde bir
"devreye" dönüşür. Donanımcının
tasarladığı **IP**'ler (intellectual property core — hazır ya da özel devre
bloğu) işte burada yaşar: bir sinyal işleme zinciri, bir motor kontrol
bloğu ya da mütevazı bir AXI GPIO.

## Evlilik: AXI

PS ile PL ayrı dünyalar olsaydı bu çipin esprisi kalmazdı. İkisi **AXI**
(Advanced eXtensible Interface — Arm'ın çip içi veriyolu standardı)
köprüleriyle birbirine bağlıdır. Senin açından kritik sonuç şu: PS'ten
bakınca PL'deki bir IP, bir adres penceresinden görünen register'lar
kümesidir. Yani donanımcının IP'siyle konuşmak, Bölüm 4'te öğreneceğin
register okuma-yazma işinden ibarettir; köprünün ayrıntılarına Bölüm 9'da
gireceğiz.

## Aynı iş, iki dünya: PS IP ve PL IP

Kafa karıştıran ama ufuk açan bir gerçek: aynı işi çoğu zaman iki tarafta da
yapabilirsin. PS'te hazır bir UART var; donanımcı istese PL'ye de bir UART
IP'si koyar. Peki farkları ne?

| | PS çevre birimi | PL IP'si |
|---|---|---|
| Varlığı | Silikonda sabit, hep orada | Bitstream yüklenmeden yok |
| Esneklik | Sayısı ve özellikleri değişmez | İstediğin kadar, istediğin özellikte |
| Driver | Hazır ve denenmiş (Xilinx) | Donanımcının tablosuna göre çoğu zaman sen yazarsın |
| Pin erişimi | Sınırlı MIO pinleri | Kartın uygun her FPGA pini |

:::analoji Hazır mutfak, boş arsa
PS, mutfağı kurulu bir eve taşınmaktır: ocağın yeri bellidir, belki tam
istediğin yerde değildir ama bugün yemek pişirirsin. PL boş arsadır:
istediğin mutfağı kurarsın, ama mimar (donanımcı) çizmeden ve inşaat
(bitstream) bitmeden çay bile demleyemezsin.
:::

## Kart turu: ZCU111'in üzerinde ne var?

Çipten karta çıkalım. Aşağıdaki kroki fotoğraf değil, harita — parçaların
yerleri temsilidir, kimlikleri gerçektir.

{{svg:sema-04-kart-anatomisi.svg|Şekil 4 — ZCU111 kart anatomisi (temsili kroki): sarı işaretli DS50/SW19 ikilisine PS'ten bitstream'siz erişilir; LED, buton ve DIP switch kümesi PL pinlerindedir.}}

- **U1 — RFSoC:** Kartın ortasındaki büyük paket; az önce tanıştığın
  XCZU28DR. PS de PL de bu tek paketin içinde.
- **DDR4 SODIMM (J50):** PS'in ana belleği — dizüstü bilgisayardakine benzer
  şekilde sokete takılan 4 GB'lık modül. Bölüm 3'te bellek haritasında yerini
  göreceksin.
- **8 kullanıcı LED'i (DS11–DS18):** Sıra sıra dizilmiş yeşil LED'ler. Dikkat:
  bunlar **PL pinlerine** bağlıdır — birazdan bu ayrıntıya döneceğiz.
- **DIP switch (SW14) ve 5'li buton takımı (SW9–SW13):** 8 kutuplu anahtar
  ve yön tuşları gibi dizilmiş beş buton. Bunlar da PL tarafındadır; bu
  yolculukta kart turunda tanıyıp Bölüm 9'a kadar kenarda bırakacağız.
- **DS50 LED'i ve SW19 butonu:** Kartın gösterişsiz ama bizim için en değerli
  ikilisi. PS'in MIO pinlerine bağlılar (LED MIO23, buton MIO22) — yani
  bitstream olmadan, saf PS koduyla erişebileceğin tek LED ve tek buton.
  İlk görevlerin baş aktörleri bunlar olacak.
- **J83 micro-USB:** Tek kabloyla çok iş. Kartın üzerindeki FT4232 köprüsü bu
  tek USB bağlantısından bilgisayarına dört ayrı port sunar: Port A **JTAG**
  (programlama/debug arayüzü — harici bir probe gerekmez), Port B **PS
  UART0** (terminal çıktın buradan akar), kalanlar PL UART'ı ve sistem
  denetleyicisi içindir.
- **SD kart yuvası (J100) ve boot switch (SW6):** Kart açılışta nereden boot
  edeceğini SW6'nın konumundan öğrenir: JTAG, QSPI flash ya da SD kart.
  Açılış hikâyesinin tamamı Bölüm 3'te.
- **PMOD konnektörleri (J48/J49):** Hobi elektroniği dünyasından tanıdık
  genişletme soketleri; küçük sensör/deneme kartları buraya takılır.
- **Güç girişi:** Kartın kendi güç adaptörü ve açma-kapama anahtarı vardır;
  USB'den beslenmez.

## Dürüst bir itiraf: LED'ler neden hemen yanmayacak?

Yukarıda iki kez altını çizdik, şimdi açık konuşalım: kartın 8 LED'i, 5
butonu ve DIP switch'i PL pinlerindedir. PL güç verildiğinde boş bir fabric
olduğuna göre, bitstream yüklenmeden PS'ten o LED'lere giden hiçbir yol
yoktur. PS koduyla, bitstream'siz erişebildiğin kullanıcı arayüzü DS50 LED'i
ile SW19 butonundan ibarettir.

Bu yüzden ilk görevlerinde (Görev 1–5) tek LED ve tek butonla çalışacaksın.
Gösterişsiz görünebilir ama bu sınırın kendisi dersin ta kendisi: PS/PL
ayrımını slayttan değil, "LED'im neden yanmıyor?" sorusundan öğreneceksin.
Sabret — Bölüm 9'da donanımcının hazırladığı bitstream ile PL kapısını
açacağız ve 8 LED'lik yürüyen ışık orada seni bekliyor (Görev 7).

:::tuzak İnternetteki her Zynq örneği senin kartında çalışmaz
Web'de bulacağın "Zynq'te LED yakma" örneklerinin çoğu başka kartlar için
yazılmıştır ve LED'leri farklı yerlere (MIO'ya ya da farklı PL pinlerine)
bağlıdır. Kod hatasız derlenir, hiçbir şey yanmaz, saatler gider. Karta özgü
her bağlantıyı kendi kartının user guide'ından (ZCU111 için UG1271) doğrulama
refleksi, bu meslekte seni çok saatlik hüsranlardan kurtaracak.
:::

## RF tarafına bir pencere

Adındaki RF'yi görmüşsündür: RFSoC'un süper gücü, çipin içine gömülü radyo
frekansı veri dönüştürücüleridir — 8 adet RF-ADC (4.096 GSPS'ye kadar
örnekleme) ve 8 adet RF-DAC (6.554 GSPS'ye kadar). Yani bu çip antenden
gelen sinyali neredeyse doğrudan sayısallaştırabilir; kartın RF sinyalleri
XM500 ek kartı üzerinden SMA konnektörlere çıkar. Bu, ZCU111'i sıradan bir
geliştirme kartı olmaktan çıkaran özelliktir — ama bizim yolculuğumuzun
dışındadır. Önce yürümeyi öğreniyoruz; hazır olduğunda serinin *RF Örnekleme
Saha Kılavuzu*'na göz at.

Kart turunu bitirdin; artık eller devreye giriyor.

:::gorev no=0 zorluk=1 baslik="İlk Temas" kisa="İlk Temas"
[Hedef]
Kartı fiziksel olarak kur, JTAG boot moduna al ve bilgisayarınla kart
arasında doğru porttan çalışan bir seri terminal bağlantısı aç.

[Ön koşul]
Bölüm 0'daki kurulum listesi tamam (özellikle terminal programı kurulu);
Bölüm 1 ve 2 okundu.

[Adımlar]
1. Kartı kutusundan çıkar: antistatik torbayı metal bir zeminde açma, kartı
   kenarlarından tut, çipe ve konnektör pinlerine dokunma. Kuru ve iletken
   olmayan bir masa yüzeyi yeterli.
2. **SW6 boot switch'ini JTAG konumuna al: dört anahtarın hepsi ON.**
   Kart fabrikadan QSPI32 konumunda gelir (ON, ON, OFF, ON) — yani büyük
   ihtimalle bir anahtarı değiştirmen gerekecek. SW6'nın kart üzerindeki
   yeri için Şekil 4'e bak.
3. Güç adaptörünü karta bağla ama güç anahtarını henüz açma.
4. J83 micro-USB konnektörünü bilgisayarına bağla.
5. Bilgisayarında (Windows 10) seri portları bul. FT4232 köprüsü tek kablodan
   birden fazla COM portu çıkarır; terminal çıktısı **PS UART0 = Port B**'den
   gelir — tipik olarak dördün ikincisi, ama COM numaraları makineden makineye
   değişir, elinle doğrula (emin olamazsan İpucu 2'ye bak). Portları görmenin
   en kolay yolu **Aygıt Yöneticisi → Bağlantı Noktaları (COM & LPT)**; istersen
   PowerShell'de tek satırla da listeleyebilirsin:

   ```komut
   Get-CimInstance Win32_SerialPort | Select-Object Name, DeviceID
   ```

6. Terminal programını o porta **115200 baud, 8 veri biti, parite yok,
   1 stop biti (115200-8N1)** ayarıyla bağla.
7. Kartın güç anahtarını aç.

[Başarı kriteri]
Doğru COM portunu belirledin ve terminal bağlantısı hatasız açık; karta
güç verdiğinde kartın güç LED'leri yanıyor (hangi LED'lerin güç durumunu
gösterdiğini kart user guide'ından — UG1271 — doğrula). Not: JTAG modunda
kart kendi başına boot etmez, terminalde yazı akmaması normaldir; kartı
SD/QSPI üzerinde hazır imajla açan ekiplerde burada bir açılış mesajı
görülür.

[Kendini sına]
- SW6'yı JTAG yerine SD konumunda bıraksaydın kart güç verilince ne yapmaya
  çalışırdı? (İpucu: cevabın tamamı Bölüm 3'te.)
- Tek micro-USB kablosundan hem JTAG hem UART geçiyor — bu nasıl mümkün
  oluyor, kartta bunu hangi çip sağlıyor?
- 115200-8N1 ayarındaki "8", "N" ve "1" nelerin kısaltması? (Tel seviyesindeki
  karşılıklarını Bölüm 8'de göreceksin; şimdilik terminal ayarı olarak bil.)

[Takıldıysan]
::ipucu İpucu 1 — Hiç seri port görünmüyorsa (sürücü sorunu)
Önce basit şüphelileri ele: kablo gerçekten veri kablosu mu (bazı micro-USB
kablolar yalnızca şarj içindir), farklı bir USB portu denedin mi, kartın güç
anahtarı açık mı (köprü devresi gücünü karttan alıyor olabilir — kapalıysa
açıp kabloyu çıkarıp tekrar tak)? Bunlar temizse sorun büyük ihtimalle FTDI
sürücüsüdür: Aygıt Yöneticisi'nde sarı ünlem işaretli ya da "Bilinmeyen aygıt"
görünüyorsa FTDI'nin **VCP (Virtual COM Port)** sürücüsünü FTDI'nin resmî
sitesinden indirip kur, sonra kabloyu çıkarıp tekrar tak — "Bağlantı Noktaları
(COM & LPT)" altında yeni COM girişleri belirmeli.
::/
::ipucu İpucu 2 — Dört port var, hangisi doğru?
Aradığın, FT4232'nin **ikinci arayüzü** (Port B). Aygıt Yöneticisi'nde
"Bağlantı Noktaları (COM & LPT)" altında aynı USB köprüsüne ait birden çok
"USB Serial Port (COMx)" girişi görürsün; bir COM portuna sağ tıklayıp
**Özellikler → Ayrıntılar → "Konum bilgisi"** (ya da "Bus reported device
description") alanına bakarsan hangi arayüz (A/B/C/D) olduğunu okuyabilirsin —
sen Port B'yi ararsın. Kestirme yol: COM numaralarını küçükten büyüğe sırala,
genelde ikincisi Port B'dir. Hâlâ emin değilsen hepsini not al: Görev 1'de
karttan ilk çıktıyı aldığında hangi portun konuştuğunu kesin olarak öğrenecek
ve bir daha unutmayacaksın.
::/
:::

Kartın masanda kurulu, terminalin bağlı, boot switch JTAG'da seni bekliyor.
Peki güç anahtarını açtığın o saniyede çipin içinde neler oluyor? Bir sonraki
bölümün konusu tam olarak bu.
