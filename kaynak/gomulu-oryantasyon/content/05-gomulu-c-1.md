# Bölüm 5 — Gömülü C Pratikleri I: Dilin Donanımla Buluştuğu Yer

Register'ları register map'ten okudun ve elle adresledin; ama C dilinin
donanımla bu düzeydeki ilişkisi inceliklerle doludur — bu bölüm
bunların ilkini ele alır. Üniversitede öğrendiğin C çoğunlukla
"değerler bellekte durur, ben okur/yazarım" varsayımıyla çalışır.
Donanım register'ları bu varsayımı bozar: bir register'ın değeri, senin
kodundan tek satır çalışmadan, arka planda değişebilir — bir düğmeye
basılır, bir interrupt gelir, bir DMA (Direct Memory Access — CPU'yu
araya sokmadan belleğe doğrudan yazan donanım; ayrıntısı Bölüm 6 ve
9'da) veri aktarır. Bu bölümde C'nin bu gerçeklikle konuşmasını
sağlayan araçları öğreneceksin.

## volatile: Derleyiciye "Optimizasyonların Burada Geçmez" Demek

Derleyiciler tembel değildir — tam tersine, saldırgan optimizasyon
yapar. Derleyici bir değişkenin art arda birkaç kez okunduğunu görür ve
arada değişmediğini "kanıtlayabilirse" (kodun kendi akışında yazma
görmüyorsa) okumayı tekrarlamaz: değeri bir kez CPU register'ında tutar
ve sonraki okumaları sessizce eler. Sıradan bir değişken için bu
mükemmel bir optimizasyondur — gereksiz bellek erişimini önler. Ama şu
koda bak:

```c
unsigned int uiFlag = 0;
while (uiFlag == 0)
{
    /* waiting for uiFlag to be set from somewhere */
}
```

Derleyici `uiFlag`'in döngü içinde hiç yazılmadığını görür ve "bu değer
hiç değişmiyor, koşulu bir kez değerlendirip sonucu sabitlerim" diye
akıl yürütebilir — sonuç, bir ISR ya da donanım `uiFlag`'i gerçekte
değiştirse bile döngüye hiç girmemek ya da içinde sonsuza dek
kalmaktır. `volatile` anahtar sözcüğü tam olarak bunu engeller:
derleyiciye "bu adresteki değer senin göremediğin bir yerden
değişebilir; her erişimde gerçekten oku/yaz, önceki okumaya güvenme"
der.

{{svg:sema-10-volatile.svg|Şekil 10 — volatile'ın öyküsü: aynı -O2 optimizasyonu volatile'sız kodda okumayı eler, volatile'lı kodda her turda taze okuma yapmaya zorlanır.}}

`volatile`'a ihtiyaç duyacağın iki tipik yer var: **donanım
register'ları** (her okuma, donanım durumunun gerçek bir sorgusu
olmalı) ve **ISR (interrupt service routine — kesme servis rutini) ile
ana kod arasında paylaşılan değişkenler** (bunu Bölüm 7'de kendi
elinle yaşayacaksın). İkisinde de ortak nokta aynıdır: değer
"dışarıdan" biri tarafından değiştirilebilir.

:::tuzak volatile'sız Bayrak, "Çalışıyor Görünen" Bir Hatadır
ISR'nin kurduğu bir bayrağı ana döngüde `volatile` olmadan okursan kod
derlenir, hatta -O0'da (optimizasyonsuz derleme) çalışıyor bile
görünebilir — çünkü -O0 gereksiz okumaları zaten elemez. Optimizasyonu
açtığın anda (örn. -O2) aynı kod takılmış görünür. Bu, klasik "debug'da
çalışıyor, release'te bozuluyor" probleminin en sık kök nedenlerinden
biridir; o klasik problemi Bölüm 6'da yakından ele alacağız.
:::

## Bit İşlemleri: Register'ın Tek Bitine Dokunmak

Bir register'ın 32 bitinin çoğu, bit ya da bit grubu olarak ayrı bir
anlam taşır — TXFULL bir bit, RXEMPTY başka bir bit. Register'ın
kalanını bozmadan tek bir bite dokunmak için dört temel işlem yeter:

| İşlem | İfade | Ne yapar |
|---|---|---|
| SET | `uiReg |= MASK;` | İlgili biti 1 yapar, diğerlerine dokunmaz |
| CLEAR | `uiReg &= ~MASK;` | İlgili biti 0 yapar, diğerlerine dokunmaz |
| TOGGLE | `uiReg ^= MASK;` | İlgili biti tersler |
| TEST | `if (uiReg & MASK)` | İlgili bitin 1 olup olmadığını sorar, hiçbir şeyi değiştirmez |

{{svg:sema-11-bit-islemleri.svg|Şekil 11 — Bit işlemleri görsel referansı: SET, CLEAR, TOGGLE ve TEST için önce/mask/sonra 8 bitlik kutular.}}

Mask'i `0x10` gibi elle yazmak yerine bit numarasından üretmek
okunabilirliği ciddi biçimde artırır. Ekibimizde hemen her projede şu
makro seti bulunur:

```c
#define BIT(n)          (1u << (n))
#define BIT_SET(reg, n)     ((reg) |=  BIT(n))
#define BIT_CLEAR(reg, n)   ((reg) &= ~BIT(n))
#define BIT_TOGGLE(reg, n)  ((reg) ^=  BIT(n))
#define BIT_TEST(reg, n)    (((reg) & BIT(n)) != 0u)
```

`BIT_SET(UART0_SR, 4)` yazmak hem `UART0_SR |= 0x10` yazmaktan daha
okunaklıdır hem de bit numarası ile register map dokümanı arasındaki
bağı doğrudan gösterir — doküman "bit 4 = TXFULL" diyorsa kodun da
"bit 4" demesi, altı ay sonra kodu yeniden okuyan sana (ya da bir ekip
arkadaşına) zaman kazandırır.

## Tip Genişliği: Neden Önemsemelisin (ve Neden Düz Tip Kullanıyoruz)

C standardı `int`'in kaç bit olduğunu garanti etmez — derleyiciye ve
platforma göre 16, 32, hatta 64 bit olabilir. Register 32 bit
genişliğindeyse ve ona genişliğini bilmediğin bir tiple erişiyorsan,
sessizce yanlış sayıda byte okuyup yazabilirsin — donanım bunu asla
affetmez. Buradaki asıl ders belirli bir tip adı değildir: **erişimin
kaç bit olduğundan emin olmaktır.**

Genellikle duyacağın öğüt şudur: "`<stdint.h>`'in sabit genişlikli
tiplerini (`uint32_t` gibi) kullan." **Ekibimiz bu işi farklı çözer:**
standardımız `stdint.h` tiplerini yasaklar ve **düz C tiplerini**
kullanır — `unsigned char`, `unsigned short`, `unsigned int`,
`unsigned long long`. Bu neden güvenli? Çünkü tek bir hedef için
yazıyorsun: ZynqMP artı tek bir toolchain. O sabit dünyada her düz
tipin genişliği kesin ve bilinir — `unsigned int`, hedefinde **her
zaman 32 bittir**. Genişlik zaten sabitken `uint32_t`'nin ek
soyutlamasına gerek kalmaz; düz tipler kod tabanına tek ve tutarlı bir
tip sözlüğü kazandırır. Yani register'a `unsigned int` ile erişirsin —
kör bir `int` değil, genişliğini *bilerek* seçtiğin bir tip.

:::ekip-notu stdint Yok — ama İlkeyi Anla
Bir gün başka bir ekipte `uint32_t` göreceksin ve o da doğrudur — iki
dünya aynı ilkenin farklı uygulamalarıdır: "genişliğini bildiğin tiple
eriş." Ekibimizde kural nettir: `uint8_t`/`uint16_t`/`uint32_t`/
`uint64_t` yerine `unsigned char`/`unsigned short`/`unsigned int`/
`unsigned long long`. Tek istisna **Xilinx kütüphane imzalarıdır:**
Xilinx başlıkları kendi typedef'lerini tanımlar, `u8`/`u32` (bunlar
`stdint` değildir — kütüphanenin kendi tipleridir);
`XUartPs_Send(..., u8* ...)` gibi bir imzayla karşılaştığında o
parametre için Xilinx'in tipini kullanırsın. Ama **kendi**
değişkenlerinde her zaman düz tipe dönersin (`unsigned int uiOffset`).
:::

## Bitfield Struct'lar: Cazibesi ve Tuzakları

C, struct içinde bit alanı tanımlamana izin verir:

```c
typedef struct
{
    unsigned int uiEnable : 1;
    unsigned int uiMode   : 2;
    unsigned int uiRsvd   : 29;
} SUartCrBits;
```

İlk bakışta cazip: `sCr.uiEnable = 1;` yazmak mask'lerle uğraşmaktan
çok daha okunaklı görünür. Ama C standardı bu bitlerin struct içinde
hangi sırayla paketlendiğini (önden mi arkadan mı, hizalamanın nasıl
işlediğini) tanımlamaz — karar derleyiciye ve platforma bırakılmıştır
("implementation-defined"). Aynı struct, farklı bir derleyicide ya da
farklı bir mimaride bitlerini ters sırada paketleyebilir; kodun o
zaman sessizce yanlış bitleri okuyup yazar.

:::tuzak Bitfield'ın Bit Sırası Taşınabilir Değildir
Bir register'ı bitfield struct'la modellemek masanın üzerinde
"çalışıyor" görünse bile, o kod farklı bir derleyiciye ya da mimariye
taşındığında bit paketleme sırası değişebilir; kod o zaman sessizce
yanlış bitleri okuyup yazar. Bu, bitfield'ların kaçınılmaz yan
etkisidir — kullanırken farkında olman gereken bir maliyettir.
:::

**Ekibimizde bitfield struct yaygın pratiktir.** `sCr.uiEnable = 1;`
yazmak hem mask aritmetiğinden çok daha okunaklıdır hem de niyeti
anında gösterir; kod tabanı büyüdükçe bu okunabilirlik gerçek bir
kazançtır. Yukarıdaki taşınabilirlik uyarısını bilerek kabul ediyoruz:
ürün kodumuz tek bir toolchain (AMD/Xilinx) ve tek bir hedef mimari
(ZynqMP) için derlenir — kontrol ettiğimiz bu sabit dünyada bit sırası
değişmez, dolayısıyla o risk bizim için fiilen ortadan kalkar. Yine de
iki kuralı unutma: **(1)** derleyiciler ya da mimariler arasında
dolaşan bir veri formatı için (ağ paketi, dosyaya yazılan kayıt, başka
bir çiple paylaşılan yapı) asla bitfield struct kullanma — orada bit
sırası garantisinin yokluğu gerçek bir hataya dönüşür; **(2)** yeni
bir register'ı bitfield'la modellediğinde, alanların donanım
yerleşimiyle gerçekten örtüştüğünü ilk bring-up sırasında bir kez
doğrula. Mask makroları (`BIT_SET`/`BIT_CLEAR`/`BIT_TEST`) el altında
durur: tekil bit dokunuşlarında ya da mutlak taşınabilirlik
gerektiğinde daha doğrudan araç onlardır. İkisi rakip değildir — aynı
çantadaki iki alettir.

## Pointer Tabanlı Register Erişim Desenleri

Bölüm 4'te gördüğün taban + offset aritmetiğinin C karşılığı, sabit
bir adresi gösteren `volatile` bir pointer'dır:

```c
#define UART0_SR (*(volatile unsigned int*)(0xFF000000U + 0x2CU))
```

Bu satırı parça parça oku: `0xFF000000U + 0x2CU` gerçek adresi
hesaplar; `(volatile unsigned int*)` bu adresi "her erişimde gerçekten
okunup yazılması gereken 32 bitlik bir konum" olarak yorumlar; baştaki
`*` o adresi **dereference** eder, yani adresin gösterdiği değerin
kendisine ulaşır. Sonuç: `UART0_SR` adını her kullandığında derleyici
seni doğrudan o adrese götürür — `UART0_SR & 0x10` bir okumadır,
`UART0_SR = 0` bir yazmadır. Aynı deseni `uart_ps.c` modülünde
(Görev 2) birebir kullanacaksın.

Bazı register'lar yalnızca okunur (Bölüm 4'teki RO erişim tipini
hatırla) — donanım günceller, sen yazamazsın. Bunu C'de ifade etmenin
yolu `const volatile` bileşimidir:

```c
#define UART0_SR_RO (*(const volatile unsigned int*)(0xFF000000U + 0x2CU))
```

`volatile` yine "her erişimde gerçekten oku" der; `const` buna "bu
pointer üzerinden yazma girişimi olursa derleme hatası üret"
talimatını ekler. İkisi çelişmez — biri erişimin *sıklığını*, diğeri
*yönünü* garanti eder.

:::ekip-notu Bunlar Code Review'da Denetlenir
Ekibimizde kod makineyle de denetlenir (adlandırma linter'ı artı
clang-format/clang-tidy); ihlaller review'dan geçmez. Özetle:

- **Fonksiyon adları** camelCase, alt çizgisiz, İngilizce:
  `uartSendChar`, `ina226Init` — `uart_send_char` gibi snake_case
  değil.
- **Değişkenler** tip öneki artı camelCase gövde: `uc` (unsigned
  char), `c` (char), `us`/`s` (short), `ui`/`i` (int), `ul`/`ull`
  (`long` tipleri). Pointer, tip önekine `p` ekler (`char*` → `cp`,
  `unsigned int*` → `uip`); struct pointer `sp` kullanır
  (`XIicPs* spIic`); dizi `Arr` ekler; `static` → `S_`, global → `G_`
  en başa gelir (`G_uiTickCount`). Örnekler: `unsigned int uiIndex`,
  `char* cpString`.
