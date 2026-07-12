# KICKOFF — ethernet-saha-kilavuzu

> Bu dosya, projenin tek başlangıç talimatıdır. Claude Code bu dosyayı okuyarak
> üretime başlar. Repo kökünde durur; CLAUDE.md bu dosyaya referans verir.

---

## 1. Proje Kimliği

- **Klasör / repo adı:** `ethernet-saha-kilavuzu`
- **Doküman adı:** *Ethernet ve Ağ İletişimi — Saha Kılavuzu*
- **Seri:** "Saha Kılavuzu" serisi (önceki üyeler: Bellek Mimarisi Saha Kılavuzu,
  RF Örnekleme Saha Kılavuzu). Aynı ruh: tek başına literatür oluşturacak
  kapsamda, pedagojik, "çok kaliteli bir blog okuyorum" hissi veren tek HTML.
- **Hedef kitle:** Ağ konusunda sıfır veya dağınık bilgisi olan, ama işinde
  Ethernet üzerinden haberleşen cihazlarla (FPGA kartları, gömülü işlemciler,
  test cihazları, kurumsal LAN) uğraşmak zorunda olan **gömülü yazılımcı**.
  Ağ yöneticisi değil; socket açan, paket yakalayan, "neden ping atamıyorum"
  diye debug eden kişi.
- **Misyon:** Okuyan kişi bittiğinde şunları yapabilmeli:
  1. Bir paketin tarayıcıdan sunucuya yolculuğunun her adımını katman katman
     anlatabilmeli (DNS → ARP → TCP → TLS → HTTP zinciri).
  2. Wireshark'ta bir capture açıp gördüğü frame'i katmanlarına ayırabilmeli.
  3. Kurumsal LAN'da bir gömülü karta UDP/TCP ile bağlanan Python kodu yazabilmeli.
  4. "Link var ama ping yok" tarzı bir arızayı sistematik teşhis edebilmeli.
- **Dil:** Türkçe gövde; teknik terimler İngilizce korunur, ilk geçtiği yerde
  parantez içinde Türkçe açıklama verilir. Örn: "broadcast (tüm ağa yayın)".
  Kısaltmalar ilk kullanımda açılır: "ARP (Address Resolution Protocol)".

---

## 2. Repo Yapısı

```
ethernet-saha-kilavuzu/
├── KICKOFF.md              ← bu dosya
├── CLAUDE.md               ← kısa yönlendirme: "KICKOFF.md'yi oku, oradaki kurallara uy"
├── content/                ← kaynak markdown, bölüm başına bir dosya
│   ├── 00-onsoz.md
│   ├── 01-katmanlar.md
│   ├── 02-fiziksel-katman.md
│   ├── ...
├── assets/
│   ├── svg/                ← el yapımı inline SVG şemalar, dosya başına bir şema
│   └── css/
│       └── kilavuz.css     ← tek tema dosyası
├── build/
│   └── build.py            ← md → tek self-contained HTML derleyici (stdlib only tercih)
└── dist/
    └── index.html          ← ÇIKTI: tek dosya, bağımlılıksız, offline çalışır
```

**Kural:** `dist/index.html` tamamen self-contained olmalı. CSS inline, SVG'ler
inline, JS minimum ve inline. CDN linki, harici font isteği, internet
bağımlılığı YOK — doküman air-gapped ortama USB ile taşınabilmeli.

---

## 3. Tasarım Sistemi

Önceki saha kılavuzlarıyla aynı görsel aile. "Teknik blog premium" hissi.

### 3.1 Tema ve Renk

- **Çift tema:** koyu (varsayılan) + açık; sağ üstte toggle, tercih
  `prefers-color-scheme` ile başlar, toggle localStorage'a yazar.
