# Bölüm 11 — Alet Çantası: Vitis ve Debug

Bölüm 4'ten beri Vitis'i defalarca kullandın, ama hep parça parça: her
seferinde önüne bir şekilde bir proje geldi, build düğmesine bastın, kod
bir yolunu bulup karta gitti. Şimdi durup bu parçaları tek bir haritada
birleştirme zamanı — çünkü Görev 10'da o haritanın her köşesine aynı anda
ihtiyacın olacak.

## Kavram Haritası: Workspace, Platform, Application

Vitis üç kavram etrafında döner ve her biri diğerlerini gerektirir.

**Workspace** (çalışma alanı), projelerini tuttuğun disk klasörüdür;
Vitis'i her açışında hangi workspace ile çalışacağını seçersin.
Workspace'i ekip arkadaşlarınla paylaşmazsın — herkesin kendi diskinde
kendi kopyası vardır; paylaşılan, git deposundaki kaynak dosyalardır.

**Platform bileşeni**, donanımın yazılıma çevirisidir. Donanım mühendisi
Vivado'dan bir **.xsa** dosyası dışa aktarır (donanım tanımı — hangi
çevre birimleri var, PL'de hangi IP blokları yüklü, saat frekansları,
bellek haritası); bu .xsa'yı Vitis'e platform olarak eklersin. Vitis bunun
üstüne bir **BSP** üretir (board support package — çevre birimi
sürücülerini ve başlangıç dosyalarını içeren ara katman; `xparameters.h`
doğrudan buradan üretilir). Platform, işletim sistemi seçimini de taşır:
standalone (işletim sistemi yok; yolculuğumuzun çoğunda kullanılan) ya da
freertos10_xilinx (Bölüm 10'da tanıştığın FreeRTOS BSP'si).

**Application bileşeni** (uygulama), `main.c`'nin ve yol arkadaşı
dosyaların yaşadığı yerdir. Bir platforma bağlanır — platformun ürettiği
sürücülere ve adreslere erişim kazanır — ama platformdan bağımsız
derlenir. Aynı platformun üstüne birden çok application bileşeni
kurabilirsin: biri deneme amaçlı bir "hello world" projesi, diğeri asıl
işin.

