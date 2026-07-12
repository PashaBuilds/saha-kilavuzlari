# Bölüm 13 — Sentez: Bir URL'nin Uçtan Uca Yolculuğu

Adres çubuğuna `https://example.com` yazıp Enter'a bastın. Sayfa yüz
milisaniye sonra ekranda. O yüz milisaniyede, bu kılavuzun on iki bölümde
tek tek kurduğu her mekanizma sırayla sahneye çıkıp işini yaptı. Bu bölüm
o sahneyi baştan sona, tek seferde oynatıyor. Kılavuzu buraya atlayarak
geldiysen de okuyabilirsin: her adımda kavramın bir cümlelik özeti ve
derinleşmek istersen bölüm numarası var.

Sahneyi zorlaştıralım ki her mekanizma görünsün: makine ağa yeni katıldı —
DNS cache boş, ARP cache boş, sunucuyla açık bağlantı yok. Her şey
sıfırdan.

{{svg:sema-23-buyuk-final.svg|Büyük resim: tek zaman çizgisinde beş faz. ARP kapıyı bulur (altın), DNS ismi adrese çevirir (mavi), TCP güvenilir hattı kurar (yeşil), TLS tüneli mühürler (mavi), HTTP asıl işi yapar (yeşil). Sağdaki katman etiketleri, her fazın hangi katta oynadığını söylüyor.}}

## Faz 0 — Daha hiçbir paket yokken

Tarayıcı URL'yi ayrıştırır: şema `https` → hedef port **443**; host
`example.com` → bir IP lazım. Ama önce eldekiler yoklanır: tarayıcının ve
işletim sisteminin **DNS cache**'i (Bölüm 10), `hosts` dosyası. Boş.
Demek ki ilk iş isim çözmek — DNS sunucusuna bir paket gerekiyor.

Stack, DNS sunucusunun adresine (diyelim `8.8.8.8`) bakar ve Bölüm 5'in
kararını verir: kendi adresi `192.168.1.20/24`, hedef `8.8.8.8` —
maskeyle AND'le, karşılaştır: **uzak**. Uzak hedefin kuralını Bölüm 6'dan
biliyorsun: paketi **default gateway**'e (`192.168.1.1`) teslim et. Frame
yazılacak; ama gateway'in **MAC adresi** bilinmiyor. ARP cache de boş.

Zincirin ilk halkası böyle belirlenir: kabloya çıkacak ilk paket, DNS
değil, **ARP**'tır.

## Faz 1 — ARP: kapıyı bulmak (Bölüm 7)