- Koyu tema paleti:
  - Arka plan: `#0E1116` (zemin), `#161B22` (kart/kod bloğu)
  - Metin: `#E6EDF3` (gövde), `#8B949E` (ikincil)
  - Vurgu: `#4DA3FF` (link/başlık vurgusu), `#E8B84B` (uyarı/altın vurgu),
    `#5BB0A6` (başarı/yeşil ton)
- Açık tema aynı hiyerarşinin ters çevrilmişi; kontrast WCAG AA'yı geçmeli.
- SVG'ler CSS değişkenleri (`var(--ink)`, `var(--accent)` vb.) kullanmalı ki
  tema değişince şemalar da uyum sağlasın. Hard-coded renk SVG içinde yasak.

### 3.2 Tipografi ve Yerleşim

- Gövde: sistem font stack'i (`-apple-system, Segoe UI, Roboto, ...`),
  16–18px, satır yüksekliği 1.7. Kod: `ui-monospace, SFMono, Consolas`.
- İçerik sütunu maksimum ~760px, ortalanmış. Şemalar gerektiğinde sütundan
  taşabilir (`max-width: 900px`).
- **Sticky içindekiler:** geniş ekranda solda sabit TOC, aktif bölüm
  scroll'a göre vurgulanır (IntersectionObserver). Dar ekranda TOC üstte
  açılır-kapanır detay (`<details>`) olur.
- Her H2 bölümü numaralı; başlıklara hover'da kopyalanabilir anchor linki.
- Üstte ince bir okuma ilerleme çubuğu (scroll progress bar).

### 3.3 İçerik Bileşenleri

Şu kutu türleri CSS class olarak tanımlanır ve içerikte bolca kullanılır:

- `saha-notu` (altın kenarlıklı): gerçek hayatta işe yarayan pratik bilgi.
  Örn: "Wireshark'ta `arp` yazıp filtrele, ilk ARP request/reply çiftini gör."
- `tuzak` (kırmızı kenarlıklı): yaygın hata / yanlış anlama.
  Örn: "Portu fiziksel Ethernet portuyla karıştırmak."
- `derin-dalis` (mavi, `<details>` ile katlanabilir): meraklısına ek derinlik;
  ana akışı okumadan atlanabilmeli.
- `analoji` (yeşil): kavramı günlük hayattan bir benzetmeyle anlatan kısa kutu.
- `komut` kutusu: kopyala butonlu kod bloğu (Wireshark filtresi, Python
  snippet, `arp -a`, `netstat`, `ping`, `tracert` çıktı örnekleri).

---

## 4. Görselleştirme Envanteri (ZORUNLU)

Bu doküman görsel ağırlıklı olacak. Her ana bölümde en az bir el yapımı SVG
şema olmalı; toplamda **en az 20 şema** hedeflenir. Şemalar süs değil,
anlatının taşıyıcısıdır: metin şemayı, şema metni tamamlar.

**Araç kuralları:**
- Tüm şemalar **el yapımı inline SVG** (kütüphane yok, Mermaid yok).
- Etiketler Türkçe, protokol/alan adları İngilizce (`SYN`, `EtherType`, `TTL`).
- Her SVG'nin `<title>` ve altında `<figcaption>` açıklaması olmalı.
- viewBox tabanlı, responsive; oklar `marker` ile, yazılar 13–14px.

**Şema listesi (asgari küme — genişletilebilir):**

