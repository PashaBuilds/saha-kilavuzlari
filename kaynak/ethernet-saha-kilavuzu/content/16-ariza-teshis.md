# Bölüm 16 — Arıza Teşhis Rehberi

Buraya kadar her bölüm bir katmanın sağlıklı halini anlattı; bu bölüm
hastalıklarını topluca ele alıyor. İki alet vereceğiz: aşağıdan yukarı
işleyen bir **karar ağacı** ve sahada en sık görülen senaryoların
**belirti → neden → kontrol** tablosu. İkisinin de ruhu aynı: rastgele
şeyler denemek yerine, her adımda bir katmanı aklayarak ilerlemek.

## Karar ağacı

{{svg:sema-22-karar-agaci.svg|Teşhis karar ağacı: link LED (L1) → gateway ping'i (L2/yerel L3) → hedef ping'i (yönlendirme) → DNS → port testi (L4). Her "hayır" cevabı, arızayı tek bir katmana hapseder — o katmanın bölümüne dön ve orada kal.}}

Ağacın mantığı, Bölüm 6'daki "teşhisin altın sırası"nın genelleşmiş
halidir. Uygulamada üç kural ekle:

1. **Tek değişken kuralı:** her seferde tek şeyi değiştir (kabloyu YA DA
   portu YA DA IP'yi), sonra yeniden test et. İki değişiklik birden,
   neyin işe yaradığını sonsuza dek gizler.
2. **Çift taraf kuralı:** "kart bozuk" demeden önce aynı testi PC→kart ve
   kart→PC yönünde düşün. Ping tek yönlü çalışıyorsa maske uyuşmazlığı
   (Bölüm 5) ya da firewall (Bölüm 12) kokusu vardır.
3. **Kanıt kuralı:** her adımın kanıtını Wireshark'ta gör. "Ping gitmiyor"
   ile "ping gidiyor ama cevap gelmiyor" ayrı arızalardır ve aradaki farkı
   yalnız capture söyler: ilkinde `icmp` filtresinde istek bile yoktur,
   ikincisinde istek var cevap yoktur.

## Senaryo tablosu

| Belirti | En olası neden(ler) | İlk kontrol |
|---|---|---|
| Link LED hiç yanmıyor | kablo/konnektör; switch portu kapalı; PHY reset'te takılı; (gömülü) RGMII/strap | kabloyu değiştir, başka porta tak; BMSR oku (Bölüm 14) |
| Link var, `arp -a`'da hedef yok, ping yok | farklı VLAN; yanlış subnet/maske; hedef stack ölü | Wireshark `arp`: request'e cevap var mı? IT'ye VLAN sor (Bölüm 3) |
| Aynı subnet'te ping yok ama ARP cevabı var | hedefte ICMP kapalı (Windows FW varsayılanı!); IP çakışması | hedefin firewall'u; `arp -a`'daki MAC beklediğin OUI mi (Bölüm 7) |
| Ping tek yönde çalışıyor | maske uyuşmazlığı; tek taraflı firewall | iki uçta da `ipconfig`/`ip addr` ile maskeyi karşılaştır (Bölüm 5) |
| `ping 8.8.8.8` var, `ping google.com` yok | DNS: resolver ulaşılmaz/yanlış | `nslookup google.com 8.8.8.8` (Bölüm 10) |
| Gateway'e ping var, internete yok | gateway'in WAN'ı düşük; kurum firewall/proxy | `tracert 8.8.8.8` nerede kesiliyor (Bölüm 6, 12) |
| TCP `refused` anında geliyor | makine ayakta, o portu kimse dinlemiyor | hedefte `netstat -ano` / `ss -tlnp`; `0.0.0.0` bind'ı (Bölüm 9) |
| TCP bağlanıyor ama veri gelmiyor | uygulama protokolü/format; `recv` akış varsayımı; window 0 (alıcı okumuyor) | Follow TCP Stream; `tcp.analysis.flags` (Bölüm 9, 15) |
| Bağlantı var ama berbat yavaş, CRC/`late collision` sayaçları artıyor | **duplex mismatch** (yarısı elle sabitlenmiş) | iki ucun hız/duplex ayarı: ya ikisi auto ya ikisi elle (Bölüm 2) |
| Gigabit'te link yok/kararsız, 100M'de sorunsuz | kablo çifti kopuk (2 çift sağlam); (gömülü) RGMII delay | kablo test/değiştir; PHY RX/TX delay konfigürasyonu (Bölüm 2, 14) |
| Uzun süre boşta kalan bağlantı ölüyor | NAT/firewall tablosundan düşme | keepalive ekle (Bölüm 12) |
| Kart yeniden başladı, PC bağlanamıyor | PC'de bayat ARP kaydı; kart farklı IP aldı (DHCP) | `arp -d`; kartın konsolundan IP'yi doğrula (Bölüm 7, 8) |

Tablodaki desenlerin ortak dersi: **belirtiyi katmana çevir, bölüme dön.**
"Yavaş" kelimesi L1'i (duplex), "refused" L4'ü, "isimle olmuyor IP'yle
oluyor" DNS'i işaret eder.

:::saha-notu Beş dakikalık kanıt paketi
Başkasından (IT, üretici, forum) yardım isteyeceksen şu beşliyi topla:
(1) iki ucun `ipconfig /all` / `ip addr` çıktısı, (2) `ping` ve `tracert`
çıktıları, (3) Wireshark'tan `.pcapng` kaydı — mümkünse arızanın olduğu
anı içeren 30 saniye, (4) switch/port bilgisi ve LED durumu, (5) "en son
ne değişti" cümlesi. Bu paket, karşındakinin sana soracağı ilk beş
sorunun cevabıdır; süreç günlerden dakikalara iner.
:::

:::tuzak "Restart'la düzeldi" bir teşhis değildir
Yeniden başlatma ARP cache'ini, DHCP lease'ini, NAT kayıtlarını ve yarım
kalmış TCP durumlarını topluca sıfırlar — yani *bir şeyi* düzeltmiştir ama
hangisini bilmiyorsun ve arıza geri gelecektir. Restart'a mecbur kaldıysan
en azından öncesinde kanıt paketini topla; "neyi sıfırlamak düzeltiyor"
bilgisi, kök nedenin en güçlü ipucudur (ör. yalnız `arp -d` yetiyorsa fail
bellidir).
:::

:::ozet
- Ağaç aşağıdan yukarı: link → gateway → hedef IP → DNS → port; her
  "hayır" tek katmanı suçlar.
- Tek değişken, çift yön, Wireshark kanıtı: üç altın kural.
- "Gitmedi" ile "gitti, cevap gelmedi" farklı arızadır; farkı capture
  gösterir.
- Belirtiyi katmana çevir: yavaş→duplex, refused→dinleyici, isim→DNS,
  boşta kopma→NAT.
- Yardım istemeden önce beş parçalık kanıt paketini topla; restart teşhis
  değildir.
:::
