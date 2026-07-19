# Bölüm 13 — Ufuk Turu

Bölüm 12 meslek kültürünü ele aldı: savunmacı kod, Git iş akışı, etkili
soru sorma. Gömülü geliştirmenin günlük işlerini artık taşıyabilecek
donanımdasın. Ama bu yolculuk her şeyi anlatmadı — anlatamazdı da. Bu
bölüm bir kapanış değil, bir ufuk turudur: kariyerin boyunca adıyla
karşılaşacağın, bu dokümanın öğretmediği yedi kavrama açılan kısa bir
pencere. Amaç seni bu konularda uzman yapmak değil; biri toplantıda bu
terimleri andığında cevabının "hiç duymadım" değil, "biliyorum, henüz
derinine inmedim" olmasını sağlamak. Mezuniyet Görevi'nden (Bölüm 14)
önceki son mola.

## DMA ve Scatter-Gather

Neden önemli: bir gün veriyi CPU'yu meşgul etmeden taşıman gerekecek ve
cevap DMA olacak (Direct Memory Access — bellek bölgeleri arasında
veriyi CPU'suz taşıyan donanım). Bölüm 6, cache ile DDR arasındaki
coherency (tutarlılık) sorununa değinmişti; DMA tam olarak o sorunun
arkasındaki donanımdır — CPU transferi başlatır, başka işe geçer,
transfer bittiğinde interrupt ile haber alır. Pratikte veri nadiren tek
bir bitişik bellek bloğunda durur; bir ağ paketi ya da görüntü frame'i
birden çok, bitişik olmayan adrese dağılmış olabilir. **Scatter-gather**,
DMA denetleyicisine "şu adresten şu kadar oku, sonra şu adrese atla ve
oradan devam et" talimatını veren bir **descriptor** (tanımlayıcı kayıt)
zinciri kurmanı sağlar — tek bir DMA işlemi dağınık parçaları tek hedefte
toplayabilir ya da tek kaynağı birden çok hedefe dağıtabilir. Hazır
olduğunda serinin *Bellek Mimarisi Saha Kılavuzu*'na başvur; DMA'nın
bellek haritasıyla ilişkisini ayrıntısıyla orada bulursun.

## Watchdog

Neden önemli: kartın masandan ayrılıp sahaya, müşteri tesisine gittiği
gün, orada reset düğmesine basacak kimse olmayacak. **Watchdog**,
yazılımının düzenli aralıklarla "hâlâ hayattayım" demek için "beslediği"
(feed/kick) bir zamanlayıcıdır; besleme gelmezse — yazılım kilitlendiği,
sonsuz döngüye girdiği ya da bir ISR hiç dönmediği için — donanım
kendini resetler. ZynqMP'nin kendi watchdog IP'si vardır; adres ve
register ayrıntıları için TRM'ye (Technical Reference Manual) başvur, bu
doküman yalnızca kavramı tanıtıyor. Tuzağını da bil: besleme mantığı
yanlış yere konursa (örneğin gerçekten asılı kalmış bir task beslemeyi
sürdürüyorsa) watchdog hiçbir şeyi kurtarmaz — yalnızca yalan söyler.
Doğru tasarımda besleme, sistemin gerçekten sağlıklı olduğunu doğrulayan
bir noktadan çıkar.

## DDR, QSPI, eMMC: depolama ailesini ayırt etmek

Neden önemli: "burada hangi bellek kullanılıyor" sorusu daha ilk donanım
seçimi toplantısında önüne gelecek ve üçünü karıştırmak pahalı bir
hataya dönüşebilir. **DDR** (Double Data Rate RAM) hızlıdır ama
**volatile**'dır (uçucu): güç kesilince içeriği silinir; kartın çalışma
belleğidir. **QSPI** (Quad SPI flash) yavaştır ama kalıcıdır;
kapasitesi küçük olduğundan genellikle boot imajını (boot.bin, Bölüm 3)
tutar. **eMMC** (embedded MultiMediaCard) QSPI'dan çok daha büyük
kapasiteli, blok tabanlı kalıcı depolama sunar — bir Linux kök dosya
sistemini barındıracak kadar geniştir — ama erişimi QSPI kadar basit
değildir; denetleyici ve dosya sistemi katmanı ister. Üçünü birlikte şöyle
düşün: DDR "o an üzerinde çalıştığın bellek", QSPI "kartın nasıl
açılacağını tutan talimat", eMMC "kalıcı dosyaların ambarı". Hazır
olduğunda serinin *Bellek Mimarisi Saha Kılavuzu*'na başvur; üçünün adres
haritasındaki yeri ve hız sınıfı orada karşılaştırmalı olarak var.

## Device Tree ve Linux tabanlı Zynq dünyası

Neden önemli: bu doküman boyunca yaşadığın dünya **bare-metal** (işletim
sistemsiz) ve FreeRTOS'tu; ama aynı Zynq kartı bambaşka bir hayat da
sürebilir — üzerinde tam bir **Linux** çekirdeği koşabilir. O dünyada
donanımı tarif etme biçimin değişir: `xparameters.h` içindeki sabitlerin
yerini **device tree** (`.dts`/`.dtb` dosyaları) alır; hangi çevre
biriminin hangi adreste oturduğunu, hangi interrupt'ı kullandığını artık
derleme zamanı sabitleri değil, çekirdeğin çalışma zamanında okuduğu bu
ağaç belirler. Xilinx/AMD ekosisteminde bu Linux imajını, kök dosya
sistemini ve device tree'yi bir arada üreten araç **PetaLinux**'tur —
varlığını bil; kendi konfigürasyon akışı ve öğrenme eğrisi vardır. Hangi
dünyayı seçeceğin ("bare-metal mi, RTOS mu, Linux mu") gereksinime
bağlıdır: sıkı zamanlama garantisi gerekiyorsa FreeRTOS'a yakın dur; ağ
yığını, dosya sistemi ya da birden çok kullanıcı alanı süreci gerekiyorsa
Linux'un ek karmaşıklığını kabul et. Hazır olduğunda serinin *Ethernet
Saha Kılavuzu*'na başvur; Linux tabanlı bir Zynq sisteminin varlık sebebi
çoğu zaman zaten ağdır.

## Secure Boot ve kriptografi

Neden önemli: kartın JTAG'e bağlı, lab masasında durduğu sürece "isteyen
istediği kodu yükler" gerçek bir dert değildir. Ürün sahaya çıktığında
ise birinin cihazına sahte firmware yükleyip yeniden satması ya da
zararlı kod koşturması ciddi bir tehdide dönüşür. **Secure boot**, Bölüm
3'te tanıştığın BootROM'un FSBL'yi (ve zincirdeki sonraki her imajı)
çalıştırmadan önce kriptografik olarak doğrulaması sürecidir: imaj özel
anahtarla **imzalanır**, her açılışta bu imza, cihazın gömülü anahtar
deposunda ya da **e-fuse**'larda (çipe yazılan kalıcı, geri döndürülemez
bit sigortaları) saklanan bir açık anahtara ya da **hash**'e (bir veriden
üretilen sabit uzunluklu parmak izi) karşı denetlenir; imza doğrulanmazsa
cihaz açılmayı reddeder. Buna **chain of trust** (güven zinciri) denir —
hiçbir katman, bir sonrakini doğrulamadan çalıştırmaz. Lab aşamasında
bunu hiç düşünmeyeceksin; ama ürün sahaya çıktıktan sonra hafife almak,
geri alması en pahalı hatalardan biridir.