{{svg:sema-23-vitis-anatomi.svg|Şekil 23 — Vitis kavram haritası: .xsa'dan üretilen platform bileşeni (BSP + donanım tanımı), üstüne kurulan application bileşeni; sağda JTAG/hw_server üzerinden karta bağlanan debug zinciri.}}

Bu üçlü ilişkiyi kavradığında Vitis'in menüleri rastgele tıkladığın
düğmeler olmaktan çıkar, mantıklı bir sıraya oturur: önce platform, sonra
application, sonra build.

## Unified IDE mi, Classic mi?

Birkaç sürüm önce Vitis, **Unified IDE** adında yeni bir arayüze geçti;
bu arayüz yakın zamanda varsayılan oldu ve eski **Classic Vitis IDE**
aşamalı olarak emekliye ayrılıyor. Kavram haritası ikisinde de aynıdır —
platform/application ayrımı, JTAG akışı ve debugger mantığı değişmez —
ama menü yolları ve proje dosyalarının iç yapısı farklıdır (Classic'te
`.mss`/`.mld` dosyaları, Unified'da CMake tabanlı bir yapı).

:::ekip-notu Ekip Hangi Sürümü Kullanıyorsa Onu Kullan
Bu doküman sana belirli bir sürüm numarası dayatmaz — Bölüm 0'da
söylendiği gibi kurulumu ekipten öğrendin; ekip hangi Vitis sürümünü
kullanıyorsa onunla çalış. Ekranındaki menü adı buradaki anlatımdan biraz
farklı görünebilir; altta yatan kavram aynıysa (platform oluştur,
application oluştur, build al, debug başlat) doğru yoldasın. Emin
olmadığın bir menü adını kıdemli bir arkadaşına sormak, yanlış tahmin
edip yarım saat kaybetmekten iyidir.
:::

## Proje Açmak, Build Almak ve Run/Debug Konfigürasyonları

Yeni bir application açtığında Vitis hazır şablonlar sunar; ilk deneme
için **Hello World** şablonu idealdir — UART üzerinden bir selam mesajı
basan, derlenmeye hazır minik bir proje. Kendi projelerinde bu şablondan
başlar, Görev 1'den beri yazdığın kaynak dosyaları içine taşırsın.

Build almak, kaynak dosyalarını cross compiler (senin bilgisayarında
çalışıp Arm çekirdeği için makine kodu üreten çapraz derleyici) ile
derler ve bir **ELF** (çalıştırılabilir çıktı dosyası) üretir. Build
başarılıysa bu ELF'i karta iki yolla gönderebilirsin:

- **Run konfigürasyonu:** ELF'i karta yükler ve doğrudan çalıştırır.
  Hızlıdır; ama bir şey ters gittiğinde elindeki tek ipucu UART
  çıktısıdır.
- **Debug konfigürasyonu:** ELF'i karta yükler ama çekirdeği başlangıçta
  durdurur (tipik olarak `main()`'in ilk satırında) ve debugger'ı bağlar.
  Görev 10 boyunca bu ikinci yolu kullanacaksın.

Fark küçük bir ayrıntı gibi görünebilir ama alışkanlık hâline getirmeye
değer: "bu neden çalışmıyor" sorusuyla karşılaştığında refleksin Run'ı
tekrar tekrar denemek değil, Debug'a geçmek olmalı.

## JTAG: Tek Kablo, İki İş

Görev 0'da kartına taktığın tek J83 micro-USB kablosu aynı anda iki işi
yürütür: kartın **FT4232** köprüsünün **Port A**'sı JTAG'i (programlama
ve debug erişimi) taşır; **Port B**'si ise terminal çıktısını okuduğun PS
UART0'ı taşır. Yani debug oturumu açıkken bile UART pencerene akış aynı
kablodan sürer — ikinci bir kablo aramana gerek yok.

Vitis'in kartla JTAG üzerinden haberleşmesi **hw_server** adlı bir arka
plan sürecinden geçer; Vivado'nun Hardware Manager'ı da aynı hw_server'a
bağlanır — yani iki araç kartı sırayla paylaşabilir (ikisinin aynı anda
kartı programlamaya kalkışması çakışma yaratır; sırayla ilerle).

## Debugger ile Yüz Yüze: Breakpoint'ten Disassembly'ye

Bir debug konfigürasyonu başlattığında karşına dört ana ögeli bir görünüm
çıkar:

- **Breakpoint (kesme noktası):** bir kod satırına "buraya gelince dur"
  dersin. Çekirdek o satıra ulaştığında donar, sen durumu incelersin.
- **Step over / step into:** bir sonraki satıra geçerken fonksiyon
  çağrısının üstünden atlamak (over) ile içine dalıp onu da adım adım
  yürümek (into) arasında seçim yaparsın.
- **Değişken, register ve bellek pencereleri:** güncel değişken
  değerlerini, işlemcinin register'larını ve seçtiğin herhangi bir bellek
  adresinin ham içeriğini canlı izlersin. Bölüm 4'te "adres = kapı
  numarası" diye anlattığımız register'lar artık ekranda gerçek sayılar
  olarak karşındadır.
- **Disassembly:** C satırlarının derleyici tarafından hangi işlemci
  komutlarına çevrildiğini gösteren pencere.

Yeni başlayanların çoğu bu son ögeye çekinerek bakar — "assembly
okuyamam". Gerçek şu: okuman gerekmiyor, yalnızca *tanıman* gerekiyor.
`LDR`/`STR` gördüğünde "bellekten oku / belleğe yaz" notunu düş ve devam
et. Asıl değerli olan şu: `volatile` işaretlemediğin bir değişkenin
okumasının derleyici tarafından tamamen elendiğini disassembly'de kendi
gözünle görebilirsin — Bölüm 5'te (Şekil 10) anlatılan hikâyenin somut
kanıtı ekranında durur.

:::derin-dalis Disassembly'de volatile'ın İzini Sürmek
İki derlemeyi yan yana koy. Bir bayrağı döngüde okuyan `volatile`'sız
kod, optimizasyon açıkken (`-O2`) tipik olarak şuna benzer bir çıktı
üretir — değişken register'a bir kez yüklenir, döngünün geri kalanında
belleğe bir daha uğranmaz:

```metin
; G_ucFlag volatile DEĞİL, -O2
LDR   w0, [x1]        ; BİR kez yüklendi
loopContinue:
b.eq  loopContinue     ; bundan sonra hep aynı register denetlenir
```

`volatile` eklendiğinde derleyici döngünün her turunda belleğe gerçekten
gider:

```metin
; G_ucFlag volatile, -O2
loopStart:
LDR   w0, [x1]        ; HER turda yeniden yüklenir
b.eq  loopStart
```

Görev 10'da tam olarak bu ikilemle karşılaşacaksın; şüpheni kanıta
çevireceğin yer disassembly penceresi olacak.
:::

## XSCT/xsdb: Konsolun Arkasındaki Konsol

Vitis'in altında, IDE'nin grafik arayüzünün arkasında **XSCT** (Xilinx
Software Command-Line Tool) çalışır; etkileşimli hedef denetiminde
kullanılan komut satırı arayüzü ise **xsdb**'dir. Günlük işinde XSCT'yi
elle çağırman gerekmez — Vitis onu senin yerine çalıştırır — ama bir gün
otomasyon yazman ya da IDE'nin göstermediği bir ayrıntıyı sorgulaman
gerekirse, IDE içindeki XSCT konsol penceresi tam bunun için vardır.
Şimdilik varlığını bilmen yeter; bir ekip arkadaşın "xsct'den bak"
dediğinde nereye bakacağını bileceksin.

{{svg:sema-24-debug-akisi.svg|Şekil 24 — Debug oturumu döngüsü: JTAG bağla → breakpoint koy → çalıştır/durdur → adım adım ilerle → register/bellek/değişken izle → hipotez kur → düzelt ve yeniden derle; kenarda "dört alet" rozetleri.}}

:::saha-notu Dört Alet
Bir hatanın peşine düştüğünde elinde dört alet vardır ve her biri farklı
işe yarar. **printf** (UART'a satır basmak) hızlıdır ama yürütmeyi
yavaşlatır ve ISR içinde tehlikelidir. **LED**, zamanlamayı neredeyse hiç
bozmayan tek bitlik bir sinyaldir — belirli bir noktada toggle etmek,
"buraya gelindi mi" sorusunu osiloskop altında bile cevaplayabilir.
**Debugger** yürütmeyi durdurup durumu incelemeni sağlar, ama zamanın
akışını dondurduğu için gerçek zamanlı hataları maskeleyebilir. **Logic
analyzer** hattı hiç bozmadan dışarıdan izler — en dürüst tanık, ama
kurulumu en zahmetlisi. İyi bir gömülü geliştirici bu dördü arasında
seçim yapmayı bilir; hangi belirtinin hangi aleti çağırdığını Görev 10'da
bizzat öğreneceksin.
:::

Alet çantan artık tamam; teori burada bitiyor, soruşturma başlıyor.

:::gorev no=10 zorluk=3 baslik="Hata Avı" kisa="Hata Avı"
[Hedef]
`lab10-bughunt` projesindeki 4 gerçek kusuru bul, düzelt ve her biri için
tek cümlelik kök neden yaz.

[Ön koşul]
Bölüm 4–11 okundu; Görev 1, 2, 4 ve 5 tamamlandı (register erişimi, UART,
interrupt ve TTC artık tanıdık).

[Adımlar]
1. `labs/lab10-bughunt/` projesini incele — senden önceki stajyerden
   kaldı. `README.md`'deki spesifikasyonu ve gözlenen belirtileri
   dikkatle oku: proje derlenir ve karta yüklenir, ama davranışının dört
   yönü beklentiyle uyuşmaz.
2. Projeyi kendi Vitis workspace'inde application bileşeni olarak aç,
   build al ve **Debug konfigürasyonuyla** karta yükle (tam adımlar
   README'de).
3. Dört bulguyu tahmin etmeye kalkmadan önce sistemi çalıştır ve kendi
   gözünle izle; her belirti için önce hangi aletin (printf, LED,
   debugger, logic analyzer) en uygun olduğuna kendin karar ver.
4. Dört kusuru da bul ve düzelt. Her düzeltmeden sonra sistemi baştan
   test et — bir kusuru düzeltmek bazen diğerinin belirtisini değiştirir.
5. Her kusur için tek cümlelik kök neden yaz (*ne* olduğunu değil,
   *neden* olduğunu).

[Başarı kriteri]
Proje spesifikasyona tam uyar: TTC0 üzerinden saniyede bir "tick N"
satırı basılır, her SW19 basışında "button: M" satırı düşer ve DS50
toggle olur, sayaçlar doğru artar, sistem saatlerce kararlı çalışır — ve
4 kusur için 4 kök neden cümlen hazırdır.

[Kendini sına]
- Bu dört kusurdan hangisini debugger olmadan, yalnızca UART çıktısıyla
  bulamazdın? Neden?
- Release build (optimizasyonlu, `-O2`) ile debug build (`-O0`) farkı
  hangi kusurun görünürlüğünü etkiler, hangisini gizler?
- Dördüncü kusurun belirtisi neden hemen değil de sistem "bir süre"
  çalıştıktan sonra ortaya çıkar?

[Takıldıysan]
::ipucu İpucu 1 — Hangi belirtiye hangi alet
Dört belirtiyi tek tek ele al. "Optimizasyonlu build'de buton hiç tepki
vermiyor" cümlesi seni doğrudan derleyicinin ne yaptığını sorgulamaya
götürmeli — disassembly penceresi burada devreye girer. "Tick bazen
atlıyor ya da geç geliyor" bir zamanlama meselesidir — özellikle
interrupt'ların ne kadar sürdüğüyle ilgilidir — ve LED ya da zaman
damgasıyla ölçülebilir. "DS50 bir kez yanıyor, bir daha hiç sönmüyor" saf
bir mantık hatasıdır; tek bir kaynak satırına bakmak yeter. "Sistem
rastgele çöküyor" klasik bellek/stack şüphesidir — bellek penceresi ve
`lscript.ld` müttefiklerindir.
::/
::ipucu İpucu 2 — Somut izler
(1) `G_ucButtonFlag` bayrağının tanımına bak: bir niteleyici eksik.
(2) Buton ISR'sinin içine bak: orada olmaması gereken iki şey var ve
ikisi de zaman yiyor. (3) LED'i toggle eden satırı bul: kullanılan bit
operatörü "aç" diyor, "tersle" değil. (4) 8 KB yerel diziyle başlayan
fonksiyonu bul ve `lscript.ld`'deki stack boyutuyla karşılaştır.
::/
::cozum Tam Çözüm — 4 Kusur: Yer, Kök Neden, Düzeltme
### 1. `G_ucButtonFlag` volatile Değil

**Yer:** `src/gpio_led_button.h` (global değişken tanımı); `src/main.c`
içinde ana döngüde ve `src/gpio_led_button.c` içinde buton ISR'sinde
kullanılır.

**Kök neden:** Değişken ISR ile ana döngü arasında paylaşılıyor ama
`volatile` işaretli değil; `-O2` optimizasyonunda derleyici, değişkenin
ana döngü içinde bir daha değişmeyeceğini varsayıp değerini register'da
tutar; ISR belleği güncellese de ana döngü bunu hiç görmez.

**Düzeltme:**
```c
/* onceki */
unsigned char G_ucButtonFlag = 0;
/* duzeltilmis */
volatile unsigned char G_ucButtonFlag = 0;
```

### 2. Buton ISR'sinde Uzun Süren İş (xil_printf + Gecikme Döngüsü)

**Yer:** `src/gpio_led_button.c`, `buttonIsr()` fonksiyonu.

**Kök neden:** "Hızlı bir durum satırı" gerekçesiyle ISR'ye eklenen
`xil_printf` çağrısı ve boş gecikme döngüsü, interrupt'ı olması
gerekenden çok daha uzun çalıştırır; bu süre boyunca daha yüksek
öncelikli TTC interrupt'ları gecikir ya da kaçırılır — tick sayacının
atlaması ya da geç gelmesi bundandır.

**Düzeltme:** ISR yalnızca bayrağı kurmalı ve sayacı artırmalı; basma
işini ana döngüye taşı — ayrıntılı diff için
`labs/lab10-bughunt/SOLUTION.md`.

### 3. DS50 için Toggle Yerine `|=`

**Yer:** `src/gpio_led_button.c`, `ledDs50Toggle()` fonksiyonu.

**Kök neden:** Durumu terslemesi gereken satır `^=` yerine `|=`
kullanıyor; `|= 1` her çağrıda durumu 1'e sabitler — LED bir kez
yandıktan sonra bir daha sönmez.

**Düzeltme:**
```c
/* onceki */
G_uiDs50State |= 1;
/* duzeltilmis */
G_uiDs50State ^= 1;
```

### 4. 8 KB Yerel Dizi → Stack Overflow

**Yer:** `src/main.c`, `printHealthSummary()` fonksiyonu; karşılaştırma
için `src/lscript.ld` içindeki `_STACK_SIZE`.

**Kök neden:** Fonksiyon her çağrıldığında stack üzerinde 8 KB'lik
`cArrHistoryBuffer` dizisi ayrılıyor; `lscript.ld`'de bu proje için
ayrılan stack alanı, bu diziyi üstüne binen diğer çağrı çerçeveleriyle
birlikte taşıyamayacak kadar dar. Taşma komşu bellek bölgesini bozar;
neyin bozulacağı çağrı anındaki stack derinliğine bağlı olduğundan (araya
bir interrupt girip girmediğine göre) çökme hemen değil, sistem bir süre
çalıştıktan sonra rastgele görünür.

**Düzeltme:** Tamponu gerçek ihtiyaca indir:
```c
/* onceki */
char cArrHistoryBuffer[8192];
/* duzeltilmis */
char cArrHistoryBuffer[128];
```
Kalıcı çözüm için `lscript.ld`'deki `_STACK_SIZE` değerini projenin
gerçek en-kötü-durum çağrı derinliğine göre de gözden geçir. Tam
açıklama: `labs/lab10-bughunt/SOLUTION.md`.
::/
:::

Dört kusuru da bulup düzelttiğinde alet çantanı artık gerçekten
tanıyorsun — debugger'ı çekinmeden açan, disassembly'den ürkmeyen, hangi
belirtiye hangi aletle gidileceğini bilen biri oldun. Aletleri
biliyorsun; sıra mesleğin teamüllerinde: iyi bir gömülü geliştiriciyi
yalnızca çalışan kod değil, ekip içinde etkili çalışabilme becerisi
tanımlar.
