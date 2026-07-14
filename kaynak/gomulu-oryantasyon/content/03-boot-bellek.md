# Bölüm 3 — Sistem Nasıl Ayağa Kalkar: Boot ve Bellek Haritası

Görev 0'da güç anahtarını açtın (ya da JTAG modunda açık bıraktın — kendi
kendine boot etmeyi bilerek engelledin). O saniyede kartın içinde, sen daha
hiçbir kod yazmadan önce, koca bir tören başlıyor. Bu bölümde o töreni adım
adım izleyeceğiz ve törenin sonunda ortaya çıkan sahneyi — bellek haritasını
— tanıyacağız. Register'larla konuşmaya başlamadan önce "hangi adreste ne
var" sorusuna cevap vermen lazım; bu bölüm tam olarak o cevabı hazırlıyor.
İki durağımız var: önce töreni (boot zincirini) izleyeceğiz, sonra sahneyi
(bellek haritasını) tanıyacağız.

## Bölüm 3 · Birinci yarı: Reset'ten main()'e (boot zinciri)

## Reset'ten main()'e: dört durak

Zynq UltraScale+'ta reset kalktığı anda çalışan ilk kod senin yazdığın kod
değildir — çipin kendi silikonuna gömülü, değiştiremeyeceğin bir kod
zinciridir. Sırasıyla dört durak var:

1. **PMU ROM.** PMU (Platform Management Unit — platform yönetim birimi),
   CPU çekirdeklerinden bağımsız çalışan küçük bir denetleyicidir. Reset
   kalkar kalkmaz devreye giren PMU ROM kodu, güç dizilimini ve saat
   ağaçlarını kurar — CPU'lar daha "uyanmadan" önce platformun temel
   düzeni oturur.
2. **CSU ROM (BootROM).** Sıra artık ana boot koduna gelir: CSU ROM, SW6
   anahtarının konumundan boot modunu (mod pinlerini) okur, seçilen harici
   aygıttan (JTAG, QSPI flash ya da SD kart) **FSBL**'yi bulup yükler.