## JESD204 ve PCIe: yüksek hızlı arayüzler

Neden önemli: ZCU111'inin Bölüm 2'de tanıtılan
RF örnekleme yeteneği tümüyle bu arayüzler üzerinden işler. **JESD204**
(B/C revizyonları), yüksek hızlı ADC/DAC (analog-sayısal / sayısal-analog
çevirici) çipleriyle FPGA arasında gigabit ölçeğinde veriyi seri hatlar
üzerinden taşıyan endüstri standardı bir protokoldür — RFSoC içindeki
RF-ADC/RF-DAC bloklarının verisini PL tarafına ulaştıran yol budur.
**PCIe** (PCI Express) daha genel amaçlıdır: kartları birbirine ya da
bir anakarta bağlayan yüksek bant genişlikli, paket tabanlı arayüz;
sunucu sınıfı sistemlerde hızlandırıcı kart bağlamanın standart yolu.
İkisinin ortak noktası: AXI'nin (Bölüm 9) yalın valid/ready el
sıkışmasından çok daha karmaşık fiziksel katman tasarımlarıdır — çok
kanallı, senkronizasyon ve **link training** (bağlantının otomatik
kalibrasyonu) isteyen yapılar. Bu dokümanın kapsamı dışındadır; adını
duyduğunda "AXI'nin çok daha karmaşık bir muadili" diye tanıman şimdilik yeter. Hazır
olduğunda serinin *RF Örnekleme Saha Kılavuzu*'na başvur; JESD204'ün
ZCU111 üzerindeki gerçek uygulamasını orada bulursun.

