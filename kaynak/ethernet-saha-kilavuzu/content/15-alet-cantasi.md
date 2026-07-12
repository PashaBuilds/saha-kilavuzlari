# Bölüm 15 — Pratik Alet Çantası

Teori bitti sayılır; bu bölüm tezgâhın çekmecesi. Wireshark'ı verimli
kullanmayı, komut satırının vazgeçilmezlerini ve karta bağlanan minimal
Python soket kodlarını tek yerde topluyoruz. Amaç ezber değil: her aletin
*hangi soruyu* cevapladığını bilmek.

## Wireshark: üç panel, iki filtre

**Wireshark**, ağ arabiriminden geçen frame'leri yakalayıp katmanlarına
ayırarak gösteren analizördür — bu kılavuzun neredeyse her bölümünün
"canlı kanıt" aracı. Ekranı üç panelden oluşur:

{{svg:sema-21-wireshark.svg|Wireshark anatomisi: üstte paket listesi (kuşbakışı), ortada seçili paketin katman katman detay ağacı — Şekil 2'deki enkapsülasyon zincirinin canlısı —, altta ham hex. Ağaçta bir alanı tıklamak, hex'te karşılığını vurgular: "hangi byte hangi katmanın" sorusunun kesin cevabı.}}

En kritik ayrım iki filtre türüdür:

- **Capture filter** (yakalama filtresi): yakalama *başlamadan* verilir,
  BPF sözdizimi kullanır (`host 192.168.1.130`, `port 5001`). Diske ne
  yazılacağını belirler; yoğun ağda dosya boyutunu kurtarır. Ama aşırı
  dar tutarsan "meğer sorun filtrelediğim pakette miş" tuzağına düşersin.
- **Display filter** (görüntüleme filtresi): yakalama *bittikten sonra*,
  üstteki yeşil/kırmızı kutuya yazılır; sözdizimi farklıdır
  (`ip.addr == 192.168.1.130`, `tcp.port == 5001`). Her şeyi yakala,
  sonra süz — lab'da genellikle doğru strateji budur.

Çekmeceye koyulacak reçeteler:

| Derdin | Display filter |
|---|---|
| Sadece kartla konuşmam | `ip.addr == 192.168.1.130` |
| ARP töreni (Bölüm 7) | `arp` |
| Ping trafiği | `icmp` |
| DHCP/DORA (Bölüm 8) | `dhcp` |
| DNS soru-cevap (Bölüm 10) | `dns` |
| Belirli TCP portu | `tcp.port == 5001` |
| El sıkışmalar | `tcp.flags.syn == 1` |
| Sert kopuşlar | `tcp.flags.reset == 1` |
| TCP'nin şikâyetleri | `tcp.analysis.flags` (retransmit, dup-ack…) |

Bir de iki tıklık hazine: bir TCP paketine sağ tık → **Follow → TCP
Stream**: bağlantının tüm yükü, iki yönlü, düz metin olarak önüne serilir —
kendi protokolünü debug ederken ilk bakacağın yer.

## Komut satırı: hangi soru, hangi komut

| Soru | Windows | Linux |
|---|---|---|
| IP/mask/gateway'im ne? | `ipconfig /all` | `ip addr` + `ip route` |
| Hedef yaşıyor mu (L3)? | `ping 192.168.1.130` | aynı (`-t` yerine varsayılan sürekli) |
| ARP tablomda kim var (L2)? | `arp -a` | `ip neigh` |
| Yol nereden geçiyor? | `tracert 8.8.8.8` | `traceroute 8.8.8.8` |
| İsim çözülüyor mu? | `nslookup example.com` | `nslookup` / `dig example.com` |
| Kim hangi portu dinliyor? | `netstat -ano` | `ss -tlnp` |
| Uzak port açık mı? | `telnet 192.168.1.130 5001` | `nc -vz 192.168.1.130 5001` |
| DNS cache temizle | `ipconfig /flushdns` | `resolvectl flush-caches` |
| DHCP yenile (Bölüm 8) | `ipconfig /release` + `/renew` | `dhclient -r` + `dhclient` |

Bu tablonun satırları, Bölüm 6'daki "teşhisin altın sırası" ve Bölüm
16'daki karar ağacıyla birleşince tam bir arıza seti eder.

:::saha-notu Windows'ta telnet istemcisi kapalı gelir
`telnet` komutu "tanınmıyor" derse: Denetim Masası → Programlar → Windows
özelliklerini aç/kapat → **Telnet Client** işaretle. Alternatif, PowerShell
ile: `Test-NetConnection 192.168.1.130 -Port 5001` — üstelik çıktısı daha
okunaklıdır (`TcpTestSucceeded: True/False`).
:::

## Python ile soket: dört minimal program

