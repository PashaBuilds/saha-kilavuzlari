# Bölüm 12 — Meslek Kültürü: Etkili Gömülü Mühendis

Görev 10'da dört hatayı tek tek yakaladın; bu bölümde görev kartı yok,
çünkü buradaki konu lab'da bir kez öğrenilen bir beceri değil, her gün
biraz daha yerleşen bir alışkanlıktır. İyi bir gömülü mühendisi ayıran
şey yalnızca çalışan kod değil, o kodun etrafındaki disiplindir:
savunmacı yazmak, okunur tutmak, ekiple etkili iletişim kurmak.

## Savunmacı programlama: her şeyin beklendiği gibi gitmeyeceğini varsay

Masaüstü kodunda bir fonksiyon başarısız olduğunda exception (istisna)
fırlatır, biri onu yakalar, yürütme devam eder. Gömülü sistemde o "biri"
çoğu zaman yoktur — sen kontrol etmezsen kimse etmez. Bu disiplinin
temelini üç alışkanlık oluşturur:

- **Dönüş değerini kontrol et.** `_stil.md`'nin vurguladığı gibi, bu kod
  tabanındaki `XST_SUCCESS` deseni süs değil kuraldır. Bir sürücü
  fonksiyonu hata kodu döndürüyorsa, o değeri okumadan bir sonraki satıra
  geçmek "muhtemelen iyi gitmiştir" bahsine girmektir. Sessizce başarısız
  olmuş bir I2C register okuması üzerine hesap kurmak, UART'a bile bile
  yanlış sıcaklık değeri basmaktan çok daha kötüdür.
- **Varsayımlarını `assert` ile görünür kıl.** Bir fonksiyona gelen
  pointer'ın asla NULL olmayacağına inanıyorsan bunu açıkça yaz:
  `assert(pDurum != NULL);`. Assert, "burada bir varsayım var, bozulursa
  hemen haber ver" demenin en ucuz yoludur; debug build'de seni erken
  uyarır, release build'de genellikle kapalıdır (bu yüzden gerçek hata
  yönetiminin yerine değil, yanına konur).
- **Timeout'suz sınırsız bekleme yasak.** Görev 6'da INA226'dan yanıt
  bekleyen `while` döngüsünü süresiz döndürmek yerine deneme sayısıyla
  sınırlaman istenmişti (yoksa şimdi ekle) — donanım yanıt vermezse
  programın sonsuza kadar asılı kalması kabul edilemez. Aynı disiplin her
  donanım beklemesi için geçerli: "yanıt gelene kadar bekle" yazma;
  "N deneme ya da M milisaniye bekle, sonra hata döndür" yaz.

:::tuzak "Çalışıyor" ile "doğru" aynı şey değil
Kodun bir kez sorunsuz koştuğunu görmek kodun doğru olduğu anlamına
gelmez — yalnızca o an, o koşullarda çalıştığı anlamına gelir. Donanım
yanıt vermezse, kablo bağlantısı gevşerse, sıcaklık sensörü beklenmedik
bir değer döndürürse ne olacağı düşünülmeden bırakılmış kod, sahada er
ya da geç bu senaryolardan biriyle karşılaşır.
:::

## Kod okunurluğu ve yorum kültürü

Kodun *ne* yaptığını zaten kodun kendisi söyler — satırı okuyan herkes
bir değişkenin ne tuttuğunu, bir döngünün kaç kez döndüğünü görür.
Yorumun görevi farklıdır: **neden**i açıklamak, **ne**yi değil.
`i++; /* i'yi bir artir */` gibi bir yorum zaman kaybıdır; ama
`/* once GIC etkinlesmeli, yoksa TTC interrupt'i hic gelmez */` gibi bir
yorum, bir sonraki kişiyi (altı ay sonra o kişi büyük ihtimalle sensin)
saatler sürecek bir yeniden keşiften kurtarır. Görev 10'un acı dersi
burada yeniden karşına çıkıyor: yanıltıcı ya da eksik yorum, hiç yorum
olmamasından daha tehlikelidir — "bu bayrağı ana döngü okuyor" diyen
satırın `volatile`'ı unutmuş olabileceğini hiçbir yorum söyleyemez.

