# Bölüm 10 — DNS: İnternetin Rehberi

Şu ana dek hedefleri hep IP ile andık; ama kimse tarayıcıya
`142.250.187.110` yazmaz, `google.com` yazar. İsimleri adreslere çeviren
sistem **DNS**'tir (Domain Name System) — ve ağ arızalarının şaşırtıcı bir
bölümünün gerçek faili odur: "internet gitti" diye başlayan vakaların
hatırı sayılır kısmı "internet duruyor, DNS cevap vermiyor" çıkar.

## Hiyerarşi: kimse her şeyi bilmez

DNS, tek bir dev rehber değil, dağıtık bir hiyerarşidir. `www.example.com`
adı sağdan sola okunur: kök (`.`) → `com` → `example` → `www`. Her seviyeyi
başka sunucular bilir: **root** sunucular yalnızca ".com'u kimlere
soracağını" bilir; **TLD** (top-level domain) sunucuları
"example.com'un sahibinin sunucusunu" bilir; **authoritative** (yetkili)
sunucu — alan adının sahibinin sunucusu — asıl cevabı verir.

Senin makinen bu zinciri kendisi yürümez; işi **resolver**'a (özyineli
çözücü — ISS'in, kurumun ya da 8.8.8.8 / 1.1.1.1 gibi kamusal bir hizmetin
sunucusu) havale eder:

{{svg:sema-17-dns-hiyerarsi.svg|Cache'lerin hepsi boşken tam çözümleme zinciri: makinen resolver'a tek soru sorar (3); resolver root → TLD → authoritative sırasını yürür (4–7) ve cevabı TTL etiketiyle döndürür (8). Cevap yol boyunca her katta cache'lenir.}}

Cevapla birlikte bir **TTL** (time to live — saniye cinsinden geçerlilik
süresi) gelir: cevap o süre boyunca resolver'da ve senin makinende
**cache**'lenir. DNS'in dünyayı kaldırabilmesinin sırrı budur: soruların
ezici çoğunluğu daha ilk iki adımda, cache'ten döner. Yan etkisi de budur:
bir kayıt değiştiğinde eski cevap, TTL dolana kadar dünyanın
cache'lerinde yaşamaya devam eder.

## Kayıt türleri: rehberdeki sütunlar

DNS'te bir isim tek bir "değer" değil, türlü kayıtlar (resource records)
taşır:

| Tür | Anlamı | Örnek |
|---|---|---|
| `A` | isim → IPv4 | `example.com → 93.184.216.34` |
| `AAAA` | isim → IPv6 | `example.com → 2606:2800:...` |
| `CNAME` | isim → başka isim (takma ad) | `www → example.com` |
| `MX` | bu alanın postasını kim alır | `→ mail.example.com` |
| `TXT` | serbest metin (doğrulama, SPF...) | `"v=spf1 ..."` |

Günlük hayatta %90 `A` kaydıyla uğraşırsın. `CNAME` zincirini bilmek
Wireshark/nslookup çıktısı okurken işe yarar: soru `www.example.com` iken
cevapta önce CNAME, sonra asıl ismin A kaydı görünür.

## hosts dosyası: DNS'ten önceki son söz

Stack, DNS'e sormadan önce yerel **hosts** dosyasına bakar:

```text
Windows:  C:\Windows\System32\drivers\etc\hosts
Linux:    /etc/hosts

# satır formatı:  IP  isim
192.168.1.130   fpga-kart
```

Bu satırı ekledikten sonra `ping fpga-kart` ve `http://fpga-kart` çalışır —
DNS sunucusuna hiç sorulmadan. Lab tezgâhında karta isim vermenin en ucuz
yolu budur. Madalyonun öbür yüzü: hosts'ta unutulan bayat bir satır, "bu
makine neden herkesten farklı yere gidiyor" tipinde, aklına en son gelecek
arızayı üretir.

## Sorgu araçları: nslookup ve dig

```text
Windows / Linux:  nslookup example.com
Linux (zengin):   dig example.com A

> nslookup example.com
Server:   192.168.1.1          ← cevabı VEREN resolver
Address:  192.168.1.1#53

Non-authoritative answer:      ← cevap cache'ten (yetkiliden değil)
Name:     example.com
Address:  93.184.216.34
```

Çıktının ilk iki satırını okumayı alışkanlık yap: *hangi* sunucu cevap
vermiş? Beklediğin resolver değilse (örn. VPN'in DNS'i devreye girmişse)
arızanın adresi değişti demektir. Belirli bir sunucuya sormak için:
`nslookup example.com 8.8.8.8` — kurum DNS'i ile kamusal DNS'in cevabını
karşılaştırmak, "sorun bizim resolver'da mı" sorusunu tek komutla çözer.

DNS taşımada genellikle **UDP port 53** kullanır (Bölüm 9'daki desene
uyar: küçük soru, küçük cevap, kayıpta sorunun tekrarı ucuz); büyük
cevaplar ve bölge transferleri TCP 53'e düşer.

:::saha-notu "It's always DNS"
Ağcıların yarı şaka yarı gerçek atasözü. Belirti deseni şudur:
`ping 8.8.8.8` **çalışıyor** ama `ping google.com`
"could not find host" diyor → yönlendirme ve internet sağlam, isim
çözümleme ölü. Kontrol sırası: `nslookup google.com` kime soruyor →
`ipconfig /all` içinde DNS sunucusu doğru mu → `nslookup google.com
8.8.8.8` ile kamusal DNS'ten cevap alınıyor mu? Cache şüphesinde:
Windows `ipconfig /flushdns`, Linux (systemd)
`resolvectl flush-caches`. Bölüm 16'daki karar ağacında bu dal aynen var.
:::

:::analoji Rehber, santral ve not defteri
DNS bir telefon rehberi zinciridir: cebindeki not defteri (hosts + OS
cache), aramadan önce baktığın yerdir; şirket santrali (resolver) senin
adına rehberleri arar; il rehberi (TLD) ve firmanın kendi santrali
(authoritative) doğru numarayı verir. Numara değişmişse ama sen not
defterindeki eskisini aramaya devam ediyorsan — TTL dolmamış cache tam
olarak budur.
:::

:::derin-dalis Gömülü kart DNS'siz yaşar — peki mDNS ne?
Gömülü sistemlerin çoğu DNS'e hiç bulaşmaz: hedefler statik IP'dir,
konfigürasyonda yazılıdır. lwIP'te DNS istemcisi vardır ama ancak sen
`LWIP_DNS` ile derlersen ve resolver adresi verirsen çalışır — "kart NTP
sunucusunun *ismini* çözemiyor" arızası genellikle bu eksikliktir; çare ya
DNS'i açmak ya konfigürasyona IP yazmaktır. Bir de **mDNS** (multicast
DNS) var: `raspberrypi.local` gibi `.local` isimleri, sunucusuz, yerel
segmentte multicast soruyla çözülür (Bonjour/Avahi). Lab'da isimle erişim
konforu sağlar; ama multicast'e ve aynı segmentte olmaya bağımlıdır —
kurumsal ağda VLAN sınırında sessizce ölür. `.local` çalışmıyorsa bu
yüzden şaşırma; gerçek DNS kaydı ya da hosts satırı her zaman daha
öngörülebilirdir.
:::

:::ozet
- DNS dağıtık hiyerarşidir: root → TLD → authoritative; senin makinen
  yalnız resolver'la konuşur.
- Cevaplar TTL süresince her katta cache'lenir — hız da bayatlık da
  buradan gelir.
- Kayıt türleri: A (IPv4), AAAA (IPv6), CNAME (takma ad), MX (posta),
  TXT (metin).
- hosts dosyası DNS'ten önce okunur: lab'da isimlendirme aracı,
  unutulunca arıza kaynağı.
- `nslookup`/`dig` ile kimin cevap verdiğini gör; `ping 8.8.8.8` çalışıp
  `ping google.com` çalışmıyorsa fail DNS'tir.
- DNS çoğunlukla UDP 53 üzerinden akar; gömülü kartta DNS genellikle
  kapalıdır — isim yerine IP konuş.
:::
