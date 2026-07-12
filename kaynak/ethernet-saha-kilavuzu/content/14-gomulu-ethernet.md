# Bölüm 14 — Gömülü Sistemlerde Ethernet

Kılavuz boyunca "stack" dediğimiz şey PC'de işletim sisteminin içinde
gizliydi. Gömülü dünyada o perde kalkar: PHY register'larını sen okursun,
DMA descriptor'larını sen kurarsın, lwIP'yi sen derlersin. Bu bölüm, önceki
bölümlerin kavramlarını kartın üstüne indirir — ve "kart ping atmıyor"
dendiğinde nereden başlayacağını öğretir.

## Veri yolu: kablodan uygulamana

{{svg:sema-20-gomulu-yol.svg|Gömülü Ethernet zinciri: kablodaki analog sinyali PHY dijitalleştirir, (R)(G)MII üzerinden MAC'e verir; MAC frame'i doğrulayıp DMA ile RAM'e yazar; sürücü kesmeyle haber alır, lwIP katmanları işler, uygulaman soketten okur. Altın kesikli hat veri değil kontrol taşır: MDIO ile PHY register'larına erişilir.}}

Zinciri tanıyalım:

- **PHY** (physical layer transceiver): kablonun analog dünyası ile çipin
  dijital dünyası arasındaki çevirmen. Bölüm 2'nin tüm işleri — hat
  kodlama, auto-negotiation, link tespiti — bu çipte olur. Genellikle
  kart üstünde ayrı bir entegredir; RJ45'e **magnetics** (izolasyon
  trafosu) üzerinden bağlanır.
- **MAC** (media access controller): frame dünyasının sahibi. Bölüm 3'ün
  işleri — frame'i dizmek, FCS hesaplamak/doğrulamak, hedef MAC'e göre
  kabul/ret filtrelemek — burada. İşlemcinin/FPGA'nın *içindedir*:
  Zynq-7000 ve Zynq UltraScale+/Versal'de bu blok **GEM** (Gigabit
  Ethernet MAC) adıyla anılır; yazılımın "Ethernet register'ları" dediği
  şey GEM'in register'larıdır.
- **PHY ↔ MAC arayüzü — MII ailesi:** iki çip arasındaki standart pin
  arayüzü. Adları sık duyacaksın:

| Arayüz | Hız | Pin karakteri |
|---|---|---|
| MII | 100 Mb/s | 4 bit veri × 25 MHz, çok pin |
| RMII | 100 Mb/s | 2 bit × 50 MHz, az pin (küçük MCU'ların gözdesi) |
| GMII | 1 Gb/s | 8 bit × 125 MHz, çok pin |
| **RGMII** | 1 Gb/s | 4 bit × 125 MHz DDR — sahada en yaygını |
| SGMII | 1 Gb/s | seri, diferansiyel çift; FPGA transceiver'ına girer |

- **MDIO/MDC** (management data I/O): veri yolundan tamamen ayrı, iki
  telli yavaş bir **kontrol** kanalı — I2C'nin Ethernet dünyasındaki
  kuzeni. MAC (yani senin yazılımın) PHY'nin register'larını bu hatla
  okur/yazar. Standart register haritasının ilk ikisi ezberlik:
  **BMCR** (register 0 — kontrol: reset, autoneg başlat, hız zorla) ve
  **BMSR** (register 1 — durum: **link up/down biti**, autoneg tamamlandı
  biti). "Link var mı" sorusunun donanımdaki gerçek cevabı BMSR'dedir;
  LED sadece onun kablodaki yansımasıdır.
- **DMA + descriptor:** Gigabit hızında her byte'ı CPU ile taşımak intihar
  olur; MAC, frame'leri **DMA** ile doğrudan RAM'e yazar. Sürücü ile
  donanım, **descriptor** denen küçük kayıt halkaları (ring) üzerinden
  anlaşır: her descriptor "şu adreste şu boyda bir buffer var; dolunca
  işaretle" der. Kesme gelir, sürücü dolu descriptor'ları gezer, paketleri
  stack'e verir. Verimin ve bug'ların büyük kısmı bu halkalardadır:
  buffer tükenmesi, cache tutarlılığı, hizalama...
- **Checksum offload:** IP/TCP/UDP checksum'larını yazılım yerine MAC
  donanımı hesaplayabilir/doğrulayabilir. CPU'su zayıf kartta ciddi nefes
  aldırır. İki dipnot: stack'e "donanım yapıyor, sen hesaplama" demeyi
  unutursan (lwIP'te `CHECKSUM_GEN_*`/`CHECKSUM_CHECK_*` ayarları) çift
  hesap ya da hiç hesap yapılmaz; ve Wireshark'ı *gönderen* makinede
  çalıştırırken "checksum incorrect" uyarısı görürsen paniğe kapılma —
  capture, checksum'ı henüz donanım doldurmadan alınmıştır (offload
  artefaktı), gerçek hataysa karşı taraf paketi zaten atardı.

## lwIP: kartın TCP/IP kütüphanesi

Gömülü dünyanın fiili standardı **lwIP**'dir (lightweight IP): Bölüm
5–9'da öğrendiğin her şeyin — ARP, IPv4, ICMP, UDP, TCP, üstüne DHCP ve
DNS istemcileri — birkaç on KB RAM'e sığacak boyda, açık kaynak
gerçeklemesi. PC'de işletim sisteminin görünmez yaptığı işi kartta
görünür yapar: stack, projenin içinde *derlenen bir kütüphanedir*; hangi
protokol dahil, kaç eşzamanlı bağlantı, tamponlara ne kadar RAM — hepsi
`lwipopts.h` dosyasındaki seçeneklerle senin elindedir.

lwIP iki modda çalışır ve Xilinx/Vitis'te gördüğün seçenekler doğrudan
bu ayrıma denk düşer:

- **Bare-metal (NO_SYS=1):** RTOS yok. Stack'i ana döngüde sen
  çevirirsin: `xemacif_input()` sürücüden gelen paketleri stack'e taşır,
  TCP zamanlayıcılarını periyodik sen tetiklersin. Bu modda yalnızca
  **raw API** kullanılabilir — bloklayan bir çağrıyı bekletecek thread
  yoktur. Vitis'te *standalone* domain + `api_mode = RAW_API` budur.
- **OS modu (Xilinx'te FreeRTOS):** lwIP kendine bir **tcpip_thread**
  kurar; paket işleme ve protokol durum makineleri o thread'de döner.
  raw API yine vardır (ama artık o thread'in malıdır — birazdan
  geleceğiz), üstüne bloklayan iki API açılır: **netconn** ve **socket**.
  Vitis'te *freertos10_xilinx* domain + `api_mode = SOCKET_API` budur.

Vivado/Vitis iskeleti her iki modda da aynıdır: BSP'nin lwIP kütüphanesi +
`xemacpsif` (GEM sürücüsünü lwIP'ye yapıştıran katman) + örnek `echo
server` şablonu. O şablonun `main()`'indeki sıra — PHY init & autoneg
bekle, MAC'i linkin hızına ayarla, `netif` ekle (IP/mask/gateway), sonra
paketleri stack'e pompala — bu bölümün şemasının koda dökülmüş halidir.

## raw API ile socket API: aynı iş, iki dünya

**raw API** olay güdümlüdür: stack'e "bağlantı gelirse şu fonksiyonumu,
veri gelirse bu fonksiyonumu çağır" diye **callback** kaydedersin.
Bekleyen, bloklayan hiçbir çağrı yoktur; her şey paket geldiği anda,
stack'in kendi bağlamında koşar:

```c
/* raw API echo iskeleti (bare-metal) — Bölüm 9'un kavramları koda iner */
err_t veri_geldi(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t err)
{
    if (p == NULL) {              /* NULL pbuf = karşı taraf FIN gönderdi */
        tcp_close(pcb);
        return ERR_OK;
    }
    tcp_write(pcb, p->payload, p->len, TCP_WRITE_FLAG_COPY);  /* echo    */
    tcp_recved(pcb, p->tot_len);  /* "işledim": receive window'u geri aç */
    pbuf_free(p);                 /* pbuf'ı BEN serbest bırakırım        */
    return ERR_OK;
}

err_t baglanti_geldi(void *arg, struct tcp_pcb *yeni_pcb, err_t err)
{
    tcp_recv(yeni_pcb, veri_geldi);   /* bu bağlantının veri callback'i */
    return ERR_OK;
}

/* kurulum: */
struct tcp_pcb *pcb = tcp_new();
tcp_bind(pcb, IP_ADDR_ANY, 5001);     /* 0.0.0.0:5001 (B.9'daki bind)   */
pcb = tcp_listen(pcb);
tcp_accept(pcb, baglanti_geldi);

while (1)
    xemacif_input(&netif);            /* ana döngü stack'i elle çevirir */
```

İki kavram göze çarpsın: `pbuf`, lwIP'nin zincirli paket tamponudur —
kimin ne zaman serbest bırakacağı sözleşmeyle bellidir ve raw API
bug'larının anası bu sözleşmeyi bozmaktır. `tcp_recved()` ise Bölüm 9'un
flow control'ünün ta kendisidir: çağırmayı unutursan window sıfıra düşer
ve karşı taraf "kart veri almıyor" diye durur.

**socket API** ise Bölüm 15'teki Python kodunun C halidir — aynı
`socket/bind/listen/accept/recv` zinciri, bloklayan çağrılarla:

```c
/* socket API echo iskeleti — bir FreeRTOS thread'i içinde koşar */
int s = lwip_socket(AF_INET, SOCK_STREAM, 0);

struct sockaddr_in adres = {0};
adres.sin_family      = AF_INET;
adres.sin_port        = htons(5001);
adres.sin_addr.s_addr = INADDR_ANY;              /* 0.0.0.0 */
lwip_bind(s, (struct sockaddr *)&adres, sizeof(adres));
lwip_listen(s, 1);

while (1) {
    int c = lwip_accept(s, NULL, NULL);          /* BLOKLAR → RTOS şart */
    int n;
    while ((n = lwip_read(c, buf, sizeof(buf))) > 0)
        lwip_write(c, buf, n);                   /* echo */
    lwip_close(c);                               /* n<=0: FIN ya da hata */
}
```

Bloklayan `accept`/`read`, çağıran thread'i uyutur; bu yüzden RTOS
şarttır. Perde arkasında her socket çağrısı, tcpip_thread'e mesajla
gönderilir ve cevabı beklenir — konforun bedeli bu ek kopya ve gecikmedir.

Üçüncü kapı **netconn**, ikisinin arasıdır: bloklayandır (RTOS ister)
ama BSD taklidi yapmaz; lwIP'nin kendi arayüzüdür ve socket API zaten
netconn'un üstüne kurulmuş bir uyumluluk katmanıdır — yani netconn her
zaman socket'ten bir tık hafiftir.

| | raw API | netconn | socket API |
|---|---|---|---|
| RTOS | gerekmez | gerekir | gerekir |
| Model | callback (olay güdümlü) | bloklayan, lwIP'ye özgü | bloklayan, BSD standardı |
| Performans / RAM | en iyi | orta | en maliyetli (thread'e mesaj + kopya) |
| Kod taşınabilirliği | düşük | düşük | yüksek — PC kodu neredeyse aynen |
| Durum makinesi | senin sırtında | lwIP'de | lwIP'de |

Karar pratikte şuna iner: bare-metal ya da performansın kıyısında bir iş
(hızlı telemetri, minimal bootloader) → **raw**; FreeRTOS var, PC'den
taşınan/taşınacak kod ya da birden çok bağımsız bağlantı → **socket**;
FreeRTOS var ama her byte/µs kıymetli → **netconn**.

:::tuzak raw API + FreeRTOS: "arada sırada çöküyor"un klasiği
raw API fonksiyonları (`tcp_write`, `tcp_close`...) **thread-safe
değildir**: yalnızca stack'in kendi bağlamından — bare-metal'de ana
döngü, FreeRTOS'ta tcpip_thread'in callback'leri — çağrılabilir. Kendi
FreeRTOS thread'inden ya da kesme içinden `tcp_write` çağırmak, çoğu
zaman çalışıp ayda bir açıklanamaz biçimde çöken türden bir yarış koşulu
üretir. Başka thread'den stack'e iş yaptırmanın meşru yolu
`tcpip_callback()` ile işi tcpip_thread'e postalamaktır — ya da baştan
socket API kullanmaktır. Socket API'de de kural mütevazı ama gerçektir:
aynı soketi aynı anda tek thread kullansın.
:::

:::tuzak RGMII delay: bring-up'ın klasik canavarı
RGMII'de saat ile veri pinleri arasında ~2 ns'lik kasıtlı bir gecikme
(delay/skew) gerekir; bu gecikmeyi ya PCB'de kıvrımlı hat, ya PHY'nin
"internal delay" modu (RGMII-ID), ya MAC tarafı sağlar. İki taraf da
eklerse ya da hiçbiri eklemezse ortaya çıkan tablo tanıdıktır: link
kurulur (autoneg MDIO'dan yürür, ondan etkilenmez), MDIO okumaları
mükemmeldir, ama frame'ler bozuk gelir — CRC hataları, ya da hiç paket
yok. "Link var ama tek paket geçmiyor + hız düşürünce (100M) düzeliyor"
deseni gördüğünde aklına önce RGMII delay konfigürasyonu gelsin
(PHY datasheet'inde RX_DLY/TX_DLY, devre şemasında strap pinleri).
:::

## "Kart ping atmıyor": gömülü teşhis sırası

Bölüm 16'daki genel ağaç burada da geçerli ama gömülü tarafın kendine has
ilk katmanları var. Sıra hep aşağıdan yukarı:

1. **PHY link register'ı (BMSR):** MDIO'dan oku (ya da örnek koddaki
   `phy_link_status`). Link biti 0 ise üst katmanlarla uğraşma: kablo,
   magnetics, PHY reset/strap, RGMII delay. Karşı switch portunun LED'i
   de ikinci bir tanıktır.
2. **Autoneg sonucu ve MAC ayarı:** link 1000M'de anlaşmış ama MAC 100M'e
   konfigüreyse tablo yine "link var, veri yok"tur. PHY'nin anlaştığı
   hız/duplex'i oku, MAC'i ona göre programladığından emin ol.
3. **MAC init ve istatistikler:** GEM'in rx frame sayaçları artıyor mu?
   Artmıyorsa DMA/descriptor kurulumuna, artıyorsa stack'e bak. "FCS error"
   sayacı artıyorsa fiziksel/RGMII katına geri dön.
4. **IP konfigürasyonu:** `netif`'e verilen IP/mask/gateway doğru mu?
   PC ile aynı subnet'te mi (Bölüm 5'in AND testi)?
5. **ARP görünürlüğü:** PC'den karta ping atarken Wireshark'ta `arp`
   filtresi: kartın için ARP request geliyor mu, kart cevap veriyor mu?
   Request geliyor ama cevap yoksa stack ayakta değil ya da MAC filtresi
   yanlış (yanlış/çakışan MAC adresi — Bölüm 3'ün tuzağı). Cevap var ama
   ping yoksa ICMP tarafına, yani stack konfigürasyonuna odaklan.

Bu sıranın güzelliği şu: her adım bir *katmanı* aklar. BMSR'yi görmeden
IP ayarıyla oynamak, sahada en çok vakit yakan reflekstir.

:::saha-notu İlk gün yapılacak üç şey
Yeni bir kartın Ethernet bring-up'ında, daha hiç kod yazmadan:
(1) PHY'nin MDIO adresini ve modelini devre şemasından çıkar, datasheet'in
register haritasını aç; (2) BMSR'yi okuyan 10 satırlık bir test yaz —
kablo tak/çıkar yapıp bitin değiştiğini gör (MDIO'nun çalıştığını da
kanıtlar); (3) PC tarafında Wireshark'ı `arp or icmp` filtresiyle hazır
bekletiyor ol. Bu üçlü, sonraki her arızada sana dakikalar kazandırır.
:::

:::analoji PHY dış kapı, MAC posta odası
PHY binanın sokak kapısıdır: kapı zili (link), kapının dili (autoneg)
onun işidir; içeride ne konuşulduğunu bilmez. MAC posta odasıdır:
zarfları açmadan adres kontrolü yapar, bozuk zarfı çöpe atar, sağlamları
posta arabasına (DMA) yükler. lwIP ise binanın sekreteryasıdır: zarfı
açar, dilekçeyi (TCP/UDP) işleme koyar, cevabı yazdırır. "Mektup gelmiyor"
şikâyetinde önce sokak kapısının açılıp açılmadığına bakılır — BMSR.
:::

:::ozet
- Zincir: RJ45/magnetics → PHY → (R)(G)MII → MAC (Zynq'ta GEM) → DMA/
  descriptor → RAM → sürücü → lwIP → uygulama; MDIO ayrı kontrol hattıdır.
- PHY analog↔dijital çevirmen (L1), MAC frame işçisi (L2); ikisinin
  arasındaki RGMII delay, bring-up'ın klasik tuzağıdır.
- BMSR'deki link biti, "link var mı"nın donanımdaki gerçeğidir; teşhis
  oradan başlar.
- DMA descriptor halkaları performansın kalbi, checksum offload CPU
  ilacıdır (stack ayarıyla tutarlı olmak şartıyla).
- lwIP; projene derlenen, `lwipopts.h` ile biçilen bir stack'tir. Üç API:
  raw (callback, RTOS'suz, en hızlı), netconn (bloklayan, lwIP'ye özgü),
  socket (BSD standardı, en taşınabilir). Vitis'te `api_mode` bu seçimdir.
- raw API yalnız stack bağlamından çağrılır; FreeRTOS thread'inden
  `tcp_write` çağırmak yarış koşuludur — `tcpip_callback()` ya da socket
  API kullan.
- Teşhis sırası: PHY link → autoneg/MAC hızı → MAC sayaçları → IP config →
  ARP görünürlüğü. Katman katman, aşağıdan yukarı.
:::