- **Tipler** düz C tipleridir; `stdint.h` (`uint32_t`) yasaktır
  (yukarıdaki nota bak).
- **typedef**: struct → `S` (`SUartCrBits`), enum → `E` (`EState`).
- **Biçim:** Allman brace, 4 boşluk girinti, satır ≤ 100 karakter,
  kontrol anahtar sözcüklerinden sonra boşluk, pointer yıldızı tipe
  bitişik (`XIicPs* sp`), CRLF satır sonları, `printf` çıktısında
  `\r\n`.
- **Doxygen** public fonksiyonlarda zorunludur (`@brief`, `@param`,
  `@return`).

Bunlar estetik takıntısı değildir: yüzlerce dosyalık bir kod tabanında,
dosyayı açmadan yalnızca adına bakarak bir değişkenin ne tuttuğunu ve
bir fonksiyonun ne yaptığını söyleyebilirsin — ve linter bunu senin
yerine dayattığı için review süresi biçime değil öze harcanır.
:::

Donanımla konuşan C'nin temel sözlüğünü artık öğrendin: `volatile`,
bit işlemleri, doğru genişlikte tipler ve pointer tabanlı adresleme.
Sıra pratikte: UART'tan kendi elinle bir şey basma vakti.

:::gorev no=2 zorluk=1 baslik="UART Hello World ve printf'in Arkasındakiler" kisa="UART Hello World"
[Hedef]
`xil_printf` ile UART0'dan bir satır bas; ardından kendi register
düzeyindeki `uart_ps` modülünle çok satırlı bir karşılama banner'ı
bas.