| # | Şema | Bölüm |
|---|------|-------|
| 1 | OSI vs TCP/IP katman karşılaştırması, her katmanda örnek protokol | Katmanlar |
| 2 | Enkapsülasyon soğanı: HTTP verisi → TCP segment → IP paket → Ethernet frame | Katmanlar |
| 3 | Ethernet frame anatomisi: preamble, dest/src MAC, EtherType, payload, FCS (byte ölçekli) | Ethernet |
| 4 | MAC adresi yapısı: OUI + cihaz kısmı, broadcast FF:FF:... | Ethernet |
| 5 | Hub vs Switch vs Router davranış farkı (aynı topolojide üç panel) | Cihazlar |
| 6 | Switch MAC öğrenme tablosu animasyon-vari adım adım (3 kare) | Cihazlar |
| 7 | ARP request/reply sequence diyagramı (broadcast → unicast cevap) | ARP |
| 8 | ARP tablosu + "gateway'in MAC'i" senaryosu: uzak IP'ye giden frame'in MAC hedefi | ARP/Gateway |
| 9 | IP adresi + subnet mask bit düzeyinde AND işlemi, "yerel mi uzak mı" kararı | IP/Subnet |
| 10 | Ev/kurumsal ağ topolojisi: cihaz → switch → gateway/router → internet | Gateway |
| 11 | NAT çeviri tablosu: iç IP:port ↔ dış IP:port eşlemesi | NAT |
| 12 | TCP three-way handshake + veri + FIN kapanışı sequence diyagramı | TCP |
| 13 | TCP header alan haritası vs UDP header alan haritası (yan yana, byte ölçekli) | TCP/UDP |
| 14 | Kayıp paket senaryosu: TCP retransmit vs UDP "umursamama" (iki panel) | TCP/UDP |
| 15 | Port kavramı: tek IP, çok uygulama; soket = IP+port dörtlüsü | Port |
| 16 | DNS çözümleme hiyerarşisi: cache → resolver → root → TLD → authoritative | DNS |
| 17 | TLS handshake basitleştirilmiş akışı + "kilitli tünel içinde HTTP" | HTTPS |
| 18 | BÜYÜK FİNAL ŞEMASI: "tarayıcıya URL yazınca" uçtan uca tam zincir — DNS, ARP, TCP, TLS, HTTP tek zaman çizgisinde | Sentez |
| 19 | Gömülü Ethernet yolu: PHY ↔ (R)(G)MII ↔ MAC ↔ DMA ↔ yazılım stack (lwIP/OS) | Gömülü |
| 20 | Wireshark ekran anatomisi: paket listesi / detay ağacı / hex — hangi katman nerede | Pratik |
| 21 | Arıza teşhis karar ağacı: link LED → ping gateway → ping IP → DNS → port | Teşhis |

---

## 5. İçindekiler (bölüm iskeleti)

Her bölüm: kısa "neden umursamalısın" girişi → ana anlatı → şema(lar) →
saha notu/tuzak kutuları → 3-5 maddelik "bölüm özeti".

### Bölüm 0 — Önsöz: Bu kılavuz kimin için, nasıl okunmalı
Serinin ruhu, okuma haritası ("acelen varsa 1-7-9-10 oku" tarzı rotalar).

### Bölüm 1 — Büyük Resim: Katmanlar
Neden katman var; OSI vs TCP/IP; enkapsülasyon; "her katman bir zarf" anlatısı.
Kılavuz boyunca kullanılacak 5 katmanlı zihinsel model burada sabitlenir.

### Bölüm 2 — Fiziksel Katman ve Kablonun İçi
Twisted pair, kategoriler (Cat5e/6/6a), fiber vs bakır, link speed/duplex,
auto-negotiation, link LED'inin anlamı. Kısa ama somut.

### Bölüm 3 — Ethernet ve MAC
Frame anatomisi, MAC adresi, EtherType, FCS/CRC, MTU kavramı, jumbo frame,
broadcast/multicast/unicast farkı. VLAN'a bir pencere (802.1Q tag, `derin-dalis`).

### Bölüm 4 — Ağ Cihazları: Hub, Switch, Router
Collision domain vs broadcast domain; switch'in MAC öğrenmesi; router'ın
katman-3 işi. "Switch MAC konuşur, router IP konuşur" cümlesi kalıcı hale getirilir.

### Bölüm 5 — IP, Subnet ve "Yerel mi Uzak mı" Kararı
IPv4 yapısı, subnet mask, CIDR notasyonu, private adres blokları
(10/8, 172.16/12, 192.168/16), bit düzeyinde AND örneği. IPv6'ya dürüst
bir pencere (`derin-dalis`: temel format + link-local, abartısız).

