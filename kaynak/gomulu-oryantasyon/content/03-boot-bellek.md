# Bölüm 3 — Sistem Nasıl Açılır: Boot Süreci ve Bellek Haritası

Görev 0'da karta güç verdin (ya da kartı bilerek JTAG modunda bıraktın;
bu mod kartın kendi başına boot etmesini engeller). O anda, sen daha tek
satır kod yazmamışken, kartın içinde geniş bir işlem dizisi başladı. Bu
bölüm o diziyi adım adım izler ve sonunda ortaya çıkan tabloyu — memory
map'i (bellek haritası) — önüne koyar. Register'larla konuşmadan önce
"hangi adreste ne oturuyor" sorusunun cevabı gerekir; bu bölümün işi tam
olarak o cevaptır. İki kısım var: önce dizinin kendisi (boot zinciri),
sonra ortaya çıkan tablo (bellek haritası).

## Bölüm 3 · Birinci Kısım: Reset'ten main()'e (Boot Zinciri)

## Dört Aşama

Zynq UltraScale+ üzerinde, reset bırakıldığı anda çalışan ilk kod senin
yazdığın kod değildir — çipin silikonuna gömülü, değiştiremeyeceğin bir
kod zinciridir. Sırasıyla dört aşama var:

1. **PMU ROM.** PMU (Platform Management Unit — platform yönetim birimi),
   CPU çekirdeklerinden bağımsız çalışan küçük bir denetleyicidir. Reset
   bırakılır bırakılmaz devreye giren PMU ROM kodu güç sıralamasını ve
   saat ağaçlarını kurar — CPU'lar daha "uyanmadan" platformun temel
   düzeni yerindedir.
2. **CSU ROM (BootROM).** Kontrol asıl boot koduna geçer: CSU ROM, SW6
   anahtarının konumundan boot modunu (mode pinleri) okur ve **FSBL**'yi
   seçili harici kaynaktan (JTAG, QSPI flash veya SD kart) bulup yükler.
3. **FSBL (First Stage Boot Loader).** Senin yazılım dünyana en yakın kod
   burada başlar. FSBL, DDR belleği ilklendirir (denetleyiciyi
   yapılandırır, memory training yapar), varsa PL bitstream'ini yükleyip
   FPGA fabric'i yapılandırır ve son olarak uygulamanı belleğe
   yerleştirip ona atlar.
4. **Uygulama** (ya da ara katman olarak **ATF**). Bare-metal bir
   hello-world'de FSBL uygulamanı doğrudan yükleyip çalıştırır; Linux
   koşan bir sistemde FSBL'yi ATF (ARM Trusted Firmware) katmanı, onu da
   U-Boot/Linux izler. Bu yolculukta yalnızca bare-metal çalıştığın için
   `main()` fonksiyonun, FSBL'nin doğrudan atladığı nokta olacak.

