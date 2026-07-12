# Ek B — Hızlı Referans Kartı

Tek ekranlık özet: yazdır, tezgâhın yanına as.

## Katman tablosu

| # | Katman | Paket adı | Adresi | Örnek protokoller | Kutusu |
|---|---|---|---|---|---|
| 5 | Uygulama | mesaj | — | HTTP, TLS, DNS, DHCP, MQTT | uygulaman |
| 4 | Taşıma | segment / datagram | **port** | TCP, UDP | OS / lwIP |
| 3 | Ağ | paket | **IP** | IP, ICMP | router |
| 2 | Veri bağı | frame | **MAC** | Ethernet, ARP, 802.1Q | switch |
| 1 | Fiziksel | bit | — | 1000BASE-T, kablo, PHY | hub, kablo |

## Header boyutları ve sınırlar

| Şey | Değer |
|---|---|
| Ethernet header + FCS | 14 + 4 byte |
| IPv4 header | 20 byte (seçeneksiz) |
| TCP header | 20 byte (seçeneksiz) |
| UDP header | 8 byte |
| MTU (standart) | 1500 byte payload |
| Frame payload alt sınırı | 46 byte (altı padding'lenir) |
| MAC / IPv4 / port genişliği | 48 / 32 / 16 bit |
| Broadcast MAC | `FF:FF:FF:FF:FF:FF` |
| EtherType | `0x0800` IPv4 · `0x0806` ARP · `0x86DD` IPv6 · `0x8100` VLAN |

## Portlar ve adresler

| Port | İş | | Blok | Anlamı |
|---|---|---|---|---|
| 22 | SSH | | `10.0.0.0/8` | private |
| 53 | DNS | | `172.16.0.0/12` | private |
| 67/68 | DHCP | | `192.168.0.0/16` | private |
| 80 | HTTP | | `127.0.0.1` | loopback (kendim) |
| 123 | NTP | | `169.254.0.0/16` | "DHCP alamadım" |
| 443 | HTTPS | | `x.x.x.0` (/24) | ağ adresi — verilemez |
| 502 | Modbus/TCP | | `x.x.x.255` (/24) | subnet broadcast |

## Komut karnesi

| Soru | Windows | Linux |
|---|---|---|
| IP/mask/gateway? | `ipconfig /all` | `ip addr` + `ip route` |
| Hedef yaşıyor mu? | `ping X` | `ping X` |
| ARP tablosu? | `arp -a` | `ip neigh` |
| Yol? | `tracert X` | `traceroute X` |
| İsim çözümü? | `nslookup X` | `dig X` |
| Dinleyenler? | `netstat -ano` | `ss -tlnp` |
| Port açık mı? | `Test-NetConnection X -Port N` | `nc -vz X N` |
| DNS cache temizle | `ipconfig /flushdns` | `resolvectl flush-caches` |
| DHCP yenile | `ipconfig /release` + `/renew` | `dhclient -r` + `dhclient` |

## Wireshark hızlı filtreler

| Amaç | Display filter |
|---|---|
| Tek cihaz | `ip.addr == 192.168.1.130` |
| ARP / ping / DHCP / DNS | `arp` · `icmp` · `dhcp` · `dns` |
| TCP portu / el sıkışma / reset | `tcp.port == N` · `tcp.flags.syn == 1` · `tcp.flags.reset == 1` |
| Sorunlu TCP | `tcp.analysis.flags` |
| İçerik oku | sağ tık → Follow → TCP Stream |

## Teşhis sırası (ezber)

`ping 127.0.0.1` → `ping <kendi IP>` → `ping <gateway>` → `ping 8.8.8.8` →
`nslookup ad` → `telnet hedef port`. Hangi adım kırıldıysa arıza o
katmandadır; ağacın tamamı [Bölüm 16](#bolum-16-ariza-teshis-rehberi)'da.

Gömülü kart için ön ek: **BMSR link biti → autoneg/MAC hızı → MAC
sayaçları → IP config → ARP görünürlüğü**
([Bölüm 14](#bolum-14-gomulu-sistemlerde-ethernet)).