Makine broadcast bağırır: *"Who has 192.168.1.1?"* — hedef MAC
`FF:FF:FF:FF:FF:FF`, segmentteki herkes duyar (Bölüm 3-4: switch
broadcast'i her porta taşırır). Yalnız router elini kaldırır, unicast
cevap verir: *"is at 44:d9:e7:0a:71:5e."* Eşleme ARP cache'e yazılır.
Artık dış dünyaya giden her frame'in üstüne yazılacak adres belli.

Bu töreni bir kez yaptık; bundan sonraki *bütün* dış paketler — DNS'e,
sunucuya, nereye giderse gitsin — aynı MAC'e, gateway'e teslim edilecek.

## Faz 2 — DNS: ismi adrese çevirmek (Bölüm 10)

Şimdi asıl soru: `example.com` kim? Makine, resolver'a **UDP port 53**
üzerinden tek soruluk bir paket atar. Paketin kimlik bilgileri, kılavuzun
en önemli ayrımını sergiler:

- **Hedef IP:** `8.8.8.8` — nihai hedef, yol boyunca değişmez.
- **Hedef MAC:** gateway'inki — yalnız bu segmentte geçerli ilk durak.

Neden UDP? Soru-cevap tek paketlik iş; el sıkışma masrafına değmez,
kaybolursa soruyu tekrarlamak ucuz (Bölüm 9'un takası). Resolver —
cache'inde yoksa — root → TLD → authoritative zincirini yürütür ve cevap
döner: `example.com = 93.184.216.34`, yanında TTL. Cevap cache'lenir;
bir sonraki ziyaret bu fazı hiç görmeyecek.

## Faz 3 — TCP: güvenilir hattı kurmak (Bölüm 9)

Tarayıcı `connect()` çağırır: hedef `93.184.216.34:443`. Üçlü el sıkışma
döner: **SYN** → **SYN+ACK** → **ACK**. İki taraf sıra numaralarında
anlaşır; soket dörtlüsü — `(192.168.1.20:52814 ↔ 93.184.216.34:443)` —
artık canlı bir bağlantıyı adresliyor. Bundan sonra hangi byte kaybolursa
kaybolsun, TCP sayacak, ACK'layacak, gerekirse yeniden gönderecek.

Yolda iki şey daha oldu, ikisi de görünmez ama Bölüm 6 ve 12'den
biliyorsun: evin router'ı NAT yaptı — paketin kaynak adresi
`85.102.7.44:40001`'e çevrildi, eşleme tabloya yazıldı; ve her router
atlamasında IP paketi aynı kalırken frame söküldü, yeni segmentin
MAC'leriyle yeniden sarıldı. İstanbul'dan çıkan IP paketi, sunucuya kadar
belki on beş kez "zarf değiştirdi".

## Faz 4 — TLS: tüneli mühürlemek (Bölüm 11)

Şema `https` idi; düz konuşmak yok. TCP hattının üstünde TLS el sıkışması
döner: **ClientHello** (yeteneklerim + rastgelem) → **ServerHello +
sertifika**. Tarayıcı sertifika zincirini güvenilen köke kadar doğrular —
isim `example.com` mu, tarih geçerli mi, imzalar sağlam mı. Sonra anahtar
anlaşması: iki taraf, kablodan hiç geçmeyen ortak bir **simetrik anahtar**
türetir. Tünel kuruldu: bu noktadan sonra yol üstündeki hiç kimse — ISS,
meraklı komşu, ARP spoofing'çi — içeriği okuyamaz, fark edilmeden
değiştiremez.

## Faz 5 — HTTP: asıl işi yapmak (Bölüm 11)

Ve nihayet, bütün bu altyapının uğruna kurulduğu tek cümle:

```http
GET / HTTP/1.1
Host: example.com
```

Sunucu `200 OK` ve HTML'i döner. Sayfa MTU'ya sığmaz elbette (Bölüm 3):
TCP onu 1500'er byte'lık segmentlere böler, numaralar, akıtır; kaybolan
olursa sessizce tamamlar. Tarayıcı HTML'i ayrıştırırken CSS, script,
görsel için yeni istekler doğar — ama artık her şey sıcak: DNS cache dolu,
ARP cache dolu, TCP+TLS bağlantısı açık ve yeniden kullanılıyor. İlk
yolculuğun yüz milisaniyesi, sonraki isteklerde onda birine iner.

## Aynı sahne, katman gözlüğüyle

Yolculuğu bir de Bölüm 1'in şemasına yaslayıp özetleyelim — her faz hangi
katmanın oyunuydu:

| Faz | Protokol | Katman | Cevapladığı soru |
|---|---|---|---|
| 1 | ARP | L2 köprüsü | "Bu segmentte kapı hangi MAC?" |
| 2 | DNS | L7 (UDP/53 üstünde) | "Bu ismin IP'si ne?" |
| 3 | TCP | L4 | "Byte'lar eksiksiz ve sıralı aksın" |
| 4 | TLS | L4 ile L7 arası | "Kimse okuyamasın, karşım gerçek olsun" |
| 5 | HTTP | L7 | "Sayfayı ver" |

Ve alttan alta, her pakette: IP (L3) yön buldu, Ethernet (L2) segment
segment taşıdı, fiziksel katman (L1) bitleri kabloya döktü. Hiçbir katman
diğerinin işine karışmadı; hepsi sadece kendi header'ını okudu. Bölüm 1'de
"katmanlar karmaşayı böler" demiştik — işte bölünmüş hali.

:::saha-notu Bu bölümü Wireshark'ta kendin oynat
Capture'ı başlat, `arp or dns or tcp.port == 443` display filter'ını yaz,
cache'leri temizle (`ipconfig /flushdns` + `arp -d *`) ve tarayıcıdan daha
önce girmediğin bir siteye git. Beş fazı — ARP çifti, DNS soru/cevabı,
SYN/SYN+ACK/ACK, ClientHello/sertifika, ardından okunamayan `Application
Data` — kendi capture'ında, bu şemadaki sırayla göreceksin. Bu on dakikalık
deney, on üç bölümlük kılavuzun en kalıcı dersidir.
:::

:::tuzak "Sayfa açılmıyor"un beş ayrı hastalığı
Bu zincirin değeri arızada belli olur: hangi faz kırıldıysa belirti
farklıdır. ARP kırıksa gateway'e bile çıkamazsın (yerel ağ arızası); DNS
kırıksa "sunucu bulunamadı" (ama `ping 8.8.8.8` çalışır); TCP kırıksa
bekleyip "bağlanılamadı" (SYN'e cevap yok — hedef ya da firewall); TLS
kırıksa "bağlantınız gizli değil" (sertifika); HTTP kırıksa sunucudan
4xx/5xx kodu gelir (karşı taraf konuşuyor ama derdi var). "Açılmıyor"
diyen kullanıcıdan bu ayrımı sökmek, teşhisin yarısıdır — gerisi
Bölüm 16'nın ağacı.
:::

:::ozet
- Sıfırdan ilk sayfa: ARP (kapının MAC'i) → DNS (ismin IP'si) → TCP
  (güvenilir hat) → TLS (mühürlü tünel) → HTTP (asıl iş).
- İlk kabloya çıkan paket ARP'tır — DNS bile ondan önce kapı adresi ister.
- Yol boyunca IP adresleri sabit kaldı; MAC'ler her segmentte, kaynak
  adres NAT'ta değişti.
- UDP tek paketlik soruya (DNS), TCP eksiksizlik isteyen akışa (HTTP)
  seçildi — Bölüm 9'un takası canlı örnekte.
- Cache'ler (ARP, DNS, TCP+TLS oturumu) ikinci ziyareti uçurur; ilk
  ziyaret her zaman en pahalısıdır.
- Hangi faz kırıksa belirti farklı: bu zinciri bilen, "açılmıyor"u beş
  ayrı arızaya ayrıştırır.
:::
