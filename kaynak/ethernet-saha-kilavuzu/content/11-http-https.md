# Bölüm 11 — HTTP ve HTTPS

Taşıma katmanı byte'ları güvenle taşıyor; sıra o byte'ların *anlamında*.
Uygulama katmanının kralı **HTTP**'dir (Hypertext Transfer Protocol) —
yalnızca web sayfaları değil: REST API'ler, firmware güncelleme
servisleri, kartının kendi web arayüzü, hatta çoğu IoT bulut trafiği HTTP
konuşur. Üstüne **TLS** gelince HTTPS olur. İkisini de okuyabilir hale
geleceksin.

## HTTP: düz metin soru-cevap

HTTP, TCP bağlantısı (genellikle port 80) üzerinde akan, insan gözüyle
okunabilir bir istek/yanıt protokolüdür. İstek üç parçadır: **istek
satırı** (metot + yol + sürüm), **header'lar** (üstbilgiler) ve isteğe
bağlı **gövde** (body):

```http
GET /api/status HTTP/1.1
Host: 192.168.1.130
User-Agent: python-requests/2.31
Accept: application/json
                                   ← boş satır: header bitti
```

Cevap da aynı iskelet: **durum satırı** + header'lar + gövde:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 38

{"uptime": 4211, "temp_c": 47.2}
```

Ezber gerektiren iki küçük tablo:

| Metot | Anlamı |
|---|---|
| `GET` | oku — gövdesiz istek, yan etkisiz olmalı |
| `POST` | yeni veri gönder / işlem tetikle |
| `PUT` | değiştir/yerine koy |
| `DELETE` | sil |

| Kod | Sınıf | Sahada en sık |
|---|---|---|
| 2xx | başarı | `200 OK`, `204 No Content` |
| 3xx | yönlendirme | `301/302` (taşındı), `304` (cache'ten kullan) |
| 4xx | **istemci** hatası | `400` bozuk istek, `401/403` yetki, `404` yok |
| 5xx | **sunucu** hatası | `500` iç hata, `502/504` arka uç ulaşılamıyor |

4xx/5xx ayrımı teşhis yönünü belirler: 4xx "isteğini düzelt", 5xx
"karşı taraf hasta" der. `Host` header'ı da göründüğünden önemlidir: aynı
IP'de onlarca site barınabilir (virtual hosting); sunucu hangi siteyi
istediğini bu header'dan anlar.

:::saha-notu Tarayıcı yerine curl ile konuş
Kartın HTTP servisini test ederken tarayıcının cache'i ve otomatik
yönlendirmeleri gözünü boyar. `curl -v http://192.168.1.130/api/status`
(Windows 10+ dahil) ham alışverişi gösterir: `>` ile giden satırlar,
`<` ile gelenler. `-v` çıktısında TCP bağlantısının kurulduğunu, isteği
ve durum kodunu tek bakışta görürsün. Wireshark tarafında karşılığı:
display filter `http` — port 80 düz metin olduğu için istek/yanıt satırları
capture'da aynen okunur.
:::

## TLS: üç iş birden

Düz HTTP'nin sorunu ortada: yol üstündeki herkes — aynı broadcast
domain'deki meraklı, ISS, ARP spoofing yapan saldırgan (Bölüm 7) — her
şeyi okuyabilir ve değiştirebilir. **TLS** (Transport Layer Security),
TCP ile uygulama arasına giren ve üç şeyi birden sağlayan katmandır:

1. **Şifreleme** — içerik yolda okunamaz.
2. **Bütünlük** — içerik yolda *fark edilmeden* değiştirilemez.
3. **Kimlik** — karşındaki sunucu, iddia ettiği sunucudur (sertifika).

{{svg:sema-18-tls.svg|Basitleştirilmiş TLS el sıkışması: taraflar yetenek listelerini değişir, sunucu sertifikasını sunar, istemci zinciri doğrular, anahtar anlaşmasıyla iki taraf aynı simetrik anahtarı türetir. Sonrası şifreli tüneldir — HTTP o tünelin içinde, değişmeden akar.}}

Sezgisel akış şu: pahalı **asimetrik** kriptografi (public/private key)
yalnızca el sıkışmada, kimlik ve anahtar anlaşması için kullanılır;
sonrasında trafik, o anda türetilen **simetrik** anahtarla şifrelenir —
hızlıdır. "HTTPS yavaştır" efsanesinin gerçek payı sadece el sıkışmanın
1-2 gidiş-dönüşüdür; kurulan bağlantı üzerinde fark ihmal edilebilir.