{{svg:sema-05-boot-akisi.svg|Şekil 5 — Boot akışı zaman çizgisi: PMU ROM → CSU ROM (BootROM) → FSBL → (ATF) → uygulama; altında boot.bin'in içeriği; en altta SW6 boot kaynağı dallanması.}}

FSBL de bir yere yüklenmesi gereken bir programdır: DDR henüz hazır
olmadığından BootROM onu **OCM**'e (On-Chip Memory, 256 KB) yükler;
başlangıç adresi tam olarak `0xFFFC_0000`'dır (aralığın tamamını bölüm
sonundaki adres özetinde bulacaksın). Buradaki mantık nettir: DDR'ı
ilklendirmekle görevli kod DDR'ın kendisinde duramaz; bu iş için çip
üzerinde her zaman hazır küçük bir bellek bloğu (OCM) ayrılmıştır.

## boot.bin: Tek Dosyada Üç Parça

Karta güç verildiğinde BootROM tek bir dosya okur: **boot.bin**. Bu dosya
aslında art arda dizilmiş üç ayrı parçadan oluşur: **FSBL**, **PL
bitstream** (varsa) ve **senin uygulaman**. Vitis (klasik akışta bootgen
aracı) bu üç parçayı senin yerine tek dosyada paketler; SD karta veya
QSPI flash'a yazılan da bu tek dosyadır. JTAG boot modunda bu paketleme
adımını da atlarsın — Vitis, FSBL'yi ve uygulamanı debugger üzerinden
doğrudan karta yükler; boot.bin kavramı asıl değerini SD veya QSPI gibi
"kendi kendine açılma" senaryolarında gösterir.

## Boot Modları: SW6 Anahtarının Dili

Kart hangi kaynaktan boot edeceğini **SW6** adlı 4 kutuplu DIP
anahtardan okur. Her anahtar bir mode bitine karşılık gelir ve mantık
terstir: **anahtar ON konumundayken ilgili bit 0'dır.** Yani "hepsi ON"
görüntüsü yanıltıcı olabilir — aslında "hepsi sıfır" anlamına gelir.

| Boot Modu | Mode Pinleri [3:0] | SW6 [4:1] |
|---|---|---|
| JTAG | 0000 | ON, ON, ON, ON |
| QSPI32 (fabrika varsayılanı) | 0010 | ON, ON, OFF, ON |
| SD | 1110 | OFF, OFF, OFF, ON |

Görev 0'da kartı JTAG konumuna aldıysan tablonun ilk satırını kendi
elinle doğruladın. Kart fabrikadan QSPI32 konumunda çıkar — yani büyük
olasılıkla bir anahtar çevirmen gerekti. SD kart yuvası **J100**'dür;
SD'den boot etmek için boot.bin'i karta koyar, SW6'yı SD konumuna alır
ve kartın gücünü kesip yeniden verirsin.

Bu noktada kartın kendini nasıl ayağa kaldırdığını gördün: PMU'dan CSU
ROM'a, oradan FSBL'ye, oradan `main()` fonksiyonuna. Şimdi ikinci kısma
geçiyoruz: sistem ayaktayken CPU dünyayı nasıl görür — yani bellek
haritası.

## Bölüm 3 · İkinci Kısım: Her Şeyin Bir Adresi Var (Bellek Haritası)

## Bellek Haritasını Okumak

Sistemin ayakta olduğunu artık biliyorsun. Peki CPU "UART'a yaz" ya da
"şu LED'i yak" gibi bir işlemi nasıl ifade eder? Cevap basit ama kritik:
**her şeyin bir adresi var.** DDR bellek, çip üstü bellek, her
çevre biriminin register'ları ve PL'de duran her IP kendi
adres aralığına sahiptir. CPU'nun gözünden bunların hepsi aynı düz adres
uzayında yaşar — RAM'e yazmak ile bir UART register'ına yazmak donanım
düzeyinde aynı işlemdir; yalnızca adres farklıdır.

{{svg:sema-06-bellek-haritasi.svg|Şekil 6 — Bellek haritası çubuğu: DDR Low (2 GB, 0x0), PL adres pencereleri, çevre birimi register blokları (UART0/UART1/GPIO/TTC0), OCM (0xFFFC_0000); sağda ayrı çubukta DDR High (0x8_0000_0000).}}

Harita kabaca dört bölgeye ayrılır:

- **OCM — 256 KB.** Az önce gördüğün FSBL'nin ilk durağı
  (`0xFFFC_0000`'dan başlar); küçüktür ama her zaman hazırdır, DDR gibi
  ayrı bir ilklendirme istemez.
- **DDR Low — 2 GB, `0x0`'dan başlar.** Uygulamanın asıl çalışma alanı:
  kod, stack, heap (dinamik bellek havuzu) ve veri burada durur
  (stack/heap/linker script kavramları Bölüm 6'nın konusu; şimdilik:
  her bölümün bellekte nereye yerleşeceğini linker script adlı bir
  betik belirler). ZCU111'in PS tarafındaki DDR4 SODIMM aslında tek
  parça 4 GB'tır, ama bu bölgede o 4 GB'ın yalnızca alt 2 GB'ı görünür.
- **DDR High — SODIMM'in üst 2 GB'ı,** `0x8_0000_0000`'dan başlayan
  tamamen ayrı bir pencere. DDR Low'un devamı değildir; adres uzayında
  uzakta, ayrı bir köşede görünür. Aradaki boşluk fiziksel değildir —
  ZynqMP'nin adresleme mimarisinin sonucudur.
- **Çevre birimleri ve PL pencereleri.** UART0, GPIO, TTC0 gibi PS çevre
  birimlerinin register blokları `0xFF00_0000` civarında dizilir (tam
  adresler bölüm sonundaki tabloda); PL'de duran IP'ler de (Bölüm 9)
  donanım tasarımcısının yerleşimine göre kendi adres pencerelerinden
  görünür.

:::analoji Memory map: şehir imar planı
İmar planı hangi parselin konut, hangisinin sanayi, hangisinin kamu
binası olduğunu önceden belirler; yanlış parsele bina dikemezsin. Bellek
haritası aynı işi yapar: DDR geniş bir imar bölgesidir, istediğin gibi
doldurursun; OCM merkezde küçük ama değerli bir parseldir; çevre
birimlerinin her biri kendi adresine kayıtlı bir resmi dairedir. Yanlış
kapıya gidersen (yanlış adrese yazarsan) ya hiçbir şey olmaz ya da çok
daha kötüsü olur.
:::

:::tuzak 4 GB SODIMM'i Bitişik 4 GB Adres Aralığı Sanma
ZCU111 üzerindeki PS DDR4 modülü fiziksel olarak tek parça 4 GB'tır, ama
bellek haritasında tek bir bitişik adres bloğu **değildir**. SODIMM'in
alt yarısı (2 GB) DDR Low bölgesinde, `0x0`–`0x7FFF_FFFF` aralığında
durur; üst yarısı (kalan 2 GB) DDR High olarak `0x8_0000_0000`'dan
başlayan tamamen ayrı bir pencerede görünür. Aradaki adresler boştur —
SODIMM'e ait değildir. Bunu tek bitişik blok sanıp bir buffer'ın ya da
linker script bölümünün o sınırı aşmasına izin verirsen derleyici seni
uyarmaz; kartta, sessizce yanlış adrese yazan bir uygulamayla kalırsın.
:::

:::derin-dalis Perde Arkası: ATF ve PMU
PMU, CPU çekirdeklerinden bağımsız çalışan küçük bir mikrodenetleyicidir;
CPU'lar devreye girmeden önce güç sıralamasını ve saat ağaçlarını
yönetir — PMU ROM dediğimiz ilk aşama bu birimin kodudur. ATF (ARM
Trusted Firmware), FSBL'den sonra devreye girebilen bir ara katmandır:
kontrolü uygulamaya ya da bir işletim sistemine (Linux, U-Boot)
devretmeden önce güvenli bir ortam kurar. Bare-metal çalışmamızda bu
katman devre dışıdır çünkü FSBL uygulamayı doğrudan yükler; ama ekipte
Linux koşan bir Zynq sistemi üzerinde çalışırsan mutlaka karşına çıkar.
TrustZone, donanımın "secure" ve "non-secure" dünya ayrımını çip
düzeyinde uygulayan mimarinin adıdır — şimdilik adını bilmen yeter.
:::

## Bu Bölümün Adres Özeti

Bu bölümde geçen tüm adresler tek bakışta:

| Bileşen | Adres / Aralık | Not |
|---|---|---|
| OCM (çip üstü bellek) | `0xFFFC_0000`–`0xFFFF_FFFF` | 256 KB, FSBL'nin ilk durağı |
| FSBL yük adresi | `0xFFFC_0000` | OCM başlangıcıyla aynı adres |
| DDR Low | `0x0000_0000`–`0x7FFF_FFFF` | 2 GB, uygulamanın asıl çalışma alanı (kod, stack, heap, veri) |
| DDR High | `0x8_0000_0000`–`0xF_FFFF_FFFF` | Ayrı 32 GB pencere; SODIMM'in üst 2 GB'ı burada görünür |
| UART0 | `0xFF00_0000` | PS çevre birimi register bloğu |
| GPIO | `0xFF0A_0000` | PS çevre birimi register bloğu |
| TTC0 | `0xFF11_0000` | PS çevre birimi register bloğu |

Haritayı gördün; adres artık soyut bir kavram değil. Şimdi kapıları tek
tek çalacağız: her çevre biriminin kendi register'ları ve kendi
kuralları var — bir sonraki bölümün konusu tam olarak bu.
