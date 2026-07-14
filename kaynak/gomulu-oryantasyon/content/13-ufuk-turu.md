# Bölüm 13 — Ufuk Turu

Bölüm 12'de meslek kültürünü konuştuk: savunmacı kod, git akışı, doğru soru
sorma. Artık gömülü dünyanın günlük işini yapabilecek donanımdasın. Ama bu
yolculuk her şeyi kapsamadı — kapsayamazdı da. Bu bölüm bir kapanış değil,
bir ufuk turu: kariyerinde adını sık sık duyacağın, bu dokümanın sana
öğretmediği yedi kavrama kısa birer pencere. Amaç seni uzman yapmak değil;
biri bu kelimeleri toplantıda geçirdiğinde "hiç duymadım" değil, "biliyorum,
derinliğine henüz girmedim" diyebilmen. Mezuniyet Görevi'ne (Bölüm 14)
geçmeden önce son bir mola.

## DMA ve Scatter-Gather

Bunu neden umursayacaksın: bir gün "CPU'yu meşgul etmeden veri taşı" ihtiyacı
karşına çıkacak ve cevap DMA (Direct Memory Access — CPU'ya uğramadan
bellekler arası veri taşıyan donanım) olacak. Bölüm 6'da cache ile DDR
arasındaki tutarlılık sorununa değinmiştik; DMA tam da o sorunun kaynağı olan
donanımdır — CPU bir transferi başlatır, sonra başka işine döner, transfer
bittiğinde bir interrupt ile haberdar olur. Gerçek dünyada veriler nadiren
tek bir bitişik bellek bloğunda durur; bir ağ paketi, bir görüntü çerçevesi
parça parça, farklı adreslerde yaşayabilir. **Scatter-gather**, DMA
denetleyicisine "şu adresten şu kadar al, sonra şu adrese atla, oradan da al"
diyen bir **descriptor** (tanımlayıcı) zinciri kurmanı sağlar — tek bir DMA
işlemi, dağınık parçaları tek bir hedefe toplar ya da tek bir kaynağı dağınık
hedeflere yayar. Hazır olduğunda serinin *Bellek Mimarisi Saha Kılavuzu*'na
göz at; DMA'nın bellek haritasıyla nasıl konuştuğunu orada bulacaksın.

## Watchdog

Bunu neden umursayacaksın: kartın masandan kalkıp sahaya, müşteriye gittiği
gün, kimse orada "reset butonuna bas" diyemeyecek. **Watchdog** (bekçi
zamanlayıcı), yazılımının düzenli aralıklarla "hâlâ hayattayım" diye
"beslediği" (feed/kick) bir sayaçtır; besleme gelmezse — yazılım kilitlenmiş,
sonsuz döngüye girmiş ya da bir ISR asla dönmemişse — donanım kendini resetler.
ZynqMP'nin kendine ait bir watchdog IP'si vardır; adres ve register
ayrıntıları için TRM'e (Technical Reference Manual — teknik referans kılavuzu)
bakman gerekecek, biz burada sadece fikri tanıtıyoruz. Tuzağı da bil: besleme
işini yanlış yere koyarsan (örneğin gerçekten takılmış bir task'ın kendisi
besliyorsa) watchdog hiçbir şeyi kurtarmaz, sadece yalan söyler. Doğru
tasarımda besleme, sistemin gerçekten sağlıklı olduğunu doğrulayan bir
noktadan gelir.

## DDR, QSPI, eMMC: Depolama Ailesinin Farkları

Bunu neden umursayacaksın: "hangi bellek burada kullanılır" sorusu ilk
donanım seçimi toplantısında karşına çıkar ve üçünü karıştırmak pahalı bir
hataya dönüşebilir. **DDR** (Double Data Rate — çift veri hızlı RAM) hızlı
ama **uçucu** (volatile): güç kesilince içeriği kaybolur, kartın çalışma
belleğidir. **QSPI** (Quad SPI — dört hatlı SPI flash) yavaş ama kalıcıdır;
küçük boyutuyla genelde önyükleme imajını (boot.bin, Bölüm 3) tutar. **eMMC**
(embedded MultiMediaCard) ise QSPI'den çok daha büyük kapasiteli, blok
tabanlı kalıcı depolamadır — bir Linux kök dosya sistemini (root filesystem)
barındıracak kadar geniştir, ama QSPI kadar basit erişilmez; bir denetleyici
ve dosya sistemi katmanı ister. Üçünü bir arada düşün: DDR "şu anki iş
belleğin", QSPI "kartın nasıl ayağa kalkacağının tarifi", eMMC "kalıcı
dosyaların deposu". Hazır olduğunda serinin *Bellek Mimarisi Saha
Kılavuzu*'na göz at; orada bu üçünün adres haritasındaki yerini ve hız
sınıflarını karşılaştırmalı göreceksin.