Aşağıdaki dördü de yalnızca standart kütüphane (`socket`) kullanır;
Windows'ta ve Linux'ta aynen çalışır. Önce UDP çifti — telemetri deseni
(Bölüm 9: bağlantısız, datagram başına bağımsız):

```python
# udp_alici.py — karttan gelen UDP telemetriyi dinle
import socket

alici = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP soketi
alici.bind(("0.0.0.0", 5005))       # tüm arabirimlerde 5005'i dinle
                                    # ("127.0.0.1" yazma: dışarıdan gelen giremez!)
print("5005/udp dinleniyor...")
while True:
    veri, gonderen = alici.recvfrom(2048)   # tek datagram (en çok 2048 byte)
    print(f"{gonderen[0]}:{gonderen[1]} -> {len(veri)} byte: {veri[:32]!r}")
```

```python
# udp_gonderen.py — karta (ya da udp_alici'ye) datagram at
import socket, time

gonderen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
HEDEF = ("192.168.1.130", 5005)     # kartın IP'si ve portu

for sira in range(10):
    mesaj = f"olcum {sira}".encode()
    gonderen.sendto(mesaj, HEDEF)   # bağlantı yok: gönder ve unut
    time.sleep(0.5)
print("bitti (ulaşıp ulaşmadığını UDP söylemez — Bölüm 9)")
```

Sonra TCP çifti — komut/kontrol deseni (güvenilir, sıralı):

```python
# tcp_sunucu.py — kart tarafını taklit eden echo sunucusu
import socket

sunucu = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
sunucu.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# ^ programı hemen yeniden başlatınca "address already in use" yememek için
sunucu.bind(("0.0.0.0", 5001))
sunucu.listen(1)                    # gelen bağlantı kuyruğu
print("5001/tcp dinleniyor...")

while True:
    baglanti, istemci = sunucu.accept()      # el sıkışma burada tamamlanır
    print("bağlandı:", istemci)
    with baglanti:
        while True:
            veri = baglanti.recv(1024)       # akıştan en çok 1024 byte
            if not veri:                     # b"" = karşı taraf FIN gönderdi
                break
            baglanti.sendall(veri)           # aynen geri yolla (echo)
    print("kapandı:", istemci)
```

```python
# tcp_istemci.py — karta bağlan, komut at, cevabı bekle
import socket

istemci = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
istemci.settimeout(3.0)             # cevapsız recv sonsuza dek asılı kalmasın
istemci.connect(("192.168.1.130", 5001))    # SYN/SYN+ACK/ACK burada döner

istemci.sendall(b"STATUS?\n")
cevap = istemci.recv(1024)
print("cevap:", cevap)
istemci.close()                     # FIN ile nazik kapanış
```

İki kalıcı uyarı: (1) TCP **akıştır**, mesaj değil — tek `sendall()` ile
gönderdiğin 100 byte, karşıda iki `recv()`'e bölünebilir ya da iki
gönderim tek `recv()`'de birleşebilir; kendi protokolünde mesaj sınırını
kendin çiz (uzunluk öneki ya da ayraç). (2) `recv(1024)`'ün 1024'ü "en
fazla"dır, garanti değil.

:::tuzak Çalışmayan soket kodunda ilk üç şüpheli
(1) `bind("127.0.0.1", ...)` — yalnız kendi makinenden erişilir; dış
dünya için `0.0.0.0` gerekir (Bölüm 9'daki netstat kontrolü). (2) Windows
Defender Güvenlik Duvarı — Python ilk dinlemeye geçtiğinde çıkan "erişime
izin ver" kutusunu İptal'lediysen gelen bağlantılar sessizce düşer;
Denetim Masası → Güvenlik Duvarı → uygulamaya izin ver. (3) Yanlış subnet /
maske — kod hatası aramadan önce Bölüm 5'in AND testini yap. Üçü de
"kodum bozuk" diye saatler yakılan, kodla ilgisi olmayan arızalardır.
:::

:::ozet
- Wireshark: capture filter diske yazılanı, display filter gösterileni
  süzer; detay ağacı = enkapsülasyon; Follow TCP Stream = protokol
  debug'ının kestirmesi.
- Komut tablosunu (ping/arp/tracert/nslookup/netstat/telnet) soru bazlı
  ezberle: her satır bir katmanı sorgular.
- UDP kodu: `SOCK_DGRAM`, `sendto`/`recvfrom`, bağlantı yok. TCP kodu:
  `SOCK_STREAM`, `connect`/`accept`, `recv`'in `b""` dönüşü = FIN.
- TCP akıştır: mesaj sınırını uygulaman çizer; `0.0.0.0` bind'ı ve
  firewall istisnası, "bağlanamıyorum"un iki numaralı şüphelileridir.
:::
