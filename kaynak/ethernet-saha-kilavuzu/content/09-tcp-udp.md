# Bölüm 9 — Taşıma Katmanı: TCP ve UDP

IP, paketi doğru *makineye* ulaştırır — ama makinede onlarca program
çalışıyor. Paket SSH oturumuna mı, web sunucusuna mı, senin telemetri
uygulamana mı? Bu son adres adımı ve "veri kaybolursa ne olacak" sorusunun
tamamı **taşıma katmanının** işidir. Buradaki iki oyuncu — TCP ve UDP —
senin `socket()` çağrının arkasındaki dünyadır; gömülü yazılımcının en çok
kod yazdığı katman burasıdır.

## Port ve soket: son kapı numarası

**Port**, 16 bitlik bir sayıdır (0–65535): makinenin *içindeki* uygulamayı
seçer. IP binayı bulur, port daireyi. Sunucu uygulama bir portu **dinler**
(listen); istemci ise işletim sisteminin o an tahsis ettiği rastgele bir
**ephemeral** (geçici) porttan bağlanır.

{{svg:sema-13-port-soket.svg|Tek IP, çok uygulama: kartın her servisi ayrı bir port dinler. Bağlantının kimliği dört değerin birleşimidir — kaynak IP:port ↔ hedef IP:port. Stack, gelen her segmenti bu dörtlüyle doğru sokete eşler.}}

Bir bağlantıyı benzersiz kılan şey **soket dörtlüsüdür**: (kaynak IP,
kaynak port, hedef IP, hedef port). Bu yüzden aynı karta aynı 5001
portuna iki farklı PC'den (hatta aynı PC'den iki farklı ephemeral portla)
aynı anda bağlanılabilir — dörtlüler farklıdır, karışmaz.

Bazı portlar gelenekle sahiplidir (**well-known ports**, 0–1023) —
ezberlemen gerekenler bir avuçtur:

| Port | Protokol | İş |
|---|---|---|
| 22 | TCP | SSH (uzak konsol, scp) |
| 53 | UDP+TCP | DNS |
| 67/68 | UDP | DHCP (sunucu/istemci) |
| 80 | TCP | HTTP |
| 123 | UDP | NTP (zaman) |
| 443 | TCP | HTTPS |
| 502 | TCP | Modbus/TCP (endüstriyel) |

Kendi uygulamana port seçerken 1024–49151 arasından, o makinede boş bir
numara seç; 49152 üstü ephemeral bölgesidir, sunucu portu olarak kullanma.

:::tuzak "Port" kelimesinin iki hayatı
Switch'in fiziksel **port**u (kablonun takıldığı delik) ile TCP/UDP
**port**u (16 bitlik yazılım kapısı) yalnızca isim akrabasıdır. "Kartın
portu kapalı" cümlesi iki ayrı arıza olabilir: switch portu (link yok,
L1) ya da TCP portu (dinleyen uygulama yok, L4). Hangisinden bahsettiğini
hep netleştir — teşhis yolları tamamen farklıdır.
:::

## TCP: güvenilir akış

**TCP (Transmission Control Protocol)**, iki uygulama arasında **güvenilir,
sıralı bir byte akışı** sunar: sen `send()` ile ne döktüysen, karşı taraf
`recv()` ile aynı sırayla, eksiksiz alır. Kablo bunu vaat etmiyordu —
frame'ler kaybolur (FCS bozuğu sessizce atılıyordu, hatırla), sıralar
karışabilir. TCP bu vaadi üç mekanizmayla *inşa eder*: numaralandır,
onayla, tekrarla.

