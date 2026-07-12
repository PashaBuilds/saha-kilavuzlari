# Bölüm 4 — Ağ Cihazları: Hub, Switch, Router

Kablolar tek başına ağ yapmaz; onları birleştiren kutular yapar. Bu üç
kutunun — hub, switch, router — farkını katman diliyle söyleyebilmek,
"trafiğim nereden akıyor, kim neyi görüyor" sorularının anahtarıdır. Bölümün
sonunda cebinde tek cümle kalacak: **switch MAC konuşur, router IP konuşur.**

## Aynı topoloji, üç farklı kutu

Dört cihazı aynı kutuya bağlayalım ve A'dan C'ye bir frame gönderelim.
Kutunun türüne göre olan biten kökten değişir:

{{svg:sema-06-hub-switch-router.svg|Aynı yıldız topolojide üç kutu: hub frame'i körlemesine herkese kopyalar; switch MAC tablosuna bakıp yalnızca hedef porta iletir; router iki ayrı IP ağını birbirine bağlar ve broadcast'i sınırda durdurur.}}

**Hub**, fiziksel katman (L1) cihazıdır — aslında elektrikli bir çoklayıcı.
Bir porttan gelen sinyali *anlamadan* diğer bütün portlara kopyalar. Frame,
MAC, adres... hiçbirinden haberi yoktur. Sonuç: aynı anda iki cihaz konuşursa
sinyaller çarpışır (**collision**). Hub'lı ağda herkes tek **collision
domain** (çarpışma alanı) paylaşır; bant genişliği ortaktır ve cihaz sayısı
arttıkça verim erir. Half-duplex ve CSMA/CD (çarpışma algılayıp bekleyerek
yeniden deneme) o dünyanın icadıdır. Hub bugün ölü bir türdür; anlatıyoruz
çünkü collision domain kavramını ve eski dokümanlardaki half-duplex
mirasını açıklıyor.

**Switch**, veri bağı katmanı (L2) cihazıdır. Frame'i alır, **hedef MAC'e
bakar** ve yalnızca doğru porta iletir. Her port kendi collision domain'idir;
her bağlantı full-duplex çalışır; A↔C konuşurken B↔D tam hızda ayrıca
konuşabilir. Modern LAN'ın omurgası budur.

**Router (yönlendirici)**, ağ katmanı (L3) cihazıdır. Frame'in *içini* açar,
IP paketini çıkarır, **hedef IP'ye bakar** ve paketi başka bir ağa doğru
yeni bir frame'e sararak yollar (Bölüm 6'nın konusu). Router'ın her bacağı
ayrı bir IP ağıdır.

## Broadcast domain: görünmez sınır

Bölüm 3'te broadcast frame'i görmüştük: hedefi `FF:FF:FF:FF:FF:FF` olan,
herkese giden frame. Switch, broadcast'i tanım gereği bütün portlara
kopyalar — hedef "herkes" ise davranış budur. Yani switch'ler collision
domain'i böler ama **broadcast domain'i bölmez**: birbirine bağlı
switch'lerden oluşan bütün ağ, tek bir broadcast alanıdır.

Broadcast'i durduran kutu **router'dır**. Broadcast bir L2 kavramıdır;
router L3'te çalıştığı ve paketi yeni bir frame'e sardığı için broadcast
onun sınırından geçemez. Bu, tasarımın kendisidir: dünyadaki her ARP
sorgusu her cihaza ulaşsaydı internet broadcast gürültüsünden çökerdi.

Pratik sonuç: "broadcast domain" ≈ "senin subnet'in" (Bölüm 5). ARP ve
DHCP gibi broadcast'e dayanan protokoller yalnızca kendi broadcast
domain'inde çalışır — DHCP sunucusunun neden her VLAN'da ayrı ayarlandığı,
kartını neden sunucuyla *aynı* subnet'e takınca hayatın kolaylaştığı
buradan çıkar.

## Switch nasıl öğrenir?

Switch'e kimse "A cihazı 1. portta" diye tablo girmez; kendisi öğrenir.
Mekanizma zarif ve basittir — üç kare izleyelim:

{{svg:sema-07-mac-ogrenme.svg|Switch'in MAC öğrenmesi üç karede: (1) A'dan gelen frame'in kaynak MAC'i tabloya işlenir ama hedef B bilinmediği için frame A hariç her porta taşırılır (flood); (2) B'nin cevabı geldiğinde B de öğrenilir ve cevap yalnızca A'nın portuna gider; (3) tablo dolu, trafik artık nokta atışı.}}