## Sürüm kontrolünün temelleri

Git iş akışının inceliklerini burada yeniden öğretecek değiliz —
üniversiteden zaten biliyorsun — ama iki alışkanlığın gömülü işlerde
ağırlığı özellikle büyüktür:

- **Küçük branch, küçük değişiklik.** Bir branch ne kadar uzun yaşarsa
  ana kod tabanından o kadar uzaklaşır ve eninde sonunda gelecek merge o
  kadar sancılı olur. Bir çevre birimi sürücüsü, bir hata düzeltmesi —
  her biri kendi branch'inde, tek başına review edilebilecek boyutta
  kalmalı.
- **Anlamlı commit mesajı.** "fix", "wip", "asdf" gibi mesajlar, altı ay
  sonra `git log`a bakan kişiye (sen dahil) hiçbir şey söylemez.
  "TTC0 interrupt maskesi düzeltildi: yanlış bit sayısı frekansı iki
  katına çıkarıyordu" gibi bir mesaj hem o anki niyetini kayda geçirir
  hem de aynı hatayı arayan bir sonraki kişiye doğrudan cevap verir.

:::ekip-notu Bozuk build asla push edilmez
Ekibimizde pazarlığı olmayan tek kural şudur: push ettiğin branch build
olmak zorundadır. "Sonra düzeltirim" niyetiyle bırakılan bozuk build, o
branch'i çeken herkese birer kayıp gün olarak yansır. Push etmeden önce
yerel build'ini bir kez daha çalıştır. Görev 10'daki gibi "build oluyor
ama doğru çalışmıyor" ayrı ve daha hafif bir kategoridir — ama "build
olmuyor" hiçbir zaman kabul edilmez.
:::

## Kodu review'a sunmak

Kodun review'a hazır olması "bitti, gönderdim"den fazlasıdır. Şu üç
adımı atlama:

- **Küçük PR (pull request) hazırla.** 800 satırlık bir değişikliği
  kimse gerçekten review edemez; şöyle bir bakılır, onaylanır ve hatalar
  aradan sızar. Tek bir amaca hizmet eden 100-200 satırlık bir PR hem
  senin hem review eden için daha hızlı ve daha güvenlidir.
- **Önce kendi kodunu kendin review et.** PR'ı açmadan önce diff'i baştan
  sona kendin gez. Unutulmuş bir `xil_printf` satırı, yorum içinde
  bırakılmış test kodu, yanlış yazılmış bir tanımlayıcı — bunları kendin
  yakalarsan, review eden kişi zamanını asıl önemli olan mantığa harcar.
- **Ekip stiline uy.** Bölüm 5'te tanıtılan Hungarian notation,
  `module_object_action()` adlandırması ve Allman braces süs değildir;
  tüm kod tabanını tek bir gözlükle okunur tutan bir sözleşmedir. Stile
  uymayan PR, mantığı doğru olsa bile "önce stili düzelt" diye geri döner.

:::ekip-notu Review'dan ne beklenir, ne beklenmez
Ekibimizde review'ın amacı kodu güçlendirmektir, yazanı küçültmek değil.
Yorum almak savunmaya geçme sebebi değildir — "bunu neden böyle yaptın"
sorusu çoğu zaman gerçek bir meraktır, suçlama değil. Aynısı review eden
taraf için de geçerli: "bu satır saçma" demek yerine "bu satır neden
burada" diye sor. Teknik tartışma sert olabilir; kişisel olamaz.
:::

## Datasheet ve user guide okuma stratejisi

