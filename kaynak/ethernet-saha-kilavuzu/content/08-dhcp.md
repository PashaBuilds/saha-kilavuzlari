# Bölüm 8 — DHCP: Adresler Nereden Geliyor

Telefonunu ofisin Wi-Fi'sine tutuyorsun, saniyeler içinde internettesin.
IP'sini kim verdi? Maskeyi, gateway'i, DNS sunucusunu kim söyledi? Cevap
**DHCP** (Dynamic Host Configuration Protocol). Kısa bir bölüm; ama gömülü
tarafta "statik mi DHCP mi" kararını bilinçli vermek ve `169.254.x.x`
işaretini okumak için gereken her şey burada.

## DORA: dört adımlı el sıkışma

Ağa katılan cihazın IP'si yoktur; o yüzden konuşma broadcast'le başlamak
zorundadır (kime unicast atacaksın?). Akış, mesajların baş harfleriyle
**DORA** diye anılır:

{{svg:sema-12-dhcp-dora.svg|DORA akışı: istemci Discover ile broadcast bağırır, sunucu Offer ile adres önerir, istemci Request ile teklifi resmen ister, sunucu ACK ile kirayı onaylar. Offer paketi IP'yle birlikte maske, gateway ve DNS'i de taşır.}}

İki ayrıntı önemli. Birincisi, DHCP yalnızca IP vermez: **maske, gateway,
DNS sunucusu** ve daha onlarca seçenek aynı pakette gelir — Bölüm 5-6'da
elle girdiğimiz her şey. İkincisi, adres *verilmez*, **kiralanır** (lease):
süre dolmadan cihaz sessizce yenileme ister; yenileyemezse adresi bırakmak
zorundadır. Kesintisiz çalışan cihazlarda "gece yarısı IP değişti, bağlantı
koptu" hikâyelerinin kökü genellikle başarısız lease yenilemesidir.

DHCP broadcast'e dayandığı için **yalnızca kendi broadcast domain'inde**
çalışır (Bölüm 4'ün sınırı). Router'ın arkasındaki başka bir subnet'e DHCP
hizmeti vermek için router'da *DHCP relay* kurulur — kurumsal ağda her
VLAN'ın DHCP'sinin ayrı ayarlanmasının sebebi bu.

## Statik mi, DHCP mi?

| | DHCP | Statik IP |
|---|---|---|
| Kurulum | sıfır — tak, çalışsın | elle, cihaz başına |
| Adres öngörülebilir mi | hayır (rezervasyon yoksa) | evet, hep aynı |
| Sunucuya bağımlılık | var — sunucu yoksa adres yok | yok |
| Uygun yer | dizüstü, telefon, misafir cihaz | sunucu, yazıcı, **gömülü kart** |

Gömülü kartlarda ibre çoğu zaman statikten yanadır, üç sebeple:

1. **Öngörülebilirlik:** karta bağlanan yazılıma, test scriptine, tarayıcı
   yer imine sabit bir adres lazım; "bugün .57, yarın .63" olmaz.
2. **Bağımsızlık:** lab tezgâhında, doğrudan PC'ye bağlı (switch'siz)
   senaryoda DHCP sunucusu yoktur; kart statikse hemen konuşur.
3. **Determinizm:** açılışta DORA beklemek, timeout'lara düşmek, testi
   geciktirir; kritik sistemde açılış süresine belirsizlik sokar.

Orta yol da var: **DHCP reservation** (rezervasyon) — sunucuya "bu MAC
her zaman bu IP'yi alsın" kuralı girilir. Cihaz DHCP'nin konforunu, sen
statiğin öngörülebilirliğini alırsın; kurumsal ağda IT'den isteyeceğin şey
tam olarak budur.

:::saha-notu Kiralamayı elle tazelemek
Ağ değiştirdin, kablo taktın ama adres eskisi gibi mi görünüyor?
Windows'ta `ipconfig /release` + `ipconfig /renew`, Linux'ta
`sudo dhclient -r` + `sudo dhclient` (ya da masaüstünde arayüzü kapat-aç)
DORA'yı baştan koşturur. Wireshark'ta `dhcp` (eski sürümde `bootp`)
filtresiyle dört mesajı canlı izleyebilirsin — Offer içinde gateway ve
DNS'in de geldiğini kendi gözünle gör.
:::

:::tuzak 169.254.x.x: "adres aldım" sanma
`ipconfig` çıktısında `169.254.b.c` görüyorsan cihaz DHCP'den cevap
**alamamış** ve kendine rastgele bir link-local adres uydurmuş demektir
(APIPA). Bu adresle yalnız aynı segmentteki benzer kaderdeki cihazlarla
konuşabilirsin; gateway'in, internetin yoktur. Teşhis olarak değerlidir:
"kablo/link tamam ama DHCP sunucusuna ulaşamadım" der — kablo kopuğuysa
link zaten olmazdı; bu daha çok yanlış VLAN, kapalı DHCP servisi ya da
sunucusuz tezgâh ağı işaretidir. Bir de tersi tuzak: lab'a kendi "yardımcı"
DHCP'siyle gelen bir cihaz (hotspot modunda kalmış telefon, yanlış
konfigüre AP) ağa ikinci bir DHCP sunucusu sokarsa, cihazlar hangi
Offer önce gelirse onu alır — kimin hangi gateway'le kaldığı belli olmayan
kaotik bir ağ doğar. Kurumsal switch'lerdeki *DHCP snooping* özelliği tam
bu kazayı engellemek içindir.
:::

:::ozet
- DHCP; IP + maske + gateway + DNS'i tek pakette dağıtır; akış DORA'dır:
  Discover → Offer → Request → ACK.
- Adres kiralanır (lease); yenilenemeyen kira düşer, adres değişebilir.
- Broadcast'e dayanır → yalnız kendi broadcast domain'inde çalışır;
  subnet'ler arası için relay gerekir.
- Gömülü kartta tercih: statik IP ya da MAC'e bağlı DHCP rezervasyonu.
- `169.254.x.x` = "DHCP'den alamadım" itirafı; iki DHCP sunuculu ağ kaos
  üretir.
:::
