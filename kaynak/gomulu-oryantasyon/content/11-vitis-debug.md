# Bölüm 11 — Alet Çantası: Vitis ve Debug

Bölüm 4'ten bu yana Vitis'i defalarca kullandın ama hep parça parça: bir
proje her seferinde bir şekilde önünde hazır çıktı, derleme düğmesine
bastın, kod karta bir şekilde indi. Şimdi durup bu parçaları tek bir
haritada birleştirme zamanı — çünkü Görev 10'da bu haritanın her köşesine
aynı anda ihtiyacın olacak.

## Kavram haritası: workspace, platform, uygulama

Vitis üç kavram etrafında döner ve üçü de birbirini gerektirir.

**Workspace (çalışma alanı)**, diskte projelerini tuttuğun klasördür; Vitis'i
her açtığında hangi workspace'le çalışacağını seçersin. Ekip arkadaşlarınla
aynı workspace'i paylaşmazsın — herkesin diskinde kendi kopyası olur,
paylaşılan olan git deposundaki kaynak dosyalardır.

**Platform component (platform bileşeni)**, donanımın yazılıma çevirisidir.
Donanımcı Vivado'dan bir **.xsa** dosyası (donanım tanımı — hangi çevre
birimlerin var, PL'de hangi IP'ler yüklü, saat frekansları, bellek haritası)
dışa aktarır; sen bu .xsa'yı Vitis'e platform olarak eklersin. Vitis bunun
üzerine bir **BSP** (board support package — çevre birimlerinin sürücülerini
ve başlangıç dosyalarını içeren ara katman; `xparameters.h` tam olarak
buradan doğar) üretir. Platform, işletim sistemi seçimini de taşır:
standalone (işletim sistemsiz, yolculuğumuzun büyük kısmı) ya da
freertos10_xilinx (Bölüm 10'da tanıştığın FreeRTOS BSP'si).

**Application component (uygulama bileşeni)**, senin yazdığın `main.c` ve
kardeşlerinin yaşadığı yerdir. Bir platforma bağlanır — platformun ürettiği
sürücülere ve adreslere erişir — ama platformdan bağımsız olarak derlenir.
Aynı platform üzerine birden fazla uygulama bileşeni kurabilirsin: biri
deneme "hello world" projesi, biri asıl işin.