### Bölüm 6 — Gateway ve Yönlendirme
Default gateway ne yapar; routing table okuma (`route print` / `ip route`);
"IP hedefi uzak ama MAC hedefi gateway" kritik kavrayışı; TTL ve traceroute.

### Bölüm 7 — ARP: İki Dünyanın Köprüsü
Request/reply, ARP cache, gratuitous ARP, ARP'ın güvenlik zaafı
(spoofing — `derin-dalis`). Wireshark'ta canlı ARP izleme saha notu.

### Bölüm 8 — DHCP: Adresler Nereden Geliyor
DORA akışı (Discover/Offer/Request/Ack), lease, statik IP vs DHCP;
gömülü kartlarda statik IP tercih nedenleri. Kısa bölüm.

### Bölüm 9 — Taşıma Katmanı: TCP ve UDP
Port kavramı ve soket dörtlüsü; well-known portlar tablosu;
TCP: handshake, sequence/ACK, retransmit, flow/congestion control (sezgisel
düzeyde), FIN/RST; UDP: minimalizm ve nerede kazandığı. Header karşılaştırması.
Gömülü perspektif: telemetride UDP tercihi, TCP retransmit jitter'ı.

### Bölüm 10 — DNS: İnternetin Rehberi
Hiyerarşi, resolver zinciri, cache/TTL, kayıt türleri (A, AAAA, CNAME, MX, TXT),
hosts dosyası, `nslookup`/`dig` kullanımı. "It's always DNS" kutusu.

### Bölüm 11 — HTTP ve HTTPS
HTTP istek/yanıt anatomisi (metot, status code, header); TLS'in üç işi
(şifreleme, bütünlük, kimlik); sertifika zinciri sezgisel anlatım;
HTTP/1.1 → 2 → 3 (QUIC/UDP) evrimi kısa pencere.

### Bölüm 12 — NAT ve Ev/Kurum Ağının Gerçeği
Neden NAT var, port forwarding, "dışarıdan cihazıma neden erişemiyorum"
sorusunun cevabı. Kurumsal LAN'da proxy/firewall kavramına kısa dokunuş.

