# Bölüm 12 — Meslek Kültürü: İyi Gömülü Yazılımcı

Görev 10'da dört hatayı avladın; bu bölümde görev kartı yok, çünkü
anlatacağımız şey bir laboratuvarda tek seferde öğrenilen bir beceri değil,
her gün biraz daha oturan bir alışkanlık. İyi bir gömülü yazılımcıyı iyi
yapan şey yalnızca doğru çalışan kod değil; kodun etrafındaki disiplin —
savunmacı yazmak, okunaklı bırakmak, ekiple doğru konuşmak.

## Savunmacı programlama: her şey yolunda gitmeyebilir varsayımı

Masaüstü kodunda bir fonksiyon başarısız olursa exception fırlatır, birileri
yakalar, hayat devam eder. Gömülüde çoğu zaman o "birileri" yoktur — sen
kontrol etmezsen kimse etmez. Üç alışkanlık bunun temelini oluşturur:

- **Dönüş değerini kontrol et.** `_stil.md`'nin de vurguladığı gibi bizim
  kodumuzda `XST_SUCCESS` kalıbı bir süs değil, bir kuraldır: bir sürücü
  fonksiyonu bir hata kodu döndürüyorsa, o değeri okumadan bir sonraki
  satıra geçmek, "muhtemelen iyi gitmiştir" kumarına girmektir. Bir I2C
  yazmacı okunamadıysa bunu bilmeden üzerine bir hesap kurman, yanlış bir
  sıcaklık değerini doğruymuş gibi UART'a basmandan çok daha kötüdür.
- **`assert` ile varsayımlarını görünür kıl.** Bir fonksiyona gelen pointer'ın
  asla NULL olmayacağını mı düşünüyorsun? Yaz onu: `assert(pDurum != NULL);`.
  Assert, "burada bir varsayım var, kırılırsa hemen haber ver" demenin en
  ucuz yoludur; debug derlemesinde seni erken uyarır, release derlemesinde
  genelde devre dışı kalır (bu yüzden gerçek hata kontrolünün yerine
  geçmez, onun tamamlayıcısıdır).
- **Timeout'suz sonsuz bekleme yasak.** Görev 6'da INA226'dan yanıt beklerken
  bir `while` döngüsünü sonsuza kadar değil, bir deneme sınırı içinde
  çalıştırman istenmişti (istenmediyse şimdi ekle) — donanım cevap
  vermezse programın sonsuza kadar orada donması kabul edilemez. Aynı
  disiplin her donanım beklemesinde geçerli: "cevap gelene kadar bekle"
  değil, "N deneme ya da M milisaniye bekle, sonra hata döndür" yaz.

:::tuzak "Çalışıyor" ile "doğru" aynı şey değildir
Bir kere test edip çalıştığını görmek, kodun doğru olduğu anlamına gelmez —
yalnızca o an, o koşullarda çalıştığı anlamına gelir. Donanım cevap
vermediğinde, kablo gevşek geldiğinde, sıcaklık sensörü beklenmedik bir
değer bastığında ne olacağını düşünmeden bırakılan kod, sahada er ya da geç
bu senaryolardan biriyle karşılaşır.
:::

## Kod okunabilirliği ve yorum kültürü

Kodun kendisi *ne* yaptığını zaten söylüyor — satırı okuyan biri değişkenin
ne olduğunu, döngünün kaç kere döndüğünü görebilir. Yorumun işi başka: **NE**
değil **NEDEN**i anlatmak. `i++; /* i'yi bir artır */` gibi bir yorum
zaman kaybıdır; ama `/* GIC önce enable edilmeli, yoksa TTC kesmesi hiç
gelmiyor */` gibi bir yorum, bir sonraki kişiyi (ki bu kişi altı ay sonraki
sen olabilirsin) saatler süren bir tekrar-keşiften kurtarır. Görev 10'un
sana öğrettiği acı ders tam burada tekrar karşına çıkıyor: yanıltıcı ya da
eksik bir yorum, hiç yorum olmamasından daha tehlikelidir — "bayrağı ana
döngü okuyor" yazan bir satırın `volatile` unutmuş olabileceğini kimse
yorumdan anlayamaz.