Kural iki cümledir:

1. **Kaynaktan öğren:** her gelen frame'in *kaynak* MAC'ini, geldiği port
   ile birlikte tabloya yaz.
2. **Hedefe göre ilet:** hedef MAC tablodaysa yalnız o porta gönder;
   değilse (ya da broadcast ise) geldiği port hariç her porta **flood** et.

Tablodaki kayıtlar kalıcı değildir; belli bir süre (tipik 300 saniye) o
MAC'ten frame gelmezse kayıt silinir (aging). Sessiz duran bir cihaza
giden ilk frame bu yüzden yine flood edilir — arıza değil, tasarım.

:::saha-notu Sessiz gömülü kart, kör Wireshark
Switch nokta atışı ilettiği için, PC'ne Wireshark açıp "kartın trafiğini
izleyeyim" demek çoğu zaman boş liste getirir: o trafik senin portuna hiç
gelmiyor. İzlemek için üç meşru yol var: (1) yönetilebilir switch'te
**port mirroring / SPAN** (bir portun kopyasını senin portuna aynala),
(2) araya **network tap** ya da eski usul gerçek bir hub sokmak,
(3) en pratiği: capture'ı iletişimin ucundaki makinede almak. Bir de tersi
var: kartın hiç konuşmuyorsa switch onu öğrenemez; karttan tek bir
gratuitous ARP (Bölüm 7) attırmak hem switch tablosunu hem senin
Wireshark'ını canlandırır.
:::

:::tuzak "Ev router'ı" tek kutu, dört cihaz
Evdeki (ve çoğu lab'daki) "modem/router", içinde ayrı roller barındırır:
WAN tarafında router + NAT (Bölüm 12), LAN tarafında 4 portlu bir switch,
üstüne Wi-Fi erişim noktası ve genellikle DHCP/DNS sunucusu. LAN portları
arasındaki trafik router'a hiç uğramaz — onlar aynı switch'in portlarıdır.
"Router'ım LAN içi trafiği filtrelesin" beklentisi bu yüzden boşa çıkar;
LAN içi trafik L2'de akar.
:::

:::analoji Posta dağıtımının üç hali
Hub, apartman girişine bağırarak anons yapan kapıcıdır: mektup kime
geldiyse gelsin, herkes duyar. Switch, kutulara ayrılmış posta kutusu
panosudur: zarf yalnızca doğru kutuya girer — ve kapıcı hangi dairenin
hangi kutuyu kullandığını, kutulara atılan zarfların üstündeki gönderen
adresinden zamanla öğrenir. Router ise şehirlerarası postanedir: zarfı
alır, başka bir şehrin dağıtım ağına yeni torbayla teslim eder; apartman
içi anonslar (broadcast) şehir dışına asla çıkmaz.
:::

:::derin-dalis Yönetilebilir switch, STP ve LLDP
Lab'daki switch "unmanaged" (yönetilemez) ise takar unutursun. Kurumsal
switch'ler ise yönetilebilirdir: VLAN, port mirroring, hız sabitleme, port
güvenliği buradan ayarlanır. İki kavram daha duyacaksın: **STP** (Spanning
Tree Protocol), switch'ler arası kablolamada halka (loop) oluşursa ağın
broadcast fırtınasıyla kilitlenmesini önlemek için fazla bağlantıları
mantıksal olarak kapatır — iki switch'i yanlışlıkla iki kabloyla birbirine
bağladığında seni STP kurtarır (unmanaged switch'te kurtaramaz; ağ çöker,
bu gerçek ve klasik bir kaza senaryosudur). **LLDP** (Link Layer Discovery
Protocol) ise cihazların "ben kimim, hangi portumdasın" bilgisini komşuya
duyurduğu bir keşif protokolüdür; Wireshark'ta `lldp` filtresiyle, hangi
switch'in hangi portuna takılı olduğunu kablo izlemeden öğrenebilirsin.
:::

:::ozet
- Hub L1'dir: sinyali herkese kopyalar; tek collision domain — ölü teknoloji
  ama half-duplex mirasını açıklar.
- Switch L2'dir: kaynak MAC'ten öğrenir, hedef MAC'e göre iletir,
  bilinmeyene flood eder; her port ayrı collision domain'dir.
- Router L3'tür: IP'ye bakar, ağlar arası yönlendirir.
- Switch broadcast domain'i bölmez; router böler. Broadcast domain ≈ subnet.
- Cebe atılacak cümle: **switch MAC konuşur, router IP konuşur.**
:::