### Bölüm 13 — SENTEZ: Bir URL'nin Uçtan Uca Yolculuğu
Kılavuzun zirvesi. `https://example.com` yazıldığı andan sayfa gelene kadar
her adım, önceki 12 bölümün kavramlarıyla, tek büyük zaman çizgisi şemasıyla
(şema #18). Bu bölüm bağımsız okunabilir kalitede olmalı.

### Bölüm 14 — Gömülü Sistemlerde Ethernet
PHY/MAC ayrımı, MII/RMII/RGMII/SGMII arayüzleri, MDIO ile PHY register erişimi,
lwIP ve raw/netconn/socket API'leri, Zynq/Versal GEM MAC'ine kısa referans,
checksum offload, "kart ping atmıyor" gömülü teşhis sırası (PHY link reg →
MAC init → IP config → ARP görünürlüğü).

### Bölüm 15 — Pratik Alet Çantası
Wireshark başlangıç (capture filter vs display filter, temel filtre reçeteleri);
`ping`, `arp -a`, `ipconfig /all`, `netstat -ano`, `tracert`, `nslookup`,
`telnet host port` ile port testi; Python ile minimal UDP ve TCP soket örneği
(gönderen + alan, yorum satırlı, Windows'ta çalışır halde).

### Bölüm 16 — Arıza Teşhis Rehberi
Karar ağacı (şema #21) + senaryo tablosu: "link LED yok", "ping var DNS yok",
"aynı subnet'te ping yok", "TCP bağlanıyor ama veri gelmiyor", "duplex
mismatch" — her satırda belirti / muhtemel neden / kontrol komutu.

### Ek A — Terimler Sözlüğü
Alfabetik, iki-üç cümlelik tanımlar, ilgili bölüme link.

### Ek B — Hızlı Referans Kartı
Tek ekranlık özet: katman tablosu, header boyutları, well-known portlar,
private IP blokları, temel komutlar. Yazdırılabilir hissi versin.

---

## 6. Yazım Kuralları

1. **Pedagojik sıra:** Hiçbir kavram tanımlanmadan kullanılamaz. Bölümler
   yukarıdaki sırayla birbirinin üstüne inşa edilir; ileri referans gerekirse
   "Bölüm X'te göreceğiz" denir.
2. **Anlatı tonu:** Ciddi ama sıcak; akademik makale değil, ustasının çırağa
   anlattığı ton. Kısa cümleler, aktif çatı. Emoji yok. LinkedIn dili yok.
3. **Her soyut kavrama bir somut karşılık:** analoji kutusu, gerçek komut
   çıktısı ya da Wireshark görünümü. Havada kalan paragraf yasak.
4. **Sayılar gerçek:** header boyutları, port numaraları, adres blokları
   doğru olmalı; emin olunmayan detay yazılmaz.
5. **Bölüm uzunluğu:** ana bölümler 800–1500 kelime; sentez bölümü (13)
   ve gömülü bölümü (14) 2000 kelimeye kadar çıkabilir.
6. **Kod örnekleri:** Python 3 stdlib only (`socket`), Windows'ta test
   edilebilir; komut örnekleri hem Windows hem Linux karşılığıyla verilir
   (`arp -a` / `ip neigh` gibi).

---

## 7. Build Kuralları

- `build/build.py`: `content/*.md` dosyalarını sırayla okur, SVG'leri yerine
  gömer, CSS'i inline eder, TOC'u başlıklardan otomatik üretir, tek
  `dist/index.html` yazar. Tercihen stdlib; markdown parser gerekiyorsa
  tek dosyalık vendored çözüm kullanılabilir.
- HTML çıktısı 2 MB altında kalmaya çalışsın (SVG'ler zaten hafif).
- JS bütçesi: tema toggle + TOC vurgusu + kod kopyala + progress bar.
  Başka framework/JS yok.

---

## 8. Üretim Akışı (Claude Code için)

1. Repo iskeletini kur, CLAUDE.md'yi yaz.
2. `kilavuz.css` temasını üret; boş bir bölümle uçtan uca build'i doğrula.
3. Bölümleri sırayla yaz (0→16, sonra ekler). Her bölümün SVG'lerini bölümle
   birlikte üret — "önce tüm metin sonra tüm şema" YAPMA; şema anlatının parçası.
4. Her 3-4 bölümde bir build alıp `dist/index.html`'i görsel olarak kontrol et:
   TOC çalışıyor mu, SVG'ler iki temada da okunuyor mu, taşma var mı.
5. Sentez bölümünü (13) en son yaz — önceki bölümlerin diline ve şemalarına
   geri referans verecek.
6. Son tur: tutarlılık taraması (terimlerin ilk açılımları, çapraz linkler,
   bölüm özetleri), sözlük ve hızlı referans kartını içerikten derle.

## 9. Kalite Çıtası (bitmiş sayılma kriterleri)

- [ ] `dist/index.html` çift tıklamayla, internetsiz, tarayıcıda kusursuz açılıyor
- [ ] En az 20 el yapımı SVG var ve ikisi de temada okunaklı
- [ ] Sentez bölümü (13) tek başına paylaşılabilir kalitede
- [ ] Her bölümde en az bir `saha-notu` veya `tuzak` kutusu var
- [ ] Python soket örnekleri kopyala-yapıştır çalışıyor
- [ ] TOC, anchor linkler, tema toggle, kod kopyala butonları çalışıyor
- [ ] Terimler sözlüğü ve hızlı referans kartı tam