{{svg:sema-23-vitis-anatomi.svg|Şekil 23 — Vitis kavram haritası: .xsa'dan doğan platform bileşeni (BSP + donanım tanımı), üzerine kurulan uygulama bileşeni; sağda JTAG/hw_server üzerinden karta bağlanan debug zinciri.}}

Bu üçlü ilişkiyi bir kez kavradığında Vitis'in menüleri rastgele tıklanan
düğmeler olmaktan çıkıp mantıklı bir sıraya oturur: önce platform, sonra
uygulama, sonra derleme.

## Unified IDE mi, Classic mi?

Vitis birkaç sürüm önce **Unified IDE** adında yeni bir arayüze geçti; yakın
dönemde bu arayüz varsayılan hale geldi ve eski **Classic Vitis IDE**
kullanımdan kaldırılıyor (deprecated). İkisinin kavram haritası aynıdır —
platform/uygulama ayrımı, JTAG akışı, debugger mantığı değişmez — ama menü
yolları ve proje dosyalarının iç yapısı (Classic'te `.mss`/`.mld` dosyaları,
Unified'da CMake tabanlı yapı) farklıdır.

:::ekip-notu Hangi sürümdeyse ekip, ona uy
Bu doküman sana bir sürüm numarası dayatmıyor — kurulumu Bölüm 0'da
söylediğimiz gibi ekipten öğrendin, ekip hangi Vitis sürümünü kullanıyorsa
onunla çalış. Ekranındaki menü adı burada anlattığımızdan biraz farklı
görünebilir; kavram aynıysa (platform oluştur, uygulama oluştur, derle,
debug başlat) doğru yoldasın demektir. Emin olamadığın bir menü adını
yanındaki kıdemli arkadaşına sormak, yanlış tahmin edip yarım saat
kaybetmekten iyidir.
:::

## Proje açma, derleme, Run ve Debug konfigürasyonları

Yeni bir uygulama açarken Vitis sana hazır şablonlar sunar; **Hello World**
şablonu ilk denemen için idealdir — UART üzerinden bir karşılama mesajı
basan, derlenmeye hazır minik bir proje. Kendi projelerinde bu şablonu boş
bırakıp Görev 1'den beri yazdığın kaynak dosyaları içine taşırsın.

Derleme (build), kaynak dosyalarını çapraz derleyiciyle (cross compiler —
senin bilgisayarında çalışıp Arm çekirdeği için makine kodu üreten
derleyici) işleyip bir **ELF** (yürütülebilir çıktı dosyası) üretir. Derleme
başarılıysa bu ELF'i karta iki şekilde gönderebilirsin:

- **Run configuration:** ELF'i karta yükler ve doğrudan çalıştırır. Hızlıdır,
  ama bir hata çıktığında elinde tek UART çıktısı kalır.
- **Debug configuration:** ELF'i karta yükler ama çekirdeği başlangıçta
  (genelde `main()`'in ilk satırında) durdurur ve debugger'ı bağlar. Görev
  10'da hep bu ikincisini kullanacaksın.

Aradaki fark küçük bir ayrıntı gibi görünse de alışkanlık haline getirmeye
değer: "neden çalışmıyor" sorusuyla karşılaştığında refleksin Run'ı tekrar
tekrar denemek değil, Debug'a geçmek olmalı.

## JTAG: tek kablo, iki iş

Kartına Görev 0'da taktığın o tek J83 micro-USB kablosu, aynı anda iki işi
görür: kartın üzerindeki **FT4232** köprüsünün **Port A**'sı JTAG
(programlama ve debug erişimi) taşırken, **Port B**'si senin terminal
çıktını okuduğun PS UART0'ı taşır. Yani debug oturumu açıkken de UART
penceren aynı kablodan akmaya devam eder — iki farklı kablo aramana gerek
yok.

Vitis'in JTAG üzerinden karta konuşması **hw_server** adlı bir arka plan
sürecinden geçer; Vivado'nun Hardware Manager'ı da aynı hw_server'a bağlanır,
yani ikisi aynı kartı sırayla paylaşabilir (ikisinin aynı anda kartı
programlamaya çalışması karışıklık çıkarır — sırayla ilerle).

## Debugger'la göz göze: breakpoint'ten disassembly'ye

Debug konfigürasyonunu başlattığında karşına dört köşeden bir manzara çıkar:

- **Breakpoint (kesme noktası):** kodun bir satırına "buraya geldiğinde dur"
  dersin. Çekirdek o satıra ulaştığında donar, sen inceleme yaparsın.
- **Step over / step into (üzerinden geç / içine gir):** bir sonraki satıra
  geçerken fonksiyon çağrısının içine girmeden atlamak (over) ya da içine
  dalıp orada da adım adım ilerlemek (into) arasında seçim yaparsın.
- **Değişken, register ve memory pencereleri:** o anki değişken değerlerini,
  işlemcinin register'larını ve istediğin bir bellek adresinin ham
  içeriğini canlı izlersin. Bölüm 4'te "adres = kapı numarası" dediğimiz
  register'ları artık ekranda gerçek sayılar olarak görürsün.
- **Disassembly (çözümlenmiş makine kodu):** C satırlarının derleyici
  tarafından hangi işlemci komutlarına çevrildiğini gösteren pencere.

Bu son maddeye çoğu yeni başlayan ürküyle bakar — "ben assembly okuyamam"
diye. Gerçek şu: okuman gerekmiyor, *tanıman* yetiyor. `LDR`/`STR` gördüğünde
"bellekten okuma/belleğe yazma" de, geç. Asıl değerli olan şu: `volatile`
işaretlemediğin bir değişkenin okunmasının derleyici tarafından tamamen
silindiğini disassembly'de gözünle görebilmen — Bölüm 5'te anlattığımız
hikâyenin (Şekil 10) somut kanıtı burada, ekranında duruyor.

:::derin-dalis Disassembly'de volatile'ın izini sürmek
İki derlemeyi yan yana koy. `volatile` olmayan bir bayrağı döngüde okuyan
kod, optimizasyon açıldığında (`-O2`) genelde şuna benzer bir şey üretir —
değişken bir kere register'a yüklenir, döngü boyunca bellek bir daha hiç
ziyaret edilmez:

```metin
; G_ucFlag volatile DEĞİL, -O2
LDR   w0, [x1]        ; bir KERE yüklendi
donguDevam:
b.eq  donguDevam       ; sonrasında hep aynı register'a bakılıyor
```

`volatile` eklenince derleyici her döngü turunda belleğe gerçekten gider:

```metin
; G_ucFlag volatile, -O2
donguBasi:
LDR   w0, [x1]        ; HER turda tekrar yükleniyor
b.eq  donguBasi
```

Görev 10'da tam bu ikilemle karşılaşacaksın; disassembly penceresi orada
şüpheni kanıta çevirecek yer olacak.
:::

## XSCT/xsdb: konsolun arkasındaki konsol

Vitis'in altında, IDE'nin grafik arayüzünün perde arkasında **XSCT** (Xilinx
Software Command-Line Tool) çalışır; interaktif hedef kontrolü için
kullanılan komut satırı arayüzü **xsdb**'dir. Günlük işinde XSCT'yi elle
çağırman gerekmez — Vitis onu senin için çalıştırır — ama bir gün otomasyon
yazman ya da IDE'nin göstermediği bir ayrıntıyı sorgulaman gerekirse, IDE
içindeki XSCT konsolu penceresi tam bu iş için orada durur. Şimdilik
varlığını bil; ekip arkadaşların "xsct'den bak" dediğinde nereye bakacağını
bileceksin.

{{svg:sema-24-debug-akisi.svg|Şekil 24 — Debug oturumu döngüsü: JTAG bağlan → breakpoint koy → run/durdu → adım adım ilerle → register/memory/değişken izle → hipotez kur → düzelt ve yeniden derle; kenarda "dört silah" rozetleri.}}

:::saha-notu Dört silah
Bir hata avına çıktığında elinde dört silah var, hepsi farklı işe yarar.
**printf** (UART'a satır bas) hızlıdır ama akışı yavaşlatır, ISR içinde
tehlikelidir. **LED** tek bitlik ama zamanlamayı neredeyse hiç bozmayan bir
sinyaldir — belirli bir noktada yakıp söndürmek, "buraya geldi mi geldi"
sorusuna osiloskopla bile cevap verebilir. **Debugger** durdurur, içine
bakmanı sağlar, ama zaman akışını dondurduğun için gerçek zamanlı hataları
maskeleyebilir. **Lojik analizör** dışarıdan, hattı hiç bozmadan izler — en
dürüst tanık, ama kurulumu en zahmetli olan. İyi bir gömülü yazılımcı bu
dördü arasında seçim yapmayı bilir; hangi belirtinin hangi silahı istediğini
Görev 10'da elinle öğreneceksin.
:::

Alet çantan artık tam; teori burada bitiyor, sıra dedektiflikte.

:::gorev no=10 zorluk=3 baslik="Bug Avı" kisa="Bug Avı"
[Hedef]
`lab10-bugav` projesindeki 4 gerçek hatayı bul, düzelt ve her biri için tek
cümlelik bir kök neden yaz.

[Ön koşul]
Bölüm 4-11 okundu; Görev 1, 2, 4 ve 5 tamamlandı (register erişimi, UART,
interrupt ve TTC ile artık aşinasın).

[Adımlar]
1. `labs/lab10-bugav/` projesini incele — bu proje senden önceki stajyerden
   kaldı. `README.md`'deki spesifikasyonu ve gözlenen belirtileri dikkatle
   oku: derleniyor, karta yükleniyor, ama dört yerinde iş beklendiği gibi
   yürümüyor.
2. Projeyi kendi Vitis workspace'inde bir uygulama bileşeni olarak aç, derle
   ve **Debug configuration** ile karta yükle (README'de tam adımlar var).
3. Sıradaki dört bulguyu tahmin etmeden önce sistemi kendi gözünle çalıştır;
   her belirti için hangi silahın (printf, LED, debugger, lojik analizör)
   işine yarayacağına önce kendin karar ver.
4. Dört hatayı bulup düzelt. Her düzeltmeden sonra sistemi baştan test et —
   bir hatayı düzeltmek bazen bir öncekinin belirtisini değiştirir.
5. Her hata için tek cümlelik bir kök neden yaz (ne oldu değil, *neden*
   oldu).

[Başarı kriteri]
Proje spesifikasyona tam uyuyor: TTC0 ile saniyede bir "tick N" satırı
akıyor, SW19 basışında "buton: M" satırı çıkıyor ve DS50 toggle oluyor,
sayaçlar doğru artıyor, sistem saatlerce kararlı çalışıyor — ve elinde 4
hata için 4 kök neden cümlesi var.

[Kendini sına]
- Bu dört hatadan hangisini debugger olmadan, yalnızca UART çıktısına
  bakarak bulamazdın? Neden?
- Release (optimizasyonlu, `-O2`) ve debug (`-O0`) derlemeleri arasındaki
  fark hangi hatanın görünürlüğünü etkiliyor, hangisini gizliyor?
- Dördüncü hatanın belirtisi neden hemen değil, sistem "bir süre" çalıştıktan
  sonra ortaya çıkıyor?

[Takıldıysan]
::ipucu İpucu 1 — Hangi silah hangi belirtiye
Dört belirtiyi teker teker düşün. "Optimizasyonlu derlemede buton hiç tepki
vermiyor" cümlesi seni doğrudan derleyicinin ne yaptığını sorgulamaya
götürmeli — disassembly penceresi burada devreye girer. "Tick bazen sekiyor
ya da geç geliyor" zamanlamayla ilgili, yani kesmelerin ne kadar sürdüğüyle
— bir LED ya da zaman damgasıyla ölçülebilir. "DS50 bir kez yanıp bir daha
sönmüyor" saf bir mantık hatası, tek satırlık kaynağa bakmak yeterli.
"Sistem rastgele çöküyor" ise klasik bir bellek/stack şüphesi — memory
penceresi ve `lscript.ld` senin dostun.
::/
::ipucu İpucu 2 — Somut izler
(1) `G_ucButtonFlag` bayrağının tanımına bak: bir niteleyici eksik. (2)
Buton ISR'inin içine bak: orada olmaması gereken iki şey var, ikisi de
zaman alıyor. (3) LED'i tersine çeviren satırı bul: kullanılan bit
operatörü "aç" diyor ama "tersine çevir" demiyor. (4) 8 KB'lık yerel bir
diziyle başlayan fonksiyonu bul, `lscript.ld`'deki stack boyutuyla
karşılaştır.
::/
::cozum Tam çözüm — 4 hata: konum, kök neden, düzeltme
### 1. `G_ucButtonFlag` volatile değil

**Konum:** `src/gpio_led_buton.h` (global değişken tanımı); kullanıldığı
yerler `src/main.c` ana döngü ve `src/gpio_led_buton.c` buton ISR'i.

**Kök neden:** Değişken ISR ile ana döngü arasında paylaşılıyor ama
`volatile` işaretli değil; `-O2` optimizasyonunda derleyici ana döngüde
değişkenin bir daha değişmeyeceğini varsayıp değerini bir register'da
önbelleğe alıyor, bu yüzden ISR belleği güncellese de ana döngü bunu hiç
görmüyor.

**Düzeltme:**
```c
/* önce */
unsigned char G_ucButtonFlag = 0;
/* sonra */
volatile unsigned char G_ucButtonFlag = 0;
```

### 2. Buton ISR'inde uzun iş (xil_printf + gecikme döngüsü)

**Konum:** `src/gpio_led_buton.c`, `buttonIsr()` fonksiyonu.

**Kök neden:** ISR'in içine "hızlı bir durum satırı" gerekçesiyle eklenen
`xil_printf` çağrısı ve boş bekleme döngüsü, kesmeyi olması gerekenden çok
daha uzun tutuyor; bu süre boyunca öncelikli TTC kesmeleri gecikiyor ya da
kaçıyor, bu da tick sayacının sekmesine/geç gelmesine yol açıyor.

**Düzeltme:** ISR yalnızca bayrağı set etsin ve sayacı artırsın; yazdırma
işini ana döngüye taşı — ayrıntılı diff için `labs/lab10-bugav/COZUM.md`'ye
bak.

### 3. DS50 toggle'da `|=` kullanılmış

**Konum:** `src/gpio_led_buton.c`, `ledDs50Toggle()` fonksiyonu.

**Kök neden:** Durumu tersine çevirmesi gereken satır `^=` yerine `|=`
kullanıyor; `|= 1` her çağrıda durumu 1'e sabitliyor, yani LED bir kez
yandıktan sonra bir daha hiç sönmüyor.

**Düzeltme:**
```c
/* önce */
G_uiDs50State |= 1;
/* sonra */
G_uiDs50State ^= 1;
```

### 4. 8 KB'lık yerel dizi → stack taşması

**Konum:** `src/main.c`, `printHealthSummary()` fonksiyonu;
karşılaştırma için `src/lscript.ld`'deki `_STACK_SIZE`.

**Kök neden:** Fonksiyon her çağrıldığında 8 KB'lık `cArrHistoryBuffer` dizisi
stack üzerinde ayrılıyor; bu proje için `lscript.ld`'de ayrılan stack alanı
bunu, üstüne binen diğer çağrı çerçeveleriyle birlikte, taşıracak kadar dar.
Taşma komşu bellek bölgesini bozuyor; bozulan verinin ne olduğu çağrı
anındaki stack derinliğine (kesme araya girdi mi, girmedi mi) bağlı olduğu
için çökme hemen değil, sistem bir süre çalıştıktan sonra rastgele ortaya
çıkıyor.

**Düzeltme:** Buffer'ı gerçek ihtiyaca indir:
```c
/* önce */
char cArrHistoryBuffer[8192];
/* sonra */
char cArrHistoryBuffer[128];
```
Kalıcı çözüm için `lscript.ld`'deki `_STACK_SIZE` değerini de projenin
gerçek en kötü durum çağrı derinliğine göre gözden geçir. Tam açıklama:
`labs/lab10-bugav/COZUM.md`.
::/
:::

Dört hatayı da bulup düzelttiysen artık alet çantanı gerçekten tanıyorsun —
debugger'ı korkmadan açan, disassembly'ye bakınca ürkmeyen, hangi belirtide
hangi silahı çekeceğini bilen biri oldun. Aletleri tanıdın; şimdi sıra
zanaatın görgü kurallarında: iyi bir gömülü yazılımcıyı yalnızca çalışan
kod değil, ekiple çalışabilme becerisi de tanımlar.
