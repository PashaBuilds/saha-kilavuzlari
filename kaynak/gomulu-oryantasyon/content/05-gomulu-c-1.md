# Bölüm 5 — Gömülü C Pratikleri I: Dil Donanıma Değince

Register'ları register map'ten okuyup elle adresledin; ama C dilinin bu
düzeyde donanımla ilişkisi ince noktalarla dolu — bu bölüm o inceliklerin
ilki. Üniversitede öğrendiğin C, çoğunlukla "değerler bellekte durur, ben
onları okur/yazarım" varsayımıyla çalışır. Donanım register'ları bu
varsayımı kırar: bir register'ın değeri senin kodun hiçbir satır
çalıştırmadan, arka planda değişebilir — bir buton basılır, bir kesme
gelir, bir DMA (DMA — Direct Memory Access; CPU'yu atlayıp doğrudan
belleğe yazan donanım; Bölüm 6 ve 9'da ayrıntısı) verisi taşır. Bu
bölümde C'nin bu gerçeklikle konuşmasını sağlayan araçları öğreneceksin.

## volatile: derleyiciye "burada numaran geçmez" demek

Derleyiciler tembel değil, tam tersi — agresif optimizasyon yapar. Bir
değişkeni art arda birkaç kez okuduğunu görürse ve o değişkenin arada
değişmediğini "kanıtlayabiliyorsa" (kodun kendi akışında hiçbir yazma
göremiyorsa), okumayı tekrarlamaz: değeri bir CPU register'ında bir kere
tutar, sonraki okumaları sessizce siler. Normal bir değişken için bu
harika bir optimizasyondur — gereksiz bellek erişimini önler. Ama şu kodu
düşün:

```c
unsigned int uiFlag = 0;
while (uiFlag == 0)
{
    /* bir yerlerden uiFlag set edilmesini bekliyoruz */
}
```

Derleyici `uiFlag`'in döngü içinde hiç yazılmadığını görür ve "bu değer
hiç değişmiyor, o zaman koşulu bir kez değerlendirip sonucu sabitleyeyim"
diye düşünebilir — sonuç ya döngüye hiç girmemek ya da sonsuza dek
takılmaktır, `uiFlag`'i gerçekte bir ISR ya da donanım değiştirse bile.
`volatile` anahtar kelimesi tam olarak bunu engeller: derleyiciye "bu
adresin değeri senin görmediğin bir yerden değişebilir, her erişimde
gerçekten oku/yaz, önceki okumaya güvenme" der.

{{svg:sema-10-volatile.svg|Şekil 10 — volatile'ın hikâyesi: aynı -O2 optimizasyonu, volatile'sız kodda okumayı siliyor, volatile'lı kodda her turda yeniden okutuyor.}}

`volatile` kullanman gereken iki tipik yer var: **donanım register'ları**
(her okuma gerçek bir donanım durumu sorgusu olmalı) ve **bir ISR
(interrupt service routine — kesme işleyicisi) ile ana koddan ortaklaşa
kullanılan değişkenler** (Bölüm 7'de bunu bizzat yaşayacaksın). İkisinde de
ortak nokta aynı: değeri "dışarıdan" biri değiştirebiliyor.

:::tuzak volatile'sız bir bayrak, "çalışıyor gibi görünen" bir hatadır
Bir ISR'nin set ettiği bayrağı ana döngüde `volatile` olmadan okursan, kod
derlenir, hatta -O0'da (optimizasyonsuz derlemede) çalışıyormuş gibi bile
görünebilir — çünkü -O0 zaten gereksiz okumayı silmez. Optimizasyonu
açtığın (-O2 gibi) an aynı kod donmuş gibi takılır. Bu, "debug'da
çalışıyor, release'te çalışmıyor" klasiğinin en sık kök nedenlerinden
biridir; Bölüm 6'da bu klasiği bizzat konuşacağız.
:::

## Bit işlemleri: register'ın tek bir bitiyle konuşmak

Bir register'ın 32 bitinin çoğu zaman her biri (ya da her grubu) ayrı bir
anlam taşır — TXFULL bir bit, RXEMPTY başka bir bit. Tüm register'ı
değiştirmeden tek bir bitle konuşmak için dört temel işlem yeterli:

| İşlem | İfade | Ne yapar |
|---|---|---|
| SET | `uiReg |= MASKE;` | İlgili biti 1 yapar, diğerlerine dokunmaz |
| CLEAR | `uiReg &= ~MASKE;` | İlgili biti 0 yapar, diğerlerine dokunmaz |
| TOGGLE | `uiReg ^= MASKE;` | İlgili biti tersine çevirir |
| TEST | `if (uiReg & MASKE)` | İlgili bit 1 mi diye sorar, hiçbir şeyi değiştirmez |

{{svg:sema-11-bit-islemleri.svg|Şekil 11 — Bit işlemleri görsel referansı: SET, CLEAR, TOGGLE ve TEST için önce/maske/sonra 8-bit kutuları.}}

Maskeyi elle `0x10` gibi yazmak yerine bit numarasından üretmek okunurluğu
katbekat artırır. Bizim ekipte hemen her projede şu makro seti bulunur:

```c
#define BIT(n)          (1u << (n))
#define BIT_SET(reg, n)     ((reg) |=  BIT(n))
#define BIT_CLEAR(reg, n)   ((reg) &= ~BIT(n))
#define BIT_TOGGLE(reg, n)  ((reg) ^=  BIT(n))
#define BIT_TEST(reg, n)    (((reg) & BIT(n)) != 0u)
```

`BIT_SET(UART0_SR, 4)` yazmak, `UART0_SR |= 0x10` yazmaktan hem daha
okunur hem de bit numarasıyla register map dokümanı arasındaki bağı
doğrudan gösterir — dokümanda "bit 4 = TXFULL" yazıyorsa kodun da "bit 4"
demesi, altı ay sonra kodu tekrar okuyan sana (ya da arkadaşına) zaman
kazandırır.

## Tip genişliği: neden umursarsın (ve neden biz düz tip kullanırız)

C standardı `int`'in kaç bit olduğunu garanti etmez — 16, 32, hatta bazı
platformlarda 64 bit olabilir; derleyiciye ve platforma bağlıdır. Bir
register 32 bit genişliğindeyse ve sen ona genişliğini bilmediğin bir tiple
erişirsen, sessizce yanlış sayıda bayt okuyup yazabilirsin — donanım bunu
asla affetmez. Buradaki asıl ders belirli bir tip adı değil: **erişimin kaç
bit olduğundan emin olmak**.

Genel olarak duyacağın tavsiye "`<stdint.h>`'nin sabit genişlikli tiplerini
(`uint32_t` gibi) kullan"dır. **Bizim ekibimiz bunu farklı çözer:**
standardımız `stdint.h` tiplerini yasaklar ve **düz C tiplerini** kullanır —
`unsigned char`, `unsigned short`, `unsigned int`, `unsigned long long`.
Neden güvenli? Çünkü sen tek bir hedef için yazıyorsun: ZynqMP + tek bir
toolchain. O sabit dünyada her düz tipin genişliği kesin ve bilinir —
`unsigned int` senin hedefinde **her zaman 32 bit**. Genişlik zaten
sabitken `uint32_t`'nin ekstra soyutlamasına gerek kalmaz; düz tipler kod
tabanına tek ve tutarlı bir tip sözlüğü verir. Yani register'a
`unsigned int` ile erişirsin — kör bir `int` değil, genişliğini *bilerek*
seçtiğin bir tip.

:::ekip-notu stdint yok — ama ilkeyi anla
Bir gün başka bir ekipte `uint32_t` göreceksin, o da doğru; iki dünya da
"genişliğini bildiğin tiple eriş" ilkesinin farklı uygulamaları. Bizde
kural nettir: `uint8_t`/`uint16_t`/`uint32_t`/`uint64_t` yerine
`unsigned char`/`unsigned short`/`unsigned int`/`unsigned long long`.
Tek istisna **Xilinx kütüphane imzaları:** Xilinx başlıkları `u8`/`u32` diye
kendi typedef'lerini tanımlar (bunlar `stdint` değil, kütüphanenin tipleri);
`XUartPs_Send(..., u8* ...)` gibi bir imzayla karşılaşınca o parametrede
Xilinx'in tipini kullanırsın. Ama **kendi** değişkenlerinde her zaman düz
tipe (`unsigned int uiOffset`) dönersin.
:::

## Bitfield struct'lar: cazibesi ve tuzakları

C, bir struct içinde bit alanları tanımlamana izin verir:

```c
typedef struct
{
    unsigned int uiEnable : 1;
    unsigned int uiMode   : 2;
    unsigned int uiRsvd   : 29;
} SUartCrBits;
```

İlk bakışta çekicidir: `sCr.uiEnable = 1;` yazmak, maskeyle uğraşmaktan
çok daha okunur görünür. Ama C standardı bu bitlerin struct içinde hangi
sırada paketleneceğini (baştan mı sondan mı, hizalamanın nasıl
olacağını) **tanımlamaz** — bu derleyiciye ve platforma bırakılmış
("implementation-defined") bir karardır. Aynı struct, farklı bir
derleyicide ya da farklı bir mimaride bitleri ters sırada paketleyebilir;
kodun sessizce yanlış bitleri okur/yazar hale gelir.

:::tuzak Bitfield'in bit sırası taşınabilir değildir
Bir register'ı bitfield struct'la modellemek masaüstünde "çalışıyor"
görünse bile, o kodu **başka bir derleyiciye ya da başka bir mimariye**
taşıdığında bit paketleme sırası değişebilir; kod sessizce yanlış bitleri
okur/yazar. Bu, bitfield'ın kaçınılmaz yan etkisidir — kullanırken
farkında olman gereken bedel.
:::

**Bizim ekipte bitfield struct'lar yaygın bir pratiktir (common practice).**
Çünkü `sCr.uiEnable = 1;` yazmak, maske aritmetiğinden hem çok daha okunur
hem de niyeti apaçık gösterir; kod tabanı büyüdükçe bu okunurluk gerçek bir
kazançtır. Yukarıdaki taşınabilirlik uyarısını bilerek kabul ederiz: ürün
kodumuz tek bir toolchain (AMD/Xilinx) ve tek bir hedef mimari (ZynqMP)
için derlenir — bit sırası bizim kontrolümüzdeki sabit bir dünyada
değişmez, dolayısıyla o riziko bizim için fiilen ortadan kalkar. İki kuralı
yine de unutma: **(1)** bir bitfield struct'ı **asla** derleyiciler/mimariler
arası taşınan bir veri formatı için (ağ paketi, dosyaya yazılan kayıt,
başka bir çiple paylaşılan yapı) kullanma — orada bit sırası garantisizliği
gerçek bir hataya döner; **(2)** yeni bir register'ı bitfield'la
modellediğinde, alanların gerçekten donanım düzenine oturduğunu ilk
bring-up'ta bir kez doğrula. Maske makroları (`BIT_SET` / `BIT_CLEAR` /
`BIT_TEST`) hâlâ elinin altında: tek tük bit dokunuşlarında ya da mutlak
taşınabilirlik gerektiğinde onlar daha doğrudan bir araçtır. İkisi rakip
değil, aynı çantadaki iki alet.

## Pointer ile register erişim kalıpları

Bölüm 4'te gördüğün taban + offset aritmetiğinin C'deki karşılığı, sabit
bir adresi gösteren bir `volatile` pointer'dır:

```c
#define UART0_SR (*(volatile unsigned int*)(0xFF000000U + 0x2CU))
```

Bu satırı parça parça oku: `0xFF000000U + 0x2CU` gerçek adresi hesaplar;
`(volatile unsigned int*)` bu adresi "32 bitlik, her erişimde gerçekten
oku/yaz'ılması gereken bir yer" olarak yorumlar; başındaki `*` o adresi
**dereference** eder, yani "oradaki değerin kendisi". Sonuç: `UART0_SR`
adını her kullandığında derleyici seni doğrudan o adrese götürür —
`UART0_SR & 0x10` bir okuma, `UART0_SR = 0` bir yazmadır. `uart_ps.c`
modülünde (Görev 2) bu deseni birebir kullanacaksın.

Bazı register'lar salt okunurdur (Bölüm 4'teki RO erişim tipini
hatırla) — donanım günceller, sen yazamazsın. Bunu C'de ifade etmenin
yolu `const volatile` kombinasyonudur:

```c
#define UART0_SR_RO (*(const volatile unsigned int*)(0xFF000000U + 0x2CU))
```

`volatile` hâlâ "her erişimde gerçekten oku" der; `const` ise derleyiciye
"bu pointer üzerinden yazma denemesi olursa derleme hatası ver" talimatını
ekler. İkisi çelişmiyor — biri erişimin *sıklığını*, diğeri erişimin
*yönünü* garanti ediyor.

:::ekip-notu Kod review'da bunlara bakılır
Ekibimizde kod, makine tarafından da denetlenir (naming linter +
clang-format/clang-tidy); ihlal review'ı geçmez. Özü:

- **Fonksiyon adları** camelCase, alt çizgisiz, İngilizce: `uartSendChar`,
  `ina226Init` — `uartSendChar` gibi snake_case **değil**.
- **Değişkenler** tip öneki + camelCase gövde: `uc` (unsigned char), `c`
  (char), `us`/`s` (short), `ui`/`i` (int), `ul`/`ull` (long'lar). Pointer,
  tip önekine `p` ekler (`char*` → `cp`, `unsigned int*` → `uip`); struct
  pointer `sp` (`XIicPs* spIic`); dizi `Arr` ekler; `static` → `S_`,
  global → `G_` en başa gelir (`G_uiTickCount`). Örn: `unsigned int uiIndex`,
  `char* cpString`.
- **Tipler** düz C tipleri; `stdint.h` (`uint32_t`) yasak (yukarıdaki nota bak).
- **typedef** struct → `S` (`SUartCrBits`), enum → `E` (`EState`).
- **Biçim:** Allman brace, 4 boşluk girinti, satır ≤ 100 karakter, kontrol
  sözcüğünden sonra boşluk, pointer yıldızı tipe yapışık (`XIicPs* sp`),
  satır sonu CRLF, `printf` çıktısında `\r\n`.
- **Doxygen** public fonksiyonlarda zorunlu (`@brief`, `@param`, `@return`).

Bunlar estetik takıntı değil: yüzlerce dosyalık bir kod tabanında isme
bakarak bir değişkenin ne tuttuğunu, bir fonksiyonun ne yaptığını dosyayı
açmadan anlarsın — ve linter bunu senin yerine zorladığı için review zamanı
biçime değil, gerçek meseleye kalır.
:::

Artık donanımla konuşan C'nin temel sözlüğünü öğrendin: `volatile`, bit
işlemleri, doğru genişlikli tipler, pointer'la adresleme. Sıra pratikte:
UART'tan kendi elinle bir şeyler bastırma vakti geldi.

:::gorev no=2 zorluk=1 baslik="UART Merhaba Dünya ve printf'in Arkası" kisa="UART Merhaba"
[Hedef]
UART0'dan `xil_printf` ile bir satır, ardından kendi yazdığın register
seviyesi `uart_ps` modülüyle çok satırlı bir karşılama ekranı (banner)
bastırmak.

[Ön koşul]
Bölüm 4 ve 5 okundu; Görev 1 tamamlandı (Vitis'te boş uygulama projesi
açma akışı elinde).

[Adımlar]
1. Vitis'te yeni bir **boş (empty) uygulama** projesi aç, ekibin
   platformuna bağla.
2. Bu görevin çözüm dosyaları olan `lab02-uart/src/uart_ps.h`,
   `uart_ps.c` ve `main.c`'yi projenin `src/` klasörüne kopyala —
   ama önce kendi denemeni yapmak istersen aşağıdaki ipucu merdivenini
   kullanmadan kendi `uart_ps.c`'ni yazmayı dene.
3. `uartSendChar()` fonksiyonunda önce **SR register'ını**
   (taban `0xFF000000` + offset `0x2C`) oku, **TXFULL bitini**
   (maske `0x10`) sıfır olana kadar bekle, sonra karakteri **FIFO
   register'ına** (offset `0x30`) yaz — Bölüm 4'ün son örneğinin ta
   kendisi.
4. `uartSendString()`'i, dizgiyi karakter karakter
   `uartSendChar()`'e yollayacak, `'\n'` gördüğünde önce `'\r'`
   gönderecek şekilde yaz (neden gerektiğini kod yorumunda açıkla).
5. `main()`'de önce `xil_printf` ile tek bir satır bas, sonra kendi
   `uartInit()` / `uartSendString()` fonksiyonlarınla birkaç
   satırlık bir karşılama ekranı bastır.
6. Projeyi derle, JTAG üzerinden karta yükle, terminali Görev 0'daki
   ayarla aç.

[Başarı kriteri]
Terminalde önce `xil_printf` satırını, ardından kendi fonksiyonunla
bastığın çok satırlı karşılama ekranını (banner) görüyorsun.

[Kendini sına]
- TXFULL biti düşene kadar beklemeseydin (kontrolü atlasaydın) ne
  olurdu? FIFO doluyken yazdığın karakterlere ne olur?
- `xil_printf` içinde `%f` neden çalışmıyor? (İpucu: `main.c`'deki
  yorumda cevap var, ama önce kendi tahminini yap.)
- `uartInit()` fonksiyonun aslında neredeyse boş — bunun neden
  "eksik" değil, bilinçli bir tasarım olduğunu bir cümleyle anlat.

[Takıldıysan]
::ipucu İpucu 1 — TXFULL bekleme döngüsü çalışmıyor / hiç bitmiyor
Maskeyi (`0x10`) SR register'ının doğru adresine mi uyguluyorsun
(taban + `0x2C`, `0x30` değil)? `while` koşulunu "TXFULL 1 iken bekle"
yönünde mi kurdun, yoksa yanlışlıkla tersini mi yazdın? SR'yi `volatile`
pointer ile mi okuyorsun — değilse derleyici okumayı silip seni sonsuz
döngüde bırakabilir (Bölüm 5'in ana dersi tam burada karşına çıkıyor).
::/
::ipucu İpucu 2 — '\n' gönderiyorum ama terminalde satır kaymıyor
Terminaller `'\n'`i (line feed) "aynı sütunda bir satır aşağı in" olarak
yorumlar; satırın gerçekten en başa dönmesi için ayrıca `'\r'` (carriage
return) göndermen gerekir. `uartSendString()` içinde `'\n'`
karakterini gördüğün anda önce `uartSendChar('\r')` çağırıp
sonra `'\n'`i göndermeyi dene.
::/
::cozum Tam çözüm — lab02-uart
Aşağıdaki üç dosya UART0'ı register seviyesinde sürer ve karşılama
ekranını bastırır:
{{kod:lab02-uart/src/uart_ps.h}}
{{kod:lab02-uart/src/uart_ps.c}}
{{kod:lab02-uart/src/main.c}}
::/
:::