[Ön koşul]
Bölüm 4 ve 5 okundu; Görev 1 tamamlandı (Vitis'te empty application
projesi açma akışına aşinasın).

[Adımlar]
1. Vitis'te yeni bir **empty application** projesi aç ve ekibinin
   platformuna bağla.
2. Bu görevin çözüm dosyaları `lab02-uart/src/uart_ps.h`, `uart_ps.c`
   ve `main.c`'yi projenin `src/` klasörüne kopyala. Önce kendin
   denemek istersen, aşağıdaki ipucu merdivenine başvurmadan kendi
   `uart_ps.c` dosyanı yazmayı dene.
3. `uartSendChar()` içinde önce **SR register'ını** oku (taban
   `0xFF000000` + offset `0x2C`), **TXFULL biti** (mask `0x10`)
   sıfırlanana kadar bekle, sonra karakteri **FIFO register'ına**
   (offset `0x30`) yaz — bu, Bölüm 4'ün son örneğinin ta kendisidir.
4. `uartSendString()` fonksiyonunu, string'i karakter karakter
   `uartSendChar()`'a gönderecek ve her `'\n'` gördüğünde önce `'\r'`
   gönderecek şekilde yaz (bunun neden gerekli olduğunu kod yorumunda
   açıkla).
5. `main()` içinde önce `xil_printf` ile tek satır bas, ardından kendi
   `uartInit()` / `uartSendString()` fonksiyonlarınla birkaç satırlık
   karşılama banner'ını bas.