3. **FSBL (First Stage Boot Loader — ilk aşama önyükleyici).** Artık senin
   yazılım dünyana en yakın kod burada başlıyor. FSBL, DDR belleği
   başlatır (denetleyiciyi yapılandırır, bellek training'ini yapar), varsa PL
   bitstream'ini yükleyip FPGA fabric'ini yapılandırır ve son olarak
   uygulamanı belleğe koyup ona atlar.
4. **Uygulama** (ya da ara katman olarak **ATF**). Bare-metal bir
   hello-world'de FSBL uygulamanı doğrudan yükler ve çalıştırır; Linux
   koşan bir sistemde FSBL'den sonra bir ATF (ARM Trusted Firmware) katmanı
   ve ardından U-Boot/Linux gelir. Bu yolculukta hep bare-metal
   çalışacağımız için senin `main()`'in FSBL'nin doğrudan sıçradığı yer
   olacak.

{{svg:sema-05-boot-akisi.svg|Şekil 5 — Boot akışı zaman çizgisi: PMU ROM → CSU ROM (BootROM) → FSBL → (ATF) → uygulama; altta boot.bin'in içi, en altta SW6 boot kaynağı dallanması.}}

FSBL kendisi de bir yere yüklenmesi gereken bir programdır: BootROM onu
DDR henüz hazır olmadan **OCM**'e (On-Chip Memory — çip içi bellek, 256 KB)
yükler; başlangıç adresi tam olarak `0xFFFC_0000`'dir (tam aralığı bölüm
sonundaki adres özetinde bulacaksın). Bunun mantığı basit: DDR'yi
başlatacak kodun kendisi DDR'de yaşayamaz, o yüzden çip üzerinde küçük ama
her zaman hazır bir bellek (OCM) bu iş için ayrılmıştır.

## boot.bin: tek dosyada üç bileşen

Kart açıldığında BootROM'un okuduğu şey tek bir dosyadır: **boot.bin**.
Bu dosya aslında birbirinden farklı üç parçanın art arda dizilmesinden
oluşur: **FSBL**, (varsa) **PL bitstream'i** ve **uygulaman**. Vitis (ya da
klasik akışta bootgen aracı) bu üç parçayı senin için tek dosyada
paketler; SD karta ya da QSPI flash'a yazılan da bu tek dosyadır. JTAG
boot modunda ise bu paketleme adımını bile atlarsın — Vitis, FSBL'yi ve
uygulamanı debugger üzerinden doğrudan karta basar; boot.bin kavramı asıl
değerini SD/QSPI gibi "kendi kendine açılan" senaryolarda gösterir.

## Boot modları: SW6 anahtarının dili

Kart, hangi kaynaktan boot edeceğini **SW6** adlı 4 kutuplu DIP anahtardan
okur. Anahtarların her biri bir mod bitine karşılık gelir ve mantık
ters-çevrilidir: **anahtar ON konumundaysa karşılık gelen bit 0'dır.**
Yani "hepsi ON" görüntüsü kafa karıştırıcı gelebilir ama aslında "hepsi
sıfır" demektir.

| Boot Modu | Mode Pinleri [3:0] | SW6 [4:1] |
|---|---|---|
| JTAG | 0000 | ON, ON, ON, ON |
| QSPI32 (fabrika varsayılanı) | 0010 | ON, ON, OFF, ON |
| SD | 1110 | OFF, OFF, OFF, ON |

Görev 0'da kartı JTAG konumuna aldıysan, tablodaki ilk satırı elinle
doğrulamış oldun. Kart fabrikadan QSPI32 konumunda gelir — yani muhtemelen
bir anahtarı çevirmen gerekmişti. SD kart yuvası **J100**'dür; SD'den boot
etmek istediğinde boot.bin'i karta koyar, SW6'yı SD konumuna alır ve gücü
çevirirsin.

Nefes al — buraya kadar kartın kendi kendine nasıl ayağa kalktığını
gördün: PMU'dan CSU ROM'a, oradan FSBL'ye, oradan senin `main()`'ine.
Şimdi ikinci yarıya geçiyoruz: o ayağa kalkmış sistemde CPU'nun dünyayı
nasıl gördüğünü, yani bellek haritasını konuşacağız.

## Bölüm 3 · İkinci yarı: Her şeyin bir adresi var (bellek haritası)

## Bellek haritası: her şeyin bir adresi var

Artık sistemin ayağa kalktığını biliyorsun. Peki CPU, "UART'a yaz" ya da
"şu LED'i yak" dediğinde bunu nasıl ifade ediyor? Cevap basit ama kritik:
**her şeyin bir adresi var.** DDR belleğin de, çip içi belleğin de, her bir
çevre biriminin register'larının da, PL'de yaşayan bir IP'nin de kendine
ait bir adres aralığı vardır. CPU'nun gözünden bakınca hepsi aynı düz
adres uzayında yaşar — RAM'e yazmakla bir UART register'ına yazmak,
donanım seviyesinde aynı işlemdir, sadece adres farklıdır.

{{svg:sema-06-bellek-haritasi.svg|Şekil 6 — Bellek haritası çubuğu: DDR Low (2 GB, 0x0), PL adres pencereleri, çevre birimi register blokları (UART0/UART1/GPIO/TTC0), OCM (0xFFFC_0000); sağda ayrı bir çubukta DDR High (0x8_0000_0000).}}

Haritanın kabaca dört bölgesi var:

- **OCM — 256 KB.** FSBL'nin az önce gördüğün ilk konağı (`0xFFFC_0000`'dan
  başlıyor); küçük ama her zaman hazır, DDR gibi ayrıca başlatılmaya
  ihtiyaç duymaz.
- **DDR Low — 2 GB, `0x0`'dan başlar.** Uygulamanın ana çalışma alanı:
  kod, stack (yığıt), heap (dinamik bellek havuzu) ve veri hep burada
  yaşar (stack/heap/linker script kavramları Bölüm 6'da işlenecek;
  şimdilik: her bölümün belleğe nereye yerleşeceğini bir betik — linker
  script — belirler). ZCU111'in PS tarafındaki DDR4 SODIMM'i aslında 4
  GB'lık tek bir modüldür ama bu 4 GB'ın yalnızca alt 2 GB'ı bu bölgede
  görünür.
- **DDR High — SODIMM'in üst 2 GB'ı, `0x8_0000_0000`'dan başlayan bambaşka
  bir pencere.** DDR Low'un devamı değildir; adres uzayının çok uzağında,
  ayrı bir köşede ortaya çıkar. Aradaki boşluk gerçek değil — ZynqMP'nin
  adresleme mimarisinin bir sonucu.