## Unit Test ve CI

Neden önemli: şimdiye kadar yazdığın her satırı doğrudan gerçek donanım
üzerinde koşturup gözledin — ama ekip büyüdükçe her değişikliği karta
elle yükleyip denemek ölçeklenmez. Sağlıklı bir gömülü kod tabanı,
donanıma dokunan katmanı (register erişimi, sürücü çağrıları) dokunmayan
katmandan (protokol ayrıştırma, durum makinesi mantığı, CLI komut
ayrıştırma — Bölüm 14'te yazacağın türden kod) bilinçli olarak ayırır.
İkinci katman, karta hiç bağlanmadan sıradan bir bilgisayarda **unit
test** (birim testi) çerçeveleriyle test edilebilir; bu da **CI**'a
(Continuous Integration — sürekli tümleştirme) bağlanır: her commit
otomatik bir build ve test koşusunu tetikler, hatalar bir insana ulaşmadan
yakalanır. Ekibimizde "bu fonksiyon donanımdan ayrılabilir mi" sorusu
tasarımın erken adımlarından biridir — cevap çoğunlukla evettir ve bu
ayrım test edilebilirlikle kod okunurluğunu aynı anda iyileştirir.

## Adını bilmen yeter

Bu bölümdeki kavramları ezberlemeye çalışma — amaç yalnızca biri adını
andığında ne işe yaradığını hatırlaman:

| Kavram | Tek cümle: ne yapar |
|---|---|
| DMA | CPU'yu meşgul etmeden bellek bölgeleri arasında veri taşıyan donanım birimi. |
| Scatter-gather | Bitişik olmayan bellek bloklarını tek işlemde toplamayı/dağıtmayı DMA denetleyicisine tarif eden descriptor zinciri. |
| Watchdog | Yazılım "hâlâ hayattayım" sinyalini kesince donanımı otomatik resetleyen zamanlayıcı. |
| DDR | Kartın hızlı ama volatile (güç kesilince silinen) çalışma belleği. |
| QSPI | Yavaş ama kalıcı flash bellek; genellikle boot imajını (boot.bin) tutar. |
| eMMC | QSPI'dan çok daha büyük, blok tabanlı kalıcı depolama; Linux kök dosya sistemini barındırır. |
| Device tree | Hangi çevre biriminin hangi adreste/interrupt'ta olduğunu Linux'a çalışma zamanında söyleyen donanım ağacı. |
| PetaLinux | Xilinx/AMD'nin Linux imajı, kök dosya sistemi ve device tree'yi birlikte üreten araç seti. |
| Secure boot | Her açılış adımının bir sonrakinin imzasını doğrulayarak yüklediği zincir. |
| e-fuse | Çipe yazılan kalıcı, geri döndürülemez bit sigortaları; doğrulama anahtarı ya da hash saklayabilir. |
| Hash | Bir veriden üretilen sabit uzunluklu parmak izi; verinin bütünlüğünü doğrulamakta kullanılır. |
| Chain of trust | Hiçbir katmanın bir sonrakini doğrulamadan çalıştırmadığı güvenlik modeli. |
| JESD204 | Yüksek hızlı ADC/DAC çipleriyle FPGA arasında gigabit ölçeğinde veriyi seri hatlar üzerinden taşıyan protokol. |
| PCIe | Kartlar arası ya da kart-anakart arası yüksek bant genişlikli, paket tabanlı genel amaçlı arayüz. |
| Link training | Yüksek hızlı seri bağlantının otomatik kalibrasyon süreci. |
| Unit test | Donanımdan bağımsız kodu, kart olmadan sıradan bilgisayarda test etme yöntemi. |
| CI (Continuous Integration) | Her commit'te otomatik build ve test koşturup hataları insana ulaşmadan yakalayan sistem. |
| TRM (Technical Reference Manual) | Bir çipin register ve adres ayrıntıları için üreticinin resmi, eksiksiz kaynağı. |
| Root filesystem (kök dosya sistemi) | Linux'un çalışması için gereken dosya/dizin hiyerarşisini tutan depolama alanı. |

Yedi kavramın hepsine bugün hâkim olman beklenmiyor; bu bölümün tek işi
her biri için zihnine bir kanca bırakmaktı. Şimdi sıra, kazandığın bütün
becerileri — register okumak, interrupt yapılandırmak, I2C üzerinden
haberleşmek, FreeRTOS task'ı yazmak — tek bir projede birleştirmekte.
Sırada Mezuniyet Görevi var.
