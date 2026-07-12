# Bölüm 7 — ARP: İki Dünyanın Köprüsü

Elinde bir çelişki birikti: stack, paketi IP adresine göre yönlendiriyor
(Bölüm 5-6); ama kabloya çıkan frame'in hedefi bir MAC adresi (Bölüm 3).
"192.168.1.130'a göndereceğim" kararı ile "d8:3a:dd:... MAC'ine frame yaz"
eylemi arasındaki boşluğu kim dolduruyor? Cevap: **ARP (Address Resolution
Protocol — adres çözümleme protokolü)**. Küçük, yaşlı ve zarif bir
protokoldür; ağ arızalarını teşhis ederken en çok işine yarayacak
protokollerden biridir, çünkü "L2 ile L3 birbirini görüyor mu" sorusunun
turnusoludur.

## Request ve reply: bağıran soru, fısıldanan cevap

ARP'ın tüm hayatı iki mesajdır. Bir hedefin IP'sini bilip MAC'ini
bilmiyorsan:

1. **ARP request** — segmente **broadcast** atarsın:
   *"Who has 192.168.1.130? Tell 192.168.1.20."* Broadcast olmak
   zorundadır: MAC'ini bilmediğin birine unicast gönderemezsin; tavuk-yumurta
   problemi broadcast'le kırılır.
2. **ARP reply** — yalnızca IP'nin sahibi cevap verir, bu kez **unicast**:
   *"192.168.1.130 is at d8:3a:dd:4f:a2:1c."* Diğer herkes soruyu duyar ve
   sessizce çöpe atar.