6. Projeyi derle, JTAG üzerinden karta yükle ve terminali Görev 0'daki
   ayarlarla aç.

[Başarı kriteri]
Terminalde önce `xil_printf` satırını, ardından kendi fonksiyonlarının
bastığı çok satırlı karşılama banner'ını görürsün.

[Kendini sına]
- TXFULL bitinin düşmesini beklemeseydin (kontrolü atlasaydın) ne
  olurdu? FIFO doluyken yazdığın karakterlere ne olur?
- `xil_printf` içinde `%f` neden çalışmaz? (İpucu: cevap `main.c`'deki
  bir yorumda; ama önce kendi tahminini yap.)
- `uartInit()` fonksiyonun aslında neredeyse boş — bunun bir eksik
  değil bilinçli bir tasarım tercihi olduğunu tek cümleyle açıkla.

[Takıldıysan]
::ipucu İpucu 1 — TXFULL Bekleme Döngüsü Çalışmıyor / Hiç Bitmiyor
Mask'i (`0x10`) SR register'ının doğru adresine mi uyguluyorsun (taban
+ `0x2C`, `0x30` değil)? `while` koşulunu "TXFULL 1 iken bekle" diye
mi yazdın, yoksa yanlışlıkla tersini mi? SR'yi `volatile` bir pointer
üzerinden mi okuyorsun — değilse derleyici okumayı eleyip seni sonsuz
döngüde bırakabilir (Bölüm 5'in ana dersi tam burada karşına çıkar).
::/
::ipucu İpucu 2 — '\n' Gönderiyorum ama Terminal Satır Başına Dönmüyor
Terminaller `'\n'` (line feed) karakterini "bir satır aşağı in, sütun
aynı" diye yorumlar; satırı gerçekten başa döndürmek için `'\r'`
(carriage return) karakterini de göndermen gerekir. `uartSendString()`
içinde, bir `'\n'` gördüğün anda önce `uartSendChar('\r')` çağırmayı,
sonra `'\n'` göndermeyi dene.
::/
::cozum Tam Çözüm — lab02-uart
Aşağıdaki üç dosya UART0'ı register düzeyinde sürer ve karşılama
banner'ını basar:
{{kod:lab02-uart/src/uart_ps.h}}
{{kod:lab02-uart/src/uart_ps.c}}
{{kod:lab02-uart/src/main.c}}
::/
:::
