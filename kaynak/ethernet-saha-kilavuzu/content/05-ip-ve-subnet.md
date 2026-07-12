# Bölüm 5 — IP, Subnet ve "Yerel mi Uzak mı" Kararı

Ethernet ve MAC, "aynı odadaki" cihazları konuşturur. Ama dünya tek bir oda
değildir; frame'in eninde sonunda başka ağlara uzanması gerekir. O iş, ağ
katmanının ve **IP**'nin (Internet Protocol) işidir. Bu bölümde IPv4
adresinin yapısını, subnet (alt ağ) kavramını ve ağ stack'inin her paket
gönderiminde verdiği en kritik kararı öğreneceksin: **hedef yerel mi,
uzak mı?** Bu karar, gömülü kartına neden bazen bağlanıp bazen
bağlanamadığının cevabıdır.

## IPv4 adresi: 32 bit, dört parça

IPv4 adresi 32 bittir ve okunabilirlik için 8'er bitlik dört parçaya
bölünüp noktayla yazılır (dotted decimal): `192.168.1.130`. Her parça
0–255 arasıdır — çünkü 8 bitin alabileceği değerler bunlardır. Adres,
MAC'ten farklı olarak *hiyerarşiktir*: bir kısmı **hangi ağda** olduğunu,
kalanı ağın **içindeki hangi host** (cihaz) olduğunu söyler. Posta koduna
benzer: `34710` İstanbul/Kadıköy'ü seçer, sokak+numara evi seçer. MAC ise
TC kimlik numarası gibidir: benzersizdir ama *nerede oturduğun hakkında
hiçbir şey söylemez*. Yönlendirme bu yüzden IP ile yapılır.

## Subnet mask: ağ/host sınırını çizen cetvel

Adresin neresi ağ, neresi host? Bunu **subnet mask** (alt ağ maskesi)
söyler: ağ kısmına denk gelen bitleri 1, host kısmını 0 olan 32 bitlik bir
şablon. `255.255.255.0`, "ilk 24 bit ağ, son 8 bit host" demektir. Aynı şey
**CIDR** (Classless Inter-Domain Routing) gösterimiyle `/24` diye yazılır —
baştaki 1 bitlerinin sayısı. `192.168.1.130/24` gördüğünde oku:
"192.168.1 ağındaki 130 numaralı host."

Stack, bir hedefe paket gönderirken şu işlemi yapar: kendi IP'sini ve hedef
IP'yi maskeyle bit bit **AND**'ler. İki sonuç aynıysa hedef **yerel**dir
(aynı subnet), farklıysa **uzak**tır:

{{svg:sema-08-subnet-and.svg|Subnet kararının mekaniği: IP ve maske bit düzeyinde AND'lenir, çıkan ağ adresi hedefinkiyle karşılaştırılır. Aynıysa hedef yereldir ve frame doğrudan ona gider; farklıysa frame gateway'e yollanır.}}

Bu kararın sonucu iki bambaşka davranıştır:

- **Yerel hedef:** "aynı odadayız" — ARP ile hedefin MAC'i bulunur
  (Bölüm 7), frame doğrudan ona gönderilir.
- **Uzak hedef:** "başka oda" — frame, IP hedefi değişmeden, **default
  gateway'in MAC'ine** gönderilir (Bölüm 6). Gateway ötesini halleder.

/24 dışındaki maskeleri de okuyabilmelisin: `/16` = `255.255.0.0` (65.534
host'luk ağ), `/25` = `255.255.255.128` (126 host'luk yarım ağ, sınır artık
oktet ortasından geçer). Kural aynıdır: maske kaç bit 1 ise o kadarı ağdır;
oktet sınırına denk gelmek zorunda değildir.

Her subnet'te iki adres cihazlara verilemez: host bitleri **tümü 0** olan
adres ağın kendisidir (`192.168.1.0/24`), **tümü 1** olan adres o subnet'in
**broadcast adresidir** (`192.168.1.255` — bu IP'ye gönderilen paket,
Ethernet'te `FF:FF:...` broadcast frame'ine biner ve subnet'teki herkese
ulaşır). /24'te bu yüzden 256 değil **254** kullanılabilir adres vardır.

## Private adres blokları

İnternette yönlendirilmeyen, herkesin kendi iç ağında serbestçe
kullanabildiği üç blok ayrılmıştır (RFC 1918):

| Blok | Aralık | Tipik yer |
|---|---|---|
| `10.0.0.0/8` | 10.0.0.0 – 10.255.255.255 | büyük kurumsal ağlar |
| `172.16.0.0/12` | 172.16.0.0 – 172.31.255.255 | orta ölçek, Docker varsayılanları |
| `192.168.0.0/16` | 192.168.0.0 – 192.168.255.255 | ev, küçük ofis, lab tezgâhı |