- **Çevre birimleri ve PL pencereleri.** UART0, GPIO, TTC0 gibi PS çevre
  birimlerinin register blokları `0xFF00_0000` civarında sıralanır (tam
  adresler bölüm sonundaki tabloda); PL'de yaşayan IP'ler de (Bölüm 9)
  donanımcının tasarımına göre kendi adres pencerelerinden görünür.

:::analoji Bellek haritası bir şehrin imar planı gibidir
İmar planında hangi bölgenin konut, hangisinin sanayi, hangisinin resmi
daire olduğu önceden bellidir; yanlış adrese bina dikemezsin. Bellek
haritası da böyle çalışır: DDR geniş bir "konut bölgesi" — istediğin gibi
doldurursun; OCM küçük ve değerli bir merkez parseli; çevre birimleri ise
her biri kendi kapı numarasına sahip resmi daireler. Yanlış kapıyı
çalarsan (yanlış adrese yazarsan) ya hiçbir şey olmaz ya da çok daha kötü
bir şey olur.
:::

:::tuzak 4 GB SODIMM diye adres de 4 GB sürekli sanma
ZCU111'deki PS DDR4 modülü fiziksel olarak 4 GB'lık tek bir parça, ama
bellek haritasında tek bir sürekli adres bloğu DEĞİL. SODIMM'in alt yarısı
(2 GB) `0x0`'dan `0x7FFF_FFFF`'e kadar DDR Low bölgesinde yaşar; üst yarısı
(kalan 2 GB) ise bambaşka bir pencerede, `0x8_0000_0000` adresinden
itibaren DDR High olarak ortaya çıkar. Aradaki adresler boştur, SODIMM'in
bir parçası değildir — bunu tek sürekli blok sanıp bir arabellek ya da
linker script bölümünü sınırın üzerinden taşırsan derleyici seni uyarmaz,
kartta sessizce yanlış adrese yazan bir uygulamayla karşılaşırsın.
:::

:::derin-dalis ATF ve PMU'nun sahne arkası
PMU, CPU çekirdeklerinden bağımsız çalışan küçük bir mikrodenetleyicidir;
güç dizilimi ve saat ağaçlarını CPU'lar daha devreye girmeden halleder —
PMU ROM dediğimiz ilk durak bu birimin kodudur. ATF (ARM Trusted
Firmware), FSBL'den sonra devreye girebilen, güvenli bir ortam kurup
uygulamayı ya da bir işletim sistemini (Linux, U-Boot) devralan bir ara
katmandır; bizim bare-metal çalışmalarımızda FSBL uygulamayı doğrudan
yüklediği için bu katman devre dışı kalır, ama ekipte Linux'lu bir Zynq
sistemiyle karşılaşırsan mutlaka göreceksin. TrustZone ise donanımın
"güvenli" ve "güvensiz" dünya ayrımını çip seviyesinde uygulayan mimarinin
adıdır — şimdilik yalnızca adını bilmen yeterli.
:::

## Bu bölümün adres özeti

Bu bölümde geçen tüm adresler tek bakışta:

| Bileşen | Adres / Aralık | Not |
|---|---|---|
| OCM (çip içi bellek) | `0xFFFC_0000`–`0xFFFF_FFFF` | 256 KB, FSBL'nin ilk konağı |
| FSBL yükleme adresi | `0xFFFC_0000` | OCM'in başlangıcıyla aynı adres |
| DDR Low | `0x0000_0000`–`0x7FFF_FFFF` | 2 GB, uygulamanın ana çalışma alanı (kod, stack, heap, veri) |
| DDR High | `0x8_0000_0000`–`0xF_FFFF_FFFF` | 32 GB'lık ayrı pencere; SODIMM'in üst 2 GB'ı burada görünür |
| UART0 | `0xFF00_0000` | PS çevre birimi register bloğu |
| GPIO | `0xFF0A_0000` | PS çevre birimi register bloğu |
| TTC0 | `0xFF11_0000` | PS çevre birimi register bloğu |

Haritayı gördün, adres artık soyut bir kavram değil. Şimdi tek tek
kapıları çalacağız: her çevre biriminin kendi register'ları, kendi
kuralları var — bir sonraki bölümün konusu tam olarak bu.