**Sertifika zinciri** de sezgisel anlatılabilir: sunucunun sertifikası
"ben example.com'um, public key'im bu" der ve bir **CA** (Certificate
Authority — sertifika otoritesi) tarafından imzalanmıştır; o CA'nın
sertifikası da bir üst CA tarafından... Zincir, işletim sistemine/
tarayıcıya fabrikadan gömülü **güvenilen kökler** listesindeki bir
sertifikada bitmek zorundadır. Tarayıcının "bağlantınız gizli değil"
uyarısı, zincirin köke bağlanamadığı (self-signed — kendinden imzalı),
ismin uyuşmadığı ya da tarihin geçtiği durumdur. Kartının web arayüzü
self-signed sertifika kullanıyorsa bu uyarı *beklenen* davranıştır —
zincir yok, kimlik kanıtlanamıyor; şifreleme yine de kurulur.

HTTPS varsayılan **port 443**'te akar. Wireshark'ta `tls` filtresiyle el
sıkışmasını (ClientHello içindeki sunucu adı — SNI — dahil) görürsün ama
sonrası `Application Data`: anlamsız byte'lar. "HTTPS trafiğinin *içini*
Wireshark'la okuyayım" beklentisi, tasarım gereği boşa çıkar.

:::tuzak "Kart HTTPS konuşsun" demeden önce
Gömülü web arayüzünü HTTPS'e taşımak üç yük getirir: TLS kütüphanesi
(mbedTLS gibi — kod + RAM), el sıkışmanın hesap yükü (küçük MCU'da
saniyeler sürebilir) ve sertifika yönetimi (kim imzalayacak, nasıl
yenilenecek?). Kapalı lab ağındaki bir test kartı için düz HTTP çoğu zaman
doğru mühendislik kararıdır; internete/kurum ağına açılan üründe ise TLS
pazarlık konusu değildir. Karar bilinçli olsun; "443 daha profesyonel
görünüyor" gerekçe değildir.
:::

:::analoji Noter tasdikli kilitli çanta
TLS'siz HTTP, kartpostalın arkasına yazılmış yazışmadır — taşıyan herkes
okur. TLS, yazışmayı kilitli çantaya koyar (şifreleme), çantaya mühür
vurur (bütünlük — mühür kırılmışsa anlarsın) ve teslimatçının kimliğini
noter zinciriyle doğrular (sertifika → CA → güvenilen kök). Çantanın
içindeki mektubun dili (HTTP) hiç değişmez; sadece artık kimse okuyamaz.
:::

:::derin-dalis HTTP/1.1 → 2 → 3: aynı anlam, değişen taşıma
HTTP'nin *anlamı* (metotlar, kodlar, header'lar) 30 yıldır aynı; değişen,
byte'ların hatta nasıl dizildiği. **HTTP/1.1** düz metindir ve bir TCP
bağlantısında aynı anda tek istek yürür — tarayıcılar bu yüzden 6'şar
bağlantı açardı. **HTTP/2** (2015) tek bağlantıda çok isteği çerçeveleyip
paralel akıtır (multiplexing), header'ları sıkıştırır; ama TCP üstünde
olduğu için tek kayıp paket *bütün* akışları bekletir (Bölüm 9'daki
head-of-line blocking, bağlantı seviyesinde geri döner). **HTTP/3**
(2022) bu yüzden TCP'yi bırakır: **QUIC** üzerinde, o da **UDP** üzerinde
çalışır. QUIC; TCP'nin güvenilirliğini ve TLS 1.3'ü UDP üstünde, akış
başına bağımsız olarak yeniden kurar — bir akışın kaybı diğerlerini
bekletmez, el sıkışma tek gidiş-dönüşe iner. Wireshark'ta `quic`
filtresiyle 443/UDP trafiği olarak görürsün. Ders: Bölüm 9'daki "TCP mi
UDP mi" takası o kadar gerçek ki, web'in kendisi UDP'ye taşındı —
güvenilirliği uygulama katmanında kendisi inşa ederek.
:::

:::ozet
- HTTP: TCP/80 üstünde okunabilir istek/yanıt; metot + yol + header'lar +
  gövde; durum kodları 4xx "sen", 5xx "sunucu" der.
- `curl -v`, HTTP teşhisinin temel aletidir; Wireshark'ta düz HTTP aynen
  okunur.
- TLS üç iş yapar: şifreleme, bütünlük, kimlik; pahalı asimetrik kripto
  yalnız el sıkışmada, sonrası hızlı simetrik şifre.
- Sertifika zinciri güvenilen kökte bitmelidir; self-signed = "şifreli ama
  kimliksiz" — tarayıcı uyarısı normaldir.
- HTTPS = TLS tüneli içinde değişmemiş HTTP; port 443; Wireshark içeriği
  göremez.
- Evrim: HTTP/2 çoklama getirdi, HTTP/3 QUIC/UDP'ye geçti — taşıma
  takasları gerçek.
:::