## Device Tree ve Linux'lu Zynq Dünyası

Bunu neden umursayacaksın: bu doküman boyunca yaşadığın dünya **bare-metal**
(işletim sistemsiz) ve FreeRTOS idi; ama aynı Zynq kartı tamamen farklı bir
hayat da yaşayabilir — üzerinde tam bir **Linux** çekirdeği. O dünyada
donanımı tanımlama şeklin değişir: `xparameters.h`'deki sabitler yerini
**device tree**'ye (donanım ağacı — `.dts`/`.dtb` dosyaları) bırakır; hangi
çevre biriminin hangi adreste olduğunu, hangi kesmeyi kullandığını artık
derleme zamanı sabitleri değil, çekirdeğin çalışma zamanında okuduğu bu ağaç
söyler. Xilinx/AMD dünyasında bu Linux imajını, kök dosya sistemini ve
device tree'yi bir araya getiren araç **PetaLinux**'tur — var olduğunu bil,
kendi yapılandırma akışı ve öğrenme eğrisi var. Hangi dünyayı seçeceğin
("bare-metal mi, RTOS mu, Linux mu") gereksinimlere bağlıdır: sıkı zaman
garantisi istiyorsan FreeRTOS'a yakın kal; ağ yığını, dosya sistemi, çoklu
kullanıcı süreci istiyorsan Linux'un karmaşıklığını göze alırsın. Hazır
olduğunda serinin *Ethernet Saha Kılavuzu*'na göz at; Linux'lu Zynq'ların
çoğu zaman asıl var olma sebebi ağdır.

## Güvenli Boot ve Kriptografi

Bunu neden umursayacaksın: elindeki kart laboratuvar masasında JTAG'e bağlı
olduğu sürece "kim istediği kodu yükler" bir sorun değil. Ama bir ürün sahaya
çıktığında, birinin senin cihazına sahte bir firmware yükleyip yeniden
satması ya da kötü amaçlı kod çalıştırması ciddi bir tehdittir. **Güvenli
boot** (secure boot), Bölüm 3'te gördüğün BootROM'un, çalıştıracağı FSBL'yi
(ve zincirdeki sonraki her imajı) yüklemeden önce kriptografik olarak
doğrulamasıdır: imaj bir özel anahtarla **imzalanır** (signed image), karta
gömülü genel anahtar ya da **e-fuse**'larda (e-fuse — çipe kalıcı yazılan,
geri alınamaz bit sigortaları) saklı bir **özet** (hash/özet — bir veriden
üretilen sabit uzunlukta parmak izi) ile bu imza her boot'ta kontrol edilir;
imza tutmuyorsa cihaz açılmayı reddeder. Buna **güven zinciri** (chain of
trust) denir — her katman bir sonrakini doğrulamadan çalıştırmaz. Bu konuyu
laboratuvar aşamasında hiç düşünmezsin,
ama ürün sahaya çıkarken hafife alınırsa geri dönüşü en pahalı hatalardan
biri olur.

## JESD204 ve PCIe: Yüksek Hızlı Arayüzler

Bunu neden umursayacaksın: elindeki ZCU111'in Bölüm 2'de "süper gücü" diye
bir pencereden gösterip geçtiğimiz RF örnekleme tarafı, tam olarak bu
arayüzler sayesinde çalışır. **JESD204** (B/C sürümleri), yüksek hızlı
ADC/DAC (analogdan sayısala / sayısaldan analoga çeviricilerin) çipleri ile
FPGA arasında seri hatlar üzerinden gigabit mertebesinde veri taşıyan sanayi
standardı bir protokoldür — RFSoC'un içindeki RF-ADC/RF-DAC bloklarının PL
tarafına verisini ulaştırma yolu budur. **PCIe** (PCI Express) ise daha genel
amaçlı: kartlar arası ya da kart-anakart arası yüksek bant genişlikli,
paket tabanlı bir arabirim; sunucu sınıfı sistemlerde hızlandırıcı kartları
bağlamanın standart yoludur. İkisinin ortak noktası: AXI'nin (Bölüm 9)
rahat valid/ready el sıkışmasından çok daha karmaşık, çok kanallı,
senkronizasyon ve link training (bağlantının otomatik kalibrasyonu) gerektiren fiziksel katman
tasarımlarıdır — bu dokümanın kapsamı dışında ama adını duyduğunda "bu, AXI'nin
bir üst ligi" diye tanıman yeter. Hazır olduğunda serinin *RF Örnekleme Saha
Kılavuzu*'na göz at; JESD204'ün ZCU111'deki gerçek kullanımını orada
bulacaksın.