## Versiyon kontrol temelleri

Git akışının inceliklerini burada tekrar öğretmeyeceğiz — üniversiteden
aşinasındır — ama gömülü dünyada iki alışkanlık özellikle önem kazanır:

- **Küçük dallar (branch), küçük değişiklikler.** Bir dalın ömrü ne kadar
  uzarsa, ana koddan o kadar uzaklaşır ve birleştirmesi (merge) o kadar
  acı verir. Bir çevre birimi driver'ı, bir bug düzeltmesi — her biri kendi
  dalında, kendi başına gözden geçirilebilir boyutta kalsın.
- **Anlamlı commit mesajları.** "fix", "wip", "asdf" gibi mesajlar altı ay
  sonra `git log`'a bakan hiç kimseye (senin dahil) bir şey anlatmaz.
  "TTC0 kesme maskesini düzelt: yanlış bit sayacı 2× hızlandırıyordu" gibi
  bir mesaj, hem o anki niyetini kaydeder hem de gelecekte aynı hatayı
  arayan birine doğrudan cevap verir.

:::ekip-notu Derlenmeyen kod push edilmez
Bizim ekipte tek katı kural şu: push ettiğin dal derlenir. "Sonra
düzeltirim" diye bırakılan kırık bir derleme, senden sonra o dalı çeken
herkesin günü çalınır demektir. Push etmeden önce en azından yerel
derlemeni bir kere daha çalıştır; Görev 10'daki gibi "derleniyor ama
çalışmıyor" bambaşka bir kategoridir ve o kadar vahim değildir — ama
"derlenmiyor" hiç kabul edilmez.
:::

## Code review'a kod gönderme

Kodun review'a hazır olması, "bitti, gönderdim" demek değildir. Üç adımı
atlama:

- **Küçük PR (pull request) hazırla.** 800 satırlık bir değişikliği kimse
  gerçek anlamda inceleyemez; göz gezdirip onaylar, hata kaçar. 100-200
  satırlık, tek bir amaca hizmet eden bir PR hem senin için hem
  incelen kişi için daha hızlı ve daha güvenlidir.
- **Kendi kodunu önce sen incele.** PR'ı açmadan diff'e kendi gözünle bak;
  unutulmuş bir `xil_printf` satırı, yorum satırına alınmış bir test kodu,
  isim yazım hatası — bunları sen bulursan, incelemeyi yapan arkadaşın
  zamanı asıl mantık hatalarına gider.
