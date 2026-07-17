# Önsöz — Bu Kılavuz Ne Değildir

Bu bir FPGA tasarım eğitimi değil. Burada RTL (Register Transfer Level —
donanımın davranışını tarif eden kod) yazmayacağız, timing kapatmayacağız,
tek bir constraint dosyasına elimizi sürmeyeceğiz. Bunların hepsi donanımcının
işi ve donanımcı bu işi senden iyi yapıyor.

Bu kılavuzun derdi başka: **donanımcının sana teslim ettiği Vivado projesini
okuyabilmek.** Gömülü yazılım geliştiren herkesin başına aynı sahne gelir —
donanımcı "proje hazır, buyur" der, sen Vivado'yu açarsın ve karşında yüzlerce
çizgiden oluşan bir blok dizayn, onlarca sekmelik bir konfigürasyon ekranı
bulursun. UART hangi pinde? DDR açık mı? Timer'ın adresi ne? Bu soruların
cevabı o ekranların içinde bir yerde duruyor; bu kılavuz sana tam olarak
nereye bakacağını gösteriyor.

## Kimin için

Register, driver, BSP (Board Support Package — donanıma özel sürücü ve
başlangıç kodu katmanı), Vitis gibi kavramlara aşina olan; ama Vivado'ya ya
hiç girmemiş ya da "bir şeyi bozarım" korkusuyla giren gömülü yazılımcı için.
Sıfırdan mühendislik anlatmıyoruz; senin bildiğin dünyayı Vivado'nun
dünyasına bağlıyoruz.

## Nasıl okunur

Kılavuz iki karakter taşır: ders kitabı ve lab guide. Her bölümde anlatının
yanında `Deneme` kutuları bulacaksın — repo'daki demo projeyi kendi
Vivado'nda açıp aynı ekrana gider, somut bir soruya cevap ararsın.
Kutulardaki onay kutucukları tarayıcında saklanır; kaldığın yerden devam
edersin.

:::saha-notu
Acil bring-up durumu: yeni kart elinde, konsol yok, zaman dar. Rota:
**Bölüm 3 → 5 → 7 → 10.** Blok dizaynda yolunu bul, UART/clock ayarlarını
oku, adres haritasını çıkar, kontrol listesini koştur. Gerisini kart
ayaktayken okursun.
:::

## Sürüm notu

Bu kılavuzdaki tüm ekran görüntüleri ve komutlar **Vivado 2022.2** ile
üretildi ve birebir doğrulandı. Ekran yerleşimleri sürümler arasında
değişebilir; kavramlar kalıcıdır. 2020'lerden bu yana PS konfigürasyon
ekranlarının yapısı büyük ölçüde stabil — sekme adı değişse de aradığın
bilgi aynı mantıkla organize edilmiş halde durur.

Demo projelerimizden ilki ZCU102 kartını (Zynq UltraScale+ MPSoC) hedefler.
Ekipteki ZCU111 (RFSoC) ile bire bir aynı PS mimarisini taşır — bu eşleşmenin
neden sorunsuz olduğunu Bölüm 4'te netleştiriyoruz. İkinci demo VCK190
(Versal) üzerine kurulu; Bölüm 8'in konusu.

## Repo ve demo projeler

Bu doküman bir repo ile birlikte yaşar. `vivado/` altındaki Tcl scriptleri,
kılavuzdaki TÜM gerçek ekranların ve tabloların kaynağı olan iki demo projeyi
sıfırdan kurar:

```tcl
vivado -mode batch -source vivado/rfsoc/create_bd.tcl    ;# Demo 1: UltraScale+ PS
vivado -mode batch -source vivado/versal/create_bd.tcl   ;# Demo 2: Versal CIPS+NoC
```

Deneme kutularını çalışmak için bu projeleri kendi makinende kurman yeterli.
Hiçbir tablo, hiçbir adres, hiçbir ekran görüntüsü elle uydurulmadı — hepsi
bu projelerden söküldü.