## Birim Test ve CI

Bunu neden umursayacaksın: bugüne kadar yazdığın her satırı gerçek kartta
çalıştırıp gördün — ama ekip büyüdükçe, her değişikliği elle karta basıp test
etmek ölçeklenmez. Sağlıklı bir gömülü kod tabanı, donanıma dokunan katmanı
(register erişimi, driver çağrıları) donanıma dokunmayan katmandan (protokol
ayrıştırma, durum makinesi mantığı, CLI komut ayrıştırma gibi Bölüm 14'te
yazacağın türden kod) bilinçli olarak ayırır. İkinci katman, kartsız, sıradan
bir bilgisayarda **birim test** (unit test) çerçeveleriyle test edilebilir;
bu da **CI**'ye (Continuous Integration — sürekli entegrasyon) bağlanır: her
commit'te otomatik derleme ve testler çalışır, hata insana ulaşmadan
yakalanır. Bizim ekipte "bu fonksiyonu donanımdan ayırabilir miyim" sorusu
tasarım aşamasının erken bir adımıdır — cevap genelde evet, ve o ayrım hem
test edilebilirliği hem de kodun okunabilirliğini birden yükseltir.

## Sadece adını tanı

Bu bölümde geçen kavramları ezberleme — amaç, biri adını andığında ne
olduğunu hatırlaman:

| Kavram | Tek cümle: ne işe yarar |
|---|---|
| DMA | CPU'yu meşgul etmeden bellekler arası veri taşıyan donanım birimi. |
| Scatter-gather | DMA'ya dağınık bellek parçalarını tek işlemde toplat/dağıt diyen descriptor zinciri. |
| Watchdog | Yazılım "hâlâ hayattayım" demeyi keserse donanımı kendiliğinden resetleyen bekçi zamanlayıcı. |
| DDR | Kartın hızlı ama uçucu (güç kesilince silinen) çalışma belleği. |
| QSPI | Yavaş ama kalıcı; genelde önyükleme imajını (boot.bin) tutan flash bellek. |
| eMMC | QSPI'den çok daha büyük, blok tabanlı kalıcı depolama; Linux kök dosya sistemini barındırır. |
| Device tree | Linux'a hangi çevre biriminin hangi adreste/kesmede olduğunu çalışma zamanında anlatan donanım ağacı. |
| PetaLinux | Xilinx/AMD'nin Linux imajı, kök dosya sistemi ve device tree'yi bir arada üreten araç seti. |
| Secure boot (güvenli boot) | Her önyükleme adımının bir sonrakini yüklemeden önce imzasını doğruladığı zincir. |
| e-fuse | Çipe kalıcı ve geri alınamaz şekilde yazılan bit sigortaları; doğrulama anahtarı/özeti burada saklanabilir. |
| Hash/özet | Bir veriden üretilen, verinin bütünlüğünü doğrulamaya yarayan sabit uzunlukta parmak izi. |
| Chain of trust (güven zinciri) | Her katmanın bir sonrakini doğrulamadan çalıştırmadığı güvenlik modeli. |
| JESD204 | Yüksek hızlı ADC/DAC çipleri ile FPGA arasında seri hatlarla gigabit mertebesinde veri taşıyan protokol. |
| PCIe | Kartlar/anakart arası yüksek bant genişlikli, paket tabanlı genel amaçlı arabirim. |
| Link training | Yüksek hızlı bir seri bağlantının otomatik kalibrasyon süreci. |
| Birim test (unit test) | Donanıma dokunmayan kodu kartsız, sıradan bir bilgisayarda test etme yöntemi. |
| CI (Continuous Integration) | Her commit'te otomatik derleme ve test çalıştırıp hatayı insana ulaşmadan yakalayan sistem. |
| TRM (Technical Reference Manual) | Çipin register/adres ayrıntılarının resmi, tam kaynağı olan üretici dokümanı. |
| Root filesystem (kök dosya sistemi) | Linux'un çalışması için gereken dosya/dizin hiyerarşisinin bulunduğu depolama alanı. |

Yedi kavramın hepsini bugün öğrenmeni beklemiyoruz; bu bölümün tek işi,
kafanda birer çengel bırakmaktı. Şimdi elindeki tüm becerileri — register
okuma, interrupt kurma, I2C konuşma, FreeRTOS task yazma — tek bir projede
birleştirme zamanı. Sırada Mezuniyet Görevi var.