- **Ekip stiline uy.** Bölüm 5'te tanıştığın Hungarian notation, `modul_
  nesne_eylem()` isimlendirmesi ve Allman parantezleri süs değil; ekibin
  tüm kod tabanını tek bir gözle okunabilir tutan bir sözleşmedir. Stile
  uymayan bir PR, mantığı doğru olsa bile "önce stili düzelt" yorumuyla
  geri döner.

:::ekip-notu Review'da ne bekleriz, ne beklemeyiz
Bizim ekipte review'un işi seni küçük düşürmek değil, kodu sağlamlaştırmak.
Bir yorum aldığında savunmaya geçmene gerek yok — "neden böyle yaptın"
sorusu çoğu zaman gerçekten meraktır, suçlama değil. Aynı şekilde sen
review yaparken de üslubuna dikkat et: "bu satır neden burada?" diye sor,
"bu satır saçma" deme. Teknik tartışma sert olabilir, kişisel olmasın.
:::

## Datasheet ve user guide okuma stratejisi

Görev 6'da bunu bir kere yaşadın: elinde onlarca sayfalık bir belge varken
nereden başlayacağını bilmek başlı başına bir beceridir. Üstelik gömülüde
tek bir doküman nadiren yeter — bu yolculukta üç köşeli bir üçgenle
çalıştın: **UG1271** kartın kendisini anlatır (hangi cihaz hangi pine
bağlı), **UG1085** çipin içini anlatır (register haritaları, kesme
numaraları, bellek adresleri), **cihazın kendi datasheet'i** (örneğin
INA226'nınki) o cihazın kendi register setini anlatır. Sorun genelde
üçünden birinde değil, ikisinin kesişiminde çözülür — "bu I2C adresi hangi
cihaza gidiyor" sorusunun cevabı kart dokümanında, "bu register ne anlama
geliyor" sorusunun cevabı cihaz datasheet'inde.

Hangi belge olursa olsun, okuma sırası aynı kalır:

1. **Önce içindekiler.** Belgenin hangi bölümünde register haritası,
   hangisinde elektriksel özellikler, hangisinde zamanlama diyagramları var
   — bunu bulmadan tek satır okumaya başlama.
2. **Register özetine atla.** Çoğu datasheet ve user guide'ın bir "register
   summary" ya da "memory map" tablosu vardır; bu tablo, dokümanın geri
   kalanına giden bir haritadır.
3. **Metne yalnızca tablo yetmediğinde dön.** Bir alanın anlamını tablo tek
   başına açıklamıyorsa (örneğin bir bitin hangi koşulda anlamlı olduğu),
   ilgili paragrafa git — dokümanın tamamını baştan sona okumaya çalışma,
   kimse öyle okumaz.

:::saha-notu Tablo dipnotları asıl hazinedir
Bir register tablosunun altındaki küçük punto dipnotları atlama alışkanlığı,
bu meslekte seni en çok yakan tuzaklardan biridir. "Bu bit yalnızca X modu
aktifken geçerlidir" ya da "reset değeri revizyona göre değişir" gibi
cümleler, tam da o dipnotlarda saklanır. Bir değeri beklenmedik bulduğunda
ilk bakılacak yer ana tablo değil, dipnottur.
:::

## Soru sorma sanatı: "ne denedin" şablonu

Bölüm 0'da "sormak zayıflık değil" demiştik; ama nasıl sorduğun da önemli.
"Çalışmıyor, yardım edin" cümlesi karşındaki kişiyi sıfırdan başlatır ve
senin zaten yaptığın işi tekrar ettirir. Bunun yerine dört parçalı bir
şablon kullan:

- **Belirti:** Ne gözlemliyorsun, tam olarak? ("UART'ta hiçbir şey
  görünmüyor" değil, "terminal açık, baud doğru, ama karta güç verdiğimden
  beri hiç karakter gelmedi".)
- **Beklenen:** Ne olmasını bekliyordun?
- **Denenenler:** Hangi ihtimalleri eledin? (Kabloyu değiştirdin mi, farklı
  bir port denedin mi, debugger'da PC'nin `main()`'e ulaştığını gördün mü?)
- **Hipotez:** Sence sorun nerede olabilir, varsa?

:::ekip-notu "Ne denedin" sorusuna hazır gel
Bizim ekipte bir soruya "ne denedin" diye karşılık vermek standarttır —
bu seni sınamak için değil, aynı arayışı iki kere yapmamak için. Yukarıdaki
dört parçayı önceden hazırlayarak gelen bir soru, genelde beşinci dakikada
değil ikinci dakikada cevabını bulur; çünkü karşındaki kişi nereye
bakılmadığını hemen görür.
:::

Bu alışkanlıklar bir günde oturmaz; ama şimdi adlarını bildiğine göre onları
fark etmeye başlayacaksın — kendi kodunda da, ekip arkadaşlarının kodunda
da. Yolculuğun teknik gövdesi burada tamamlanıyor; son durak, bu dokümana
sığmayan ama adını duyacağın kavramların kısa bir ufuk turu.