Görev 6'da bunu bizzat yaşadın: onlarca sayfalık bir dokümanın karşısında
nereden başlayacağını bilmek başlı başına bir beceridir. Üstelik gömülü
işlerde tek doküman nadiren yeter — bu yolculuk boyunca üç kaynaklı bir
üçgenle çalıştın: **UG1271** kartın kendisini anlatır (hangi cihaz hangi
pine bağlı), **UG1085** çipin içini anlatır (register haritaları,
interrupt numaraları, bellek adresleri), cihazın kendi datasheet'i
(örneğin INA226'nınki) o cihazın kendi register setini anlatır. Bir
sorunun cevabı nadiren üçünden yalnız birinde bulunur — çoğu zaman
ikisinin kesişimindedir: "bu I2C adresi hangi cihaza atanmış" sorusunun
cevabı kart dokümanında, "bu register ne anlama geliyor" sorusunun
cevabı cihaz datasheet'indedir.

Doküman hangisi olursa olsun okuma sırası değişmez:

1. **İçindekiler tablosuyla başla.** Tek satır gövde metni okumadan önce
   register haritasının hangi bölümde, elektriksel karakteristiklerin
   hangi bölümde, zamanlama diyagramlarının hangi bölümde olduğunu tespit
   et.
2. **Register özetine atla.** Çoğu datasheet ve user guide bir "register
   summary" ya da "memory map" tablosu içerir; bu tablo dokümanın geri
   kalanının haritasıdır.
3. **Gövde metnine yalnızca tablo yetmediğinde dön.** Bir alanın anlamını
   tablo tek başına açıklamıyorsa (örneğin bir bitin hangi koşulda
   anlamlı olduğunu), ilgili paragrafa git — dokümanı baştan sona okumaya
   kalkma; bunu gerçekte kimse yapmaz.

:::saha-notu Asıl bilgi tablo dipnotlarında saklanır
Register tablosunun altındaki küçük puntolu dipnotları atlama alışkanlığı
bu mesleğin en pahalı tuzaklarından biridir. "Bu bit yalnızca X modu
etkinken geçerlidir" ya da "reset değeri revizyona göre değişir" gibi
cümleler tam olarak o dipnotlarda durur. Bir değer beklenmedik
davrandığında ilk bakılacak yer ana tablo değil, dipnottur.
:::

## Soru sorma sanatı: "ne denedin" şablonu

Bölüm 0'da yardım istemenin zayıflık olmadığını söylemiştik; ama nasıl
sorduğun da önemlidir. "Çalışmıyor, yardım eder misin" cümlesi karşı
tarafı sıfırdan başlamaya ve senin zaten yaptığın işi tekrarlamaya
zorlar. Bunun yerine dört parçalı bir şablon kullan:

- **Belirti:** Tam olarak ne gözlemliyorsun? ("UART'ta bir şey
  görünmüyor" değil; "terminal açık, baud hızı doğru, ama kart
  açıldığından beri tek karakter gelmedi.")
- **Beklenen:** Ne olmasını bekliyordun?
- **Denemeler:** Hangi ihtimalleri şimdiden eledin? (Kabloyu değiştirdin
  mi, başka bir port denedin mi, debugger'da PC'nin `main()`'e ulaştığını
  doğruladın mı?)
- **Hipotez:** Bir tahminin varsa, sorunun nerede olduğundan
  şüpheleniyorsun?

:::ekip-notu "Ne denedin"e hazır gel
Ekibimizde bir soruya "ne denedin" diye karşılık vermek standart
uygulamadır — seni sınamak için değil, aynı aramayı iki kez yapmamak
için. Yukarıdaki dört parçası hazır gelen bir soru, genellikle beşinci
dakikada değil ikinci dakikada cevap bulur; çünkü karşı taraf henüz
bakmadığın yeri hemen görür.
:::

Bu alışkanlıklar bir günde yerleşmez; ama artık adlarını bildiğine göre
onları fark etmeye başlayacaksın — hem kendi kodunda hem ekip
arkadaşlarının kodunda. Bu yolculuğun teknik çekirdeği burada bitiyor;
son durak, bu dokümanın kapsamı dışında kalan ama adıyla mutlaka
karşılaşacağın kavramların kısa bir turu.