{{svg:sema-14-tcp-handshake.svg|TCP'nin yaşam döngüsü: SYN / SYN+ACK / ACK üçlü el sıkışmasıyla iki taraf sıra numaralarında anlaşır; veri byte byte sayılır ve ACK'lanır; FIN'lerle iki yön ayrı ayrı kapanır. RST ise tek paketlik acil kesmedir.}}

- **El sıkışma (SYN → SYN+ACK → ACK):** taraflar bağlantı durumunu kurar
  ve başlangıç **sequence number**'larında (sıra numarası) anlaşır.
  `connect()` çağrın dönene kadar olan şey tam olarak budur.
- **Sequence/ACK:** her byte numaralıdır. Alıcı, "şu numaraya kadar hepsi
  bende" diyen kümülatif **ACK**'lar yollar. Gönderen, ACK'lanmayan veriyi
  zamanlayıcı dolunca ya da tekrarlanan ACK görünce **yeniden gönderir**
  (retransmit).
- **Flow control (akış kontrolü):** alıcı, header'daki **window** alanıyla
  "tamponumda şu kadar yer var" der; gönderen bundan fazlasını havada
  tutmaz. Yavaş gömülü kart, hızlı PC'yi böyle frenler — `recv()` çağırmayı
  bırakırsan window sıfıra düşer ve karşı taraf durur. "Veri gelmiyor"
  değil, "sen almıyorsun" durumu.
- **Congestion control (tıkanıklık kontrolü):** gönderen, *ağı* boğmamak
  için de kendini frenler: yavaş başlar (slow start), kayıp gördükçe hızını
  kısar. Sezgisel düzeyde bil: TCP'nin hızı sabit değildir, ağın haline
  göre nefes alır.
- **Kapanış:** her yön bağımsız olarak **FIN** ile kapanır. **RST** ise
  kaba kesiştir: kapalı porta bağlanınca aldığın "connection refused",
  karşıdan gelen bir RST'dir — ve teşhiste değerlidir: RST geliyorsa makine
  *ayakta*, sadece o portu kimse dinlemiyor.

## UDP: zarif minimalizm

**UDP (User Datagram Protocol)** ise taşıma katmanının "çıplak" hali:
porta adresleme + checksum. Hepsi bu. Bağlantı yok, el sıkışma yok, ACK
yok, sıra yok. `sendto()` dersin, datagram gider — ulaşırsa ulaşır.

{{svg:sema-15-tcp-udp-header.svg|İki header yan yana: TCP'nin 20 byte'ındaki her alan bir mekanizmanın (sıralama, onay, akış kontrolü) karşılığıdır; UDP'nin 8 byte'ı yalnızca "hangi uygulamaya" sorusunu cevaplar.}}

UDP'nin değeri tam da bu yokluklardadır: state (durum) tutulmaz — RAM'i
kısıtlı gömülü stack için hafiftir; zamanlama *öngörülebilirdir* — arka
planda kimse senin adına yeniden gönderim yapmaz; broadcast/multicast
yapabilir — TCP yapamaz (bağlantı "herkesle" kurulamaz; DHCP'nin UDP
olması tesadüf değil).

## Kayıp paket günü: iki dünya

Farkı en net, bir şeyler ters gittiğinde görürsün:

{{svg:sema-16-kayip-paket.svg|Aynı kayıp, iki felsefe: TCP deliği yeniden gönderimle kapatır ama sonraki veriyi bekletir — veri tam, zamanlama değişken. UDP deliği umursamaz — veri delik, zamanlama sabit. Hangisinin "doğru" olduğunu uygulaman belirler.}}

Bu şemadaki bedel takası, gömülü telemetri tasarımının kalbidir. Kartından
saniyede 10.000 ölçüm akıtıyorsun:

- **TCP ile:** hiçbir ölçüm kaybolmaz; ama tek bir kayıp frame, arkasından
  gelen *sağlam* verinin de uygulamaya teslimatını retransmit süresince
  bekletir (head-of-line blocking). Grafikte takılma, gecikmede zıplama
  (**jitter**) görürsün. Dosya, konfigürasyon, komut — "eksiksiz olsun"
  dediğin her şey için doğru seçim yine TCP'dir.
- **UDP ile:** her datagram bağımsızdır; kayıp olan ölçüm gider, sonrakiler
  zamanında gelir. Canlı izlemede 10.000'de 3 örneğin kaybı çoğu zaman
  hiçtir — ama bunu *sen* karar verebilesin diye datagram'a uygulama
  seviyesinde bir sıra numarası koy: delikleri say, raporla, gerekirse
  telafiyi kendi kurallarınla yap.

Kaba kural: **komut/kontrol ve dosya → TCP; yüksek oranlı canlı veri ve
keşif/yayın → UDP.** Endüstride de desen budur: Modbus/TCP komut taşır,
ses/görüntü akışları (RTP) UDP'ye biner.

:::saha-notu Kim hangi portu dinliyor?
"Bağlanamıyorum" dediğinde önce dinleyen var mı bak: Windows'ta
`netstat -ano` (PID ile birlikte; PID'i Görev Yöneticisi'nde bul),
Linux'ta `ss -tlnp`. `LISTENING 0.0.0.0:5001` satırı yoksa sunucun ya hiç
başlamamış ya sadece `127.0.0.1`'i dinliyordur — dışarıdan gelen bağlantı
`127.0.0.1`'e bağlanamaz; sunucu soketini `0.0.0.0`'a (tüm arabirimler)
bind et. Hızlı port testi için: `telnet 192.168.1.130 5001` — bağlanırsa
port açık, "refused" ise makine var ama dinleyen yok, timeout ise araya
firewall girmiş ya da makineye ulaşılamıyor demektir (Bölüm 16'da tablo var).
:::

:::analoji Telefon ve kartpostal
TCP telefon görüşmesidir: önce karşı taraf açar ("alo" = el sıkışma),
konuşurken "hı hı" onayları akar, anlaşılmayan cümle tekrar edilir ve
kapanırken vedalaşılır. UDP kartpostaldır: yazar atarsın; ulaşıp
ulaşmadığını, hangi sırayla ulaştığını posta idaresi umursamaz. Acil tek
cümlelik haberler için kartpostal hem ucuz hem hızlıdır; sözleşme
imzalatacaksan telefonda hecelet, teyit al.
:::

:::derin-dalis Nagle, ACK gecikmesi ve "neden 200 ms?"
Küçük komut paketleri gönderen TCP uygulamalarında klasik bir sürpriz:
tek tek `send()` edilen küçük mesajlar karşıya ~40–200 ms gecikmeyle
ulaşır. İki iyi niyetli mekanizma çakışıyordur: **Nagle algoritması**
(gönderen, ACK gelmeden ikinci küçük paketi yollamayıp biriktirir — ağı
minik paketle doldurmamak için) ve **delayed ACK** (alıcı, ACK'ı hemen
değil kısa bir süre bekleyip yollar — ACK'ı veriye bindirebilmek için).
İkisi birleşince kilitlenirler: gönderen ACK bekler, alıcı ACK'ı bekletir.
Etkileşimli, gecikmeye duyarlı protokollerde çare soket seçeneğidir:
`TCP_NODELAY` (Nagle'ı kapatır). Python'da:
`sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)`. Toplu veri
aktarımında ise Nagle'a dokunma; işini iyi yapıyor.
:::

:::ozet
- Port, makine içindeki uygulamayı seçer; bağlantının kimliği soket
  dörtlüsüdür (IP:port ↔ IP:port).
- TCP: el sıkışma + sequence/ACK + retransmit + flow/congestion control =
  güvenilir, sıralı byte akışı. RST = "makine ayakta, port kapalı" sinyali.
- UDP: port + checksum, başka hiçbir şey; hafif, öngörülebilir,
  broadcast/multicast yapabilir.
- Kayıpta TCP veriyi tamamlar ama bekletir (jitter); UDP delik bırakır ama
  zamanında akar — telemetride UDP + uygulama sıra numarası klasik desendir.
- Komut/dosya → TCP; yüksek oranlı canlı akış → UDP.
- `netstat -ano` / `ss -tlnp` dinleyenleri gösterir; `0.0.0.0` bind'ını
  unutma.
:::