Şirket ağındaki `10.4.12.7` de, evindeki `192.168.1.130` da private
adrestir; internete çıkışları NAT üzerinden olur (Bölüm 12). İki özel adres
daha gör: `127.0.0.1` **loopback**tur — "kendim": bu adrese giden trafik
kabloya hiç çıkmaz, stack'in içinde döner; kendi yazdığın sunucuyu aynı
makinede test etmenin adresidir. `169.254.x.x` (link-local) ise "DHCP'den
adres alamadım" itirafıdır — PC'nde bunu görüyorsan adres *alamamışsın*
demektir (Bölüm 8).

:::saha-notu Kendi ayarını okumayı bilmek
Windows'ta `ipconfig` (ayrıntı için `ipconfig /all`), Linux'ta `ip addr`
(kısaca `ip a`). Bakacağın üçlü: **IPv4 adresi**, **subnet mask**,
**default gateway**. Kartına bağlanamıyorsan ilk soru: kartın IP'si ile
PC'nin IP'si aynı subnet'te mi? `192.168.1.10/24` ile `192.168.2.20/24`
aynı kabloda olsalar bile birbirine "uzak"tır — stack paketi gateway'e
yollamaya çalışır, gateway yoksa trafik ölür. Lab tezgâhında en hızlı
çözüm: PC'ye kartla aynı subnet'ten elle ikinci bir IP vermek.
:::

:::tuzak Maske uyuşmazlığı: tek yönlü hayalet arıza
İki cihazın *IP'leri* aynı subnet'te görünürken *maskeleri* farklıysa
(biri /24, öbürü /16), trafik tek yönde çalışıp öbür yönde çalışmayabilir:
A, B'yi yerel görüp doğrudan gönderir; B, A'yı uzak görüp gateway'e atar.
Ping'in gidip cevabın gelmediği, "bazen çalışıyor" hissi veren sinir
bozucu arızaların klasiğidir. IP'yi kontrol ederken maskeyi de *her zaman*
kontrol et.
:::

:::analoji Apartman ve site
Subnet bir site, host adresi daire numarasıdır. Maske, adresin
"site adı / daire no" sınırını çizer. Aynı sitedeysen (yerel) zarfı komşunun
kapısının altından kendin atarsın (ARP + doğrudan frame). Başka sitedeyse
(uzak) zarfı sitenin güvenlik kulübesine (gateway) bırakırsın; gerisini
o düşünür. Kulübenin yerini bilmiyorsan (gateway tanımsız) zarf elinde
kalır — "network unreachable".
:::

:::derin-dalis IPv6'ya dürüst bir pencere
IPv4'ün 32 biti ~4,3 milyar adres eder ve tükendi; **IPv6** adresleri
128 bittir ve hex gruplarla yazılır: `2001:db8:4f00::1a2c`. (`::`, aradaki
sıfır gruplarının kısaltmasıdır; bir adreste yalnız bir kez kullanılır.)
Bilmen gereken minimum şu: her IPv6 arabirimi kendine `fe80::` ile başlayan
bir **link-local** adres üretir — DHCP'siz, konfigürasyonsuz, yalnız yerel
segmentte geçerli. Modern işletim sistemleri IPv6'yı varsayılan açar; bu
yüzden Wireshark'ta hiç istemediğin halde ICMPv6/`fe80::` trafiği görürsün;
arıza değildir. Gömülü stack'lerde (lwIP dahil) IPv6 genellikle derleme
seçeneğidir ve kapalı tutulur; kurumsal LAN pratiğinde de bu kılavuz
boyunca IPv4 konuşacağız. IPv6'da subnet mantığı aynıdır, maske hemen hep
/64'tür ve ARP'ın yerini NDP (Neighbor Discovery Protocol) alır — kavramlar
birebir taşınır.
:::

:::ozet
- IPv4 = 32 bit, dört oktet; adres hiyerarşiktir: ağ kısmı + host kısmı.
- Subnet mask / CIDR (`/24`) bu sınırı çizer; stack her gönderimde
  AND'leyip **yerel mi uzak mı** kararı verir.
- Yerel → ARP + doğrudan frame; uzak → gateway'in MAC'ine frame.
- Host bitleri tüm-0 = ağ adresi, tüm-1 = subnet broadcast; /24'te 254
  kullanılabilir adres kalır.
- Private bloklar: 10/8, 172.16/12, 192.168/16; `127.0.0.1` loopback,
  `169.254.x.x` "DHCP alamadım" işareti.
- Maske uyuşmazlığı tek yönlü arıza üretir; IP'yle birlikte maskeyi de
  kontrol et.
:::
