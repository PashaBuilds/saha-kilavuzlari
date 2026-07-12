# Ek A — Terimler Sözlüğü

Alfabetik. Her tanımın sonundaki bağlantı, terimin asıl anlatıldığı bölüme
götürür.

**ACK (acknowledgment)** — TCP'de alıcının "buraya kadar eksiksiz aldım"
onayı; header'daki acknowledgment number ile taşınır. ACK'lanmayan veri
yeniden gönderilir. → [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**ARP (Address Resolution Protocol)** — Yerel ağda bir IP adresinin hangi
MAC'te olduğunu bulan protokol; broadcast soru, unicast cevap. IP dünyası
ile Ethernet dünyasının köprüsü. → [Bölüm 7](#bolum-7-arp-iki-dunyanin-koprusu)

**ARP cache** — Öğrenilen IP↔MAC eşlemelerinin tutulduğu tablo
(`arp -a` / `ip neigh`). Bayat kaydı, "IP aynı ama cihaz değişti"
arızalarının klasik failidir. → [Bölüm 7](#bolum-7-arp-iki-dunyanin-koprusu)

**Auto-negotiation** — İki PHY'nin hız ve duplex'te anlaşma töreni; link
LED'i bu anlaşma bitince yanar. Tek tarafı elle sabitlemek duplex
mismatch üretir. → [Bölüm 2](#bolum-2-fiziksel-katman-ve-kablonun-ici)

**Broadcast** — Segmentteki herkese gönderim; Ethernet'te hedef
`FF:FF:FF:FF:FF:FF`, IPv4'te subnet'in son adresi. ARP ve DHCP broadcast'e
dayanır. → [Bölüm 3](#bolum-3-ethernet-ve-mac)

**Broadcast domain** — Bir broadcast frame'inin ulaşabildiği alan.
Switch'ler bölmez, router böler; pratikte "senin subnet'in".
→ [Bölüm 4](#bolum-4-ag-cihazlari-hub-switch-router)

**CIDR (/24 gösterimi)** — Subnet mask'ın "baştaki 1 bitlerinin sayısı"
olarak yazımı: `/24` = `255.255.255.0`.
→ [Bölüm 5](#bolum-5-ip-subnet-ve-yerel-mi-uzak-mi-karari)

**Collision domain** — Aynı anda tek cihazın konuşabildiği, çakışmaların
yaşandığı alan; hub'lı dünyanın derdi. Switch her portu ayrı collision
domain yapar. → [Bölüm 4](#bolum-4-ag-cihazlari-hub-switch-router)

**Default gateway** — Subnet dışına giden her paketin teslim edildiği
router adresi; routing table'daki `default` satırı.
→ [Bölüm 6](#bolum-6-gateway-ve-yonlendirme)

**DHCP (Dynamic Host Configuration Protocol)** — IP + maske + gateway +
DNS'i otomatik dağıtan protokol; DORA (Discover/Offer/Request/ACK)
akışıyla çalışır, adresi kiralar (lease).
→ [Bölüm 8](#bolum-8-dhcp-adresler-nereden-geliyor)

**DNS (Domain Name System)** — Alan adlarını IP adreslerine çeviren
dağıtık hiyerarşi (root → TLD → authoritative); cevaplar TTL süresince
cache'lenir. → [Bölüm 10](#bolum-10-dns-internetin-rehberi)

**Duplex (full/half)** — Full: aynı anda iki yön; half: tek seferde tek
yön. Modern switch'li ağ full-duplex'tir; uyumsuzluk sinsi yavaşlık
üretir. → [Bölüm 2](#bolum-2-fiziksel-katman-ve-kablonun-ici)

**Enkapsülasyon** — Her katmanın, üstten aldığı veriye kendi header'ını
ekleyip alta devretmesi: mesaj → segment → paket → frame.
→ [Bölüm 1](#bolum-1-buyuk-resim-katmanlar)

**Ephemeral port** — İstemci tarafına işletim sisteminin geçici olarak
verdiği yüksek numaralı port (tipik 49152+).
→ [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**EtherType** — Ethernet header'ında payload'ın protokolünü söyleyen 2
byte: `0x0800` IPv4, `0x0806` ARP. → [Bölüm 3](#bolum-3-ethernet-ve-mac)

**FCS (frame check sequence)** — Frame sonundaki CRC-32; tutmazsa frame
sessizce atılır, üst katmana haber gitmez.
→ [Bölüm 3](#bolum-3-ethernet-ve-mac)

**Firewall** — IP/port kurallarıyla trafiğe izin veren/engelleyen
mekanizma; "timeout ama refused değil" arızalarının sık faili.
→ [Bölüm 12](#bolum-12-nat-ve-ev-kurum-aginin-gercegi)

**Flow control (TCP)** — Alıcının window alanıyla "şu kadar alabilirim"
diyerek göndereni frenlemesi. `recv()` çağırmayan uygulama, karşı tarafı
durdurur. → [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**Frame** — Veri bağı katmanının paket birimi: MAC'ler + EtherType +
payload + FCS. → [Bölüm 3](#bolum-3-ethernet-ve-mac)

**Gratuitous ARP** — Sorulmadan yayınlanan ARP: "ben buradayım" duyurusu
ve IP çakışması tespiti. → [Bölüm 7](#bolum-7-arp-iki-dunyanin-koprusu)

**Hub** — Sinyali anlamadan tüm portlara kopyalayan L1 cihazı; ölü
teknoloji, collision domain kavramının atası.
→ [Bölüm 4](#bolum-4-ag-cihazlari-hub-switch-router)

**ICMP** — IP'nin haberci protokolü: ping'in echo request/reply'ı,
traceroute'un "time exceeded" mesajı buradandır.
→ [Bölüm 6](#bolum-6-gateway-ve-yonlendirme)

**Jumbo frame** — 1500'den büyük (tipik 9000) MTU'lu frame; yol üstündeki
her cihaz desteklerse çalışır. → [Bölüm 3](#bolum-3-ethernet-ve-mac)

**Link-local (169.254.x.x / fe80::)** — Yalnız yerel segmentte geçerli,
kendiliğinden üretilen adres. IPv4'te görülmesi "DHCP'den alamadım"
demektir. → [Bölüm 8](#bolum-8-dhcp-adresler-nereden-geliyor)

**Loopback (127.0.0.1)** — Makinenin kendisi; trafik kabloya çıkmaz.
Kendi sunucunu yerelde test etme adresi.
→ [Bölüm 5](#bolum-5-ip-subnet-ve-yerel-mi-uzak-mi-karari)

**lwIP** — Gömülü sistemlerin hafif TCP/IP stack'i; raw/netconn/socket
API'leri sunar. → [Bölüm 14](#bolum-14-gomulu-sistemlerde-ethernet)

**MAC adresi** — 48 bitlik donanım kimliği: OUI (üretici) + cihaz kısmı.
Yalnız yerel segmentte anlamlıdır; her router atlamasında frame'le
birlikte yenilenir. → [Bölüm 3](#bolum-3-ethernet-ve-mac)

**MDIO/MDC** — MAC'in PHY register'larına eriştiği iki telli yönetim
hattı; link durumunun (BMSR) gerçek kaynağı.
→ [Bölüm 14](#bolum-14-gomulu-sistemlerde-ethernet)

**MTU (Maximum Transmission Unit)** — Frame payload'ının üst sınırı;
standart Ethernet'te 1500 byte. → [Bölüm 3](#bolum-3-ethernet-ve-mac)

**Multicast** — Bir gruba gönderim; yalnız abone kartlar işler. mDNS,
LLDP, endüstriyel protokoller kullanır.
→ [Bölüm 3](#bolum-3-ethernet-ve-mac)

**NAT (Network Address Translation)** — Private iç adresleri tek public
adrese çeviren mekanizma; eşlemeler NAT tablosunda, kayıtlar ölümlü.
→ [Bölüm 12](#bolum-12-nat-ve-ev-kurum-aginin-gercegi)

**OUI (Organizationally Unique Identifier)** — MAC'in ilk 3 byte'ı;
üreticiyi söyler, Wireshark isimlendirmede kullanır.
→ [Bölüm 3](#bolum-3-ethernet-ve-mac)

**PHY** — Kablonun analog dünyası ile çipin dijital dünyası arasındaki
alıcı-verici; autoneg ve link tespiti buradadır.
→ [Bölüm 14](#bolum-14-gomulu-sistemlerde-ethernet)

**Port (TCP/UDP)** — Makine içindeki uygulamayı seçen 16 bitlik numara;
0–1023 well-known bölgesidir. Switch'in fiziksel portuyla karıştırma.
→ [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**Port forwarding** — Router'a girilen kalıcı NAT kuralı: "dışarıdan şu
porta geleni içeride şu adrese ilet".
→ [Bölüm 12](#bolum-12-nat-ve-ev-kurum-aginin-gercegi)

**Port mirroring (SPAN)** — Yönetilebilir switch'te bir portun trafiğinin
kopyasını başka porta aynalama; Wireshark'la başkasının trafiğini
izlemenin meşru yolu. → [Bölüm 4](#bolum-4-ag-cihazlari-hub-switch-router)

**Private adres** — İnternette yönlendirilmeyen bloklar: 10/8, 172.16/12,
192.168/16; dışarı NAT ile çıkar.
→ [Bölüm 5](#bolum-5-ip-subnet-ve-yerel-mi-uzak-mi-karari)

**raw API (lwIP)** — lwIP'nin callback tabanlı, RTOS gerektirmeyen
arayüzü; en hızlı ama thread-safe olmayan kapı. Bloklayan kardeşleri
netconn ve socket API'dir; Vitis'teki `api_mode` seçimi budur.
→ [Bölüm 14](#bolum-14-gomulu-sistemlerde-ethernet)

**Resolver** — Senin adına DNS hiyerarşisini gezen özyineli sunucu
(ISS'in DNS'i, 8.8.8.8...). → [Bölüm 10](#bolum-10-dns-internetin-rehberi)

**Retransmit** — ACK'lanmayan TCP verisinin yeniden gönderimi; veriyi
kurtarır, gecikme (jitter) olarak faturalanır.
→ [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**RGMII** — PHY–MAC arası en yaygın Gigabit pin arayüzü; saat/veri
gecikme (delay) ayarı, bring-up'ın klasik tuzağıdır.
→ [Bölüm 14](#bolum-14-gomulu-sistemlerde-ethernet)

**Router** — IP'ye bakıp ağlar arası yönlendiren L3 cihazı; broadcast'i
durdurur, her bacağı ayrı subnet'tir.
→ [Bölüm 4](#bolum-4-ag-cihazlari-hub-switch-router)

**RST (reset)** — TCP'nin acil kesmesi; kapalı porta bağlantıda dönen
"connection refused"un kendisi. Teşhiste "makine ayakta, dinleyen yok"
demektir. → [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**Sequence number** — TCP'de her byte'ın numarası; sıralamanın ve
retransmit'in temeli. → [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**Soket (socket)** — Uygulamanın ağ uç noktası; bağlantının kimliği
dörtlüdür: kaynak IP:port ↔ hedef IP:port.
→ [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**STP (Spanning Tree Protocol)** — Switch'ler arası halka (loop)
oluştuğunda ağı broadcast fırtınasından koruyan protokol.
→ [Bölüm 4](#bolum-4-ag-cihazlari-hub-switch-router)

**Subnet mask** — IP'nin ağ/host sınırını çizen 32 bitlik şablon; "yerel
mi uzak mı" kararı IP'nin maskeyle AND'lenmesiyle verilir.
→ [Bölüm 5](#bolum-5-ip-subnet-ve-yerel-mi-uzak-mi-karari)

**Switch** — Kaynak MAC'ten öğrenip hedef MAC'e göre ileten L2 cihazı;
bilinmeyene flood eder, broadcast'i böl(e)mez.
→ [Bölüm 4](#bolum-4-ag-cihazlari-hub-switch-router)

**TCP** — Güvenilir, sıralı byte akışı: el sıkışma, seq/ACK, retransmit,
akış ve tıkanıklık kontrolü. Komut, dosya, eksiksizlik isteyen her iş
için. → [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**TLS (Transport Layer Security)** — Şifreleme + bütünlük + kimlik üçlüsü;
HTTPS = TLS tüneli içinde HTTP. Sertifika zinciri güvenilen kökte
bitmelidir. → [Bölüm 11](#bolum-11-http-ve-https)

**Traceroute / tracert** — TTL'i 1'den başlatıp artırarak yoldaki her
router'ı konuşturan araç. İlk hop daima kendi gateway'in olmalı.
→ [Bölüm 6](#bolum-6-gateway-ve-yonlendirme)

**TTL (IP)** — Paketin her router'da 1 azalan ömür sayacı; sıfırda paket
atılır, halkalar böyle kırılır. → [Bölüm 6](#bolum-6-gateway-ve-yonlendirme)

**TTL (DNS)** — Bir DNS cevabının cache'lerde geçerli kalma süresi
(saniye). İki TTL'in adı aynı, işi farklıdır.
→ [Bölüm 10](#bolum-10-dns-internetin-rehberi)

**UDP** — Bağlantısız, onaysız, minimal taşıma: port + checksum. Düşük
gecikmeli canlı akış ve tek paketlik soru-cevap için.
→ [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**Unicast** — Tek alıcıya gönderim; trafiğin olağan hali.
→ [Bölüm 3](#bolum-3-ethernet-ve-mac)

**VLAN (802.1Q)** — Tek fiziksel altyapıyı mantıksal ağlara bölme; frame'e
4 byte'lık tag eklenir, her VLAN ayrı broadcast domain'dir.
→ [Bölüm 3](#bolum-3-ethernet-ve-mac)

**Well-known port** — 0–1023 arası, geleneksel sahipli portlar: 22 SSH,
53 DNS, 80 HTTP, 443 HTTPS... → [Bölüm 9](#bolum-9-tasima-katmani-tcp-ve-udp)

**Wireshark** — Frame'leri yakalayıp katmanlarına ayıran analizör; detay
ağacı, enkapsülasyonun canlı halidir.
→ [Bölüm 15](#bolum-15-pratik-alet-cantasi)