{{svg:sema-10-arp-sequence.svg|ARP alışverişi: soru broadcast'tir, segmentteki herkes duyar; cevap unicast'tir, yalnız sorana döner. Öğrenilen eşleme ARP cache'e yazılır ve sonraki paketler için soru tekrarlanmaz.}}

Her paket için bu tören dönmesin diye sonuç **ARP cache**'e (tablo)
yazılır ve bir süre — işletim sistemine göre saniyelerle dakikalar arası —
oradan kullanılır. Tabloyu görmek için:

```text
Windows:  arp -a
Linux:    ip neigh        (eski araç: arp -a)
```

## Gateway senaryosu: ARP kimin için sorulur?

Kritik incelik: ARP **yalnızca yerel adresler için** çalışır. Uzak bir
IP'yi asla ARP'lamazsın — o soru cevapsız kalırdı, çünkü broadcast router'ı
geçemez ve uzak makine seni duyamaz. Bölüm 5'in "yerel mi uzak mı" kararı
tam burada ete kemiğe bürünür: stack, paket *uzaksa* ARP'a "gateway'in
IP'sinin MAC'i ne?" diye sorar; *yerelse* hedefin kendisini sorar.

{{svg:sema-11-arp-gateway.svg|Aynı ARP tablosu, iki farklı gönderim: yerel hedefin frame'i kendi MAC'ine, uzak hedefin frame'i gateway'in MAC'ine yazılır. Uzak IP hiçbir zaman ARP'lanmaz.}}

Bölüm 6'daki gözlemin mekanizması da böylece tamamlandı: internete giden
bütün frame'lerin hedef MAC'i aynı, çünkü hepsi için ARP'a sorulan tek
soru "192.168.1.1 kimde?" idi.

## Gratuitous ARP: sorulmadan verilen cevap

Bir cihaz, kimse sormadığı halde kendi IP'si için ARP mesajı yayınlarsa
buna **gratuitous ARP** (karşılıksız ARP) denir. İki meşru kullanımı var:

- **Duyuru:** cihaz ağa yeni katıldığında ya da IP/MAC'i değiştiğinde
  "ben buradayım, tablolarınızı güncelleyin" der. Switch'ler de bu frame'den
  MAC öğrenir — Bölüm 4'teki "sessiz kart" sorununun ilacı.
- **Çakışma tespiti:** cihaz kendi almak istediği IP'yi sorar; cevap
  gelirse o IP'yi başkası kullanıyordur ("duplicate IP" tespiti).

Gömülü stack'lerde (lwIP dahil) arayüz ayağa kalkarken bir gratuitous ARP
atmak görgü kuralıdır; çoğu stack bunu kendiliğinden yapar.

:::saha-notu Wireshark'ta ilk ARP çiftini yakala
Wireshark'ı aç, display filter kutusuna `arp` yaz, sonra karta ping at.
Cache'i temizlersen (`arp -d *` — Windows'ta yönetici konsolu; Linux'ta
`ip neigh flush all`) töreni baştan izlersin: önce
`Who has ...? Tell ...` broadcast'i, hemen ardından `... is at ...`
cevabı. Bu çifti görmek, L2'nin sağlıklı olduğunun en net kanıtıdır.
**Cevap yoksa** teşhis de nettir: hedef kapalı, yanlış subnet'te, başka
VLAN'da ya da kablo/switch yolunda sorun var — ve ping'le uğraşmaya gerek
kalmadan sorunun L2/L3 sınırında olduğunu biliyorsun. "Kart ping atmıyor"
vakasında ilk bakılacak şey ARP'a cevap verip vermediğidir (Bölüm 14 ve 16).
:::

:::tuzak Bayat ARP kaydı: IP aynı, MAC eski
Kartı yenisiyle değiştirdin, aynı IP'yi verdin, "bağlanamıyorum". Sebep
çoğu zaman PC'nin ARP cache'inde eski kartın MAC'inin oturmasıdır: frame'ler
artık var olmayan bir MAC'e gidiyor. Çözüm: `arp -d` ile kaydı sil ya da
birkaç dakika bekle. Tersi de olur: iki cihaza yanlışlıkla aynı IP verilmişse
(duplicate IP) ARP cevapları yarışır, bağlantı "bir çalışıp bir kopan"
kararsız bir hale girer — Windows bu durumda "IP address conflict" uyarısı
basar, gömülü kart basmaz; şüphede `arp -a` çıktısındaki MAC'in *beklediğin
cihaza* ait olduğunu OUI'den doğrula.
:::

:::analoji Kalabalık salonda isim bağırmak
ARP request, kalabalık bir salonda "Ayşe Yılmaz kim?!" diye bağırmaktır —
herkes duyar (broadcast), yalnız Ayşe elini kaldırır (unicast reply). Sen
de not defterine "Ayşe = mavi kazaklı, pencere kenarı" yazarsın (cache).
Defterdeki not eskiyebilir: Ayşe yer değiştirmişse (MAC değişti) yanlış
kişiye mektup uzatırsın — bayat cache tam olarak budur.
:::

:::derin-dalis ARP'ın güvenlik zaafı: spoofing
ARP'ta kimlik doğrulama yoktur: kim "192.168.1.1 benim MAC'imde" derse
tablolar ona inanır — en son konuşan kazanır. **ARP spoofing/poisoning**
saldırısı budur: saldırgan, kurbanın cache'ine kendini gateway diye
yazdırır; kurbanın tüm dış trafiği saldırganın üstünden akar
(man-in-the-middle). Aynı teknik ağı "dinlenebilir" yapmak için iki yönlü
uygulanır. Savunma tarafında kurumsal switch'lerde *dynamic ARP
inspection* gibi özellikler, uçlarda statik ARP kayıtları ve en önemlisi
üst katman şifrelemesi (TLS — Bölüm 11) vardır: TLS varken trafiğin
yönünü çalmak içeriğini çalmaya yetmez. Bu bilgiyi kendi ağını korumak ve
Wireshark'ta "aynı IP için iki farklı MAC cevap veriyor" anomalisini
tanımak için taşı.
:::

:::ozet
- ARP, IP dünyası ile MAC dünyası arasındaki köprüdür: "bu IP kimde?"
  sorusunu broadcast'le sorar, unicast cevap alır, sonucu cache'ler.
- ARP yalnızca yerel adresler için sorulur; uzak hedefte sorulan soru
  gateway'in MAC'idir.
- Gratuitous ARP: sorulmadan yapılan duyuru — yeni cihaz kendini tanıtır,
  IP çakışması tespit edilir.
- `arp -a` / `ip neigh` tabloyu gösterir; bayat kayıt ve duplicate IP,
  klasik "hayalet" arızalardır.
- ARP'a cevap alabilmek, L2 sağlığının turnusoludur; teşhiste ping'den
  önce gelir.
:::
